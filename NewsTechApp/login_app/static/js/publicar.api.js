const form      = document.getElementById("form-post");
const idEl      = document.getElementById("id");
const tituloEl  = document.getElementById("titulo");
const autorEl   = document.getElementById("autor");
const conteudoEl= document.getElementById("conteudo");
const imageEl   = document.getElementById("image");

function qsId(){
  const id = new URL(location.href).searchParams.get("id");
  return id ? Number(id) : null;
}

async function apiGet(id){
  const r = await fetch(`/api/posts/${id}`, { headers: { "Accept":"application/json" } });
  if (!r.ok) throw new Error("Falha ao carregar");
  return r.json();
}

async function apiCreateFD(fd){
  const r = await fetch(`/api/posts`, { method:"POST", body: fd });
  if (!r.ok) throw new Error("Falha ao criar");
  return r.json();
}

async function apiUpdateFD(id, fd){
  const r = await fetch(`/api/posts/${id}`, { method:"PUT", body: fd });
  if (!r.ok) throw new Error("Falha ao atualizar");
  return r.json();
}

async function boot(){
  const id = qsId();
  if (!id) return;
  const p = await apiGet(id);
  idEl.value       = p.id;
  tituloEl.value   = p.titulo || "";
  autorEl.value    = p.autor || "";
  conteudoEl.value = p.conteudo || "";
  document.title   = `Editar: ${p.titulo} • Portal`;
}

form.addEventListener("submit", async (e)=>{
  e.preventDefault();

  const id = idEl.value ? Number(idEl.value) : null;

  const fd = new FormData();
  fd.append("titulo",   tituloEl.value.trim());
  fd.append("autor",    autorEl.value.trim());
  fd.append("conteudo", conteudoEl.value.trim());
  if (imageEl.files && imageEl.files[0]) {
    fd.append("image", imageEl.files[0]);
  }

  if (!fd.get("titulo") || !fd.get("autor") || !fd.get("conteudo")){
    alert("Preencha todos os campos.");
    return;
  }

  if (id) await apiUpdateFD(id, fd);
  else    await apiCreateFD(fd);

  location.href = "{{ url_for('auth.home') }}"; // volta pra listagem
});

boot();
