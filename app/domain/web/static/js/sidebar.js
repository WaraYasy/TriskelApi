// Sidebar Toggle Functionality

document.addEventListener("DOMContentLoaded", function () {
  initSidebar();
});

function initSidebar() {
  const sidebar = document.querySelector(".sidebar");
  if (!sidebar) return;

  // Create toggle button
  const toggleBtn = document.createElement("button");
  toggleBtn.className = "sidebar-toggle";
  toggleBtn.setAttribute("title", "Colapsar menú");
  toggleBtn.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M15 18l-6-6 6-6"/>
        </svg>
    `;
  sidebar.appendChild(toggleBtn);

  // Add data-tooltip attributes to nav items
  const navItems = sidebar.querySelectorAll(".nav-item");
  navItems.forEach((item) => {
    const span = item.querySelector("span");
    if (span) {
      item.setAttribute("data-tooltip", span.textContent);
    }
  });

  // Check localStorage for saved state
  const isCollapsed = localStorage.getItem("sidebarCollapsed") === "true";
  if (isCollapsed) {
    sidebar.classList.add("collapsed");
    document.body.classList.add("sidebar-collapsed");
    toggleBtn.setAttribute("title", "Expandir menú");
  }

  // Toggle event
  toggleBtn.addEventListener("click", function () {
    sidebar.classList.toggle("collapsed");
    document.body.classList.toggle("sidebar-collapsed");

    const collapsed = sidebar.classList.contains("collapsed");
    localStorage.setItem("sidebarCollapsed", collapsed);
    toggleBtn.setAttribute(
      "title",
      collapsed ? "Expandir menú" : "Colapsar menú",
    );
  });
}

// Export for use in other scripts
if (typeof window !== "undefined") {
  window.initSidebar = initSidebar;
}
