/**
 * Code Execution Manager
 * Handles compilation and execution of code
 */

class CodeExecutionManager {
    constructor(domElements, codeEditor, uiUtils, fileManager = null) {
        this.dom = domElements;
        this.codeEditor = codeEditor;
        this.ui = uiUtils;
        this.fileManager = fileManager;

        // Compilation state
        this.compiledFilePath = null;
        this.compiledOutputPath = null;

        // Execution state
        this.currentExecutionId = null;
        this.statusCheckInterval = null;
    }

    // Reset compilation paths
    resetCompilation() {
        this.compiledFilePath = null;
        this.compiledOutputPath = null;
    }

    // Prepare request data for API calls
    prepareRequestData() {
        if (this.fileManager) {
            // Multi-file support
            this.fileManager.saveCurrentFile();
            const files = this.fileManager.getAllFiles();

            if (files.length === 0) {
                this.ui.updateStatus('No files available', false);
                return null;
            }

            const language = this.dom.language.value;

            return {
                language: language,
                files: files.map(file => ({
                    name: file.name,
                    content: file.content
                })),
                main_file: this.fileManager.getActiveFile()?.name || files[0].name
            };
        } else {
            // Single file support (legacy)
            const code = this.codeEditor.getCodeContent();
            if (!code.trim()) {
                this.ui.updateStatus('Please enter some code first', false);
                return null;
            }

            return {
                code: code,
                language: this.dom.language.value
            };
        }
    }

    // Compile code
    async compileCode() {
        const requestData = this.prepareRequestData();
        if (!requestData) return false;

        this.ui.updateStatus('Compiling...', true);

        try {
            const response = await fetch('/compile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            const result = await response.json();

            this.ui.updateStatus(result.message, result.success);
            this.ui.updateOutput(result.output);

            if (result.success) {
                this.compiledFilePath = result.file_path || null;
                this.compiledOutputPath = result.output_path || null;
            }

            return result.success;
        } catch (error) {
            console.error('Compilation error:', error);
            this.ui.updateStatus('Error during compilation: ' + error.message, false);
            return false;
        }
    }

    // Run code
    async runCode(useCompiled = true) {
        const requestData = this.prepareRequestData();
        if (!requestData) return;

        const timeout = parseInt(this.dom.timeoutInput.value) || 30;
        requestData.timeout = timeout;

        if (useCompiled && this.compiledFilePath) {
            requestData.file_path = this.compiledFilePath;
            if (this.compiledOutputPath) {
                requestData.output_path = this.compiledOutputPath;
            }
        }

        this.ui.setExecutionState(true);
        this.ui.updateStatus('Starting execution...', true);

        try {
            const response = await fetch('/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            const result = await response.json();
            this.currentExecutionId = result.execution_id;

            if (result.started) {
                this.ui.updateStatus('Running...', true);
                this.startStatusCheck(result.execution_id, timeout);
            } else {
                this.ui.updateStatus(result.message, result.success);
                this.ui.updateOutput(result.output || '');
                this.ui.setExecutionState(false);
                this.currentExecutionId = null;
            }

        } catch (error) {
            console.error('Runtime error:', error);
            this.ui.updateStatus('Error during execution: ' + error.message, false);
            this.ui.setExecutionState(false);
            this.currentExecutionId = null;
        }
    }

    // Verify code (Eiffel only)
    async verifyCode() {
        const requestData = this.prepareRequestData();
        if (!requestData) return;

        const timeout = parseInt(this.dom.timeoutInput.value) || 30;
        requestData.timeout = timeout;

        this.ui.setExecutionState(true);
        this.ui.updateStatus('Starting verification...', true);

        try {
            const response = await fetch('/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            const result = await response.json();
            this.currentExecutionId = result.execution_id;

            if (result.started) {
                this.ui.updateStatus('Verifying with AutoProof...', true);
                this.startStatusCheck(result.execution_id, timeout);
            } else {
                this.ui.updateStatus(result.message, result.success);
                this.ui.updateOutput(result.output || '');
                this.ui.setExecutionState(false);
                this.currentExecutionId = null;
            }

        } catch (error) {
            console.error('Verification error:', error);
            this.ui.updateStatus('Error during verification: ' + error.message, false);
            this.ui.setExecutionState(false);
            this.currentExecutionId = null;
        }
    }

    // Start checking execution status
    startStatusCheck(executionId, timeout) {
        this.statusCheckInterval = setInterval(async () => {
            try {
                const response = await fetch(`/status/${executionId}`);
                const status = await response.json();

                if (!status.running) {
                    this.ui.setExecutionState(false);
                    this.currentExecutionId = null;

                    if (status.completed) {
                        const exitCodeMsg = status.exit_code !== undefined ? ` (Exit code: ${status.exit_code})` : '';
                        this.ui.updateStatus(status.message + exitCodeMsg, status.success);

                        const isHtml = status.operation_type === 'verify';
                        this.ui.updateOutput(status.output || '', isHtml);

                        // Update container status if element exists
                        if (this.dom.containerStatusEl) {
                            this.dom.containerStatusEl.innerHTML += '<br>Last execution completed in container';
                        }
                    } else {
                        this.ui.updateStatus(status.message || 'Execution completed', false);
                    }

                    if (this.statusCheckInterval) {
                        clearInterval(this.statusCheckInterval);
                        this.statusCheckInterval = null;
                    }
                    return;
                }

                const elapsed = status.elapsed_time;
                const remaining = Math.max(0, timeout - elapsed);
                this.ui.updateStatus(`Running in container... (${elapsed.toFixed(1)}s elapsed, ${remaining.toFixed(1)}s remaining)`, true);

                if (elapsed >= timeout * 1.1) {
                    this.ui.setExecutionState(false);
                    this.currentExecutionId = null;
                    this.ui.updateStatus('Execution timed out', false);
                    if (this.statusCheckInterval) {
                        clearInterval(this.statusCheckInterval);
                        this.statusCheckInterval = null;
                    }
                }

            } catch (error) {
                console.error('Status check error:', error);
                this.ui.setExecutionState(false);
                this.currentExecutionId = null;
                this.ui.updateStatus('Error checking execution status', false);
                if (this.statusCheckInterval) {
                    clearInterval(this.statusCheckInterval);
                    this.statusCheckInterval = null;
                }
            }
        }, 1000);
    }

    // Cancel current execution
    async cancelExecution() {
        if (!this.currentExecutionId) {
            this.ui.updateStatus('No execution to cancel', false);
            return;
        }

        try {
            const formData = new FormData();
            formData.append('execution_id', this.currentExecutionId);

            const response = await fetch('/cancel', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            this.ui.updateStatus(result.message, result.success);

            if (result.success) {
                this.ui.setExecutionState(false);
                this.currentExecutionId = null;
                if (this.statusCheckInterval) {
                    clearInterval(this.statusCheckInterval);
                    this.statusCheckInterval = null;
                }
            }
        } catch (error) {
            console.error('Cancel error:', error);
            this.ui.updateStatus('Error cancelling execution: ' + error.message, false);
        }
    }

    // Compile and run in sequence
    async compileAndRun() {
        const success = await this.compileCode();
        if (success) {
            this.runCode(true);
        }
    }
}

// Export as global for backwards compatibility
window.CodeExecutionManager = CodeExecutionManager;
