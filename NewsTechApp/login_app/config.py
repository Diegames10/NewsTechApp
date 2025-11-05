
import os

class Config:
   SECRET_KEY = os.getenv("SECRET_KEY", "troque-este-segredo-em-producao")

    # Banco principal (usuários etc.)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:////data/app.db")

    # Banco de postagens (bind)
    SQLALCHEMY_BINDS = {
        "posts": os.getenv("POSTS_DATABASE_URL", "sqlite:////data/posts.db")
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads no disco persistente do Render
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/data/uploads")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT (PyJWT manual)
    JWT_SECRET = os.getenv("JWT_SECRET", "troque-por-um-segredo-diferente-do-SECRET_KEY")
    JWT_ALG = os.getenv("JWT_ALG", "HS256")
    JWT_ACCESS_EXPIRES = int(os.getenv("JWT_ACCESS_EXPIRES", "900"))       # 15 min
    JWT_REFRESH_EXPIRES = int(os.getenv("JWT_REFRESH_EXPIRES", "2592000")) # 30 dias

    # Cookies para JWT
    JWT_COOKIE_SECURE = os.getenv("JWT_COOKIE_SECURE", "true").lower() == "true"
    JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "Lax")  # Lax/Strict/None
    JWT_ACCESS_COOKIE_NAME = os.getenv("JWT_ACCESS_COOKIE_NAME", "access_token")
    JWT_REFRESH_COOKIE_NAME = os.getenv("JWT_REFRESH_COOKIE_NAME", "refresh_token")
    CSRF_COOKIE_NAME = os.getenv("CSRF_COOKIE_NAME", "csrf_token")

    # Sessão (mantemos por compatibilidade)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "true").lower() == "true"
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")

    # Preferir HTTPS em URLs externas
    PREFERRED_URL_SCHEME = "https"

class Config:
    # chave secreta do Flask
    SECRET_KEY = "uma_chave_secreta_aqui"

    # banco principal (usuários, autenticação)
    SQLALCHEMY_DATABASE_URI = "sqlite:////data/app.db"  # caminho absoluto no disco persistente

    # segundo banco (postagens)
    POSTS_DATABASE_URI = "sqlite:////data/posts.db"

    # dicionário de binds: o SQLAlchemy usa isso para identificar o segundo banco
    SQLALCHEMY_BINDS = {
        "posts": POSTS_DATABASE_URI
    }

    # configurações gerais
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "troque-por-um-segredo-diferente-do-SECRET_KEY")
    JWT_ALG = "HS256"
    JWT_ACCESS_EXPIRES = int(os.getenv("JWT_ACCESS_EXPIRES", 15 * 60))         # 15 min (segundos)
    JWT_REFRESH_EXPIRES = int(os.getenv("JWT_REFRESH_EXPIRES", 30 * 24 * 3600))# 30 dias (segundos)

    # Cookies seguros (Render é HTTPS)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Para os cookies de JWT
    COOKIE_SECURE = True
    COOKIE_SAMESITE = "Lax"
    COOKIE_DOMAIN = None  # deixe None; Render define domínio. Ajuste se usar subdomínios.
