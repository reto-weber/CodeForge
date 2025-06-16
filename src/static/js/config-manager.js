/**
 * Configuration Manager
 * Handles configuration loading and saving
 */

class ConfigManager {
    constructor(domElements, uiUtils, examplesManager) {
        this.dom = domElements;
        this.ui = uiUtils;
        this.examplesManager = examplesManager;
    }

    // Load configuration from server
    async loadConfig() {
        if (!this.dom.configTextarea) {
            console.warn('Config textarea not found, skipping config load');
            return;
        }

        try {
            const response = await fetch('/config');
            const config = await response.json();
            this.dom.configTextarea.value = JSON.stringify(config, null, 2);
        } catch (error) {
            console.error('Error loading config:', error);
            this.dom.configTextarea.value = '{"error": "Failed to load configuration"}';
        }
    }

    // Save configuration to server
    async saveConfig() {
        if (!this.dom.configTextarea) {
            console.warn('Config textarea not found, skipping config save');
            return;
        }

        try {
            const configText = this.dom.configTextarea.value;
            let config;

            try {
                config = JSON.parse(configText);
            } catch (parseError) {
                this.ui.updateStatus('Invalid JSON configuration', false);
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
                this.ui.updateStatus('Configuration saved successfully', true);

                // Update language selector if languages changed
                if (config.compilers) {
                    await this.updateLanguageSelector(config);
                }
            } else {
                this.ui.updateStatus('Failed to save configuration', false);
            }
        } catch (error) {
            console.error('Error saving config:', error);
            this.ui.updateStatus('Error saving configuration: ' + error.message, false);
        }
    }

    // Update language selector when configuration changes
    async updateLanguageSelector(config) {
        const languages = Object.keys(config.compilers);
        const currentLanguage = this.dom.language.value;

        // Clear options
        this.dom.language.innerHTML = '';

        // Add new options
        languages.forEach(lang => {
            const option = document.createElement('option');
            option.value = lang;
            option.textContent = lang.charAt(0).toUpperCase() + lang.slice(1);
            this.dom.language.appendChild(option);
        });

        // Try to select previous language or default
        if (languages.includes(currentLanguage)) {
            this.dom.language.value = currentLanguage;
        } else if (config.default_language && languages.includes(config.default_language)) {
            this.dom.language.value = config.default_language;
        }

        // Update example code and dropdown
        await this.examplesManager.setExampleCode(this.dom.language.value);
        this.examplesManager.updateExamplesDropdown();
    }

    // Toggle configuration editor visibility
    toggleConfigEditor() {
        if (!this.dom.configEditor) {
            console.warn('Config editor not found, cannot toggle');
            return;
        }

        if (this.dom.configEditor.style.display === 'none') {
            this.dom.configEditor.style.display = 'block';
            this.loadConfig();
        } else {
            this.dom.configEditor.style.display = 'none';
        }
    }
}

// Export as global for backwards compatibility
window.ConfigManager = ConfigManager;
