// ------------------------------
// MÓDULO: Sidebar (abre/fecha e ajusta layout)
// ------------------------------
(() => {
  const sidebar = document.getElementById("sidebar");
  const toggle  = document.getElementById("sidebar-toggle");
  const main    = document.querySelector("main");
  if (!sidebar || !toggle || !main) return;

  function setState(open) {
    sidebar.dataset.state = open ? "open" : "closed";
    toggle.setAttribute("aria-expanded", String(open));
    document.body.classList.toggle("sidebar-open", open);
  }

  // restaura estado do usuário
  const savedOpen = localStorage.getItem("sidebar-open") === "1";
  setState(savedOpen);

  toggle.addEventListener("click", () => {
    const open = sidebar.dataset.state !== "open";
    setState(open);
    localStorage.setItem("sidebar-open", open ? "1" : "0");
  });

  // fecha ao clicar fora (mobile ou desktop)
  document.addEventListener("click", (e) => {
    if (sidebar.dataset.state !== "open") return;
    const within = sidebar.contains(e.target) || toggle.contains(e.target);
    if (!within) setState(false);
  });

  // fecha com ESC
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") setState(false);
  });
})();
