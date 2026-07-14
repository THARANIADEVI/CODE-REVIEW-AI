"""Orchestrates the 3-stage analysis: static analysis (pylint/bandit/radon),
AI-powered review, and documentation generation. Persists a Review + its
ReviewFindings for a Project.
"""
from extensions import db
from models import Review, ReviewFinding
from services.pylint_service import run_pylint
from services.bandit_service import run_bandit
from services.radon_service import run_radon
from services.eslint_service import run_eslint
from services.openai_service import review_code_with_ai
from services.documentation_service import generate_documentation
from utils.file_utils import detect_language

SEVERITY_MAP = {
    "error": "high", "fatal": "critical", "warning": "medium",
    "refactor": "low", "convention": "info",
}
BANDIT_SEVERITY_MAP = {"high": "high", "medium": "medium", "low": "low"}
ESLINT_SEVERITY_MAP = {"error": "high", "warning": "medium"}


def analyze_files(project, files: list) -> Review:
    """files: list of dicts {filename, content}"""
    all_findings = []
    per_file_metrics = []
    per_file_docs = []
    quality_scores = []
    ai_summaries = []

    for file in files:
        filename = file["filename"]
        content = file["content"]
        language = detect_language(filename)

        pylint_result = run_pylint(content, filename) if language == "python" else {}
        bandit_result = run_bandit(content, filename) if language == "python" else {}
        radon_result = run_radon(content, filename) if language == "python" else {}
        eslint_result = (
            run_eslint(content, filename) if language in ("javascript", "typescript") else {}
        )
        ai_result = review_code_with_ai(content, filename)
        doc_result = generate_documentation(content, filename)

        per_file_docs.append({"filename": filename, "documentation": doc_result})

        for m in pylint_result.get("messages", []):
            all_findings.append(ReviewFinding(
                severity=SEVERITY_MAP.get(m["type"], "info"),
                category="code_quality",
                issue=f"{m['symbol'] or m['type']}: {m['message']}"[:295],
                explanation=m["message"],
                suggestion="Follow PEP 8 / pylint recommendation for this rule.",
                file_name=filename,
                line_number=m["line"],
                source="pylint",
            ))

        for m in eslint_result.get("messages", []):
            all_findings.append(ReviewFinding(
                severity=ESLINT_SEVERITY_MAP.get(m["severity"], "medium"),
                category="code_quality",
                issue=f"{m['rule'] or 'eslint'}: {m['message']}"[:295],
                explanation=m["message"],
                suggestion="Follow the ESLint rule recommendation for this check.",
                file_name=filename,
                line_number=m["line"],
                source="eslint",
            ))

        for issue in bandit_result.get("issues", []):
            all_findings.append(ReviewFinding(
                severity=BANDIT_SEVERITY_MAP.get(issue["severity"], "medium"),
                category="security",
                issue=issue["test_id"] + ": " + issue["issue"][:250],
                explanation=issue["issue"],
                suggestion="Review Bandit documentation for this check and remediate.",
                file_name=filename,
                line_number=issue["line"],
                source="bandit",
            ))

        for finding in ai_result.get("findings", []):
            all_findings.append(ReviewFinding(
                severity=finding.get("severity", "medium"),
                category=finding.get("category", "best_practice"),
                issue=finding.get("issue", "")[:295],
                explanation=finding.get("explanation", ""),
                suggestion=finding.get("suggestion", ""),
                file_name=filename,
                line_number=finding.get("line_number", 0),
                source="ai",
            ))

        if "quality_score" in ai_result:
            quality_scores.append(ai_result["quality_score"])
        if ai_result.get("summary"):
            ai_summaries.append(f"{filename}: {ai_result['summary']}")

        file_metrics = {"filename": filename, "language": language}
        if radon_result and not radon_result.get("skipped"):
            file_metrics.update(radon_result)
        if pylint_result.get("score") is not None:
            file_metrics["pylint_score"] = pylint_result["score"]
        if eslint_result.get("score") is not None:
            file_metrics["eslint_score"] = eslint_result["score"]
        per_file_metrics.append(file_metrics)

    aggregated_metrics = _aggregate_metrics(per_file_metrics)
    documentation = {"files": per_file_docs}

    overall_score = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 70.0

    review = Review(
        project_id=project.id,
        review_score=overall_score,
        summary=" | ".join(ai_summaries)[:4000] or "Automated multi-stage code review completed.",
    )
    review.metrics = aggregated_metrics
    review.documentation = documentation
    review.source_files = [{"filename": f["filename"], "content": f["content"]} for f in files]
    db.session.add(review)
    db.session.flush()  # get review.id

    for f in all_findings:
        f.review_id = review.id
        db.session.add(f)

    db.session.commit()
    return review


def _aggregate_metrics(per_file_metrics: list) -> dict:
    total_loc = sum(m.get("loc", 0) for m in per_file_metrics)
    total_functions = sum(m.get("num_functions", 0) for m in per_file_metrics)
    total_classes = sum(m.get("num_classes", 0) for m in per_file_metrics)
    mi_values = [m["maintainability_index"] for m in per_file_metrics if "maintainability_index" in m]
    avg_mi = round(sum(mi_values) / len(mi_values), 2) if mi_values else None
    cc_values = [m["average_complexity"] for m in per_file_metrics if "average_complexity" in m]
    avg_cc = round(sum(cc_values) / len(cc_values), 2) if cc_values else None
    avg_func_len_values = [m["average_function_length"] for m in per_file_metrics if "average_function_length" in m]
    avg_func_len = round(sum(avg_func_len_values) / len(avg_func_len_values), 2) if avg_func_len_values else None

    return {
        "total_lines_of_code": total_loc,
        "num_functions": total_functions,
        "num_classes": total_classes,
        "average_cyclomatic_complexity": avg_cc,
        "maintainability_index": avg_mi,
        "average_function_length": avg_func_len,
        "files": per_file_metrics,
    }
