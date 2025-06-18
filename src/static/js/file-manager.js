/**
 * File Manager
 * Handles multiple file tabs and file management
 */

class FileManager {
    constructor(domElements, codeEditorManager) {
        this.dom = domElements;
        this.codeEditor = codeEditorManager;
        this.files = new Map();
        this.activeFileId = null;
        this.fileCounter = 1;

        this.initialize();
    }

    initialize() {
        // Set up event listeners first
        this.setupEventListeners();

        // Delay file creation to ensure language dropdown is properly initialized
        setTimeout(() => {
            this.initializeFirstFile();
        }, 100);

        // Listen for language changes to suggest filename updates
        this.dom.language.addEventListener('change', () => this.onLanguageChange());
    }

    initializeFirstFile() {
        // Get the default language from data attribute (most reliable)
        let currentLanguage = 'python'; // fallback

        if (this.dom.language) {
            // First try the data attribute
            const defaultLang = this.dom.language.dataset.defaultLanguage;
            if (defaultLang) {
                currentLanguage = defaultLang;
            }
            // Then try the current value
            else if (this.dom.language.value) {
                currentLanguage = this.dom.language.value;
            }
            // Finally check selected option
            else {
                const selectedOption = this.dom.language.querySelector('option[selected]');
                if (selectedOption) {
                    currentLanguage = selectedOption.value;
                }
            }
        }

        const defaultFilename = this.getDefaultFilename(currentLanguage);

        // Ensure the dropdown is set to the correct language
        if (this.dom.language.value !== currentLanguage) {
            this.dom.language.value = currentLanguage;
        }

        // Create the initial file only if no files exist yet
        // This will be populated with content later by the examples manager
        if (this.files.size === 0) {
            this.createFile(defaultFilename, '', 'main', true);
        }
    }

    setupEventListeners() {
        // Add file button
        const addFileBtn = document.getElementById('add-file-btn');
        if (addFileBtn) {
            addFileBtn.addEventListener('click', async () => { await this.addNewFile(); });
        }

        // File tabs container for event delegation
        const fileTabsContainer = document.getElementById('file-tabs');
        if (fileTabsContainer) {
            fileTabsContainer.addEventListener('click', (e) => this.handleTabClick(e));
            fileTabsContainer.addEventListener('dblclick', (e) => this.handleTabClick(e));
            fileTabsContainer.addEventListener('contextmenu', (e) => this.handleTabRightClick(e));
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', async (e) => {
            // Ctrl+N or Cmd+N: New file
            if ((e.ctrlKey || e.metaKey) && e.key === 'n' && !e.shiftKey) {
                e.preventDefault();
                await this.addNewFile();
            }
            // Ctrl+W or Cmd+W: Close current file
            else if ((e.ctrlKey || e.metaKey) && e.key === 'w') {
                e.preventDefault();
                if (this.activeFileId) {
                    this.closeFile(this.activeFileId);
                }
            }
        });
    }

    createFile(filename, content = '', fileId = null, setActive = false) {
        if (!fileId) {
            fileId = `file_${this.fileCounter++}`;
        }

        // Determine file extension for language detection
        const extension = this.getFileExtension(filename);
        const language = this.getLanguageFromExtension(extension);

        const file = {
            id: fileId,
            name: filename,
            content: content,
            extension: extension,
            language: language
        };

        this.files.set(fileId, file);
        this.createTabElement(file);

        if (setActive || this.files.size === 1) {
            this.switchToFile(fileId);
        }

        return fileId;
    }

    createTabElement(file) {
        const fileTabsContainer = document.getElementById('file-tabs');
        if (!fileTabsContainer) return;

        const tabElement = document.createElement('div');
        tabElement.className = 'file-tab';
        tabElement.dataset.fileId = file.id;

        tabElement.innerHTML = `
            <span class="tab-name" title="Double-click to rename">${file.name}</span>
            <button class="tab-close" title="Close file">&times;</button>
        `;

        fileTabsContainer.appendChild(tabElement);
    }

    handleTabClick(e) {
        const tabElement = e.target.closest('.file-tab');
        if (!tabElement) return;

        const fileId = tabElement.dataset.fileId;

        if (e.target.classList.contains('tab-close')) {
            // Close tab
            e.stopPropagation();
            this.closeFile(fileId);
        } else if (e.target.classList.contains('tab-name') && e.type === 'dblclick') {
            // Rename file on double-click
            e.stopPropagation();
            this.renameFilePrompt(fileId);
        } else {
            // Switch to tab
            this.switchToFile(fileId);
        }
    }

    switchToFile(fileId) {
        if (!this.files.has(fileId)) return;

        // Save current file content before switching
        if (this.activeFileId && this.files.has(this.activeFileId)) {
            const currentContent = this.codeEditor.getCodeContent();
            this.files.get(this.activeFileId).content = currentContent;
        }

        // Update active file
        this.activeFileId = fileId;
        const file = this.files.get(fileId);

        // Update editor content
        this.codeEditor.setCodeContent(file.content);

        // Update language if it differs from current
        if (this.dom.language.value !== file.language) {
            this.dom.language.value = file.language;
            this.codeEditor.updateCodeMirrorMode();
        }

        // Update active tab visual state
        this.updateActiveTabVisual(fileId);
    }

    updateActiveTabVisual(activeFileId) {
        const allTabs = document.querySelectorAll('.file-tab');
        allTabs.forEach(tab => {
            tab.classList.remove('active');
            if (tab.dataset.fileId === activeFileId) {
                tab.classList.add('active');
            }
        });
    }

    closeFile(fileId) {
        if (this.files.size <= 1) {
            // Don't allow closing the last file
            if (window.modalManager) {
                window.modalManager.alert('Cannot close the last file. At least one file must remain open.');
            } else {
                alert('Cannot close the last file. At least one file must remain open.');
            }
            return;
        }

        // Remove from files map
        this.files.delete(fileId);

        // Remove tab element
        const tabElement = document.querySelector(`[data-file-id="${fileId}"]`);
        if (tabElement) {
            tabElement.remove();
        }

        // If closing active file, switch to another file
        if (this.activeFileId === fileId) {
            const remainingFileIds = Array.from(this.files.keys());
            if (remainingFileIds.length > 0) {
                this.switchToFile(remainingFileIds[0]);
            }
        }
    }

    async addNewFile() {
        if (window.modalManager) {
            const existingFiles = Array.from(this.files.values()).map(f => f.name);
            const currentLanguage = this.dom.language.value || 'python';
            const filename = await window.modalManager.promptFilename('', existingFiles, currentLanguage);
            if (filename) {
                const fileId = this.createFile(filename, '', null, true);
                return fileId;
            }
        } else {
            // fallback
            const filename = this.promptForFilename();
            if (filename) {
                const fileId = this.createFile(filename, '', null, true);
                return fileId;
            }
        }
    }

    async promptForFilename() {
        if (window.modalManager) {
            const existingFiles = Array.from(this.files.values()).map(f => f.name);
            const currentLanguage = this.dom.language.value || 'python';
            return await window.modalManager.promptFilename('', existingFiles, currentLanguage);
        }
        // fallback to old prompt
        const currentLanguage = this.dom.language.value || 'python';
        const extension = this.getLanguageExtension(currentLanguage);
        let baseName = 'new_file';
        let counter = 1;
        let suggestedName = `${baseName}.${extension}`;
        const existingFiles = Array.from(this.files.values());
        while (existingFiles.some(file => file.name === suggestedName)) {
            suggestedName = `${baseName}${counter}.${extension}`;
            counter++;
        }
        let filename = prompt('Enter filename:', suggestedName);
        if (!filename) return null;
        filename = filename.trim();
        if (!filename) {
            alert('Filename cannot be empty.');
            return this.promptForFilename();
        }
        if (existingFiles.some(file => file.name === filename)) {
            alert('A file with this name already exists.');
            return this.promptForFilename();
        }
        return filename;
    }

    getDefaultFilename(language) {
        const defaultNames = {
            'python': 'main.py',
            'c': 'main.c',
            'cpp': 'main.cpp',
            'java': 'Main.java',
            'javascript': 'main.js',
            'eiffel': 'main.e'
        };

        return defaultNames[language] || 'main.txt';
    }

    onLanguageChange() {
        const newLanguage = this.dom.language.value;

        // Update the language for the active file
        if (this.activeFileId && this.files.has(this.activeFileId)) {
            const activeFile = this.files.get(this.activeFileId);
            const currentExtension = this.getFileExtension(activeFile.name);
            const expectedExtension = this.getLanguageExtension(newLanguage);

            // If the file has a generic extension or wrong extension, suggest renaming
            if (currentExtension === 'txt' || currentExtension === '' ||
                this.getLanguageFromExtension(currentExtension) !== newLanguage) {

                const baseName = this.getBaseName(activeFile.name);
                const suggestedName = baseName + '.' + expectedExtension;

                // Ask user if they want to rename the file
                if (confirm(`Change filename from "${activeFile.name}" to "${suggestedName}" to match the selected language?`)) {
                    this.renameFile(this.activeFileId, suggestedName);
                } else {
                    // Just update the language property
                    activeFile.language = newLanguage;
                }
            } else {
                // Just update the language property
                activeFile.language = newLanguage;
            }
        }
    }

    getLanguageExtension(language) {
        const extensions = {
            'python': 'py',
            'c': 'c',
            'cpp': 'cpp',
            'java': 'java',
            'javascript': 'js',
            'eiffel': 'e'
        };

        return extensions[language] || 'txt';
    }

    getBaseName(filename) {
        const lastDot = filename.lastIndexOf('.');
        return lastDot !== -1 ? filename.substring(0, lastDot) : filename;
    }

    getFileExtension(filename) {
        const lastDot = filename.lastIndexOf('.');
        return lastDot !== -1 ? filename.substring(lastDot + 1).toLowerCase() : '';
    }

    getLanguageFromExtension(extension) {
        const extensionMap = {
            'py': 'python',
            'c': 'c',
            'cpp': 'cpp',
            'cc': 'cpp',
            'cxx': 'cpp',
            'cpp': 'cpp',
            'h': 'c',
            'hpp': 'cpp',
            'hxx': 'cpp',
            'java': 'java',
            'js': 'javascript',
            'jsx': 'javascript',
            'ts': 'javascript',
            'tsx': 'javascript',
            'e': 'eiffel',
            'ecf': 'eiffel',
            'txt': 'python',  // Default for text files
            'md': 'python',   // Default for markdown
            '': 'python'      // Default for no extension
        };

        return extensionMap[extension] || 'python'; // Default to python
    }

    // Get current active file info
    getActiveFile() {
        if (!this.activeFileId || !this.files.has(this.activeFileId)) {
            return null;
        }
        return this.files.get(this.activeFileId);
    }

    // Get all files
    getAllFiles() {
        // Update current file content before returning
        if (this.activeFileId && this.files.has(this.activeFileId)) {
            const currentContent = this.codeEditor.getCodeContent();
            this.files.get(this.activeFileId).content = currentContent;
        }

        return Array.from(this.files.values());
    }

    // Save current file content
    saveCurrentFile() {
        if (this.activeFileId && this.files.has(this.activeFileId)) {
            const currentContent = this.codeEditor.getCodeContent();
            this.files.get(this.activeFileId).content = currentContent;
        }
    }

    async renameFilePrompt(fileId) {
        if (!this.files.has(fileId)) return;
        const file = this.files.get(fileId);
        const existingFiles = Array.from(this.files.values()).filter(f => f.id !== fileId).map(f => f.name);
        if (window.modalManager) {
            const newName = await window.modalManager.promptRename(file.name, existingFiles);
            if (newName && newName.trim() && newName !== file.name) {
                this.renameFile(fileId, newName.trim());
            }
        } else {
            // fallback
            const newName = prompt('Enter new filename:', file.name);
            if (newName && newName.trim() && newName !== file.name) {
                const trimmedName = newName.trim();
                if (existingFiles.includes(trimmedName)) {
                    alert('A file with this name already exists.');
                    return;
                }
                this.renameFile(fileId, trimmedName);
            }
        }
    }

    // Update filename
    renameFile(fileId, newName) {
        if (!this.files.has(fileId)) return false;

        const file = this.files.get(fileId);
        file.name = newName;
        file.extension = this.getFileExtension(newName);
        file.language = this.getLanguageFromExtension(file.extension);

        // Update tab display
        const tabElement = document.querySelector(`[data-file-id="${fileId}"]`);
        if (tabElement) {
            const tabName = tabElement.querySelector('.tab-name');
            if (tabName) {
                tabName.textContent = newName;
            }
        }

        // Update language if this is the active file
        if (this.activeFileId === fileId) {
            if (this.dom.language.value !== file.language) {
                this.dom.language.value = file.language;
                this.codeEditor.updateCodeMirrorMode();
            }
        }

        return true;
    }

    handleTabRightClick(e) {
        e.preventDefault();
        // Placeholder for context menu functionality
        console.log('Right-click on tab - context menu not implemented yet');
    }
}

// Export as global for backwards compatibility
window.FileManager = FileManager;