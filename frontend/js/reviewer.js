/**
 * Reviewer UI — Code submission and review results display.
 */
const Reviewer = (() => {
    function init() {
        const codeInput = document.getElementById('code-input');
        const charCount = document.getElementById('char-count');
        const submitBtn = document.getElementById('btn-submit-code');

        // Character count
        codeInput.addEventListener('input', () => {
            const len = codeInput.value.length;
            charCount.textContent = `${len.toLocaleString()} / 50,000 chars`;
            if (len > 50000) {
                charCount.style.color = 'var(--color-error)';
            } else {
                charCount.style.color = 'var(--text-tertiary)';
            }
        });

        // Tab key support in textarea
        codeInput.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                e.preventDefault();
                const start = codeInput.selectionStart;
                const end = codeInput.selectionEnd;
                codeInput.value = codeInput.value.substring(0, start) + '    ' + codeInput.value.substring(end);
                codeInput.selectionStart = codeInput.selectionEnd = start + 4;
            }
        });

        // Submit code for review
        submitBtn.addEventListener('click', async () => {
            const code = codeInput.value.trim();
            const language = document.getElementById('language-select').value;

            if (!code) {
                App.showToast('Please paste some code to review', 'error');
                return;
            }

            if (code.length > 50000) {
                App.showToast('Code exceeds the 50,000 character limit', 'error');
                return;
            }

            submitBtn.classList.add('loading');
            try {
                const result = await API.post('/submit', { code, language });
                displayResults(result);
                App.showToast('Review complete! Rating: ' + result.rating + '/10', 'success');
            } catch (err) {
                App.showToast(err.message, 'error');
            } finally {
                submitBtn.classList.remove('loading');
            }
        });
    }

    function displayResults(result) {
        const panel = document.getElementById('review-results');
        panel.classList.remove('hidden');

        // Rating
        const ratingValue = document.getElementById('rating-value');
        const ratingBadge = document.getElementById('rating-badge');
        ratingValue.textContent = result.rating;

        // Color-code rating
        ratingBadge.className = 'rating-badge';
        if (result.rating >= 8) ratingBadge.classList.add('excellent');
        else if (result.rating >= 6) ratingBadge.classList.add('good');
        else if (result.rating >= 4) ratingBadge.classList.add('average');
        else ratingBadge.classList.add('poor');

        // Animated counter
        animateValue(ratingValue, 0, result.rating, 600);

        // Feedback
        document.getElementById('review-feedback').textContent = result.feedback;

        // Issues
        const issuesList = document.getElementById('issues-list');
        if (result.issues && result.issues.length > 0) {
            issuesList.innerHTML = result.issues.map((issue, i) => `
                <div class="issue-item" style="animation-delay: ${i * 0.08}s">
                    <span class="issue-type-badge ${issue.type}">${issue.type}</span>
                    <span class="issue-description">${escapeHtml(issue.description)}</span>
                </div>
            `).join('');
        } else {
            issuesList.innerHTML = '<p style="color: var(--color-success); font-size: 0.9rem;">✅ No issues found — excellent code!</p>';
        }

        // Code preview
        document.getElementById('code-preview').textContent = result.code_preview || '';

        // Smooth scroll to results
        panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function animateValue(el, start, end, duration) {
        const range = end - start;
        const startTime = performance.now();

        function step(timestamp) {
            const progress = Math.min((timestamp - startTime) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
            el.textContent = Math.round(start + range * eased);
            if (progress < 1) requestAnimationFrame(step);
        }

        requestAnimationFrame(step);
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    return { init };
})();
