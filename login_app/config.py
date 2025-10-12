class Config:
    SECRET_KEY = "uma_chave_secreta_aqui"
    SQLALCHEMY_DATABASE_URI = "sqlite:////data/app.db"  # caminho absoluto no disco persistente
    SQLALCHEMY_TRACK_MODIFICATIONS = False
