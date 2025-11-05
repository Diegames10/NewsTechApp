const form       = document.getElementById("form-post");
const idEl       = document.getElementById("id");
const tituloEl   = document.getElementById("titulo");
const autorEl    = document.getElementById("autor");
const conteudoEl = document.getElementById("conteudo");
const imageEl    = document.getElementById("image");

// Use URL literal ou injete window.ROUTES.home no template
const HOME_URL = "/home";
const LOGIN_URL = "/login";

function qsId() {
  const id = new URL(location.href).searchParams.get("id");
  return id ? Number(id) : null;
}

async function apiGet(id) {
  const r = await fetch(`/api/posts/${id}`, {
    headers: { "Accept": "application/json" },
    credentials: "include",
  });
  if (r.status === 401) { location.href = LOGIN_URL; return; }
  if (!r.ok) throw new Error("Falha ao carregar");
  return r.json();
}

async function apiCreateFD(fd) {
  const r = await fetch(`/api/posts`, {
    method: "POST",
    body: fd,
    credentials: "include",
  });
  if (r.status === 401) { location.href = LOGIN_URL; return; }
  if (!r.ok) throw new Error("Falha ao criar");
  return r.json();
}

async function apiUpdateFD(id, fd) {
  const r = await fetch(`/api/posts/${id}`, {
    method: "PUT",
    body: fd,
    credentials: "include",
  });
  if (r.status === 401) { location.href = LOGIN_URL; return; }
  if (!r.ok) throw new Error("Falha ao atualizar");
  return r.json();
}

async function preencherAutor() {
  try {
    const me = await fetch("/api/me", { credentials: "include" }).then(r => r.json());
    if (me?.logged) {
      autorEl.value = me.username || me.email || "Usuário";
      autorEl.readOnly = true; // evita edição manual
    } else {
      location.href = LOGIN_URL;
    }
  } catch {
    location.href = LOGIN_URL;
  }
}

async function boot() {
  await preencherAutor();

  const id = qsId();
  if (!id) return;

  try {
    const p = await apiGet(id);
    if (!p) return; // já redirecionou
    idEl.value       = p.id;
    tituloEl.value   = p.titulo || "";
    autorEl.value    = p.autor || autorEl.value || "";
    conteudoEl.value = p.conteudo || "";
    document.title   = `Editar: ${p.titulo} • Portal`;
  } catch (e) {
    alert(e.message || "Erro ao carregar a postagem");
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const id = idEl.value ? Number(idEl.value) : null;

  const fd = new FormData();
  fd.append("titulo",   tituloEl.value.trim());
  fd.append("autor",    autorEl.value.trim());
  fd.append("conteudo", conteudoEl.value.trim());
  if (imageEl.files && imageEl.files[0]) {
    fd.append("image", imageEl.files[0]);
  }

  if (!fd.get("titulo") || !fd.get("autor") || !fd.get("conteudo")) {
    alert("Preencha todos os campos.");
    return;
  }

  try {
    if (id) await apiUpdateFD(id, fd);
    else    await apiCreateFD(fd);
    location.href = HOME_URL; // nada de Jinja aqui
  } catch (e) {
    alert(e.message || "Erro ao salvar a postagem");
  }
});

boot();
