/**
 * Enhanced Strain Lineage Editor
 * Improved UI/UX, error handling, validation, and functionality
 */
class EnhancedStrainLineageEditor {
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
        this.lineageHistory = [];
        this.validationErrors = [];
    }

    init() {
        console.log('EnhancedStrainLineageEditor: Initializing enhanced editor...');
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeEditor());
        } else {
            this.initializeEditor();
        }
    }

    initializeEditor() {
        try {
            console.log('EnhancedStrainLineageEditor: DOM ready, initializing enhanced editor...');
            
            // Check if modal element already exists
            this.modalElement = document.getElementById('strainLineageEditorModal');
            
            if (!this.modalElement) {
                console.log('EnhancedStrainLineageEditor: Modal element not found, creating enhanced modal...');
                this.createEnhancedModalElement();
            } else {
                console.log('EnhancedStrainLineageEditor: Modal element found, reusing existing');
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
                console.log('EnhancedStrainLineageEditor: Enhanced editor successfully initialized');
            } else {
                console.error('EnhancedStrainLineageEditor: Bootstrap not available');
                this.createFallbackModal();
            }
        } catch (error) {
            console.error('EnhancedStrainLineageEditor: Initialization error:', error);
            this.createFallbackModal();
        }
    }

    createEnhancedModalElement() {
        console.log('EnhancedStrainLineageEditor: Creating enhanced modal element...');
        
        const modalHTML = `
            <div class="modal fade" id="strainLineageEditorModal" tabindex="-1" aria-labelledby="strainLineageEditorModalLabel" aria-hidden="true" data-bs-backdrop="static" data-bs-keyboard="false">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title" id="strainLineageEditorModalLabel">
                                <i class="fas fa-dna me-2"></i>Edit Strain Lineage
                            </h5>
                            <button type="button" class="btn-close btn-close-white" id="lineageEditorCloseBtn" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div id="lineageEditorContent">
                                <div class="text-center py-4">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                    <p class="mt-2 text-muted">Loading enhanced lineage editor...</p>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-outline-secondary" id="lineageEditorCancelBtn">
                                <i class="fas fa-times me-1"></i>Cancel
                            </button>
                            <button type="button" class="btn btn-primary" id="saveStrainLineageBtn">
                                <i class="fas fa-save me-1"></i>Save Changes
                            </button>
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

        console.log('EnhancedStrainLineageEditor: Setting up enhanced event listeners...');

        // Save button with enhanced functionality
        const saveButton = document.getElementById('saveStrainLineageBtn');
        if (saveButton) {
            saveButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.saveChanges();
            });
        }

        // Close button (X) with confirmation
        const closeButton = document.getElementById('lineageEditorCloseBtn');
        if (closeButton) {
            closeButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.confirmClose();
            });
        }

        // Cancel button with confirmation
        const cancelButton = document.getElementById('lineageEditorCancelBtn');
        if (cancelButton) {
            cancelButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.confirmClose();
            });
        }

        // Enhanced modal events for Bootstrap modal
        if (this.modal) {
            this.modalElement.addEventListener('hide.bs.modal', (e) => {
                console.log('EnhancedStrainLineageEditor: Modal hide event');
                // Prevent automatic hiding if we're in the middle of an operation
                if (this.isLoading || this.modalState === 'opening' || this.preventClose) {
                    e.preventDefault();
                    console.log('EnhancedStrainLineageEditor: Prevented modal hide during loading/opening');
                    return false;
                }
            });

            this.modalElement.addEventListener('hidden.bs.modal', (e) => {
                console.log('EnhancedStrainLineageEditor: Modal hidden event');
                this.cleanup();
            });

            this.modalElement.addEventListener('shown.bs.modal', (e) => {
                console.log('EnhancedStrainLineageEditor: Modal shown event');
                this.onModalShown();
            });
        }

        // Prevent clicks on backdrop from closing modal
        this.modalElement.addEventListener('click', (e) => {
            if (e.target === this.modalElement) {
                e.preventDefault();
                e.stopPropagation();
                console.log('EnhancedStrainLineageEditor: Prevented backdrop click');
            }
        });

        this.eventListenersAdded = true;
    }

    confirmClose() {
        if (this.hasUnsavedChanges()) {
            if (confirm('You have unsaved changes. Are you sure you want to close without saving?')) {
                this.userRequestedClose = true;
                this.closeModal();
            }
        } else {
            this.userRequestedClose = true;
            this.closeModal();
        }
    }

    hasUnsavedChanges() {
        const lineageSelect = document.getElementById('lineageSelect');
        const customLineage = document.getElementById('customLineage');
        
        if (!lineageSelect || !customLineage) return false;
        
        const newLineage = lineageSelect.value || customLineage.value.trim();
        return newLineage !== this.currentLineage;
    }

    async openEditor(strainName, currentLineage) {
        console.log('EnhancedStrainLineageEditor: Opening enhanced editor for', strainName, currentLineage);
        
        try {
            this.currentStrain = strainName;
            this.currentLineage = currentLineage;
            this.isLoading = true;
            this.preventClose = true;
            this.modalState = 'opening';

            // Wait for initialization
            await this.waitForInitialization();
            
            // Load enhanced editor content
            await this.loadEnhancedEditorContent();
            
            // Show modal
            this.showModal();
            
        } catch (error) {
            console.error('EnhancedStrainLineageEditor: Error opening enhanced editor:', error);
            this.handleError('Failed to open enhanced lineage editor: ' + error.message);
        }
    }

    async waitForInitialization() {
        let attempts = 0;
        while (!this.isInitialized && attempts < 10) {
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }
        
        if (!this.isInitialized) {
            throw new Error('Enhanced editor failed to initialize');
        }
    }

    async loadEnhancedEditorContent() {
        console.log('EnhancedStrainLineageEditor: Loading enhanced editor content...');
        
        try {
            // Ensure product database is enabled
            await this.ensureProductDatabaseEnabled();
            
            // Get comprehensive strain information
            const strainInfo = await this.getStrainInfo(this.currentStrain);
            
            // Create enhanced editor HTML
            const editorHTML = this.createEnhancedEditorHTML(strainInfo);
            
            // Update modal content
            const contentDiv = document.getElementById('lineageEditorContent');
            if (contentDiv) {
                contentDiv.innerHTML = editorHTML;
                this.initializeEnhancedFormElements();
                this.setupFormValidation();
            }
            
        } catch (error) {
            console.error('EnhancedStrainLineageEditor: Error loading enhanced content:', error);
            throw error;
        }
    }

    async getStrainInfo(strainName) {
        try {
            // Get product count
            const countResponse = await fetch('/api/get-strain-product-count', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ strain_name: strainName })
            });
            
            let productCount = 0;
            if (countResponse.ok) {
                const countData = await countResponse.json();
                productCount = countData.count || 0;
            }

            // Get vendor information
            const vendorResponse = await fetch('/api/vendor-strain-browser');
            let vendors = [];
            if (vendorResponse.ok) {
                const vendorData = await vendorResponse.json();
                if (vendorData.strains) {
                    const strainData = vendorData.strains.find(s => s.strain_name === strainName);
                    if (strainData) {
                        vendors = strainData.vendors ? strainData.vendors.split(',') : [];
                    }
                }
            }

            return {
                productCount,
                vendors,
                currentLineage: this.currentLineage
            };
            
        } catch (error) {
            console.warn('EnhancedStrainLineageEditor: Could not get comprehensive strain info:', error);
            return {
                productCount: 0,
                vendors: [],
                currentLineage: this.currentLineage
            };
        }
    }

    createEnhancedEditorHTML(strainInfo) {
        const { productCount, vendors, currentLineage } = strainInfo;
        
        return `
            <div class="row">
                <div class="col-md-8">
                    <!-- Main Lineage Editor -->
                    <div class="card border-0 shadow-sm">
                        <div class="card-header bg-light">
                            <h6 class="mb-0"><i class="fas fa-edit me-2"></i>Lineage Information</h6>
                        </div>
                        <div class="card-body">
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <label class="form-label fw-bold text-primary">Strain Name:</label>
                                    <div class="form-control-plaintext">${this.escapeHtml(this.currentStrain)}</div>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label fw-bold text-primary">Current Lineage:</label>
                                    <div class="form-control-plaintext">
                                        <span class="badge bg-secondary">${this.escapeHtml(currentLineage || 'None')}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mb-3">
                                <label for="lineageSelect" class="form-label fw-bold">Select New Lineage:</label>
                                <select class="form-select form-select-lg" id="lineageSelect">
                                    <option value="">-- Select Lineage --</option>
                                    <option value="SATIVA" class="text-success">🌿 SATIVA</option>
                                    <option value="INDICA" class="text-info">🍃 INDICA</option>
                                    <option value="HYBRID" class="text-warning">🌱 HYBRID</option>
                                    <option value="HYBRID/SATIVA" class="text-success">🌿 HYBRID/SATIVA</option>
                                    <option value="HYBRID/INDICA" class="text-info">🍃 HYBRID/INDICA</option>
                                    <option value="CBD" class="text-primary">💚 CBD</option>
                                    <option value="CBD_BLEND" class="text-primary">💚 CBD BLEND</option>
                                    <option value="MIXED" class="text-secondary">🔀 MIXED</option>
                                    <option value="PARA" class="text-dark">⚫ PARA</option>
                                </select>
                            </div>
                            
                            <div class="mb-3">
                                <label for="customLineage" class="form-label fw-bold">Or Enter Custom Lineage:</label>
                                <input type="text" class="form-control form-control-lg" id="customLineage" 
                                       placeholder="Enter custom lineage (e.g., RUNTZ, OG KUSH, etc.)...">
                                <div class="form-text">Custom lineages will be stored exactly as entered</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <!-- Sidebar Information -->
                    <div class="card border-0 shadow-sm mb-3">
                        <div class="card-header bg-info text-white">
                            <h6 class="mb-0"><i class="fas fa-info-circle me-2"></i>Strain Details</h6>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <label class="form-label fw-bold">Products Affected:</label>
                                <div class="h4 text-primary mb-0">${productCount}</div>
                                <small class="text-muted">products will be updated</small>
                            </div>
                            
                            ${vendors.length > 0 ? `
                            <div class="mb-3">
                                <label class="form-label fw-bold">Vendors:</label>
                                <div class="d-flex flex-wrap gap-1">
                                    ${vendors.map(vendor => `<span class="badge bg-outline-secondary">${this.escapeHtml(vendor.trim())}</span>`).join('')}
                                </div>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <!-- Lineage History -->
                    <div class="card border-0 shadow-sm">
                        <div class="card-header bg-warning text-dark">
                            <h6 class="mb-0"><i class="fas fa-history me-2"></i>Lineage History</h6>
                        </div>
                        <div class="card-body">
                            <div id="lineageHistoryContent">
                                <p class="text-muted small">No previous changes recorded</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Validation Messages -->
            <div id="validationMessages" class="mt-3"></div>
        `;
    }

    initializeEnhancedFormElements() {
        // Set current lineage in select
        const lineageSelect = document.getElementById('lineageSelect');
        if (lineageSelect && this.currentLineage) {
            lineageSelect.value = this.currentLineage;
        }

        // Add event listeners for form changes
        const customLineage = document.getElementById('customLineage');
        if (customLineage) {
            customLineage.addEventListener('input', () => {
                // Clear select when custom lineage is entered
                if (lineageSelect) {
                    lineageSelect.value = '';
                }
                this.validateForm();
            });
        }

        if (lineageSelect) {
            lineageSelect.addEventListener('change', () => {
                // Clear custom lineage when select is used
                if (customLineage) {
                    customLineage.value = '';
                }
                this.validateForm();
            });
        }
    }

    setupFormValidation() {
        this.validateForm();
    }

    validateForm() {
        this.validationErrors = [];
        const lineageSelect = document.getElementById('lineageSelect');
        const customLineage = document.getElementById('customLineage');
        const validationDiv = document.getElementById('validationMessages');
        
        if (!lineageSelect || !customLineage || !validationDiv) return;

        const selectedLineage = lineageSelect.value;
        const customValue = customLineage.value.trim();
        const newLineage = selectedLineage || customValue;

        // Clear previous validation messages
        validationDiv.innerHTML = '';

        // Validation rules
        if (!newLineage) {
            this.validationErrors.push('Please select or enter a lineage');
        }

        if (customValue && customValue.length < 2) {
            this.validationErrors.push('Custom lineage must be at least 2 characters long');
        }

        if (customValue && customValue.length > 50) {
            this.validationErrors.push('Custom lineage must be 50 characters or less');
        }

        // Display validation messages
        if (this.validationErrors.length > 0) {
            const errorHTML = this.validationErrors.map(error => 
                `<div class="alert alert-danger alert-sm"><i class="fas fa-exclamation-triangle me-2"></i>${error}</div>`
            ).join('');
            validationDiv.innerHTML = errorHTML;
        } else {
            validationDiv.innerHTML = '<div class="alert alert-success alert-sm"><i class="fas fa-check-circle me-2"></i>Form is valid</div>';
        }

        // Update save button state
        const saveButton = document.getElementById('saveStrainLineageBtn');
        if (saveButton) {
            saveButton.disabled = this.validationErrors.length > 0;
        }
    }

    async saveChanges() {
        console.log('EnhancedStrainLineageEditor: Saving enhanced changes...');
        
        // Validate form before saving
        this.validateForm();
        if (this.validationErrors.length > 0) {
            this.showValidationError('Please fix the validation errors before saving');
            return;
        }
        
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
            // Show enhanced saving state
            const saveButton = document.getElementById('saveStrainLineageBtn');
            if (saveButton) {
                saveButton.disabled = true;
                saveButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Saving...';
            }

            // Save lineage
            const result = await this.saveLineage(newLineage);
            
            // Add to history
            this.addToHistory(newLineage, result.products_updated);
            
            // Show enhanced success message
            this.showEnhancedSuccess(`Lineage updated successfully! ${result.products_updated} products affected.`);
            
            // Update current lineage
            this.currentLineage = newLineage;
            
            // Close modal after delay
            setTimeout(() => {
                this.closeModal();
            }, 2000);
            
        } catch (error) {
            console.error('EnhancedStrainLineageEditor: Error saving enhanced changes:', error);
            this.handleError('Failed to save changes: ' + error.message);
            
            // Re-enable save button
            const saveButton = document.getElementById('saveStrainLineageBtn');
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.innerHTML = '<i class="fas fa-save me-1"></i>Save Changes';
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
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to save lineage');
        }
        
        return await response.json();
    }

    addToHistory(newLineage, productsUpdated) {
        const historyEntry = {
            timestamp: new Date().toLocaleString(),
            lineage: newLineage,
            productsUpdated: productsUpdated
        };
        
        this.lineageHistory.unshift(historyEntry);
        
        // Keep only last 10 entries
        if (this.lineageHistory.length > 10) {
            this.lineageHistory = this.lineageHistory.slice(0, 10);
        }
        
        this.updateHistoryDisplay();
    }

    updateHistoryDisplay() {
        const historyContent = document.getElementById('lineageHistoryContent');
        if (!historyContent) return;
        
        if (this.lineageHistory.length === 0) {
            historyContent.innerHTML = '<p class="text-muted small">No previous changes recorded</p>';
            return;
        }
        
        const historyHTML = this.lineageHistory.map(entry => `
            <div class="border-bottom pb-2 mb-2">
                <div class="d-flex justify-content-between align-items-start">
                    <span class="badge bg-primary">${this.escapeHtml(entry.lineage)}</span>
                    <small class="text-muted">${entry.timestamp}</small>
                </div>
                <div class="small text-muted">${entry.productsUpdated} products updated</div>
            </div>
        `).join('');
        
        historyContent.innerHTML = historyHTML;
    }

    showValidationError(message) {
        const validationDiv = document.getElementById('validationMessages');
        if (validationDiv) {
            validationDiv.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-triangle me-2"></i>${message}</div>`;
        }
    }

    showEnhancedSuccess(message) {
        console.log('EnhancedStrainLineageEditor Success:', message);
        
        // Create a toast notification
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-success border-0 position-fixed';
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-check-circle me-2"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Show toast
        const toastInstance = new bootstrap.Toast(toast, { delay: 3000 });
        toastInstance.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        });
    }

    closeModal() {
        console.log('EnhancedStrainLineageEditor: Closing enhanced modal...');
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
        console.log('EnhancedStrainLineageEditor: Cleaning up enhanced editor...');
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
        console.error('EnhancedStrainLineageEditor Error:', message);
        
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
        console.log('EnhancedStrainLineageEditor Success:', message);
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
                console.log('EnhancedStrainLineageEditor: Enabling product database...');
                await fetch('/api/product-db/enable', { method: 'POST' });
            }
        } catch (error) {
            console.warn('EnhancedStrainLineageEditor: Could not check/enable product database:', error);
        }
    }

    showModal() {
        console.log('EnhancedStrainLineageEditor: Showing enhanced modal...');
        
        if (this.modal) {
            try {
                this.modal.show();
                console.log('EnhancedStrainLineageEditor: Bootstrap modal.show() completed');
            } catch (error) {
                console.error('EnhancedStrainLineageEditor: Error in Bootstrap modal.show():', error);
            }
        } else {
            console.log('EnhancedStrainLineageEditor: Using fallback modal');
            if (this.modalElement) {
                this.modalElement.style.display = 'block';
                this.modalElement.classList.add('show');
                this.onModalShown();
            }
        }
    }

    onModalShown() {
        console.log('EnhancedStrainLineageEditor: Enhanced modal shown');
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
        console.log('EnhancedStrainLineageEditor: Creating fallback modal...');
        
        const fallbackHTML = `
            <div id="strainLineageEditorModal" class="fallback-modal" style="display: none;">
                <div class="fallback-modal-overlay">
                    <div class="fallback-modal-content">
                        <div class="fallback-modal-header">
                            <h5>Edit Strain Lineage (Fallback Mode)</h5>
                            <button type="button" class="fallback-modal-close" id="lineageEditorCloseBtn">&times;</button>
                        </div>
                        <div class="fallback-modal-body" id="lineageEditorContent">
                            <p>Loading lineage editor...</p>
                        </div>
                        <div class="fallback-modal-footer">
                            <button type="button" class="btn btn-secondary" id="lineageEditorCancelBtn">Cancel</button>
                            <button type="button" class="btn btn-primary" id="saveStrainLineageBtn">Save Changes</button>
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
    window.enhancedStrainLineageEditor = new EnhancedStrainLineageEditor();
    window.enhancedStrainLineageEditor.init();
}
