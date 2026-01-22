/**
 * Navegación del sidebar con autenticación
 * Gestiona la visibilidad del menú admin según el estado de autenticación
 */

function updateSidebarAuth() {
  if (typeof isAuthenticated !== "function") return;

  const adminSection = document.getElementById("nav-admin-section");
  const btnLogin = document.getElementById("btn-login");
  const btnLogout = document.getElementById("btn-logout");

  if (isAuthenticated()) {
    // Mostrar sección admin y botón logout
    if (adminSection) adminSection.style.display = "block";
    if (btnLogin) btnLogin.style.display = "none";
    if (btnLogout) btnLogout.style.display = "flex";
  } else {
    // Ocultar sección admin y mostrar botón login
    if (adminSection) adminSection.style.display = "none";
    if (btnLogin) btnLogin.style.display = "flex";
    if (btnLogout) btnLogout.style.display = "none";
  }
}

// Auto-inicializar cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", function () {
  updateSidebarAuth();
});
