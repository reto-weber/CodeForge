/**
 * Session Manager
 * Handles session and container management
 */

class SessionManager {
    constructor(domElements, uiUtils) {
        this.dom = domElements;
        this.ui = uiUtils;
        this.sessionInfo = null;
    }

    // Load session information from server
    async loadSessionInfo() {
        try {
            const response = await fetch('/session/info');
            const data = await response.json();

            if (data.error) {
                this.dom.sessionStatusEl.textContent = 'No active session';
                this.dom.containerStatusEl.textContent = 'No container information available';
                return;
            }

            this.sessionInfo = data;
            this.updateSessionDisplay();
        } catch (error) {
            console.error('Error loading session info:', error);
            this.dom.sessionStatusEl.textContent = 'Error loading session info';
        }
    }

    updateSessionDisplay() {
        if (!this.sessionInfo) return;

        const sessionAge = Math.round((Date.now() / 1000) - this.sessionInfo.session_created);
        const lastUsed = Math.round((Date.now() / 1000) - this.sessionInfo.session_last_used);

        this.dom.sessionStatusEl.innerHTML = `
            Session ID: ${this.sessionInfo.session_id.substring(0, 8)}...<br>
            Age: ${this.ui.formatDuration(sessionAge)}<br>
            Last used: ${this.ui.formatDuration(lastUsed)} ago
        `;

        if (this.sessionInfo.container) {
            const containerAge = Math.round(this.sessionInfo.container.age_seconds);
            this.dom.containerStatusEl.innerHTML = `
                Container Status: ${this.sessionInfo.container.status}<br>
                Container Age: ${this.ui.formatDuration(containerAge)}<br>
                Container ID: ${this.sessionInfo.container.container_id.substring(0, 12)}...
            `;
        } else {
            this.dom.containerStatusEl.textContent = 'No container active (will be created on first execution)';
        }
    }

    async cleanupSession() {
        if (!confirm('Are you sure you want to clean up the current session? This will stop any running containers.')) {
            return;
        }

        try {
            this.dom.cleanupSessionBtn.disabled = true;
            this.dom.cleanupSessionBtn.textContent = '🔄 Cleaning...';

            const formData = new FormData();
            const response = await fetch('/session/cleanup', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.dom.sessionStatusEl.textContent = 'Session cleaned up successfully';
                this.dom.containerStatusEl.textContent = 'No container active';
                this.sessionInfo = null;
                // Reload session info to get new session
                setTimeout(() => this.loadSessionInfo(), 1000);
            } else {
                alert('Failed to clean up session: ' + result.message);
            }
        } catch (error) {
            console.error('Error cleaning up session:', error);
            alert('Error cleaning up session: ' + error.message);
        } finally {
            this.dom.cleanupSessionBtn.disabled = false;
            this.dom.cleanupSessionBtn.textContent = '🗑️ Clean Session';
        }
    }

    // Start auto-refresh of session info
    startAutoRefresh(intervalMs = 30000) {
        // Initial load
        this.loadSessionInfo();

        // Refresh session info every intervalMs
        setInterval(() => this.loadSessionInfo(), intervalMs);
    }
}

// Export as global for backwards compatibility
window.SessionManager = SessionManager;
