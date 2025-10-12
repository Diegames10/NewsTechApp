from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from werkzeug.middleware.proxy_fix import ProxyFix
import os

# Extensões globais
db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Corrige HTTPS no Render
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////data/app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "changeme")

    # Inicializa extensões
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    # Importa e registra Blueprints
    from login_app.routes.auth import auth_bp, google_bp, github_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(google_bp, url_prefix="/oauth2/login/google")
    app.register_blueprint(github_bp, url_prefix="/oauth2/login/github")

    return app
