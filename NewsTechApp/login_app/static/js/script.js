/** =========================
 *  MENU / PERFIL
 * ========================= */
const perfilBtn = document.getElementById("perfil-btn");
const perfilMenu = document.getElementById("perfil-menu");

if (perfilBtn && perfilMenu) {
  perfilBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    perfilMenu.style.display = perfilMenu.style.display === "block" ? "none" : "block";
  });
  document.addEventListener("click", () => {
    if (perfilMenu.style.display === "block") perfilMenu.style.display = "none";
  });
  perfilMenu.addEventListener("click", (e) => e.stopPropagation());
}

/** =========================
 *  TEMA ESCURO / CLARO
 * ========================= */
const toggleTema = document.getElementById("toggle-tema");
const body = document.body;

function aplicarTemaInicial() {
  const salvo = localStorage.getItem("tema"); // 'escuro' | 'claro' | null
  const prefereEscuro = window.matchMedia?.("(prefers-color-scheme: dark)").matches;
  if (salvo === "escuro" || (!salvo && prefereEscuro)) {
    body.classList.add("dark");
    if (toggleTema) toggleTema.textContent = "☀️ Modo Claro";
  } else {
    body.classList.remove("dark");
    if (toggleTema) toggleTema.textContent = "🌙 Modo Escuro";
  }
}
aplicarTemaInicial();

if (toggleTema) {
  toggleTema.addEventListener("click", () => {
    const isDark = body.classList.toggle("dark");
    toggleTema.textContent = isDark ? "☀️ Modo Claro" : "🌙 Modo Escuro";
    localStorage.setItem("tema", isDark ? "escuro" : "claro");
  });
}

/** =========================
 *  API REMOTA (Flask)
 * ========================= */
async function apiMe() {
  const r = await fetch("/api/me", { credentials: "same-origin" });
  if (!r.ok) return { logged: false };
  return r.json();
}

async function apiListPosts({ q = "", order = "recente", page = 1, page_size = 10 } = {}) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (order) params.set("order", order);
  params.set("page", page);
  params.set("page_size", page_size);

  const r = await fetch(`/api/posts?${params.toString()}`, { credentials: "same-origin" });
  if (!r.ok) throw new Error(`Falha ao listar posts: ${r.status}`);
  return r.json(); // esperado: {items, total, page, page_size}
}

async function apiCreatePost({ titulo, conteudo, imagemDataURL }) {
  const r = await fetch("/api/posts", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ titulo, conteudo, imagemDataURL })
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

async function apiUpdatePost(id, { titulo, conteudo, imagemDataURL }) {
  const r = await fetch(`/api/posts/${id}`, {
    method: "PUT",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ titulo, conteudo, imagemDataURL })
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

async function apiDeletePost(id) {
  const r = await fetch(`/api/posts/${id}`, {
    method: "DELETE",
    credentials: "same-origin"
  });
  if (!r.ok) throw new Error(await r.text());
  return true;
}

/** =========================
 *  UTIL
 * ========================= */
function fileToDataURL(file) {
  return new Promise((resolve, reject) => {
    if (!file) return resolve(null);
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

/** =========================
 *  PUBLICAR (página publicar.html)
 * ========================= */
const form = document.getElementById("form-noticia");
if (form) {
  // pré-preenche autor (UX) — back já sabe quem é pelo cookie
  apiMe().then(me => {
    const autor = document.getElementById("autor");
    if (me.logged && autor && !autor.value) {
      autor.value = me.username || me.email || "Usuário";
    }
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const titulo = document.getElementById("titulo").value.trim();
    const conteudo = document.getElementById("conteudo").value.trim();
    const imagemFile = document.getElementById("imagem").files[0];

    if (!titulo || !conteudo) {
      alert("Preencha título e conteúdo.");
      return;
    }

    try {
      const me = await apiMe();
      if (!me.logged) {
        alert("Faça login para publicar.");
        return;
      }
      const imagemDataURL = await fileToDataURL(imagemFile);
      await apiCreatePost({ titulo, conteudo, imagemDataURL });
      alert("Notícia publicada com sucesso!");
      form.reset();
      const preview = document.getElementById("preview-noticia");
      if (preview) preview.remove();
    } catch (err) {
      console.error(err);
      alert("Erro ao publicar: " + err.message);
    }
  });

  // preview da imagem
  const inputImg = document.getElementById("imagem");
  if (inputImg) {
    inputImg.addEventListener("change", () => {
      const file = inputImg.files && inputImg.files[0];
      if (!file) return;
      let preview = document.getElementById("preview-noticia");
      if (!preview) {
        preview = document.createElement("img");
        preview.id = "preview-noticia";
        preview.style.maxWidth = "320px";
        preview.style.display = "block";
        preview.style.marginTop = "8px";
        inputImg.parentElement.appendChild(preview);
      }
      const reader = new FileReader();
      reader.onload = () => (preview.src = reader.result);
      reader.readAsDataURL(file);
    });
  }
}

/** =========================
 *  LISTAGEM (página index.html)
 * ========================= */
const PAGE_SIZE = 10;

const elLista = document.getElementById("lista-noticias");
const elVazio = document.getElementById("vazio");
const elBusca = document.getElementById("q");
const elOrdem = document.getElementById("ordem");
const elPag = document.getElementById("paginacao");

function getPageFromURL() {
  const params = new URLSearchParams(location.search);
  const p = parseInt(params.get("p") || "1", 10);
  return isNaN(p) || p < 1 ? 1 : p;
}
function setPageInURL(p) {
  const params = new URLSearchParams(location.search);
  params.set("p", String(p));
  history.replaceState(null, "", `${location.pathname}?${params.toString()}`);
}

function renderPaginacao(totalPages, pageAtual) {
  if (!elPag) return;
  elPag.innerHTML = "";
  if (totalPages <= 1) return;

  const mkBtn = (label, page, {disabled=false, active=false} = {}) => {
    const btn = document.createElement("button");
    btn.className = "page-btn" + (active ? " active" : "");
    btn.textContent = label;
    btn.disabled = !!disabled;
    btn.addEventListener("click", () => {
      setPageInURL(page);
      atualizarLista(); // re-render
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
    return btn;
  };

  elPag.appendChild(mkBtn("« Anterior", pageAtual - 1, { disabled: pageAtual <= 1 }));

  const windowSize = 7;
  let start = Math.max(1, pageAtual - Math.floor(windowSize/2));
  let end = start + windowSize - 1;
  if (end > totalPages) { end = totalPages; start = Math.max(1, end - windowSize + 1); }

  if (start > 1) {
    elPag.appendChild(mkBtn("1", 1, { active: pageAtual === 1 }));
    if (start > 2) elPag.appendChild(document.createTextNode("…"));
  }

  for (let p = start; p <= end; p++) {
    elPag.appendChild(mkBtn(String(p), p, { active: p === pageAtual }));
  }

  if (end < totalPages) {
    if (end < totalPages - 1) elPag.appendChild(document.createTextNode("…"));
    elPag.appendChild(mkBtn(String(totalPages), totalPages, { active: pageAtual === totalPages }));
  }

  elPag.appendChild(mkBtn("Próxima »", pageAtual + 1, { disabled: pageAtual >= totalPages }));
}

function renderCards(items) {
  if (!elLista || !elVazio) return;
  elLista.innerHTML = "";

  if (!items.length) {
    elVazio.style.display = "block";
    return;
  }
  elVazio.style.display = "none";

  items.forEach(n => {
    const card = document.createElement("article");
    card.className = "card-noticia";

    const imgSrc = n.imagem_url || n.imagemDataURL;
    if (imgSrc) {
      const img = document.createElement("img");
      img.src = imgSrc;
      img.alt = `Imagem de ${n.titulo}`;
      img.className = "img-noticia";
      img.loading = "lazy";
      card.appendChild(img);
    }

    const h3 = document.createElement("h3");
    h3.textContent = n.titulo;
    card.appendChild(h3);

    const meta = document.createElement("small");
    const dataFmt = new Date(n.created_at || n.createdAt || Date.now()).toLocaleString("pt-BR");
    const autor = n.autor || n.author || "Autor";
    meta.textContent = `Por ${autor} • ${dataFmt}`;
    card.appendChild(meta);

    const p = document.createElement("p");
    p.innerHTML = (n.conteudo || n.content || "").replace(/\n/g, "<br>");
    card.appendChild(p);

    // ações (editar/apagar) — precisa de rotas PUT/DELETE no backend
    // const actions = document.createElement("div");
    // actions.className = "card-actions";
    // const btnDel = document.createElement("button");
    // btnDel.className = "btn danger";
    // btnDel.textContent = "Excluir";
    // btnDel.onclick = async () => {
    //   if (!confirm("Excluir esta postagem?")) return;
    //   await apiDeletePost(n.id);
    //   atualizarLista();
    // };
    // actions.appendChild(btnDel);
    // card.appendChild(actions);

    elLista.appendChild(card);
  });
}

async function atualizarLista({ resetPage=false } = {}) {
  if (!elLista) return;
  const q = elBusca ? elBusca.value.trim() : "";
  const order = elOrdem ? elOrdem.value : "recente";
  let page = getPageFromURL();
  if (resetPage) page = 1;

  const data = await apiListPosts({ q, order, page, page_size: PAGE_SIZE });
  const items = Array.isArray(data) ? data : (data.items || []);
  const total = Array.isArray(data) ? items.length : (data.total || items.length);
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  renderCards(items);
  renderPaginacao(totalPages, Array.isArray(data) ? page : (data.page || page));
}

// eventos da listagem
if (elBusca) elBusca.addEventListener("input", () => atualizarLista({ resetPage:true }));
if (elOrdem) elOrdem.addEventListener("change", () => atualizarLista({ resetPage:true }));
document.addEventListener("DOMContentLoaded", () => {
  if (elLista) atualizarLista();
});

/** =========================
 *  PERFIL (mostrar nome + sair)
 * ========================= */
document.addEventListener("DOMContentLoaded", () => {
  const perfilNome = document.getElementById("perfil-nome");
  const menuNome = document.getElementById("menu-nome");
  const btnSair = document.getElementById("btn-sair");
  const avatar = document.getElementById("avatar");
  const menuAvatar = document.getElementById("menu-avatar");

  apiMe()
    .then((me) => {
      if (me.logged) {
        const nome = me.username || "Usuário";
        if (perfilNome) perfilNome.textContent = nome;
        if (menuNome) menuNome.textContent = nome;

        if (btnSair) {
          btnSair.style.display = "block";
          btnSair.onclick = () => { window.location.href = "/logout"; };
        }

        if (me.avatar_url) {
          if (avatar) avatar.src = me.avatar_url;
          if (menuAvatar) menuAvatar.src = me.avatar_url;
        }
      } else {
        if (perfilNome) perfilNome.textContent = "Entrar";
        if (menuNome) menuNome.textContent = "Visitante";
        if (btnSair) btnSair.style.display = "none";
      }
    })
    .catch((err) => console.error("Falha ao buscar /api/me:", err));
});
