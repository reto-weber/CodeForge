/**
 * Examples Manager
 * Handles loading and managing code examples
 */

class ExamplesManager {
    constructor(domElements, codeEditor, uiUtils) {
        this.dom = domElements;
        this.codeEditor = codeEditor;
        this.ui = uiUtils;
        this.availableExamples = {};

        this.defaultExamples = {
            'python': 'hello_world.py',
            'c': 'hello_world.c',
            'cpp': 'hello_world.cpp',
            'java': 'HelloWorld.java',
            'eiffel': 'hello_world.e'
        };
    }

    // Load available examples from server
    async loadAvailableExamples() {
        try {
            const response = await fetch('/examples');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            this.availableExamples = data;

            this.updateExamplesDropdown();
        } catch (error) {
            console.error('Error loading examples:', error);
            console.error('Error stack:', error.stack);
        }
    }

    // Update examples dropdown based on selected language
    updateExamplesDropdown() {

        if (!this.dom.language) {
            console.error('languageSelect is null!');
            return;
        }

        const currentLanguage = this.dom.language.value;
        const examples = this.availableExamples[currentLanguage] || {};
        
        console.log(examples)
        if (!this.dom.examples) {
            console.error('examplesSelect is null!');
            return;
        }

        // Clear existing options
        this.dom.examples.innerHTML = '<option value="">Select an example...</option>';

        // Add examples for current language
        Object.keys(examples).forEach(filename => {
            const option = document.createElement('option');
            option.value = filename;
            option.textContent = `${filename}`;
            this.dom.examples.appendChild(option);
        });

        // Update button state
        this.updateLoadExampleButton();
    }

    // Update the Load Example button state based on selection
    updateLoadExampleButton() {
        if (!this.dom.loadExample || !this.dom.examples) return;

        const hasSelection = this.dom.examples.value !== '';
        this.dom.loadExample.disabled = !hasSelection;
        this.dom.loadExample.textContent = hasSelection ? 'Load Example' : 'Load Example';
    }

    // Load selected example
    async loadExample() {
        console.log('=== loadExample called ===');
        const selectedExample = this.dom.examples.value;
        const currentLanguage = this.dom.language.value;

        if (!selectedExample) {
            this.ui.updateStatus('Please select an example from the dropdown first', false);
            // Flash the dropdown to draw attention
            this.ui.flashElement(this.dom.examples);
            return;
        }

        try {
            this.ui.updateStatus('Loading example...', true);

            const response = await fetch(`/examples/${currentLanguage}/${selectedExample}`);
            const result = await response.json();

            if (response.ok) {
                // Navigate to the example URL
                if (result.url) {
                    window.location.href = result.url;
                } else {
                    this.ui.updateStatus('Error: No URL found for example', false);
                }
            } else {
                this.ui.updateStatus(`Error loading example: ${result.detail || result.error}`, false);
            }
        } catch (error) {
            console.error('Error loading example:', error);
            this.ui.updateStatus('Error loading example: ' + error.message, false);
        }
    }

    // Load default example code for the selected language
    async setExampleCode(language) {
        try {
            const defaultFile = this.defaultExamples[language];
            let code = '';
            let filename = '';

            if (defaultFile && this.availableExamples[language] && this.availableExamples[language][defaultFile]) {
                // Load the default example file
                const response = await fetch(`/examples/${language}/${defaultFile}`);
                const result = await response.json();

                if (response.ok) {
                    code = result.code;
                    filename = defaultFile;
                }
            }

            // Fallback to simple placeholder if no example available
            if (!code) {
                code = this.getPlaceholderCode(language);
                // Use default filename for the language
                const defaultNames = {
                    'python': 'main.py',
                    'c': 'main.c',
                    'cpp': 'main.cpp',
                    'java': 'Main.java',
                    'eiffel': 'main.e'
                };
                filename = defaultNames[language] || 'main.txt';
            }

            // If there's a file manager, work with existing files or create a new one
            if (window.fileManager) {
                if (window.fileManager.files.size === 0) {
                    // No files exist, create a new one
                    window.fileManager.createFile(filename, code, 'default', true);
                } else {
                    // Files exist, update the active file with the new content
                    const activeFile = window.fileManager.getActiveFile();
                    if (activeFile) {
                        // Update the file properties
                        activeFile.content = code;

                        // Update the tab name if it's still the default
                        if (activeFile.name.startsWith('main.') || activeFile.id === 'main') {
                            window.fileManager.renameFile(activeFile.id, filename);
                        }

                        // Update editor content
                        this.codeEditor.setCodeContent(code);
                    }
                }
            } else {
                // Fallback: just set the editor content
                this.codeEditor.setCodeContent(code);
            }
        } catch (error) {
            console.error('Error loading default example:', error);
            // Fallback to basic placeholder
            const fallbackCode = `// Enter your ${language} code here...`;
            const defaultNames = {
                'python': 'main.py',
                'c': 'main.c',
                'cpp': 'main.cpp',
                'java': 'Main.java',
                'eiffel': 'main.e'
            };
            const filename = defaultNames[language] || 'main.txt';

            if (window.fileManager) {
                if (window.fileManager.files.size === 0) {
                    window.fileManager.createFile(filename, fallbackCode, 'default', true);
                } else {
                    const activeFile = window.fileManager.getActiveFile();
                    if (activeFile) {
                        activeFile.content = fallbackCode;
                        this.codeEditor.setCodeContent(fallbackCode);
                    }
                }
            } else {
                this.codeEditor.setCodeContent(fallbackCode);
            }
        }
    }

    getPlaceholderCode(language) {
        switch (language) {
            case 'eiffel':
                return '-- Enter your Eiffel code here...\nclass\n\tHELLO_WORLD\n\ncreate\n\tmake\n\nfeature\n\tmake\n\t\t\t-- Print hello world message\n\t\tdo\n\t\t\tprint ("Hello, World!%N")\n\t\tend\n\nend';
            case 'python':
                return '# Enter your Python code here...\nprint("Hello, World!")';
            case 'c':
                return '// Enter your C code here...\n#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}';
            case 'cpp':
                return '// Enter your C++ code here...\n#include <iostream>\n\nint main() {\n    std::cout << "Hello, World!" << std::endl;\n    return 0;\n}';
            case 'java':
                return '// Enter your Java code here...\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}';
            default:
                return '// Enter your code here...';
        }
    }
}

// Export as global for backwards compatibility
window.ExamplesManager = ExamplesManager;
