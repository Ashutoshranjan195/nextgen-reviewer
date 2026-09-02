/**
 * Rules UI — CSV upload (with drag-and-drop) and rules list display.
 */
const Rules = (() => {
    function init() {
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('csv-file-input');

        // Click to browse
        dropZone.addEventListener('click', (e) => {
            if (e.target.tagName !== 'LABEL' && e.target.tagName !== 'INPUT') {
                fileInput.click();
            }
        });

        // File input change
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                handleUpload(fileInput.files[0]);
            }
        });

        // Drag and drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                handleUpload(e.dataTransfer.files[0]);
            }
        });
    }

    async function handleUpload(file) {
        const status = document.getElementById('upload-status');

        if (!file.name.endsWith('.csv')) {
            showStatus('Please upload a .csv file', 'error');
            return;
        }

        showStatus('Uploading...', 'info');

        try {
            const result = await API.uploadFile('/upload-csv', file);
            showStatus(`✅ ${result.message}`, 'success');
            App.showToast(result.message, 'success');
            // Refresh rules list
            await load();
        } catch (err) {
            showStatus(`❌ ${err.message}`, 'error');
            App.showToast('Upload failed: ' + err.message, 'error');
        }
    }

    function showStatus(message, type) {
        const status = document.getElementById('upload-status');
        status.classList.remove('hidden', 'success', 'error', 'info');
        status.classList.add(type);
        status.textContent = message;
    }

    async function load() {
        const container = document.getElementById('rules-list');
        const countBadge = document.getElementById('rules-count');

        try {
            const data = await API.get('/rules');
            const rules = data.rules || [];
            countBadge.textContent = data.count || rules.length;

            if (rules.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <span class="empty-icon">📋</span>
                        <p>No rules imported yet</p>
                    </div>
                `;
                return rules;
            }

            container.innerHTML = rules.map((rule, i) => `
                <div class="rule-item" style="animation-delay: ${i * 0.04}s">
                    <span class="issue-type-badge ${rule.type}">${rule.type}</span>
                    <span class="rule-description">${escapeHtml(rule.description)}</span>
                </div>
            `).join('');

            return rules;
        } catch (err) {
            App.showToast('Failed to load rules: ' + err.message, 'error');
            return [];
        }
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }

    return { init, load };
})();
