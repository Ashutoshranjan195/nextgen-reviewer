/**
 * Auth UI — Login and registration form handling.
 */
const Auth = (() => {
    let isLoginMode = true;

    function init() {
        const loginForm = document.getElementById('form-login');
        const registerForm = document.getElementById('form-register');
        const toggleBtn = document.getElementById('btn-toggle-auth');
        const toggleText = document.getElementById('auth-toggle-text');

        // Toggle between login and register
        toggleBtn.addEventListener('click', () => {
            isLoginMode = !isLoginMode;
            loginForm.classList.toggle('hidden', !isLoginMode);
            registerForm.classList.toggle('hidden', isLoginMode);
            toggleBtn.textContent = isLoginMode ? 'Sign Up' : 'Sign In';
            toggleText.textContent = isLoginMode
                ? "Don't have an account?"
                : 'Already have an account?';
        });

        // Login handler
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btn-login');
            const username = document.getElementById('login-username').value.trim();
            const password = document.getElementById('login-password').value;

            if (!username || !password) return;

            btn.classList.add('loading');
            try {
                const data = await API.post('/login', { username, password });
                API.setToken(data.access_token);
                API.setUsername(data.username);
                App.showToast('Welcome back, ' + data.username + '!', 'success');
                App.navigateToApp();
            } catch (err) {
                App.showToast(err.message, 'error');
            } finally {
                btn.classList.remove('loading');
            }
        });

        // Register handler
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btn-register');
            const username = document.getElementById('register-username').value.trim();
            const password = document.getElementById('register-password').value;

            if (!username || !password) return;

            if (username.length < 3) {
                App.showToast('Username must be at least 3 characters', 'error');
                return;
            }
            if (password.length < 6) {
                App.showToast('Password must be at least 6 characters', 'error');
                return;
            }

            btn.classList.add('loading');
            try {
                await API.post('/register', { username, password });
                App.showToast('Account created! You can now sign in.', 'success');
                // Auto-switch to login
                toggleBtn.click();
                document.getElementById('login-username').value = username;
            } catch (err) {
                App.showToast(err.message, 'error');
            } finally {
                btn.classList.remove('loading');
            }
        });
    }

    return { init };
})();
