// static/js/publicar.api.js
(function () {
  // Seletores base (compatíveis com seu HTML)
  const $list   = document.getElementById("lista-noticias"); // container de cards
  const $pagi   = document.getElementById("paginacao");      // paginação
  const $vazio  = document.getElementById("vazio");          // mensagem de vazio
  const $q      = document.getElementById("q");              // busca
  const $ordem  = document.getElementById("ordem");          // ordenação
  const $btnAtt = document.getElementById("btn-atualizar");  // botão "Atualizar"

  // Se a lista não existe na página, não faz nada (evita "innerHTML of null")
  if (!$list) return;

  // Estado simples
  let state = {
    page: 1,
    q: "",
    ordem: "recente",
  };

  // Utilidades
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

  function normalizeMeta(meta) {
    if (!meta) return { page: 1, pages: 1, has_prev: false, has_next: false, prev_page: 1, next_page: 1 };
    const page = meta.page ?? meta.current_page ?? 1;
    const pages = meta.pages ?? meta.total_pages ?? 1;
    const has_prev = meta.has_prev ?? meta.hasPrev ?? page > 1;
    const has_next = meta.has_next ?? meta.hasNext ?? page < pages;
    const prev_page = meta.prev_page ?? meta.prevPage ?? (page > 1 ? page - 1 : 1);
    const next_page = meta.next_page ?? meta.nextPage ?? (page < pages ? page + 1 : pages);
    return { page, pages, has_prev, has_next, prev_page, next_page };
  }

  // Render de cards
  function renderPosts(items) {
    if (!Array.isArray(items) || items.length === 0) {
      if ($list) $list.innerHTML = "";
      if ($vazio) $vazio.style.display = "block";
      return;
    }
    if ($vazio) $vazio.style.display = "none";

    const html = items.map(p => {
      const titulo   = escapeHtml(p.titulo || "Sem título");
      const conteudo = escapeHtml((p.conteudo || "").slice(0, 240)) + ((p.conteudo || "").length > 240 ? "..." : "");
      const autor    = escapeHtml(p.autor_nome || p.autor_email || "Autor desconhecido");
      const data     = formatDate(p.created_at);
      const img      = p.image_url ? `
        <div class="card-media">
          <img src="${p.image_url}" alt="${titulo}" loading="lazy">
        </div>` : "";

      return `
        <article class="card">
          ${img}
          <div class="card-body">
            <h3 class="card-title">${titulo}</h3>
            <p class="card-text">${conteudo}</p>
            <div class="card-meta">
              <span>${autor}</span>
              <time datetime="${p.created_at || ""}">${data}</time>
            </div>
          </div>
        </article>
      `;
    }).join("");

    if ($list) $list.innerHTML = html;
  }

  // Render da paginação
  function renderPaginator(metaRaw) {
    if (!$pagi) return;
    const meta = normalizeMeta(metaRaw);

    const btn = (label, target, disabled=false) =>
      `<button class="page-btn" data-page="${target}" ${disabled ? "disabled" : ""}>${label}</button>`;

    const html = `
      ${btn("« Primeira", 1, !meta.has_prev)}
      ${btn("‹ Anterior", meta.prev_page, !meta.has_prev)}
      <span class="page-info">Página ${meta.page} de ${meta.pages}</span>
      ${btn("Próxima ›", meta.next_page, !meta.has_next)}
      ${btn("Última »", meta.pages, !meta.has_next)}
    `;
    $pagi.innerHTML = html;

    // Delegação de clique
    $pagi.onclick = (ev) => {
      const t = ev.target;
      if (t.matches(".page-btn") && !t.disabled) {
        const p = parseInt(t.getAttribute("data-page"), 10);
        if (Number.isFinite(p)) {
          state.page = p;
          load();
        }
      }
    };
  }

  // Monta query string para filtros (se sua API aceitar)
  function qs(params) {
    const u = new URLSearchParams();
    Object.entries(params).forEach(([k,v]) => {
      if (v !== undefined && v !== null && String(v).trim() !== "") u.set(k, v);
    });
    const s = u.toString();
    return s ? `?${s}` : "";
  }

  // Carrega itens da API
  async function load() {
    // Se sua API ainda não suporta q/ordem, só passe page:
    // const url = `/api/posts/?page=${state.page}`;
    // Se já suporta (ex.: /api/posts/?page=1&q=foo&ordem=recente):
    const url = `/api/posts/${qs({ page: state.page, q: state.q, ordem: state.ordem })}`;

    try {
      const r = await fetch(url, { method: "GET" });
      if (!r.ok) throw new Error(`Falha ao buscar posts (${r.status})`);
      const data = await r.json();

      // Aceita tanto "items" quanto "Objectitems" (pelo seu console.log)
      const items = data.items || data.Objectitems || [];
      renderPosts(items);
      renderPaginator(data.meta);
    } catch (e) {
      console.error(e);
      if ($list && !$list.innerHTML) {
        $list.innerHTML = `<p style="color:#dc2626">Erro ao carregar as notícias.</p>`;
      }
      if ($vazio) $vazio.style.display = "block";
    }
  }

  // Listeners de filtros
  $q?.addEventListener("input", (e) => {
    state.q = e.target.value || "";
    state.page = 1;
    // debounce simples
    clearTimeout($q.__t);
    $q.__t = setTimeout(load, 300);
  });

  $ordem?.addEventListener("change", (e) => {
    state.ordem = e.target.value || "recente";
    state.page = 1;
    load();
  });

  $btnAtt?.addEventListener("click", () => {
    state.page = 1;
    load();
  });

  // Start
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => load(), { once: true });
  } else {
    load();
  }
})();
