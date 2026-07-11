from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from extensions import db
from models import Review, Project, ReviewFinding
from utils.decorators import current_user_required

review_bp = Blueprint("review", __name__)


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


def _get_owned_review(user, review_id):
    return (
        db.session.query(Review)
        .join(Project, Review.project_id == Project.id)
        .filter(Review.id == review_id, Project.user_id == user.id)
        .first()
    )
