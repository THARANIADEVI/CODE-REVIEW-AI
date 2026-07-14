"""AI-powered code review. Uses Mistral AI's Chat Completions API when
MISTRAL_API_KEY is configured; otherwise falls back to a local heuristic
reviewer so the app is fully usable without any external API key.
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


def _mistral_client():
    """Returns (client, model) if MISTRAL_API_KEY is configured, else (None, None).
    Mistral AI's API is OpenAI Chat Completions-compatible, so the `openai` SDK
    is reused here pointed at Mistral's base URL instead of adding a new dependency."""
    api_key = current_app.config.get("MISTRAL_API_KEY")
    if not api_key:
        return None, None

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=current_app.config.get("MISTRAL_BASE_URL", "https://api.mistral.ai/v1"))
    model = current_app.config.get("MISTRAL_MODEL", "mistral-small-latest")
    return client, model


def review_code_with_ai(code: str, filename: str) -> dict:
    client, model = _mistral_client()
    if client:
        try:
            return _review_with_mistral(code, filename, client, model)
        except Exception as exc:  # pragma: no cover - network/library failure fallback
            fallback = _heuristic_review(code, filename)
            fallback["summary"] = f"AI provider error, used local heuristic review. ({exc})"
            return fallback
    return _heuristic_review(code, filename)


def _review_with_mistral(code: str, filename: str, client, model: str) -> dict:
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
        "Configure MISTRAL_API_KEY for deeper LLM-powered analysis."
    )

    return {"quality_score": quality_score, "summary": summary, "findings": findings}


# --------------------------------------------------------------------------
# AI-powered auto-refactor
# --------------------------------------------------------------------------
REFACTOR_SYSTEM_PROMPT = "You are an experienced Senior Software Engineer specializing in refactoring."

REFACTOR_USER_PROMPT_TEMPLATE = """Rewrite the following source file to fix the issues listed below while
preserving its external behavior. Apply best practices, clean up code smells, and address the findings
where reasonably possible. Do not change the overall purpose of the code.

Return the response in structured JSON format with this exact schema:
{{
  "refactored_code": "<the full refactored source code, as a single string>",
  "changes": ["<short description of change 1>", "<short description of change 2>", "..."]
}}

File: {filename}

Findings to address:
{findings_text}

Original code:
```
{code}
```
"""


def generate_refactored_code(source_code: str, findings: list, filename: str = "") -> dict:
    client, model = _mistral_client()
    if client:
        try:
            return _refactor_with_mistral(source_code, findings, filename, client, model)
        except Exception as exc:  # pragma: no cover - network/library failure fallback
            fallback = _heuristic_refactor(source_code, findings, filename)
            fallback["changes"].insert(0, f"AI provider error, used local heuristic refactor. ({exc})")
            return fallback
    return _heuristic_refactor(source_code, findings, filename)


def _refactor_with_mistral(source_code: str, findings: list, filename: str, client, model: str) -> dict:
    findings_text = "\n".join(
        f"- [{f.get('severity', 'medium')}] {f.get('issue', '')}: {f.get('explanation', '')}"
        for f in (findings or [])
    ) or "None reported."

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": REFACTOR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": REFACTOR_USER_PROMPT_TEMPLATE.format(
                    filename=filename, findings_text=findings_text, code=source_code[:20000]
                ),
            },
        ],
        temperature=0.2,
    )
    content = response.choices[0].message.content
    return _normalize_refactor(json.loads(content), source_code)


def _normalize_refactor(data: dict, original_code: str) -> dict:
    data.setdefault("refactored_code", original_code)
    data.setdefault("changes", [])
    if not isinstance(data.get("changes"), list):
        data["changes"] = [str(data["changes"])]
    return data


# --------------------------------------------------------------------------
# Offline heuristic refactor fallback (no API key required)
# --------------------------------------------------------------------------
def _heuristic_refactor(source_code: str, findings: list, filename: str) -> dict:
    """Applies a few safe, deterministic transforms using the same heuristics
    defined above. Never invents behavior changes: if nothing safe to change
    is found, returns the original code unchanged with an explanatory note."""
    refactored = source_code
    changes = []

    # 1. print(...) -> logging.info(...) (only when logging isn't already used oddly)
    if re.search(r"print\(", refactored):
        new_refactored = re.sub(r"\bprint\(", "logging.info(", refactored)
        if new_refactored != refactored:
            if not re.search(r"^import logging\b", refactored, re.M):
                new_refactored = "import logging\n" + new_refactored
            refactored = new_refactored
            changes.append("Replaced print() calls with logging.info() calls.")

    # 2. bare `except:` -> `except Exception:`
    new_refactored = re.sub(r"\bexcept\s*:\s*$", "except Exception:", refactored, flags=re.M)
    if new_refactored != refactored:
        refactored = new_refactored
        changes.append("Replaced bare `except:` clauses with `except Exception:`.")

    # 3. Strip trailing whitespace on each line (safe cosmetic cleanup)
    new_refactored = "\n".join(line.rstrip() for line in refactored.splitlines())
    if source_code.splitlines() and new_refactored != "\n".join(source_code.splitlines()):
        if refactored != new_refactored:
            changes.append("Removed trailing whitespace.")
        refactored = new_refactored + ("\n" if source_code.endswith("\n") else "")

    if not changes:
        changes.append("AI refactor requires MISTRAL_API_KEY")
        refactored = source_code

    return {"refactored_code": refactored, "changes": changes}


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
