// Ultra-fast frontend optimizations for PythonAnywhere
// Add this to your main.js or create a new fast-mode.js

// Fast upload with minimal processing
function uploadFileUltraFast(file, progressCallback, successCallback, errorCallback) {
    const formData = new FormData();
    formData.append('file', file);
    
    const startTime = Date.now();
    
    // Show progress immediately
    if (progressCallback) progressCallback(10);
    
    fetch('/upload-ultra-fast', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (progressCallback) progressCallback(90);
        return response.json();
    })
    .then(data => {
        if (progressCallback) progressCallback(100);
        
        const uploadTime = Date.now() - startTime;
        
        if (data.success) {
            if (successCallback) {
                successCallback({
                    ...data,
                    upload_time_ms: uploadTime
                });
            }
        } else {
            if (errorCallback) errorCallback(data.error || 'Upload failed');
        }
    })
    .catch(error => {
        const uploadTime = Date.now() - startTime;
        console.error('Upload error:', error);
        if (errorCallback) errorCallback(`Upload failed after ${uploadTime}ms: ${error.message}`);
    });
}

// Fast document generation with minimal features
function generateDocumentUltraFast(data, progressCallback, successCallback, errorCallback) {
    const startTime = Date.now();
    
    // Show progress immediately
    if (progressCallback) progressCallback(10);
    
    // Limit data for speed (max 25 items)
    const limitedData = {
        items: data.items ? data.items.slice(0, 25) : []
    };
    
    fetch('/generate-ultra-fast', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(limitedData)
    })
    .then(response => {
        if (progressCallback) progressCallback(80);
        return response.json();
    })
    .then(data => {
        if (progressCallback) progressCallback(100);
        
        const generationTime = Date.now() - startTime;
        
        if (data.success) {
            if (successCallback) {
                successCallback({
                    ...data,
                    generation_time_ms: generationTime
                });
            }
        } else {
            if (errorCallback) errorCallback(data.error || 'Generation failed');
        }
    })
    .catch(error => {
        const generationTime = Date.now() - startTime;
        console.error('Generation error:', error);
        if (errorCallback) errorCallback(`Generation failed after ${generationTime}ms: ${error.message}`);
    });
}

// Add fast mode toggle to your UI
function enableFastMode() {
    // Replace default upload handler with ultra-fast version
    window.uploadFile = uploadFileUltraFast;
    window.generateDocument = generateDocumentUltraFast;
    
    // Update UI to show fast mode is enabled
    const fastModeIndicator = document.createElement('div');
    fastModeIndicator.id = 'fast-mode-indicator';
    fastModeIndicator.innerHTML = `
        <div style="
            position: fixed;
            top: 10px;
            right: 10px;
            background: #28a745;
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1000;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        ">
            ⚡ Fast Mode (PythonAnywhere)
        </div>
    `;
    document.body.appendChild(fastModeIndicator);
    
    // Add warnings about limitations
    console.log('⚡ Fast Mode Enabled for PythonAnywhere');
    console.log('📝 Limitations: Max 25 items, simplified features');
    console.log('🔧 Endpoints: /upload-ultra-fast, /generate-ultra-fast');
}

// Auto-enable fast mode if on PythonAnywhere
if (window.location.hostname.includes('pythonanywhere.com')) {
    enableFastMode();
    console.log('🚀 PythonAnywhere detected - Fast mode auto-enabled');
}

// Export functions for manual use
window.uploadFileUltraFast = uploadFileUltraFast;
window.generateDocumentUltraFast = generateDocumentUltraFast;
window.enableFastMode = enableFastMode;