/**
 * App — Main SPA controller: routing, view management, toast system, and init.
 */
const App = (() => {
    const viewAuth = document.getElementById('view-auth');
    const viewApp = document.getElementById('view-app');

    // ── View / Tab Switching ─────────────────────────────────────────────

    function showAuthView() {
        viewAuth.classList.add('active');
        viewApp.classList.remove('active');
    }

    function navigateToApp() {
        viewAuth.classList.remove('active');
        viewApp.classList.add('active');

        // Set username in nav
        const username = API.getUsername();
        document.getElementById('nav-username').textContent = username || '';

        // Load default tab data
        switchTab('reviewer');
    }

    function switchTab(tabName) {
        // Update nav buttons
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === tabName);
        });

        // Update tab panels
        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.toggle('active', panel.id === `tab-${tabName}`);
        });

        // Load data for the tab
        switch (tabName) {
            case 'history':
                History.load();
                break;
            case 'rules':
                Rules.load();
                break;
            case 'dashboard':
                Dashboard.load();
                break;
        }
    }

    // ── Toast System ─────────────────────────────────────────────────────

    function showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);

        // Remove after animation
        setTimeout(() => {
            if (toast.parentNode) toast.remove();
        }, 4000);
    }

    // ── Init ─────────────────────────────────────────────────────────────

    function init() {
        // Initialize all modules
        Auth.init();
        Reviewer.init();
        History.init();
        Rules.init();
        Dashboard.init();

        // Navigation click handlers
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                switchTab(btn.dataset.view);
            });
        });

        // Logout
        document.getElementById('btn-logout').addEventListener('click', () => {
            API.clearToken();
            showAuthView();
            showToast('Logged out successfully', 'info');
        });

        // Listen for auth expiry
        window.addEventListener('auth:expired', () => {
            showAuthView();
            showToast('Session expired. Please log in again.', 'error');
        });

        // Check existing session
        if (API.isAuthenticated()) {
            navigateToApp();
        } else {
            showAuthView();
        }
    }

    // Boot when DOM is ready
    document.addEventListener('DOMContentLoaded', init);

    return { showToast, navigateToApp, switchTab };
})();
