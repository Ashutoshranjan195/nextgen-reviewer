/**
 * Dashboard UI — Stats cards with animated counters, language breakdown,
 * and recent activity feed.
 */
const Dashboard = (() => {
    function init() {
        // Dashboard loads when tab is activated
    }

    async function load() {
        try {
            // Fetch history and rules in parallel
            const [historyData, rulesData] = await Promise.all([
                API.get('/history'),
                API.get('/rules'),
            ]);

            const submissions = historyData.submissions || [];
            const rules = rulesData.rules || [];

            renderStats(submissions, rules);
            renderLanguageBreakdown(submissions);
            renderRecentActivity(submissions);
        } catch (err) {
            App.showToast('Failed to load dashboard: ' + err.message, 'error');
        }
    }

    function renderStats(submissions, rules) {
        const total = submissions.length;

        // Average rating
        let avgRating = '—';
        if (total > 0) {
            const sum = submissions.reduce((acc, s) => acc + s.rating, 0);
            avgRating = (sum / total).toFixed(1);
        }

        // Growth score: compare average of first half vs second half
        let growth = '—';
        if (total >= 2) {
            const mid = Math.floor(total / 2);
            const firstHalf = submissions.slice(0, mid);
            const secondHalf = submissions.slice(mid);
            const avgFirst = firstHalf.reduce((a, s) => a + s.rating, 0) / firstHalf.length;
            const avgSecond = secondHalf.reduce((a, s) => a + s.rating, 0) / secondHalf.length;
            const diff = avgSecond - avgFirst;
            growth = (diff >= 0 ? '+' : '') + diff.toFixed(1);
        }

        // Animate the counters
        animateCounter('stat-total', total);
        document.getElementById('stat-avg-rating').textContent = avgRating;
        document.getElementById('stat-growth').textContent = growth;
        document.getElementById('stat-rules').textContent = rules.length;
    }

    function renderLanguageBreakdown(submissions) {
        const container = document.getElementById('lang-breakdown');

        if (submissions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon">🌐</span>
                    <p>Submit some reviews to see language stats</p>
                </div>
            `;
            return;
        }

        // Count per language
        const langCounts = {};
        submissions.forEach(s => {
            langCounts[s.language] = (langCounts[s.language] || 0) + 1;
        });

        // Sort by count descending
        const sorted = Object.entries(langCounts).sort((a, b) => b[1] - a[1]);
        const maxCount = sorted[0][1];

        container.innerHTML = sorted.map(([lang, count]) => {
            const pct = (count / maxCount) * 100;
            return `
                <div class="lang-bar-item">
                    <span class="lang-bar-name">${lang}</span>
                    <div class="lang-bar-track">
                        <div class="lang-bar-fill" style="width: ${pct}%"></div>
                    </div>
                    <span class="lang-bar-count">${count}</span>
                </div>
            `;
        }).join('');
    }

    function renderRecentActivity(submissions) {
        const container = document.getElementById('recent-activity');

        if (submissions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon">🕐</span>
                    <p>No recent activity</p>
                </div>
            `;
            return;
        }

        // Show last 8 submissions
        const recent = [...submissions].reverse().slice(0, 8);

        container.innerHTML = recent.map(sub => {
            const time = formatTimeAgo(sub.created_at);
            return `
                <div class="activity-item">
                    <div class="activity-dot"></div>
                    <span class="activity-text">
                        Reviewed <strong>${sub.language}</strong> code — rated <strong>${sub.rating}/10</strong>
                    </span>
                    <span class="activity-time">${time}</span>
                </div>
            `;
        }).join('');
    }

    function animateCounter(elementId, target) {
        const el = document.getElementById(elementId);
        const duration = 800;
        const startTime = performance.now();

        function step(timestamp) {
            const progress = Math.min((timestamp - startTime) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(target * eased);
            if (progress < 1) requestAnimationFrame(step);
        }

        requestAnimationFrame(step);
    }

    function formatTimeAgo(isoString) {
        if (!isoString) return '';
        try {
            const date = new Date(isoString);
            const now = new Date();
            const diff = (now - date) / 1000;

            if (diff < 60) return 'Just now';
            if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
            if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
            if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        } catch {
            return '';
        }
    }

    return { init, load };
})();
