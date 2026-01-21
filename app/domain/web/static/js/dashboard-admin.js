// Dashboard Admin - JavaScript
// Carga métricas y datos para el panel de administración

document.addEventListener('DOMContentLoaded', async function () {
    await loadUserInfo();
    await loadDashboardMetrics();
    await loadCharts();
    await loadRecentEvents();
});

/**
 * Cargar información del usuario autenticado
 */
async function loadUserInfo() {
    try {
        const user = await requireAuth();

        if (!user) return;

        // Actualizar información del usuario en el sidebar
        const userName = document.getElementById('userName');
        const userEmail = document.getElementById('userEmail');

        if (userName) userName.textContent = user.username || 'Admin';
        if (userEmail) userEmail.textContent = user.email || 'admin@example.com';

    } catch (error) {
        console.error('Error loading user info:', error);
    }
}

/**
 * Cargar métricas del dashboard
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

        // Actualizar métricas
        updateMetric('totalPlayers', metrics.total_players || 0);
        updateMetric('totalDecisions', calculateAvgDecisions(metrics));
        updateMetric('totalRelics', calculateTotalRelics(metrics));
        updateMetric('forestHealth', `${metrics.completion_rate || 75}%`);

        // Actualizar barra de progreso
        const progressBar = document.getElementById('forestProgressBar');
        if (progressBar) {
            const percentage = metrics.completion_rate || 75;
            setTimeout(() => {
                progressBar.style.width = `${percentage}%`;
            }, 300);
        }

    } catch (error) {
        console.error('Error fetching dashboard metrics:', error);
        showPlaceholderMetrics();
    }
}

function calculateAvgDecisions(metrics) {
    if (metrics.total_games && metrics.total_players) {
        // Asumiendo ~3 decisiones por partida
        return Math.round((metrics.total_games * 3) / metrics.total_players);
    }
    return 0;
}

function calculateTotalRelics(metrics) {
    // Si tenemos datos de reliquias, usarlos
    if (metrics.total_relics) {
        return metrics.total_relics;
    }
    // Estimación basada en partidas completadas
    if (metrics.completed_games) {
        return metrics.completed_games * 5; // ~5 reliquias por juego completado
    }
    return 0;
}

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

function animateValue(element, start, end, duration) {
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

function showPlaceholderMetrics() {
    // Mostrar 0 si la API no está disponible (sin datos falsos)
    updateMetric('totalPlayers', 0);
    updateMetric('totalDecisions', 0);
    updateMetric('totalRelics', 0);
    updateMetric('forestHealth', '0%');

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
    // Gráfico de tendencia de afinidad
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

    // Gráfico de ejes morales
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

        // Generar datos simulados con tendencia
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

    } catch (error) {
        console.error('Error loading events:', error);
        showNoEventsMessage(tableBody);
    }
}

function showNoEventsMessage(tableBody) {
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
 * Función de logout
 */
function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    window.location.href = '/web/admin/login';
}
