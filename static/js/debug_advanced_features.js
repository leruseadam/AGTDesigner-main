// Debug script for advanced features
console.log('Debug script loaded');

// Test if functions exist
function testAdvancedFeatures() {
    console.log('Testing advanced features...');
    
    const functions = [
        'openDatabaseAnalytics',
        'openProductSimilarity', 
        'openDatabaseHealth',
        'openAdvancedSearch',
        'openDatabaseBackup',
        'openTrendAnalysis',
        'openVendorAnalytics',
        'openDatabaseOptimization',
        'showDatabaseModal'
    ];
    
    functions.forEach(funcName => {
        if (typeof window[funcName] === 'function') {
            console.log(`✅ ${funcName} exists`);
        } else {
            console.log(`❌ ${funcName} is not defined`);
        }
    });
    
    // Test if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        console.log('✅ Bootstrap is loaded');
        console.log('Bootstrap version:', bootstrap.VERSION || 'Unknown');
    } else {
        console.log('❌ Bootstrap is not loaded');
    }
    
    // Test API endpoints
    const endpoints = [
        '/api/database-stats',
        '/api/database-vendor-stats',
        '/api/database-analytics',
        '/api/available-tags'
    ];
    
    endpoints.forEach(endpoint => {
        fetch(endpoint)
            .then(response => {
                if (response.ok) {
                    console.log(`✅ ${endpoint} - OK`);
                } else {
                    console.log(`❌ ${endpoint} - ${response.status}`);
                }
            })
            .catch(error => {
                console.log(`❌ ${endpoint} - Error: ${error.message}`);
            });
    });
}

// Run test when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', testAdvancedFeatures);
} else {
    testAdvancedFeatures();
}

// Add click handlers to test buttons
document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('[onclick*="openDatabase"]');
    buttons.forEach(button => {
        console.log('Found button:', button.textContent.trim());
        button.addEventListener('click', function(e) {
            console.log('Button clicked:', this.textContent.trim());
        });
    });
}); 