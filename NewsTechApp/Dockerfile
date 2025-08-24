# Imagem base
FROM python:3.11-slim

# Instale dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev libssl-dev libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crie diretório da aplicação
WORKDIR /app

# Copie dependências primeiro (melhor cache)
COPY login_app/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copie o restante do código
COPY login_app /app/login_app

# Defina variável de ambiente para evitar buffering
ENV PYTHONUNBUFFERED=1

# Expõe a porta do Flask (ou FastAPI, etc.)
EXPOSE 8080

# Comando para rodar a aplicação

CMD ["python3", "login_app/app.py"]