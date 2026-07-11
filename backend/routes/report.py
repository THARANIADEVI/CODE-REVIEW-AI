from flask import Blueprint, jsonify, Response, send_file
from flask_jwt_extended import jwt_required
import io

from extensions import db
from models import Review, Project, ReviewFinding
from utils.decorators import current_user_required
from services.report_service import build_markdown, build_html, build_pdf

report_bp = Blueprint("report", __name__)


def _get_owned_review(user, review_id):
    return (
        db.session.query(Review)
        .join(Project, Review.project_id == Project.id)
        .filter(Review.id == review_id, Project.user_id == user.id)
        .first()
    )


@report_bp.get("/<int:review_id>/markdown")
@jwt_required()
@current_user_required
def export_markdown(user, review_id):
    review = _get_owned_review(user, review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404
    findings = ReviewFinding.query.filter_by(review_id=review.id).all()
    content = build_markdown(review, findings)
    return Response(
        content, mimetype="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=review_{review_id}.md"},
    )


@report_bp.get("/<int:review_id>/html")
@jwt_required()
@current_user_required
def export_html(user, review_id):
    review = _get_owned_review(user, review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404
    findings = ReviewFinding.query.filter_by(review_id=review.id).all()
    content = build_html(review, findings)
    return Response(
        content, mimetype="text/html",
        headers={"Content-Disposition": f"attachment; filename=review_{review_id}.html"},
    )


@report_bp.get("/<int:review_id>/pdf")
@jwt_required()
@current_user_required
def export_pdf(user, review_id):
    review = _get_owned_review(user, review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404
    findings = ReviewFinding.query.filter_by(review_id=review.id).all()
    pdf_bytes = build_pdf(review, findings)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"review_{review_id}.pdf",
    )
