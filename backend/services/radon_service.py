from radon.complexity import cc_visit
from radon.metrics import mi_visit
from radon.raw import analyze


def run_radon(code: str, filename: str = "snippet.py") -> dict:
    """Computes cyclomatic complexity, maintainability index and raw metrics for python source."""
    if not filename.endswith(".py"):
        return {"skipped": True}

    try:
        blocks = cc_visit(code)
        complexity = [
            {
                "name": b.name,
                "type": b.letter,  # F = function, M = method, C = class
                "line_number": b.lineno,
                "complexity": b.complexity,
                "rank": _rank(b.complexity),
            }
            for b in blocks
        ]
        maintainability = round(mi_visit(code, multi=True), 2)
        raw = analyze(code)

        num_functions = len([b for b in blocks if b.letter in ("F", "M")])
        num_classes = len([b for b in blocks if b.letter == "C"])
        avg_function_length = (
            round(raw.lloc / num_functions, 2) if num_functions else 0
        )
        avg_complexity = (
            round(sum(b.complexity for b in blocks) / len(blocks), 2) if blocks else 0
        )

        return {
            "complexity_blocks": complexity,
            "average_complexity": avg_complexity,
            "maintainability_index": maintainability,
            "loc": raw.loc,
            "lloc": raw.lloc,
            "sloc": raw.sloc,
            "comments": raw.comments,
            "blank_lines": raw.blank,
            "num_functions": num_functions,
            "num_classes": num_classes,
            "average_function_length": avg_function_length,
        }
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}


def _rank(complexity: int) -> str:
    if complexity <= 5:
        return "A"
    if complexity <= 10:
        return "B"
    if complexity <= 20:
        return "C"
    if complexity <= 30:
        return "D"
    if complexity <= 40:
        return "E"
    return "F"
