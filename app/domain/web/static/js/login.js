// Triskel Web - Login Page

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const loginBtn = document.getElementById('loginBtn');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        if (!username || !password) {
            showError('Please enter username and password');
            return;
        }

        // Disable button
        loginBtn.disabled = true;
        loginBtn.textContent = 'Logging in...';

        try {
            await login(username, password);
            window.location.href = '/web/admin/dashboard';
        } catch (error) {
            showError(error.message);
            loginBtn.disabled = false;
            loginBtn.textContent = 'Login';
        }
    });
});

function showError(message) {
    const existingAlert = document.querySelector('.alert-error');
    if (existingAlert) {
        existingAlert.remove();
    }

    const alert = document.createElement('div');
    alert.className = 'alert alert-error';
    alert.textContent = message;

    const form = document.getElementById('loginForm');
    form.insertBefore(alert, form.firstChild);
}
