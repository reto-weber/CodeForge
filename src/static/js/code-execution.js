/**
 * Code Execution Manager
 * Handles compilation and execution of code
 */

class CodeExecutionManager {
    constructor(domElements, codeEditor, uiUtils) {
        this.dom = domElements;
        this.codeEditor = codeEditor;
        this.ui = uiUtils;

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

    // Compile code
    async compileCode() {
        const code = this.codeEditor.getCodeContent();
        const language = this.dom.language.value;

        if (!code.trim()) {
            this.ui.updateStatus('Please enter some code first', false);
            return false;
        }

        this.ui.updateStatus('Compiling...', true);

        try {
            const formData = new FormData();
            formData.append('code', code);
            formData.append('language', language);

            const response = await fetch('/compile', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            this.ui.updateStatus(result.message, result.success);
            this.ui.updateOutput(result.output);

            if (result.success) {
                // Store file paths for running
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
        const code = this.codeEditor.getCodeContent();
        const language = this.dom.language.value;
        const timeout = parseInt(this.dom.timeoutInput.value) || 30;

        if (!code.trim()) {
            this.ui.updateStatus('Please enter some code first', false);
            return;
        }

        this.ui.setExecutionState(true);
        this.ui.updateStatus('Starting execution...', true);

        try {
            const formData = new FormData();
            formData.append('code', code);
            formData.append('language', language);
            formData.append('timeout', timeout.toString());

            // Add compiled file paths if available and requested
            if (useCompiled && this.compiledFilePath) {
                formData.append('file_path', this.compiledFilePath);

                if (this.compiledOutputPath) {
                    formData.append('output_path', this.compiledOutputPath);
                }
            }

            const response = await fetch('/run', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            this.currentExecutionId = result.execution_id;
            console.log('Execution ID:', this.currentExecutionId);

            if (result.started) {
                // Execution started successfully, begin status checking
                this.ui.updateStatus('Running...', true);
                this.startStatusCheck(result.execution_id, timeout);
            } else {
                // Execution failed to start
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
        const code = this.codeEditor.getCodeContent();
        const language = this.dom.language.value;
        const timeout = parseInt(this.dom.timeoutInput.value) || 30;

        if (!code.trim()) {
            this.ui.updateStatus('Please enter some code first', false);
            return;
        }

        if (language !== 'eiffel') {
            this.ui.updateStatus('Verification is only supported for Eiffel', false);
            return;
        }

        this.ui.setExecutionState(true);
        this.ui.updateStatus('Starting verification...', true);

        try {
            const formData = new FormData();
            formData.append('code', code);
            formData.append('language', language);
            formData.append('timeout', timeout.toString());

            const response = await fetch('/verify', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            this.currentExecutionId = result.execution_id;
            console.log('Verification ID:', this.currentExecutionId);

            if (result.started) {
                // Verification started successfully, begin status checking
                this.ui.updateStatus('Verifying with AutoProof...', true);
                this.startStatusCheck(result.execution_id, timeout);
            } else {
                // Verification failed to start
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
                    // Execution completed
                    this.ui.setExecutionState(false);
                    this.currentExecutionId = null;

                    if (status.completed) {
                        // Show final results
                        const exitCodeMsg = status.exit_code !== undefined ? ` (Exit code: ${status.exit_code})` : '';
                        this.ui.updateStatus(status.message + exitCodeMsg, status.success);

                        // Use HTML rendering for verification results
                        const isHtml = status.operation_type === 'verify';
                        this.ui.updateOutput(status.output || '', isHtml);

                        // Update container status after execution
                        this.dom.containerStatusEl.innerHTML += '<br>Last execution completed in container';
                    } else {
                        this.ui.updateStatus(status.message || 'Execution completed', false);
                    }

                    // Refresh session info after execution completes
                    if (window.sessionManager) {
                        setTimeout(() => window.sessionManager.loadSessionInfo(), 500);
                    }

                    // Clear the interval
                    if (this.statusCheckInterval) {
                        clearInterval(this.statusCheckInterval);
                        this.statusCheckInterval = null;
                    }
                    return;
                }

                // Still running - update status with timing info
                const elapsed = status.elapsed_time;
                const remaining = Math.max(0, timeout - elapsed);
                this.ui.updateStatus(`Running in container... (${elapsed.toFixed(1)}s elapsed, ${remaining.toFixed(1)}s remaining)`, true);

                // Check if we've exceeded timeout (shouldn't happen with backend timeout, but just in case)
                if (elapsed >= timeout * 1.1) { // 10% buffer
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
        }, 1000); // Check every second
    }

    // Cancel current execution
    async cancelExecution() {
        console.log('Cancelling execution:', this.currentExecutionId);
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
