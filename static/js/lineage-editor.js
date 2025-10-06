/**
 * Fixed Strain Lineage Editor
 * Prevents modal from closing immediately
 */
class StrainLineageEditor {
    constructor() {
        this.isInitialized = false;
        this.isLoading = false;
        this.currentStrain = null;
        this.currentLineage = null;
        this.modal = null;
        this.modalElement = null;
        this.eventListenersAdded = false;
        this.userRequestedClose = false;
        this.modalState = 'closed';
        this.preventClose = false;
    }

    init() {
        console.log('StrainLineageEditor: Initializing...');
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeEditor());
        } else {
            this.initializeEditor();
        }
    }

    initializeEditor() {
        try {
            console.log('StrainLineageEditor: DOM ready, initializing editor...');
            
            // Check if modal element already exists
            this.modalElement = document.getElementById('strainLineageEditorModal');
            
            if (!this.modalElement) {
                console.log('StrainLineageEditor: Modal element not found, creating...');
                this.createModalElement();
            } else {
                console.log('StrainLineageEditor: Modal element found, reusing existing');
            }

            // Initialize Bootstrap modal with enhanced configuration
            if (typeof bootstrap !== 'undefined' && typeof bootstrap.Modal !== 'undefined') {
                this.modal = new bootstrap.Modal(this.modalElement, {
                    backdrop: 'static',
                    keyboard: false,
                    focus: true
                });
                
                // Add enhanced event listeners
                this.setupEventListeners();
                this.isInitialized = true;
                console.log('StrainLineageEditor: Successfully initialized');
            } else {
                console.error('StrainLineageEditor: Bootstrap not available');
                this.createFallbackModal();
            }
        } catch (error) {
            console.error('StrainLineageEditor: Initialization error:', error);
            this.createFallbackModal();
        }
    }

    createModalElement() {
        console.log('StrainLineageEditor: Creating modal element...');
        
        const modalHTML = `
            <div class="modal fade" id="strainLineageEditorModal" tabindex="-1" aria-labelledby="strainLineageEditorModalLabel" aria-hidden="true" data-bs-backdrop="static" data-bs-keyboard="false">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content glass-card">
                        <div class="modal-header border-0 bg-transparent">
                            <h5 class="modal-title text-white" id="strainLineageEditorModalLabel">Edit Strain Lineage</h5>
                            <button type="button" class="btn-close btn-close-white" id="lineageEditorCloseBtn" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div id="lineageEditorContent">
                                <div class="text-center">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                    <p class="mt-3 text-white-50">Loading lineage editor...</p>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer border-0 bg-transparent">
                            <button type="button" class="btn btn-glass" id="lineageEditorCancelBtn">Cancel</button>
                            <button type="button" class="btn btn-modern2" id="saveStrainLineageBtn">Save Changes</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modalElement = document.getElementById('strainLineageEditorModal');
    }

    setupEventListeners() {
        if (this.eventListenersAdded || !this.modalElement) return;

        console.log('StrainLineageEditor: Setting up event listeners...');

        // Save button
        const saveButton = document.getElementById('saveStrainLineageBtn');
        if (saveButton) {
            saveButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.saveChanges();
            });
        }

        // Close button (X)
        const closeButton = document.getElementById('lineageEditorCloseBtn');
        if (closeButton) {
            closeButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.userRequestedClose = true;
                this.closeModal();
            });
        }

        // Cancel button
        const cancelButton = document.getElementById('lineageEditorCancelBtn');
        if (cancelButton) {
            cancelButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.userRequestedClose = true;
                this.closeModal();
            });
        }

        // Modal events for Bootstrap modal
        if (this.modal) {
            this.modalElement.addEventListener('hide.bs.modal', (e) => {
                console.log('StrainLineageEditor: Modal hide event');
                // Prevent automatic hiding if we're in the middle of an operation
                if (this.isLoading || this.modalState === 'opening' || this.preventClose) {
                    e.preventDefault();
                    console.log('StrainLineageEditor: Prevented modal hide during loading/opening');
                    return false;
                }
            });

            this.modalElement.addEventListener('hidden.bs.modal', (e) => {
                console.log('StrainLineageEditor: Modal hidden event');
                this.cleanup();
            });

            this.modalElement.addEventListener('shown.bs.modal', (e) => {
                console.log('StrainLineageEditor: Modal shown event');
                this.onModalShown();
            });
        }

        // Prevent clicks on backdrop from closing modal
        this.modalElement.addEventListener('click', (e) => {
            if (e.target === this.modalElement) {
                e.preventDefault();
                e.stopPropagation();
                console.log('StrainLineageEditor: Prevented backdrop click');
            }
        });

        this.eventListenersAdded = true;
    }

    async openEditor(strainName, currentLineage) {
        console.log('StrainLineageEditor: Opening editor for', strainName, currentLineage);
        
        try {
            this.currentStrain = strainName;
            this.currentLineage = currentLineage;
            this.isLoading = true;
            this.preventClose = true;
            this.modalState = 'opening';

            // Wait for initialization
            await this.waitForInitialization();
            
            // Load editor content
            await this.loadEditorContent();
            
            // Show modal
            this.showModal();
            
        } catch (error) {
            console.error('StrainLineageEditor: Error opening editor:', error);
            this.handleError('Failed to open lineage editor: ' + error.message);
        }
    }

    async waitForInitialization() {
        let attempts = 0;
        while (!this.isInitialized && attempts < 10) {
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        if (!this.isInitialized) {
            throw new Error('Editor failed to initialize');
        }
    }

    async loadEditorContent() {
        console.log('StrainLineageEditor: Loading editor content...');
        
        try {
            // Ensure product database is enabled
            await this.ensureProductDatabaseEnabled();
            
            // Get strain product count
            const productCount = await this.getStrainProductCount(this.currentStrain);
            
            // Create editor HTML
            const editorHTML = this.createEditorHTML(productCount);
            
            // Update modal content
            const contentDiv = document.getElementById('lineageEditorContent');
            if (contentDiv) {
                contentDiv.innerHTML = editorHTML;
                this.initializeFormElements();
            }
            
        } catch (error) {
            console.error('StrainLineageEditor: Error loading content:', error);
            throw error;
        }
    }

    async ensureProductDatabaseEnabled() {
        try {
            const response = await fetch('/api/product-db/status');
            const data = await response.json();
            
            if (!data.enabled) {
                console.log('StrainLineageEditor: Enabling product database...');
                await fetch('/api/product-db/enable', { method: 'POST' });
            }
        } catch (error) {
            console.warn('StrainLineageEditor: Could not check/enable product database:', error);
        }
    }

    async getStrainProductCount(strainName) {
        try {
            const response = await fetch('/api/get-strain-product-count', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ strain_name: strainName })
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.count || 0;
            }
        } catch (error) {
            console.warn('StrainLineageEditor: Could not get strain product count:', error);
        }
        
        return 0;
    }

    createEditorHTML(productCount) {
        return `
            <div class="mb-3">
                <label class="form-label"><strong>Strain:</strong> ${this.escapeHtml(this.currentStrain)}</label>
            </div>
            <div class="mb-3">
                <label class="form-label"><strong>Current Lineage:</strong> ${this.escapeHtml(this.currentLineage || 'None')}</label>
            </div>
            <div class="mb-3">
                <label class="form-label"><strong>Products with this strain:</strong> ${productCount}</label>
            </div>
            <div class="mb-3">
                <label for="lineageSelect" class="form-label">Select New Lineage:</label>
                <select class="form-select" id="lineageSelect">
                    <option value="">-- Select Lineage --</option>
                    <option value="SATIVA">SATIVA</option>
                    <option value="INDICA">INDICA</option>
                    <option value="HYBRID">HYBRID</option>
                    <option value="HYBRID/SATIVA">HYBRID/SATIVA</option>
                    <option value="HYBRID/INDICA">HYBRID/INDICA</option>
                    <option value="CBD">CBD</option>
                    <option value="CBD_BLEND">CBD_BLEND</option>
                    <option value="MIXED">MIXED</option>
                    <option value="PARA">PARA</option>
                </select>
            </div>
            <div class="mb-3">
                <label for="customLineage" class="form-label">Or Enter Custom Lineage:</label>
                <input type="text" class="form-control" id="customLineage" placeholder="Enter custom lineage...">
            </div>
        `;
    }

    initializeFormElements() {
        // Set current lineage in select
        const lineageSelect = document.getElementById('lineageSelect');
        if (lineageSelect && this.currentLineage) {
            lineageSelect.value = this.currentLineage;
        }
    }

    showModal() {
        console.log('StrainLineageEditor: Showing modal...');
        
        if (this.modal) {
            try {
                this.modal.show();
                console.log('StrainLineageEditor: Bootstrap modal.show() completed');
            } catch (error) {
                console.error('StrainLineageEditor: Error in Bootstrap modal.show():', error);
            }
        } else {
            console.log('StrainLineageEditor: Using fallback modal');
            if (this.modalElement) {
                this.modalElement.style.display = 'block';
                this.modalElement.classList.add('show');
                this.onModalShown();
            }
        }
    }

    onModalShown() {
        console.log('StrainLineageEditor: Modal shown');
        this.isLoading = false;
        this.preventClose = false;
        this.modalState = 'open';
        document.body.style.overflow = 'hidden';
    }

    async saveChanges() {
        console.log('StrainLineageEditor: Saving changes...');
        
        const lineageSelect = document.getElementById('lineageSelect');
        const customLineage = document.getElementById('customLineage');
        
        if (!lineageSelect || !customLineage) {
            this.handleError('Form elements not found');
            return;
        }

        const newLineage = lineageSelect.value || customLineage.value.trim();
        
        if (!newLineage) {
            this.handleError('Please select or enter a lineage');
            return;
        }

        try {
            // Show saving state
            const saveButton = document.getElementById('saveStrainLineageBtn');
            if (saveButton) {
                saveButton.disabled = true;
                saveButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Saving...';
            }

            // Save lineage
            await this.saveLineage(newLineage);
            
            // Show success message
            this.showSuccess('Lineage updated successfully!');
            
            // Close modal after delay
            setTimeout(() => {
                this.closeModal();
            }, 1500);
            
        } catch (error) {
            console.error('StrainLineageEditor: Error saving changes:', error);
            this.handleError('Failed to save changes: ' + error.message);
            
            // Re-enable save button
            const saveButton = document.getElementById('saveStrainLineageBtn');
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.textContent = 'Save Changes';
            }
        }
    }

    async saveLineage(newLineage) {
        const response = await fetch('/api/set-strain-lineage', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                strain_name: this.currentStrain,
                lineage: newLineage
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to save lineage');
        }
        
        return await response.json();
    }

    closeModal() {
        console.log('StrainLineageEditor: Closing enhanced modal...');
        this.userRequestedClose = true;
        this.preventClose = false;
        
        if (this.modal) {
            this.modal.hide();
        } else if (this.modalElement) {
            this.modalElement.style.display = 'none';
            this.modalElement.classList.remove('show');
            this.cleanup();
        }
    }

    cleanup() {
        console.log('StrainLineageEditor: Cleaning up enhanced editor...');
        this.isLoading = false;
        this.preventClose = false;
        this.modalState = 'closed';
        this.userRequestedClose = false;
        document.body.style.overflow = '';
        
        // Clear validation messages
        const validationDiv = document.getElementById('validationMessages');
        if (validationDiv) {
            validationDiv.innerHTML = '';
        }
    }

    handleError(message) {
        console.error('StrainLineageEditor Error:', message);
        
        // Create a toast notification for errors
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-danger border-0 position-fixed';
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-exclamation-triangle me-2"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Show toast
        const toastInstance = new bootstrap.Toast(toast, { delay: 5000 });
        toastInstance.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        });
    }

    showSuccess(message) {
        console.log('StrainLineageEditor Success:', message);
        this.showEnhancedSuccess(message);
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Enhanced utility methods
    async ensureProductDatabaseEnabled() {
        try {
            const response = await fetch('/api/product-db/status');
            const data = await response.json();
            
            if (!data.enabled) {
                console.log('StrainLineageEditor: Enabling product database...');
                await fetch('/api/product-db/enable', { method: 'POST' });
            }
        } catch (error) {
            console.warn('StrainLineageEditor: Could not check/enable product database:', error);
        }
    }

    showModal() {
        console.log('StrainLineageEditor: Showing enhanced modal...');
        
        if (this.modal) {
            try {
                this.modal.show();
                console.log('StrainLineageEditor: Bootstrap modal.show() completed');
            } catch (error) {
                console.error('StrainLineageEditor: Error in Bootstrap modal.show():', error);
            }
        } else {
            console.log('StrainLineageEditor: Using fallback modal');
            if (this.modalElement) {
                this.modalElement.style.display = 'block';
                this.modalElement.classList.add('show');
                this.onModalShown();
            }
        }
    }

    onModalShown() {
        console.log('StrainLineageEditor: Enhanced modal shown');
        this.isLoading = false;
        this.preventClose = false;
        this.modalState = 'open';
        document.body.style.overflow = 'hidden';
        
        // Focus on the first form element
        const firstInput = document.getElementById('lineageSelect') || document.getElementById('customLineage');
        if (firstInput) {
            firstInput.focus();
        }
    }

    createFallbackModal() {
        console.log('StrainLineageEditor: Creating fallback modal...');
        
        const fallbackHTML = `
            <div id="strainLineageEditorModal" class="fallback-modal" style="display: none;">
                <div class="fallback-modal-overlay">
                    <div class="fallback-modal-content">
                        <div class="fallback-modal-header">
                            <h5>Edit Strain Lineage (Fallback Mode)</h5>
                            <button type="button" class="fallback-modal-close" id="lineageEditorCloseBtn" aria-label="Close">&times;</button>
                        </div>
                        <div class="fallback-modal-body" id="lineageEditorContent">
                            <div class="text-center">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p class="mt-3">Loading lineage editor...</p>
                            </div>
                        </div>
                        <div class="fallback-modal-footer">
                            <button type="button" class="btn btn-glass" id="lineageEditorCancelBtn">Cancel</button>
                            <button type="button" class="btn btn-modern2" id="saveStrainLineageBtn">Save Changes</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', fallbackHTML);
        this.modalElement = document.getElementById('strainLineageEditorModal');
    }
}

// Initialize the enhanced editor when the script loads
if (typeof window !== 'undefined') {
    window.strainLineageEditor = new StrainLineageEditor();
    window.strainLineageEditor.init();
}
