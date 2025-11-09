(() => {
  const panel = document.getElementById("chatfloat-panel");
  const btn = document.getElementById("chatfloat-toggle");
  const close = document.getElementById("chatfloat-close");
  const form = document.getElementById("chatfloat-form");
  const input = document.getElementById("chatfloat-input");
  const messages = document.getElementById("chatfloat-messages");
  if (!panel || !btn || !form || !input || !messages) return;

  const API = "/api/chat"; // se seu blueprint de chat está em /api/chat

  function setOpen(open) {
    panel.hidden = !open;
    btn.setAttribute("aria-expanded", String(open));
    if (open) input.focus();
  }

  btn.addEventListener("click", () => setOpen(panel.hidden));
  close?.addEventListener("click", () => setOpen(false));

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
      const r = await fetch(`${API}`, {
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
