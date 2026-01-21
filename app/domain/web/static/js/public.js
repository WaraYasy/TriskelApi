// Public Landing Page - JavaScript
// Carga métricas globales desde la API sin autenticación

document.addEventListener('DOMContentLoaded', async function () {
    await loadPublicMetrics();
});

async function loadPublicMetrics() {
    try {
        // Llamar al endpoint de métricas públicas
        const response = await fetch('/web/dashboard/api/metrics');

        if (!response.ok) {
            console.error('Error loading metrics:', response.status);
            showPlaceholderData();
            return;
        }

        const metrics = await response.json();

        // Actualizar estadísticas
        updateStat('totalPlayers', metrics.total_players || 0);
        updateStat('totalDecisions', calculateTotalDecisions(metrics));
        updateStat('totalRelics', metrics.total_relics || 0);
        updateStat('forestHealth', metrics.completion_rate ? `${metrics.completion_rate}%` : '0%');

        // Actualizar barra de progreso
        const progressBar = document.getElementById('forestProgress');
        if (progressBar && metrics.completion_rate) {
            progressBar.style.width = `${metrics.completion_rate}%`;
        }

        // Ocultar cambios si no hay datos históricos
        hideChange('playersChange');
        hideChange('relicsChange');

    } catch (error) {
        console.error('Error fetching public metrics:', error);
        showPlaceholderData();
    }
}

function calculateTotalDecisions(metrics) {
    // Calcular decisiones promedio por jugador
    if (metrics.total_games && metrics.total_players) {
        const avgDecisions = Math.round((metrics.total_games * 3) / metrics.total_players);
        return avgDecisions;
    }
    return 0;
}

function updateStat(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        // Animación de contador
        animateValue(element, 0, parseInt(value) || value, 1500);
    }
}

function updateChange(elementId, value, isPositive) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
        element.className = isPositive ? 'stat-change positive' : 'stat-change negative';
    }
}

function hideChange(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

function animateValue(element, start, end, duration) {
    // Si el valor no es numérico, solo actualizar
    if (typeof end === 'string') {
        element.textContent = end;
        return;
    }

    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.round(current).toLocaleString();
    }, 16);
}

function showPlaceholderData() {
    // Mostrar 0 si la API no está disponible (sin datos falsos)
    updateStat('totalPlayers', 0);
    updateStat('totalDecisions', 0);
    updateStat('totalRelics', 0);
    updateStat('forestHealth', '0%');

    const progressBar = document.getElementById('forestProgress');
    if (progressBar) {
        progressBar.style.width = '0%';
    }

    hideChange('playersChange');
    hideChange('relicsChange');
}
