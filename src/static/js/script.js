document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded');

    // DOM elements
    const codeEditor = document.getElementById('code-editor');
    const languageSelect = document.getElementById('language');
    const timeoutInput = document.getElementById('timeout');
    const compileBtn = document.getElementById('compile-btn');
    const runBtn = document.getElementById('run-btn');
    const verifyBtn = document.getElementById('verify-btn');
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
    console.log('Elements found:');
    console.log('languageSelect:', languageSelect);
    console.log('examplesSelect:', examplesSelect);
    console.log('loadExampleBtn:', loadExampleBtn);

    // Verify all critical elements are available
    if (!languageSelect) {
        console.error('languageSelect element not found!');
        return;
    }
    if (!examplesSelect) {
        console.error('examplesSelect element not found!');
        return;
    }
    if (!loadExampleBtn) {
        console.error('loadExampleBtn element not found!');
        return;
    }

    // CodeMirror initialization
    let codeEditorCM = null;

    // Language mode mapping for CodeMirror
    const languageModes = {
        'python': 'python',
        'c': 'text/x-csrc',
        'cpp': 'text/x-c++src',
        'java': 'text/x-java',
        'javascript': 'javascript',
        'eiffel': 'text/x-eiffel'
    };

    // Initialize CodeMirror
    function initializeCodeMirror() {
        const currentLanguage = languageSelect.value;
        const mode = languageModes[currentLanguage] || 'text/plain';

        if (codeEditorCM) {
            codeEditorCM.toTextArea();
        }

        codeEditorCM = CodeMirror.fromTextArea(codeEditor, {
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
        codeEditorCM.on('change', function (instance) {
            instance.save();
        });

        // Setup resize handling for CodeMirror
        setupEditorResize();

        console.log('CodeMirror initialized with mode:', mode);
    }

    // Setup resize functionality for the editor
    function setupEditorResize() {
        const editorContainer = document.getElementById('editor-container');

        if (!editorContainer || !codeEditorCM) {
            return;
        }

        // Create a ResizeObserver to watch for container size changes
        if (window.ResizeObserver) {
            const resizeObserver = new ResizeObserver(entries => {
                for (let entry of entries) {
                    if (entry.target === editorContainer) {
                        // Refresh CodeMirror when container is resized
                        setTimeout(() => {
                            if (codeEditorCM) {
                                codeEditorCM.refresh();
                            }
                        }, 10);
                    }
                }
            });

            resizeObserver.observe(editorContainer);
        }

        // Also handle manual refresh on window resize
        window.addEventListener('resize', () => {
            if (codeEditorCM) {
                setTimeout(() => {
                    codeEditorCM.refresh();
                }, 100);
            }
        });
    }

    // Function to get code content (works with both textarea and CodeMirror)
    function getCodeContent() {
        if (codeEditorCM) {
            return codeEditorCM.getValue();
        }
        return codeEditor.value;
    }

    // Function to set code content (works with both textarea and CodeMirror)
    function setCodeContent(content) {
        if (codeEditorCM) {
            codeEditorCM.setValue(content);
        } else {
            codeEditor.value = content;
        }
    }

    // Function to update CodeMirror mode when language changes
    function updateCodeMirrorMode() {
        if (codeEditorCM) {
            const currentLanguage = languageSelect.value;
            const mode = languageModes[currentLanguage] || 'text/plain';
            codeEditorCM.setOption('mode', mode);
            console.log('CodeMirror mode updated to:', mode);
        }
    }

    // Initialize CodeMirror when DOM is ready
    if (typeof CodeMirror !== 'undefined') {
        initializeCodeMirror();
    } else {
        console.warn('CodeMirror not available, falling back to textarea');
    }

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

            availableExamples = data;
            console.log('Available examples stored:', availableExamples);
            console.log('Available languages:', Object.keys(availableExamples));

            console.log('Calling updateExamplesDropdown...');
            updateExamplesDropdown();
            console.log('=== loadAvailableExamples complete ===');
        } catch (error) {
            console.error('Error loading examples:', error);
            console.error('Error stack:', error.stack);
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
        console.log('=== updateExamplesDropdown called ===');
        console.log('availableExamples object:', availableExamples);
        console.log('languageSelect:', languageSelect);
        console.log('languageSelect.value:', languageSelect ? languageSelect.value : 'null');

        if (!languageSelect) {
            console.error('languageSelect is null!');
            return;
        }

        const currentLanguage = languageSelect.value;
        console.log('Current language:', currentLanguage);
        const examples = availableExamples[currentLanguage] || {};
        console.log('Examples for language:', examples);
        console.log('Object.keys(examples):', Object.keys(examples));

        if (!examplesSelect) {
            console.error('examplesSelect is null!');
            return;
        }

        // Clear existing options
        examplesSelect.innerHTML = '<option value="">Select an example...</option>';
        console.log('Cleared dropdown, current innerHTML:', examplesSelect.innerHTML);

        // Add examples for current language
        Object.keys(examples).forEach(filename => {
            const example = examples[filename];
            const option = document.createElement('option');
            option.value = filename;
            option.textContent = `${example.title} - ${example.description}`;
            examplesSelect.appendChild(option);
            console.log('Added option:', filename, example.title);
        });

        console.log('Final dropdown innerHTML:', examplesSelect.innerHTML);
        console.log('=== updateExamplesDropdown complete ===');

        // Update button state
        updateLoadExampleButton();
    }

    // Update the Load Example button state based on selection
    function updateLoadExampleButton() {
        if (!loadExampleBtn || !examplesSelect) return;

        const hasSelection = examplesSelect.value !== '';
        loadExampleBtn.disabled = !hasSelection;
        loadExampleBtn.textContent = hasSelection ? 'Load Example' : 'Load Example';
    }

    // Load selected example
    async function loadExample() {
        console.log('=== loadExample called ===');
        const selectedExample = examplesSelect.value;
        const currentLanguage = languageSelect.value;

        if (!selectedExample) {
            updateStatus('Please select an example from the dropdown first', false);
            // Flash the dropdown to draw attention
            examplesSelect.style.border = '2px solid #ff6b6b';
            setTimeout(() => {
                examplesSelect.style.border = '';
            }, 2000);
            return;
        }

        try {
            updateStatus('Loading example...', true);

            const response = await fetch(`/examples/${currentLanguage}/${selectedExample}`);
            const result = await response.json();

            if (response.ok) {
                setCodeContent(result.code);
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
                'java': 'HelloWorld.java',
                'eiffel': 'hello_world.e'
            };

            const defaultFile = defaultExamples[language];

            if (defaultFile && availableExamples[language] && availableExamples[language][defaultFile]) {
                // Load the default example file
                const response = await fetch(`/examples/${language}/${defaultFile}`);
                const result = await response.json();

                if (response.ok) {
                    setCodeContent(result.code);
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
                case 'eiffel':
                    placeholderCode = '-- Enter your Eiffel code here...\nclass\n\tHELLO_WORLD\n\ncreate\n\tmake\n\nfeature\n\tmake\n\t\t\t-- Print hello world message\n\t\tdo\n\t\t\tprint ("Hello, World!%N")\n\t\tend\n\nend';
                    break;
                default:
                    placeholderCode = '// Enter your code here...';
            }

            setCodeContent(placeholderCode);
        } catch (error) {
            console.error('Error loading default example:', error);
            // Fallback to basic placeholder
            setCodeContent(`// Enter your ${language} code here...`);
        }
    }

    // Set initial example code (after examples are loaded)
    async function initializeEditor() {
        console.log('Starting editor initialization...');
        await loadAvailableExamples();
        console.log('Examples loaded, setting example code...');
        await setExampleCode(languageSelect.value);
        console.log('Editor initialization complete');
    }

    // Initialize the editor
    console.log('Initializing editor...');
    initializeEditor();

    // Set initial verify button visibility
    updateVerifyButtonVisibility();

    // Change example code when language changes
    languageSelect.addEventListener('change', async () => {
        console.log('Language changed to:', languageSelect.value);
        updateCodeMirrorMode(); // Update CodeMirror syntax highlighting
        await setExampleCode(languageSelect.value);
        updateExamplesDropdown();
        updateVerifyButtonVisibility(); // Show/hide verify button based on language
        // Reset compilation paths
        compiledFilePath = null;
        compiledOutputPath = null;
    });

    // Update status display
    function updateStatus(message, isSuccess) {
        statusEl.textContent = message;
        statusEl.className = 'status ' + (isSuccess ? 'success' : 'error');
    }

    // Show/hide verify button based on language
    function updateVerifyButtonVisibility() {
        const language = languageSelect.value;
        if (language === 'eiffel') {
            verifyBtn.style.display = 'inline-block';
        } else {
            verifyBtn.style.display = 'none';
        }
    }

    // Show/hide cancel button and disable/enable other buttons
    function setExecutionState(isRunning) {
        if (isRunning) {
            cancelBtn.style.display = 'inline-block';
            compileBtn.disabled = true;
            runBtn.disabled = true;
            verifyBtn.disabled = true;
        } else {
            cancelBtn.style.display = 'none';
            compileBtn.disabled = false;
            runBtn.disabled = false;
            verifyBtn.disabled = false;
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
    function updateOutput(text, isHtml = false) {
        if (isHtml) {
            outputEl.innerHTML = text || '';
        } else {
            outputEl.textContent = text || '';
        }
    }

    // Compile code
    async function compileCode() {
        const code = getCodeContent();
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
        const code = getCodeContent();
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

    // Verify code (Eiffel only)
    async function verifyCode() {
        const code = getCodeContent();
        const language = languageSelect.value;
        const timeout = parseInt(timeoutInput.value) || 30;

        if (!code.trim()) {
            updateStatus('Please enter some code first', false);
            return;
        }

        if (language !== 'eiffel') {
            updateStatus('Verification is only supported for Eiffel', false);
            return;
        }

        setExecutionState(true);
        updateStatus('Starting verification...', true);

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
            currentExecutionId = result.execution_id;
            console.log('Verification ID:', currentExecutionId);

            if (result.started) {
                // Verification started successfully, begin status checking
                updateStatus('Verifying with AutoProof...', true);
                startStatusCheck(result.execution_id, timeout);
            } else {
                // Verification failed to start
                updateStatus(result.message, result.success);
                updateOutput(result.output || '');
                setExecutionState(false);
                currentExecutionId = null;
            }

        } catch (error) {
            console.error('Verification error:', error);
            updateStatus('Error during verification: ' + error.message, false);
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

                        // Use HTML rendering for verification results
                        const isHtml = status.operation_type === 'verify';
                        updateOutput(status.output || '', isHtml);

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

    verifyBtn.addEventListener('click', verifyCode);

    showConfigBtn.addEventListener('click', () => {
        if (configEditor.style.display === 'none') {
            configEditor.style.display = 'block';
            loadConfig();
        } else {
            configEditor.style.display = 'none';
        }
    });

    saveConfigBtn.addEventListener('click', saveConfig);

    loadExampleBtn.addEventListener('click', () => {
        console.log('Load example button clicked');
        loadExample();
    });

    // Update button state when example selection changes
    examplesSelect.addEventListener('change', updateLoadExampleButton);
    // Add event listener to load example when selection changes (optional: auto-load)
    // examplesSelect.addEventListener('change', loadExample); // Uncomment to auto-load on change

    cancelBtn.addEventListener('click', cancelExecution); cleanupSessionBtn.addEventListener('click', cleanupSession);

    // Initialize
    loadSessionInfo();

    // Refresh session info every 30 seconds
    setInterval(loadSessionInfo, 30000);
});
