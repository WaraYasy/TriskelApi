// Dashboard Admin - JavaScript
// Carga métricas y datos para el panel de administración con actualización en tiempo real

const METRICS_REFRESH_INTERVAL = 30000; // 30 segundos
const EVENTS_REFRESH_INTERVAL = 15000; // 15 segundos
let metricsPollingInterval = null;
let eventsPollingInterval = null;
let lastMetrics = null;
let lastEventsHash = null;

document.addEventListener('DOMContentLoaded', async function () {
    await loadUserInfo();
    await loadDashboardMetrics();
    await loadCharts();
    await loadRecentEvents();
    startPolling();
});

/**
 * Inicia el polling para actualización en tiempo real
 */
function startPolling() {
    if (!metricsPollingInterval) {
        metricsPollingInterval = setInterval(refreshMetrics, METRICS_REFRESH_INTERVAL);
    }
    if (!eventsPollingInterval) {
        eventsPollingInterval = setInterval(refreshEvents, EVENTS_REFRESH_INTERVAL);
    }
    console.log('Polling iniciado: métricas cada 30s, eventos cada 15s');
}

/**
 * Detiene el polling
 */
function stopPolling() {
    if (metricsPollingInterval) {
        clearInterval(metricsPollingInterval);
        metricsPollingInterval = null;
    }
    if (eventsPollingInterval) {
        clearInterval(eventsPollingInterval);
        eventsPollingInterval = null;
    }
    console.log('Polling detenido');
}

/**
 * Refresca métricas sin animación completa
 */
async function refreshMetrics() {
    try {
        const response = await fetch('/web/dashboard/api/metrics');
        if (!response.ok) return;

        const metrics = await response.json();

        if (JSON.stringify(metrics) !== JSON.stringify(lastMetrics)) {
            updateMetricSmooth('totalPlayers', metrics.total_players || 0);
            updateMetricSmooth('totalDecisions', calculateAvgDecisions(metrics));
            updateMetricSmooth('totalRelics', calculateTotalRelics(metrics));
            updateMetricDirect('forestHealth', `${metrics.completion_rate || 0}%`);

            const progressBar = document.getElementById('forestProgressBar');
            if (progressBar) {
                progressBar.style.width = `${metrics.completion_rate || 0}%`;
            }

            lastMetrics = metrics;
            updateLastRefreshIndicator();
        }
    } catch (error) {
        console.error('Error refreshing metrics:', error);
    }
}

/**
 * Refresca eventos
 */
async function refreshEvents() {
    try {
        const response = await fetch('/web/dashboard/api/events');
        if (!response.ok) return;

        const events = await response.json();
        const eventsHash = JSON.stringify(events);

        if (eventsHash !== lastEventsHash) {
            lastEventsHash = eventsHash;
            renderEvents(events);
            updateLastRefreshIndicator();
        }
    } catch (error) {
        console.error('Error refreshing events:', error);
    }
}

/**
 * Cargar información del usuario autenticado
 */
async function loadUserInfo() {
    try {
        const user = await requireAuth();

        if (!user) return;

        const userName = document.getElementById('userName');
        const userEmail = document.getElementById('userEmail');

        if (userName) userName.textContent = user.username || 'Admin';
        if (userEmail) userEmail.textContent = user.email || 'admin@example.com';

    } catch (error) {
        console.error('Error loading user info:', error);
    }
}

/**
 * Cargar métricas del dashboard (carga inicial con animación)
 */
async function loadDashboardMetrics() {
    try {
        const response = await fetch('/web/dashboard/api/metrics');

        if (!response.ok) {
            console.error('Error loading metrics:', response.status);
            showPlaceholderMetrics();
            return;
        }

        const metrics = await response.json();
        lastMetrics = metrics;

        updateMetric('totalPlayers', metrics.total_players || 0);
        updateMetric('totalDecisions', calculateAvgDecisions(metrics));
        updateMetric('totalRelics', calculateTotalRelics(metrics));
        updateMetric('forestHealth', `${metrics.completion_rate || 0}%`);

        const progressBar = document.getElementById('forestProgressBar');
        if (progressBar) {
            const percentage = metrics.completion_rate || 0;
            setTimeout(() => {
                progressBar.style.width = `${percentage}%`;
            }, 300);
        }

        updateLastRefreshIndicator();

    } catch (error) {
        console.error('Error fetching dashboard metrics:', error);
        showPlaceholderMetrics();
    }
}

function calculateAvgDecisions(metrics) {
    if (metrics.total_games && metrics.total_players) {
        return Math.round((metrics.total_games * 3) / metrics.total_players);
    }
    return 0;
}

function calculateTotalRelics(metrics) {
    if (metrics.total_relics) {
        return metrics.total_relics;
    }
    if (metrics.completed_games) {
        return metrics.completed_games * 5;
    }
    return 0;
}

/**
 * Actualiza métrica con animación completa (carga inicial)
 */
function updateMetric(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        if (typeof value === 'number') {
            animateValue(element, 0, value, 1500);
        } else {
            element.textContent = value;
        }
    }
}

/**
 * Actualiza métrica con transición suave (polling)
 */
function updateMetricSmooth(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        const currentValue = parseInt(element.textContent.replace(/,/g, '')) || 0;
        if (currentValue !== value) {
            animateValue(element, currentValue, value, 500);
        }
    }
}

/**
 * Actualiza métrica directamente sin animación
 */
function updateMetricDirect(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

function animateValue(element, start, end, duration) {
    const range = end - start;
    if (range === 0) return;

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

function showPlaceholderMetrics() {
    updateMetricDirect('totalPlayers', '0');
    updateMetricDirect('totalDecisions', '0');
    updateMetricDirect('totalRelics', '0');
    updateMetricDirect('forestHealth', '0%');

    const progressBar = document.getElementById('forestProgressBar');
    if (progressBar) {
        setTimeout(() => {
            progressBar.style.width = '0%';
        }, 300);
    }
}

/**
 * Cargar gráficos con Plotly
 */
async function loadCharts() {
    const affinityData = generateAffinityTrendData();
    const affinityLayout = {
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        margin: { t: 20, r: 20, b: 40, l: 40 },
        xaxis: {
            gridcolor: 'rgba(75, 85, 99, 0.2)',
            color: '#9ca3af',
            showline: false
        },
        yaxis: {
            gridcolor: 'rgba(75, 85, 99, 0.2)',
            color: '#9ca3af',
            showline: false,
            range: [0, 100]
        },
        showlegend: true,
        legend: {
            font: { color: '#9ca3af' },
            orientation: 'h',
            y: -0.2
        }
    };

    Plotly.newPlot('affinityChart', affinityData, affinityLayout, {
        responsive: true,
        displayModeBar: false
    });

    const moralData = generateMoralAxesData();
    const moralLayout = {
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        margin: { t: 20, r: 20, b: 40, l: 40 },
        showlegend: false
    };

    Plotly.newPlot('moralAxesChart', moralData, moralLayout, {
        responsive: true,
        displayModeBar: false
    });
}

function generateAffinityTrendData() {
    const days = 30;
    const dates = [];
    const affinityValues = [];
    const corruptionValues = [];

    for (let i = days; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        dates.push(date.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' }));

        const baseAffinity = 50 + Math.sin(i / 5) * 15 + (days - i) * 0.5;
        const baseCorruption = 30 + Math.cos(i / 4) * 10 + (i) * 0.2;

        affinityValues.push(baseAffinity + Math.random() * 5);
        corruptionValues.push(baseCorruption + Math.random() * 5);
    }

    return [
        {
            x: dates,
            y: affinityValues,
            type: 'scatter',
            mode: 'lines',
            name: 'Nivel de Afinidad',
            line: {
                color: '#34d399',
                width: 3,
                shape: 'spline'
            },
            fill: 'tozeroy',
            fillcolor: 'rgba(52, 211, 153, 0.1)'
        },
        {
            x: dates,
            y: corruptionValues,
            type: 'scatter',
            mode: 'lines',
            name: 'Corrupción',
            line: {
                color: '#f59e0b',
                width: 2,
                shape: 'spline',
                dash: 'dot'
            }
        }
    ];
}

function generateMoralAxesData() {
    const categories = ['Empatía', 'Indiferencia', 'Exploración', 'Combate'];
    const values = [65, 35, 82, 45];

    return [{
        type: 'bar',
        x: categories,
        y: values,
        marker: {
            color: ['#34d399', '#6b7280', '#f59e0b', '#a855f7'],
            opacity: 0.8
        },
        text: values.map(v => `${v}%`),
        textposition: 'outside',
        textfont: {
            color: '#9ca3af'
        }
    }];
}

/**
 * Cargar eventos recientes desde la API
 */
async function loadRecentEvents() {
    const tableBody = document.getElementById('eventsTableBody');
    if (!tableBody) return;

    try {
        const response = await fetch('/web/dashboard/api/events');

        if (!response.ok) {
            showNoEventsMessage(tableBody);
            return;
        }

        const events = await response.json();
        lastEventsHash = JSON.stringify(events);
        renderEvents(events);

    } catch (error) {
        console.error('Error loading events:', error);
        showNoEventsMessage(document.getElementById('eventsTableBody'));
    }
}

/**
 * Renderiza los eventos en la tabla
 */
function renderEvents(events) {
    const tableBody = document.getElementById('eventsTableBody');
    if (!tableBody) return;

    if (!events || events.length === 0) {
        showNoEventsMessage(tableBody);
        return;
    }

    tableBody.innerHTML = events.map(event => {
        const eventInfo = getEventDisplayInfo(event);
        const formattedDate = formatEventDate(event.timestamp);

        return `
        <tr>
            <td>
                <div class="event-name">
                    <div class="event-icon ${eventInfo.iconType}">
                        ${eventInfo.icon}
                    </div>
                    <span>${event.event_type || 'Evento'}</span>
                </div>
            </td>
            <td>@${event.player_username || 'desconocido'}</td>
            <td>
                <span class="event-status ${eventInfo.status}">
                    ${eventInfo.status}
                </span>
            </td>
            <td>${formattedDate}</td>
            <td>
                <button class="chart-action">→</button>
            </td>
        </tr>
    `;
    }).join('');
}

function showNoEventsMessage(tableBody) {
    if (!tableBody) return;
    tableBody.innerHTML = `
        <tr>
            <td colspan="5" style="text-align: center; color: #9ca3af; padding: 2rem;">
                No hay eventos recientes
            </td>
        </tr>
    `;
}

function getEventDisplayInfo(event) {
    const eventType = (event.event_type || '').toLowerCase();

    const eventTypes = {
        'relic_found': { icon: '🏺', iconType: 'info', status: 'rare' },
        'level_completed': { icon: '✓', iconType: 'success', status: 'completed' },
        'death': { icon: '💀', iconType: 'danger', status: 'critical' },
        'choice_made': { icon: '⚖️', iconType: 'warning', status: 'decision' },
        'game_started': { icon: '🎮', iconType: 'info', status: 'started' },
        'game_completed': { icon: '🏆', iconType: 'success', status: 'completed' }
    };

    return eventTypes[eventType] || { icon: '📝', iconType: 'info', status: 'event' };
}

function formatEventDate(timestamp) {
    if (!timestamp) return 'Fecha desconocida';

    try {
        const date = new Date(timestamp);
        return date.toLocaleDateString('es-ES', {
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return 'Fecha desconocida';
    }
}

/**
 * Actualiza el indicador de última actualización
 */
function updateLastRefreshIndicator() {
    const indicator = document.getElementById('lastRefresh');
    if (indicator) {
        const now = new Date();
        indicator.textContent = `Actualizado: ${now.toLocaleTimeString('es-ES')}`;
        indicator.classList.add('pulse');
        setTimeout(() => indicator.classList.remove('pulse'), 1000);
    }
}

/**
 * Función de logout
 */
function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    window.location.href = '/web/admin/login';
}

// Pausar polling cuando la pestaña no está visible
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        stopPolling();
    } else {
        refreshMetrics();
        refreshEvents();
        startPolling();
    }
});
