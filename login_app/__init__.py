# login_app/__init__.py
import os
from pathlib import Path
import time as _time

from flask import Flask, send_from_directory, make_response, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_mail import Mail
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.http import http_date, parse_date  # p/ ETag/Last-Modified
from .routes.news import news_bp
app.register_blueprint(news_bp)


# ==============================
# Extensões globais (única fonte)
# ==============================
db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
mail = Mail()

def create_app():
    app = Flask(__name__)

    # ==============================
    # Configuração base
    # ==============================
    # Certifique-se de que login_app/config.py tem a classe Config
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
    # Helper: resposta com cache (ETag/Last-Modified)
    # ==============================
    def cached_file_response(directory: str, filename: str):
        file_path = os.path.join(directory, filename)
        if not os.path.isfile(file_path):
            abort(404)

        st = os.stat(file_path)
        mtime = int(st.st_mtime)
        size = st.st_size

        # ETag fraca (suficiente p/ cache)
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
                # fallback: ignora erro de parse e segue servindo o arquivo
                pass

        # Entrega o arquivo normalmente
        resp = make_response(
            send_from_directory(directory, filename, as_attachment=False)
        )
        resp.headers["ETag"] = etag
        resp.headers["Last-Modified"] = last_modified
        resp.headers["Cache-Control"] = "public, max-age=604800, immutable"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp

    # ==============================
    # Rota de uploads com cache controlado
    # ==============================
    @app.route("/uploads/<path:filename>")
    def uploads(filename):
        upload_dir = app.config["UPLOAD_FOLDER"]
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

    # ==============================
    # CORS (apenas rotas /api/*)
    # ==============================
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ==============================
    # Models (para o Migrate enxergar)
    # ==============================
    with app.app_context():
        # ⚠️ IMPORT RELATIVO (dentro do pacote)
        from .models import user  # noqa: F401
        from .models import post  # noqa: F401

    # ==============================
    # Blueprints (imports RELATIVOS + registro seguro)
    # ==============================
    try:
        from .routes.auth import auth_bp, google_bp, github_bp
        app.register_blueprint(auth_bp)
        app.register_blueprint(google_bp, url_prefix="/oauth2/login")
        app.register_blueprint(github_bp, url_prefix="/oauth2/login")
    except Exception as e:
        app.logger.warning(f"[auth blueprints] não registrados: {e}")

    try:
        from .routes.posts_api import posts_api  # expõe /api/posts
        app.register_blueprint(posts_api)
    except Exception as e:
        app.logger.warning(f"[posts_api blueprint] não registrado: {e}")

    # 🔹 Blueprint de Notícias/RSS
    try:
        from .routes.news import news_bp  # /news, /buscar-chat, /rss, /api/rss, /assistente
        app.register_blueprint(news_bp)
    except Exception as e:
        app.logger.warning(f"[news blueprint] não registrado: {e}")

    # 🔹 (Opcional) Chat API, se existir
    try:
        from .chat_api import bp_chat
        app.register_blueprint(bp_chat, url_prefix="/api/chat")
    except Exception as e:
        app.logger.info(f"[chat_api] não registrado (opcional): {e}")

    # ==============================
    # uploads + (opcional) blueprint de mídia
    # ==============================
    app.config.setdefault("UPLOAD_DIR", "/data/uploads")
    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)

    # ==============================
    # Versionar assets nos templates a cada deploy
    # ==============================
    @app.context_processor
    def inject_version():
        # variável 'version' disponível em TODOS os templates
        return {"version": int(_time.time())}

    return app
