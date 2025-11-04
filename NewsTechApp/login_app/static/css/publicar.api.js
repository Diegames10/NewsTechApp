const form = document.getElementById("form-post");
const idEl = document.getElementById("id");
const tituloEl = document.getElementById("titulo");
const autorEl = document.getElementById("autor");
const conteudoEl = document.getElementById("conteudo");

function qsId(){
  const id = new URL(location.href).searchParams.get("id");
  return id ? Number(id) : null;
}

async function apiGet(id){
  const r = await fetch(`/api/posts/${id}`, {headers:{ "Accept":"application/json" }});
  if (!r.ok) throw new Error("Falha ao carregar");
  return r.json();
}
async function apiCreate(payload){
  const r = await fetch(`/api/posts`, {
    method:"POST",
    headers:{ "Content-Type":"application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error("Falha ao criar");
  return r.json();
}
async function apiUpdate(id, payload){
  const r = await fetch(`/api/posts/${id}`, {
    method:"PUT",
    headers:{ "Content-Type":"application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error("Falha ao atualizar");
  return r.json();
}

async function boot(){
  const id = qsId();
  if (!id) return;
  const p = await apiGet(id);
  idEl.value = p.id;
  tituloEl.value = p.titulo;
  autorEl.value = p.autor;
  conteudoEl.value = p.conteudo;
  document.title = `Editar: ${p.titulo} • Portal`;
}

form.addEventListener("submit", async (e)=>{
  e.preventDefault();
  const payload = {
    titulo: tituloEl.value.trim(),
    autor: autorEl.value.trim(),
    conteudo: conteudoEl.value.trim(),
  };
  if (!payload.titulo || !payload.autor || !payload.conteudo){
    alert("Preencha todos os campos.");
    return;
  }
  const id = idEl.value ? Number(idEl.value) : null;
  if (id) await apiUpdate(id, payload);
  else await apiCreate(payload);
  location.href = "./index.html";
});

boot();
