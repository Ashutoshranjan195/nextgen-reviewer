/**
 * History UI — Display past code review submissions.
 */
const History = (() => {
    function init() {
        // History loads when the tab is activated (via App.switchTab)
    }

    async function load() {
        const container = document.getElementById('history-list');

        try {
            const data = await API.get('/history');
            const submissions = data.submissions || [];

            if (submissions.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <span class="empty-icon">📭</span>
                        <p>No submissions yet. Submit your first code review!</p>
                    </div>
                `;
                return submissions;
            }

            // Render submissions (newest first for display, but API returns oldest first)
            const displayItems = [...submissions].reverse();

            container.innerHTML = displayItems.map((sub, i) => {
                const ratingClass = getRatingClass(sub.rating);
                const timeAgo = formatTime(sub.created_at);

                return `
                    <div class="history-card glass-panel" style="animation-delay: ${i * 0.05}s">
                        <div class="history-rating ${ratingClass}">${sub.rating}</div>
                        <div class="history-info">
                            <div class="history-preview">${escapeHtml(sub.code_preview)}</div>
                            <div class="history-meta">
                                <span class="lang-badge">${sub.language}</span>
                                <span>${timeAgo}</span>
                            </div>
                        </div>
                        <div class="history-time">${formatDate(sub.created_at)}</div>
                    </div>
                `;
            }).join('');

            return submissions;
        } catch (err) {
            App.showToast('Failed to load history: ' + err.message, 'error');
            return [];
        }
    }

    function getRatingClass(rating) {
        if (rating >= 8) return 'excellent';
        if (rating >= 6) return 'good';
        if (rating >= 4) return 'average';
        return 'poor';
    }

    function formatTime(isoString) {
        if (!isoString) return '';
        try {
            const date = new Date(isoString);
            const now = new Date();
            const diff = (now - date) / 1000; // seconds

            if (diff < 60) return 'Just now';
            if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
            if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
            if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
            return formatDate(isoString);
        } catch {
            return '';
        }
    }

    function formatDate(isoString) {
        if (!isoString) return '';
        try {
            return new Date(isoString).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
            });
        } catch {
            return '';
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }

    return { init, load };
})();
