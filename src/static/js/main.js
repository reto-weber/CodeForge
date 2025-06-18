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
        this.codeExecution = new CodeExecutionManager(this.dom, this.codeEditor, this.ui, this.fileManager);
        this.configManager = new ConfigManager(this.dom, this.ui, this.examplesManager);
        this.libraryBrowser = new EiffelLibraryBrowser();

        // Make managers globally available for backwards compatibility
        window.codeExecution = this.codeExecution;
        window.examplesManager = this.examplesManager;
        window.fileManager = this.fileManager;
        window.libraryBrowser = this.libraryBrowser;

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
            this.updateLibraryBrowserVisibility(this.dom.language.value);
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

        // Output section close button
        if (this.dom.closeOutputBtn) {
            this.dom.closeOutputBtn.addEventListener('click', () => {
                this.ui.clearOutput();
            });
        }

        // Add keyboard shortcut to close output (Escape key)
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.dom.outputSection && this.dom.outputSection.style.display !== 'none') {
                this.ui.clearOutput();
            }
        });

        // Share Code URL button
        const shareUrlBtn = document.getElementById('share-url-btn');
        const shareUrlOutput = document.getElementById('share-url-output');
        if (shareUrlBtn && shareUrlOutput) {
            shareUrlBtn.addEventListener('click', () => {
                let lang = this.dom.language.value;
                let files = [];
                let activeFile = null;
                if (this.fileManager) {
                    files = this.fileManager.getAllFiles().map(f => ({ name: f.name, content: f.content }));
                    activeFile = this.fileManager.getActiveFile()?.name || (files[0] && files[0].name);
                } else {
                    files = [{ name: 'main.' + lang, content: this.codeEditor.getCodeContent() }];
                    activeFile = files[0].name;
                }
                let data = { lang, files, activeFile };
                let encoded = btoa(unescape(encodeURIComponent(JSON.stringify(data))));
                let baseUrl = window.location.origin + window.location.pathname;
                let params = new URLSearchParams();
                params.set('files', encoded);
                let shareUrl = `${baseUrl}?${params.toString()}`;
                shareUrlOutput.value = shareUrl;
                shareUrlOutput.style.display = 'block';
                shareUrlOutput.focus();
                shareUrlOutput.select();
            });
        }

        console.log('Event listeners set up');
    }

    updateLibraryBrowserVisibility(language) {
        if (this.libraryBrowser) {
            this.libraryBrowser.updateVisibility(language);
        }
    }

    async initialize() {
        console.log('Starting application initialization...');

        // Check for files/lang in URL params (for shareable links)
        const params = new URLSearchParams(window.location.search);
        let filesRestoredFromUrl = false;
        if (params.has('files')) {
            try {
                const data = JSON.parse(decodeURIComponent(escape(atob(params.get('files')))));
                if (data.lang && this.dom.language.value !== data.lang) {
                    this.dom.language.value = data.lang;
                    this.codeEditor.updateCodeMirrorMode();
                }
                if (data.files && Array.isArray(data.files) && this.fileManager) {
                    // Remove all current files
                    this.fileManager.files.clear();
                    document.getElementById('file-tabs').innerHTML = '';
                    // Add files from URL
                    let firstId = null;
                    data.files.forEach((f, idx) => {
                        const id = this.fileManager.createFile(f.name, f.content, null, false);
                        if (idx === 0) firstId = id;
                    });
                    // Set active file
                    let activeId = null;
                    for (let [id, file] of this.fileManager.files.entries()) {
                        if (file.name === data.activeFile) {
                            activeId = id;
                            break;
                        }
                    }
                    this.fileManager.switchToFile(activeId || firstId);
                    filesRestoredFromUrl = true;
                }
            } catch (e) {
                console.warn('Failed to decode shared files from URL:', e);
            }
        } else if (params.has('code')) {
            try {
                const code = decodeURIComponent(escape(atob(params.get('code'))));
                const lang = params.get('lang');
                if (lang && this.dom.language.value !== lang) {
                    this.dom.language.value = lang;
                    this.codeEditor.updateCodeMirrorMode();
                }
                this.codeEditor.setCodeContent(code);
                filesRestoredFromUrl = true;
            } catch (e) {
                console.warn('Failed to decode shared code from URL:', e);
            }
        }

        // Initialize examples and set default code only if no files restored from URL
        await this.examplesManager.loadAvailableExamples();
        if (!filesRestoredFromUrl && (!this.fileManager.files || this.fileManager.files.size === 0)) {
            await this.examplesManager.setExampleCode(this.dom.language.value);
        }

        // Set initial verify button visibility
        this.ui.updateVerifyButtonVisibility(this.dom.language.value);

        // Set initial library browser visibility
        this.updateLibraryBrowserVisibility(this.dom.language.value);

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
