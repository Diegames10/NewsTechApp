# login_app/routes/news.py
from flask import Blueprint, render_template, request, jsonify
from markupsafe import escape

from login_app.utils.token import login_required_view
from login_app.utils.jwt_auth import login_required_api

news_bp = Blueprint("news", __name__)

# ========= Imports internos/externos com fallback seguro =========
# Chat blueprint será registrado no __init__.py (não aqui)
try:
    from ..chat_api import bp_chat as _bp_chat  # apenas para checagem do pacote
    HAS_CHAT_BP = True
except Exception:
    HAS_CHAT_BP = False

# RSS client
try:
    from ..rss_client import fetch_category_sub, list_subkeys  # se estiver dentro do pacote
except Exception:
    try:
        # fallback se estiver na raiz do projeto (não recomendado)
        from rss_client import fetch_category_sub, list_subkeys  # type: ignore
    except Exception:
        fetch_category_sub = None
        list_subkeys = None

# News search (ex: NewsAPI client)
try:
    from ..news_client import fetch_by_keywords_strict  # ajuste ao seu cliente real
except Exception:
    try:
        from news_client import fetch_by_keywords_strict  # type: ignore
    except Exception:
        fetch_by_keywords_strict = None


# ==========================================================
# 🔍 PÁGINA INICIAL DE NOTÍCIAS (mudamos para /news p/ não conflitar com auth /)
# ==========================================================
@news_bp.get("/news")
@login_required_view
def news_home():
    return render_template(
        "news.html",
        articles=[],
        error="",
        q="",
        lang="pt,en",
        mode="AND",
        scope="title",
        exact="1",
        sort="publishedAt",
    )


# ==========================================================
# 🔎 BUSCA — NewsAPI (segura e filtrada)
# ==========================================================
@news_bp.get("/buscar-chat")
def buscar():
    raw_q = request.args.get("q", "", type=str).strip()
    safe_q = escape(raw_q)

    # idiomas
    lang = request.args.get("lang", "pt,en").lower()
    langs = [s.strip() for s in lang.split(",") if s.strip() in ("pt", "en")] or ["pt"]

    # modo (AND/OR)
    mode = request.args.get("mode", "AND").upper()
    if mode not in ("AND", "OR"):
        mode = "AND"

    # escopo
    scope = request.args.get("scope", "title")
    if scope not in ("title", "title+desc"):
        scope = "title"

    # ordenação
    sort = request.args.get("sort", "publishedAt")
    if sort not in ("publishedAt", "relevancy", "popularity"):
        sort = "publishedAt"

    # aspas/exato
    exact = request.args.get("exact", "1").lower() in ("1", "true", "on", "yes")

    # vazio -> volta ao formulário
    if not safe_q:
        return render_template(
            "news.html",
            articles=[],
            error="Digite algo para pesquisar.",
            q="",
            lang=",".join(langs),
            mode=mode,
            scope=scope,
            exact="1" if exact else "0",
            sort=sort,
        )

    # normaliza termos (máx. 10)
    import re as _re
    parts = _re.split(r"[|,;]+", raw_q)
    keywords = [p.strip() for p in parts if p.strip() and 2 <= len(p.strip()) <= 64][:10]

    if not keywords:
        return render_template(
            "news.html",
            articles=[],
            error="Nenhum termo de busca válido encontrado.",
            q=safe_q,
            lang=",".join(langs),
            mode=mode,
            scope=scope,
            exact="1" if exact else "0",
            sort=sort,
        )

    # busca
    articles, error = [], None
    try:
        if fetch_by_keywords_strict is None:
            raise RuntimeError("Motor de busca de notícias não está disponível.")
        articles, error = fetch_by_keywords_strict(
            keywords=keywords,
            languages=langs,
            hours_back=168,   # últimos 7 dias
            page_size=24,
            page=1,
            mode=mode,
            exact=exact,
            scope=scope,
            sort_by=sort,
        )
    except TimeoutError:
        error = "Tempo de resposta excedido. Tente novamente em alguns segundos."
    except ConnectionError:
        error = "Falha de conexão com o provedor de notícias."
    except Exception as e:
        error = f"Ocorreu um erro inesperado: {escape(str(e))}"

    if not isinstance(error, str):
        error = None

    return render_template(
        "news.html",
        articles=articles or [],
        error=error,
        q=safe_q,
        lang=",".join(langs),
        mode=mode,
        scope=scope,
        exact="1" if exact else "0",
        sort=sort,
    )


# =========================
# 📊 DASHBOARD / RSS (HTML)
# =========================
@news_bp.get("/dashboard-rss")
def rss_dashboard_page():
    return render_template("dashboard-rss.html")


@news_bp.get("/rss/<cat>/<sub>")
def rss_items_page(cat: str, sub: str):
    if not fetch_category_sub:
        return render_template("rss_list.html", cat=cat, sub=sub, articles=[], error="RSS indisponível"), 200

    items, err = fetch_category_sub(cat, sub, limit=24)
    return render_template(
        "rss_list.html",
        cat=cat,
        sub=sub,
        articles=items or [],
        error=err or "",
    )


# =========================
# 🧩 RSS (API JSON)
# =========================
@news_bp.get("/api/rss/subs/<category>")
def rss_list_subs_api(category: str):
    if not list_subkeys:
        return jsonify({"category": category, "subkeys": [], "error": "RSS indisponível"}), 200
    return jsonify({"category": category, "subkeys": list_subkeys(category)})


@news_bp.get("/api/rss/items/<category>/<subkey>")
def rss_fetch_items_api(category: str, subkey: str):
    if not fetch_category_sub:
        return jsonify({"category": category, "subkey": subkey, "items": [], "error": "RSS indisponível"}), 200
    items, err = fetch_category_sub(category, subkey, limit=12)
    return jsonify({"category": category, "subkey": subkey, "error": err or "", "items": items or []})


@news_bp.get("/rss/<cat>/<sub>/<region>")
def rss_page_region(cat, sub, region):
    # exemplo: /rss/tecnologia/gadgets/nacional
    try:
        from ..rss_client import FEEDS, _parse_one  # pacote
    except Exception:
        try:
            from rss_client import FEEDS, _parse_one  # fallback raiz
        except Exception:
            return "RSS indisponível", 503

    if cat not in FEEDS or sub not in FEEDS[cat]:
        return f"Subcategoria '{sub}' inválida para '{cat}'", 404

    region = region.lower()
    urls = FEEDS[cat][sub].get(region)
    if not urls:
        return f"Região '{region}' não encontrada em {cat}/{sub}", 404

    all_items = []
    for u in urls:
        all_items.extend(_parse_one(u, limit=24))

    return render_template(
        "rss_list.html",
        cat=cat,
        sub=f"{sub} ({region})",
        articles=all_items,
        error=None,
    )


@news_bp.get("/assistente")
@login_required_view
def assistente_page():
    return render_template("assistente.html")








