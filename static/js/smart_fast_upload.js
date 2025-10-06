
// Smart-fast upload frontend - processes all data efficiently
(function() {
    'use strict';
    
    // Override the upload function for smart-fast processing
    if (typeof TagManager !== 'undefined' && TagManager.prototype.uploadFile) {
        const originalUploadFile = TagManager.prototype.uploadFile;
        
        TagManager.prototype.uploadFile = function(file) {
            console.log('🧠 Using SMART-FAST upload mode');
            
            const formData = new FormData();
            formData.append('file', file);
            
            // Show smart-fast UI
            this.showUploadProgress('Smart-fast mode: Processing all products efficiently...');
            
            return fetch('/upload-smart-fast', {
                method: 'POST',
                body: formData,
                timeout: 30000  // 30 second timeout
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('🧠 Smart-fast upload result:', data);
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Show success message
                this.showUploadSuccess(`🧠 Smart-fast upload complete in ${data.processing_time}s! Processed ${data.total_products} products.`);
                
                // Load tags immediately
                this.loadTags();
                
                return data;
            })
            .catch(error => {
                console.error('🧠 Smart-fast upload failed:', error);
                // Try ultra-instant as fallback
                console.log('🧠 Trying ultra-instant mode...');
                return this.tryUltraInstantUpload(file);
            });
        };
        
        // Add ultra-instant upload fallback
        TagManager.prototype.tryUltraInstantUpload = function(file) {
            const formData = new FormData();
            formData.append('file', file);
            
            this.showUploadProgress('Ultra-instant mode: Just saving file...');
            
            return fetch('/upload-ultra-instant', {
                method: 'POST',
                body: formData,
                timeout: 5000  // 5 second timeout
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('⚡ Ultra-instant upload result:', data);
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                this.showUploadSuccess(`⚡ Ultra-instant upload complete in ${data.processing_time}s!`);
                this.loadTags();
                
                return data;
            })
            .catch(error => {
                console.error('⚡ Ultra-instant upload failed:', error);
                this.showUploadError(`Both smart-fast and ultra-instant upload failed: ${error.message}`);
                throw error;
            });
        };
        
        console.log('🧠 Smart-fast upload mode activated');
    }
})();
