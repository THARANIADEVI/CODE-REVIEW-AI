import secrets
from urllib.parse import urlencode

import requests
from flask import Blueprint, current_app, redirect, request
from flask_jwt_extended import create_access_token

from extensions import db
from models import User

oauth_bp = Blueprint("oauth", __name__)

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_USER_URL = "https://api.github.com/user"
GITHUB_API_EMAILS_URL = "https://api.github.com/user/emails"

STATE_COOKIE_NAME = "github_oauth_state"


@oauth_bp.get("/github/login")
def github_login():
    state = secrets.token_urlsafe(32)

    params = {
        "client_id": current_app.config["GITHUB_CLIENT_ID"],
        "redirect_uri": current_app.config["GITHUB_OAUTH_REDIRECT_URI"],
        "scope": "user:email",
        "state": state,
    }
    authorize_url = f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"

    response = redirect(authorize_url)
    # Short-lived, httponly cookie holds the state so we can compare it against
    # what GitHub echoes back on the callback (basic CSRF protection).
    response.set_cookie(
        STATE_COOKIE_NAME,
        state,
        max_age=600,
        httponly=True,
        secure=request.is_secure,
        samesite="Lax",
    )
    return response


@oauth_bp.get("/github/callback")
def github_callback():
    frontend_url = current_app.config["FRONTEND_URL"]
    failure_redirect = redirect(f"{frontend_url}/login?error=oauth_failed")

    code = request.args.get("code")
    state = request.args.get("state")
    cookie_state = request.cookies.get(STATE_COOKIE_NAME)

    if not code or not state or not cookie_state or not secrets.compare_digest(state, cookie_state):
        return failure_redirect

    try:
        token_resp = requests.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": current_app.config["GITHUB_CLIENT_ID"],
                "client_secret": current_app.config["GITHUB_CLIENT_SECRET"],
                "code": code,
                "redirect_uri": current_app.config["GITHUB_OAUTH_REDIRECT_URI"],
            },
            timeout=15,
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("No access_token in GitHub response")

        auth_headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        }
        user_resp = requests.get(GITHUB_API_USER_URL, headers=auth_headers, timeout=15)
        user_resp.raise_for_status()
        github_user = user_resp.json()

        emails_resp = requests.get(GITHUB_API_EMAILS_URL, headers=auth_headers, timeout=15)
        emails_resp.raise_for_status()
        emails = emails_resp.json()
    except Exception:
        current_app.logger.warning("GitHub OAuth exchange failed", exc_info=True)
        return failure_redirect

    primary_email = next(
        (e["email"] for e in emails if e.get("primary") and e.get("verified")),
        None,
    ) or next((e["email"] for e in emails if e.get("verified")), None)

    if not primary_email:
        current_app.logger.warning("GitHub OAuth: no verified email available")
        return failure_redirect

    github_id = str(github_user.get("id"))
    name = github_user.get("name") or github_user.get("login") or "GitHub User"
    avatar_url = github_user.get("avatar_url")

    user = User.query.filter_by(github_id=github_id).first()
    if not user:
        user = User.query.filter_by(email=primary_email.lower()).first()

    if user:
        user.github_id = github_id
        user.avatar_url = avatar_url
    else:
        user = User(
            name=name,
            email=primary_email.lower(),
            github_id=github_id,
            avatar_url=avatar_url,
        )

    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))

    response = redirect(f"{frontend_url}/oauth/callback?token={token}")
    response.delete_cookie(STATE_COOKIE_NAME)
    return response
