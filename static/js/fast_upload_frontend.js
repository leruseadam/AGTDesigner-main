// Fast upload frontend modifications
// Add this to your main.js or include it separately

// Override the upload function to use the fast endpoint
if (typeof TagManager !== 'undefined') {
    // Store the original upload function
    TagManager.originalUploadFile = TagManager.uploadFile;
    
    // Replace with fast upload
    TagManager.uploadFile = async function(file) {
        const maxRetries = 2;
        let retryCount = 0;
        
        while (retryCount <= maxRetries) {
            try {
                console.log(`Starting FAST file upload (attempt ${retryCount + 1}):`, file.name, 'Size:', file.size, 'bytes');
                
                // Show Excel loading splash screen
                this.showExcelLoadingSplash(file.name);
                
                // Show loading state
                this.updateUploadUI(`Uploading ${file.name} (fast mode)...`);
                
                const formData = new FormData();
                formData.append('file', file);
                
                console.log('Sending FAST upload request...');
                
                // Create AbortController for timeout (increased timeout for large files)
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout for large files
                
                const response = await fetch('/upload-fast', {
                    method: 'POST',
                    body: formData,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                console.log('Fast upload response status:', response.status);
                
                let data;
                try {
                    data = await response.json();
                    console.log('Fast upload response data:', data);
                } catch (jsonError) {
                    console.error('Error parsing JSON response:', jsonError);
                    throw new Error('Invalid server response');
                }
                
                if (response.ok) {
                    // Fast upload successful
                    console.log('Fast upload successful:', data);
                    
                    // Hide loading splash
                    this.hideExcelLoadingSplash();
                    
                    // Update UI
                    this.updateUploadUI(`File uploaded successfully (${data.rows} rows)`);
                    
                    // Clear UI state for new file
                    this.clearUIStateForNewFile();
                    
                    // Show success message
                    this.showToast('success', `File uploaded successfully! ${data.rows} rows processed in ultra-fast mode.`);
                    
                    // Refresh the tag lists
                    await this.refreshTagLists();
                    
                    return data;
                } else {
                    // Upload failed
                    console.error('Fast upload failed:', data);
                    this.hideExcelLoadingSplash();
                    this.showToast('error', data.error || 'Upload failed');
                    throw new Error(data.error || 'Upload failed');
                }
                
            } catch (error) {
                console.error(`Fast upload attempt ${retryCount + 1} failed:`, error);
                
                if (retryCount < maxRetries) {
                    retryCount++;
                    console.log(`Retrying fast upload (attempt ${retryCount + 1})...`);
                    
                    // Wait before retry
                    await new Promise(resolve => setTimeout(resolve, 1000));
                } else {
                    // All retries failed, try original upload as fallback
                    console.log('Fast upload failed, trying original upload as fallback...');
                    this.hideExcelLoadingSplash();
                    
                    try {
                        return await this.originalUploadFile(file);
                    } catch (fallbackError) {
                        console.error('Fallback upload also failed:', fallbackError);
                        this.showToast('error', 'Upload failed. Please try again.');
                        throw fallbackError;
                    }
                }
            }
        }
    };
}

// Also override the enhanced-ui.js upload function
if (typeof handleFiles !== 'undefined') {
    // Store original function
    const originalHandleFiles = handleFiles;
    
    // Replace with fast version
    window.handleFiles = async function(files) {
        if (files.length > 0) {
            const file = files[0];
            if (currentFile) currentFile.textContent = file.name;
            if (currentFileInfo) currentFileInfo.style.display = 'block';
            
            // Update the file path container with the new file name
            const filePathContainer = document.querySelector('.file-path-container');
            const currentFileInfoElement = document.getElementById('currentFileInfo');
            if (currentFileInfoElement) {
                currentFileInfoElement.textContent = file.name;
            }
            
            // Animate the file info appearance
            if (currentFileInfo) {
                currentFileInfo.style.opacity = '0';
                setTimeout(() => {
                    currentFileInfo.style.transition = 'opacity 0.3s ease';
                    currentFileInfo.style.opacity = '1';
                }, 10);
            }

            // Show Excel loading splash screen for manual uploads
            if (typeof TagManager !== 'undefined' && TagManager.showExcelLoadingSplash) {
                TagManager.showExcelLoadingSplash(file.name);
            }

            // Handle file upload with FAST endpoint
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                TagManager.setLoading(true);
                
                // Clear UI state immediately when upload starts
                if (typeof TagManager !== 'undefined' && TagManager.clearUIStateForNewFile) {
                    TagManager.clearUIStateForNewFile(true); // Preserve filters during upload
                }
                
                const response = await fetch('/upload-fast', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if (response.ok) {
                    // File uploaded successfully
                    const filename = data.filename;
                    console.log(`Fast upload successful: ${filename}, ${data.rows} rows processed`);
                    console.log('Fast upload response data:', data);
                    
                    // Hide splash screen
                    if (typeof TagManager !== 'undefined' && TagManager.hideExcelLoadingSplash) {
                        TagManager.hideExcelLoadingSplash();
                    }
                    
                    // Update splash screen status
                    if (typeof TagManager !== 'undefined' && TagManager.updateExcelLoadingStatus) {
                        TagManager.updateExcelLoadingStatus('Processing complete!');
                    }
                    
                    // Add animation class to file path container
                    if (filePathContainer) {
                        filePathContainer.classList.add('file-loaded');
                        setTimeout(() => {
                            filePathContainer.classList.remove('file-loaded');
                        }, 600);
                    }
                    
                    // Show success feedback
                    if (fileDropZone) {
                        fileDropZone.style.borderColor = '#4facfe';
                        setTimeout(() => {
                            fileDropZone.style.borderColor = '';
                        }, 1000);
                    }
                    
                    // Refresh tag lists
                    if (typeof TagManager !== 'undefined' && TagManager.refreshTagLists) {
                        await TagManager.refreshTagLists();
                    }
                    
                    // Show success message
                    if (typeof TagManager !== 'undefined' && TagManager.showToast) {
                        TagManager.showToast('success', `File uploaded successfully! ${data.rows} rows processed in ultra-fast mode.`);
                    }
                    
                } else {
                    // Hide splash screen on error
                    if (typeof TagManager !== 'undefined' && TagManager.hideExcelLoadingSplash) {
                        TagManager.hideExcelLoadingSplash();
                    }
                    showToast("error", data.error || 'Upload failed');
                }
            } catch (error) {
                console.error('Fast upload error:', error);
                
                // Hide splash screen on error
                if (typeof TagManager !== 'undefined' && TagManager.hideExcelLoadingSplash) {
                    TagManager.hideExcelLoadingSplash();
                }
                
                showToast("error", `Upload failed: ${error.message}`);
            } finally {
                TagManager.setLoading(false);
            }
        }
    };
}

console.log('🚀 Fast upload frontend loaded! Using /upload-fast endpoint for maximum speed.');
