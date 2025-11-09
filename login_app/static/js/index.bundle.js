// ------------------------------
// MÓDULO: Lista de posts + paginação
// ------------------------------
(() => {
  // Elementos
  const listEl     = document.getElementById("lista-noticias") || document.getElementById("list");
  const emptyEl    = document.getElementById("vazio")          || document.getElementById("empty");
  const countEl    = document.getElementById("contador")       || document.getElementById("count");
  const searchEl   = document.getElementById("q")              || document.getElementById("search");
  const refreshBtn = document.getElementById("btn-atualizar");
  const pagEl      = document.getElementById("paginacao");

  // Estado de paginação
  let currentPage = 1;
  let totalPages  = 1;
  const PER_PAGE  = 10;

  // Imagens acima da dobra + proporção fallback
  const ABOVE_THE_FOLD  = 3;
  const FALLBACK_ASPECT = "16/9";

  // Helpers
  function safeSetText(el, text) { if (el) el.textContent = text; }
  function setCount(n) { safeSetText(countEl, `${n} ${n === 1 ? "item" : "itens"}`); }

  function escapeHtml(s = "") {
    return s.replace(/[&<>"']/g, c => (
      {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]
    ));
  }

  function withCacheBuster(src) {
    try {
      const url = new URL(src, window.location.origin);
      url.searchParams.set("b", Date.now());
      return url.toString();
    } catch {
      const sep = src.includes("?") ? "&" : "?";
      return `${src}${sep}b=${Date.now()}`;
    }
  }

  // API
  async function apiList(q = "", page = 1) {
    const u = new URL("/api/posts", window.location.origin);
    if (q) u.searchParams.set("q", q);
    u.searchParams.set("page", page);
    u.searchParams.set("per_page", PER_PAGE);

    const r = await fetch(u, {
      headers: { "Accept": "application/json" },
      credentials: "include"
    });
    if (!r.ok) throw new Error(`Falha ao listar (${r.status})`);
    const data = await r.json();

    currentPage = data?.meta?.page  || 1;
    totalPages  = data?.meta?.pages || 1;

    // aceita { items: [...] } ou { Objectitems: [...] } ou lista direta
    const items = Array.isArray(data) ? data : (data.items || data.Objectitems || []);
    return items;
  }

  async function apiDelete(id) {
    const r = await fetch(`/api/posts/${id}`, { method: "DELETE", credentials: "include" });
    if (!r.ok) throw new Error(`Falha ao excluir (${r.status})`);
  }

  // Imagens: robustez extra
  function ensureImagesVisible() {
    const imgs = document.querySelectorAll("img.thumb");
    let idx = 0;
    imgs.forEach((img) => {
      const eager  = idx < ABOVE_THE_FOLD;
      const broken = !img.complete || img.naturalWidth === 0 || img.dataset.err === "1";

      if (eager) {
        img.loading = "eager";
        img.setAttribute("fetchpriority", "high");
      }

      img.addEventListener("load",  () => { img.dataset.loaded = "1"; }, { once: true });
      img.addEventListener("error", () => { img.dataset.loaded = "1"; }, { once: true });

      if (broken && !img.dataset.retried) {
        img.dataset.retried = "1";
        img.src = withCacheBuster(img.src);
        img.addEventListener("error", () => { img.dataset.err = "1"; }, { once: true });
      }

      idx++;
    });
  }

  // UI
  function postCard(p, idx = 0) {
    const div = document.createElement("div");
    div.className = "card card-noticia";

    const titulo   = p.titulo ?? "Sem título";
    const conteudo = p.conteudo ?? "";
    const autor    = p.autor_nome || p.autor_email || p.autor || "Autor desconhecido";
    const dt       = p.created_at || p.criado_em || "";
    const dtStr    = dt ? new Date(dt).toLocaleString() : "";

    const eager   = idx < ABOVE_THE_FOLD;
    const loading = eager ? "eager" : "lazy";

    // conteúdo textual (imagem será inserida antes, se houver image_url)
    div.innerHTML = `
      <h3 style="margin:0 0 .25rem 0;">${escapeHtml(titulo)}</h3>
      <div class="muted" style="margin-bottom:.5rem;">
        por ${escapeHtml(autor)} ${dtStr ? `• ${dtStr}` : ""}
      </div>
      <p style="white-space:pre-wrap; margin-bottom:.75rem;">${
        escapeHtml(conteudo.length > 240 ? conteudo.slice(0, 240) + "..." : conteudo)
      }</p>
      <div class="card-actions" style="display:flex; gap:.5rem; flex-wrap: wrap;">
        <a class="btn" href="/publicar?id=${p.id}">Editar</a>
        <button class="btn danger" data-del="${p.id}">Excluir</button>
      </div>
    `;

    if (p.image_url) {
      const img = document.createElement("img");
      img.className         = "thumb img-noticia";
      img.src               = p.image_url;
      img.alt               = "Imagem da notícia";
      img.loading           = loading;
      img.decoding          = "async";
      img.style.width       = "100%";
      img.style.aspectRatio = FALLBACK_ASPECT;
      img.style.objectFit   = "cover";

      if (eager) img.setAttribute("fetchpriority", "high");

      img.addEventListener("load",  () => { img.dataset.loaded = "1"; }, { once: true });
      img.addEventListener("error", () => {
        if (!img.dataset.retried) {
          img.dataset.retried = "1";
          img.src = withCacheBuster(img.src);
        } else {
          img.dataset.err = "1";
        }
      }, { once: true });

      div.insertBefore(img, div.firstChild);
    }

    return div;
  }

  function renderPagination() {
    if (!pagEl) return;
    pagEl.innerHTML = "";

    const mkBtn = (label, disabled, onClick, isActive = false) => {
      const b = document.createElement("button");
      b.textContent = label;
      b.disabled = !!disabled;
      b.className = isActive ? "page-btn active" : "page-btn";
      b.addEventListener("click", onClick);
      return b;
    };

    // anterior
    pagEl.appendChild(
      mkBtn("◀", currentPage === 1, () => {
        if (currentPage > 1) { currentPage--; render(searchEl?.value || ""); }
      })
    );

    // janela de páginas
    const windowSize = 5;
    let start = Math.max(1, currentPage - Math.floor(windowSize / 2));
    let end   = Math.min(totalPages, start + windowSize - 1);
    if (end - start + 1 < windowSize) start = Math.max(1, end - windowSize + 1);

    for (let i = start; i <= end; i++) {
      const btn = mkBtn(String(i), i === currentPage, () => {
        if (currentPage !== i) { currentPage = i; render(searchEl?.value || ""); }
      }, i === currentPage);
      pagEl.appendChild(btn);
    }

    // próximo
    pagEl.appendChild(
      mkBtn("▶", currentPage === totalPages, () => {
        if (currentPage < totalPages) { currentPage++; render(searchEl?.value || ""); }
      })
    );

    // info opcional
    const info = document.createElement("span");
    info.style.marginLeft = ".5rem";
    info.style.opacity = ".7";
    info.textContent = `Página ${currentPage} de ${totalPages}`;
    pagEl.appendChild(info);
  }

  async function render(q = "") {
    if (!listEl) return;

    try {
      const items = await apiList(q, currentPage);
      listEl.innerHTML = "";

      if (!Array.isArray(items) || items.length === 0) {
        if (emptyEl) emptyEl.style.display = "block";
        setCount(0);
      } else {
        if (emptyEl) emptyEl.style.display = "none";
        items.forEach((p, i) => listEl.appendChild(postCard(p, i)));
        setCount(items.length);
      }

      renderPagination();
      await Promise.resolve();
      ensureImagesVisible();
    } catch (err) {
      console.error(err);
      if (listEl && !listEl.innerHTML) {
        listEl.innerHTML = `<p style="color:#dc2626">Erro ao carregar as notícias.</p>`;
      }
      if (emptyEl) emptyEl.style.display = "block";
      setCount(0);
      renderPagination();
      ensureImagesVisible();
    }
  }

  // Eventos
  document.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-del]");
    if (!btn) return;
    const id = Number(btn.dataset.del);
    if (!Number.isFinite(id)) return;

    try {
      if (confirm("Excluir esta postagem?")) {
        await apiDelete(id);
        await render(searchEl?.value || "");
      }
    } catch (err) {
      console.error(err);
      alert("Não foi possível excluir a postagem.");
    }
  });

  searchEl?.addEventListener("input", (e) => {
    clearTimeout(searchEl._t);
    searchEl._t = setTimeout(() => {
      currentPage = 1;
      render(e.target.value);
    }, 250);
  });

  refreshBtn?.addEventListener("click", () => {
    render(searchEl?.value || "");
  });

  // start
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => render(), { once: true });
  } else {
    render();
  }

  window.addEventListener("pageshow", (e) => {
    if (e.persisted) requestAnimationFrame(() => ensureImagesVisible());
  });
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
      requestAnimationFrame(() => ensureImagesVisible());
    }
  });

  // auto-ativar "Atualizar" após load (opcional)
  window.addEventListener("load", () => {
    const btn = document.getElementById("btn-atualizar");
    if (btn) setTimeout(() => btn.click(), 300);
  });
})();

// ------------------------------
// MÓDULO: Sidebar (esquerda)
// ------------------------------
(() => {
  const sidebar = document.getElementById("sidebar");
  const toggle  = document.getElementById("sidebar-toggle");
  if (!sidebar || !toggle) return;

  function setState(open) {
    sidebar.dataset.state = open ? "open" : "closed";
    toggle.setAttribute("aria-expanded", String(open));
    const content = sidebar.querySelector(".sidebar-content");
    if (content) content.setAttribute("aria-hidden", String(!open));
  }

  // restaurar estado do usuário (opcional)
  const savedOpen = localStorage.getItem("sidebar-open") === "1";
  setState(savedOpen);

  toggle.addEventListener("click", () => {
    const open = sidebar.dataset.state !== "open";
    setState(open);
    localStorage.setItem("sidebar-open", open ? "1" : "0");
  });

  // fechar ao clicar fora (mobile)
  document.addEventListener("click", (e) => {
    if (sidebar.dataset.state !== "open") return;
    const within = sidebar.contains(e.target) || toggle.contains(e.target);
    if (!within) setState(false);
  });
})();

// ------------------------------
// MÓDULO: Chat Float (inferior direito)
// ------------------------------
(() => {
  const panel    = document.getElementById("chatfloat-panel");
  const btn      = document.getElementById("chatfloat-toggle");
  const closeBtn = document.getElementById("chatfloat-close");
  const form     = document.getElementById("chatfloat-form");
  const input    = document.getElementById("chatfloat-input");
  const messages = document.getElementById("chatfloat-messages");
  if (!panel || !btn || !form || !input || !messages) return;

  const API = "/api/chat"; // ajuste se seu blueprint diferir

  function setOpen(open) {
    panel.hidden = !open;
    btn.setAttribute("aria-expanded", String(open));
    if (open) input.focus();
  }

  btn.addEventListener("click", () => setOpen(panel.hidden));
  closeBtn?.addEventListener("click", () => setOpen(false));

  function push(role, text) {
    const el = document.createElement("div");
    el.className = `msg msg-${role}`;
    el.style.margin = "8px 0";
    el.textContent = text;
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (!q) return;
    input.value = "";
    push("user", q);

    try {
      const r = await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: q })
      });
      const data = await r.json();
      push("assistant", data.reply || "Sem resposta.");
    } catch {
      push("assistant", "Falha ao conectar ao chat.");
    }
  });
})();
