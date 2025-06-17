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
        this.dom.status.className = 'status-indicator ' + (isSuccess ? 'success' : 'error');
        this.dom.status.style.display = 'block';

        // Update output section visibility
        this.updateOutputSectionVisibility();
    }

    // Update output display
    updateOutput(text, isHtml = false) {
        if (isHtml) {
            this.dom.output.innerHTML = text || '';
        } else {
            this.dom.output.textContent = text || '';
        }

        // Update output section visibility based on current content and status
        this.updateOutputSectionVisibility();
    }

    // Update output section visibility based on current content and status
    updateOutputSectionVisibility() {
        const hasContent = this.dom.output && (
            (this.dom.output.textContent && this.dom.output.textContent.trim()) ||
            (this.dom.output.innerHTML && this.dom.output.innerHTML.trim())
        );
        const hasStatus = this.dom.status && this.dom.status.textContent && this.dom.status.textContent.trim();

        if (hasContent || hasStatus) {
            this.showOutputSection();
        } else {
            this.hideOutputSection();
        }
    }

    // Show the output section
    showOutputSection() {
        if (this.dom.outputSection) {
            this.dom.outputSection.style.display = 'block';
        }
    }

    // Hide the output section
    hideOutputSection() {
        if (this.dom.outputSection) {
            // Add a fade-out effect before hiding
            this.dom.outputSection.style.opacity = '0';
            this.dom.outputSection.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                this.dom.outputSection.style.display = 'none';
                // Reset for next show
                this.dom.outputSection.style.opacity = '';
                this.dom.outputSection.style.transform = '';
            }, 200);
        }
    }

    // Clear output and hide section
    clearOutput() {
        this.dom.output.textContent = '';
        this.dom.output.innerHTML = '';
        // Also clear status when closing output
        this.dom.status.style.display = 'none';
        this.dom.status.textContent = '';
        this.hideOutputSection();
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
