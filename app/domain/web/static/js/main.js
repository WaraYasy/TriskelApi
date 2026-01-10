/**
 * Triskel Dashboard - Main JavaScript
 * Funcionalidades comunes del dashboard
 */

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('Triskel Dashboard cargado');

    // Añadir animaciones de entrada
    addFadeInAnimations();

    // Inicializar tooltips de Bootstrap
    initializeTooltips();

    // Auto-actualizar métricas cada 30 segundos (si está en analytics)
    if (window.location.pathname.includes('/dashboard')) {
        startMetricsAutoRefresh(30000); // 30 segundos
    }
});


/**
 * Añade animaciones de fade-in a los elementos
 */
function addFadeInAnimations() {
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });
}


/**
 * Inicializa los tooltips de Bootstrap
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}


/**
 * Auto-actualizar métricas desde la API
 * @param {number} interval - Intervalo en milisegundos
 */
function startMetricsAutoRefresh(interval) {
    setInterval(async () => {
        try {
            const response = await fetch('/dashboard/api/metrics');
            if (response.ok) {
                const metrics = await response.json();
                updateMetricsDisplay(metrics);
            }
        } catch (error) {
            console.error('Error al actualizar métricas:', error);
        }
    }, interval);
}


/**
 * Actualiza las métricas en el DOM
 * @param {Object} metrics - Objeto con las métricas
 */
function updateMetricsDisplay(metrics) {
    // TODO: Implementar actualización de las cards de métricas
    console.log('Métricas actualizadas:', metrics);
}


/**
 * Exportar datos a CSV
 * @param {string} type - Tipo de datos a exportar (players, games, events)
 */
function exportData(type) {
    window.location.href = `/dashboard/export?type=${type}&format=csv`;
}


/**
 * Mostrar spinner de carga
 */
function showLoadingSpinner() {
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    spinner.id = 'global-spinner';
    document.body.appendChild(spinner);
}


/**
 * Ocultar spinner de carga
 */
function hideLoadingSpinner() {
    const spinner = document.getElementById('global-spinner');
    if (spinner) {
        spinner.remove();
    }
}


/**
 * Formatear segundos a formato legible (1h 30m)
 * @param {number} seconds - Segundos
 * @returns {string} - Tiempo formateado
 */
function formatPlaytime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
}


/**
 * Formatear fecha a formato legible
 * @param {string} isoDate - Fecha en formato ISO
 * @returns {string} - Fecha formateada
 */
function formatDate(isoDate) {
    const date = new Date(isoDate);
    return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}


// Exponer funciones globales
window.TriskelDashboard = {
    exportData,
    showLoadingSpinner,
    hideLoadingSpinner,
    formatPlaytime,
    formatDate
};
