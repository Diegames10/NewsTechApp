# rss_client.py
from __future__ import annotations
import datetime as dt
from typing import List, Tuple, Optional, Dict
import feedparser
import html
import re

# ==============================================================
# 🌐 Fontes confiáveis com RSS (NewsTechApp)
# ==============================================================

FEEDS: Dict[str, Dict[str, List[str]]] = {
    "hardware": {
        "nacional": [
            "https://canaltech.com.br/rss/hardware/",
            #"https://adrenaline.com.br/rss/categoria/hardware",
        ],
        "internacional": [
            "https://www.tomshardware.com/feeds/all",
            "https://www.extremetech.com/feed",
        ],
    },
    "games": {
        "nacional": [
            "https://www.theenemy.com.br/rss",
            "https://www.gamevicio.com/rss/noticias/",
            "https://www.theenemy.com.br/games/rss-de-volta",
        ],
        "internacional": [
            "https://www.pcgamer.com/rss/",
            "https://www.tweaktown.com/feeds/news-mf.xml",
        ],
        "console": [
            "https://blog.playstation.com/feed/",
            "https://news.xbox.com/en-us/feed/",
            "https://store.steampowered.com/feeds/news.xml",
        ],
    },
    "tecnologia": {
        "ia": {
            "nacional": [
                "https://canaltech.com.br/rss/inteligencia-artificial/",
                "https://olhardigital.com.br/feed/",
            ],
            "internacional": [
                "https://www.theverge.com/rss/index.xml",
                "https://www.theverge.com/artificial-intelligence/rss/index.xml",
            ],
        },
        "seguranca": {
            "nacional": [
                "https://www.cisoadvisor.com.br/feed/",
                "https://www.tecmundo.com.br/seguranca/rss",
            ],
            "internacional": [
                "https://feeds.feedburner.com/TechCrunch/startups",
                "https://krebsonsecurity.com/feed/",
                "https://www.bleepingcomputer.com/feed/",
            ],
        },
        "gadgets": {
            "nacional": [
                "https://www.tudocelular.com/rss/",
                "https://tecnoblog.net/feed/",
            ],
            "internacional": [
                "https://www.engadget.com/rss.xml",
                "https://www.androidauthority.com/feed/",
                "https://www.techrepublic.com/rssfeeds/articles/",
            ],
        },
    },
    "desenvolvedores": {
        "nacional": [
            "https://imasters.com.br/feed",
            "https://www.infoq.com/br/feed",
        ],
        "internacional": [
            "https://news.ycombinator.com/rss",
            "https://stackoverflow.blog/feed/",
        ],
        "devops": [
            "https://dev.to/feed/tag/devops",
        ],
        "ai_tools": [
            "https://dev.to/feed/tag/machinelearning",
        ],
    },
}

# ==============================================================
# ⚙️ Config HTTP para contornar 403/Cloudflare em alguns feeds
# ==============================================================

# Define um UA global do feedparser (alguns servidores checam isso)
feedparser.USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/119.0 Safari/537.36 NewsTechApp/1.0"
)

REQUEST_HEADERS = {
    "User-Agent": feedparser.USER_AGENT,
    "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Referer": "https://news-tech.local/",
}

# ==============================================================
# 🧹 Utilitários
# ==============================================================

def list_subkeys(category: str) -> List[str]:
    """Lista as subchaves válidas da categoria (ou lista vazia)."""
    return list(FEEDS.get(category, {}).keys())

def _clean_text(s: Optional[str]) -> str:
    if not s:
        return ""
    s = html.unescape(s)
    s = re.sub(r"<.*?>", "", s)         # remove tags HTML
    s = re.sub(r"\s+", " ", s).strip()  # normaliza espaços
    return s

def _extract_image(entry: dict) -> Optional[str]:
    """
    Tenta encontrar uma imagem representativa no item RSS.
    Prioridades:
      - media:content / media:thumbnail
      - enclosures image/*
      - links rel="enclosure" / type image/*
    """
    try:
        # media:content
        if "media_content" in entry and entry.media_content:
            for media in entry.media_content:
                url = media.get("url")
                if url:
                    return url

        # media:thumbnail
        if "media_thumbnail" in entry and entry.media_thumbnail:
            url = entry.media_thumbnail[0].get("url")
            if url:
                return url

        # enclosures (com extensões ou type image/*)
        if "enclosures" in entry and entry.enclosures:
            for enc in entry.enclosures:
                url = enc.get("href") or enc.get("url")
                typ = (enc.get("type") or "").lower()
                if url and (typ.startswith("image/") or re.search(r"\.(jpe?g|png|gif|webp)$", url, re.I)):
                    return url

        # links com rel=enclosure e type image/*
        if "links" in entry and entry.links:
            for l in entry.links:
                rel = (l.get("rel") or "").lower()
                typ = (l.get("type") or "").lower()
                href = l.get("href")
                if rel == "enclosure" and href and typ.startswith("image/"):
                    return href
    except Exception:
        pass
    return None

# ==============================================================
# 🔍 Funções principais
# ==============================================================

def _safe_feed_title(parsed) -> str:
    """Pega título do feed sem levantar exceção se faltar metadado."""
    feed_meta = getattr(parsed, "feed", None)
    if isinstance(feed_meta, dict):
        return feed_meta.get("title", "RSS desconhecido")
    return "RSS desconhecido"

def _parse_one(feed_url: str, limit: int = 24) -> List[dict]:
    """Analisa um único feed RSS e retorna itens normalizados."""
    parsed = feedparser.parse(feed_url, request_headers=REQUEST_HEADERS)
    items: List[dict] = []

    for e in getattr(parsed, "entries", [])[:limit]:
        title = _clean_text(getattr(e, "title", ""))
        desc = _clean_text(getattr(e, "summary", "") or getattr(e, "description", ""))
        link = getattr(e, "link", "")
        image = _extract_image(e)

        # Data: tenta published_parsed, cai para updated_parsed
        pub_dt = None
        tm = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
        if tm:
            pub_dt = dt.datetime(*tm[:6], tzinfo=dt.timezone.utc)

        items.append({
            "title": title or "(sem título)",
            "description": desc or None,
            "url": link,
            "urlToImage": image,
            "publishedAt": pub_dt.isoformat() if pub_dt else None,
            "source": _safe_feed_title(parsed),
        })
    return items

def fetch_category_sub(category: str, subkey: str, limit: int = 24) -> Tuple[List[dict], Optional[str]]:
    """
    Retorna (items, error).
    - Valida categoria/sub.
    - Faz merge das entradas dos RSS configurados.
    - Tenta carregar imagens e sanitiza textos.
    """
    try:
        cat = category.strip().lower()
        sub = subkey.strip().lower()
        if cat not in FEEDS:
            return [], f"Categoria inválida: {cat}"
        if sub not in FEEDS[cat]:
            return [], f"Subcategoria inválida: {sub} (válidas: {', '.join(list_subkeys(cat))})"

        urls = FEEDS[cat][sub]
        all_items: List[dict] = []

        for u in urls:
            try:
                all_items.extend(_parse_one(u, limit))
            except Exception as ex:
                # Continua nas demais fontes, preservando a origem com erro
                all_items.append({
                    "title": f"[Falha ao ler feed] {u}",
                    "description": str(ex),
                    "url": u,
                    "urlToImage": None,
                    "publishedAt": None,
                    "source": "rss-client",
                })

        # Ordena por data (desc); itens sem data vão pro fim
        def _key(x):
            p = x.get("publishedAt")
            try:
                return dt.datetime.fromisoformat(p) if p else dt.datetime.min.replace(tzinfo=dt.timezone.utc)
            except Exception:
                return dt.datetime.min.replace(tzinfo=dt.timezone.utc)

        all_items.sort(key=_key, reverse=True)
        return all_items[:limit], None

    except Exception as e:
        return [], f"Erro inesperado no RSS: {e}"
