(() => {
  const sidebar = document.getElementById("sidebar");
  const content = document.getElementById("sidebar-content");
  const toggle  = document.getElementById("sidebar-toggle");
  if (!sidebar || !content || !toggle) return;

  const setState = (open) => {
    sidebar.setAttribute("data-state", open ? "open" : "closed");
    toggle.setAttribute("aria-expanded", String(open));
    content.setAttribute("aria-hidden", String(!open));
    document.body.classList.toggle("has-sidebar-open", open);
  };

  // restaura
  setState(localStorage.getItem("sidebar-open") === "1");

  toggle.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();        // evita conflitos
    const open = sidebar.getAttribute("data-state") !== "open";
    setState(open);
    localStorage.setItem("sidebar-open", open ? "1" : "0");
  });

  document.addEventListener("click", (e) => {
    if (sidebar.getAttribute("data-state") !== "open") return;
    const within = content.contains(e.target) || toggle.contains(e.target);
    if (!within) setState(false);
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && sidebar.getAttribute("data-state") === "open") {
      setState(false);
    }
  });
})();
