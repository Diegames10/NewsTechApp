import os
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, session
)
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.github import make_github_blueprint, github
from werkzeug.security import generate_password_hash, check_password_hash
from login_app import db
from login_app.models.user import User

# =====================================================
# 🔹 Blueprint principal
# =====================================================
auth_bp = Blueprint("auth", __name__)

# =====================================================
# 🔹 Google OAuth2
# =====================================================
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    redirect_to="auth.google_authorized",
    scope=["profile", "email"]
)

# =====================================================
# 🔹 GitHub OAuth2
# =====================================================
github_bp = make_github_blueprint(
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    redirect_to="auth.github_authorized"
)

# =====================================================
# 🔹 Rotas locais
# =====================================================

@auth_bp.route("/")
def home():
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username, provider="local").first()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("auth.dashboard"))
        else:
            flash("Usuário ou senha inválidos!", "danger")
            return redirect(url_for("auth.login"))

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("Nome de usuário já existe!", "warning")
            return redirect(url_for("auth.register"))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_pw, provider="local")
        db.session.add(new_user)
        db.session.commit()
        flash("Conta criada com sucesso! Faça login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Faça login para acessar o painel.", "warning")
        return redirect(url_for("auth.login"))
    return render_template("dashboard.html", username=session.get("username"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado com sucesso!", "info")
    return redirect(url_for("auth.login"))


# =====================================================
# 🔹 Login com Google
# =====================================================
@auth_bp.route("/oauth2/login/google/authorized")
def google_authorized():
    if not google.authorized:
        flash("Falha na autorização com Google.", "danger")
        return redirect(url_for("auth.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Erro ao obter informações do Google.", "danger")
        return redirect(url_for("auth.login"))

    info = resp.json()
    email = info["email"]
    username = info.get("name", email.split("@")[0])

    user = User.query.filter_by(email=email, provider="google").first()
    if not user:
        user = User(username=username, email=email, password_hash="oauth", provider="google")
        db.session.add(user)
        db.session.commit()

    session["user_id"] = user.id
    session["username"] = user.username
    flash(f"Bem-vindo, {user.username} (Google)!", "success")
    return redirect(url_for("auth.dashboard"))


# =====================================================
# 🔹 Login com GitHub
# =====================================================
@auth_bp.route("/oauth2/login/github/authorized")
def github_authorized():
    if not github.authorized:
        flash("Falha na autorização com GitHub.", "danger")
        return redirect(url_for("auth.login"))

    resp = github.get("/user")
    if not resp.ok:
        flash("Erro ao obter informações do GitHub.", "danger")
        return redirect(url_for("auth.login"))

    info = resp.json()
    username = info["login"]
    email = info.get("email") or f"{username}@github.com"  # fallback se GitHub não retornar email

    user = User.query.filter_by(username=username, provider="github").first()
    if not user:
        user = User(username=username, email=email, password_hash="oauth", provider="github")
        db.session.add(user)
        db.session.commit()

    session["user_id"] = user.id
    session["username"] = user.username
    flash(f"Bem-vindo, {user.username} (GitHub)!", "success")
    return redirect(url_for("auth.dashboard"))


# =====================================================
# 🔹 Recuperar senha
# =====================================================
@auth_bp.route("/reset_request", methods=["GET", "POST"])
def reset_request():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email, provider="local").first()

        if user:
            flash("Link de redefinição enviado (simulado).", "info")
        else:
            flash("Email não encontrado.", "warning")

        return redirect(url_for("auth.login"))

    return render_template("reset_request.html")


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    # Placeholder: aqui ficaria a validação real de token
    if request.method == "POST":
        new_pw = request.form.get("password")
        email = request.form.get("email")

        user = User.query.filter_by(email=email, provider="local").first()
        if user:
            user.password_hash = generate_password_hash(new_pw)
            db.session.commit()
            flash("Senha atualizada com sucesso!", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("Usuário não encontrado.", "danger")

    return render_template("reset_password.html", token=token)
