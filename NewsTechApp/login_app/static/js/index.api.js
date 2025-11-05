// static/js/index.api.js

const listEl  = document.getElementById("lista-noticias");
const emptyEl = document.getElementById("vazio");
const searchEl= document.getElementById("q");

function escapeHtml(s=""){return s.replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}

async function apiList(q=""){
  const u = new URL("/api/posts", window.location.origin);
  if (q) u.searchParams.set("q", q);
  const r = await fetch(u, { headers: { "Accept":"application/json" }});
  if (!r.ok) throw new Error("Falha ao listar");
  return r.json();
}

function renderCard(p){
  const criado = p.criado_em ? new Date(p.criado_em).toLocaleString() : "";
  const atualizado = p.atualizado_em ? ` • Atualizado: ${new Date(p.atualizado_em).toLocaleString()}` : "";
  const imgHtml = p.image_url ? `<img class="img-noticia" src="${p.image_url}" alt="${escapeHtml(p.titulo)}">` : "";
  return `
    <article class="card-noticia">
      ${imgHtml}
      <h3>${escapeHtml(p.titulo)}</h3>
      <small>Por ${escapeHtml(p.autor)} — ${criado}${atualizado}</small>
      <p>${escapeHtml(p.conteudo)}</p>
      <div class="card-actions">
        <a class="btn" href="{{ url_for('auth.publicar') }}?id=${p.id}">Editar</a>
        <button class="btn danger" data-del="${p.id}">Excluir</button>
      </div>
    </article>
  `;
}

async function render(q=""){
  const items = await apiList(q);
  listEl.innerHTML = "";
  if (!items.length){
    emptyEl.style.display = "block";
    return;
  }
  emptyEl.style.display = "none";
  listEl.innerHTML = items.map(renderCard).join("");
}

document.addEventListener("click", async (e)=>{
  const btn = e.target.closest("[data-del]");
  if (!btn) return;
  if (confirm("Excluir esta postagem?")){
    const id = Number(btn.dataset.del);
    const r = await fetch(`/api/posts/${id}`, { method: "DELETE" });
    if (!r.ok) { alert("Falha ao excluir"); return; }
    await render(searchEl?.value || "");
  }
});

searchEl?.addEventListener("input", (e)=>{
  clearTimeout(searchEl._t);
  searchEl._t = setTimeout(()=>render(e.target.value), 200);
});

window.addEventListener("DOMContentLoaded", () => render());
