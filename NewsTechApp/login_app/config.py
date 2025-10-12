class Config:
    SECRET_KEY = "uma_chave_secreta_aqui"
    SQLALCHEMY_DATABASE_URI = "sqlite:////data/app.db"  # caminho absoluto no disco persistente
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuração de e-mail (Brevo)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp-relay.brevo.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "NewsTechApp <no-reply@newstechapp.com>")
