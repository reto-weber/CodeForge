/**
 * Test script to verify the refactored JavaScript modules
 * This can be run in the browser console to test functionality
 */

// Test function to verify all modules are loaded
function testModules() {
    const results = {
        DOMElements: typeof DOMElements !== 'undefined',
        UIUtils: typeof UIUtils !== 'undefined',
        CodeEditorManager: typeof CodeEditorManager !== 'undefined',
        ExamplesManager: typeof ExamplesManager !== 'undefined',
        SessionManager: typeof SessionManager !== 'undefined',
        CodeExecutionManager: typeof CodeExecutionManager !== 'undefined',
        ConfigManager: typeof ConfigManager !== 'undefined'
    };

    console.log('Module availability test:', results);

    // Check if all modules are available
    const allLoaded = Object.values(results).every(loaded => loaded);
    console.log('All modules loaded:', allLoaded);

    return results;
}

// Test DOM elements
function testDOMElements() {
    try {
        const dom = new DOMElements();
        console.log('DOMElements test: SUCCESS');
        console.log('Language select found:', !!dom.language);
        console.log('Examples select found:', !!dom.examples);
        return true;
    } catch (error) {
        console.error('DOMElements test: FAILED', error);
        return false;
    }
}

// Test examples loading
async function testExamplesAPI() {
    try {
        const response = await fetch('/examples');
        const data = await response.json();
        console.log('Examples API test: SUCCESS');
        console.log('Available languages:', Object.keys(data));
        return true;
    } catch (error) {
        console.error('Examples API test: FAILED', error);
        return false;
    }
}

// Run all tests
function runAllTests() {
    console.log('=== Running Module Tests ===');

    testModules();
    testDOMElements();
    testExamplesAPI();

    console.log('=== Tests Complete ===');
}

// Auto-run tests when this script is loaded
if (typeof window !== 'undefined') {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', runAllTests);
    } else {
        runAllTests();
    }
}
