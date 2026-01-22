// Theme Toggle Functionality

// Apply saved theme immediately (before DOM loads to prevent flash)
(function () {
  const savedTheme = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);
})();

// Toggle theme function - available globally
function toggleTheme() {
  const currentTheme =
    document.documentElement.getAttribute("data-theme") || "dark";
  const newTheme = currentTheme === "dark" ? "light" : "dark";

  document.documentElement.setAttribute("data-theme", newTheme);
  localStorage.setItem("theme", newTheme);

  // Update button title
  const toggleBtn = document.querySelector(".theme-toggle");
  if (toggleBtn) {
    toggleBtn.setAttribute(
      "title",
      newTheme === "dark" ? "Cambiar a modo claro" : "Cambiar a modo oscuro",
    );
  }
}

// Re-apply theme on DOM load (safety measure)
document.addEventListener("DOMContentLoaded", function () {
  const savedTheme = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);

  // Update button title based on current theme
  const toggleBtn = document.querySelector(".theme-toggle");
  if (toggleBtn) {
    toggleBtn.setAttribute(
      "title",
      savedTheme === "dark" ? "Cambiar a modo claro" : "Cambiar a modo oscuro",
    );
  }
});

// Export for use in other scripts
if (typeof window !== "undefined") {
  window.toggleTheme = toggleTheme;
}
