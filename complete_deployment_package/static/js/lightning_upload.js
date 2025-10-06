
// Ultra-fast upload frontend
(function() {
    'use strict';
    
    // Override the upload function for lightning speed
    if (typeof TagManager !== 'undefined' && TagManager.prototype.uploadFile) {
        const originalUploadFile = TagManager.prototype.uploadFile;
        
        TagManager.prototype.uploadFile = function(file) {
            console.log('🚀 Using LIGHTNING upload mode');
            
            const formData = new FormData();
            formData.append('file', file);
            
            // Show lightning-fast UI
            this.showUploadProgress('Lightning mode: Processing first 100 rows...');
            
            return fetch('/upload-lightning', {
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
                console.log('⚡ Lightning upload result:', data);
                
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Show success message
                this.showUploadSuccess(`⚡ Lightning upload complete in ${data.processing_time}s! Processed ${data.rows_processed} rows, stored ${data.rows_stored} to database.`);
                
                // Load tags immediately
                this.loadTags();
                
                return data;
            })
            .catch(error => {
                console.error('⚡ Lightning upload failed:', error);
                this.showUploadError(`Lightning upload failed: ${error.message}`);
                throw error;
            });
        };
        
        console.log('⚡ Lightning upload mode activated');
    }
})();
