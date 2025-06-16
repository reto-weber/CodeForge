/**
 * UI Utilities
 * Handles status updates and other UI-related utilities
 */

class UIUtils {
    constructor(domElements) {
        this.dom = domElements;
    }

    // Update status display
    updateStatus(message, isSuccess) {
        this.dom.status.textContent = message;
        this.dom.status.className = 'status ' + (isSuccess ? 'success' : 'error');
    }

    // Update output display
    updateOutput(text, isHtml = false) {
        if (isHtml) {
            this.dom.output.innerHTML = text || '';
        } else {
            this.dom.output.textContent = text || '';
        }
    }

    // Show/hide cancel button and disable/enable other buttons
    setExecutionState(isRunning) {
        if (isRunning) {
            this.dom.cancelBtn.style.display = 'inline-block';
            this.dom.compileBtn.disabled = true;
            this.dom.runBtn.disabled = true;
            this.dom.verifyBtn.disabled = true;
        } else {
            this.dom.cancelBtn.style.display = 'none';
            this.dom.compileBtn.disabled = false;
            this.dom.runBtn.disabled = false;
            this.dom.verifyBtn.disabled = false;
        }
    }

    // Format duration in seconds to human readable format
    formatDuration(seconds) {
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
        return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
    }

    // Flash element to draw attention
    flashElement(element, color = '#ff6b6b', duration = 2000) {
        const originalBorder = element.style.border;
        element.style.border = `2px solid ${color}`;
        setTimeout(() => {
            element.style.border = originalBorder;
        }, duration);
    }

    // Show/hide verify button based on language
    updateVerifyButtonVisibility(language) {
        if (language === 'eiffel') {
            this.dom.verifyBtn.style.display = 'inline-block';
        } else {
            this.dom.verifyBtn.style.display = 'none';
        }
    }
}

// Export as global for backwards compatibility
window.UIUtils = UIUtils;
