# ==========================================================
# 📰 NewsTechApp — Cliente seguro da NewsAPI (PT/EN + Strict + Presets)
# ==========================================================
import os
from typing import Tuple, List, Dict, Any
from datetime import datetime, timedelta, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv


load_dotenv()

NEWSAPI_KEY: str | None = os.getenv("NEWSAPI_KEY")
BASE: str = "https://newsapi.org/v2"

# -------------------- Sessão global (com retries) --------------------
def _build_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

_session: requests.Session = _build_session()

# Sessão “rápida” (sem retries) para buscas — evita “carregando eterno”
def _build_quick_session() -> requests.Session:
    return requests.Session()

# -------------------- Helpers --------------------
def _safe_str(v: Any) -> str:
    if v is None or callable(v):
        return ""
    return str(v)

def _valid_url(v: Any) -> str:
    s = _safe_str(v).strip()
    return s if s.startswith("http") else ""

def _normalize_articles(items: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(items, list):
        return out
    for it in items:
        if not isinstance(it, dict):
            continue
        src = it.get("source") or {}
        out.append({
            "source": {"id": _safe_str(src.get("id")), "name": _safe_str(src.get("name"))},
            "author": _safe_str(it.get("author")),
            "title": _safe_str(it.get("title")) or "(Sem título)",
            "description": _safe_str(it.get("description")),
            "url": _valid_url(it.get("url")),
            "urlToImage": _valid_url(it.get("urlToImage")),
            "publishedAt": _safe_str(it.get("publishedAt")),
            "content": _safe_str(it.get("content")),
        })
    return out

def _dedup_articles(arts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out: List[Dict[str, Any]] = []
    for a in arts:
        key = (a.get("url") or "").lower() or (a.get("title") or "").lower()
        if key and key not in seen:
            seen.add(key)
            out.append(a)
    return out

def _iso_from(hours_back: int = 168) -> str:
    # clamp para evitar ranges muito grandes/pequenos
    hours_back = max(1, min(int(hours_back), 24 * 30))
    dt = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

# -------------------- Strict keywords core --------------------
def _norm(s: str) -> str:
    return (s or "").lower()

def _match_keywords_local(a: dict, keywords: list[str], mode: str = "AND", scope: str = "title"):
    title = _norm(a.get("title"))
    desc  = _norm(a.get("description"))
    hay   = title if scope == "title" else f"{title} {desc}"
    kws   = [k.strip().lower() for k in keywords if k.strip()]
    if not kws:
        return True
    hits = [(k in hay) for k in kws]
    return all(hits) if mode.upper() == "AND" else any(hits)

def _build_query(keywords: list[str], mode: str = "AND", exact: bool = True):
    toks = []
    for k in keywords:
        k = k.strip()
        if not k:
            continue
        # coloca entre aspas quando “exato” ou tiver espaço; palavras simples sem aspas funcionam bem
        if exact or (" " in k):
            toks.append(f"\"{k}\"")
        else:
            toks.append(k)
    if not toks:
        return ""
    joiner = f" {mode.upper()} "
    return joiner.join(toks)

# -------------------- Busca por palavras (rápida) --------------------
def fetch_by_keywords_strict(
    keywords: list[str],
    languages: list[str] | None = None,
    hours_back: int = 168,
    page_size: int = 20,
    page: int = 1,
    mode: str = "AND",
    exact: bool = True,
    scope: str = "title",
    sort_by: str = "publishedAt",
    request_timeout: float = 7.0,      # timeout curto por idioma
    max_retries_per_lang: int = 0,     # 0 = sem retries (responsivo)
) -> Tuple[List[Dict[str, Any]], str]:
    if not NEWSAPI_KEY:
        return [], "NEWSAPI_KEY não definida no .env"

    # valida idiomas aceitos
    if languages is None:
        languages = ["pt"]
    else:
        allow = {"pt", "en"}
        languages = [l for l in languages if l in allow]
        if not languages:
            languages = ["pt"]

    headers = {"X-Api-Key": NEWSAPI_KEY, "User-Agent": "NewsTechApp/1.0 (+keywords-strict)"}
    fr = _iso_from(hours_back)
    all_arts: List[Dict[str, Any]] = []
    errors: List[str] = []
    q = _build_query(keywords, mode=mode, exact=exact)
    if not q:
        return [], "Informe ao menos uma palavra-chave."

    # sessão rápida (sem retries) por padrão
    quick = _build_quick_session()
    if max_retries_per_lang > 0:
        r = Retry(
            total=max_retries_per_lang,
            backoff_factor=0.3,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            raise_on_status=False,
        )
        adp = HTTPAdapter(max_retries=r)
        quick.mount("https://", adp)
        quick.mount("http://", adp)

    for lang in languages:
        params = {
            "language": lang,
            "from": fr,
            "sortBy": sort_by,
            "pageSize": min(max(int(page_size), 1), 100),
            "page": max(int(page), 1),
        }
        params["qInTitle" if scope == "title" else "q"] = q

        try:
            r = quick.get(f"{BASE}/everything", headers=headers, params=params, timeout=request_timeout)
            if r.status_code == 200:
                raw = (r.json() or {}).get("articles") or []
                chunk = _normalize_articles(raw)
                # filtro local para garantir aderência às palavras
                chunk = [a for a in chunk if _match_keywords_local(a, keywords, mode=mode, scope=scope)]
                all_arts.extend(chunk)
            else:
                try:
                    msg = r.json().get("message", "")
                except Exception:
                    msg = r.text[:200]
                errors.append(f"{lang} {r.status_code}: {msg}")
        except requests.RequestException as e:
            errors.append(f"{lang} erro: {e}")

    all_arts = _dedup_articles(all_arts)
    if not all_arts:
        if errors:
            return [], "Nenhuma notícia encontrada. " + "; ".join(errors)
        return [], "Nenhuma notícia encontrada."
    return all_arts, ""

# -------------------- Presets (para futuro / RSS mapeado) --------------------
PRESETS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "hardware": {
        "gpus": {
            "keywords": ["GPU", "RTX", "GeForce", "Radeon", "DLSS", "FSR", "NVIDIA", "AMD"],
            "mode": "OR", "scope": "title", "exact": True, "languages": ["pt","en"]
        },
        "cpus": {
            "keywords": ["CPU", "Ryzen", "Core Ultra", "Intel", "AMD", "benchmark", "clock"],
            "mode": "OR", "scope": "title", "exact": True, "languages": ["pt","en"]
        },
        "armazenamento": {
            "keywords": ["SSD", "NVMe", "PCIe 5.0", "SATA", "Gen5", "leitura", "gravação"],
            "mode": "OR", "scope": "title+desc", "exact": True, "languages": ["pt","en"]
        },
        "perifericos": {
            "keywords": ["teclado mecânico", "mouse gamer", "headset", "monitor", "144Hz", "240Hz"],
            "mode": "OR", "scope": "title+desc", "exact": True, "languages": ["pt","en"]
        },
    },
    "games": {
        "lancamentos": {
            "keywords": ["lançamento", "release date", "trailer", "reveal", "pre-order", "gameplay"],
            "mode": "OR", "scope": "title", "exact": True, "languages": ["pt","en"]
        },
        "reviews": {
            "keywords": ["review", "análise", "nota", "metacritic"],
            "mode": "OR", "scope": "title", "exact": True, "languages": ["pt","en"]
        },
        "esports": {
            "keywords": ["eSports", "CS2", "Valorant", "LoL", "CBLOL", "campeonato"],
            "mode": "OR", "scope": "title+desc", "exact": True, "languages": ["pt","en"]
        },
        "pc_console": {
            "keywords": ["PC gamer", "PlayStation", "PS5", "Xbox Series", "Nintendo Switch", "Steam"],
            "mode": "OR", "scope": "title+desc", "exact": True, "languages": ["pt","en"]
        },
    },
    "tecnologia": {
        "ia": {
            "keywords": ["inteligência artificial", "IA", "AI", "machine learning", "LLM", "ChatGPT", "Copilot"],
            "mode": "OR", "scope": "title", "exact": True, "languages": ["pt","en"]
        },
        "startups": {
            "keywords": ["startup", "rodada", "Series A", "Series B", "valuation", "aceleração"],
            "mode": "OR", "scope": "title+desc", "exact": True, "languages": ["pt","en"]
        },
        "seguranca": {
            "keywords": ["segurança digital", "vazamento", "breach", "ransomware", "phishing"],
            "mode": "OR", "scope": "title+desc", "exact": True, "languages": ["pt","en"]
        },
        "gadgets": {
            "keywords": ["smartphone", "laptop", "wearable", "fones", "tablet"],
            "mode": "OR", "scope": "title+desc", "exact": True, "languages": ["pt","en"]
        },
    },
    "desenvolvedores": {
        "python": {
            "keywords": ["Python", "Flask", "Django", "FastAPI", "pip", "virtualenv"],
            "mode": "OR", "scope": "title", "exact": True, "languages": ["pt","en"]
        },
        "javascript": {
            "keywords": ["JavaScript", "Node.js", "React", "Next.js", "TypeScript", "Vite"],
            "mode": "OR", "scope": "title", "exact": True, "languages": ["pt","en"]
        },
        "devops": {
            "keywords": ["DevOps", "Docker", "Kubernetes", "CI/CD", "GitHub Actions", "Helm"],
            "mode": "OR", "scope": "title+desc", "exact": True, "languages": ["pt","en"]
        },
        "ai_tools": {
            "keywords": ["LLM", "RAG", "fine-tuning", "prompt engineering", "Copilot", "GenAI"],
            "mode": "OR", "scope": "title+desc", "exact": True, "languages": ["pt","en"]
        },
    },
}

def get_subkeys_for(category: str) -> List[str]:
    cfg = PRESETS.get(category, {})
    return list(cfg.keys())

def fetch_by_preset(category: str, subkey: str, page_size: int = 24) -> Tuple[List[Dict[str, Any]], str]:
    cat = PRESETS.get(category)
    if not cat or subkey not in cat:
        return [], "Preset não encontrado."
    p = cat[subkey]
    return fetch_by_keywords_strict(
        keywords=p["keywords"],
        languages=p["languages"],
        hours_back=168,
        page_size=page_size,
        page=1,
        mode=p["mode"],
        exact=p["exact"],
        scope=p["scope"],
        sort_by="publishedAt",
    )

# -------------------- Top-headlines utilitário (opcional) --------------------
def fetch_news(
    category: str = "technology",
    country: str = "br",
    page_size: int = 12,
    include_english: bool = True,
):
    """
    Busca notícias top-headlines em PT e EN.
    Retorna (articles, error).
    """
    if not NEWSAPI_KEY:
        return [], "NEWSAPI_KEY não definida no .env"

    headers = {"X-Api-Key": NEWSAPI_KEY, "User-Agent": "NewsTechApp/1.0 (+top)"}
    all_articles: List[Dict[str, Any]] = []
    errors: List[str] = []

    # 🇧🇷 Notícias do Brasil
    try:
        r1 = _session.get(
            f"{BASE}/top-headlines",
            headers=headers,
            params={"country": country, "category": category, "pageSize": page_size},
            timeout=10,
        )
        if r1.status_code == 200:
            data = r1.json()
            articles = data.get("articles", []) or []
            all_articles.extend(_normalize_articles(articles))
        else:
            errors.append(f"PT {r1.status_code}: {r1.text[:100]}")
    except Exception as e:
        errors.append(f"Erro PT: {e}")

    # 🇺🇸 Notícias internacionais
    if include_english:
        try:
            r2 = _session.get(
                f"{BASE}/top-headlines",
                headers=headers,
                params={"country": "us", "category": category, "pageSize": page_size},
                timeout=10,
            )
            if r2.status_code == 200:
                data = r2.json()
                articles = data.get("articles", []) or []
                all_articles.extend(_normalize_articles(articles))
            else:
                errors.append(f"EN {r2.status_code}: {r2.text[:100]}")
        except Exception as e:
            errors.append(f"Erro EN: {e}")

    if not all_articles:
        return [], ("Nenhuma notícia retornada. " + "; ".join(errors) if errors else "Nenhuma notícia retornada.")
    return _dedup_articles(all_articles), ""

# -------------------- Categorias prontas (se quiser usar) --------------------
def fetch_developer_news(page_size: int = 24):
    keywords = [
        "Python", "Flask", "Django", "FastAPI",
        "JavaScript", "TypeScript", "Node.js", "React", "Next.js",
        "DevOps", "Docker", "Kubernetes", "CI/CD",
        "GitHub", "VS Code", "Copilot"
    ]
    return fetch_by_keywords_strict(
        keywords=keywords,
        languages=["pt", "en"],
        hours_back=168,
        page_size=page_size,
        page=1,
        mode="OR",
        exact=True,
        scope="title",
        sort_by="publishedAt",
        request_timeout=7.0,
        max_retries_per_lang=0,
    )

def fetch_hardware_news(page_size: int = 24):
    keywords = [
        "GPU", "RTX", "GeForce", "Radeon", "DLSS", "FSR",
        "NVIDIA", "AMD", "Intel", "Ryzen",
        "CPU", "processador", "placa de vídeo",
        "SSD", "NVMe", "PCIe 5.0", "Gen5", "notebook", "desktop"
    ]
    return fetch_by_keywords_strict(
        keywords=keywords,
        languages=["pt", "en"],
        hours_back=168,
        page_size=page_size,
        page=1,
        mode="OR",
        exact=True,
        scope="title+desc",
        sort_by="publishedAt",
        request_timeout=7.0,
        max_retries_per_lang=0,
    )

def fetch_games_news(page_size: int = 24):
    keywords = [
        "video games", "gaming", "jogos",
        "trailer", "gameplay", "lançamento", "pre-order", "reveal",
        "review", "análise",
        "PlayStation", "PS5", "Xbox Series", "Nintendo Switch", "Steam", "PC gamer"
    ]
    return fetch_by_keywords_strict(
        keywords=keywords,
        languages=["pt", "en"],
        hours_back=168,
        page_size=page_size,
        page=1,
        mode="OR",
        exact=True,
        scope="title",
        sort_by="publishedAt",
        request_timeout=7.0,
        max_retries_per_lang=0,
    )

def fetch_technology_news(page_size: int = 24):
    keywords = [
        "tecnologia", "technology", "inovação", "startups",
        "inteligência artificial", "AI", "machine learning", "LLM",
        "gadgets", "smartphone", "laptop",
        "segurança digital", "ransomware", "phishing", "vazamento"
    ]
    return fetch_by_keywords_strict(
        keywords=keywords,
        languages=["pt", "en"],
        hours_back=168,
        page_size=page_size,
        page=1,
        mode="OR",
        exact=True,
        scope="title+desc",
        sort_by="publishedAt",
        request_timeout=7.0,
        max_retries_per_lang=0,
    )

