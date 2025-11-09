# Imagem base
FROM python:3.11-slim

# Dependências do sistema (mínimas; adicione mais se precisar)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev libssl-dev libpq-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Diretório da aplicação
WORKDIR /app

# >>> IMPORTANTE: /data é o disco persistente no Render
RUN mkdir -p /data/uploads && chmod -R 755 /data

# Copie requirements primeiro (melhor cache)
COPY NewsTechApp/login_app/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

# Copie o código
COPY NewsTechApp/login_app /app/login_app

# Variáveis padrão (podem ser sobrescritas no painel do Render)
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    SQLALCHEMY_DATABASE_URI=sqlite:////data/app.db \
    UPLOAD_FOLDER=/data/uploads \
    PREFERRED_URL_SCHEME=https

# Porta (o Render injeta $PORT; isso aqui é só documentação)
EXPOSE 8080

# Script de inicialização
COPY NewsTechApp/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Início
CMD ["/app/start.sh"]
