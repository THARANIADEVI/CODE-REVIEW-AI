import os

ALLOWED_EXTENSIONS = {"py", "js", "jsx", "ts", "tsx"}
IGNORED_DIRS = {"node_modules", "venv", ".venv", "__pycache__", ".git", "dist", "build"}
IGNORED_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "svg", "ico", "pdf", "zip", "tar", "gz",
    "exe", "dll", "so", "pyc", "lock", "woff", "woff2", "ttf", "eot",
}


def is_allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def is_ignored_path(path: str) -> bool:
    parts = set(path.replace("\\", "/").split("/"))
    if parts & IGNORED_DIRS:
        return True
    if "." in path:
        ext = path.rsplit(".", 1)[1].lower()
        if ext in IGNORED_EXTENSIONS:
            return True
    return False


def detect_language(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "py":
        return "python"
    if ext in {"js", "jsx"}:
        return "javascript"
    if ext in {"ts", "tsx"}:
        return "typescript"
    return "unknown"
