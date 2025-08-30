import os
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.contrib.github import make_github_blueprint

# Inicializar extensões **sem redeclarar depois**
db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()

# Importar blueprints **depois de criar as extensões**
from login_app.routes.auth import auth_bp, google_bp, github_bp

def create_app():
    app = Flask(__name__)

    # Configurações do banco de dados
    # No Render, usar o disco persistente montado em /data
    data_dir = "/data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    
    db_path = os.path.join(data_dir, "app.db")
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "supersecret")

    # Inicializar extensões com a app
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(google_bp, url_prefix="/login")
    app.register_blueprint(github_bp, url_prefix="/login")

    # Criar tabelas se não existirem
    with app.app_context():
        db.create_all()

    return app

# Instância da app para WSGI/Gunicorn
app = create_app()

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
