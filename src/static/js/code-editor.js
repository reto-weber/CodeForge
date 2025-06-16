/**
 * Code Editor Manager
 * Handles CodeMirror initialization and management
 */

class CodeEditorManager {
    constructor(domElements) {
        this.dom = domElements;
        this.codeEditorCM = null;
        this.languageModes = {
            'python': 'python',
            'c': 'text/x-csrc',
            'cpp': 'text/x-c++src',
            'java': 'text/x-java',
            'javascript': 'javascript',
            'eiffel': 'text/x-eiffel'
        };

        this.initialize();
    }

    initialize() {
        if (typeof CodeMirror !== 'undefined') {
            this.initializeCodeMirror();
        } else {
            console.warn('CodeMirror not available, falling back to textarea');
        }
    }

    initializeCodeMirror() {
        const currentLanguage = this.dom.language.value;
        const mode = this.languageModes[currentLanguage] || 'text/plain';

        if (this.codeEditorCM) {
            this.codeEditorCM.toTextArea();
        }

        this.codeEditorCM = CodeMirror.fromTextArea(this.dom.editor, {
            mode: mode,
            theme: 'default',
            lineNumbers: true,
            matchBrackets: true,
            autoCloseBrackets: true,
            styleActiveLine: true,
            indentUnit: 4,
            tabSize: 4,
            indentWithTabs: false,
            extraKeys: {
                "Ctrl-Space": "autocomplete",
                "Tab": function (cm) {
                    if (cm.somethingSelected()) {
                        cm.indentSelection("add");
                    } else {
                        cm.replaceSelection("    ", "end");
                    }
                }
            },
            placeholder: "Enter your code here...",
            viewportMargin: Infinity
        });

        // Update textarea when CodeMirror content changes
        this.codeEditorCM.on('change', function (instance) {
            instance.save();
        });

        // Setup resize handling for CodeMirror
        this.setupEditorResize();

        console.log('CodeMirror initialized with mode:', mode);
    }

    setupEditorResize() {
        const editorContainer = document.getElementById('editor-container');

        if (!editorContainer || !this.codeEditorCM) {
            return;
        }

        // Create a ResizeObserver to watch for container size changes
        if (window.ResizeObserver) {
            const resizeObserver = new ResizeObserver(entries => {
                for (let entry of entries) {
                    if (entry.target === editorContainer) {
                        // Refresh CodeMirror when container is resized
                        setTimeout(() => {
                            if (this.codeEditorCM) {
                                this.codeEditorCM.refresh();
                            }
                        }, 10);
                    }
                }
            });

            resizeObserver.observe(editorContainer);
        }

        // Also handle manual refresh on window resize
        window.addEventListener('resize', () => {
            if (this.codeEditorCM) {
                setTimeout(() => {
                    this.codeEditorCM.refresh();
                }, 100);
            }
        });
    }

    // Get code content (works with both textarea and CodeMirror)
    getCodeContent() {
        if (this.codeEditorCM) {
            return this.codeEditorCM.getValue();
        }
        return this.dom.editor.value;
    }

    // Set code content (works with both textarea and CodeMirror)
    setCodeContent(content) {
        if (this.codeEditorCM) {
            this.codeEditorCM.setValue(content);
        } else {
            this.dom.editor.value = content;
        }
    }

    // Update CodeMirror mode when language changes
    updateCodeMirrorMode() {
        if (this.codeEditorCM) {
            const currentLanguage = this.dom.language.value;
            const mode = this.languageModes[currentLanguage] || 'text/plain';
            this.codeEditorCM.setOption('mode', mode);
            console.log('CodeMirror mode updated to:', mode);
        }
    }
}

// Export as global for backwards compatibility
window.CodeEditorManager = CodeEditorManager;
