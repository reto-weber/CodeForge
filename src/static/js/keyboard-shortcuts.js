// Keyboard accessibility for buttons, dropdowns, and file tabs
// Assigns hotkeys to each button and dropdown, and shows a help overlay with assignments

(function () {
    const keyMap = [
        { key: 'L', selector: '#language', label: 'Language Dropdown' },
        { key: 'E', selector: '#examples', label: 'Examples Dropdown' },
        { key: 'X', selector: '#load-example-btn', label: 'Load Example' },
        { key: 'C', selector: '#compile-btn', label: 'Compile' },
        { key: 'R', selector: '#run-btn', label: 'Run' },
        { key: 'V', selector: '#verify-btn', label: 'Verify' },
        { key: 'S', selector: '#share-url-btn', label: 'Share Code URL' },
        { key: 'A', selector: '#add-file-btn', label: 'Add File' },
        { key: 'O', selector: '#close-output-btn', label: 'Close Output' },
        { key: 'T', selector: '#timeout', label: 'Timeout Input' },
        { key: 'B', selector: null, label: 'Go to Eiffel Library Browser' },
    ];
    const helpKey = '?'; // Shift+/ on most keyboards
    let helpOverlay = null;

    function showHelpOverlay() {
        if (helpOverlay) return;
        helpOverlay = document.createElement('div');
        helpOverlay.className = 'hotkey-help-overlay';
        helpOverlay.tabIndex = 0;
        helpOverlay.innerHTML =
            '<div class="hotkey-help-content">' +
            '<h2>Keyboard Shortcuts</h2>' +
            '<ul>' +
            keyMap.map(k => `<li><b>${k.key}</b>: ${k.label}</li>`).join('') +
            '<li><b style="color:#60a5fa;">Shift+[1-9]</b>: Go to tab 1-9 (Shift+1 prioritizes root files)</li>' +
            '</ul>' +
            '<p>Press <b>Esc</b> to close</p>' +
            '</div>';
        document.body.appendChild(helpOverlay);
        helpOverlay.focus();
        helpOverlay.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                hideHelpOverlay();
            }
        });
    }
    function hideHelpOverlay() {
        if (helpOverlay) {
            helpOverlay.remove();
            helpOverlay = null;
        }
    }

    // Function to check if CodeMirror is focused and handle escape
    function isCodeMirrorFocused() {
        return document.querySelector('.CodeMirror-focused') !== null;
    }

    // Wait for CodeMirror to be initialized and hook into it
    function setupCodeMirrorEscape() {
        const codeMirrorEl = document.querySelector('.CodeMirror');
        if (codeMirrorEl && codeMirrorEl.CodeMirror) {
            const cm = codeMirrorEl.CodeMirror;
            cm.setOption('extraKeys', {
                ...cm.getOption('extraKeys'),
                'Esc': function (cm) {
                    cm.getInputField().blur();
                    document.body.focus();
                }
            });
        } else {
            // Retry after a short delay if CodeMirror isn't ready yet
            setTimeout(setupCodeMirrorEscape, 100);
        }
    }

    // Setup CodeMirror escape handling when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupCodeMirrorEscape);
    } else {
        setupCodeMirrorEscape();
    }

    document.addEventListener('keydown', function (e) {
        // Handle Esc in input fields to blur them and allow global shortcuts
        if (e.key === 'Escape' && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) {
            e.target.blur();
            e.preventDefault();
            return;
        }

        // Skip processing if we're in any input field (including CodeMirror)
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable || isCodeMirrorFocused()) {
            // Only handle help overlay when CodeMirror is focused
            if (isCodeMirrorFocused() && e.shiftKey && e.key === helpKey) {
                showHelpOverlay();
                e.preventDefault();
                return;
            }
            return;
        }
        if (e.shiftKey && e.key === helpKey) {
            showHelpOverlay();
            e.preventDefault();
            return;
        }
        if (helpOverlay) {
            if (e.key === 'Escape') hideHelpOverlay();
            return;
        }
        // Shift+{number} to go to tab {number}
        if (e.shiftKey && /^Digit[1-9]$/.test(e.code)) {
            const tabNum = Number(e.code.replace('Digit', ''));
            goToTab(tabNum - 1);
            e.preventDefault();
            return;
        }
        for (const { key, selector } of keyMap) {
            if (e.key.toUpperCase() === key) {
                // Handle special cases that don't use DOM selectors
                if (key === 'B') {
                    toggleLibraryBrowser();
                    e.preventDefault();
                    break;
                }

                const el = document.querySelector(selector);
                if (el) {
                    if (el.tagName === 'BUTTON') {
                        el.focus();
                        el.click();
                    } else if (el.tagName === 'SELECT' || el.tagName === 'INPUT') {
                        el.focus();
                    }
                }
                e.preventDefault();
                break;
            }
        }
    });

    // Go to library browser function
    function toggleLibraryBrowser() {
        const librarySection = document.getElementById('library-section');
        if (!librarySection) return;

        // Always show the library browser
        librarySection.style.display = 'block';

        // Focus the library input field after a short delay
        setTimeout(() => {
            const libraryInput = document.getElementById('library-class-input');
            if (libraryInput) {
                libraryInput.focus();
            }
        }, 50);
    }

    // Go to tab by index (0-based)
    function goToTab(idx) {
        const tabs = Array.from(document.querySelectorAll('.file-tabs .file-tab'));
        if (!tabs.length || idx < 0 || idx >= tabs.length) return;
        tabs[idx].focus();
        tabs[idx].click();
    }

    // Add minimal styles for the help overlay
    const style = document.createElement('style');
    style.textContent = `
    .hotkey-help-overlay {
        position: fixed; z-index: 2000; top: 0; left: 0; width: 100vw; height: 100vh;
        background: rgba(30, 41, 59, 0.85); color: #fff; display: flex; align-items: center; justify-content: center;
    }
    .hotkey-help-content {
        background: #1e293b; border-radius: 12px; padding: 2rem 2.5rem; box-shadow: 0 8px 32px rgba(0,0,0,0.25);
        min-width: 320px; max-width: 90vw;
    }
    .hotkey-help-content h2 { margin-top: 0; font-size: 1.5rem; color: #60a5fa; }
    .hotkey-help-content ul { list-style: none; padding: 0; margin: 1rem 0; }
    .hotkey-help-content li { margin: 0.5rem 0; font-size: 1.1rem; }
    .hotkey-help-content b { color: #60a5fa; }
    .hotkey-help-content p { margin: 1rem 0 0 0; font-size: 1rem; color: #cbd5e1; }
    `;
    document.head.appendChild(style);
})();
