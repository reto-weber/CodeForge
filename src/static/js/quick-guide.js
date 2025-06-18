/**
 * Quick Guide Manager
 * Manages the initial quick guide overlay for new users
 */

class QuickGuideManager {
    constructor() {
        this.overlay = null;
        this.closeBtn = null;
        this.gotItBtn = null;
        this.dontShowCheckbox = null;
        this.showGuideBtn = null;
        this.storageKey = 'codeforge-hide-quick-guide';

        this.initialize();
    }

    initialize() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupGuide());
        } else {
            this.setupGuide();
        }
    }

    setupGuide() {
        this.overlay = document.getElementById('quick-guide-overlay');
        this.closeBtn = document.getElementById('close-guide-btn');
        this.gotItBtn = document.getElementById('got-it-btn');
        this.dontShowCheckbox = document.getElementById('dont-show-guide-again');
        this.showGuideBtn = document.getElementById('show-guide-btn');

        if (!this.overlay) return;

        this.setupEventListeners();
        this.checkShouldShow();
    }

    setupEventListeners() {
        // Close button
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.hideGuide());
        }

        // Got it button
        if (this.gotItBtn) {
            this.gotItBtn.addEventListener('click', () => this.hideGuide());
        }

        // Show guide button in header
        if (this.showGuideBtn) {
            this.showGuideBtn.addEventListener('click', () => this.forceShow());
        }

        // Click outside to close
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.hideGuide();
            }
        });

        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible()) {
                this.hideGuide();
            }
        });
    }

    checkShouldShow() {
        // Check if user has chosen not to show the guide
        const shouldHide = localStorage.getItem(this.storageKey);

        if (!shouldHide) {
            // Show guide after a short delay to allow page to load
            setTimeout(() => this.showGuide(), 500);
        }
    }

    showGuide() {
        if (this.overlay) {
            this.overlay.classList.add('show');
            // Focus the overlay for accessibility
            this.overlay.focus();
        }
    }

    hideGuide() {
        if (this.overlay) {
            this.overlay.classList.remove('show');

            // Save preference if checkbox is checked
            if (this.dontShowCheckbox && this.dontShowCheckbox.checked) {
                localStorage.setItem(this.storageKey, 'true');
            }
        }
    }

    isVisible() {
        return this.overlay && this.overlay.classList.contains('show');
    }

    // Method to manually show guide (could be called from help menu)
    forceShow() {
        this.showGuide();
    }

    // Method to reset the "don't show again" preference
    resetPreference() {
        localStorage.removeItem(this.storageKey);
    }
}

// Initialize the quick guide manager
window.quickGuideManager = new QuickGuideManager();

// Export for global access
window.QuickGuideManager = QuickGuideManager;
