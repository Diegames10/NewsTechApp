// publicar.api.js

const form      = document.getElementById("form-post");
const idEl      = document.getElementById("id");        // hidden para edição
const tituloEl  = document.getElementById("titulo");
const autorEl   = document.getElementById("autor");
const conteudoEl= document.getElementById("conteudo");
const imageEl   = document.getElementById("image");     // <input type="file" name="image">

function qsId() {
  const id = new URL(location.href).searchParams.get("id");
  return id ? Number(id) : null;
}

// (opcional) lê CSRF do cookie se seu backend exigir header X-CSRF-Token
function readCookie(name) {
  const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return m ? decodeURIComponent(m.pop()) : null;
}
function csrfHeaders() {
  const csrf = readCookie("csrf_token");
  return csrf ? { "X-CSRF-Token": csrf } : {};
}

async function apiGet(id){
  const r = await fetch(`/api/posts/${id}`, { headers: { "Accept":"application/json" } });
  if (!r.ok) throw new Error("Falha ao carregar");
  return r.json();
}

// Cria via multipart
async function apiCreate(fd){
  const r = await fetch(`/api/posts`, {
    method: "POST",
    // IMPORTANTÍSSIMO: não defina Content-Type ao usar FormData
    headers: { ...csrfHeaders() },
    body: fd,
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`Falha ao criar: ${r.status} ${t}`);
  }
  return r.json();
}

// Atualiza via multipart (PUT)
async function apiUpdate(id, fd){
  const r = await fetch(`/api/posts/${id}`, {
    method: "PUT",
    headers: { ...csrfHeaders() },
    body: fd,
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`Falha ao atualizar: ${r.status} ${t}`);
  }
  return r.json();
}

async function boot(){
  const id = qsId();
  if (!id) return;
  const p = await apiGet(id);

  // Preenche campos
  idEl.value        = p.id;
  tituloEl.value    = p.titulo || "";
  autorEl.value     = p.autor || "";
  conteudoEl.value  = p.conteudo || "";

  // Se já existe imagem, guarda o filename em um data-attr para manter caso usuário não troque
  if (p.image_filename) {
    form.dataset.currentImage = p.image_filename;
  }
  document.title = `Editar: ${p.titulo || "Post"} • Portal`;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const titulo  = tituloEl.value.trim();
  const autor   = autorEl.value.trim();
  const conteudo= conteudoEl.value.trim();

  if (!titulo || !autor || !conteudo){
    alert("Preencha todos os campos.");
    return;
  }

  // Monta FormData
  const fd = new FormData();
  fd.append("titulo", titulo);
  fd.append("autor", autor);
  fd.append("conteudo", conteudo);

  // Se o usuário escolheu um novo arquivo, anexamos
  if (imageEl && imageEl.files && imageEl.files[0]) {
    fd.append("image", imageEl.files[0]);
  } else {
    // Se estamos editando e não trocou a imagem, avisa o backend para manter a atual
    if (form.dataset.currentImage) {
      fd.append("keep_image", "1");
    }
  }

  try {
    const id = idEl.value ? Number(idEl.value) : qsId();

    if (id) await apiUpdate(id, fd);
    else    await apiCreate(fd);

    // Redireciona de volta para o portal
    location.href = "/home"; // ou use uma variável global injetada pelo template
  } catch (err) {
    console.error(err);
    alert(err.message || "Erro ao salvar");
  }
});

boot();
