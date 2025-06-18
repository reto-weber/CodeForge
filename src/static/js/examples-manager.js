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
            console.log('=== loadAvailableExamples called ===');
            console.log('Fetching /examples...');
            const response = await fetch('/examples');
            console.log('Response status:', response.status);
            console.log('Response ok:', response.ok);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Raw response data:', data);

            this.availableExamples = data;
            console.log('Available examples stored:', this.availableExamples);
            console.log('Available languages:', Object.keys(this.availableExamples));

            console.log('Calling updateExamplesDropdown...');
            this.updateExamplesDropdown();
            console.log('=== loadAvailableExamples complete ===');
        } catch (error) {
            console.error('Error loading examples:', error);
            console.error('Error stack:', error.stack);
        }
    }

    // Update examples dropdown based on selected language
    updateExamplesDropdown() {
        console.log('=== updateExamplesDropdown called ===');
        console.log('availableExamples object:', this.availableExamples);
        console.log('languageSelect:', this.dom.language);
        console.log('languageSelect.value:', this.dom.language ? this.dom.language.value : 'null');

        if (!this.dom.language) {
            console.error('languageSelect is null!');
            return;
        }

        const currentLanguage = this.dom.language.value;
        console.log('Current language:', currentLanguage);
        const examples = this.availableExamples[currentLanguage] || {};
        console.log('Examples for language:', examples);
        console.log('Object.keys(examples):', Object.keys(examples));

        if (!this.dom.examples) {
            console.error('examplesSelect is null!');
            return;
        }

        // Clear existing options
        this.dom.examples.innerHTML = '<option value="">Select an example...</option>';
        console.log('Cleared dropdown, current innerHTML:', this.dom.examples.innerHTML);

        // Add examples for current language
        Object.keys(examples).forEach(filename => {
            const example = examples[filename];
            const option = document.createElement('option');
            option.value = filename;
            option.textContent = `${example.title} - ${example.description}`;
            this.dom.examples.appendChild(option);
            console.log('Added option:', filename, example.title);
        });

        console.log('Final dropdown innerHTML:', this.dom.examples.innerHTML);
        console.log('=== updateExamplesDropdown complete ===');

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
                // If there's a file manager and we have files, update the active file
                if (window.fileManager && window.fileManager.files.size > 0) {
                    const activeFile = window.fileManager.getActiveFile();
                    if (activeFile) {
                        // Update the active file's content and name
                        activeFile.content = result.code;
                        activeFile.name = selectedExample;
                        activeFile.extension = window.fileManager.getFileExtension(selectedExample);
                        activeFile.language = window.fileManager.getLanguageFromExtension(activeFile.extension);

                        // Update tab display
                        const tabElement = document.querySelector(`[data-file-id="${activeFile.id}"]`);
                        if (tabElement) {
                            const tabName = tabElement.querySelector('.tab-name');
                            if (tabName) {
                                tabName.textContent = selectedExample;
                            }
                        }

                        // Update editor content
                        this.codeEditor.setCodeContent(result.code);
                    }
                } else if (window.fileManager && window.fileManager.files.size === 0) {
                    // No files exist, create a new one
                    window.fileManager.createFile(selectedExample, result.code, null, true);
                } else {
                    // Fallback: just set the editor content
                    this.codeEditor.setCodeContent(result.code);
                }

                this.ui.updateStatus(`Loaded example: ${selectedExample}`, true);

                // Reset compilation paths when loading new code
                if (window.codeExecution) {
                    window.codeExecution.resetCompilation();
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
            case 'python':
                return '# Enter your Python code here...\nprint("Hello, World!")';
            case 'c':
                return '// Enter your C code here...\n#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}';
            case 'cpp':
                return '// Enter your C++ code here...\n#include <iostream>\n\nint main() {\n    std::cout << "Hello, World!" << std::endl;\n    return 0;\n}';
            case 'java':
                return '// Enter your Java code here...\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}';
            case 'eiffel':
                return '-- Enter your Eiffel code here...\nclass\n\tHELLO_WORLD\n\ncreate\n\tmake\n\nfeature\n\tmake\n\t\t\t-- Print hello world message\n\t\tdo\n\t\t\tprint ("Hello, World!%N")\n\t\tend\n\nend';
            default:
                return '// Enter your code here...';
        }
    }
}

// Export as global for backwards compatibility
window.ExamplesManager = ExamplesManager;
