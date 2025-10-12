import os
from flask import Flask
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.contrib.github import make_github_blueprint
from flask_migrate import upgrade
from werkzeug.middleware.proxy_fix import ProxyFix

# Importa as extensões centralizadas
from login_app.extensions import db, bcrypt, migrate, mail
from login_app.models import User


def create_app():
    app = Flask(__name__)

    # Forçar HTTPS no Render
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.config['PREFERRED_URL_SCHEME'] = 'https'

    # Configurações básicas
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev_secret_key")

    # Banco de dados persistente
    if os.environ.get("RENDER"):
        data_dir = "/data"
    else:
        data_dir = os.path.abspath(os.path.dirname(__file__))

    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(data_dir, 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Configurações de e-mail
    app.config['MAIL_SERVER'] = os.environ.get("MAIL_SERVER", "smtp-relay.brevo.com")
    app.config['MAIL_PORT'] = int(os.environ.get("MAIL_PORT", 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get("MAIL_DEFAULT_SENDER", "no-reply@newstechapp.com")

    # Inicializa extensões
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Importa e registra blueprints (autenticação e OAuth)
    from login_app.routes.auth import auth_bp, google_bp, github_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(google_bp, url_prefix="/logingoogle")
    app.register_blueprint(github_bp, url_prefix="/logingithub")

    # Criação automática do banco
    with app.app_context():
        db.create_all()
        print("Banco de dados inicializado em:", app.config['SQLALCHEMY_DATABASE_URI'])

    return app


# Instância global do app para o Gunicorn
app = create_app()


# Execução local (Render ignora)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
