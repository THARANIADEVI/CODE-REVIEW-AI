import json
import subprocess
import sys
import tempfile
import os


def run_pylint(code: str, filename: str = "snippet.py") -> dict:
    """Runs pylint on a single python source string, returns quality score + messages."""
    if not filename.endswith(".py"):
        return {"score": None, "messages": [], "skipped": True}

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = os.path.join(tmp_dir, os.path.basename(filename))
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pylint", tmp_path,
                 "--output-format=json", "--disable=C0114,C0115,C0116"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            messages = json.loads(result.stdout) if result.stdout.strip() else []
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return {"score": None, "messages": [], "error": "pylint unavailable or timed out"}

        score = _estimate_score(messages, code)
        cleaned = [
            {
                "line": m.get("line", 0),
                "column": m.get("column", 0),
                "type": m.get("type", "convention"),
                "symbol": m.get("symbol", ""),
                "message": m.get("message", ""),
            }
            for m in messages
        ]
        return {"score": score, "messages": cleaned}


def _estimate_score(messages, code) -> float:
    """Pylint's own 10-point score requires --score plain output; approximate similarly here."""
    loc = max(len(code.splitlines()), 1)
    weight = {"error": 5, "fatal": 5, "warning": 2, "refactor": 1, "convention": 0.5}
    penalty = sum(weight.get(m.get("type", "convention"), 1) for m in messages)
    score = max(0.0, 10.0 - (penalty * 10 / (loc * 2)))
    return round(score, 2)
