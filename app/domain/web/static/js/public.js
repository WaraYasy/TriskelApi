// Public Landing Page - JavaScript
// Carga métricas globales desde la API con actualización en tiempo real

const REFRESH_INTERVAL = 30000; // 30 segundos
let pollingInterval = null;
let lastMetrics = null;

document.addEventListener("DOMContentLoaded", async function () {
  await loadPublicMetrics();
  startPolling();
});

/**
 * Inicia el polling para actualizar métricas en tiempo real
 */
function startPolling() {
  if (pollingInterval) return;

  pollingInterval = setInterval(async () => {
    await refreshMetrics();
  }, REFRESH_INTERVAL);

  console.log(
    `Polling iniciado: actualizando cada ${REFRESH_INTERVAL / 1000}s`,
  );
}

/**
 * Detiene el polling
 */
function stopPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
    console.log("Polling detenido");
  }
}

/**
 * Refresca las métricas sin animación completa
 */
async function refreshMetrics() {
  try {
    const response = await fetch("/web/dashboard/api/metrics");

    if (!response.ok) {
      console.error("Error refreshing metrics:", response.status);
      return;
    }

    const metrics = await response.json();

    // Solo actualizar si hay cambios
    if (JSON.stringify(metrics) !== JSON.stringify(lastMetrics)) {
      updateStatSmooth("totalPlayers", metrics.total_players || 0);
      updateStatSmooth("totalDecisions", calculateTotalDecisions(metrics));
      updateStatSmooth("totalRelics", metrics.total_relics || 0);
      updateStatDirect(
        "forestHealth",
        metrics.completion_rate ? `${metrics.completion_rate}%` : "0%",
      );

      // Actualizar barra de progreso (soporta ambos IDs)
      const progressBar =
        document.getElementById("forestProgress") ||
        document.getElementById("forestProgressBar");
      if (progressBar && metrics.completion_rate) {
        progressBar.style.width = `${metrics.completion_rate}%`;
      }

      lastMetrics = metrics;
      updateLastRefreshTime();
    }
  } catch (error) {
    console.error("Error refreshing metrics:", error);
  }
}

/**
 * Carga inicial de métricas con animación completa
 */
async function loadPublicMetrics() {
  try {
    const response = await fetch("/web/dashboard/api/metrics");

    if (!response.ok) {
      console.error("Error loading metrics:", response.status);
      showPlaceholderData();
      return;
    }

    const metrics = await response.json();
    lastMetrics = metrics;

    // Actualizar estadísticas con animación
    updateStat("totalPlayers", metrics.total_players || 0);
    updateStat("totalDecisions", calculateTotalDecisions(metrics));
    updateStat("totalRelics", metrics.total_relics || 0);
    updateStat(
      "forestHealth",
      metrics.completion_rate ? `${metrics.completion_rate}%` : "0%",
    );

    // Actualizar barra de progreso (soporta ambos IDs)
    const progressBar =
      document.getElementById("forestProgress") ||
      document.getElementById("forestProgressBar");
    if (progressBar && metrics.completion_rate) {
      progressBar.style.width = `${metrics.completion_rate}%`;
    }

    // Ocultar cambios si no hay datos históricos
    hideChange("playersChange");
    hideChange("relicsChange");

    updateLastRefreshTime();
  } catch (error) {
    console.error("Error fetching public metrics:", error);
    showPlaceholderData();
  }
}

function calculateTotalDecisions(metrics) {
  if (metrics.total_games && metrics.total_players) {
    const avgDecisions = Math.round(
      (metrics.total_games * 3) / metrics.total_players,
    );
    return avgDecisions;
  }
  return 0;
}

/**
 * Actualiza stat con animación completa (carga inicial)
 */
function updateStat(elementId, value) {
  const element = document.getElementById(elementId);
  if (element) {
    animateValue(element, 0, parseInt(value) || value, 1500);
  }
}

/**
 * Actualiza stat con transición suave (polling)
 */
function updateStatSmooth(elementId, value) {
  const element = document.getElementById(elementId);
  if (element) {
    const currentValue = parseInt(element.textContent.replace(/,/g, "")) || 0;
    if (currentValue !== value) {
      animateValue(element, currentValue, value, 500);
    }
  }
}

/**
 * Actualiza stat directamente sin animación
 */
function updateStatDirect(elementId, value) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = value;
  }
}

function updateChange(elementId, value, isPositive) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = value;
    element.className = isPositive
      ? "stat-change positive"
      : "stat-change negative";
  }
}

function hideChange(elementId) {
  const element = document.getElementById(elementId);
  if (element) {
    element.style.display = "none";
  }
}

function animateValue(element, start, end, duration) {
  if (typeof end === "string") {
    element.textContent = end;
    return;
  }

  const range = end - start;
  if (range === 0) return;

  const increment = range / (duration / 16);
  let current = start;

  const timer = setInterval(() => {
    current += increment;
    if (
      (increment > 0 && current >= end) ||
      (increment < 0 && current <= end)
    ) {
      current = end;
      clearInterval(timer);
    }
    element.textContent = Math.round(current).toLocaleString();
  }, 16);
}

function showPlaceholderData() {
  updateStatDirect("totalPlayers", "0");
  updateStatDirect("totalDecisions", "0");
  updateStatDirect("totalRelics", "0");
  updateStatDirect("forestHealth", "0%");

  const progressBar =
    document.getElementById("forestProgress") ||
    document.getElementById("forestProgressBar");
  if (progressBar) {
    progressBar.style.width = "0%";
  }

  hideChange("playersChange");
  hideChange("relicsChange");
}

function updateLastRefreshTime() {
  const element = document.getElementById("lastUpdate");
  if (element) {
    const now = new Date();
    element.textContent = `Actualizado: ${now.toLocaleTimeString("es-ES")}`;
  }
}

// Pausar polling cuando la pestaña no está visible
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    stopPolling();
  } else {
    refreshMetrics();
    startPolling();
  }
});
