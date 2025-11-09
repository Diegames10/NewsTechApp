#!/usr/bin/env bash
set -euo pipefail

echo "Iniciando aplicação NewsTechApp..."

# Garante diretórios de dados
mkdir -p /data /data/uploads
chmod 755 /data

# Aplica migrations (idempotente). Não use create_all em produção.
echo "Aplicando migrations..."
python -m flask --app login_app:create_app db upgrade || true

# Sobe o servidor via app factory (sem precisar de run.py ou app.py)
echo "Iniciando servidor Gunicorn..."
exec gunicorn --factory \
  -w 2 -k gthread \
  -b 0.0.0.0:${PORT:-8080} \
  'login_app:create_app' \
  --timeout 120 --threads 8
