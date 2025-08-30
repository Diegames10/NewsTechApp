from flask import Blueprint, redirect, url_for
from flask_dance.contrib.google import google
from flask_dance.contrib.github import github

oauth_bp = Blueprint("oauth", __name__)

@oauth_bp.route("/oauth2/login/google")
def google_login():
    """Inicia o processo de autenticação com Google"""
    return redirect(url_for("google.login"))

@oauth_bp.route("/oauth2/login/github") 
def github_login():
    """Inicia o processo de autenticação com GitHub"""
    return redirect(url_for("github.login"))

