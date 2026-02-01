/**
 * Navegación del sidebar con autenticación
 * Gestiona la visibilidad del menú admin según el estado de autenticación
 */

async function updateSidebarAuth() {
  if (typeof isAuthenticated !== "function") return;

  const adminSection = document.getElementById("nav-admin-section");
  const userProfile = document.getElementById("user-profile");
  const btnLogin = document.getElementById("btn-login");
  const btnLogout = document.getElementById("btn-logout");
  const userNameElement = document.getElementById("userName");
  const userEmailElement = document.getElementById("userEmail");

  if (isAuthenticated()) {
    // Usuario autenticado: mostrar perfil + logout, ocultar login
    if (adminSection) adminSection.style.display = "block";
    if (userProfile) userProfile.style.display = "flex";
    if (btnLogin) btnLogin.style.display = "none";
    if (btnLogout) btnLogout.style.display = "flex";

    // Cargar datos del usuario
    try {
      if (typeof getCurrentUser === "function") {
        const user = await getCurrentUser();
        if (userNameElement) userNameElement.textContent = user.username || "Admin";
        if (userEmailElement) userEmailElement.textContent = user.email || "";
      }
    } catch (error) {
      console.error("Error al cargar usuario:", error);
      if (userNameElement) userNameElement.textContent = "Admin";
      if (userEmailElement) userEmailElement.textContent = "";
    }
  } else {
    // Usuario NO autenticado: mostrar login, ocultar perfil + logout
    if (adminSection) adminSection.style.display = "none";
    if (userProfile) userProfile.style.display = "none";
    if (btnLogin) btnLogin.style.display = "flex";
    if (btnLogout) btnLogout.style.display = "none";
  }
}

// Auto-inicializar cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", function () {
  updateSidebarAuth();
});
