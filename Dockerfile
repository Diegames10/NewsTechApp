# Dockerfile (na raiz do repo)
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev libssl-dev libpq-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Se o requirements.txt está em login_app/
COPY /requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    SQLALCHEMY_DATABASE_URI=sqlite:////data/app.db \
    UPLOAD_FOLDER=/data/uploads \
    PREFERRED_URL_SCHEME=https
# Copia o projeto inteiro
COPY . /app

# Garantir permissão do start.sh
RUN chmod +x /app/start.sh

ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=wsgi.py

EXPOSE 8080

CMD ["/app/start.sh"]
