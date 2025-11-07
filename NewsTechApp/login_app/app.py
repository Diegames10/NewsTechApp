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

from login_app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

