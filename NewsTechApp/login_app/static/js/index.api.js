// =======================
// Elementos
// =======================
const listEl   = document.getElementById("lista-noticias") || document.getElementById("list");
const emptyEl  = document.getElementById("vazio")          || document.getElementById("empty");
const countEl  = document.getElementById("contador")       || document.getElementById("count");
const searchEl = document.getElementById("q")              || document.getElementById("search");
const refreshBtn = document.getElementById("btn-atualizar");

// =======================
// Estado da paginação
// =======================
let currentPage = 1;
let totalPages  = 1;
const PER_PAGE  = 10;

// =======================
// Helpers
// =======================
function safeSetText(el, text) { if (el) el.textContent = text; }
function setCount(n) { safeSetText(countEl, `${n} ${n === 1 ? "item" : "itens"}`); }

function escapeHtml(s = "") {
  return s.replace(/[&<>"']/g, c => (
    {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]
  ));
}

// =======================
// API
// =======================
async function apiList(q = "", page = 1) {
  const u = new URL("/api/posts", window.location.origin);
  if (q) u.searchParams.set("q", q);
  u.searchParams.set("page", page);
  u.searchParams.set("per_page", PER_PAGE);

  const r = await fetch(u, {
    headers: { "Accept": "application/json" },
    credentials: "include" // mantém cookies/sessão
  });
  if (!r.ok) throw new Error(`Falha ao listar (${r.status})`);
  const data = await r.json();

  // lê meta da API
  currentPage = data?.meta?.page  || 1;
  totalPages  = data?.meta?.pages || 1;

  // aceita { items: [...] } ou { Objectitems: [...] } ou lista direta
  const items = Array.isArray(data) ? data : (data.items || data.Objectitems || []);
  return items;
}

async function apiDelete(id) {
  const r = await fetch(`/api/posts/${id}`, { method: "DELETE", credentials: "include" });
  if (!r.ok) throw new Error(`Falha ao excluir (${r.status})`);
}

// =======================
// UI
// =======================
function postCard(p) {
  const div = document.createElement("div");
  div.className = "card";

  const titulo   = p.titulo ?? "Sem título";
  const conteudo = p.conteudo ?? "";
  const autor    = p.autor_nome || p.autor_email || p.autor || "Autor desconhecido";
  const dt       = p.created_at || p.criado_em || "";
  const dtStr    = dt ? new Date(dt).toLocaleString() : "";

  const imgHtml = p.image_url
    ? `<img class="thumb" src="${p.image_url}" alt="Imagem da notícia" loading="eager"
         onerror="this.dataset.err=1;console.warn('Falha ao carregar imagem:', this.src)"/>`
    : "";

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
    b.className = isActive ? "btn active" : "btn";
    b.style.margin = "0 .25rem";
    b.addEventListener("click", onClick);
    return b;
  };

  // anterior
  pagEl.appendChild(
    mkBtn("◀", currentPage === 1, () => { if (currentPage > 1) { currentPage--; render(searchEl?.value || ""); } })
  );

  // janela de páginas
  const windowSize = 5;
  let start = Math.max(1, currentPage - Math.floor(windowSize / 2));
  let end   = Math.min(totalPages, start + windowSize - 1);
  if (end - start + 1 < windowSize) start = Math.max(1, end - windowSize + 1);

  for (let i = start; i <= end; i++) {
    const btn = mkBtn(String(i), i === currentPage, () => {
      if (currentPage !== i) { currentPage = i; render(searchEl?.value || ""); }
    }, i === currentPage);
    pagEl.appendChild(btn);
  }

  // próximo
  pagEl.appendChild(
    mkBtn("▶", currentPage === totalPages, () => { if (currentPage < totalPages) { currentPage++; render(searchEl?.value || ""); } })
  );

  // info opcional
  const info = document.createElement("span");
  info.style.marginLeft = ".5rem";
  info.style.opacity = ".7";
  info.textContent = `Página ${currentPage} de ${totalPages}`;
  pagEl.appendChild(info);
}

async function render(q = "") {
  if (!listEl) {
    console.error('[index.api] Container da lista não encontrado (#lista-noticias ou #list).');
    return;
  }

  try {
    const items = await apiList(q, currentPage);
    listEl.innerHTML = "";

    if (!Array.isArray(items) || items.length === 0) {
      if (emptyEl) emptyEl.style.display = "block";
      setCount(0);
    } else {
      if (emptyEl) emptyEl.style.display = "none";
      for (const p of items) listEl.appendChild(postCard(p));
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
    // mesmo em erro, tenta desenhar paginação com estado atual
    renderPagination();
  }
}

// =======================
// Eventos
// =======================

// exclusão delegada
document.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-del]");
  if (!btn) return;
  const id = Number(btn.dataset.del);
  if (!Number.isFinite(id)) return;

  try {
    if (confirm("Excluir esta postagem?")) {
      await apiDelete(id);
      // mantém a página atual ao excluir
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

// botão atualizar — mantém a página atual
refreshBtn?.addEventListener("click", () => {
  render(searchEl?.value || "");
});

// start (garante DOM pronto)
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => render(), { once: true });
} else {
  render();
}

// Se a página foi restaurada do bfcache, força um refresh leve mantendo página
window.addEventListener("pageshow", (e) => {
  if (e.persisted) render(searchEl?.value || "");
});
