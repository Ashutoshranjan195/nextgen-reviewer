/**
 * API Client — Fetch wrapper with automatic JWT token injection.
 */
const API = (() => {
    const BASE = '/api';

    function getToken() {
        return localStorage.getItem('access_token');
    }

    function setToken(token) {
        localStorage.setItem('access_token', token);
    }

    function clearToken() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('username');
    }

    function getUsername() {
        return localStorage.getItem('username');
    }

    function setUsername(name) {
        localStorage.setItem('username', name);
    }

    function isAuthenticated() {
        return !!getToken();
    }

    /**
     * Make an authenticated JSON request.
     */
    async function request(endpoint, options = {}) {
        const url = `${BASE}${endpoint}`;
        const headers = {
            ...(options.headers || {}),
        };

        // Add auth header if we have a token
        const token = getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // Add JSON content-type for non-FormData bodies
        if (options.body && !(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }

        const response = await fetch(url, {
            ...options,
            headers,
        });

        // Handle 401 — session expired
        if (response.status === 401) {
            clearToken();
            window.dispatchEvent(new CustomEvent('auth:expired'));
            throw new Error('Session expired. Please log in again.');
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || data.message || `Request failed (${response.status})`);
        }

        return data;
    }

    // ── Convenience methods ──────────────────────────────────────────────

    function get(endpoint) {
        return request(endpoint, { method: 'GET' });
    }

    function post(endpoint, body) {
        return request(endpoint, {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }

    function uploadFile(endpoint, file) {
        const form = new FormData();
        form.append('file', file);
        return request(endpoint, {
            method: 'POST',
            body: form,
        });
    }

    return {
        getToken, setToken, clearToken,
        getUsername, setUsername,
        isAuthenticated,
        get, post, uploadFile,
    };
})();
