document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.getElementById("sidebar");
  const toggle  = document.getElementById("sidebar-toggle");
  if (!sidebar || !toggle) return;

  function setState(open){
    sidebar.dataset.state = open ? "open" : "closed";
    toggle.setAttribute("aria-expanded", String(open));
    document.getElementById("sidebar-content")?.setAttribute("aria-hidden", String(!open));
    document.body.classList.toggle("has-sidebar-open", open);
  }

  const saved = localStorage.getItem("sidebar-open") === "1";
  setState(saved);

  toggle.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    const willOpen = sidebar.dataset.state !== "open";
    setState(willOpen);
    localStorage.setItem("sidebar-open", willOpen ? "1" : "0");
  });

  document.addEventListener("click", (e) => {
    if (sidebar.dataset.state !== "open") return;
    const within = sidebar.contains(e.target) || toggle.contains(e.target);
    if (!within) setState(false);
  });
});
