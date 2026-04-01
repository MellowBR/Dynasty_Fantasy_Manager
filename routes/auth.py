"""
routes/auth.py — Google OAuth + Flask-Login authentication.

Blueprint: auth_bp
Routes: /login, /logout, /auth/callback
"""

import os
from functools import wraps
from flask import Blueprint, redirect, url_for, render_template, request, jsonify, flash
from flask_login import login_user, logout_user, current_user, login_required
from authlib.integrations.flask_client import OAuth
from models import db, User

auth_bp = Blueprint("auth", __name__)

# OAuth is initialized in init_auth() called from app.py
oauth = OAuth()


def init_auth(app):
    """Initialize OAuth and LoginManager on the Flask app."""
    from flask_login import LoginManager

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/api/"):
            return jsonify({"error": "unauthorized", "status": 401}), 401
        return redirect(url_for("auth.login_page"))

    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


# ── Routes ──────────────────────────────────────────────────────────────────


@auth_bp.route("/login")
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("roster.index"))
    return render_template("login.html")


@auth_bp.route("/login/google")
def login_google():
    redirect_uri = url_for("auth.auth_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/auth/callback")
def auth_callback():
    token = oauth.google.authorize_access_token()
    user_info = token.get("userinfo")
    if not user_info:
        user_info = oauth.google.userinfo()

    email = user_info.get("email", "").lower().strip()
    if not email:
        return render_template("error.html", code=401,
                               message="Não foi possível obter seu email do Google."), 401

    user = User.query.filter_by(email=email).first()
    if not user:
        return render_template("error.html", code=403,
                               message="Acesso não autorizado. Seu email não está cadastrado "
                                       "na liga Dynasty SB. Fale com o administrador."), 403

    # Update name from Google profile if not set
    if not user.name and user_info.get("name"):
        user.name = user_info["name"]
        db.session.commit()

    login_user(user, remember=True)
    next_page = request.args.get("next", url_for("roster.index"))
    return redirect(next_page)


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login_page"))


# ── Admin decorator ─────────────────────────────────────────────────────────


def admin_required(f):
    """Decorator: requires authenticated user with is_admin=True."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            if request.path.startswith("/api/"):
                return jsonify({"error": "forbidden", "status": 403}), 403
            return render_template("error.html", code=403,
                                   message="Acesso restrito ao administrador."), 403
        return f(*args, **kwargs)
    return decorated
