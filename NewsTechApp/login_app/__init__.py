# login_app/__init__.py
import os
from pathlib import Path

from flask import Flask, send_from_directory, make_response, request
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

    # ==============================
    # Uploads (rota com cache controlado)
    # ==============================
    @app.route("/uploads/<path:filename>")
    def uploads(filename):
        # envia o arquivo normalmente
        resp = make_response(
            send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=False)
        )
        # permite cache local por 7 dias e reuso ao voltar no navegador
        resp.headers["Cache-Control"] = "public, max-age=604800, immutable"
        resp.headers["Access-Control-Allow-Origin"] = "*"  # evita bloqueio CORS
        return cached_file_response(upload_dir, filename)

    @app.after_request
    def add_header(resp):
        # não interfere nas imagens nem em arquivos estáticos
        if request.path.startswith("/uploads/") or request.path.startswith("/static/"):
            return resp
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp

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

    # ==============================
    # === uploads no disco persistente + blueprint de mídia ===
    # ==============================
    app.config.setdefault("UPLOAD_DIR", "/data/uploads")
    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)

    #from login_app.routes.media import media_bp
    #app.register_blueprint(media_bp)

    # ==============================
    # === VERSIONA AS TEMPLATES CADA VEZ QUE FAZ DEPLOY ===
    # ==============================
    import time as _time

    @app.context_processor
    def inject_version():
        # variável 'version' disponível em TODOS os templates
        return {"version": int(_time.time())}

    def cached_file_response(directory: str, filename: str):
    file_path = os.path.join(directory, filename)
    if not os.path.isfile(file_path):
        abort(404)

    st = os.stat(file_path)
    mtime = int(st.st_mtime)
    size  = st.st_size

    # ETag fraca (leve e suficiente para cache)
    etag = f'W/"{size:x}-{mtime:x}"'
    last_modified = http_date(mtime)

    # Condicionais do cliente
    inm = request.headers.get("If-None-Match")
    ims = request.headers.get("If-Modified-Since")

    # Valida ETag primeiro
    if inm and etag in inm:
        resp = make_response("", 304)
        resp.headers["ETag"] = etag
        resp.headers["Last-Modified"] = last_modified
        resp.headers["Cache-Control"] = "public, max-age=604800, immutable"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp

    # Depois valida Last-Modified
    if ims:
        try:
            ims_dt = parse_date(ims)
            if ims_dt and int(ims_dt.timestamp()) >= mtime:
                resp = make_response("", 304)
                resp.headers["ETag"] = etag
                resp.headers["Last-Modified"] = last_modified
                resp.headers["Cache-Control"] = "public, max-age=604800, immutable"
                resp.headers["Access-Control-Allow-Origin"] = "*"
                return resp
        except Exception:
            pass  # se algo der errado, segue servindo o arquivo

    # Entrega o arquivo normalmente
    resp = make_response(send_from_directory(directory, filename, as_attachment=False))
    resp.headers["ETag"] = etag
    resp.headers["Last-Modified"] = last_modified
    resp.headers["Cache-Control"] = "public, max-age=604800, immutable"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

    return app
