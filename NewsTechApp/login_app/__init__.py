from flask import Flask
from .config import Config
from .extensions import db, bcrypt, migrate
from .routes.auth import auth_bp, google_bp, github_bp

def create_app():
    app = Flask(__name__)
    
    app.config.from_object(Config)  # Carrega as configurações
    
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(google_bp, url_prefix="/login/google")
    app.register_blueprint(github_bp, url_prefix="/login/github")

    return app
