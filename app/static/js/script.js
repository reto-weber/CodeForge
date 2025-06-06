document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const codeEditor = document.getElementById('code-editor');
    const languageSelect = document.getElementById('language');
    const timeoutInput = document.getElementById('timeout');
    const compileBtn = document.getElementById('compile-btn');
    const runBtn = document.getElementById('run-btn');
    const compileRunBtn = document.getElementById('compile-run-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const statusEl = document.getElementById('status');
    const outputEl = document.getElementById('output');
    const containerStatusEl = document.getElementById('container-status');
    const sessionStatusEl = document.getElementById('session-status');
    const cleanupSessionBtn = document.getElementById('cleanup-session-btn');
    const showConfigBtn = document.getElementById('show-config-btn');
    const configEditor = document.getElementById('config-editor');
    const configTextarea = document.getElementById('config-textarea');
    const saveConfigBtn = document.getElementById('save-config-btn');
    const examplesSelect = document.getElementById('examples');
    const loadExampleBtn = document.getElementById('load-example-btn');

    // Variables to store compilation results and session info
    let compiledFilePath = null;
    let compiledOutputPath = null;
    let availableExamples = {};
    let currentExecutionId = null;
    let statusCheckInterval = null;
    let sessionInfo = null;

    // Load available examples
    async function loadAvailableExamples() {
        try {
            const response = await fetch('/examples');
            availableExamples = await response.json();
            updateExamplesDropdown();
        } catch (error) {
            console.error('Error loading examples:', error);
        }
    }

    // Session management functions
    async function loadSessionInfo() {
        try {
            const response = await fetch('/session/info');
            const data = await response.json();

            if (data.error) {
                sessionStatusEl.textContent = 'No active session';
                containerStatusEl.textContent = 'No container information available';
                return;
            }

            sessionInfo = data;
            updateSessionDisplay();
        } catch (error) {
            console.error('Error loading session info:', error);
            sessionStatusEl.textContent = 'Error loading session info';
        }
    }

    function updateSessionDisplay() {
        if (!sessionInfo) return;

        const sessionAge = Math.round((Date.now() / 1000) - sessionInfo.session_created);
        const lastUsed = Math.round((Date.now() / 1000) - sessionInfo.session_last_used);

        sessionStatusEl.innerHTML = `
            Session ID: ${sessionInfo.session_id.substring(0, 8)}...<br>
            Age: ${formatDuration(sessionAge)}<br>
            Last used: ${formatDuration(lastUsed)} ago
        `;

        if (sessionInfo.container) {
            const containerAge = Math.round(sessionInfo.container.age_seconds);
            containerStatusEl.innerHTML = `
                Container Status: ${sessionInfo.container.status}<br>
                Container Age: ${formatDuration(containerAge)}<br>
                Container ID: ${sessionInfo.container.container_id.substring(0, 12)}...
            `;
        } else {
            containerStatusEl.textContent = 'No container active (will be created on first execution)';
        }
    }

    function formatDuration(seconds) {
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
        return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
    }

    async function cleanupSession() {
        if (!confirm('Are you sure you want to clean up the current session? This will stop any running containers.')) {
            return;
        }

        try {
            cleanupSessionBtn.disabled = true;
            cleanupSessionBtn.textContent = '🔄 Cleaning...';

            const formData = new FormData();
            const response = await fetch('/session/cleanup', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                sessionStatusEl.textContent = 'Session cleaned up successfully';
                containerStatusEl.textContent = 'No container active';
                sessionInfo = null;
                // Reload session info to get new session
                setTimeout(loadSessionInfo, 1000);
            } else {
                alert('Failed to clean up session: ' + result.message);
            }
        } catch (error) {
            console.error('Error cleaning up session:', error);
            alert('Error cleaning up session: ' + error.message);
        } finally {
            cleanupSessionBtn.disabled = false;
            cleanupSessionBtn.textContent = '🗑️ Clean Session';
        }
    }

    // Update examples dropdown based on selected language
    function updateExamplesDropdown() {
        const currentLanguage = languageSelect.value;
        const examples = availableExamples[currentLanguage] || {};

        // Clear existing options
        examplesSelect.innerHTML = '<option value="">Select an example...</option>';

        // Add examples for current language
        Object.keys(examples).forEach(filename => {
            const example = examples[filename];
            const option = document.createElement('option');
            option.value = filename;
            option.textContent = `${example.title} - ${example.description}`;
            examplesSelect.appendChild(option);
        });
    }

    // Load selected example
    async function loadExample() {
        const selectedExample = examplesSelect.value;
        const currentLanguage = languageSelect.value;

        if (!selectedExample) {
            updateStatus('Please select an example first', false);
            return;
        }

        try {
            updateStatus('Loading example...', true);

            const response = await fetch(`/examples/${currentLanguage}/${selectedExample}`);
            const result = await response.json();

            if (response.ok) {
                codeEditor.value = result.code;
                updateStatus(`Loaded example: ${selectedExample}`, true);

                // Reset compilation paths when loading new code
                compiledFilePath = null;
                compiledOutputPath = null;
            } else {
                updateStatus(`Error loading example: ${result.detail || result.error}`, false);
            }
        } catch (error) {
            console.error('Error loading example:', error);
            updateStatus('Error loading example: ' + error.message, false);
        }
    }

    // Load default example code for the selected language
    async function setExampleCode(language) {
        try {
            // Define default example files for each language
            const defaultExamples = {
                'python': 'hello_world.py',
                'c': 'hello_world.c',
                'cpp': 'hello_world.cpp',
                'java': 'HelloWorld.java'
            };

            const defaultFile = defaultExamples[language];

            if (defaultFile && availableExamples[language] && availableExamples[language][defaultFile]) {
                // Load the default example file
                const response = await fetch(`/examples/${language}/${defaultFile}`);
                const result = await response.json();

                if (response.ok) {
                    codeEditor.value = result.code;
                    return;
                }
            }

            // Fallback to simple placeholder if no example available
            let placeholderCode = '';
            switch (language) {
                case 'python':
                    placeholderCode = '# Enter your Python code here...\nprint("Hello, World!")';
                    break;
                case 'c':
                    placeholderCode = '// Enter your C code here...\n#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}';
                    break;
                case 'cpp':
                    placeholderCode = '// Enter your C++ code here...\n#include <iostream>\n\nint main() {\n    std::cout << "Hello, World!" << std::endl;\n    return 0;\n}';
                    break;
                case 'java':
                    placeholderCode = '// Enter your Java code here...\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}';
                    break;
                default:
                    placeholderCode = '// Enter your code here...';
            }

            codeEditor.value = placeholderCode;
        } catch (error) {
            console.error('Error loading default example:', error);
            // Fallback to basic placeholder
            codeEditor.value = `// Enter your ${language} code here...`;
        }
    }

    // Set initial example code (after examples are loaded)
    async function initializeEditor() {
        await loadAvailableExamples();
        await setExampleCode(languageSelect.value);
    }

    // Initialize the editor
    initializeEditor();

    // Change example code when language changes
    languageSelect.addEventListener('change', async () => {
        await setExampleCode(languageSelect.value);
        updateExamplesDropdown();
        // Reset compilation paths
        compiledFilePath = null;
        compiledOutputPath = null;
    });

    // Update status display
    function updateStatus(message, isSuccess) {
        statusEl.textContent = message;
        statusEl.className = 'status ' + (isSuccess ? 'success' : 'error');
    }

    // Show/hide cancel button and disable/enable other buttons
    function setExecutionState(isRunning) {
        if (isRunning) {
            cancelBtn.style.display = 'inline-block';
            compileBtn.disabled = true;
            runBtn.disabled = true;
            compileRunBtn.disabled = true;
        } else {
            cancelBtn.style.display = 'none';
            compileBtn.disabled = false;
            runBtn.disabled = false;
            compileRunBtn.disabled = false;
            if (statusCheckInterval) {
                clearInterval(statusCheckInterval);
                statusCheckInterval = null;
            }
        }
    }

    // Cancel current execution
    async function cancelExecution() {
        console.log('Cancelling execution:', currentExecutionId);
        if (!currentExecutionId) {
            updateStatus('No execution to cancel', false);
            return;
        }

        try {
            const formData = new FormData();
            formData.append('execution_id', currentExecutionId);

            const response = await fetch('/cancel', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            updateStatus(result.message, result.success);

            if (result.success) {
                setExecutionState(false);
                currentExecutionId = null;
            }
        } catch (error) {
            console.error('Cancel error:', error);
            updateStatus('Error cancelling execution: ' + error.message, false);
        }
    }

    // Update output display
    function updateOutput(text) {
        outputEl.textContent = text || '';
    }

    // Compile code
    async function compileCode() {
        const code = codeEditor.value;
        const language = languageSelect.value;

        if (!code.trim()) {
            updateStatus('Please enter some code first', false);
            return false;
        }

        updateStatus('Compiling...', true);

        try {
            const formData = new FormData();
            formData.append('code', code);
            formData.append('language', language);

            const response = await fetch('/compile', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            updateStatus(result.message, result.success);
            updateOutput(result.output);

            if (result.success) {
                // Store file paths for running
                compiledFilePath = result.file_path || null;
                compiledOutputPath = result.output_path || null;
            }

            return result.success;
        } catch (error) {
            console.error('Compilation error:', error);
            updateStatus('Error during compilation: ' + error.message, false);
            return false;
        }
    }

    // Run code
    async function runCode(useCompiled = true) {
        const code = codeEditor.value;
        const language = languageSelect.value;
        const timeout = parseInt(timeoutInput.value) || 30;

        if (!code.trim()) {
            updateStatus('Please enter some code first', false);
            return;
        }

        setExecutionState(true);
        updateStatus('Starting execution...', true);

        try {
            const formData = new FormData();
            formData.append('code', code);
            formData.append('language', language);
            formData.append('timeout', timeout.toString());

            // Add compiled file paths if available and requested
            if (useCompiled && compiledFilePath) {
                formData.append('file_path', compiledFilePath);

                if (compiledOutputPath) {
                    formData.append('output_path', compiledOutputPath);
                }
            }

            const response = await fetch('/run', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            currentExecutionId = result.execution_id;
            console.log('Execution ID:', currentExecutionId);

            if (result.started) {
                // Execution started successfully, begin status checking
                updateStatus('Running...', true);
                startStatusCheck(result.execution_id, timeout);
            } else {
                // Execution failed to start
                updateStatus(result.message, result.success);
                updateOutput(result.output || '');
                setExecutionState(false);
                currentExecutionId = null;
            }

        } catch (error) {
            console.error('Runtime error:', error);
            updateStatus('Error during execution: ' + error.message, false);
            setExecutionState(false);
            currentExecutionId = null;
        }
    }

    // Start checking execution status
    function startStatusCheck(executionId, timeout) {
        statusCheckInterval = setInterval(async () => {
            try {
                const response = await fetch(`/status/${executionId}`);
                const status = await response.json();

                if (!status.running) {
                    // Execution completed
                    setExecutionState(false);
                    currentExecutionId = null;

                    if (status.completed) {
                        // Show final results
                        const exitCodeMsg = status.exit_code !== undefined ? ` (Exit code: ${status.exit_code})` : '';
                        updateStatus(status.message + exitCodeMsg, status.success);
                        updateOutput(status.output || '');

                        // Update container status after execution
                        containerStatusEl.innerHTML += '<br>Last execution completed in container';
                    } else {
                        updateStatus(status.message || 'Execution completed', false);
                    }

                    // Refresh session info after execution completes
                    setTimeout(loadSessionInfo, 500);
                    return;
                }

                // Still running - update status with timing info
                const elapsed = status.elapsed_time;
                const remaining = Math.max(0, timeout - elapsed);
                updateStatus(`Running in container... (${elapsed.toFixed(1)}s elapsed, ${remaining.toFixed(1)}s remaining)`, true);

                // Check if we've exceeded timeout (shouldn't happen with backend timeout, but just in case)
                if (elapsed >= timeout * 1.1) { // 10% buffer
                    setExecutionState(false);
                    currentExecutionId = null;
                    updateStatus('Execution timed out', false);
                }

            } catch (error) {
                console.error('Status check error:', error);
                setExecutionState(false);
                currentExecutionId = null;
                updateStatus('Error checking execution status', false);
            }
        }, 1000); // Check every second
    }

    // Load configuration
    async function loadConfig() {
        try {
            const response = await fetch('/config');
            const config = await response.json();
            configTextarea.value = JSON.stringify(config, null, 2);
        } catch (error) {
            console.error('Error loading config:', error);
            configTextarea.value = '{"error": "Failed to load configuration"}';
        }
    }

    // Save configuration
    async function saveConfig() {
        try {
            const configText = configTextarea.value;
            let config;

            try {
                config = JSON.parse(configText);
            } catch (parseError) {
                updateStatus('Invalid JSON configuration', false);
                return;
            }

            const response = await fetch('/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: configText
            });

            const result = await response.json();

            if (result.success) {
                updateStatus('Configuration saved successfully', true);

                // Update language selector if languages changed
                if (config.compilers) {
                    const languages = Object.keys(config.compilers);
                    const currentLanguage = languageSelect.value;

                    // Clear options
                    languageSelect.innerHTML = '';

                    // Add new options
                    languages.forEach(lang => {
                        const option = document.createElement('option');
                        option.value = lang;
                        option.textContent = lang.charAt(0).toUpperCase() + lang.slice(1);
                        languageSelect.appendChild(option);
                    });

                    // Try to select previous language or default
                    if (languages.includes(currentLanguage)) {
                        languageSelect.value = currentLanguage;
                    } else if (config.default_language && languages.includes(config.default_language)) {
                        languageSelect.value = config.default_language;
                    }

                    // Update example code
                    await setExampleCode(languageSelect.value);
                    updateExamplesDropdown();
                }
            } else {
                updateStatus('Failed to save configuration', false);
            }
        } catch (error) {
            console.error('Error saving config:', error);
            updateStatus('Error saving configuration: ' + error.message, false);
        }
    }

    // Event listeners
    compileBtn.addEventListener('click', compileCode);

    runBtn.addEventListener('click', () => {
        // Run without compilation
        runCode(false);
    });

    compileRunBtn.addEventListener('click', async () => {
        // Compile then run if successful
        const success = await compileCode();
        if (success) {
            runCode(true);
        }
    });

    showConfigBtn.addEventListener('click', () => {
        if (configEditor.style.display === 'none') {
            configEditor.style.display = 'block';
            loadConfig();
        } else {
            configEditor.style.display = 'none';
        }
    });

    saveConfigBtn.addEventListener('click', saveConfig);

    loadExampleBtn.addEventListener('click', loadExample);

    cancelBtn.addEventListener('click', cancelExecution);

    cleanupSessionBtn.addEventListener('click', cleanupSession);

    // Initialize
    loadAvailableExamples();
    loadSessionInfo();

    // Refresh session info every 30 seconds
    setInterval(loadSessionInfo, 30000);
});
