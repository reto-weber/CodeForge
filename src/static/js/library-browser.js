/**
 * Eiffel Library Browser
 * Handles browsing Eiffel library classes using apb -short command
 */
class EiffelLibraryBrowser {
    constructor() {
        this.currentLanguage = null;
        this.libraryEditor = null; // CodeMirror instance for library output
        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        this.librarySection = document.getElementById('library-section');
        this.libraryClassInput = document.getElementById('library-class-input');
        this.fetchLibraryBtn = document.getElementById('fetch-library-btn');
        this.libraryStatus = document.getElementById('library-status');
        this.libraryOutput = document.getElementById('library-output');

        // Initialize CodeMirror for library output
        this.initializeLibraryEditor();
    }

    initializeLibraryEditor() {
        if (this.libraryOutput && typeof CodeMirror !== 'undefined') {
            // Replace the pre element with a CodeMirror editor
            this.libraryEditor = CodeMirror(this.libraryOutput.parentNode, {
                value: '',
                mode: 'text/x-eiffel', // Use correct MIME type for Eiffel syntax highlighting
                lineNumbers: true,
                readOnly: true,
                theme: 'default',
                lineWrapping: true, // Enable line wrapping for long lines
                scrollbarStyle: "native", // Use native scrollbars for compatibility
                viewportMargin: 50, // Reduced viewport margin for better performance
                matchBrackets: true, // Enable bracket matching
                styleActiveLine: false, // Disable active line styling for read-only editor
                extraKeys: {
                    "Ctrl-F": "find", // Enable Ctrl+F search
                    "Ctrl-G": "findNext",       // Find next occurrence
                    "Shift-Ctrl-G": "findPrev", // Find previous occurrence
                    "Alt-G": "jumpToLine",      // Jump to line
                    "Ctrl-H": "replace",        // Find and replace
                    "Esc": function (cm) {
                        // Close search dialog on Esc
                        if (cm.state.search && cm.state.search.overlay) {
                            CodeMirror.commands.clearSearch(cm);
                        }
                    }
                }
            });

            // Hide the original pre element
            this.libraryOutput.style.display = 'none';

            // Style the CodeMirror instance with adjustable height
            const cmWrapper = this.libraryEditor.getWrapperElement();
            cmWrapper.style.minHeight = '200px';
            cmWrapper.style.maxHeight = '600px';
            cmWrapper.style.height = '400px';
            cmWrapper.style.border = '1px solid #cbd5e0';
            cmWrapper.style.borderRadius = '8px';
            cmWrapper.style.fontSize = '14px';
            cmWrapper.style.fontFamily = '"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, "Courier New", monospace';
            cmWrapper.style.resize = 'vertical';
            cmWrapper.style.overflow = 'hidden';

            // Make the CodeMirror scrollable
            const cmScroll = cmWrapper.querySelector('.CodeMirror-scroll');
            if (cmScroll) {
                cmScroll.style.minHeight = '200px';
                cmScroll.style.maxHeight = '600px';
            }

            // Add resize observer to refresh CodeMirror when container is resized
            if (window.ResizeObserver) {
                const resizeObserver = new ResizeObserver(() => {
                    if (this.libraryEditor) {
                        setTimeout(() => {
                            this.libraryEditor.refresh();
                        }, 10);
                    }
                });
                resizeObserver.observe(cmWrapper);
            }

            // Add click handler to ensure the editor can receive focus and keyboard events
            cmWrapper.addEventListener('click', () => {
                if (this.libraryEditor) {
                    this.libraryEditor.focus();
                }
            });

            // Ensure the editor is focusable
            cmWrapper.setAttribute('tabindex', '0');
        }
    }

    bindEvents() {
        if (this.fetchLibraryBtn) {
            this.fetchLibraryBtn.addEventListener('click', () => this.fetchLibraryClass());
        }

        if (this.libraryClassInput) {
            this.libraryClassInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.fetchLibraryClass();
                }
            });
        }

        // Quick access buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('quick-class-btn')) {
                const className = e.target.getAttribute('data-class');
                if (className && this.libraryClassInput) {
                    this.libraryClassInput.value = className;
                    this.fetchLibraryClass();
                }
            }
        });
    }

    /**
     * Show or hide the library browser based on the selected language
     */
    updateVisibility(language) {
        this.currentLanguage = language;
        if (this.librarySection) {
            if (language === 'eiffel') {
                this.librarySection.style.display = 'block';
            } else {
                this.librarySection.style.display = 'none';
            }
        }
    }

    /**
     * Fetch and display an Eiffel library class
     */
    async fetchLibraryClass() {
        const className = this.libraryClassInput.value.trim();

        if (!className) {
            this.showStatus('Please enter a class name', 'error');
            return;
        }

        if (this.currentLanguage !== 'eiffel') {
            this.showStatus('Library browsing is only available for Eiffel', 'error');
            return;
        }

        try {
            this.showStatus('Fetching library class...', 'loading');
            this.libraryOutput.textContent = '';

            const response = await fetch(`/eiffel/library/${encodeURIComponent(className)}`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showStatus(`Class ${className} fetched successfully`, 'success');
                // Use CodeMirror editor if available, otherwise fallback to textContent
                if (this.libraryEditor) {
                    this.libraryEditor.setValue(result.source_code);
                    // Refresh after a short delay to ensure proper rendering
                    setTimeout(() => {
                        this.libraryEditor.refresh();
                        // Focus the editor to enable keyboard shortcuts
                        this.libraryEditor.focus();
                    }, 50);
                } else {
                    this.libraryOutput.textContent = result.source_code;
                }
            } else {
                this.showStatus(result.message, 'error');
                if (this.libraryEditor) {
                    this.libraryEditor.setValue('');
                } else {
                    this.libraryOutput.textContent = '';
                }
            }

        } catch (error) {
            console.error('Error fetching library class:', error);
            this.showStatus(`Error fetching class: ${error.message}`, 'error');
            if (this.libraryEditor) {
                this.libraryEditor.setValue('');
            } else {
                this.libraryOutput.textContent = '';
            }
        }
    }

    /**
     * Show status message
     */
    showStatus(message, type) {
        if (!this.libraryStatus) return;

        this.libraryStatus.textContent = message;
        this.libraryStatus.className = `status-indicator ${type}`;
        this.libraryStatus.style.display = 'block';

        // Hide status after 5 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                this.libraryStatus.style.display = 'none';
            }, 5000);
        }
    }

    /**
     * Clear the library output
     */
    clearOutput() {
        if (this.libraryEditor) {
            this.libraryEditor.setValue('');
        } else if (this.libraryOutput) {
            this.libraryOutput.textContent = '';
        }
        if (this.libraryStatus) {
            this.libraryStatus.style.display = 'none';
        }
    }

    /**
     * Set focus to the class input field
     */
    focusInput() {
        if (this.libraryClassInput) {
            this.libraryClassInput.focus();
        }
    }

    /**
     * Set focus to the library editor for keyboard shortcuts
     */
    focusLibraryEditor() {
        if (this.libraryEditor) {
            this.libraryEditor.focus();
        }
    }

    /**
     * Get popular Eiffel library classes for quick access
     */
    getPopularClasses() {
        return [
            'ANY',
            'SIMPLE_ARRAY',
            'INTEGER',
            'MML_SET'
        ];
    }

    /**
     * Add quick access buttons for popular classes
     */
    addQuickAccessButtons() {
        const searchGroup = document.querySelector('.search-input-group');
        if (!searchGroup) return;

        const quickAccessDiv = document.createElement('div');
        quickAccessDiv.className = 'quick-access-buttons';
        quickAccessDiv.innerHTML = `
            <p style="font-size: 0.875rem; color: #6b7280; margin: 0.5rem 0;">Quick access:</p>
            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                ${this.getPopularClasses().map(className =>
            `<button class="btn btn-outline quick-class-btn" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;" data-class="${className}">${className}</button>`
        ).join('')}
            </div>
        `;

        searchGroup.parentNode.insertBefore(quickAccessDiv, searchGroup.nextSibling);

        // Add event listeners to quick access buttons
        quickAccessDiv.addEventListener('click', (e) => {
            if (e.target.classList.contains('quick-class-btn')) {
                const className = e.target.dataset.class;
                this.libraryClassInput.value = className;
                this.fetchLibraryClass();
            }
        });
    }
}

// Export for use in main.js
window.EiffelLibraryBrowser = EiffelLibraryBrowser;
