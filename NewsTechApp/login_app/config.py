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
