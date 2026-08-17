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
    # MAN-AUTH1 (metade A): sem `prompt`, o Google reusa a sessão ativa do navegador e
    # autentica em SILÊNCIO — quem tem outra conta logada (a do trabalho, por exemplo)
    # nunca chega a ver o seletor e cai direto no 403. `select_account` força a escolha.
    # ⛔ Custo medido na F1: só o caminho FRIO paga o clique extra — o owner recorrente
    # entra pelo cookie `remember` (365d) e nem passa por aqui.
    return oauth.google.authorize_redirect(redirect_uri, prompt="select_account")


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
        # MAN-AUTH1 (metade C): o 403 genérico não dizia QUAL conta foi rejeitada e não
        # oferecia saída — a única frase acionável ("fale com o administrador") apontava o
        # remédio errado para o caso comum (a conta certa existe; o navegador é que entrou
        # com outra). Template próprio: o error.html segue servindo 404/500 e o admin_required.
        return render_template("login_denied.html", email=email), 403

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
