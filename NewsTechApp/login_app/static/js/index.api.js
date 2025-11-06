
const listEl  = document.getElementById("lista-noticias") || document.getElementById("list");   // <-- antes estava querySelector("lista-noticias") (sem #)
const emptyEl = document.getElementById("vazio")          || document.getElementById("empty");
const countEl = document.getElementById("contador")       || document.getElementById("count");
const searchEl= document.getElementById("q")              || document.getElementById("search");

// helpers
function safeSetText(el, text) { if (el) el.textContent = text; }
function setCount(n) { safeSetText(countEl, `${n} ${n === 1 ? "item" : "itens"}`); }

function escapeHtml(s = "") {
  return s.replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}

async function apiList(q = "") {
  const u = new URL("/api/posts", window.location.origin);
  if (q) u.searchParams.set("q", q);
  const r = await fetch(u, {
    headers: { "Accept": "application/json" },
    credentials: "include" // mantém cookies/sessão
  });
  if (!r.ok) throw new Error(`Falha ao listar (${r.status})`);
  const data = await r.json();

  // aceita { items: [...] } ou { Objectitems: [...] } ou lista direta
  const items = Array.isArray(data) ? data : (data.items || data.Objectitems || []);
  return items;
}

async function apiDelete(id) {
  const r = await fetch(`/api/posts/${id}`, { method: "DELETE", credentials: "include" });
  if (!r.ok) throw new Error(`Falha ao excluir (${r.status})`);
}

function postCard(p) {
  const div = document.createElement("div");
  div.className = "card";

  // log para inspecionar payload
  console.log("POST:", p);

  const titulo = p.titulo ?? "Sem título";
  const conteudo = p.conteudo ?? "";
  const autor = p.autor_nome || p.autor_email || p.autor || "Autor desconhecido";
  const dt = p.created_at || p.criado_em || "";
  const dtStr = dt ? new Date(dt).toLocaleString() : "";

  const imgHtml = p.image_url
    ? `<img class="thumb" src="${p.image_url}" alt="Imagem da notícia" loading="lazy"
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

async function render(q = "") {
  // guarda anti-erro: se o container não existe, apenas loga e sai
  if (!listEl) {
    console.error('[index.api] Container da lista não encontrado (#lista-noticias ou #list).');
    return;
  }

  try {
    const items = await apiList(q);
    console.log("LISTA:", items); // confirme que vem image_url

    listEl.innerHTML = "";

    if (!Array.isArray(items) || items.length === 0) {
      if (emptyEl) emptyEl.style.display = "block";
      setCount(0);
      return;
    }

    if (emptyEl) emptyEl.style.display = "none";

    for (const p of items) {
      listEl.appendChild(postCard(p));
    }
    setCount(items.length);
  } catch (err) {
    console.error(err);
    // estado de erro amigável
    if (listEl && !listEl.innerHTML) {
      listEl.innerHTML = `<p style="color:#dc2626">Erro ao carregar as notícias.</p>`;
    }
    if (emptyEl) emptyEl.style.display = "block";
    setCount(0);
  }
}

// exclusão delegada
document.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-del]");
  if (!btn) return;
  const id = Number(btn.dataset.del);
  if (!Number.isFinite(id)) return;

  try {
    if (confirm("Excluir esta postagem?")) {
      await apiDelete(id);
      await render(searchEl?.value || "");
    }
  } catch (err) {
    console.error(err);
    alert("Não foi possível excluir a postagem.");
  }
});

// busca em tempo real (debounce)
searchEl?.addEventListener("input", (e) => {
  clearTimeout(searchEl._t);
  searchEl._t = setTimeout(() => render(e.target.value), 250);
});

// start (garante DOM pronto)
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => render(), { once: true });
} else {
  render();
}
