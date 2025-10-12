# Imagem base
FROM python:3.11-slim

# Instale dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev libssl-dev libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crie diretório da aplicação e diretório para dados persistentes
WORKDIR /app
RUN mkdir -p /data && chmod 755 /data

# Copie dependências primeiro (melhor cache)
COPY NewsTechApp/login_app/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copie o restante do código
COPY NewsTechApp/login_app /app/login_app

# Defina variável de ambiente para evitar buffering
ENV PYTHONUNBUFFERED=1

# Expõe a porta do Flask (ou FastAPI, etc.)
EXPOSE 8080

# Script de inicialização que cria o banco se necessário
COPY NewsTechApp/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Use o script de inicialização
CMD ["/app/start.sh"]
