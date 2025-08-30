import os
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.contrib.github import make_github_blueprint
from login_app.routes.auth import auth_bp, google_bp, github_bp
from .models.user import db, bcrypt
from login_app import create_app

db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()  # <-- adiciona isso

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = "secreta"

    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)  # <-- inicializa o migrate


    # Registrar rotas e Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(google_bp, url_prefix="/login")
    app.register_blueprint(github_bp, url_prefix="/login")

    return app


app = create_app()

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
