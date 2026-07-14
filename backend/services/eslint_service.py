"""JavaScript/TypeScript static analysis via ESLint, mirroring pylint_service's
shape (findings + a 0-10 quality score) so multi-language projects get real
static analysis rather than only the AI review pass. Gracefully skips if
Node.js/npx/eslint aren't available on the host, so the app keeps working
without them (same fallback philosophy as the OpenAI integration)."""
import json
import subprocess
import tempfile
import os
import shutil

_ESLINT_CONFIG = {
    "env": {"browser": True, "es2021": True, "node": True},
    "parserOptions": {"ecmaVersion": "latest", "sourceType": "module", "ecmaFeatures": {"jsx": True}},
    "rules": {
        "no-eval": "error",
        "no-implied-eval": "error",
        "no-unused-vars": "warn",
        "no-undef": "warn",
        "no-var": "warn",
        "eqeqeq": "warn",
        "no-console": "off",
        "no-debugger": "warn",
        "no-empty": "warn",
        "no-dupe-keys": "error",
        "no-unreachable": "error",
    },
}

_NPX_PATH = shutil.which("npx")
_NPX_AVAILABLE = _NPX_PATH is not None


def run_eslint(code: str, filename: str) -> dict:
    """Runs ESLint on a single JS/TS source string, returns quality score (0-10) + messages."""
    if not filename.endswith((".js", ".jsx", ".ts", ".tsx")):
        return {"score": None, "messages": [], "skipped": True}
    if not _NPX_AVAILABLE:
        return {"score": None, "messages": [], "skipped": True, "error": "eslint unavailable (npx not found)"}

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = os.path.join(tmp_dir, os.path.basename(filename))
        config_path = os.path.join(tmp_dir, ".eslintrc.json")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(code)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(_ESLINT_CONFIG, f)

        try:
            result = subprocess.run(
                [_NPX_PATH, "--yes", "eslint", "--no-eslintrc", "-c", config_path,
                 "--format", "json", tmp_path],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=tmp_dir,
                shell=False,
            )
            payload = json.loads(result.stdout) if result.stdout.strip() else []
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return {"score": None, "messages": [], "skipped": True, "error": "eslint unavailable or timed out"}

        messages = []
        for file_result in payload:
            for m in file_result.get("messages", []):
                messages.append({
                    "line": m.get("line", 0),
                    "column": m.get("column", 0),
                    "severity": "error" if m.get("severity") == 2 else "warning",
                    "rule": m.get("ruleId") or "",
                    "message": m.get("message", ""),
                })

        score = _estimate_score(messages, code)
        return {"score": score, "messages": messages}


def _estimate_score(messages, code) -> float:
    loc = max(len(code.splitlines()), 1)
    weight = {"error": 5, "warning": 2}
    penalty = sum(weight.get(m["severity"], 2) for m in messages)
    score = max(0.0, 10.0 - (penalty * 10 / (loc * 2)))
    return round(score, 2)
