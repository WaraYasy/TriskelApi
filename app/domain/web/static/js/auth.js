// Triskel Web - Authentication Module

const AUTH_API_URL = '/v1/auth';

/**
 * Login user with username and password
 */
async function login(username, password) {
    const response = await fetch(`${AUTH_API_URL}/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    
    // Save tokens
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    
    return data;
}

/**
 * Logout current user
 */
async function logout() {
    const token = localStorage.getItem('access_token');

    if (token) {
        try {
            await fetch(`${AUTH_API_URL}/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        } catch (error) {
            console.error('Logout error:', error);
        }
    }

    // Clear tokens
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    // Redirect to login
    window.location.href = '/web/admin/login';
}

/**
 * Get current user info
 */
async function getCurrentUser() {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
        throw new Error('No token found');
    }

    const response = await fetch(`${AUTH_API_URL}/me`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    if (!response.ok) {
        if (response.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/web/admin/login';
        }
        throw new Error('Failed to get user info');
    }

    return await response.json();
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!localStorage.getItem('access_token');
}

/**
 * Require authentication for page
 */
async function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/web/admin/login';
        return null;
    }

    try {
        return await getCurrentUser();
    } catch (error) {
        window.location.href = '/web/admin/login';
        return null;
    }
}
