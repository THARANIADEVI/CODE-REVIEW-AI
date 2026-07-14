from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from extensions import db
from models import Review, Project, ReviewFinding
from utils.decorators import current_user_required
from services.openai_service import generate_refactored_code

review_bp = Blueprint("review", __name__)


@review_bp.get("/analytics")
@jwt_required()
@current_user_required
def review_analytics(user):
    """Aggregate stats across all of the user's reviews: score trend over time,
    findings broken down by severity/category, and submissions by upload type."""
    reviews = (
        db.session.query(Review)
        .join(Project, Review.project_id == Project.id)
        .filter(Project.user_id == user.id)
        .order_by(Review.created_at.asc())
        .all()
    )

    severity_totals = {}
    category_totals = {}
    upload_type_totals = {}
    score_trend = []

    review_ids = [r.id for r in reviews]
    findings = (
        ReviewFinding.query.filter(ReviewFinding.review_id.in_(review_ids)).all()
        if review_ids else []
    )
    for f in findings:
        severity_totals[f.severity] = severity_totals.get(f.severity, 0) + 1
        category_totals[f.category] = category_totals.get(f.category, 0) + 1

    for r in reviews:
        upload_type = r.project.upload_type if r.project else "unknown"
        upload_type_totals[upload_type] = upload_type_totals.get(upload_type, 0) + 1
        score_trend.append({
            "review_id": r.id,
            "project_name": r.project.project_name if r.project else None,
            "score": r.review_score,
            "created_at": r.created_at.isoformat(),
        })

    avg_score = round(sum(r.review_score for r in reviews) / len(reviews), 2) if reviews else 0

    return jsonify({
        "total_reviews": len(reviews),
        "total_findings": len(findings),
        "avg_score": avg_score,
        "score_trend": score_trend,
        "severity_totals": severity_totals,
        "category_totals": category_totals,
        "upload_type_totals": upload_type_totals,
    }), 200


@review_bp.get("")
@jwt_required()
@current_user_required
def list_reviews(user):
    """Supports ?search=&min_score=&max_score=&upload_type=&sort=newest|oldest|score"""
    search = request.args.get("search", "").strip()
    min_score = request.args.get("min_score", type=float)
    max_score = request.args.get("max_score", type=float)
    upload_type = request.args.get("upload_type", "").strip()
    sort = request.args.get("sort", "newest")

    query = (
        db.session.query(Review)
        .join(Project, Review.project_id == Project.id)
        .filter(Project.user_id == user.id)
    )

    if search:
        query = query.filter(Project.project_name.ilike(f"%{search}%"))
    if min_score is not None:
        query = query.filter(Review.review_score >= min_score)
    if max_score is not None:
        query = query.filter(Review.review_score <= max_score)
    if upload_type:
        query = query.filter(Project.upload_type == upload_type)

    if sort == "oldest":
        query = query.order_by(Review.created_at.asc())
    elif sort == "score":
        query = query.order_by(Review.review_score.desc())
    else:
        query = query.order_by(Review.created_at.desc())

    reviews = query.all()
    return jsonify({"reviews": [r.to_dict() for r in reviews]}), 200


@review_bp.get("/compare")
@jwt_required()
@current_user_required
def compare_reviews(user):
    """?a=<review_id>&b=<review_id> — side-by-side diff of score/metrics/findings
    for two reviews owned by the current user."""
    a_id = request.args.get("a", type=int)
    b_id = request.args.get("b", type=int)
    if not a_id or not b_id:
        return jsonify({"error": "Both a and b review ids are required"}), 400
    if a_id == b_id:
        return jsonify({"error": "Choose two different reviews to compare"}), 400

    review_a = _get_owned_review(user, a_id)
    review_b = _get_owned_review(user, b_id)
    if not review_a or not review_b:
        return jsonify({"error": "One or both reviews were not found"}), 404

    def severity_counts(review):
        counts = {}
        for f in ReviewFinding.query.filter_by(review_id=review.id).all():
            counts[f.severity] = counts.get(f.severity, 0) + 1
        return counts

    metric_keys = [
        "total_lines_of_code", "num_functions", "num_classes",
        "average_cyclomatic_complexity", "maintainability_index", "average_function_length",
    ]
    metrics_diff = {}
    for key in metric_keys:
        val_a = review_a.metrics.get(key)
        val_b = review_b.metrics.get(key)
        delta = (val_b - val_a) if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)) else None
        metrics_diff[key] = {"a": val_a, "b": val_b, "delta": delta}

    return jsonify({
        "a": review_a.to_dict(include_findings=True),
        "b": review_b.to_dict(include_findings=True),
        "score_delta": round(review_b.review_score - review_a.review_score, 2),
        "metrics_diff": metrics_diff,
        "severity_counts": {"a": severity_counts(review_a), "b": severity_counts(review_b)},
    }), 200


@review_bp.get("/<int:review_id>")
@jwt_required()
@current_user_required
def get_review(user, review_id):
    review = _get_owned_review(user, review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    severity = request.args.get("severity", "").strip()
    findings_query = ReviewFinding.query.filter_by(review_id=review.id)
    if severity:
        findings_query = findings_query.filter(ReviewFinding.severity == severity)
    findings = findings_query.order_by(ReviewFinding.severity.asc()).all()

    data = review.to_dict()
    data["findings"] = [f.to_dict() for f in findings]
    return jsonify({"review": data}), 200


@review_bp.delete("/<int:review_id>")
@jwt_required()
@current_user_required
def delete_review(user, review_id):
    review = _get_owned_review(user, review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    project = review.project
    db.session.delete(review)
    # remove the project too if it has no other reviews (each upload = one project = one review)
    db.session.flush()
    if project and not project.reviews:
        db.session.delete(project)
    db.session.commit()
    return jsonify({"message": "Review deleted"}), 200


@review_bp.post("/<int:review_id>/refactor")
@jwt_required()
@current_user_required
def generate_refactor(user, review_id):
    """Generates (or regenerates) AI-refactored source code for this review's
    submitted file(s) and stores it on the Review row."""
    review = _get_owned_review(user, review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    source_files = review.source_files
    if not source_files:
        return jsonify({"error": "Original source code is not available for this review"}), 400

    # Reviews wrap one or more submitted files; concatenate for multi-file
    # projects so the AI sees full context, but keep the primary filename.
    primary_filename = source_files[0]["filename"]
    combined_source = "\n\n".join(
        f"# --- {f['filename']} ---\n{f['content']}" for f in source_files
    ) if len(source_files) > 1 else source_files[0]["content"]

    findings = [f.to_dict() for f in ReviewFinding.query.filter_by(review_id=review.id).all()]

    result = generate_refactored_code(combined_source, findings, primary_filename)

    review.refactored_code = result.get("refactored_code", combined_source)
    review.refactor_changes = result.get("changes", [])
    db.session.commit()

    return jsonify({
        "review_id": review.id,
        "refactored_code": review.refactored_code,
        "changes": review.refactor_changes,
    }), 200


@review_bp.get("/<int:review_id>/refactor")
@jwt_required()
@current_user_required
def get_refactor(user, review_id):
    """Fetches a previously generated refactor without regenerating it."""
    review = _get_owned_review(user, review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404

    if not review.refactored_code:
        return jsonify({"error": "No refactor has been generated for this review yet"}), 404

    return jsonify({
        "review_id": review.id,
        "refactored_code": review.refactored_code,
        "changes": review.refactor_changes,
    }), 200


def _get_owned_review(user, review_id):
    return (
        db.session.query(Review)
        .join(Project, Review.project_id == Project.id)
        .filter(Review.id == review_id, Project.user_id == user.id)
        .first()
    )
