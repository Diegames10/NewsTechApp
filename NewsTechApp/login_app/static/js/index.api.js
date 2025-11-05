// tenta pegar pelos ids "novos" e, se não existir, pelos "antigos"
const listEl = document.querySelector("#lista-noticias, #list") || document.getElementById("list");
const emptyEl  = document.getElementById("vazio")          || document.getElementById("empty");
const countEl  = document.getElementById("contador")       || document.getElementById("count");
const searchEl = document.getElementById("q")              || document.getElementById("search");

function escapeHtml(s=""){
  return s.replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}

async function apiList(q=""){
  const u = new URL("/api/posts", window.location.origin);
  if (q) u.searchParams.set("q", q);
  const r = await fetch(u, {
    headers: { "Accept": "application/json" },
    credentials: "include"
  });
  if (!r.ok) throw new Error("Falha ao listar");
  return r.json();
}

async function apiDelete(id){
  const r = await fetch(`/api/posts/${id}`, {
    method: "DELETE",
    credentials: "include"
  });
  if (!r.ok) throw new Error("Falha ao excluir");
}

function postCard(p){
  const div = document.createElement("div");
  div.className = "card";

  // log para ver o que está chegando
  console.log("POST:", p);

  const imgHtml = p.image_url
    ? `<img class="thumb" src="${p.image_url}" alt="Imagem da notícia" loading="lazy" onerror="this.dataset.err=1;console.warn('Falha ao carregar imagem:', this.src)"/>`
    : "";

  div.innerHTML = `
    ${imgHtml}
    <h3 style="margin:0 0 .25rem 0;">${escapeHtml(p.titulo)}</h3>
    <div class="muted" style="margin-bottom:.5rem;">
      por ${escapeHtml(p.autor)} • ${p.criado_em ? new Date(p.criado_em).toLocaleString() : ""}
    </div>
    <p style="white-space:pre-wrap; margin-bottom:.75rem;">${escapeHtml(p.conteudo)}</p>
    <div style="display:flex; gap:.5rem;">
      <a class="btn" href="/publicar?id=${p.id}">Editar</a>
      <button class="btn danger" data-del="${p.id}">Excluir</button>
    </div>
  `;
  return div;
}


async function render(q=""){
  const items = await apiList(q);
  if (!listEl) return; // segurança

  listEl.innerHTML = "";
  if (!items.length){
    if (emptyEl) emptyEl.style.display = "block";
    if (countEl) countEl.textContent = "0 itens";
    return;
  }

  if (emptyEl) emptyEl.style.display = "none";
  items.forEach(p => listEl.appendChild(postCard(p)));
  if (countEl) countEl.textContent = `${items.length} ${items.length===1?"item":"itens"}`;
}

document.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-del]");
  if (!btn) return;
  const id = Number(btn.dataset.del);
  if (confirm("Excluir esta postagem?")){
    await apiDelete(id);
    await render(searchEl?.value || "");
  }
});

// busca em tempo real
searchEl?.addEventListener("input", (e) => {
  clearTimeout(searchEl._t);
  searchEl._t = setTimeout(() => render(e.target.value), 200);
});

// start
render();
