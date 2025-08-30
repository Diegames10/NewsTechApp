import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.contrib.github import make_github_blueprint
from login_app.routes.auth import auth_bp, google_bp, github_bp
from .models.user import db, bcrypt
from login_app import create_app

#app = create_app()
def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "sua_chave_secreta")

    # Caminho do banco de dados persistente no Render
    db_path = os.getenv("DATABASE_PATH", "/data/users.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Inicializar extensões
    db.init_app(app)
    bcrypt.init_app(app)

    # Criar tabelas no primeiro start
    with app.app_context():
        db.create_all()

    # Registrar rotas e Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(google_bp, url_prefix="/login")
    app.register_blueprint(github_bp, url_prefix="/login")

    return app


app = create_app()

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
