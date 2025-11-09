(() => {
  const sidebar = document.getElementById("sidebar");
  const content = document.getElementById("sidebar-content");
  const toggle  = document.getElementById("sidebar-toggle");
  if (!sidebar || !content || !toggle) {
    console.warn("[sidebar] elementos não encontrados");
    return;
  }

  function setState(open){
    sidebar.dataset.state = open ? "open" : "closed";
    toggle.setAttribute("aria-expanded", String(open));
    content.setAttribute("aria-hidden", String(!open));
    document.body.classList.toggle("has-sidebar-open", open);
    console.debug("[sidebar] state =", open ? "open" : "closed");
  }

  // restaura estado salvo
  const saved = localStorage.getItem("sidebar-open") === "1";
  setState(saved);

  // abre/fecha no botão
  toggle.addEventListener("click", (e) => {
    e.stopPropagation();
    const open = sidebar.dataset.state !== "open";
    setState(open);
    localStorage.setItem("sidebar-open", open ? "1" : "0");
  });

  // fecha clicando fora (overlay/mobile)
  document.addEventListener("click", (e) => {
    if (sidebar.dataset.state !== "open") return;
    const within = content.contains(e.target) || toggle.contains(e.target);
    if (!within) setState(false);
  });

  // acessibilidade: ESC fecha
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && sidebar.dataset.state === "open") {
      setState(false);
    }
  });
})();
