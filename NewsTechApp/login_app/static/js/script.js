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
 *  "BANCO DE DADOS" LOCAL
 *  IndexedDB: noticiasDB / store: noticias
 * ========================= */
const DB_NAME = "noticiasDB";
const DB_VERSION = 1;
const STORE = "noticias";

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onerror = () => reject(req.error);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: "id", autoIncrement: true });
        store.createIndex("created_at_idx", "created_at", { unique: false });
        store.createIndex("titulo_idx", "titulo", { unique: false });
      }
    };
    req.onsuccess = () => resolve(req.result);
  });
}

async function addNoticia(n) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.oncomplete = () => resolve(true);
    tx.onerror = () => reject(tx.error);
    tx.objectStore(STORE).add(n);
  });
}

async function getNoticias() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const store = tx.objectStore(STORE);
    const req = store.getAll();
    req.onsuccess = () => {
      const arr = req.result || [];
      arr.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      resolve(arr);
    };
    req.onerror = () => reject(req.error);
  });
}

async function exportarNoticiasJSON() {
  const dados = await getNoticias();
  const blob = new Blob([JSON.stringify(dados, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "noticias_local.json";
  a.click();
  URL.revokeObjectURL(url);
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
 *  FORM: salvar localmente
 * ========================= */
const form = document.getElementById("form-noticia");
if (form) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const titulo = document.getElementById("titulo").value.trim();
    const autor = document.getElementById("autor").value.trim();
    const conteudo = document.getElementById("conteudo").value.trim();
    const imagemFile = document.getElementById("imagem").files[0];

    if (!titulo || !autor || !conteudo) {
      alert("Preencha título, autor e conteúdo.");
      return;
    }

    try {
      const imagemDataURL = await fileToDataURL(imagemFile);
      const noticia = {
        titulo,
        autor,
        conteudo,
        imagemDataURL,
        created_at: new Date().toISOString()
      };
      await addNoticia(noticia);
      alert("Notícia salva LOCALMENTE com sucesso!");
      form.reset();
      const preview = document.getElementById("preview-noticia");
      if (preview) preview.remove();
    } catch (err) {
      console.error(err);
      alert("Erro ao salvar localmente: " + err.message);
    }
  });
}

/** =========================
 *  Preview da imagem (opcional)
 * ========================= */
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

/** =========================
 *  LISTA COM BUSCA, ORDEM E PAGINAÇÃO (10 por página)
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

function normalizar(s) {
  return (s || "").toString().toLowerCase();
}

function aplicarFiltroOrdenacao(noticias) {
  const termo = normalizar(elBusca ? elBusca.value : "");
  const ordem = elOrdem ? elOrdem.value : "recente";

  let lista = noticias.filter(n => {
    const t = normalizar(n.titulo);
    const c = normalizar(n.conteudo);
    return t.includes(termo) || c.includes(termo);
  });

  switch (ordem) {
    case "antigo":
      // já vem por created_at desc; invertendo fica asc
      lista = lista.slice().reverse();
      break;
    case "titulo-az":
      lista.sort((a,b) => a.titulo.localeCompare(b.titulo, "pt-BR", {sensitivity:"base"}));
      break;
    case "titulo-za":
      lista.sort((a,b) => b.titulo.localeCompare(a.titulo, "pt-BR", {sensitivity:"base"}));
      break;
    case "recente":
    default:
      // manter default (mais recentes primeiro)
      break;
  }
  return lista;
}

function paginar(lista, page, size) {
  const total = lista.length;
  const totalPages = Math.max(1, Math.ceil(total / size));
  const p = Math.min(Math.max(1, page), totalPages);
  const start = (p - 1) * size;
  const end = start + size;
  return { page: p, total, totalPages, items: lista.slice(start, end) };
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
    if (start > 2) {
      const sep = document.createElement("span");
      sep.textContent = "…";
      elPag.appendChild(sep);
    }
  }

  for (let p = start; p <= end; p++) {
    elPag.appendChild(mkBtn(String(p), p, { active: p === pageAtual }));
  }

  if (end < totalPages) {
    if (end < totalPages - 1) {
      const sep = document.createElement("span");
      sep.textContent = "…";
      elPag.appendChild(sep);
    }
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

    if (n.imagemDataURL) {
      const img = document.createElement("img");
      img.src = n.imagemDataURL;
      img.alt = `Imagem de ${n.titulo}`;
      img.className = "img-noticia";
      img.loading = "lazy";
      card.appendChild(img);
    }

    const h3 = document.createElement("h3");
    h3.textContent = n.titulo;
    card.appendChild(h3);

    const meta = document.createElement("small");
    const dataFmt = new Date(n.created_at).toLocaleString("pt-BR");
    meta.textContent = `Por ${n.autor} • ${dataFmt}`;
    card.appendChild(meta);

    const p = document.createElement("p");
    p.innerHTML = (n.conteudo || "").replace(/\n/g, "<br>");
    card.appendChild(p);

    elLista.appendChild(card);
  });
}

async function atualizarLista({ resetPage=false } = {}) {
  // carrega tudo do IndexedDB
  const todas = await getNoticias();

  // aplica busca + ordenação
  const filtradaOrdenada = aplicarFiltroOrdenacao(todas);

  // pagina
  let page = getPageFromURL();
  if (resetPage) page = 1;

  const { page: p, totalPages, items } = paginar(filtradaOrdenada, page, PAGE_SIZE);
  setPageInURL(p);
  renderCards(items);
  renderPaginacao(totalPages, p);
}

// Eventos da UI
if (elBusca) elBusca.addEventListener("input", () => atualizarLista({ resetPage:true }));
if (elOrdem) elOrdem.addEventListener("change", () => atualizarLista({ resetPage:true }));

// Inicializa automaticamente quando estiver na página de listagem
document.addEventListener("DOMContentLoaded", () => {
  if (elLista) atualizarLista();
});
