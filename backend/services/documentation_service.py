"""Generates function/class/module documentation via AST inspection.
Falls back gracefully for non-python files (returns empty doc set)."""
import ast


def generate_documentation(code: str, filename: str) -> dict:
    if not filename.endswith(".py"):
        return {"module": None, "classes": [], "functions": []}

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}"}

    module_doc = ast.get_docstring(tree)
    classes = []
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "line_number": node.lineno,
                "docstring": ast.get_docstring(node) or _auto_summary_class(node),
                "methods": [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))],
            })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_top_level_or_method(node, tree):
            functions.append({
                "name": node.name,
                "line_number": node.lineno,
                "args": [a.arg for a in node.args.args],
                "docstring": ast.get_docstring(node) or _auto_summary_function(node),
            })

    return {
        "module": module_doc or f"Module `{filename}` — no module-level docstring found.",
        "classes": classes,
        "functions": functions,
    }


def _is_top_level_or_method(node, tree):
    for parent in ast.walk(tree):
        if isinstance(parent, (ast.ClassDef, ast.Module)):
            if node in getattr(parent, "body", []):
                return True
    return False


def _auto_summary_function(node) -> str:
    args = ", ".join(a.arg for a in node.args.args)
    return f"Auto-generated: `{node.name}({args})` — no docstring provided in source."


def _auto_summary_class(node) -> str:
    return f"Auto-generated: class `{node.name}` — no docstring provided in source."


def generate_readme_summary(project_name: str, files_docs: list) -> str:
    lines = [f"# {project_name}", "", "Auto-generated summary from AI Code Review Assistant.", ""]
    for doc in files_docs:
        filename = doc.get("filename", "unknown")
        module = doc.get("documentation", {}).get("module")
        lines.append(f"## `{filename}`")
        if module:
            lines.append(module)
        classes = doc.get("documentation", {}).get("classes", [])
        functions = doc.get("documentation", {}).get("functions", [])
        if classes:
            lines.append("\n**Classes:**")
            for c in classes:
                lines.append(f"- `{c['name']}` — {c['docstring']}")
        if functions:
            lines.append("\n**Functions:**")
            for f in functions:
                lines.append(f"- `{f['name']}({', '.join(f['args'])})` — {f['docstring']}")
        lines.append("")
    return "\n".join(lines)
