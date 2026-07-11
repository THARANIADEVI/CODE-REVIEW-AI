import json
import subprocess
import sys
import tempfile
import os


def run_bandit(code: str, filename: str = "snippet.py") -> dict:
    """Runs bandit security scan on a single python source string."""
    if not filename.endswith(".py"):
        return {"issues": [], "skipped": True}

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = os.path.join(tmp_dir, os.path.basename(filename))
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            result = subprocess.run(
                [sys.executable, "-m", "bandit", "-f", "json", "-q", tmp_path],
                capture_output=True,
                text=True,
                timeout=60,
            )
            payload = json.loads(result.stdout) if result.stdout.strip() else {}
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return {"issues": [], "error": "bandit unavailable or timed out"}

        issues = [
            {
                "line": r.get("line_number", 0),
                "severity": r.get("issue_severity", "LOW").lower(),
                "confidence": r.get("issue_confidence", "LOW").lower(),
                "test_id": r.get("test_id", ""),
                "issue": r.get("issue_text", ""),
            }
            for r in payload.get("results", [])
        ]
        return {"issues": issues}
