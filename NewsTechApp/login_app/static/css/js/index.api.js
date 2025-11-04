const listEl = document.getElementById("list");
const emptyEl = document.getElementById("empty");
const countEl = document.getElementById("count");
const searchEl = document.getElementById("search");

function escapeHtml(s=""){return s.replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}

async function apiList(q=""){
  const u = new URL("/api/posts", window.location.origin);
  if (q) u.searchParams.set("q", q);
  const r = await fetch(u, {headers:{ "Accept":"application/json" }});
  if (!r.ok) throw new Error("Falha ao listar");
  return r.json();
}

async function apiDelete(id){
  const r = await fetch(`/api/posts/${id}`, { method:"DELETE" });
  if (!r.ok) throw new Error("Falha ao excluir");
}

function postCard(p){
  const div = document.createElement("div");
  div.className = "card";
  div.innerHTML = `
    <h3 style="margin:0 0 .25rem 0;">${escapeHtml(p.titulo)}</h3>
    <div class="muted" style="margin-bottom:.5rem;">
      por ${escapeHtml(p.autor)} • ${new Date(p.criado_em).toLocaleString()}
    </div>
    <p style="white-space:pre-wrap; margin-bottom:.75rem;">${escapeHtml(p.conteudo)}</p>
    <div style="display:flex; gap:.5rem;">
      <a class="btn" href="./publicar.html?id=${p.id}">Editar</a>
      <button class="btn danger" data-del="${p.id}">Excluir</button>
    </div>
  `;
  return div;
}

async function render(q=""){
  const items = await apiList(q);
  listEl.innerHTML = "";
  if (!items.length){ emptyEl.style.display="block"; countEl.textContent="0 itens"; return; }
  emptyEl.style.display="none";
  items.forEach(p=>listEl.appendChild(postCard(p)));
  countEl.textContent = `${items.length} ${items.length===1?"item":"itens"}`;
}

document.addEventListener("click", async (e)=>{
  const btn = e.target.closest("[data-del]");
  if (!btn) return;
  const id = Number(btn.dataset.del);
  if (confirm("Excluir esta postagem?")){
    await apiDelete(id);
    await render(searchEl.value);
  }
});

searchEl?.addEventListener("input",(e)=>{
  clearTimeout(searchEl._t);
  searchEl._t = setTimeout(()=>render(e.target.value), 200);
});

render();
