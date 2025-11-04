// index.init.js (module)
const PAGE_SIZE = 10;

const elLista   = document.getElementById("lista-noticias");
const elVazio   = document.getElementById("vazio");
const elBusca   = document.getElementById("q");
const elOrdem   = document.getElementById("ordem");
const elAtual   = document.getElementById("btn-atualizar");
const elPag     = document.getElementById("paginacao");

// Utils ----------------------------------------------------
function getNoticiasRaw() {
  try {
    return JSON.parse(localStorage.getItem("noticias")) || [];
  } catch {
    return [];
  }
}
function normalizarTexto(s) {
  return (s || "").toString().toLowerCase();
}
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

// Filtro & ordenação ---------------------------------------
function aplicarFiltroOrdenacao(noticias) {
  const termo = normalizarTexto(elBusca ? elBusca.value : "");
  const ordem = elOrdem ? elOrdem.value : "recente";

  // filtro
  let lista = noticias.filter(n => {
    const t = normalizarTexto(n.titulo);
    const c = normalizarTexto(n.conteudo);
    return t.includes(termo) || c.includes(termo);
  });

  // ordenação
  switch (ordem) {
    case "antigo":
      // por data mais antiga (como string pt-BR); para confiabilidade, ordene por índice original se tiver
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
      // assumindo que o array no storage já está do mais novo p/ antigo (unshift)
      // então mantemos a ordem natural
      break;
  }

  return lista;
}

// Paginação -------------------------------------------------
function paginar(lista, page, size) {
  const total = lista.length;
  const totalPages = Math.max(1, Math.ceil(total / size));
  const p = Math.min(Math.max(1, page), totalPages);
  const start = (p - 1) * size;
  const end = start + size;
  return {
    page: p,
    total,
    totalPages,
    items: lista.slice(start, end)
  };
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
      atualizarView(); // re-render
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
    return btn;
  };

  // Prev
  elPag.appendChild(mkBtn("« Anterior", pageAtual - 1, { disabled: pageAtual <= 1 }));

  // Janela de páginas (máx 7 números)
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

  // Next
  elPag.appendChild(mkBtn("Próxima »", pageAtual + 1, { disabled: pageAtual >= totalPages }));
}

// Render da lista -------------------------------------------
function renderLista(items) {
  if (!elLista || !elVazio) return;

  elLista.innerHTML = "";
  if (!items.length) {
    elVazio.style.display = "block";
    return;
  }
  elVazio.style.display = "none";

  items.forEach(noticia => {
    const card = document.createElement("article");
    card.className = "noticia card";

    const h3 = document.createElement("h3");
    h3.textContent = noticia.titulo;

    const meta = document.createElement("p");
    meta.innerHTML = `<strong>Autor:</strong> ${noticia.autor || "—"}<br><small>${noticia.data || ""}</small>`;

    card.appendChild(h3);
    card.appendChild(meta);

    if (noticia.imagem) {
      const img = document.createElement("img");
      img.src = noticia.imagem;
      img.alt = noticia.titulo;
      img.loading = "lazy";
      card.appendChild(img);
    }

    const corpo = document.createElement("p");
    corpo.textContent = noticia.conteudo || "";
    card.appendChild(corpo);

    // (opcional) ações por card — editar/excluir
    // mantive seu espaço para integrar com o modal existente
    const actions = document.createElement("div");
    actions.className = "card-actions";
    // Exemplo placeholders:
    // const btnEdit = document.createElement("button");
    // btnEdit.className = "btn secondary"; btnEdit.textContent = "Editar";
    // const btnDel = document.createElement("button");
    // btnDel.className = "btn danger"; btnDel.textContent = "Excluir";
    // actions.append(btnEdit, btnDel);
    // card.appendChild(actions);

    elLista.appendChild(card);
  });
}

// Pipeline principal ----------------------------------------
function atualizarView({ resetPage = false } = {}) {
  const noticias = getNoticiasRaw();
  const filtradaOrdenada = aplicarFiltroOrdenacao(noticias);

  let page = getPageFromURL();
  if (resetPage) page = 1;

  const { page: p, totalPages, items } = paginar(filtradaOrdenada, page, PAGE_SIZE);
  setPageInURL(p); // normaliza URL se precisou ajustar
  renderLista(items);
  renderPaginacao(totalPages, p);
}

// Eventos ---------------------------------------------------
if (elAtual) elAtual.addEventListener("click", () => atualizarView({ resetPage: false }));
if (elBusca) elBusca.addEventListener("input", () => atualizarView({ resetPage: true }));
if (elOrdem) elOrdem.addEventListener("change", () => atualizarView({ resetPage: true }));

// Inicialização ---------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  atualizarView();
});
