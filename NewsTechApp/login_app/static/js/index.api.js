// static/js/index.api.js

const $lista         = document.getElementById("lista-noticias");
const $vazio         = document.getElementById("vazio");
const $q             = document.getElementById("q");
const $ordem         = document.getElementById("ordem");
const $btnAtualizar  = document.getElementById("btn-atualizar");
const $paginacao     = document.getElementById("paginacao");

const publicarUrl = document.body?.dataset?.publicarUrl || "/publicar";

function escapeHtml(s = "") {
  return s.replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}

async function apiList(q = "", limit = 50) {
  const u = new URL("/api/posts", window.location.origin);
  if (q)     u.searchParams.set("q", q);
  if (limit) u.searchParams.set("limit", String(limit));
  const r = await fetch(u, { headers: { "Accept": "application/json" } });
  if (!r.ok) throw new Error("Falha ao listar");
  return r.json();
}

async function apiDelete(id) {
  const r = await fetch(`/api/posts/${id}`, { method: "DELETE" });
  if (!r.ok) throw new Error("Falha ao excluir");
}

function cardHtml(p) {
  const img = p.image_url
    ? `<img class="img-noticia" src="${p.image_url}" alt="${escapeHtml(p.titulo || 'Imagem da notícia')}" style="max-width:100%;border-radius:10px;margin:.5rem 0">`
    : "";

  const criado     = p.criado_em     ? new Date(p.criado_em).toLocaleString()     : "";
  const atualizado = p.atualizado_em ? ` • Atualizado: ${new Date(p.atualizado_em).toLocaleString()}` : "";

  return `
    <article class="card-noticia" style="border:1px solid #e5e7eb;border-radius:12px;padding:14px;margin:0 0 12px 0;background:var(--bg);color:var(--text)">
      ${img}
      <h3 style="margin:.2rem 0">${escapeHtml(p.titulo || "")}</h3>
      <p class="meta" style="margin:.2rem 0;color:#555">
        <small>por ${escapeHtml(p.autor || "")} • ${criado}${atualizado}</small>
      </p>
      <p style="white-space:pre-wrap;margin:.4rem 0 0 0">${escapeHtml(p.conteudo || "")}</p>
      <div class="card-actions" style="display:flex;gap:.5rem;margin-top:.75rem;">
        <a class="btn" href="${publicarUrl}?id=${p.id}">Editar</a>
        <button class="btn danger" data-del="${p.id}">Excluir</button>
      </div>
    </article>
  `;
}

let posts = [];
let filtrados = [];
let pagina = 1;
const POR_PAGINA = 10;

function aplicarFiltros() {
  const termo = ($q?.value || "").trim().toLowerCase();

  filtrados = termo
    ? posts.filter(p =>
        (p.titulo || "").toLowerCase().includes(termo) ||
        (p.conteudo || "").toLowerCase().includes(termo)
      )
    : [...posts];

  // ordenação
  const ord = $ordem?.value || "recente";
  filtrados.sort((a, b) => {
    if (ord === "antigo")     return (a.id || 0) - (b.id || 0);
    if (ord === "titulo-az")  return (a.titulo || "").localeCompare(b.titulo || "");
    if (ord === "titulo-za")  return (b.titulo || "").localeCompare(a.titulo || "");
    // padrão: recentes primeiro
    return (b.id || 0) - (a.id || 0);
  });

  pagina = 1;
  render();
}

function render() {
  if (!$lista) return;

  // paginação simples
  const inicio = (pagina - 1) * POR_PAGINA;
  const fim    = inicio + POR_PAGINA;
  const pageItems = filtrados.slice(inicio, fim);

  if (!filtrados.length) {
    $lista.innerHTML = "";
    if ($vazio)      $vazio.style.display = "block";
    if ($paginacao)  $paginacao.innerHTML = "";
    return;
  }
  if ($vazio) $vazio.style.display = "none";

  $lista.innerHTML = pageItems.map(cardHtml).join("");

  // excluir
  $lista.querySelectorAll("[data-del]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = Number(btn.dataset.del);
      if (confirm("Excluir esta postagem?")) {
        await apiDelete(id);
        await carregar(); // recarrega do servidor mantendo imagem/datas corretas
      }
    });
  });

  // paginação
  if ($paginacao) {
    const totalPag = Math.max(1, Math.ceil(filtrados.length / POR_PAGINA));
    const mk = (num, label = num) =>
      `<button class="btn ${num === pagina ? "secondary" : ""}" data-page="${num}" ${num === pagina ? "disabled" : ""} style="margin:2px 4px">${label}</button>`;

    const anterior = pagina > 1        ? mk(pagina - 1, "« Anterior") : "";
    const proxima  = pagina < totalPag ? mk(pagina + 1, "Próxima »")  : "";

    $paginacao.innerHTML = `
      <div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center;justify-content:center;padding:8px 0">
        ${anterior}
        ${Array.from({ length: totalPag }, (_, i) => mk(i + 1)).join("")}
        ${proxima}
      </div>
    `;

    $paginacao.querySelectorAll("button[data-page]").forEach(b => {
      b.addEventListener("click", () => {
        pagina = parseInt(b.dataset.page, 10);
        render();
      });
    });
  }
}

async function carregar() {
  try {
    if ($lista) $lista.innerHTML = `<p style="color:#666">Carregando…</p>`;
    posts = await apiList($q?.value || "", 100);
    aplicarFiltros();
  } catch (e) {
    console.error(e);
    if ($lista)     $lista.innerHTML = `<p style="color:#b00">Erro ao carregar publicações.</p>`;
    if ($paginacao) $paginacao.innerHTML = "";
  }
}

// Eventos
$q?.addEventListener("input", () => {
  clearTimeout($q._t);
  $q._t = setTimeout(aplicarFiltros, 200);
});
$ordem?.addEventListener("change", aplicarFiltros);
$btnAtualizar?.addEventListener("click", carregar);

// Start
window.addEventListener("DOMContentLoaded", carregar);
