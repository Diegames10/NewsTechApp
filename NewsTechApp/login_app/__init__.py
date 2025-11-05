# login_app/__init__.py
import os
from pathlib import Path

from flask import Flask, send_from_directory, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_mail import Mail
from werkzeug.middleware.proxy_fix import ProxyFix



# Extensões globais
db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
mail = Mail()  # suporte a e-mails

def create_app():
    app = Flask(__name__)

    # ==============================
    # Configuração base
    # ==============================
    app.config.from_object("login_app.config.Config")

    # HTTPS correto atrás de proxy (Render)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.config["PREFERRED_URL_SCHEME"] = "https"

    # ==============================
    # Uploads (Render usa /data persistente)
    # ==============================    
    app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "/data/uploads")
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    @app.route("/uploads/<path:filename>")
    def uploads(filename):
        return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
        
    @app.context_processor
    def inject_current_user():
        from flask import session  # <- importa aqui
        return {
        "current_user_id": session.get("user_id"),
        "current_user_name": session.get("user_name"),
        "is_authenticated": bool(session.get("user_id")),
        }
    # ==============================
    # SMTP (Brevo)
    # ==============================
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp-relay.brevo.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

    # ==============================
    # Inicialização das extensões
    # ==============================
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Models (para o Migrate enxergar)
    with app.app_context():
        from login_app.models import user  # noqa: F401
        from login_app.models import post  # noqa: F401

    # ==============================
    # Blueprints
    # ==============================
    from login_app.routes.auth import auth_bp, google_bp, github_bp
    from login_app.routes.posts_api import posts_api  # arquivo: posts_api.py ; variável: posts_api

    app.register_blueprint(auth_bp)
    app.register_blueprint(google_bp, url_prefix="/oauth2/login")
    app.register_blueprint(github_bp, url_prefix="/oauth2/login")
    app.register_blueprint(posts_api)  # expõe /api/posts

    return app
