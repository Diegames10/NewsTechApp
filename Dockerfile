FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev libssl-dev libpq-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    SQLALCHEMY_DATABASE_URI=sqlite:////data/app.db \
    UPLOAD_FOLDER=/data/uploads

EXPOSE 8080

RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]
