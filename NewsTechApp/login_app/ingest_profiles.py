import os, requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

from news_client import fetch_news

def get_tecnologia():
    return fetch_news(category="technology")

def get_hardware():
    return fetch_news(q="GPU OR CPU OR 'placa de vídeo' OR 'placa-mãe' OR SSD")

def get_games():
    return fetch_news(q="jogos OR PS5 OR Xbox OR Nintendo OR 'PC Gaming'")

def get_programacao():
    return fetch_news(q="programação OR Python OR JavaScript OR Node.js OR React OR .NET")

PROFILES = {
    "tecnologias": get_tecnologia,
    "hardware": get_hardware,
    "games": get_games,
    "programacao": get_programacao
}

load_dotenv()
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
BASE = "https://newsapi.org/v2"

def fetch_news(category="technology", country="br", language="pt", page_size=10):
    """Busca notícias da NewsAPI"""
    url = f"{BASE}/top-headlines"
    params = {
        "country": country,
        "category": category,
        "language": language,
        "pageSize": page_size,
    }
    r = requests.get(url, headers={"X-Api-Key": NEWSAPI_KEY}, params=params, timeout=15)
    r.raise_for_status()
    return r.json().get("articles", [])