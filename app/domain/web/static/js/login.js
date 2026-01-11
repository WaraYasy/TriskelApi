// Triskel Web - Login Page

document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.getElementById('loginForm');
    const loginBtn = document.getElementById('loginBtn');
    const loginBtnText = document.getElementById('loginBtnText');
    const loginBtnIcon = document.getElementById('loginBtnIcon');
    const loginSpinner = document.getElementById('loginSpinner');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');

    loginForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        if (!username || !password) {
            showError('Por favor ingresa usuario y contraseña');
            return;
        }

        // Disable button and show loading state
        setLoadingState(true);

        try {
            await login(username, password);
            showSuccess('¡Acceso concedido! Redirigiendo...');
            setTimeout(() => {
                window.location.href = '/web/admin/dashboard';
            }, 800);
        } catch (error) {
            showError(error.message || 'Error de autenticación. Verifica tus credenciales.');
            setLoadingState(false);
        }
    });

    function setLoadingState(isLoading) {
        loginBtn.disabled = isLoading;

        if (isLoading) {
            loginBtnText.style.display = 'none';
            loginBtnIcon.style.display = 'none';
            loginSpinner.style.display = 'block';
        } else {
            loginBtnText.style.display = 'block';
            loginBtnIcon.style.display = 'block';
            loginSpinner.style.display = 'none';
        }
    }
});

function showError(message) {
    clearAlerts();

    const alert = document.createElement('div');
    alert.className = 'alert alert-error';
    alert.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style="flex-shrink: 0;">
            <circle cx="10" cy="10" r="9" stroke="currentColor" stroke-width="1.5"/>
            <path d="M10 6v4M10 14h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <span>${message}</span>
    `;

    const alertContainer = document.getElementById('alertContainer');
    alertContainer.appendChild(alert);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
}

function showSuccess(message) {
    clearAlerts();

    const alert = document.createElement('div');
    alert.className = 'alert alert-success';
    alert.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style="flex-shrink: 0;">
            <circle cx="10" cy="10" r="9" stroke="currentColor" stroke-width="1.5"/>
            <path d="M6 10l3 3 5-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>${message}</span>
    `;

    const alertContainer = document.getElementById('alertContainer');
    alertContainer.appendChild(alert);
}

function clearAlerts() {
    const alertContainer = document.getElementById('alertContainer');
    alertContainer.innerHTML = '';
}

