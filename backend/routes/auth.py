import re
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from extensions import db
from models import User
from utils.decorators import current_user_required

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 200


@auth_bp.post("/logout")
@jwt_required()
def logout():
    # Stateless JWT: client discards the token. Endpoint kept for API symmetry / future blacklist.
    return jsonify({"message": "Logged out"}), 200


@auth_bp.post("/reset-password")
@jwt_required()
@current_user_required
def reset_password(user):
    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""

    if not user.check_password(current_password):
        return jsonify({"error": "Current password is incorrect"}), 401
    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    user.set_password(new_password)
    db.session.commit()
    return jsonify({"message": "Password updated"}), 200


@auth_bp.get("/profile")
@jwt_required()
@current_user_required
def get_profile(user):
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.put("/profile")
@jwt_required()
@current_user_required
def update_profile(user):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()

    if name:
        user.name = name
    if email:
        if not EMAIL_RE.match(email):
            return jsonify({"error": "Invalid email"}), 400
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != user.id:
            return jsonify({"error": "Email already in use"}), 409
        user.email = email

    db.session.commit()
    return jsonify({"user": user.to_dict()}), 200
