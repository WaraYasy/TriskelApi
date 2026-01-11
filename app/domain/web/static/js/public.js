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

        // TODO: Calcular cambios reales comparando con datos históricos
        // Por ahora están hardcodeados - se necesita endpoint de métricas históricas
        updateChange('playersChange', '+12.5%', true);
        updateChange('relicsChange', '-2.4%', false);

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
    return 287; // Valor por defecto
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
    // Mostrar datos de ejemplo si la API no está disponible
    updateStat('totalPlayers', 1974);
    updateStat('totalDecisions', 287);
    updateStat('totalRelics', 8430);
    updateStat('forestHealth', '75%');

    const progressBar = document.getElementById('forestProgress');
    if (progressBar) {
        progressBar.style.width = '75%';
    }

    updateChange('playersChange', '+12.5%', true);
    updateChange('relicsChange', '-2.4%', false);
}
