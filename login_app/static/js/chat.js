// ===== NewsAPI: sidebar próprio (não conflita com .sidebar global) =====
(() => {
  const toggle = document.getElementById("newsapi-sidebar-toggle");
  const aside  = document.getElementById("newsapi-sidebar");
  const panel  = document.getElementById("newsapi-sidebar-content");
  if (!toggle || !aside || !panel) return; // não está nessa página

  // garante que o botão não submeta forms
  if (!toggle.getAttribute("type")) toggle.setAttribute("type", "button");

  const setOpen = (open) => {
    aside.dataset.state = open ? "open" : "closed";
    toggle.setAttribute("aria-expanded", String(open));
    panel.setAttribute("aria-hidden", String(!open));

    // anima o painel (sem depender de CSS externo)
    panel.style.transform = open ? "translateX(0)" : "translateX(-105%)";
    panel.style.opacity   = open ? "1" : "0";

    // overlay no mobile (efeito simples)
    if (open) {
      aside.style.pointerEvents = "auto";
      aside.style.setProperty("--newsapi-overlay", "1");
      aside.style.background = "rgba(0,0,0,.35)";
    } else {
      aside.style.pointerEvents = "none";
      aside.style.background = "transparent";
    }
  };

  // estado inicial
  setOpen(aside.dataset.state === "open");

  // toggle por clique
  toggle.addEventListener("click", (e) => {
    e.preventDefault();
    setOpen(aside.dataset.state !== "open");
  });

  // fecha ao clicar fora
  document.addEventListener("click", (e) => {
    if (aside.dataset.state !== "open") return;
    const within = aside.contains(e.target) || toggle.contains(e.target);
    if (!within) setOpen(false);
  });

  // ESC fecha
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && aside.dataset.state === "open") setOpen(false);
  });

  // exemplo de binding (opcional): clique nos itens do menu
  panel.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-feed]");
    if (!btn) return;
    const feed = btn.getAttribute("data-feed");
    // aqui você chama sua função que já carrega as notícias via NewsAPI
    // ex.: loadNews(feed)
    // loadNews(feed);
    setOpen(false);
  });
})();
// static/js/chat.js
(() => {
  // Evita inicialização dupla
  if (window.__chatBootstrapped) return;
  window.__chatBootstrapped = true;

  document.addEventListener("DOMContentLoaded", () => {
    // ===== Utilidades seguras =====
    const esc = (s) => (s || "").replace(/[<>&]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[c]));
    const postJSONWithTimeout = async (url, body, { timeoutMs = 20000, signal } = {}) => {
      const ac = new AbortController();
      const id = setTimeout(() => ac.abort(), timeoutMs);
      const linkAbort = () => ac.abort();
      if (signal) signal.addEventListener("abort", linkAbort, { once: true });
      try {
        return await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
          signal: ac.signal
        });
      } finally {
        clearTimeout(id);
        if (signal) signal.removeEventListener("abort", linkAbort);
      }
    };
    const humanizeHTTPError = (status) => {
      if (status === 401) return "Sem autorização (verifique a chave da API no servidor).";
      if (status === 403) return "Acesso negado.";
      if (status === 429) return "Limite de uso atingido (tente novamente depois).";
      if (status >= 500) return "Serviço temporariamente indisponível.";
      return `Erro HTTP ${status}.`;
    };

    // ===== Módulo genérico do chat (reuso para fixo e flutuante) =====
    function bootstrapChat({ selectors, endpoint = "/api/chat" }) {
      const form = document.getElementById(selectors.form);
      const ta   = document.getElementById(selectors.input);
      const box  = document.getElementById(selectors.box);
      const btn  = document.getElementById(selectors.send);

      if (!form || !ta || !box || !btn) return null;

      const scrollToBottom = () => { box.scrollTop = box.scrollHeight; };

      function appendLine(who, text, isError = false) {
        const wrap = document.createElement("div");
        wrap.className = "chat-line";
        wrap.style.margin = ".4rem 0";
        const whoColor = who === "Assistente" ? "#38bdf8" : "#94a3b8";
        const textColor = isError ? "#f87171" : "#f1f5f9";
        wrap.innerHTML =
          `<strong style="color:${whoColor}">${esc(who)}:</strong> ` +
          `<span style="white-space:pre-wrap; color:${textColor}">${esc(text)}</span>`;
        box.appendChild(wrap);
        scrollToBottom();
        return wrap;
      }

      function appendLoading() {
        const el = document.createElement("div");
        el.style.margin = ".4rem 0";
        el.style.color = "#94a3b8";
        el.innerHTML = "<i>digitando…</i>";
        box.appendChild(el);
        scrollToBottom();
        return () => el.remove();
      }

      // Auto-resize + Enter envia
      const autoResize = () => {
        ta.style.height = "auto";
        ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
      };
      ta.addEventListener("input", autoResize, { passive: true });
      autoResize();
      ta.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          form.requestSubmit();
        }
      });

      // Envio com timeout e retry leve
      let inflight = null;
      form.addEventListener("submit", async (e) => {
        e.preventDefault();

        let msg = (ta.value || "").trim();
        if (!msg) return;
        if (msg.length > 2000) msg = msg.slice(0, 2000);

        // Aborta anterior se ainda estiver rodando
        if (inflight) { inflight.abort(); inflight = null; }

        appendLine("Você", msg);
        ta.value = ""; autoResize(); ta.focus();

        const stopLoading = appendLoading();
        btn.disabled = true;

        try {
          inflight = new AbortController();

          const maxAttempts = 2;
          let attempt = 0;
          let lastErr = null;
          let data = null;

          while (attempt < maxAttempts) {
            try {
              const resp = await postJSONWithTimeout(endpoint, { message: msg }, { timeoutMs: 20000, signal: inflight.signal });
              let payload = null;
              try { payload = await resp.json(); } catch { payload = null; }

              if (!resp.ok) {
                const errText = payload?.error || humanizeHTTPError(resp.status);
                if (resp.status === 429 || resp.status >= 500) {
                  lastErr = new Error(errText);
                  attempt++;
                  await new Promise(r => setTimeout(r, 600 * attempt));
                  continue;
                }
                throw new Error(errText);
              }

              data = payload;
              break; // sucesso
            } catch (err) {
              if (err.name === "AbortError") throw err;
              lastErr = err;
              attempt++;
              if (attempt >= maxAttempts) throw err;
              await new Promise(r => setTimeout(r, 400 * attempt));
            }
          }

          stopLoading();
          if (data && data.reply) {
            appendLine("Assistente", data.reply);
          } else {
            appendLine("Assistente", data?.error || (lastErr?.message || "Erro ao responder."), true);
          }
        } catch (err) {
          stopLoading();
          if (err.name !== "AbortError") {
            appendLine("Assistente", "Falha de rede ou tempo esgotado.", true);
          }
        } finally {
          inflight = null;
          btn.disabled = false;
        }
      });

      return { appendLine, box, ta };
    }

    // ===== Chat fixo (se existir) =====
    bootstrapChat({
      selectors: {
        form: "chat-form",
        input: "chat-input",
        box: "chat-box",
        send: "chat-send",
      },
      endpoint: "/api/chat",
    });

    // ===== Chat flutuante =====
    const toggleBtn = document.getElementById("chat-toggle");
    const floatEl   = document.getElementById("chat-float");

    if (toggleBtn && floatEl) {
      // Nunca deixe este botão ser "submit"
      if (!toggleBtn.getAttribute("type")) toggleBtn.setAttribute("type", "button");
      // Estado inicial oculto
      floatEl.style.display = "none";
      toggleBtn.setAttribute("aria-expanded", "false");
      toggleBtn.setAttribute("aria-controls", "chat-float");

      toggleBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        const open = floatEl.style.display === "flex";
        floatEl.style.display = open ? "none" : "flex";
        toggleBtn.textContent = open ? "💬" : "❌";
        toggleBtn.setAttribute("aria-expanded", String(!open));
        if (!open) {
          const ta = document.getElementById("chat-float-input");
          ta && ta.focus();
        }
      });

      // Fecha ao clicar fora (opcional)
      document.addEventListener("click", (evt) => {
        if (floatEl.style.display !== "flex") return;
        const insideFloat = floatEl.contains(evt.target);
        const clickedBtn  = toggleBtn.contains(evt.target);
        if (!insideFloat && !clickedBtn) {
          floatEl.style.display = "none";
          toggleBtn.textContent = "💬";
          toggleBtn.setAttribute("aria-expanded", "false");
        }
      });
    }

    // Bootstrap do chat flutuante
    const floatChat = bootstrapChat({
      selectors: {
        form: "chat-float-form",
        input: "chat-float-input",
        box: "chat-float-box",
        send: "chat-float-send",
      },
      endpoint: "/api/chat",
    });

    // Garante visível ao enviar pelo flutuante
    if (floatChat && floatEl) {
      const form = document.getElementById("chat-float-form");
      form?.addEventListener("submit", () => {
        floatEl.style.display = "flex";
        toggleBtn && toggleBtn.setAttribute("aria-expanded", "true");
      });
    }

    // ===== Toggle da sidebar (seguro) =====
    const sidebarToggle = document.getElementById("sidebar-toggle");
    const sidebarEl     = document.getElementById("rss-sidebar") || document.querySelector(".sidebar");
    if (sidebarToggle && sidebarEl) {
      if (!sidebarToggle.getAttribute("type")) sidebarToggle.setAttribute("type", "button");
      sidebarToggle.setAttribute("aria-controls", sidebarEl.id || "rss-sidebar");
      sidebarToggle.setAttribute("aria-expanded", String(sidebarEl.classList.contains("open")));

      sidebarToggle.addEventListener("click", () => {
        sidebarEl.classList.toggle("open");
        const open = sidebarEl.classList.contains("open");
        sidebarToggle.textContent = open ? "✖" : "☰";
        sidebarToggle.setAttribute("aria-expanded", String(open));
      });
    }

    console.log("[chat] pronto");
  });
})();

