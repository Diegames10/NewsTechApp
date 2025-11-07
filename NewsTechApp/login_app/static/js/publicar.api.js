// static/js/publicar.api.js
(function () {
  // =======================
  // Seletores base
  // =======================
  const $list    = document.getElementById("lista-noticias"); // container dos cards
  const $pagi    = document.getElementById("paginacao");      // paginação
  const $vazio   = document.getElementById("vazio");          // mensagem "vazio"
  const $q       = document.getElementById("q");              // busca
  const $ordem   = document.getElementById("ordem");          // ordenação (opcional)
  const $btnAtt  = document.getElementById("btn-atualizar");  // botão "Atualizar"

  if (!$list) return; // página não tem lista

  // =======================
  // Estado
  // =======================
  const PER_PAGE        = 10;
  const ABOVE_THE_FOLD  = 3;          // primeiras imagens "eager"
  const FALLBACK_ASPECT = "16/9";     // aspecto base para evitar "jump"
  let currentPage       = 1;
  let totalPages        = 1;

  const state = {
    page: 1,
    q: "",
    ordem: "recente",
  };

  // =======================
  // Utils
  // =======================
  function escapeHtml(s) {
    return (s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatDate(iso) {
    if (!iso) return "";
    try {
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return "";
      return d.toLocaleString();
    } catch { return ""; }
  }

  function qs(params) {
    const u = new URLSearchParams();
    Object.entries(params).forEach(([k,v]) => {
      if (v !== undefined && v !== null && String(v).trim() !== "") u.set(k, v);
    });
    const s = u.toString();
    return s ? `?${s}` : "";
  }

  function normalizeMeta(meta) {
    if (!meta) return { page: 1, pages: 1, has_prev: false, has_next: false, prev_page: 1, next_page: 1 };
    const page      = meta.page ?? meta.current_page ?? 1;
    const pages     = meta.pages ?? meta.total_pages ?? 1;
    const has_prev  = meta.has_prev ?? meta.hasPrev ?? page > 1;
    const has_next  = meta.has_next ?? meta.hasNext ?? page < pages;
    const prev_page = meta.prev_page ?? meta.prevPage ?? (page > 1 ? page - 1 : 1);
    const next_page = meta.next_page ?? meta.nextPage ?? (page < pages ? page + 1 : pages);
    return { page, pages, has_prev, has_next, prev_page, next_page };
  }

  // =======================
  // API
  // =======================
  async function apiList(q = "", page = 1, ordem = "recente") {
    const u = new URL("/api/posts", window.location.origin);
    if (q) u.searchParams.set("q", q);
    if (ordem) u.searchParams.set("ordem", ordem); // se o backend ignorar, não quebra
    u.searchParams.set("page", page);
    u.searchParams.set("per_page", PER_PAGE);

    const r = await fetch(u, {
      headers: { "Accept": "application/json" },
      credentials: "include", // mantém cookies/sessão
    });
    if (!r.ok) throw new Error(`Falha ao listar (${r.status})`);
    const data = await r.json();

    currentPage = data?.meta?.page  || 1;
    totalPages  = data?.meta?.pages || 1;

    const items = Array.isArray(data) ? data : (data.items || data.Objectitems || []);
    return { items, meta: data.meta || {} };
  }

  async function apiDelete(id) {
    const r = await fetch(`/api/posts/${id}`, { method: "DELETE", credentials: "include" });
    if (!r.ok) throw new Error(`Falha ao excluir (${r.status})`);
  }

  // =======================
  // UI: imagem resiliente
  // =======================
  function createSmartImage(src, alt, eager) {
    const img = document.createElement("img");
    img.className = "thumb";
    img.src = src;
    img.alt = alt || "Imagem da notícia";
    img.loading = eager ? "eager" : "lazy";
    img.decoding = "async";
    if (eager) img.setAttribute("fetchpriority", "high");
    img.style.width = "100%";
    img.style.aspectRatio = FALLBACK_ASPECT;
    img.style.objectFit = "cover";
    img.style.background = "#eee";

    // marca quando terminou (para CSS opcional)
    img.addEventListener("load",  () => { img.dataset.loaded = "1"; }, { once: true });
    img.addEventListener("error", () => {
      // retry único com cache-buster pra combater race/304 estranhos no mobile
      if (!img.dataset.retried) {
        img.dataset.retried = "1";
        const bust = (img.src.includes("?") ? "&" : "?") + "b=" + Date.now();
        img.src = img.src + bust;
        console.warn("Retry imagem com cache-buster:", img.src);
      } else {
        img.dataset.err = "1";
        console.warn("Falha ao carregar imagem definitivamente:", img.src);
      }
    }, { once: true });

    return img;
  }

  // =======================
  // UI: card seguro (sem innerHTML para conteúdo dinâmico)
  // =======================
  function buildCard(p, idx) {
    const card = document.createElement("article");
    card.className = "card";

    // mídia
    if (p.image_url) {
      const media = document.createElement("div");
      media.className = "card-media";
      const eager = idx < ABOVE_THE_FOLD;
      const img = createSmartImage(p.image_url, p.titulo || "Imagem da notícia", eager);
      media.appendChild(img);
      card.appendChild(media);
    }

    const body = document.createElement("div");
    body.className = "card-body";

    const title = document.createElement("h3");
    title.className = "card-title";
    title.textContent = p.titulo || "Sem título";
    body.appendChild(title);

    const text = document.createElement("p");
    text.className = "card-text";
    const full = p.conteudo || "";
    text.textContent = full.length > 240 ? (full.slice(0,240) + "...") : full;
    body.appendChild(text);

    const meta = document.createElement("div");
    meta.className = "card-meta";

    const autor = document.createElement("span");
    autor.textContent = p.autor_nome || p.autor_email || p.autor || "Autor desconhecido";
    meta.appendChild(autor);

    const time = document.createElement("time");
    const iso = p.created_at || p.criado_em || "";
    time.setAttribute("datetime", iso);
    time.textContent = formatDate(iso);
    meta.appendChild(time);

    body.appendChild(meta);

    // ações (editar/excluir) — se quiser, habilite conforme sua autorização
    const actions = document.createElement("div");
    actions.className = "card-actions";

    const editar = document.createElement("a");
    editar.className = "btn";
    editar.href = `/publicar?id=${p.id}`;
    editar.textContent = "Editar";
    actions.appendChild(editar);

    const excluir = document.createElement("button");
    excluir.className = "btn danger";
    excluir.type = "button";
    excluir.dataset.del = String(p.id);
    excluir.textContent = "Excluir";
    actions.appendChild(excluir);

    body.appendChild(actions);
    card.appendChild(body);

    return card;
  }

  function renderPosts(items) {
    // limpa e desenha
    $list.textContent = "";
    if (!Array.isArray(items) || items.length === 0) {
      if ($vazio) $vazio.style.display = "block";
      return;
    }
    if ($vazio) $vazio.style.display = "none";

    items.forEach((p, i) => {
      const card = buildCard(p, i);
      $list.appendChild(card);
    });
  }

  // =======================
  // Paginação
  // =======================
  function renderPaginator(metaRaw) {
    if (!$pagi) return;
    const meta = normalizeMeta(metaRaw);

    $pagi.textContent = "";

    const mkBtn = (label, target, disabled=false) => {
      const b = document.createElement("button");
      b.className = "page-btn";
      b.textContent = label;
      if (disabled) b.disabled = true;
      b.dataset.page = String(target);
      return b;
    };

    $pagi.appendChild(mkBtn("« Primeira", 1, !meta.has_prev));
    $pagi.appendChild(mkBtn("‹ Anterior", meta.prev_page, !meta.has_prev));

    const info = document.createElement("span");
    info.className = "page-info";
    info.style.margin = "0 .5rem";
    info.textContent = `Página ${meta.page} de ${meta.pages}`;
    $pagi.appendChild(info);

    $pagi.appendChild(mkBtn("Próxima ›", meta.next_page, !meta.has_next));
    $pagi.appendChild(mkBtn("Última »", meta.pages, !meta.has_next));

    // delegação de clique
    $pagi.onclick = (ev) => {
      const t = ev.target;
      if (t && t.matches(".page-btn") && !t.disabled) {
        const p = parseInt(t.getAttribute("data-page") || "", 10);
        if (Number.isFinite(p)) {
          state.page = p;
          load();
        }
      }
    };
  }

  // =======================
  // Loader principal
  // =======================
  async function load() {
    const urlParams = { page: state.page, q: state.q, ordem: state.ordem };
    try {
      const { items, meta } = await apiList(state.q, state.page, state.ordem);
      renderPosts(items);
      renderPaginator(meta);
    } catch (e) {
      console.error(e);
      if (!$list.innerHTML) {
        $list.innerHTML = `<p style="color:#dc2626">Erro ao carregar as notícias.</p>`;
      }
      if ($vazio) $vazio.style.display = "block";
      // ainda assim tenta desenhar paginação mínima
      renderPaginator({ page: state.page, pages: 1, has_prev: state.page > 1, has_next: false });
    }
  }

  // =======================
  // Eventos
  // =======================
  // Exclusão delegada
  document.addEventListener("click", async (e) => {
    const btn = e.target && e.target.closest("[data-del]");
    if (!btn) return;
    const id = Number(btn.dataset.del);
    if (!Number.isFinite(id)) return;
    try {
      if (confirm("Excluir esta postagem?")) {
        await apiDelete(id);
        await load(); // mantém estado.page
      }
    } catch (err) {
      console.error(err);
      alert("Não foi possível excluir a postagem.");
    }
  });

  // Busca (debounce + reset page)
  $q?.addEventListener("input", (e) => {
    state.q = e.target.value || "";
    state.page = 1;
    clearTimeout($q.__t);
    $q.__t = setTimeout(load, 300);
  });

  // Ordenação (reset page)
  $ordem?.addEventListener("change", (e) => {
    state.ordem = e.target.value || "recente";
    state.page = 1;
    load();
  });

  // Atualizar (mantém page)
  $btnAtt?.addEventListener("click", () => {
    load();
  });

  // bfcache: se voltar pra página, revalida lista rapidamente (imagens ficam cacheadas pelo navegador)
  window.addEventListener("pageshow", (e) => {
    if (e.persisted) load();
  });

  // Start
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => load(), { once: true });
  } else {
    load();
  }
})();
