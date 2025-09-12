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
                if (this.dom.sessionStatusEl) {
                    this.dom.sessionStatusEl.textContent = 'No active session';
                }
                if (this.dom.containerStatusEl) {
                    this.dom.containerStatusEl.textContent = 'No container information available';
                }
                return;
            }

            this.sessionInfo = data;
            this.updateSessionDisplay();
        } catch (error) {
            console.error('Error loading session info:', error);
            if (this.dom.sessionStatusEl) {
                this.dom.sessionStatusEl.textContent = 'Error loading session info';
            }
        }
    }

    updateSessionDisplay() {
        if (!this.sessionInfo) return;

        const sessionAge = Math.round((Date.now() / 1000) - this.sessionInfo.session_created);
        const lastUsed = Math.round((Date.now() / 1000) - this.sessionInfo.session_last_used);

        if (this.dom.sessionStatusEl) {
            this.dom.sessionStatusEl.innerHTML = `
                Session ID: ${this.sessionInfo.session_id.substring(0, 8)}...<br>
                Age: ${this.ui.formatDuration(sessionAge)}<br>
                Last used: ${this.ui.formatDuration(lastUsed)} ago
            `;
        }

        if (this.dom.containerStatusEl) {
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
        
        // Log session info to console for debugging when UI elements are not available
        if (!this.dom.sessionStatusEl && !this.dom.containerStatusEl) {
            console.log('Session Info:', {
                sessionId: this.sessionInfo.session_id.substring(0, 8) + '...',
                sessionAge: this.ui.formatDuration ? this.ui.formatDuration(sessionAge) : sessionAge + 's',
                lastUsed: this.ui.formatDuration ? this.ui.formatDuration(lastUsed) + ' ago' : lastUsed + 's ago',
                container: this.sessionInfo.container ? 'Active' : 'None'
            });
        }
    }

    async cleanupSession() {
        if (!confirm('Are you sure you want to clean up the current session? This will stop any running containers.')) {
            return;
        }

        try {
            if (this.dom.cleanupSessionBtn) {
                this.dom.cleanupSessionBtn.disabled = true;
                this.dom.cleanupSessionBtn.textContent = '🔄 Cleaning...';
            }

            const formData = new FormData();
            const response = await fetch('/session/cleanup', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                if (this.dom.sessionStatusEl) {
                    this.dom.sessionStatusEl.textContent = 'Session cleaned up successfully';
                }
                if (this.dom.containerStatusEl) {
                    this.dom.containerStatusEl.textContent = 'No container active';
                }
                this.sessionInfo = null;
                // Reload session info to get new session
                setTimeout(() => this.loadSessionInfo(), 1000);
                console.log('Session cleaned up successfully');
            } else {
                alert('Failed to clean up session: ' + result.message);
            }
        } catch (error) {
            console.error('Error cleaning up session:', error);
            alert('Error cleaning up session: ' + error.message);
        } finally {
            if (this.dom.cleanupSessionBtn) {
                this.dom.cleanupSessionBtn.disabled = false;
                this.dom.cleanupSessionBtn.textContent = '🗑️ Clean Session';
            }
        }
    }

    // Clean up session on language change
    async cleanupOnLanguageChange() {
        try {
            console.log('Cleaning up session containers for language change...');
            
            const response = await fetch('/session/cleanup', {
                method: 'POST',
                credentials: 'same-origin'
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log('Session containers cleaned up for language change');
                // Show brief notification to user
                if (this.ui && this.ui.updateStatus) {
                    this.ui.updateStatus('Session reset for language change', true, 2000);
                }
            } else {
                console.warn('Failed to clean up session containers:', result.message);
            }
        } catch (error) {
            console.error('Error cleaning up session on language change:', error);
        }
    }

    // Clean up session on page refresh
    async cleanupOnRefresh() {
        try {
            const response = await fetch('/session/cleanup', {
                method: 'POST',
                credentials: 'same-origin'
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log('Session containers cleaned up for page refresh');
            } else {
                console.warn('Failed to clean up session containers:', result.message);
            }
        } catch (error) {
            console.error('Error cleaning up session on refresh:', error);
        }
    }

    // Clean up session on page refresh using sendBeacon (more reliable)
    cleanupOnRefreshBeacon() {
        try {
            // Use sendBeacon for reliable cleanup when page is unloading
            const data = new FormData();
            navigator.sendBeacon('/session/cleanup', data);
            console.log('Session cleanup beacon sent for page refresh');
        } catch (error) {
            console.error('Error sending session cleanup beacon:', error);
        }
    }

    // Start auto-refresh of session info
    startAutoRefresh(intervalMs = 30000) {
        // Only start auto-refresh if we have UI elements to display info
        // Otherwise just do initial load for session setup
        this.loadSessionInfo();

        // Only set up interval if we have display elements
        if (this.dom.sessionStatusEl || this.dom.containerStatusEl) {
            setInterval(() => this.loadSessionInfo(), intervalMs);
            console.log('Session auto-refresh started');
        } else {
            console.log('Session management active (no UI elements for display)');
        }
    }
}

// Export as global for backwards compatibility
window.SessionManager = SessionManager;
