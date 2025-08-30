from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.github import make_github_blueprint, github
from dotenv import load_dotenv
import os

load_dotenv()

from login_app import db, bcrypt
from login_app.models.user import User

auth_bp = Blueprint("auth", __name__)

google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    redirect_to="auth.google_login"
)

github_bp = make_github_blueprint(
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    redirect_to="auth.github_login"
)

# Página inicial
@auth_bp.route("/")
def home():
    return redirect(url_for("auth.login"))
    
# Login local
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username, provider="local").first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            return redirect(url_for("auth.dashboard"))
        else:
            flash("Credenciais inválidas.", "danger")

    return render_template("login.html")

# Registro de usuário local
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(username=username, provider="local").first()
        if existing_user:
            flash("Nome de usuário já existe. Por favor, escolha outro.", "danger")
            return redirect(url_for("auth.register"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Conta criada com sucesso! Faça login para continuar.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

# Login Google
@auth_bp.route("/login/google")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    info = resp.json()
    email = info["email"]

    user = User.query.filter_by(username=email, provider="google").first()
    if not user:
        user = User(username=email, provider="google", password_hash="oauth")
        db.session.add(user)
        db.session.commit()

    session["user_id"] = user.id
    flash(f"✅ Login Google bem-sucedido! Bem-vindo {email}", "success")
    return redirect(url_for("auth.dashboard"))

# Login GitHub
@auth_bp.route("/login/github")
def github_login():
    if not github.authorized:
        return redirect(url_for("github.login"))

    resp = github.get("/user")
    info = resp.json()
    username = info["login"]

    user = User.query.filter_by(username=username, provider="github").first()
    if not user:
        user = User(username=username, provider="github", password_hash="oauth")
        db.session.add(user)
        db.session.commit()

    session["user_id"] = user.id
    flash(f"✅ Login GitHub bem-sucedido! Bem-vindo {username}", "success")
    return redirect(url_for("auth.dashboard"))

# Dashboard
@auth_bp.route("/dashboard")
def dashboard():
    user = None
    if "user_id" in session:
        user = User.query.get(session["user_id"])
    return render_template("dashboard.html", user=user)

# Logout
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado com sucesso.", "success")
    return redirect(url_for("auth.login"))

