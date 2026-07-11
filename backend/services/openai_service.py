"""AI-powered code review. Uses OpenAI's Chat Completions API when OPENAI_API_KEY
is configured; otherwise falls back to a local heuristic reviewer so the app is
fully usable without any external API key (per "OpenAI API or Any LLM Provider").
"""
import json
import re
from flask import current_app

SYSTEM_PROMPT = "You are an experienced Senior Software Engineer."

USER_PROMPT_TEMPLATE = """Review the uploaded code and provide:

1. Bugs found
2. Security issues
3. Code smells
4. Complexity analysis
5. Performance improvements
6. Best practices
7. Suggested refactoring
8. Better variable/function names
9. Code quality score out of 100
10. Summary of improvements

Return the response in structured JSON format with this exact schema:
{{
  "quality_score": <0-100 integer>,
  "summary": "<2-4 sentence summary>",
  "findings": [
    {{
      "severity": "critical|high|medium|low|info",
      "category": "bug|security|code_smell|performance|refactor|naming|best_practice|documentation",
      "issue": "<short title>",
      "explanation": "<why this matters>",
      "suggestion": "<concrete fix>",
      "line_number": <int or 0 if unknown>
    }}
  ]
}}

File: {filename}

Code:
```
{code}
```
"""


def review_code_with_ai(code: str, filename: str) -> dict:
    api_key = current_app.config.get("OPENAI_API_KEY")
    if api_key:
        try:
            return _review_with_openai(code, filename, api_key)
        except Exception as exc:  # pragma: no cover - network/library failure fallback
            fallback = _heuristic_review(code, filename)
            fallback["summary"] = f"AI provider error, used local heuristic review. ({exc})"
            return fallback
    return _heuristic_review(code, filename)


def _review_with_openai(code: str, filename: str, api_key: str) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    model = current_app.config.get("OPENAI_MODEL", "gpt-4o-mini")

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(filename=filename, code=code[:20000]),
            },
        ],
        temperature=0.2,
    )
    content = response.choices[0].message.content
    return _normalize(json.loads(content))


def _normalize(data: dict) -> dict:
    data.setdefault("quality_score", 70)
    data.setdefault("summary", "")
    data.setdefault("findings", [])
    for f in data["findings"]:
        f.setdefault("severity", "medium")
        f.setdefault("category", "best_practice")
        f.setdefault("issue", "Issue")
        f.setdefault("explanation", "")
        f.setdefault("suggestion", "")
        f.setdefault("line_number", 0)
    return data


# --------------------------------------------------------------------------
# Offline heuristic fallback (no API key required)
# --------------------------------------------------------------------------
_HEURISTICS = [
    (re.compile(r"\bexcept\s*:\s*$", re.M), "high", "bug",
     "Bare except clause",
     "Catching all exceptions silently hides real bugs and makes debugging harder.",
     "Catch specific exception types, e.g. `except ValueError:`."),
    (re.compile(r"\beval\s*\("), "critical", "security",
     "Use of eval()",
     "eval() executes arbitrary code and is a common injection vector.",
     "Avoid eval(); use ast.literal_eval() or explicit parsing instead."),
    (re.compile(r"\bexec\s*\("), "critical", "security",
     "Use of exec()",
     "exec() executes arbitrary code and is a common injection vector.",
     "Avoid exec(); refactor to explicit logic."),
    (re.compile(r"def\s+\w+\([^)]*=\s*(\[\]|\{\}|\(\))"), "medium", "bug",
     "Mutable default argument",
     "Mutable default arguments are shared across calls and can cause subtle bugs.",
     "Use `None` as the default and initialize inside the function body."),
    (re.compile(r"\bpassword\s*=\s*[\"'][^\"']+[\"']", re.I), "critical", "security",
     "Hardcoded credential",
     "Hardcoded secrets can leak via source control.",
     "Load credentials from environment variables or a secrets manager."),
    (re.compile(r"\bTODO\b|\bFIXME\b"), "low", "code_smell",
     "Unresolved TODO/FIXME",
     "Leftover TODO markers indicate incomplete work.",
     "Resolve or track the TODO in an issue tracker before shipping."),
    (re.compile(r"print\("), "info", "best_practice",
     "print() used instead of logging",
     "print() statements are hard to control in production.",
     "Use the `logging` module with appropriate log levels."),
    (re.compile(r"select\s+\*.+%s|\+\s*request\.", re.I), "high", "security",
     "Possible SQL/string injection via concatenation",
     "Building queries or commands via string concatenation risks injection.",
     "Use parameterized queries / an ORM instead of string concatenation."),
]


def _heuristic_review(code: str, filename: str) -> dict:
    findings = []
    lines = code.splitlines()

    for pattern, severity, category, issue, explanation, suggestion in _HEURISTICS:
        for match in pattern.finditer(code):
            line_no = code.count("\n", 0, match.start()) + 1
            findings.append({
                "severity": severity,
                "category": category,
                "issue": issue,
                "explanation": explanation,
                "suggestion": suggestion,
                "line_number": line_no,
            })

    long_functions = _find_long_functions(lines)
    findings.extend(long_functions)

    penalty = sum({"critical": 20, "high": 12, "medium": 6, "low": 2, "info": 1}.get(f["severity"], 2)
                   for f in findings)
    quality_score = max(5, 100 - penalty)

    summary = (
        f"Heuristic offline review of {filename}: found {len(findings)} potential issue(s). "
        "Configure OPENAI_API_KEY for deeper LLM-powered analysis."
    )

    return {"quality_score": quality_score, "summary": summary, "findings": findings}


def _find_long_functions(lines, threshold=40):
    findings = []
    current_start = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("def "):
            if current_start is not None and (i - current_start) > threshold:
                findings.append({
                    "severity": "medium",
                    "category": "code_smell",
                    "issue": "Long function",
                    "explanation": f"Function spans {i - current_start} lines, hurting readability.",
                    "suggestion": "Split into smaller, single-purpose functions.",
                    "line_number": current_start + 1,
                })
            current_start = i
    if current_start is not None and (len(lines) - current_start) > threshold:
        findings.append({
            "severity": "medium",
            "category": "code_smell",
            "issue": "Long function",
            "explanation": f"Function spans {len(lines) - current_start} lines, hurting readability.",
            "suggestion": "Split into smaller, single-purpose functions.",
            "line_number": current_start + 1,
        })
    return findings
