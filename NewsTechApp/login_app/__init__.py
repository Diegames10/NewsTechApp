from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
import os

# Inicializar extensões
db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Configurações do banco de dados
    # No Render, usar o disco persistente montado em /data
    data_dir = "/data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    
    db_path = os.path.join(data_dir, "app.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "supersecret")
    
    # Inicializar extensões com a app
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    # Registrar blueprints
    from login_app.routes.auth import auth_bp, google_bp, github_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(google_bp, url_prefix="/login")
    app.register_blueprint(github_bp, url_prefix="/login")

    # Criar tabelas se não existirem
    with app.app_context():
        db.create_all()

    return app

