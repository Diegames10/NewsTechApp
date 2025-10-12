import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_mail import Mail
from werkzeug.middleware.proxy_fix import ProxyFix

# Extensões globais
db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
mail = Mail()  # ← Adicionando o suporte ao envio de e-mails

def create_app():
    app = Flask(__name__)
    
    # 🔒 Corrigir redirecionamento HTTPS no Render
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config.from_object("login_app.config.Config")

    # ==============================
    # ✉️ Configuração do Brevo (SMTP)
    # ==============================
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp-relay.brevo.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")  # seu login Brevo
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")  # sua chave SMTP
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")  # e-mail do remetente
    # ==============================

    # Inicialização das extensões
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)  # ← Inicializa o envio de e-mails

    # Blueprints (rotas)
    from login_app.routes.auth import auth_bp, google_bp, github_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(google_bp, url_prefix="/oauth2/login")
    app.register_blueprint(github_bp, url_prefix="/oauth2/login")

    return app
