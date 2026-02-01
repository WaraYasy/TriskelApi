// Triskel Web - Authentication Module

const AUTH_API_URL = "/v1/auth";

/**
 * Set a cookie with the given name and value
 */
function setCookie(name, value, days = 1) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

/**
 * Delete a cookie by name
 */
function deleteCookie(name) {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
}

/**
 * Login user with username and password
 */
async function login(username, password) {
  const response = await fetch(`${AUTH_API_URL}/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    // Extraer mensaje del objeto detail si existe
    const errorMessage =
      typeof error.detail === "object" && error.detail.message
        ? error.detail.message
        : error.detail || "Error de autenticación. Verifica tus credenciales.";
    throw new Error(errorMessage);
  }

  const data = await response.json();

  // Save tokens in localStorage
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);

  // Save access token in cookie for server-side validation
  setCookie("admin_token", data.access_token, 1);

  return data;
}

/**
 * Logout current user
 */
async function logout() {
  const token = localStorage.getItem("access_token");

  if (token) {
    try {
      await fetch(`${AUTH_API_URL}/logout`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    } catch (error) {
      console.error("Logout error:", error);
    }
  }

  // Clear tokens from localStorage
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");

  // Clear cookie
  deleteCookie("admin_token");

  // Redirect to login
  window.location.href = "/web/admin/login";
}

/**
 * Get current user info
 */
async function getCurrentUser() {
  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("No token found");
  }

  const response = await fetch(`${AUTH_API_URL}/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/web/admin/login";
    }
    throw new Error("Failed to get user info");
  }

  return await response.json();
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
  return !!localStorage.getItem("access_token");
}

/**
 * Require authentication for page
 */
async function requireAuth() {
  if (!isAuthenticated()) {
    window.location.href = "/web/admin/login";
    return null;
  }

  try {
    return await getCurrentUser();
  } catch (error) {
    window.location.href = "/web/admin/login";
    return null;
  }
}
