from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from models import User


def current_user_required(fn):
    """Loads current user from JWT identity, 404s if missing."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        if not user:
            return jsonify({"error": "User not found"}), 404
        return fn(user, *args, **kwargs)

    return wrapper
