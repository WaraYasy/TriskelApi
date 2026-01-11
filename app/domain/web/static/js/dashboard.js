// Triskel Web - Dashboard Module

/**
 * Load and display user information
 */
async function loadUserInfo() {
    try {
        const user = await requireAuth();
        
        if (!user) return;

        // Update navbar
        const userInfo = document.getElementById('userInfo');
        if (userInfo) {
            userInfo.textContent = user.username + ' (' + user.email + ')';
        }

        // Update role
        const userRole = document.getElementById('userRole');
        if (userRole) {
            userRole.textContent = user.role;
        }

        // Update admin info card
        const adminInfo = document.getElementById('adminInfo');
        if (adminInfo) {
            const statusClass = user.is_active ? 'status-active' : 'status-inactive';
            const statusText = user.is_active ? 'Active' : 'Inactive';
            
            adminInfo.innerHTML = '<div class="info-grid">' +
                '<div class="info-item">' +
                    '<p class="info-label">Username</p>' +
                    '<p class="info-value">' + user.username + '</p>' +
                '</div>' +
                '<div class="info-item">' +
                    '<p class="info-label">Email</p>' +
                    '<p class="info-value">' + user.email + '</p>' +
                '</div>' +
                '<div class="info-item">' +
                    '<p class="info-label">Role</p>' +
                    '<p class="info-value">' + user.role + '</p>' +
                '</div>' +
                '<div class="info-item">' +
                    '<p class="info-label">Status</p>' +
                    '<p class="info-value ' + statusClass + '">' + statusText + '</p>' +
                '</div>' +
            '</div>';
        }

        // Load stats
        await loadStats(user);
    } catch (error) {
        console.error('Error loading user info:', error);
    }
}

/**
 * Load dashboard stats
 */
async function loadStats(user) {
    // Placeholder - implement when endpoints are ready
    const totalPlayers = document.getElementById('totalPlayers');
    const totalGames = document.getElementById('totalGames');
    const totalEvents = document.getElementById('totalEvents');

    if (totalPlayers) totalPlayers.textContent = 'N/A';
    if (totalGames) totalGames.textContent = 'N/A';
    if (totalEvents) totalEvents.textContent = 'N/A';
}

/**
 * Initialize dashboard on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    loadUserInfo();
});
