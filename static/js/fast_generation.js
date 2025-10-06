// Fast Generation Frontend
// Optimized for custom PythonAnywhere plan
(function() {
    'use strict';
    
    // Override the generation function for fast processing
    if (typeof TagManager !== 'undefined' && TagManager.prototype.generateLabels) {
        const originalGenerateLabels = TagManager.prototype.generateLabels;
        
        TagManager.prototype.generateLabels = function(templateType, scaleFactor) {
            console.log('⚡ Using FAST generation mode');
            
            const selectedTags = this.getSelectedTags();
            if (!selectedTags || selectedTags.length === 0) {
                this.showError('No tags selected for generation');
                return;
            }
            
            // Show fast generation UI
            this.showGenerationProgress('Fast generation: Processing with 6 web workers...');
            
            const requestData = {
                template_type: templateType,
                scale_factor: scaleFactor,
                selected_tags: selectedTags
            };
            
            // Try fast generation first
            return fetch('/api/generate-fast', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData),
                timeout: 30000  // 30 second timeout
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.blob();
            })
            .then(blob => {
                console.log('⚡ Fast generation result:', blob.size, 'bytes');
                
                // Create download link
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `AGT_Fast_${templateType}_${selectedTags.length}tags_${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.docx`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                // Show success message
                this.showGenerationSuccess(`⚡ Fast generation complete! Generated ${selectedTags.length} tags.`);
                
                return blob;
            })
            .catch(error => {
                console.error('⚡ Fast generation failed:', error);
                // Try parallel generation as fallback
                console.log('⚡ Trying parallel generation...');
                return this.tryParallelGeneration(templateType, scaleFactor, selectedTags);
            });
        };
        
        // Add parallel generation fallback
        TagManager.prototype.tryParallelGeneration = function(templateType, scaleFactor, selectedTags) {
            this.showGenerationProgress('Parallel generation: Using multiple workers...');
            
            const requestData = {
                template_type: templateType,
                scale_factor: scaleFactor,
                selected_tags: selectedTags
            };
            
            return fetch('/api/generate-parallel', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData),
                timeout: 60000  // 60 second timeout for parallel processing
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.blob();
            })
            .then(blob => {
                console.log('⚡ Parallel generation result:', blob.size, 'bytes');
                
                // Create download link
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `AGT_Parallel_${templateType}_${selectedTags.length}tags_${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.docx`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                this.showGenerationSuccess(`⚡ Parallel generation complete! Generated ${selectedTags.length} tags.`);
                
                return blob;
            })
            .catch(error => {
                console.error('⚡ Parallel generation failed:', error);
                this.showGenerationError(`Both fast and parallel generation failed: ${error.message}`);
                throw error;
            });
        };
        
        // Add progress and success methods if they don't exist
        if (!TagManager.prototype.showGenerationProgress) {
            TagManager.prototype.showGenerationProgress = function(message) {
                console.log('⚡ Generation Progress:', message);
                // You can add UI feedback here
            };
        }
        
        if (!TagManager.prototype.showGenerationSuccess) {
            TagManager.prototype.showGenerationSuccess = function(message) {
                console.log('⚡ Generation Success:', message);
                // You can add UI feedback here
            };
        }
        
        if (!TagManager.prototype.showGenerationError) {
            TagManager.prototype.showGenerationError = function(message) {
                console.error('⚡ Generation Error:', message);
                // You can add UI feedback here
            };
        }
        
        console.log('⚡ Fast generation mode activated');
        console.log('📊 Plan specs: 6 web workers, 20GB disk, Postgres enabled');
    }
})();
