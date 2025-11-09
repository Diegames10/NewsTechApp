(() => {
  const root = document.documentElement;
  const sidebar = document.getElementById("sidebar");
  const toggle = document.getElementById("sidebar-toggle");
  if (!sidebar || !toggle) return;

  function setState(open) {
    sidebar.dataset.state = open ? "open" : "closed";
    toggle.setAttribute("aria-expanded", String(open));
    sidebar.querySelector(".sidebar-content")?.setAttribute("aria-hidden", String(!open));

    // ✅ Adiciona ou remove a classe no <body> para ajustar o layout
    document.body.classList.toggle("has-sidebar-open", open);
  }

  // restaurar estado do usuário (opcional)
  const saved = localStorage.getItem("sidebar-open") === "1";
  setState(saved);

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
