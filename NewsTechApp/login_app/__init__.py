import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_mail import Mail
from werkzeug.middleware.proxy_fix import ProxyFix
from pathlib import Path

# Extensões globais
db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
mail = Mail()  # ← Adicionando o suporte ao envio de e-mails

def create_app():
    app = Flask(__name__)

    # ==============================
    # ✉️ Configuração de upar e mostrar imagem
    # ==============================
    # Configurações básicas
     BASE_DIR = Path(__file__).resolve().parent
     app.config["UPLOAD_FOLDER"] = os.environ.get("UPLOAD_FOLDER") or str(BASE_DIR / "static" / "uploads")
     os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Rota para servir arquivos enviados (imagens)
    from flask import send_from_directory

    @app.route("/uploads/<path:filename>")
    def uploads(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # Importar e registrar Blueprints
    from login_app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    # Exemplo: registrar blueprint de posts se existir
    from login_app.routes.posts_api import posts_api
    app.register_blueprint(posts_api)  # sem url_prefix aqui

    
    # ==============================
    # 🔒 Corrigir redirecionamento HTTPS no Render
    # ==============================
    
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

    # === IMPORTAR MODELS (garante que as tabelas/binds sejam conhecidos) ===
    with app.app_context():
        from login_app.models import user     # noqa: F401
        from login_app.models import post     # noqa: F401  <-- Post usa __bind_key__ = "posts"
        # Se quiser criar tabelas no primeiro boot SEM migrations, descomente:
        # db.create_all()              # cria no banco principal (app.db)
        # db.create_all(bind="posts")  # cria no banco de postagens (posts.db)
    
    # Blueprints (rotas)
    from login_app.routes.auth import auth_bp, google_bp, github_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(google_bp, url_prefix="/oauth2/login")
    app.register_blueprint(github_bp, url_prefix="/oauth2/login")

    # === Blueprint da API de postagens (novo) ===
    from login_app.routes.posts_api import posts_api
    app.register_blueprint(posts_api)  # expõe /api/posts

    # === Fazer upload de imagens das postagens ===
    app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "/data/uploads")
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    return app
