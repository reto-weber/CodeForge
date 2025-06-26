/**
 * DOM Elements Manager
 * Handles DOM element references and validation
 */

class DOMElements {
    constructor() {
        this.initializeElements();
        this.validateCriticalElements();
    }

    initializeElements() {
        // Core editor elements
        this.codeEditor = document.getElementById('code-editor');
        this.languageSelect = document.getElementById('language');
        this.timeoutInput = document.getElementById('timeout');

        // File management
        this.fileTabsContainer = document.getElementById('file-tabs');
        this.addFileBtn = document.getElementById('add-file-btn');

        // Action buttons
        this.compileBtn = document.getElementById('compile-btn');
        this.runBtn = document.getElementById('run-btn');
        this.verifyBtn = document.getElementById('verify-btn');
        this.cancelBtn = document.getElementById('cancel-btn');

        // Status and output
        this.statusEl = document.getElementById('status');
        this.outputEl = document.getElementById('output');
        this.outputSection = document.getElementById('output-section');
        this.closeOutputBtn = document.getElementById('close-output-btn');
        this.containerStatusEl = document.getElementById('container-status');

        // Session management (optional elements)
        this.sessionStatusEl = document.getElementById('session-status');
        this.cleanupSessionBtn = document.getElementById('cleanup-session-btn');

        // Configuration (optional elements)
        this.showConfigBtn = document.getElementById('show-config-btn');
        this.configEditor = document.getElementById('config-editor');
        this.configTextarea = document.getElementById('config-textarea');
        this.saveConfigBtn = document.getElementById('save-config-btn');

        // Examples
        this.examplesSelect = document.getElementById('examples');
        this.loadExampleBtn = document.getElementById('load-example-btn');

        console.log('DOM Elements initialized');
        console.log('languageSelect:', this.languageSelect);
        console.log('examplesSelect:', this.examplesSelect);
        console.log('loadExampleBtn:', this.loadExampleBtn);

        // Log missing optional elements
        if (!this.showConfigBtn) console.warn('Optional element show-config-btn not found');
        if (!this.configEditor) console.warn('Optional element config-editor not found');
        if (!this.configTextarea) console.warn('Optional element config-textarea not found');
        if (!this.saveConfigBtn) console.warn('Optional element save-config-btn not found');
        if (!this.sessionStatusEl) console.warn('Optional element session-status not found');
        if (!this.cleanupSessionBtn) console.warn('Optional element cleanup-session-btn not found');
        if (!this.containerStatusEl) console.warn('Optional element container-status not found');
    }

    validateCriticalElements() {
        const criticalElements = [
            { element: this.languageSelect, name: 'languageSelect' },
            { element: this.examplesSelect, name: 'examplesSelect' },
            { element: this.loadExampleBtn, name: 'loadExampleBtn' }
        ];

        for (const { element, name } of criticalElements) {
            if (!element) {
                console.error(`${name} element not found!`);
                throw new Error(`Critical DOM element ${name} not found`);
            }
        }
    }

    // Getter methods for commonly used elements
    get editor() { return this.codeEditor; }
    get language() { return this.languageSelect; }
    get examples() { return this.examplesSelect; }
    get loadExample() { return this.loadExampleBtn; }
    get status() { return this.statusEl; }
    get output() { return this.outputEl; }
}

// Export as global for backwards compatibility
window.DOMElements = DOMElements;
