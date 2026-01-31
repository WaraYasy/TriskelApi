/**
 * Utilidades JavaScript para Triskel Dashboard
 *
 * Funciones compartidas para formateo de datos,
 * validaciones y operaciones comunes.
 */

/**
 * Formatea una fecha ISO 8601 a formato dd-mm-yyyy hh:mm
 *
 * @param {string|null|undefined} dateString - Fecha en formato ISO 8601
 * @param {boolean} includeTime - Si incluir la hora (default: true)
 * @param {string} emptyText - Texto a mostrar si no hay fecha (default: "Sin registro")
 * @returns {string} Fecha formateada o texto de vacío
 *
 * Ejemplos:
 *   formatDate('2026-01-28T07:19:32.680396Z') → '28-01-2026 07:19'
 *   formatDate('2026-01-28T07:19:32.680396Z', false) → '28-01-2026'
 *   formatDate(null) → 'Sin registro'
 *   formatDate(undefined) → 'Sin registro'
 *   formatDate('') → 'Sin registro'
 *   formatDate('NaN') → 'Sin registro'
 */
function formatDate(dateString, includeTime = true, emptyText = 'Sin registro') {
    // Validar entrada
    if (!dateString ||
        dateString === 'null' ||
        dateString === 'undefined' ||
        dateString === 'NaN' ||
        dateString === '-' ||
        dateString.toString().trim() === '') {
        return emptyText;
    }

    try {
        // Intentar parsear la fecha
        const date = new Date(dateString);

        // Verificar si es una fecha válida
        if (isNaN(date.getTime())) {
            return emptyText;
        }

        // Obtener componentes de la fecha
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();

        let formatted = `${day}-${month}-${year}`;

        // Agregar hora si se requiere
        if (includeTime) {
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            formatted += ` ${hours}:${minutes}`;
        }

        return formatted;
    } catch (error) {
        console.warn('Error formateando fecha:', dateString, error);
        return emptyText;
    }
}

/**
 * Formatea una fecha como "fecha relativa" (hace X tiempo)
 *
 * @param {string|null|undefined} dateString - Fecha en formato ISO 8601
 * @param {string} emptyText - Texto a mostrar si no hay fecha
 * @returns {string} Fecha relativa o texto de vacío
 *
 * Ejemplos:
 *   formatRelativeDate('2026-01-31T10:00:00Z') → 'hace 2 horas'
 *   formatRelativeDate('2026-01-30T10:00:00Z') → 'hace 1 día'
 */
function formatRelativeDate(dateString, emptyText = 'Sin registro') {
    if (!dateString ||
        dateString === 'null' ||
        dateString === 'undefined' ||
        dateString === 'NaN' ||
        dateString === '-') {
        return emptyText;
    }

    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) {
            return emptyText;
        }

        const now = new Date();
        const diffMs = now - date;
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHour / 24);
        const diffWeek = Math.floor(diffDay / 7);
        const diffMonth = Math.floor(diffDay / 30);
        const diffYear = Math.floor(diffDay / 365);

        if (diffSec < 60) {
            return 'hace unos segundos';
        } else if (diffMin < 60) {
            return `hace ${diffMin} minuto${diffMin > 1 ? 's' : ''}`;
        } else if (diffHour < 24) {
            return `hace ${diffHour} hora${diffHour > 1 ? 's' : ''}`;
        } else if (diffDay < 7) {
            return `hace ${diffDay} día${diffDay > 1 ? 's' : ''}`;
        } else if (diffWeek < 4) {
            return `hace ${diffWeek} semana${diffWeek > 1 ? 's' : ''}`;
        } else if (diffMonth < 12) {
            return `hace ${diffMonth} mes${diffMonth > 1 ? 'es' : ''}`;
        } else {
            return `hace ${diffYear} año${diffYear > 1 ? 's' : ''}`;
        }
    } catch (error) {
        console.warn('Error formateando fecha relativa:', dateString, error);
        return emptyText;
    }
}

/**
 * Valida si un valor es nulo, indefinido o inválido
 *
 * @param {any} value - Valor a validar
 * @returns {boolean} True si es inválido
 */
function isInvalidValue(value) {
    return value === null ||
           value === undefined ||
           value === 'null' ||
           value === 'undefined' ||
           value === 'NaN' ||
           value === '-' ||
           value === '' ||
           (typeof value === 'number' && isNaN(value));
}

/**
 * Formatea un número con separadores de miles
 *
 * @param {number|string} number - Número a formatear
 * @param {string} emptyText - Texto si no hay número
 * @returns {string} Número formateado
 *
 * Ejemplos:
 *   formatNumber(1234567) → '1,234,567'
 *   formatNumber(null) → 'Sin datos'
 */
function formatNumber(number, emptyText = 'Sin datos') {
    if (isInvalidValue(number)) {
        return emptyText;
    }

    const num = parseFloat(number);
    if (isNaN(num)) {
        return emptyText;
    }

    return num.toLocaleString('es-ES');
}

/**
 * Formatea un porcentaje
 *
 * @param {number|string} value - Valor a formatear (0-100 o 0-1)
 * @param {number} decimals - Decimales a mostrar
 * @param {string} emptyText - Texto si no hay valor
 * @returns {string} Porcentaje formateado
 *
 * Ejemplos:
 *   formatPercentage(0.856) → '85.6%'
 *   formatPercentage(42.5) → '42.5%'
 */
function formatPercentage(value, decimals = 1, emptyText = 'Sin datos') {
    if (isInvalidValue(value)) {
        return emptyText;
    }

    const num = parseFloat(value);
    if (isNaN(num)) {
        return emptyText;
    }

    // Si el valor está entre 0 y 1, asumir que es decimal
    const percentage = num < 1 ? num * 100 : num;
    return `${percentage.toFixed(decimals)}%`;
}

/**
 * Escapa HTML para prevenir XSS
 *
 * @param {string} text - Texto a escapar
 * @returns {string} Texto escapado
 */
function escapeHtml(text) {
    if (!text) return '';

    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };

    return text.toString().replace(/[&<>"']/g, m => map[m]);
}

/**
 * Trunca texto largo
 *
 * @param {string} text - Texto a truncar
 * @param {number} maxLength - Longitud máxima
 * @param {string} suffix - Sufijo (default: '...')
 * @returns {string} Texto truncado
 */
function truncate(text, maxLength = 50, suffix = '...') {
    if (!text || text.length <= maxLength) {
        return text || '';
    }

    return text.substring(0, maxLength - suffix.length) + suffix;
}

/**
 * Formatea bytes a tamaño legible
 *
 * @param {number} bytes - Bytes a formatear
 * @param {number} decimals - Decimales a mostrar
 * @returns {string} Tamaño formateado
 *
 * Ejemplos:
 *   formatBytes(1024) → '1.0 KB'
 *   formatBytes(1536) → '1.5 KB'
 *   formatBytes(1048576) → '1.0 MB'
 */
function formatBytes(bytes, decimals = 1) {
    if (isInvalidValue(bytes) || bytes === 0) {
        return '0 Bytes';
    }

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
}

/**
 * Formatea duración en segundos a texto legible
 *
 * @param {number} seconds - Segundos a formatear
 * @param {string} emptyText - Texto si no hay valor
 * @returns {string} Duración formateada
 *
 * Ejemplos:
 *   formatDuration(65) → '1m 5s'
 *   formatDuration(3665) → '1h 1m 5s'
 */
function formatDuration(seconds, emptyText = 'Sin datos') {
    if (isInvalidValue(seconds)) {
        return emptyText;
    }

    const sec = parseInt(seconds);
    if (isNaN(sec) || sec < 0) {
        return emptyText;
    }

    const hours = Math.floor(sec / 3600);
    const minutes = Math.floor((sec % 3600) / 60);
    const secs = sec % 60;

    const parts = [];
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);
    if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);

    return parts.join(' ');
}

// Hacer las funciones globalmente disponibles
window.formatDate = formatDate;
window.formatRelativeDate = formatRelativeDate;
window.formatNumber = formatNumber;
window.formatPercentage = formatPercentage;
window.formatBytes = formatBytes;
window.formatDuration = formatDuration;
window.escapeHtml = escapeHtml;
window.truncate = truncate;
window.isInvalidValue = isInvalidValue;
