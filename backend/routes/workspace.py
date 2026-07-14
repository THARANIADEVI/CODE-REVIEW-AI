from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from extensions import db
from models import User, Project, Workspace, WorkspaceMember
from utils.decorators import current_user_required

workspace_bp = Blueprint("workspace", __name__)


@workspace_bp.post("")
@jwt_required()
@current_user_required
def create_workspace(user):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    workspace = Workspace(name=name, owner_id=user.id)
    db.session.add(workspace)
    db.session.flush()

    member = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner")
    db.session.add(member)
    db.session.commit()

    return jsonify({"workspace": workspace.to_dict()}), 201


@workspace_bp.get("")
@jwt_required()
@current_user_required
def list_workspaces(user):
    workspaces = (
        db.session.query(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .filter(WorkspaceMember.user_id == user.id)
        .order_by(Workspace.created_at.desc())
        .all()
    )

    result = []
    for w in workspaces:
        data = w.to_dict()
        data["member_count"] = WorkspaceMember.query.filter_by(workspace_id=w.id).count()
        result.append(data)

    return jsonify({"workspaces": result}), 200


@workspace_bp.get("/<int:workspace_id>")
@jwt_required()
@current_user_required
def get_workspace(user, workspace_id):
    workspace = Workspace.query.get(workspace_id)
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    membership = _get_membership(workspace_id, user.id)
    if not membership:
        return jsonify({"error": "You are not a member of this workspace"}), 403

    members = WorkspaceMember.query.filter_by(workspace_id=workspace_id).all()

    data = workspace.to_dict()
    data["members"] = [m.to_dict() for m in members]
    return jsonify({"workspace": data}), 200


@workspace_bp.post("/<int:workspace_id>/members")
@jwt_required()
@current_user_required
def invite_member(user, workspace_id):
    workspace = Workspace.query.get(workspace_id)
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    membership = _get_membership(workspace_id, user.id)
    if not membership:
        return jsonify({"error": "You are not a member of this workspace"}), 403
    if membership.role not in ("owner", "admin"):
        return jsonify({"error": "Only workspace owners or admins can invite members"}), 403

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "email is required"}), 400

    invitee = User.query.filter_by(email=email).first()
    if not invitee:
        return jsonify({"error": "User not found"}), 404

    if _get_membership(workspace_id, invitee.id):
        return jsonify({"error": "User is already a member of this workspace"}), 409

    new_member = WorkspaceMember(workspace_id=workspace_id, user_id=invitee.id, role="member")
    db.session.add(new_member)
    db.session.commit()

    return jsonify({"member": new_member.to_dict()}), 201


@workspace_bp.delete("/<int:workspace_id>/members/<int:member_user_id>")
@jwt_required()
@current_user_required
def remove_member(user, workspace_id, member_user_id):
    workspace = Workspace.query.get(workspace_id)
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    membership = _get_membership(workspace_id, user.id)
    if not membership:
        return jsonify({"error": "You are not a member of this workspace"}), 403

    target_membership = _get_membership(workspace_id, member_user_id)
    if not target_membership:
        return jsonify({"error": "Member not found"}), 404

    is_self = member_user_id == user.id
    if not is_self and membership.role not in ("owner", "admin"):
        return jsonify({"error": "Only workspace owners or admins can remove members"}), 403

    if target_membership.role == "owner":
        return jsonify({"error": "The workspace owner cannot be removed"}), 400

    db.session.delete(target_membership)
    db.session.commit()

    return jsonify({"message": "Member removed"}), 200


@workspace_bp.get("/<int:workspace_id>/projects")
@jwt_required()
@current_user_required
def list_workspace_projects(user, workspace_id):
    workspace = Workspace.query.get(workspace_id)
    if not workspace:
        return jsonify({"error": "Workspace not found"}), 404

    membership = _get_membership(workspace_id, user.id)
    if not membership:
        return jsonify({"error": "You are not a member of this workspace"}), 403

    projects = (
        Project.query.filter_by(workspace_id=workspace_id)
        .order_by(Project.created_at.desc())
        .all()
    )

    result = []
    for p in projects:
        data = p.to_dict()
        data["reviews"] = [{"id": r.id} for r in p.reviews]
        result.append(data)

    return jsonify({"projects": result}), 200


@workspace_bp.patch("/projects/<int:project_id>")
@jwt_required()
@current_user_required
def move_project(user, project_id):
    project = Project.query.filter_by(id=project_id, user_id=user.id).first()
    if not project:
        return jsonify({"error": "Project not found"}), 404

    data = request.get_json(silent=True) or {}
    if "workspace_id" not in data:
        return jsonify({"error": "workspace_id is required"}), 400

    workspace_id = data.get("workspace_id")
    if workspace_id is not None:
        workspace = Workspace.query.get(workspace_id)
        if not workspace:
            return jsonify({"error": "Workspace not found"}), 404
        if not _get_membership(workspace_id, user.id):
            return jsonify({"error": "You are not a member of this workspace"}), 403

    project.workspace_id = workspace_id
    db.session.commit()

    return jsonify({"project": project.to_dict()}), 200


def _get_membership(workspace_id, user_id):
    return WorkspaceMember.query.filter_by(workspace_id=workspace_id, user_id=user_id).first()
