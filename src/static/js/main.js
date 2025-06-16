/**
 * Main Application
 * Initializes and coordinates all modules
 */

class CodeCompilerApp {
    constructor() {
        this.initializeModules();
        this.setupEventListeners();
        this.initialize();
    }

    initializeModules() {
        // Initialize core modules
        this.dom = new DOMElements();
        this.ui = new UIUtils(this.dom);
        this.codeEditor = new CodeEditorManager(this.dom);
        this.fileManager = new FileManager(this.dom, this.codeEditor);
        this.examplesManager = new ExamplesManager(this.dom, this.codeEditor, this.ui);
        this.sessionManager = new SessionManager(this.dom, this.ui);
        this.codeExecution = new CodeExecutionManager(this.dom, this.codeEditor, this.ui, this.fileManager);
        this.configManager = new ConfigManager(this.dom, this.ui, this.examplesManager);

        // Make managers globally available for backwards compatibility
        window.codeExecution = this.codeExecution;
        window.sessionManager = this.sessionManager;
        window.examplesManager = this.examplesManager;
        window.fileManager = this.fileManager;

        console.log('All modules initialized');
    }

    setupEventListeners() {
        // Compilation and execution buttons
        this.dom.compileBtn.addEventListener('click', () => {
            this.codeExecution.compileCode();
        });

        this.dom.runBtn.addEventListener('click', () => {
            // Run without compilation
            this.codeExecution.runCode(false);
        });

        this.dom.verifyBtn.addEventListener('click', () => {
            // Verify code (Eiffel only)
            this.codeExecution.verifyCode();
        });

        this.dom.cancelBtn.addEventListener('click', () => {
            this.codeExecution.cancelExecution();
        });

        // Language change handling
        this.dom.language.addEventListener('change', async () => {
            console.log('Language changed to:', this.dom.language.value);
            this.codeEditor.updateCodeMirrorMode();
            await this.examplesManager.setExampleCode(this.dom.language.value);
            this.examplesManager.updateExamplesDropdown();
            this.ui.updateVerifyButtonVisibility(this.dom.language.value);
            this.codeExecution.resetCompilation();
        });

        // Examples handling
        this.dom.loadExample.addEventListener('click', () => {
            console.log('Load example button clicked');
            this.examplesManager.loadExample();
        });

        this.dom.examples.addEventListener('change', () => {
            this.examplesManager.updateLoadExampleButton();
        });

        // Configuration handling (only if elements exist)
        if (this.dom.showConfigBtn) {
            this.dom.showConfigBtn.addEventListener('click', () => {
                this.configManager.toggleConfigEditor();
            });
        }

        if (this.dom.saveConfigBtn) {
            this.dom.saveConfigBtn.addEventListener('click', () => {
                this.configManager.saveConfig();
            });
        }

        // Session management
        this.dom.cleanupSessionBtn.addEventListener('click', () => {
            this.sessionManager.cleanupSession();
        });

        console.log('Event listeners set up');
    }

    async initialize() {
        console.log('Starting application initialization...');

        // Initialize examples and set default code
        await this.examplesManager.loadAvailableExamples();
        await this.examplesManager.setExampleCode(this.dom.language.value);

        // Set initial verify button visibility
        this.ui.updateVerifyButtonVisibility(this.dom.language.value);

        // Start session management
        this.sessionManager.startAutoRefresh();

        console.log('Application initialization complete');
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded');

    try {
        new CodeCompilerApp();
    } catch (error) {
        console.error('Failed to initialize application:', error);
        alert('Failed to initialize application. Please check the console for details.');
    }
});
