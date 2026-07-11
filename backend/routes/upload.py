from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from extensions import db
from models import Project
from utils.decorators import current_user_required
from utils.file_utils import is_allowed_file, is_ignored_path
from services.analysis_pipeline import analyze_files
from services.github_service import fetch_repo_files, GitHubFetchError

upload_bp = Blueprint("upload", __name__)

MAX_FILES = 25
MAX_SNIPPET_SIZE = 200_000


@upload_bp.post("/files")
@jwt_required()
@current_user_required
def upload_files(user):
    """multipart/form-data upload of one or more source files."""
    uploaded = request.files.getlist("files")
    project_name = request.form.get("project_name") or "Untitled Upload"

    if not uploaded:
        return jsonify({"error": "No files provided"}), 400

    files_payload = []
    skipped = []
    for f in uploaded[:MAX_FILES]:
        filename = f.filename or ""
        if not filename or is_ignored_path(filename) or not is_allowed_file(filename):
            skipped.append(filename)
            continue
        content = f.read().decode("utf-8", errors="ignore")
        files_payload.append({"filename": filename, "content": content})

    if not files_payload:
        return jsonify({"error": "No supported source files found", "skipped": skipped}), 400

    project = Project(user_id=user.id, project_name=project_name, upload_type="file")
    db.session.add(project)
    db.session.commit()

    review = analyze_files(project, files_payload)
    return jsonify({
        "project": project.to_dict(),
        "review": review.to_dict(include_findings=True),
        "skipped": skipped,
    }), 201


@upload_bp.post("/snippet")
@jwt_required()
@current_user_required
def upload_snippet(user):
    """JSON body: { project_name, filename, code }"""
    data = request.get_json(silent=True) or {}
    project_name = (data.get("project_name") or "Untitled Snippet").strip()
    filename = (data.get("filename") or "snippet.py").strip()
    code = data.get("code") or ""

    if not code.strip():
        return jsonify({"error": "code is required"}), 400
    if len(code) > MAX_SNIPPET_SIZE:
        return jsonify({"error": "Snippet too large"}), 400
    if not is_allowed_file(filename):
        return jsonify({"error": "Unsupported file type"}), 400

    project = Project(user_id=user.id, project_name=project_name, upload_type="snippet")
    db.session.add(project)
    db.session.commit()

    review = analyze_files(project, [{"filename": filename, "content": code}])
    return jsonify({
        "project": project.to_dict(),
        "review": review.to_dict(include_findings=True),
    }), 201


@upload_bp.post("/github")
@jwt_required()
@current_user_required
def upload_github(user):
    """JSON body: { repo_url }. Public repos only, no auth required."""
    data = request.get_json(silent=True) or {}
    repo_url = (data.get("repo_url") or "").strip()
    if not repo_url:
        return jsonify({"error": "repo_url is required"}), 400

    try:
        files_payload = fetch_repo_files(repo_url)
    except GitHubFetchError as e:
        return jsonify({"error": str(e)}), 400

    project_name = repo_url.rstrip("/").split("/")[-1] or "GitHub Repository"
    project = Project(user_id=user.id, project_name=project_name, upload_type="github")
    db.session.add(project)
    db.session.commit()

    review = analyze_files(project, files_payload)
    return jsonify({
        "project": project.to_dict(),
        "review": review.to_dict(include_findings=True),
        "files_analyzed": [f["filename"] for f in files_payload],
    }), 201
