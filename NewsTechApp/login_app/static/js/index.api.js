// =======================
// Elementos
// =======================
const listEl     = document.getElementById("lista-noticias") || document.getElementById("list");
const emptyEl    = document.getElementById("vazio")          || document.getElementById("empty");
const countEl    = document.getElementById("contador")       || document.getElementById("count");
const searchEl   = document.getElementById("q")              || document.getElementById("search");
const refreshBtn = document.getElementById("btn-atualizar");

// =======================
// Config/Estado
// =======================
let currentPage = 1;
let totalPages  = 1;
const PER_PAGE  = 10;

// imagens
const ABOVE_THE_FOLD   = 4;        // quantos cards carregam "eager"
const FALLBACK_ASPECT  = "16 / 9"; // reserva espaço p/ imagem

// =======================
/* Helpers */
// =======================
function safeSetText(el, text) { if (el) el.textContent = text; }
function setCount(n) { safeSetText(countEl, `${n} ${n === 1 ? "item" : "itens"}`); }

function escapeHtml(s = "") {
  return s.replace(/[&<>"']/g, c => (
    {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]
  ));
}

function ensureNumber(n, fallback = 0) {
  const x = Number(n);
  return Number.isFinite(x) ? x : fallback;
}

// =======================
/* API */
// =======================
async function apiList(q = "", page = 1) {
  const u = new URL("/api/posts", window.location.origin);
  if (q) u.searchParams.set("q", q);
  u.searchParams.set("page", ensureNumber(page, 1));
  u.searchParams.set("per_page", PER_PAGE);

  const r = await fetch(u, {
    headers: { "Accept": "application/json" },
    credentials: "include"
  });
  if (!r.ok) throw new Error(`Falha ao listar (${r.status})`);
  const data = await r.json();

  // meta da API
  currentPage = ensureNumber(data?.meta?.page, 1);
  totalPages  = ensureNumber(data?.meta?.pages, 1);

  // aceita { items: [...] } ou lista direta
  const items = Array.isArray(data) ? data : (data.items || []);
  return Array.isArray(items) ? items : [];
}

async function apiDelete(id) {
  const r = await fetch(`/api/posts/${id}`, { method: "DELETE", credentials: "include" });
  if (!r.ok) throw new Error(`Falha ao excluir (${r.status})`);
}

// =======================
/* UI */
// =======================
function postCard(p, idx = 0) {
  const div = document.createElement("div");
  div.className = "card";

  const titulo   = p.titulo ?? "Sem título";
  const conteudo = p.conteudo ?? "";
  const autor    = p.autor_nome || p.autor_email || p.autor || "Autor desconhecido";
  const dt       = p.created_at || p.criado_em || "";
  const dtStr    = dt ? new Date(dt).toLocaleString() : "";

  // primeiras imagens: eager + alta prioridade; demais: lazy
  const eager    = idx < ABOVE_THE_FOLD;
  const loading  = eager ? "eager" : "lazy";
  const priority = eager ? 'fetchpriority="high"' : "";

  const imgHtml = p.image_url ? `
    <img
      class="thumb"
      src="${p.image_url}"
      alt="Imagem da notícia"
      loading="${loading}"
      ${priority}
      decoding="async"
      style="width:100%; aspect-ratio:${FALLBACK_ASPECT}; object-fit:cover; background:#eee;"
      onerror="
        if (!this.dataset.retried) {
          this.dataset.retried = 1;
          this.src = this.src + (this.src.includes('?') ? '&' : '?') + 'b=' + Date.now();
          console.warn('Retry imagem com cache-buster:', this.src);
        } else {
          this.dataset.err = 1;
          console.warn('Falha ao carregar imagem (sem retry):', this.src);
        }
      "
    />
  ` : "";

  div.innerHTML = `
    ${imgHtml}
    <h3 style="margin:0 0 .25rem 0;">${escapeHtml(titulo)}</h3>
    <div class="muted" style="margin-bottom:.5rem;">
      por ${escapeHtml(autor)} ${dtStr ? `• ${dtStr}` : ""}
    </div>
    <p style="white-space:pre-wrap; margin-bottom:.75rem;">${
      escapeHtml(conteudo.length > 240 ? conteudo.slice(0, 240) + "..." : conteudo)
    }</p>
    <div style="display:flex; gap:.5rem; flex-wrap: wrap;">
      <a class="btn" href="/publicar?id=${p.id}">Editar</a>
      <button class="btn danger" data-del="${p.id}">Excluir</button>
    </div>
  `;
  return div;
}

function renderPagination() {
  const pagEl = document.getElementById("paginacao");
  if (!pagEl) return;
  pagEl.innerHTML = "";

  const mkBtn = (label, disabled, onClick, isActive = false) => {
    const b = document.createElement("button");
    b.textContent = label;
    b.disabled = !!disabled;
    b.className = "btn" + (isActive ? " active" : "");
    b.style.margin = "0 .25rem";
    b.addEventListener("click", onClick);
    return b;
  };

  // anterior
  pagEl.appendChild(
    mkBtn("◀", currentPage <= 1, () => {
      if (currentPage > 1) { currentPage--; render(searchEl?.value || ""); }
    })
  );

  // janela de páginas
  const windowSize = 5;
  let start = Math.max(1, currentPage - Math.floor(windowSize / 2));
  let end   = Math.min(totalPages, start + windowSize - 1);
  if (end - start + 1 < windowSize) start = Math.max(1, end - windowSize + 1);

  for (let i = start; i <= end; i++) {
    const isActive = i === currentPage;
    const btn = mkBtn(String(i), isActive, () => {
      if (!isActive) { currentPage = i; render(searchEl?.value || ""); }
    }, isActive);
    pagEl.appendChild(btn);
  }

  // próximo
  pagEl.appendChild(
    mkBtn("▶", currentPage >= totalPages, () => {
      if (currentPage < totalPages) { currentPage++; render(searchEl?.value || ""); }
    })
  );

  // info
  const info = document.createElement("span");
  info.style.marginLeft = ".5rem";
  info.style.opacity = ".7";
  info.textContent = `Página ${currentPage} de ${Math.max(totalPages, 1)}`;
  pagEl.appendChild(info);
}

async function render(q = "") {
  if (!listEl) {
    console.error("[index.api] Container da lista não encontrado (#lista-noticias ou #list).");
    return;
  }

  try {
    const items = await apiList(q, currentPage);
    listEl.innerHTML = "";

    if (!Array.isArray(items) || items.length === 0) {
      // Se a página atual ficou vazia mas ainda há páginas antes, volta 1 página
      if (currentPage > 1 && totalPages >= currentPage) {
        currentPage = Math.max(1, currentPage - 1);
        const retryItems = await apiList(q, currentPage);
        if (Array.isArray(retryItems) && retryItems.length) {
          retryItems.forEach((p, i) => listEl.appendChild(postCard(p, i)));
          setCount(retryItems.length);
          renderPagination();
          if (emptyEl) emptyEl.style.display = "none";
          return;
        }
      }
      if (emptyEl) emptyEl.style.display = "block";
      setCount(0);
    } else {
      if (emptyEl) emptyEl.style.display = "none";
      items.forEach((p, i) => listEl.appendChild(postCard(p, i)));
      setCount(items.length);
    }

    renderPagination();
  } catch (err) {
    console.error(err);
    if (listEl && !listEl.innerHTML) {
      listEl.innerHTML = `<p style="color:#dc2626">Erro ao carregar as notícias.</p>`;
    }
    if (emptyEl) emptyEl.style.display = "block";
    setCount(0);
    renderPagination(); // ainda mostra navegação com estado atual
  }
}

// =======================
/* Eventos */
// =======================

// exclusão delegada (manter página; se ficar vazia, recua 1 página)
document.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-del]");
  if (!btn) return;
  const id = ensureNumber(btn.dataset.del, NaN);
  if (!Number.isFinite(id)) return;

  try {
    if (confirm("Excluir esta postagem?")) {
      await apiDelete(id);
      // Recarrega; se a página ficar vazia, o render() já recua 1 página
      await render(searchEl?.value || "");
    }
  } catch (err) {
    console.error(err);
    alert("Não foi possível excluir a postagem.");
  }
});

// busca em tempo real (debounce) — reseta para página 1
searchEl?.addEventListener("input", (e) => {
  clearTimeout(searchEl._t);
  searchEl._t = setTimeout(() => {
    currentPage = 1;
    render(e.target.value);
  }, 250);
});

// botão atualizar — mantém a página atual e o filtro
refreshBtn?.addEventListener("click", () => {
  render(searchEl?.value || "");
});

// start (garante DOM pronto)
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => render(), { once: true });
} else {
  render();
}

// Se a página foi restaurada do bfcache, força um refresh leve mantendo a página/filtro
window.addEventListener("pageshow", (e) => {
  if (e.persisted) render(searchEl?.value || "");
});
