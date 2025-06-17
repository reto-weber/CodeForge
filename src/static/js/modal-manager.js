/**
 * Modal Manager
 * Provides styled modal dialogs to replace browser alerts, prompts, and confirms
 */

class ModalManager {
    constructor() {
        this.overlay = null;
        this.currentModal = null;
        this.activePromise = null;

        this.initialize();
    }

    initialize() {
        this.overlay = document.getElementById('modal-overlay');
        if (!this.overlay) {
            console.error('Modal overlay not found in DOM');
            return;
        }

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Close modal when clicking overlay
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.cancelModal();
            }
        });

        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isModalOpen()) {
                this.cancelModal();
            }
        });

        // Close buttons
        this.overlay.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-close') || e.target.closest('.modal-close')) {
                this.cancelModal();
            }
        });
    }

    isModalOpen() {
        return this.overlay && this.overlay.style.display !== 'none';
    }

    showModal(modalId) {
        if (!this.overlay) return;

        // Hide all modals first
        const allModals = this.overlay.querySelectorAll('.modal');
        allModals.forEach(modal => {
            modal.style.display = 'none';
        });

        // Show the requested modal
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'block';
            this.currentModal = modal;
            this.overlay.style.display = 'flex';

            // Focus the first input if it exists
            const firstInput = modal.querySelector('input');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }
        }
    }

    closeModal() {
        if (!this.overlay) return;

        this.overlay.style.display = 'none';
        this.currentModal = null;

        // Only reject if there's an active promise and no explicit resolution
        // This will be handled by the specific handlers
    }

    cancelModal() {
        if (!this.overlay) return;

        this.overlay.style.display = 'none';
        this.currentModal = null;

        // Reject any pending promise
        if (this.activePromise) {
            this.activePromise.reject(new Error('Modal cancelled'));
            this.activePromise = null;
        }
    }

    /**
     * Show an alert dialog
     * @param {string} message - The message to display
     * @param {string} title - Optional title (default: "Alert")
     * @returns {Promise<void>}
     */
    alert(message, title = 'Alert') {
        return new Promise((resolve, reject) => {
            this.activePromise = { resolve, reject };

            // Set content
            const titleElement = document.getElementById('alert-modal-title');
            const messageElement = document.getElementById('alert-modal-message');

            if (titleElement) titleElement.textContent = title;
            if (messageElement) messageElement.textContent = message;

            // Setup OK button
            const okButton = document.getElementById('alert-ok');
            if (okButton) {
                const handleOk = () => {
                    okButton.removeEventListener('click', handleOk);
                    this.activePromise = null;
                    this.closeModal();
                    resolve();
                };
                okButton.addEventListener('click', handleOk);
            }

            this.showModal('alert-modal');
        });
    }

    /**
     * Show a confirmation dialog
     * @param {string} message - The message to display
     * @param {string} title - Optional title (default: "Confirm")
     * @returns {Promise<boolean>} - true if confirmed, false if cancelled
     */
    confirm(message, title = 'Confirm') {
        return new Promise((resolve, reject) => {
            this.activePromise = { resolve, reject };

            // Set content
            const titleElement = document.getElementById('confirm-modal-title');
            const messageElement = document.getElementById('confirm-modal-message');

            if (titleElement) titleElement.textContent = title;
            if (messageElement) messageElement.textContent = message;

            // Setup buttons
            const yesButton = document.getElementById('confirm-yes');
            const cancelButton = document.getElementById('confirm-cancel');

            const handleYes = () => {
                cleanup();
                this.activePromise = null;
                this.closeModal();
                resolve(true);
            };

            const handleCancel = () => {
                cleanup();
                this.activePromise = null;
                this.closeModal();
                resolve(false);
            };

            const cleanup = () => {
                if (yesButton) yesButton.removeEventListener('click', handleYes);
                if (cancelButton) cancelButton.removeEventListener('click', handleCancel);
            };

            if (yesButton) yesButton.addEventListener('click', handleYes);
            if (cancelButton) cancelButton.addEventListener('click', handleCancel);

            this.showModal('confirm-modal');
        });
    }

    /**
     * Show a prompt dialog for text input
     * @param {string} message - The message to display
     * @param {string} defaultValue - Default input value
     * @param {string} title - Optional title (default: "Input Required")
     * @param {object} options - Additional options (placeholder, validator, etc.)
     * @returns {Promise<string|null>} - The entered text or null if cancelled
     */
    prompt(message, defaultValue = '', title = 'Input Required', options = {}) {
        return new Promise((resolve, reject) => {
            this.activePromise = { resolve, reject };

            // Set content
            const titleElement = document.getElementById('filename-modal-title');
            const input = document.getElementById('filename-input');
            const hint = document.getElementById('filename-hint');

            if (titleElement) titleElement.textContent = title;
            if (input) {
                input.value = defaultValue;
                input.placeholder = options.placeholder || '';
            }
            if (hint) {
                hint.textContent = message;
                hint.className = 'input-hint';
            }

            // Setup buttons
            const confirmButton = document.getElementById('filename-confirm');
            const cancelButton = document.getElementById('filename-cancel');

            const validateInput = () => {
                if (!input) return true;

                const value = input.value.trim();
                if (!value) {
                    if (hint) {
                        hint.textContent = 'This field cannot be empty';
                        hint.className = 'input-hint error';
                    }
                    return false;
                }

                if (options.validator && typeof options.validator === 'function') {
                    const validationResult = options.validator(value);
                    if (validationResult !== true) {
                        if (hint) {
                            hint.textContent = validationResult || 'Invalid input';
                            hint.className = 'input-hint error';
                        }
                        return false;
                    }
                }

                if (hint) {
                    hint.textContent = message;
                    hint.className = 'input-hint';
                }
                return true;
            };

            const handleConfirm = () => {
                if (validateInput()) {
                    const value = input ? input.value.trim() : '';
                    cleanup();
                    this.activePromise = null;
                    this.closeModal();
                    resolve(value);
                }
            };

            const handleCancel = () => {
                cleanup();
                this.activePromise = null;
                this.closeModal();
                resolve(null);
            };

            const handleKeyDown = (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    handleConfirm();
                }
            };

            const cleanup = () => {
                if (confirmButton) confirmButton.removeEventListener('click', handleConfirm);
                if (cancelButton) cancelButton.removeEventListener('click', handleCancel);
                if (input) input.removeEventListener('keydown', handleKeyDown);
            };

            if (confirmButton) confirmButton.addEventListener('click', handleConfirm);
            if (cancelButton) cancelButton.addEventListener('click', handleCancel);
            if (input) {
                input.addEventListener('keydown', handleKeyDown);
                input.addEventListener('input', validateInput);
            }

            this.showModal('filename-modal');
        });
    }

    /**
     * Enhanced prompt specifically for filenames
     * @param {string} defaultFilename - Default filename
     * @param {Array<string>} existingFilenames - List of existing filenames to check against
     * @param {string} language - Current language for extension suggestion
     * @returns {Promise<string|null>}
     */
    promptFilename(defaultFilename = '', existingFilenames = [], language = 'python') {
        const validator = (filename) => {
            // Check for empty filename
            if (!filename.trim()) {
                return 'Filename cannot be empty';
            }

            // Check for invalid characters
            const invalidChars = /[<>:"/\\|?*]/;
            if (invalidChars.test(filename)) {
                return 'Filename contains invalid characters';
            }

            // Check for duplicate
            if (existingFilenames.includes(filename)) {
                return 'A file with this name already exists';
            }

            return true;
        };

        const getLanguageExtension = (lang) => {
            const extensions = {
                'python': 'py',
                'c': 'c',
                'cpp': 'cpp',
                'java': 'java',
                'javascript': 'js',
                'eiffel': 'e'
            };
            return extensions[lang] || 'txt';
        };

        // Generate default filename if not provided
        if (!defaultFilename) {
            const extension = getLanguageExtension(language);
            let baseName = 'new_file';
            let counter = 1;
            let suggestedName = `${baseName}.${extension}`;

            while (existingFilenames.includes(suggestedName)) {
                suggestedName = `${baseName}${counter}.${extension}`;
                counter++;
            }
            defaultFilename = suggestedName;
        }

        return this.prompt(
            'Enter a valid filename with extension',
            defaultFilename,
            'Add New File',
            {
                placeholder: `main.${getLanguageExtension(language)}`,
                validator
            }
        );
    }

    /**
     * Enhanced prompt for renaming files
     * @param {string} currentFilename - Current filename
     * @param {Array<string>} existingFilenames - List of existing filenames (excluding current)
     * @returns {Promise<string|null>}
     */
    promptRename(currentFilename, existingFilenames = []) {
        const validator = (filename) => {
            // Check for empty filename
            if (!filename.trim()) {
                return 'Filename cannot be empty';
            }

            // Check for invalid characters
            const invalidChars = /[<>:"/\\|?*]/;
            if (invalidChars.test(filename)) {
                return 'Filename contains invalid characters';
            }

            // Check for duplicate (excluding current filename)
            if (filename !== currentFilename && existingFilenames.includes(filename)) {
                return 'A file with this name already exists';
            }

            return true;
        };

        return this.prompt(
            'Enter the new filename',
            currentFilename,
            'Rename File',
            {
                placeholder: currentFilename,
                validator
            }
        );
    }
}

// Create global instance
window.modalManager = new ModalManager();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModalManager;
}
