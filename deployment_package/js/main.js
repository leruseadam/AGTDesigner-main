// Performance optimization utilities
const performanceUtils = {
    // Debounce function for search inputs
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Throttle function for scroll events
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    },
    
    // Batch DOM updates to minimize reflows
    batchDOMUpdate(callback) {
        return requestAnimationFrame(() => {
            callback();
        });
    },
    
    // Performance monitoring
    startTiming: () => performance.now(),
    endTiming: (start, operation) => {
        const duration = performance.now() - start;
        if (duration > 16) { // Log if slower than 60fps
            console.warn(`Performance: ${operation} took ${duration.toFixed(2)}ms`);
        }
        return duration;
    }
};

// Global error handler to prevent window from exiting
window.addEventListener('error', function(event) {
    console.error('Global error caught:', event.error);
    console.error('Error at:', event.filename, 'line:', event.lineno, 'column:', event.colno);
    event.preventDefault();
    return false;
});

// Global unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    event.preventDefault();
});

// Toast fallback: define Toast if not present
if (typeof Toast === 'undefined') {
  window.Toast = {
    show: (type, msg) => {
      if (type === 'error') {
        alert('Error: ' + msg);
      } else {
        // Don't show alerts for success/info messages to prevent popups
        console.log(`Toast (${type}): ${msg}`);
      }
    }
  };
}

// Classic types that should show "Lineage" instead of "Brand"
const CLASSIC_TYPES = [
    "flower", "pre-roll", "concentrate", "infused pre-roll", 
    "solventless concentrate", "vape cartridge", "rso/co2 tankers"
];

// Add this near the top of the file, before any code that uses it
// Product type normalization mapping (same as backend TYPE_OVERRIDES)
const PRODUCT_TYPE_OVERRIDES = {
  "all-in-one": "vape cartridge",
  "rosin": "concentrate",
  "mini buds": "flower",
  "bud": "flower",
  "pre-roll": "pre-roll",
  "alcohol/ethanol extract": "rso/co2 tankers",
  "Alcohol/Ethanol Extract": "rso/co2 tankers",
  "alcohol ethanol extract": "rso/co2 tankers",
  "Alcohol Ethanol Extract": "rso/co2 tankers",
  "c02/ethanol extract": "rso/co2 tankers",
  "CO2 Concentrate": "rso/co2 tankers",
  "co2 concentrate": "rso/co2 tankers"
};

// Function to normalize product types (same as backend)

    // Detect if running on PythonAnywhere
    function isPythonAnywhere() {
        return window.location.hostname.includes('pythonanywhere.com');
    }
    
    // Choose upload endpoint based on environment
    function getUploadEndpoint() {
        if (isPythonAnywhere()) {
            return '/upload-pythonanywhere';
        } else {
            return '/upload';
        }
    }
function normalizeProductType(productType) {
  if (!productType) return productType;
  const normalized = PRODUCT_TYPE_OVERRIDES[productType.toLowerCase()];
  return normalized || productType;
}

// Global function to restore body scroll after modal closes
function restoreBodyScroll() {
  document.body.style.overflow = '';
  document.body.classList.remove('modal-open');
  document.body.style.paddingRight = '';
  document.body.style.pointerEvents = '';
}

// Function to open strain lineage editor
async function openStrainLineageEditor() {
  try {
    // Show loading state
    const loadingModal = document.createElement('div');
    loadingModal.className = 'modal fade';
    loadingModal.id = 'loadingModal';
    loadingModal.innerHTML = `
      <div class="modal-dialog modal-sm">
        <div class="modal-content">
          <div class="modal-body text-center">
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading strains from database...</p>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(loadingModal);
    
    const loadingInstance = new bootstrap.Modal(loadingModal);
    loadingInstance.show();
    
    // Add timeout protection with shorter timeout
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => {
        // Ensure loading modal is hidden on timeout
        if (loadingInstance) {
          loadingInstance.hide();
        }
        if (loadingModal && loadingModal.parentNode) {
          loadingModal.parentNode.removeChild(loadingModal);
        }
        reject(new Error('Request timed out after 10 seconds'));
      }, 10000); // 10 second timeout
    });
    
    // Fetch all strains from the master database with timeout
    const fetchPromise = fetch('/api/get-all-strains');
    const response = await Promise.race([fetchPromise, timeoutPromise]);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch strains from database: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    
    // Hide loading modal and ensure it's completely removed
    if (loadingInstance) {
      loadingInstance.hide();
    }
    if (loadingModal && loadingModal.parentNode) {
      loadingModal.parentNode.removeChild(loadingModal);
    }
    
    // Ensure any remaining loading states are cleared
    const remainingLoadingModals = document.querySelectorAll('.modal[id*="loading"]');
    remainingLoadingModals.forEach(modal => {
      const instance = bootstrap.Modal.getInstance(modal);
      if (instance) {
        instance.hide();
      }
      if (modal.parentNode) {
        modal.parentNode.removeChild(modal);
      }
    });
    
    if (!data.success) {
      throw new Error(data.error || 'Failed to load strains');
    }
    
    const strains = data.strains;
    
    if (strains.length === 0) {
      alert('No strains found in the master database.');
      return;
    }
    
    // Clean up any existing strain selection modal first
    const existingModal = document.getElementById('strainSelectionModal');
    if (existingModal) {
      console.log('Removing existing strain selection modal');
      const existingModalInstance = bootstrap.Modal.getInstance(existingModal);
      if (existingModalInstance) {
        existingModalInstance.dispose();
      }
      existingModal.remove();
    }
    
    // Create a strain selection modal with search functionality
    console.log('Creating strain selection modal with', strains.length, 'strains');
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'strainSelectionModal';
    modal.setAttribute('data-bs-backdrop', 'static');
    modal.setAttribute('data-bs-keyboard', 'false');
    modal.innerHTML = `
      <div class="modal-backdrop fade show" style="z-index: 1050;"></div>
      <div class="modal-dialog modal-lg" style="z-index: 1055;">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Choose a strain to edit lineage for</h5>
            <button type="button" class="btn-close" id="strainSelectionCloseBtn" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <p class="text-muted mb-3">Choose a strain to edit lineage for ALL products with that strain in the master database:</p>
            
            <!-- Search Box -->
            <div class="mb-3">
              <div class="input-group">
                <span class="input-group-text">
                  <i class="fas fa-search"></i>
                </span>
                <input type="text" class="form-control" id="strainSearchInput" 
                       placeholder="Search strains by name..." 
                       autocomplete="off">
                <button class="btn btn-outline-secondary" type="button" id="clearStrainSearch">
                  Clear
                </button>
              </div>
              <div class="form-text">
                <small class="text-muted">
                  <span id="strainSearchResults">Showing ${strains.length} strains</span>
                </small>
              </div>
            </div>
            
            <div class="list-group" id="strainListContainer">
              ${strains.map(strain => `
                <button type="button" class="list-group-item list-group-item-action strain-item" 
                        data-strain-name="${strain.strain_name.toLowerCase()}"
                        onclick="selectStrainForEditing('${strain.strain_name.replace(/'/g, "\\'")}', '${strain.current_lineage}')">
                  <div class="d-flex justify-content-between align-items-start">
                    <div>
                      <strong class="strain-name">${strain.strain_name}</strong>
                      <br>
                      <small class="text-muted">
                        Current: ${strain.current_lineage} | 
                        Products: ${strain.total_occurrences} | 
                        Last seen: ${new Date(strain.last_seen_date).toLocaleDateString()}
                      </small>
                    </div>
                    <span class="badge bg-primary">${strain.current_lineage}</span>
                  </div>
                </button>
              `).join('')}
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" id="strainSelectionCancelBtn">Cancel</button>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    console.log('Modal added to DOM, modal element:', modal);
    
    // Add event listeners for close buttons
    const closeBtn = document.getElementById('strainSelectionCloseBtn');
    const cancelBtn = document.getElementById('strainSelectionCancelBtn');
    
    if (closeBtn) {
      closeBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('Strain selection close button clicked');
        const modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
          modalInstance.hide();
        }
      });
    }
    
    if (cancelBtn) {
      cancelBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('Strain selection cancel button clicked');
        const modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
          modalInstance.hide();
        }
      });
    }
    
    // Add search functionality
    const searchInput = document.getElementById('strainSearchInput');
    const clearSearchBtn = document.getElementById('clearStrainSearch');
    const strainItems = document.querySelectorAll('.strain-item');
    const resultsCounter = document.getElementById('strainSearchResults');
    
    // Search function
    function filterStrains(searchTerm) {
      const term = searchTerm.toLowerCase().trim();
      let visibleCount = 0;
      
      strainItems.forEach(item => {
        const strainName = item.getAttribute('data-strain-name');
        const strainNameElement = item.querySelector('.strain-name');
        const originalText = strainNameElement.textContent;
        
        if (term === '' || strainName.includes(term)) {
          item.style.display = 'block';
          visibleCount++;
          
          // Highlight matching text if there's a search term
          if (term !== '') {
            const regex = new RegExp(`(${term})`, 'gi');
            strainNameElement.innerHTML = originalText.replace(regex, '<mark>$1</mark>');
          } else {
            strainNameElement.innerHTML = originalText;
          }
        } else {
          item.style.display = 'none';
        }
      });
      
      // Update results counter
      resultsCounter.textContent = `Showing ${visibleCount} of ${strains.length} strains`;
      
      // Show "no results" message if needed
      if (visibleCount === 0 && term !== '') {
        const noResults = document.createElement('div');
        noResults.className = 'text-center text-muted py-3';
        noResults.innerHTML = `
          <i class="fas fa-search me-2"></i>
          No strains found matching "${searchTerm}"
        `;
        
        const container = document.getElementById('strainListContainer');
        const existingNoResults = container.querySelector('.no-results-message');
        if (!existingNoResults) {
          noResults.classList.add('no-results-message');
          container.appendChild(noResults);
        }
      } else {
        // Remove "no results" message if it exists
        const noResults = document.querySelector('.no-results-message');
        if (noResults) {
          noResults.remove();
        }
      }

      // Return boolean indicating whether any items are visible after filtering
      return visibleCount > 0;
    }
    
    // Event listeners for search
    if (searchInput) {
      // Create debounced filter function for better performance
      const debouncedFilter = performanceUtils.debounce((value) => {
        filterStrains(value);
      }, 150); // 150ms debounce
      
      searchInput.addEventListener('input', (e) => {
        const val = e.target.value;
        
        // Immediate visual feedback
        const hasTerm = val && val.trim().length > 0;
        searchInput.classList.toggle('search-active', !!hasTerm);
        
        // Debounced filtering for performance
        debouncedFilter(val);
      }, { passive: true });
      
      // Focus on search input when modal opens
      searchInput.focus();
      
      // Handle Enter key to select first visible strain
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const firstVisible = document.querySelector('.strain-item[style*="block"], .strain-item:not([style*="none"])');
          if (firstVisible) {
            firstVisible.click();
          }
        }
      });
    }
    
    // Clear search button
    if (clearSearchBtn) {
      clearSearchBtn.addEventListener('click', () => {
        searchInput.value = '';
        filterStrains('');
        searchInput.classList.remove('search-active');
        searchInput.focus();
      });
    }
    
    // Ensure any remaining loading modals are completely hidden and removed
    const existingLoadingModals = document.querySelectorAll('.modal[id*="loading"]');
    console.log('Found existing loading modals:', existingLoadingModals.length);
    existingLoadingModals.forEach(loadingModal => {
      const instance = bootstrap.Modal.getInstance(loadingModal);
      if (instance) {
        console.log('Hiding loading modal instance');
        instance.hide();
      }
      if (loadingModal.parentNode) {
        console.log('Removing loading modal from DOM');
        loadingModal.parentNode.removeChild(loadingModal);
      }
    });
    
    // Show the modal with debugging
    console.log('Creating modal instance for strain selection');
    const modalInstance = new bootstrap.Modal(modal);
    console.log('Showing strain selection modal');
    modalInstance.show();
    
    // Add a small delay to ensure the modal is properly displayed
    setTimeout(() => {
      console.log('Modal should now be visible');
      // Ensure any loading spinners in the modal are removed
      const loadingSpinners = modal.querySelectorAll('.spinner-border, .spinner-grow');
      loadingSpinners.forEach(spinner => {
        spinner.remove();
      });
      
      // Force the modal to be visible if it's not
      if (!modal.classList.contains('show')) {
        console.log('Modal not visible, forcing show');
        modal.classList.add('show');
        modal.style.display = 'block';
        modal.setAttribute('aria-hidden', 'false');
      }
    }, 100);
    
    // Clean up modal when hidden
    modal.addEventListener('hidden.bs.modal', () => {
      console.log('Strain selection modal hidden, cleaning up');
      if (modal.parentNode) {
        document.body.removeChild(modal);
      }
      // Ensure body overflow is restored when modal is closed
      restoreBodyScroll();
    });
    
    // Add event listener for when modal is shown
    modal.addEventListener('shown.bs.modal', () => {
      console.log('Strain selection modal is now visible');
    });
    
  } catch (error) {
    console.error('Error opening strain lineage editor:', error);
    
    // Hide loading modal if it exists
    const loadingModal = document.getElementById('loadingModal');
    if (loadingModal) {
      const loadingInstance = bootstrap.Modal.getInstance(loadingModal);
      if (loadingInstance) {
        loadingInstance.hide();
      }
      document.body.removeChild(loadingModal);
    }
    
    // Show appropriate error message
    if (error.message === 'Request timed out') {
      alert('The request to load strains timed out. Please try again. If the problem persists, refresh the page.');
    } else {
      alert(`Failed to load strains: ${error.message}`);
    }
  }
}

// Function to select a strain for editing
function selectStrainForEditing(strainName, currentLineage) {
  console.log('selectStrainForEditing called with:', strainName, currentLineage);
  
  try {
    // Close the selection modal with proper cleanup
    const selectionModal = document.getElementById('strainSelectionModal');
    if (selectionModal) {
      console.log('Closing strain selection modal');
      const modalInstance = bootstrap.Modal.getInstance(selectionModal);
      if (modalInstance) {
        modalInstance.hide();
      }
      
      // Wait for modal to fully close before opening lineage editor
      setTimeout(() => {
        console.log('Strain selection modal closed, opening lineage editor');
        openLineageEditorForStrain(strainName, currentLineage);
      }, 300);
    } else {
      console.log('No strain selection modal found, opening lineage editor directly');
      openLineageEditorForStrain(strainName, currentLineage);
    }
  } catch (error) {
    console.error('Error in selectStrainForEditing:', error);
    alert('An unexpected error occurred. Please refresh the page and try again.');
  }
}

// Separate function to open lineage editor
function openLineageEditorForStrain(strainName, currentLineage) {
  console.log('openLineageEditorForStrain called with:', strainName, currentLineage);
  
  try {
    
    // Check if strain lineage editor is available
    if (window.strainLineageEditor) {
      console.log('Strain lineage editor is available, calling openEditor');
      try {
        // Enhanced lineage editor call with error handling
                try {
                    if (window.strainLineageEditor && typeof window.strainLineageEditor.openEditor === 'function') {
                        window.strainLineageEditor.openEditor(strainName, currentLineage);
                    } else {
                        console.error('StrainLineageEditor not properly initialized');
                        alert('Lineage editor not available. Please refresh the page and try again.');
                    }
                } catch (error) {
                    console.error('Error opening lineage editor:', error);
                    alert('Error opening lineage editor. Please try again.');
                }
        console.log('openEditor called successfully');
      } catch (error) {
        console.error('Error opening strain lineage editor:', error);
        alert('Error opening strain lineage editor. Please try again.');
        return;
      }
    } else {
      console.log('Strain lineage editor not available, attempting to initialize...');
      
      // Check if the modal element exists
      const modalElement = document.getElementById('strainLineageEditorModal');
      if (!modalElement) {
        console.error('strainLineageEditorModal element not found');
        alert('Strain Lineage Editor modal not found. Please refresh the page and try again.');
        return;
      }
      
      console.log('Modal element found, attempting to initialize StrainLineageEditor');
      
      // Try to initialize the editor
      try {
        if (typeof StrainLineageEditor !== 'undefined') {
          console.log('StrainLineageEditor class is available, initializing...');
          window.strainLineageEditor = StrainLineageEditor.init();
          console.log('StrainLineageEditor initialized');
          
          setTimeout(() => {
            if (window.strainLineageEditor) {
              console.log('Calling openEditor after initialization');
              try {
                // Enhanced lineage editor call with error handling
                try {
                    if (window.strainLineageEditor && typeof window.strainLineageEditor.openEditor === 'function') {
                        window.strainLineageEditor.openEditor(strainName, currentLineage);
                    } else {
                        console.error('StrainLineageEditor not properly initialized');
                        alert('Lineage editor not available. Please refresh the page and try again.');
                    }
                } catch (error) {
                    console.error('Error opening lineage editor:', error);
                    alert('Error opening lineage editor. Please try again.');
                }
                console.log('openEditor called successfully after initialization');
              } catch (openError) {
                console.error('Error calling openEditor after initialization:', openError);
                alert('Error opening strain lineage editor. Please try again.');
              }
            } else {
              console.error('strainLineageEditor still not available after initialization');
              alert('Failed to initialize Strain Lineage Editor. Please refresh the page and try again.');
            }
          }, 100);
        } else {
          console.error('StrainLineageEditor class not defined');
          alert('Strain Lineage Editor not loaded. Please refresh the page and try again.');
        }
      } catch (error) {
        console.error('Error initializing strain lineage editor:', error);
        alert('Failed to initialize Strain Lineage Editor. Please refresh the page and try again.');
      }
    }
  } catch (error) {
    console.error('Error in selectStrainForEditing:', error);
    alert('An unexpected error occurred. Please refresh the page and try again.');
  }
}

const VALID_PRODUCT_TYPES = [
  "flower", "pre-roll", "infused pre-roll", "concentrate", "solventless concentrate", "vape cartridge",
  "edible (solid)", "edible (liquid)", "high cbd edible liquid", "tincture", "topical", "capsule", "paraphernalia",
  "rso/co2 tankers"
];

const debounce = (func, delay) => {
    let timeoutId;
    let isExecuting = false; // Add execution lock
    
    return function(...args) {
        const context = this;
        
        // If already executing, don't schedule another execution
        if (isExecuting) {
            console.log('Generation already in progress, ignoring duplicate request');
            return;
        }
        
        clearTimeout(timeoutId);
        timeoutId = setTimeout(async () => {
            isExecuting = true;
            try {
                await func.apply(context, args);
            } finally {
                isExecuting = false;
            }
        }, delay);
    };
};

// Application Loading Splash Manager
const AppLoadingSplash = {
    loadingSteps: [
        { text: 'Initializing application...', progress: 10 },
        { text: 'Loading templates...', progress: 25 },
        { text: 'Preparing interface...', progress: 40 },
        { text: 'Loading product data...', progress: 60 },
        { text: 'Processing tags...', progress: 75 },
        { text: 'Setting up filters...', progress: 90 },
        { text: 'Almost ready...', progress: 95 },
        { text: 'Welcome to Auto Generating Tag Designer!', progress: 100 }
    ],
    currentStep: 0,
    isVisible: true,
    autoAdvanceInterval: null,

    show() {
        this.isVisible = true;
        this.currentStep = 0;
        
        const splash = document.getElementById('appLoadingSplash');
        const mainContent = document.getElementById('mainContent');
        
        if (splash) {
            splash.style.display = 'flex';
            splash.classList.remove('fade-out');
        }
        
        if (mainContent) {
            mainContent.classList.remove('loaded');
            mainContent.style.opacity = '0';
        }
        
        this.updateProgress(0, 'Initializing application...');
        console.log('Splash screen shown');
    },

    updateProgress(progress, text) {
        const fillElement = document.getElementById('appLoadingFill');
        const textElement = document.getElementById('appLoadingText');
        const statusElement = document.getElementById('appLoadingStatus');
        
        if (fillElement) {
            fillElement.style.width = `${progress}%`;
        }
        
        if (textElement) {
            textElement.style.opacity = '0';
            setTimeout(() => {
                textElement.textContent = text;
                textElement.style.opacity = '1';
            }, 150);
        }
        
        if (statusElement) {
            statusElement.textContent = this.getStatusText(progress);
        }
        
        // Log progress for debugging
        console.log(`Splash progress: ${progress}% - ${text}`);
    },

    getStatusText(progress) {
        if (progress < 25) return 'Initializing';
        if (progress < 50) return 'Loading';
        if (progress < 75) return 'Processing';
        if (progress < 100) return 'Finalizing';
        return 'Ready';
    },

    nextStep() {
        if (this.currentStep < this.loadingSteps.length - 1) {
            this.currentStep++;
            const step = this.loadingSteps[this.currentStep];
            this.updateProgress(step.progress, step.text);
        }
    },

    complete() {
        this.updateProgress(100, 'Welcome to Auto Generating Tag Designer!');
        setTimeout(() => {
            this.hide();
        }, 1000);
    },

    hide() {
        this.isVisible = false;
        this.stopAutoAdvance();
        
        const splash = document.getElementById('appLoadingSplash');
        const mainContent = document.getElementById('mainContent');
        
        if (splash) {
            splash.classList.add('fade-out');
            setTimeout(() => {
                splash.style.display = 'none';
            }, 500);
        }
        
        if (mainContent) {
            setTimeout(() => {
                mainContent.classList.add('loaded');
                mainContent.style.opacity = '1';
            }, 100);
        }
        
        console.log('Splash screen hidden');
    },

    // Auto-advance steps for visual feedback
    startAutoAdvance() {
        this.stopAutoAdvance(); // Clear any existing interval
        this.autoAdvanceInterval = setInterval(() => {
            if (this.isVisible && this.currentStep < this.loadingSteps.length - 2) {
                this.nextStep();
            }
        }, 800);
    },

    stopAutoAdvance() {
        if (this.autoAdvanceInterval) {
            clearInterval(this.autoAdvanceInterval);
            this.autoAdvanceInterval = null;
        }
    },

    // Emergency hide function for debugging
    emergencyHide() {
        console.log('Emergency hiding splash screen');
        this.isVisible = false;
        this.stopAutoAdvance();
        
        const splash = document.getElementById('appLoadingSplash');
        const mainContent = document.getElementById('mainContent');
        
        if (splash) {
            splash.style.display = 'none';
        }
        
        if (mainContent) {
            mainContent.style.opacity = '1';
            mainContent.classList.add('loaded');
        }
    }
};

const TagManager = {
    state: {
        selectedTags: new Set(),
        persistentSelectedTags: new Set(), // New: persistent selected tags independent of filters
        initialized: false,
        filters: {},
        loading: false,
        isJsonMatchedSession: false, // Flag to indicate if we're in a JSON matched session
        brandCategories: new Map(),  // Add this for storing brand subcategories
        originalTags: [], // Store original tags separately
        originalFilterOptions: {}, // Store original filter options to preserve order
        lineageColors: {
            'SATIVA': 'var(--lineage-sativa)',
            'INDICA': 'var(--lineage-indica)',
            'HYBRID': 'var(--lineage-hybrid)',
            'HYBRID/SATIVA': 'var(--lineage-hybrid-sativa)',
            'HYBRID/INDICA': 'var(--lineage-hybrid-indica)',
            'CBD': 'var(--lineage-cbd)',
            'PARA': 'var(--lineage-para)',
            'MIXED': 'var(--lineage-mixed)',
            'CBD_BLEND': 'var(--lineage-cbd)'
        },
        filterCache: null,
        updateAvailableTagsTimer: null, // Add timer tracking
        isSearching: false // Whether a tag search term is active
    },
    isGenerating: false, // Add generation lock flag

    // Function to update brand filter label based on product type
    updateBrandFilterLabel() {
        const brandFilterLabel = document.querySelector('label[for="brandFilter"]');
        if (brandFilterLabel) {
            brandFilterLabel.textContent = 'Brand';
            brandFilterLabel.setAttribute('aria-label', 'Brand Filter');
        }
    },

    updateFilters(filters, preserveExistingValues = true) {
        if (!filters) return;
        
        // Debug log for filters
        console.log('Updating filters with:', filters, 'preserveExistingValues:', preserveExistingValues);
        
        // Store original filter options to preserve order
        if (!this.state.originalFilterOptions.vendor) {
            this.state.originalFilterOptions = { ...filters };
        }
        
        // Map of filter types to their HTML IDs (matching backend field names)
        const filterFieldMap = {
            vendor: 'vendorFilter',
            brand: 'brandFilter',
            productType: 'productTypeFilter', // Backend now returns 'productType'
            lineage: 'lineageFilter',
            weight: 'weightFilter',
            doh: 'dohFilter',
            highCbd: 'highCbdFilter'
            // Removed strain since there's no strainFilter dropdown in the HTML
        };
        
        // Update each filter dropdown
        Object.entries(filterFieldMap).forEach(([filterType, filterId]) => {
            const filterElement = document.getElementById(filterId);
            
            if (!filterElement) {
                console.warn(`Filter element not found: ${filterId}`);
                return;
            }
            
            // Get values for this filter type
            const fieldValues = filters[filterType] || [];
            const values = new Set();
            fieldValues.forEach(value => {
                if (value && value.trim() !== '') {
                    values.add(value.trim());
                }
            });
            
            // Sort values alphabetically for consistent ordering
            const sortedValues = Array.from(values).sort((a, b) => {
                // Special handling for lineage to maintain logical order
                if (filterType === 'lineage') {
                    const lineageOrder = ['SATIVA', 'INDICA', 'HYBRID', 'HYBRID/SATIVA', 'HYBRID/INDICA', 'CBD', 'CBD_BLEND', 'MIXED', 'PARA'];
                    const aIndex = lineageOrder.indexOf(a.toUpperCase());
                    const bIndex = lineageOrder.indexOf(b.toUpperCase());
                    if (aIndex !== -1 && bIndex !== -1) {
                        return aIndex - bIndex;
                    }
                }
                return a.localeCompare(b);
            });
            
            console.log(`Updating ${filterId} with values:`, sortedValues);
            
            // Special debug for weight filter
            if (filterType === 'weight') {
                console.log('Weight filter values (first 10):', sortedValues.slice(0, 10));
            }
            
            // Store current value
            const currentValue = filterElement.value;
            
            // Update the dropdown options with special formatting for RSO/CO2 Tanker
            filterElement.innerHTML = `
                <option value="">All</option>
                ${sortedValues.map(value => {
                    // Apply special font formatting for RSO/CO2 Tanker
                    if (value === 'rso/co2 tankers') {
                        return `<option value="${value}" style="font-weight: bold; font-style: italic; color: #a084e8;">RSO/CO2 Tanker</option>`;
                    }
                    return `<option value="${value}">${value}</option>`;
                }).join('')}
            `;
            
            // Handle value restoration based on preserveExistingValues parameter
            if (preserveExistingValues) {
                // Preserve existing value if it's still valid, or keep it even if not in current options
                if (currentValue && currentValue.trim() !== '') {
                    if (sortedValues.includes(currentValue)) {
                        // Value is still valid, restore it
                        filterElement.value = currentValue;
                    } else {
                        // Value is no longer in current options, but preserve it by adding it back
                        console.log(`Preserving filter value "${currentValue}" for ${filterId} even though it's not in current options`);
                        const option = document.createElement('option');
                        option.value = currentValue;
                        option.textContent = currentValue;
                        option.style.color = '#666'; // Gray out to indicate it's not currently available
                        filterElement.appendChild(option);
                        filterElement.value = currentValue;
                    }
                } else {
                    filterElement.value = '';
                }
            } else {
                // Only restore if value is still valid (for explicit filter clearing)
                if (currentValue && sortedValues.includes(currentValue)) {
                    filterElement.value = currentValue;
                } else {
                    filterElement.value = '';
                }
            }
        });
    },

    async updateFilterOptions() {
        try {
            // Get current filter values
            const currentFilters = {
                vendor: document.getElementById('vendorFilter')?.value || '',
                brand: document.getElementById('brandFilter')?.value || '',
                productType: document.getElementById('productTypeFilter')?.value || '',
                lineage: document.getElementById('lineageFilter')?.value || '',
                weight: document.getElementById('weightFilter')?.value || '',
                doh: document.getElementById('dohFilter')?.value || '',
                highCbd: document.getElementById('highCbdFilter')?.value || ''
            };

            // Only update filter options if we have original options
            if (!this.state.originalFilterOptions.vendor) {
                console.log('No original filter options available, skipping update');
                return;
            }

            // Get the currently filtered tags to determine available options
            const tagsToFilter = this.state.originalTags.length > 0 ? this.state.originalTags : this.state.tags;
            
            // Check if only vendor filter is selected (no other filters)
            const hasVendorFilter = currentFilters.vendor && currentFilters.vendor.trim() !== '' && currentFilters.vendor.toLowerCase() !== 'all';
            const hasOtherFilters = Object.entries(currentFilters).some(([key, value]) => 
                key !== 'vendor' && value && value.trim() !== '' && value.toLowerCase() !== 'all'
            );
            
            // If only vendor filter is selected, don't limit dropdown options - use original tags
            const shouldLimitOptions = hasOtherFilters || !hasVendorFilter;
            
            // Apply current filters to get the subset of tags that would be shown
            const filteredTags = shouldLimitOptions ? tagsToFilter.filter(tag => {
                // Check vendor filter - only apply if not empty and not "All"
                if (currentFilters.vendor && currentFilters.vendor.trim() !== '' && currentFilters.vendor.toLowerCase() !== 'all') {
                    const tagVendor = (tag.Vendor || tag.vendor || '').toString().trim();
                    if (tagVendor.toLowerCase() !== currentFilters.vendor.toLowerCase()) {
                        return false;
                    }
                }
                
                // Check brand filter - only apply if not empty and not "All"
                if (currentFilters.brand && currentFilters.brand.trim() !== '' && currentFilters.brand.toLowerCase() !== 'all') {
                    const tagBrand = (tag['Product Brand'] || tag.productBrand || '').toString().trim();
                    if (tagBrand.toLowerCase() !== currentFilters.brand.toLowerCase()) {
                        return false;
                    }
                }
                
                // Check product type filter - only apply if not empty and not "All"
                if (currentFilters.productType && currentFilters.productType.trim() !== '' && currentFilters.productType.toLowerCase() !== 'all') {
                    const tagProductType = (tag['Product Type*'] || tag.productType || '').toString().trim();
                    const normalizedTagProductType = normalizeProductType(tagProductType);
                    if (normalizedTagProductType.toLowerCase() !== currentFilters.productType.toLowerCase()) {
                        return false;
                    }
                }
                
                // Check lineage filter - only apply if not empty and not "All"
                if (currentFilters.lineage && currentFilters.lineage.trim() !== '' && currentFilters.lineage.toLowerCase() !== 'all') {
                    const tagLineage = (tag.Lineage || tag.lineage || '').toString().trim();
                    if (tagLineage.toLowerCase() !== currentFilters.lineage.toLowerCase()) {
                        return false;
                    }
                }
                
                // Check weight filter - only apply if not empty and not "All"
                if (currentFilters.weight && currentFilters.weight.toString().trim() !== '' && currentFilters.weight.toString().toLowerCase() !== 'all') {
                    // Get the tag's weight in multiple possible formats
                    const tagWeight = (tag['Weight*'] || tag.weight || '').toString().trim();
                    const tagWeightWithUnits = (tag.weightWithUnits || tag.WeightUnits || '').toString().trim();
                    const tagUnits = (tag.Units || '').toString().trim();
                    
                    // Create a normalized weight string for comparison
                    let normalizedTagWeight = '';
                    if (tagWeight && tagUnits) {
                        normalizedTagWeight = `${tagWeight}${tagUnits}`.toLowerCase();
                    } else if (tagWeightWithUnits) {
                        normalizedTagWeight = tagWeightWithUnits.toLowerCase();
                    } else if (tagWeight) {
                        normalizedTagWeight = tagWeight.toLowerCase();
                    }
                    
                    const filterWeight = currentFilters.weight.toString().trim().toLowerCase();
                    
                    // Check if any of the weight representations match the filter
                    const weightMatches = [
                        normalizedTagWeight,
                        tagWeight.toLowerCase(),
                        tagWeightWithUnits.toLowerCase(),
                        tagUnits.toLowerCase()
                    ].some(weight => weight === filterWeight);
                    
                    if (!weightMatches) {
                        return false;
                    }
                }
                
                // Check DOH filter - only apply if not empty and not "All"
                if (currentFilters.doh && currentFilters.doh.trim() !== '' && currentFilters.doh.toLowerCase() !== 'all') {
                    const tagDoh = (tag.DOH || tag.doh || '').toString().trim().toUpperCase();
                    const filterDoh = currentFilters.doh.toString().trim().toUpperCase();
                    if (tagDoh !== filterDoh) {
                        return false;
                    }
                }
                
                // Check High CBD filter - only apply if not empty and not "All"
                if (currentFilters.highCbd && currentFilters.highCbd.trim() !== '' && currentFilters.highCbd.toLowerCase() !== 'all') {
                    const tagProductType = (tag.productType || tag['Product Type*'] || '').toString().trim().toLowerCase();
                    const isHighCbd = tagProductType.startsWith('high cbd');
                    
                    if (currentFilters.highCbd === 'High CBD Products' && !isHighCbd) {
                        return false;
                    } else if (currentFilters.highCbd === 'Non-High CBD Products' && isHighCbd) {
                        return false;
                    }
                }
                
                return true;
            }) : tagsToFilter;

            // Extract available options from filtered tags
            const availableOptions = {
                vendor: new Set(),
                brand: new Set(),
                productType: new Set(),
                lineage: new Set(),
                weight: new Set(),
                doh: new Set(),
                highCbd: new Set()
            };

            filteredTags.forEach(tag => {
                if (tag.Vendor || tag.vendor) availableOptions.vendor.add((tag.Vendor || tag.vendor || '').toString().trim());
                if (tag['Product Brand'] || tag.productBrand) availableOptions.brand.add((tag['Product Brand'] || tag.productBrand || '').toString().trim());
                if (tag['Product Type*'] || tag.productType) {
                    const productType = (tag['Product Type*'] || tag.productType || '').toString().trim();
                    const normalizedType = normalizeProductType(productType);
                    if (normalizedType) availableOptions.productType.add(normalizedType);
                }
                if (tag.Lineage || tag.lineage) availableOptions.lineage.add((tag.Lineage || tag.lineage || '').toString().trim());
                // CRITICAL FIX: Check all possible weight field variations for options generation
                if (tag['Weight*'] || tag.weight || tag.weightWithUnits || tag.WeightWithUnits || tag.WeightUnits || tag.CombinedWeight) {
                    // Always use the combined value for display and filtering - check all possible sources
                    const combined = (tag.weightWithUnits || tag.WeightWithUnits || tag.WeightUnits || 
                                    tag.CombinedWeight || tag['Weight*'] || tag.weight).toString().trim();
                    if (combined) availableOptions.weight.add(combined);
                }
                if (tag.DOH || tag.doh) availableOptions.doh.add((tag.DOH || tag.doh || '').toString().trim());
                
                // For High CBD, categorize the product type
                const tagProductType = (tag['Product Type*'] || tag.productType || '').toString().trim().toLowerCase();
                const isHighCbd = tagProductType.startsWith('high cbd');
                if (isHighCbd) {
                    availableOptions.highCbd.add('High CBD Products');
                } else if (tagProductType) {
                    availableOptions.highCbd.add('Non-High CBD Products');
                }
            });

            // Update each filter dropdown with available options
            const filterFieldMap = {
                vendor: 'vendorFilter',
                brand: 'brandFilter',
                productType: 'productTypeFilter',
                lineage: 'lineageFilter',
                weight: 'weightFilter',
                doh: 'dohFilter',
                highCbd: 'highCbdFilter'
            };

            Object.entries(filterFieldMap).forEach(([filterType, filterId]) => {
                const filterElement = document.getElementById(filterId);
                if (!filterElement) {
                    return;
                }

                const currentValue = filterElement.value;
                const newOptions = Array.from(availableOptions[filterType]);
                
                // Sort options consistently
                const sortedOptions = [...newOptions].sort((a, b) => {
                    // Special handling for lineage to maintain logical order
                    if (filterType === 'lineage') {
                        const lineageOrder = ['SATIVA', 'INDICA', 'HYBRID', 'HYBRID/SATIVA', 'HYBRID/INDICA', 'CBD', 'CBD_BLEND', 'MIXED', 'PARA'];
                        const aIndex = lineageOrder.indexOf(a.toUpperCase());
                        const bIndex = lineageOrder.indexOf(b.toUpperCase());
                        if (aIndex !== -1 && bIndex !== -1) {
                            return aIndex - bIndex;
                        }
                    }
                    return a.localeCompare(b);
                });
                
                // Only update if options have actually changed
                const currentOptions = Array.from(filterElement.options).map(opt => opt.value).filter(v => v !== '');
                const optionsChanged = currentOptions.length !== sortedOptions.length || 
                                     !currentOptions.every((opt, i) => opt === sortedOptions[i]);
                
                if (optionsChanged) {
                    // Create new options HTML with special formatting for RSO/CO2 Tanker
                    const optionsHtml = `
                        <option value="">All</option>
                        ${sortedOptions.map(value => {
                            // Apply special font formatting for RSO/CO2 Tanker
                            if (value === 'rso/co2 tankers') {
                                return `<option value="${value}" style="font-weight: bold; font-style: italic; color: #a084e8;">RSO/CO2 Tanker</option>`;
                            }
                            return `<option value="${value}">${value}</option>`;
                        }).join('')}
                    `;
                    
                    // Update the dropdown options
                    filterElement.innerHTML = optionsHtml;
                    
                    // Try to restore the previous selection if it's still valid
                    if (currentValue && sortedOptions.includes(currentValue)) {
                        filterElement.value = currentValue;
                    } else {
                        filterElement.value = '';
                    }
                }
            });

        } catch (error) {
            console.error('Error updating filter options:', error);
        }
    },

    applyFilters() {
        console.log('applyFilters() called - HOT RELOAD TEST');
        
        // Get current filter values
        const vendorFilter = document.getElementById('vendorFilter')?.value || '';
        const brandFilter = document.getElementById('brandFilter')?.value || '';
        const productTypeFilter = document.getElementById('productTypeFilter')?.value || '';
        const lineageFilter = document.getElementById('lineageFilter')?.value || '';
        const weightFilter = document.getElementById('weightFilter')?.value || '';
        const dohFilter = document.getElementById('dohFilter')?.value || '';
        const highCbdFilter = document.getElementById('highCbdFilter')?.value || '';
        
        console.log('Filter values:', {
            vendor: vendorFilter,
            brand: brandFilter,
            productType: productTypeFilter,
            lineage: lineageFilter,
            weight: weightFilter,
            doh: dohFilter,
            highCbd: highCbdFilter
        });
        
        // Store current filters in state for use by updateSelectedTags
        this.state.filters = {
            vendor: vendorFilter,
            brand: brandFilter,
            productType: productTypeFilter,
            lineage: lineageFilter,
            weight: weightFilter,
            doh: dohFilter,
            highCbd: highCbdFilter
        };
        
        // Create a filter key for caching
        const filterKey = `${vendorFilter}|${brandFilter}|${productTypeFilter}|${lineageFilter}|${weightFilter}|${dohFilter}|${highCbdFilter}`;
        
        // Check if all filters are set to "All" - this means show all tags
        const allFiltersAll = [vendorFilter, brandFilter, productTypeFilter, lineageFilter, weightFilter, dohFilter, highCbdFilter]
            .every(filter => !filter || filter.trim() === '' || filter.toLowerCase() === 'all');
        
        if (allFiltersAll) {
            console.log('All filters are "All", showing all original tags');
            // Clear the filter cache since we're showing all tags
            this.state.filterCache = null;
            // Pass original tags with no filtering
            this.debouncedUpdateAvailableTags(this.state.originalTags, null);
            this.renderActiveFilters();
            return;
        }
        
        // Check if we have cached results for this exact filter combination
        if (this.state.filterCache && this.state.filterCache.key === filterKey) {
            // Always pass original tags to preserve persistent selections
            this.debouncedUpdateAvailableTags(this.state.originalTags, this.state.filterCache.result);
            this.renderActiveFilters();
            return;
        }
        
        // Filter the tags based on current filter values using original tags
        // Ensure we always use originalTags for filtering to preserve the full dataset
        const tagsToFilter = this.state.originalTags.length > 0 ? this.state.originalTags : this.state.tags;
        
        // If we don't have original tags, we can't filter properly
        if (this.state.originalTags.length === 0) {
            console.warn('No original tags available for filtering');
            return;
        }
        
        console.log('applyFilters - tagsToFilter length:', tagsToFilter.length);
        console.log('applyFilters - first tag sample:', tagsToFilter[0]);
        
        const filteredTags = tagsToFilter.filter(tag => {
            // Check vendor filter - only apply if not empty and not "All"
            if (vendorFilter && vendorFilter.trim() !== '' && vendorFilter.toLowerCase() !== 'all') {
                const tagVendor = (tag.Vendor || tag.vendor || '').toString().trim();
                if (tagVendor.toLowerCase() !== vendorFilter.toLowerCase()) {
                    return false;
                }
            }
            
            // Check brand filter - only apply if not empty and not "All"
            if (brandFilter && brandFilter.trim() !== '' && brandFilter.toLowerCase() !== 'all') {
                const tagBrand = (tag['Product Brand'] || tag.productBrand || '').toString().trim();
                if (tagBrand.toLowerCase() !== brandFilter.toLowerCase()) {
                    return false;
                }
            }
            
            // Check product type filter - only apply if not empty and not "All"
            if (productTypeFilter && productTypeFilter.trim() !== '' && productTypeFilter.toLowerCase() !== 'all') {
                const tagProductType = (tag['Product Type*'] || tag.productType || '').toString().trim();
                const normalizedTagProductType = normalizeProductType(tagProductType);
                if (normalizedTagProductType.toLowerCase() !== productTypeFilter.toLowerCase()) {
                    return false;
                }
            }
            
            // Check lineage filter - only apply if not empty and not "All"
            if (lineageFilter && lineageFilter.trim() !== '' && lineageFilter.toLowerCase() !== 'all') {
                const tagLineage = (tag.Lineage || tag.lineage || '').toString().trim();
                if (tagLineage.toLowerCase() !== lineageFilter.toLowerCase()) {
                    return false;
                }
            }
            
            // Check weight filter - only apply if not empty and not "All"
            if (weightFilter && weightFilter.trim() !== '' && weightFilter.toLowerCase() !== 'all') {
                // Get the tag's weight in multiple possible formats
                const tagWeight = (tag['Weight*'] || tag.weight || '').toString().trim();
                // CRITICAL FIX: Check all possible weight field variations for filtering
                const tagWeightWithUnits = (tag.weightWithUnits || tag.WeightWithUnits || tag.WeightUnits || 
                                          tag.CombinedWeight || tag.weightWithUnits || '').toString().trim();
                const tagUnits = (tag.Units || '').toString().trim();
                
                // Create a normalized weight string for comparison
                let normalizedTagWeight = '';
                if (tagWeight && tagUnits) {
                    normalizedTagWeight = `${tagWeight}${tagUnits}`.toLowerCase();
                } else if (tagWeightWithUnits) {
                    normalizedTagWeight = tagWeightWithUnits.toLowerCase();
                } else if (tagWeight) {
                    normalizedTagWeight = tagWeight.toLowerCase();
                }
                
                const filterWeight = weightFilter.toString().trim().toLowerCase();
                
                // Check if any of the weight representations match the filter
                const weightMatches = [
                    normalizedTagWeight,
                    tagWeight.toLowerCase(),
                    tagWeightWithUnits.toLowerCase(),
                    tagUnits.toLowerCase()
                ].some(weight => weight === filterWeight);
                
                if (!weightMatches) {
                    return false;
                }
            }
            
            // Check DOH filter - only apply if not empty and not "All"
            if (dohFilter && dohFilter.trim() !== '' && dohFilter.toLowerCase() !== 'all') {
                const tagDoh = (tag.DOH || tag.doh || '').toString().trim().toUpperCase();
                const filterDoh = dohFilter.toString().trim().toUpperCase();
                if (tagDoh !== filterDoh) {
                    return false;
                }
            }
            
            // Check High CBD filter - only apply if not empty and not "All"
            if (highCbdFilter && highCbdFilter.trim() !== '' && highCbdFilter.toLowerCase() !== 'all') {
                const tagProductType = (tag.productType || tag['Product Type*'] || '').toString().trim().toLowerCase();
                const isHighCbd = tagProductType.startsWith('high cbd');
                
                if (highCbdFilter === 'High CBD Products' && !isHighCbd) {
                    return false;
                } else if (highCbdFilter === 'Non-High CBD Products' && isHighCbd) {
                    return false;
                }
            }
            
            return true;
        });
        
        // Cache the results
        this.state.filterCache = {
            key: filterKey,
            result: filteredTags
        };
        
        // Always pass original tags to preserve persistent selections, with filtered tags for display
        // Reduced logging to prevent console spam
        // console.log('applyFilters - calling debouncedUpdateAvailableTags with filteredTags length:', filteredTags.length);
        this.debouncedUpdateAvailableTags(this.state.originalTags, filteredTags);
        
        // Update selected tags to also respect the current filters
        const selectedTagObjects = this.state.persistentSelectedTags.map(name => {
            // First try to find in current tags (filtered view)
            let foundTag = this.state.tags.find(t => t['Product Name*'] === name);
            // If not found in current tags, try original tags
            if (!foundTag) {
                foundTag = this.state.originalTags.find(t => t['Product Name*'] === name);
            }
            // If still not found, create a minimal tag object (for JSON matched items)
            if (!foundTag) {
                console.warn(`Tag not found in state: ${name}, creating minimal tag object`);
                foundTag = {
                    'Product Name*': name,
                    'Product Brand': 'Unknown',
                    'Vendor': 'Unknown',
                    'Product Type*': 'Unknown',
                    'Lineage': 'MIXED'
                };
            }
            return foundTag;
        }).filter(Boolean);
        
        this.updateSelectedTags(selectedTagObjects);
        this.renderActiveFilters();
    },

    handleSearch(listId, searchInputId) {
        const searchInput = document.getElementById(searchInputId);
        const searchTerm = searchInput.value.toLowerCase().trim();

        // Choose which tags to filter
        let tags = [];
        if (listId === 'availableTags') {
            tags = this.state.originalTags || [];
        } else if (listId === 'selectedTags') {
            tags = Array.from(this.state.selectedTags).map(name =>
                this.state.originalTags.find(t => t['Product Name*'] === name)
            ).filter(Boolean);
        }

        if (!searchTerm) {
            // Restore full list
            if (listId === 'availableTags') {
                this.debouncedUpdateAvailableTags(this.state.originalTags, null);
            } else if (listId === 'selectedTags') {
                this.updateSelectedTags(tags);
            }
            searchInput.classList.remove('search-active');
            this.state.isSearching = false;
            return true;
        }

        // Filter tags: only match product name
        const filteredTags = tags.filter(tag => {
            const tagName = tag['Product Name*'] || '';
            return tagName.toLowerCase().includes(searchTerm);
        });

        // Update the list with only matching tags
        if (listId === 'availableTags') {
            this.debouncedUpdateAvailableTags(this.state.originalTags, filteredTags);
            // Scroll to top of available tags list after search
            setTimeout(() => {
                const availableTagsContainer = document.getElementById('availableTags');
                if (availableTagsContainer) {
                    availableTagsContainer.scrollTop = 0;
                }
            }, 50);
            // Ensure groups are expanded while searching
            setTimeout(() => {
                this.expandAllTagGroups();
            }, 120);
        } else if (listId === 'selectedTags') {
            this.updateSelectedTags(filteredTags);
            // Scroll to top of selected tags list after search
            setTimeout(() => {
                const selectedTagsContainer = document.getElementById('selectedTags');
                if (selectedTagsContainer) {
                    selectedTagsContainer.scrollTop = 0;
                }
            }, 50);
        }
        searchInput.classList.add('search-active');
        this.state.isSearching = true;

        // Return boolean indicating whether any tags match the search
        return filteredTags.length > 0;
    },

    handleAvailableTagsSearch(event) {
        return this.handleSearch('availableTags', 'availableTagsSearch');
    },

    handleSelectedTagsSearch(event) {
        return this.handleSearch('selectedTags', 'selectedTagsSearch');
    },

    extractBrand(tag) {
        // Try to get brand from Product Brand field first
        let brand = tag.productBrand || tag.brand || '';
        
        // If no brand found, try to extract from product name
        if (!brand) {
            const productName = tag['Product Name*'] || tag.ProductName || tag.Description || '';
            // Look for "by [Brand]" pattern
            const byMatch = productName.match(/by\s+([A-Za-z0-9\s]+)(?:\s|$)/i);
            if (byMatch) {
                brand = byMatch[1].trim();
            }
        }
        
        // If still no brand found, try to use the vendor as the brand
        if (!brand && tag.vendor) {
            brand = tag.vendor.trim();
        }
        
        return brand;
    },

    // Helper function to capitalize vendor names properly
    capitalizeVendorName(vendor) {
        if (!vendor) return '';
        
        // Handle common vendor name patterns
        const vendorLower = vendor.toLowerCase();
        
        // Known vendor name mappings
        const vendorMappings = {
            '1555 industrial llc': '1555 Industrial LLC',
            'dcz holdings inc': 'DCZ Holdings Inc.',
            'jsm llc': 'JSM LLC',
            'harmony farms': 'Harmony Farms',
            'hustler\'s ambition': 'Hustler\'s Ambition',
            'mama j\'s': 'Mama J\'s'
        };
        
        // Check if we have a known mapping
        if (vendorMappings[vendorLower]) {
            return vendorMappings[vendorLower];
        }
        
        // General capitalization for unknown vendors
        return vendor.split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');
    },

    // Helper function to capitalize brand names properly
    capitalizeBrandName(brand) {
        if (!brand) return '';
        
        // Handle common brand name patterns
        const brandLower = brand.toLowerCase();
        
        // Known brand name mappings
        const brandMappings = {
            'dank czar': 'Dank Czar',
            'omega': 'Omega',
            'airo pro': 'Airo Pro',
            'mama j\'s': 'Mama J\'s'
        };
        
        // Check if we have a known mapping
        if (brandMappings[brandLower]) {
            return brandMappings[brandLower];
        }
        
        // General capitalization for unknown brands
        return brand.split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join(' ');
    },

    organizeBrandCategories(tags) {
        const vendorGroups = new Map();
        let skippedTags = 0;
        
        // CRITICAL FIX: For JSON matched tags, skip deduplication entirely
        // The backend already handles deduplication correctly, so we preserve all products
        const seenProductKeys = new Set();
        const uniqueTags = tags.filter(tag => {
            // Check if this is a JSON matched product
            const isJsonMatched = tag.Source && tag.Source.includes('JSON Match');
            
            if (isJsonMatched) {
                // For JSON matched products, skip deduplication entirely
                // The backend already ensures we have unique original JSON items
                console.debug(`Preserving JSON matched product: ${tag['Original JSON Product Name'] || tag['Product Name*'] || 'Unknown'}`);
                return true;
            } else {
                // For regular products, use the existing deduplication logic
                const productName = tag['Product Name*'] || tag.ProductName || tag.Description || '';
                const vendor = tag.vendor || tag['Vendor'] || tag['Vendor/Supplier*'] || '';
                const brand = tag.productBrand || tag['Product Brand'] || tag['ProductBrand'] || '';
                const weight = (tag.weight || tag['Weight*'] || tag['Weight'] || tag['WeightUnits'] || '').toString().trim();
                
                // Create a unique key that includes vendor/brand/weight to allow same product names with different weights
                const productKey = `${productName}|${vendor}|${brand}|${weight}`;
                
                if (seenProductKeys.has(productKey)) {
                    console.debug(`Skipping exact duplicate product in organizeBrandCategories: ${productKey}`);
                    return false;
                }
                seenProductKeys.add(productKey);
                return true;
            }
        });
        
        // Debug: Log the first few tags to see their structure
        if (uniqueTags.length > 0) {
            console.log('First tag structure:', uniqueTags[0]);
        }
        
        uniqueTags.forEach(tag => {
            // Use the correct field names from the tag object - check multiple possible field names
            let vendor = tag.vendor || tag['Vendor'] || tag['Vendor/Supplier*'] || tag['Vendor/Supplier'] || '';
            let brand = tag.productBrand || tag['Product Brand'] || tag['ProductBrand'] || this.extractBrand(tag) || '';
            const rawProductType = tag.productType || tag['Product Type*'] || tag['Product Type'] || '';
            const normalizedProductType = normalizeProductType(rawProductType.trim());
            const productType = VALID_PRODUCT_TYPES.includes(normalizedProductType.toLowerCase())
              ? normalizedProductType.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(' ')
              : 'Unknown Type';
            const lineage = tag.lineage || tag['Lineage'] || 'MIXED';
            const weight = (tag.weight || tag['Weight*'] || tag['Weight'] || tag['WeightUnits'] || '').toString().trim();
            // CRITICAL FIX: Ensure weightWithUnits is properly populated from multiple possible sources
            const weightWithUnits = (tag.weightWithUnits || tag.WeightWithUnits || tag.WeightUnits || 
                                   tag.CombinedWeight || tag.weightWithUnits || weight || '').toString().trim();

            // If no vendor found, try to extract from product name
            if (!vendor) {
                const productName = tag['Product Name*'] || tag.ProductName || tag.Description || '';
                // Look for "by [Brand]" pattern
                const byMatch = productName.match(/by\s+([A-Za-z0-9\s]+)(?:\s|$)/i);
                if (byMatch) {
                    vendor = byMatch[1].trim();
                }
            }

            // If still no vendor, use brand as vendor
            if (!vendor && brand) {
                vendor = brand;
            }

            // If still no vendor, use a default
            if (!vendor) {
                vendor = 'Unknown Vendor';
            }

            // Normalize the tag data
            const normalizedTag = {
                ...tag,
                vendor: this.capitalizeVendorName((vendor || '').toString().trim()),
                brand: this.capitalizeBrandName((brand || '').toString().trim()),
                productType: productType,
                lineage: (lineage || '').toString().trim().toUpperCase(), // always uppercase for color
                weight: weight,
                weightWithUnits: weightWithUnits,
                displayName: tag['Product Name*'] || tag.ProductName || tag.Description || 'Unknown Product'
            };

            // Always create vendor group (even if vendor === brand)
            if (!vendorGroups.has(normalizedTag.vendor)) {
                vendorGroups.set(normalizedTag.vendor, new Map());
            }
            const brandGroups = vendorGroups.get(normalizedTag.vendor);

            // Always create brand group under vendor (even if vendor === brand)
            if (!brandGroups.has(normalizedTag.brand)) {
                brandGroups.set(normalizedTag.brand, new Map());
            }
            const productTypeGroups = brandGroups.get(normalizedTag.brand);

            // Create product type group if it doesn't exist
            if (!productTypeGroups.has(normalizedTag.productType)) {
                productTypeGroups.set(normalizedTag.productType, new Map());
            }
            const weightGroups = productTypeGroups.get(normalizedTag.productType);

            // Create weight group if it doesn't exist - use weightWithUnits as the key
            if (!weightGroups.has(normalizedTag.weightWithUnits)) {
                weightGroups.set(normalizedTag.weightWithUnits, []);
            }
            weightGroups.get(normalizedTag.weightWithUnits).push(normalizedTag);
        });

        if (skippedTags > 0) {
            console.info(`Skipped ${skippedTags} tags due to missing vendor information`);
        }

        return vendorGroups;
    },

    // Compute likeness-based ordering helpers
    _getReferenceProductName() {
        try {
            const el = document.getElementById('searchProductName');
            const value = (el && typeof el.value === 'string') ? el.value.trim() : '';
            return value;
        } catch (e) {
            return '';
        }
    },

    _tokenizeName(name) {
        if (!name || typeof name !== 'string') return [];
        return name
            .toLowerCase()
            .replace(/\s+by\s+[^-()]+/g, ' ') // remove trailing "by Vendor"
            .replace(/\([^)]*\)/g, ' ')       // remove parenthetical vendor
            .split(/[^a-z0-9]+/g)
            .filter(Boolean);
    },

    _computeLikenessScore(tagName, refName) {
        if (!refName) return 0;
        const ref = (refName || '').toLowerCase();
        const name = (tagName || '').toLowerCase();
        if (!name) return 0;

        const refTokens = new Set(this._tokenizeName(refName));
        const nameTokens = new Set(this._tokenizeName(tagName));

        let overlap = 0;
        for (const t of refTokens) {
            if (nameTokens.has(t)) overlap += 1;
        }
        const denom = Math.min(refTokens.size || 1, nameTokens.size || 1);
        let score = denom > 0 ? overlap / denom : 0;

        // Substring and prefix bonuses
        if (name.includes(ref)) score += 0.25;
        if (name.startsWith(ref)) score += 0.15;

        return score;
    },

    _sortByLikenessIfRef(tagsArray) {
        const ref = this._getReferenceProductName();
        if (!ref) return tagsArray;
        try {
            const withScores = tagsArray.map(t => ({
                tag: t,
                s: this._computeLikenessScore((t && t['Product Name*']) || t?.ProductName || '', ref)
            }));
            withScores.sort((a, b) => {
                if (b.s !== a.s) return b.s - a.s;
                const an = (a.tag && (a.tag['Product Name*'] || a.tag.ProductName) || '').toString();
                const bn = (b.tag && (b.tag['Product Name*'] || b.tag.ProductName) || '').toString();
                return an.localeCompare(bn);
            });
            return withScores.map(x => x.tag);
        } catch (e) {
            return tagsArray;
        }
    },

    // Debounced version of updateAvailableTags to prevent multiple rapid calls
    debouncedUpdateAvailableTags: debounce(function(originalTags, filteredTags = null) {
        // Reduced logging to prevent console spam
        // console.log('debouncedUpdateAvailableTags called with:', {
        //     originalTagsLength: originalTags ? originalTags.length : 0,
        //     filteredTagsLength: filteredTags ? filteredTags.length : 0,
        //     originalTags: originalTags ? originalTags.slice(0, 2) : null,
        //     filteredTags: filteredTags ? filteredTags.slice(0, 2) : null
        // });
        
        // Show action splash for tag population - DISABLED to prevent distraction while typing
        // this.showActionSplash('Populating tags...');
        
        // Use requestAnimationFrame to ensure smooth DOM updates
        requestAnimationFrame(() => {
            this._updateAvailableTags(originalTags, filteredTags);
            
            // No splash to hide since we disabled it
            // setTimeout(() => {
            //     this.hideActionSplash();
            // }, 100);
        });
    }, 300),

    // CRITICAL FIX: Render JSON matched tags directly without any filtering or organization
    renderJsonMatchedTags(tags) {
        console.log('CRITICAL FIX: Rendering JSON matched tags directly, count:', tags.length);
        
        const availableTagsContainer = document.getElementById('availableTags');
        if (!availableTagsContainer) {
            console.error('Available tags container not found');
            return;
        }

        // Clear existing content
        availableTagsContainer.innerHTML = '';

        // Create a simple list container
        const tagList = document.createElement('div');
        tagList.className = 'tag-list';

        // Render each tag directly using the existing createTagElement function
        tags.forEach((tag, index) => {
            const tagElement = this.createTagElement(tag, false); // false = not for selected tags
            tagList.appendChild(tagElement);
        });

        availableTagsContainer.appendChild(tagList);
        
        // Add event listeners
        this.updateSelectAllCheckboxes();
        this.initializeSelectAllCheckbox();
        
        console.log('CRITICAL FIX: Rendered', tags.length, 'JSON matched tags directly');
    },

    // Internal function that actually updates the available tags
    _updateAvailableTags(originalTags, filteredTags = null) {
        console.log('_updateAvailableTags called with:', {
            originalTagsLength: originalTags ? originalTags.length : 0,
            filteredTagsLength: filteredTags ? filteredTags.length : 0,
            tags: filteredTags || originalTags
        });
        
        const availableTagsContainer = document.getElementById('availableTags');
        if (!availableTagsContainer) {
            console.error('Available tags container not found');
            return;
        }

        const tags = filteredTags || originalTags;
        if (!tags || tags.length === 0) {
            console.log('No tags provided, showing empty state');
            availableTagsContainer.innerHTML = '<div class="tag-entry">No tags available</div>';
            return;
        }
        
        console.log('Tags received, showing simple test first');
        console.log('=== TAGS BEING RENDERED ===');
        console.log('Tags array:', tags);
        console.log('Tags length:', tags.length);
        if (tags.length > 0) {
            console.log('First tag structure:', tags[0]);
            console.log('First tag keys:', Object.keys(tags[0]));
        }
        
        // Update the state with the tags
        console.log('=== UPDATING STATE ===');
        console.log('Before update - this.state.tags length:', this.state.tags.length);
        console.log('Before update - this.state.originalTags length:', this.state.originalTags.length);
        
        // Only update originalTags if we're not filtering (i.e., if filteredTags is null)
        // This preserves the original data for when filters are reset to "All"
        if (filteredTags === null) {
            this.state.originalTags = [...tags];
        }
        
        // Always update the current tags for display
        this.state.tags = [...tags];
        
        console.log('After update - this.state.tags length:', this.state.tags.length);
        console.log('After update - this.state.originalTags length:', this.state.originalTags.length);
        
        // Clear existing content
        availableTagsContainer.innerHTML = '';

        // Create organized structure with filter headers but no collapsible functionality
        const tagList = document.createElement('div');
        tagList.className = 'tag-list';

        // Add "Select All" checkbox
        const selectAllContainer = document.createElement('div');
        selectAllContainer.className = 'd-flex align-items-center gap-3 mb-2 px-3';
        selectAllContainer.innerHTML = `
            <label class="d-flex align-items-center gap-2 cursor-pointer mb-0 select-all-container">
                <input type="checkbox" id="selectAllAvailable" class="custom-checkbox">
                <span class="text-secondary fw-semibold">SELECT ALL</span>
            </label>
        `;
        tagList.appendChild(selectAllContainer);

        // Add event listener for available tags select all checkbox
        const selectAllAvailable = document.getElementById('selectAllAvailable');
        if (selectAllAvailable && !selectAllAvailable.hasAttribute('data-listener-added')) {
            selectAllAvailable.setAttribute('data-listener-added', 'true');
            selectAllAvailable.addEventListener('change', async (e) => {
                // Save current state for undo before making changes
                try {
                    await fetch('/api/save-selection-state', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            action_type: 'select_all_checkbox'
                        })
                    });
                    console.log('Selection state saved for undo (main select all)');
                } catch (error) {
                    console.warn('Failed to save selection state for undo:', error);
                    // Continue with the operation even if undo save fails
                }
                
                console.log('Select All Available checkbox changed:', e.target.checked);
                const isChecked = e.target.checked;
                
                // Get all visible tag checkboxes in available tags
                const availableCheckboxes = document.querySelectorAll('#availableTags .tag-checkbox');
                console.log('Found available tag checkboxes:', availableCheckboxes.length);
                
                availableCheckboxes.forEach(checkbox => {
                    checkbox.checked = isChecked;
                    const tag = this.state.tags.find(t => t['Product Name*'] === checkbox.value);
                    if (tag) {
                        if (isChecked) {
                            if (!this.state.persistentSelectedTags.includes(tag['Product Name*'])) {
                                this.state.persistentSelectedTags.push(tag['Product Name*']);
                            }
                        } else {
                            const index = this.state.persistentSelectedTags.indexOf(tag['Product Name*']);
                            if (index > -1) {
                                this.state.persistentSelectedTags.splice(index, 1);
                            }
                        }
                    }
                });
                
                // Update the regular selectedTags set to match persistent ones
                this.state.selectedTags = new Set(this.state.persistentSelectedTags);
                
                // Update selected tags display
                const selectedTagObjects = this.state.persistentSelectedTags.map(name =>
                    this.state.tags.find(t => t['Product Name*'] === name)
                ).filter(Boolean);
                
                this.updateSelectedTags(selectedTagObjects);
                
                // Update available tags display to reflect selection changes
                this.efficientlyUpdateAvailableTagsDisplay();
                
                // Update select all checkbox state
                this.updateSelectAllCheckboxes();
            });
        } else if (selectAllAvailable) {
            console.log('Select All Available checkbox already has listener');
        } else {
            console.log('Select All Available checkbox not found');
        }

        // CRITICAL FIX: For JSON matched tags, skip organization entirely and render directly
        const isJsonMatchedSession = tags.some(tag => tag.Source && tag.Source.includes('JSON Match'));
        
        let organizedTags;
        if (isJsonMatchedSession) {
            console.log('CRITICAL FIX: JSON matched session detected, skipping organization and rendering directly');
            // For JSON matched tags, render them directly without organization
            this.renderJsonMatchedTags(tags);
            return;
        } else {
            // Organize tags by vendor, brand, product type, weight (but without collapsible functionality)
            console.log('About to organize tags, tags length:', tags.length);
            try {
                organizedTags = this.organizeBrandCategories(tags);
                console.log('Tags organized successfully, vendor count:', organizedTags.size);
            } catch (error) {
                console.error('Error organizing tags:', error);
                // Fallback to simple list if organization fails
                availableTagsContainer.innerHTML = '<div class="tag-entry">Error organizing tags: ' + error.message + '</div>';
                return;
            }
        }
        
        // Create vendor sections
        if (!organizedTags || organizedTags.size === 0) {
            console.log('No organized tags, showing simple list');
            // Fallback to simple list
            const sortedSimple = this._sortByLikenessIfRef(tags);
            sortedSimple.forEach(tag => {
            // Use cleaned displayName for logging consistency
            const displayName = tag.displayName || tag['Product Name*'] || tag.ProductName || tag.Description || 'Unnamed Product';
            console.log('Creating tag element for:', displayName);
            const tagElement = this.createTagElement(tag, false);
            console.log('Tag element created:', tagElement);
            tagList.appendChild(tagElement);
        });
                    availableTagsContainer.appendChild(tagList);
        this.updateSelectAllCheckboxes();
        
        // Ensure Select All checkbox is properly initialized
        this.initializeSelectAllCheckbox();
            return;
        }
        
        const sortedVendors = Array.from(organizedTags.entries())
            .sort(([a], [b]) => (a || '').localeCompare(b || ''));

        sortedVendors.forEach(([vendor, brandGroups]) => {
            const vendorSection = document.createElement('div');
            vendorSection.className = 'vendor-section mb-3';
            
            // Create vendor header with checkbox and collapse functionality
            const vendorHeader = document.createElement('h5');
            vendorHeader.className = 'vendor-header mb-2 d-flex align-items-center cursor-pointer';
            vendorHeader.addEventListener('click', (e) => {
                if (e.target.type === 'checkbox') return; // Don't collapse if clicking checkbox
                if (this.state.isSearching) return; // Don't collapse while searching
                const vendorContent = vendorSection.querySelector('.vendor-content');
                const isCollapsed = vendorContent.classList.contains('collapsed');
                vendorContent.classList.toggle('collapsed', !isCollapsed);
                vendorHeader.querySelector('.collapse-icon').textContent = isCollapsed ? '▼' : '▶';
                
                // Remove the instructional blurb when any chevron is clicked
                this.removeDropdownInstructionBlurb();
            });
            
            const vendorCheckbox = document.createElement('input');
            vendorCheckbox.type = 'checkbox';
            vendorCheckbox.className = 'select-all-checkbox me-2';
            vendorCheckbox.addEventListener('change', (e) => {
                const isChecked = e.target.checked;
                // Only iterate tag checkboxes within this vendor section
                const checkboxes = vendorSection.querySelectorAll('input.tag-checkbox');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = isChecked;
                    if (checkbox.classList.contains('tag-checkbox')) {
                        const tag = this.state.tags.find(t => t['Product Name*'] === checkbox.value);
                        if (tag) {
                            if (isChecked) {
                                if (!this.state.persistentSelectedTags.includes(tag['Product Name*'])) {
                                    this.state.persistentSelectedTags.push(tag['Product Name*']);
                                }
                            } else {
                                const index = this.state.persistentSelectedTags.indexOf(tag['Product Name*']);
                                if (index > -1) {
                                    this.state.persistentSelectedTags.splice(index, 1);
                                }
                            }
                        }
                    }
                });
                this.state.selectedTags = new Set(this.state.persistentSelectedTags);
                const selectedTagObjects = this.state.persistentSelectedTags.map(name =>
                    this.state.tags.find(t => t['Product Name*'] === name)
                ).filter(Boolean);
                this.updateSelectedTags(selectedTagObjects);
                this.efficientlyUpdateAvailableTagsDisplay();
            });
            
            vendorHeader.appendChild(vendorCheckbox);
            vendorHeader.appendChild(document.createTextNode(vendor));
            vendorHeader.appendChild(document.createElement('span')).className = 'collapse-icon ms-auto';
            
            // Check if any filters are active to determine initial collapse state
            const hasActiveFilters = this.hasActiveFilters();
            const shouldStartCollapsed = this.state.isSearching ? false : !hasActiveFilters;
            
            vendorHeader.querySelector('.collapse-icon').textContent = shouldStartCollapsed ? '▶' : '▼';
            vendorSection.appendChild(vendorHeader);
            tagList.appendChild(vendorSection);

            // Create vendor content container
            const vendorContent = document.createElement('div');
            vendorContent.className = 'vendor-content';
            if (shouldStartCollapsed) {
                vendorContent.classList.add('collapsed');
            }
            vendorSection.appendChild(vendorContent);

            // Create brand sections
            const sortedBrands = Array.from(brandGroups.entries())
                .sort(([a], [b]) => (a || '').localeCompare(b || ''));

            sortedBrands.forEach(([brand, productTypeGroups]) => {
                const brandSection = document.createElement('div');
                brandSection.className = 'brand-section ms-3 mb-2';
                
                            // Create brand header with checkbox and collapse functionality
            const brandHeader = document.createElement('h6');
            brandHeader.className = 'brand-header mb-2 d-flex align-items-center cursor-pointer';
            brandHeader.addEventListener('click', (e) => {
                if (e.target.type === 'checkbox') return; // Don't collapse if clicking checkbox
                if (this.state.isSearching) return; // Don't collapse while searching
                const brandContent = brandSection.querySelector('.brand-content');
                const isCollapsed = brandContent.classList.contains('collapsed');
                brandContent.classList.toggle('collapsed', !isCollapsed);
                brandHeader.querySelector('.collapse-icon').textContent = isCollapsed ? '▼' : '▶';
                
                // Remove the instructional blurb when any chevron is clicked
                this.removeDropdownInstructionBlurb();
            });
                
                const brandCheckbox = document.createElement('input');
                brandCheckbox.type = 'checkbox';
                brandCheckbox.className = 'select-all-checkbox me-2';
            brandCheckbox.addEventListener('change', (e) => {
                const isChecked = e.target.checked;
                // Only iterate tag checkboxes within this brand section
                const checkboxes = brandSection.querySelectorAll('input.tag-checkbox');
                checkboxes.forEach(checkbox => {
                        checkbox.checked = isChecked;
                        if (checkbox.classList.contains('tag-checkbox')) {
                            const tag = this.state.tags.find(t => t['Product Name*'] === checkbox.value);
                            if (tag) {
                                if (isChecked) {
                                    if (!this.state.persistentSelectedTags.includes(tag['Product Name*'])) {
                                        this.state.persistentSelectedTags.push(tag['Product Name*']);
                                    }
                                } else {
                                    const index = this.state.persistentSelectedTags.indexOf(tag['Product Name*']);
                                    if (index > -1) {
                                        this.state.persistentSelectedTags.splice(index, 1);
                                    }
                                }
                            }
                        }
                    });
                    this.state.selectedTags = new Set(this.state.persistentSelectedTags);
                    const selectedTagObjects = this.state.persistentSelectedTags.map(name =>
                        this.state.tags.find(t => t['Product Name*'] === name)
                    ).filter(Boolean);
                    this.updateSelectedTags(selectedTagObjects);
                    this.efficientlyUpdateAvailableTagsDisplay();
                });
                
                brandHeader.appendChild(brandCheckbox);
                brandHeader.appendChild(document.createTextNode(brand));
                brandHeader.appendChild(document.createElement('span')).className = 'collapse-icon ms-auto';
                
                // Check if any filters are active to determine initial collapse state
                const hasActiveFilters = this.hasActiveFilters();
                const shouldStartCollapsed = this.state.isSearching ? false : !hasActiveFilters;
                
                brandHeader.querySelector('.collapse-icon').textContent = shouldStartCollapsed ? '▶' : '▼';
                vendorContent.appendChild(brandSection);
                brandSection.appendChild(brandHeader);

                // Create brand content container
                const brandContent = document.createElement('div');
                brandContent.className = 'brand-content';
                if (shouldStartCollapsed) {
                    brandContent.classList.add('collapsed');
                }
                brandSection.appendChild(brandContent);

                // Create product type sections
                const sortedProductTypes = Array.from(productTypeGroups.entries())
                    .sort(([a], [b]) => (a || '').localeCompare(b || ''));

                sortedProductTypes.forEach(([productType, weightGroups]) => {
                    const productTypeSection = document.createElement('div');
                    productTypeSection.className = 'product-type-section ms-3 mb-2';
                    
                    // Create product type header with checkbox and collapse functionality
                    const typeHeader = document.createElement('div');
                    typeHeader.className = 'product-type-header mb-2 d-flex align-items-center cursor-pointer';
                    typeHeader.addEventListener('click', (e) => {
                        if (e.target.type === 'checkbox') return; // Don't collapse if clicking checkbox
                        if (this.state.isSearching) return; // Don't collapse while searching
                        const productTypeContent = productTypeSection.querySelector('.product-type-content');
                        const isCollapsed = productTypeContent.classList.contains('collapsed');
                        productTypeContent.classList.toggle('collapsed', !isCollapsed);
                        typeHeader.querySelector('.collapse-icon').textContent = isCollapsed ? '▼' : '▶';
                        
                        // Remove the instructional blurb when any chevron is clicked
                        this.removeDropdownInstructionBlurb();
                    });
                    
                    const productTypeCheckbox = document.createElement('input');
                    productTypeCheckbox.type = 'checkbox';
                    productTypeCheckbox.className = 'select-all-checkbox me-2';
                    productTypeCheckbox.addEventListener('change', (e) => {
                        const isChecked = e.target.checked;
                        // Only iterate tag checkboxes within this product type section
                        const checkboxes = productTypeSection.querySelectorAll('input.tag-checkbox');
                        checkboxes.forEach(checkbox => {
                            checkbox.checked = isChecked;
                            if (checkbox.classList.contains('tag-checkbox')) {
                                const tag = this.state.tags.find(t => t['Product Name*'] === checkbox.value);
                                if (tag) {
                                    if (isChecked) {
                                        if (!this.state.persistentSelectedTags.includes(tag['Product Name*'])) {
                                            this.state.persistentSelectedTags.push(tag['Product Name*']);
                                        }
                                    } else {
                                        const index = this.state.persistentSelectedTags.indexOf(tag['Product Name*']);
                                        if (index > -1) {
                                            this.state.persistentSelectedTags.splice(index, 1);
                                        }
                                    }
                                }
                            }
                        });
                        this.state.selectedTags = new Set(this.state.persistentSelectedTags);
                        const selectedTagObjects = this.state.persistentSelectedTags.map(name =>
                            this.state.tags.find(t => t['Product Name*'] === name)
                        ).filter(Boolean);
                        this.updateSelectedTags(selectedTagObjects);
                        this.efficientlyUpdateAvailableTagsDisplay();
                    });
                    
                    typeHeader.appendChild(productTypeCheckbox);
                    typeHeader.appendChild(document.createTextNode(productType));
                    typeHeader.appendChild(document.createElement('span')).className = 'collapse-icon ms-auto';
                    
                    // Check if any filters are active to determine initial collapse state
                    const hasActiveFilters = this.hasActiveFilters();
                    const shouldStartCollapsed = this.state.isSearching ? false : !hasActiveFilters;
                    
                    typeHeader.querySelector('.collapse-icon').textContent = shouldStartCollapsed ? '▶' : '▼';
                    brandContent.appendChild(productTypeSection);
                    productTypeSection.appendChild(typeHeader);

                    // Create product type content container
                    const productTypeContent = document.createElement('div');
                    productTypeContent.className = 'product-type-content';
                    if (shouldStartCollapsed) {
                        productTypeContent.classList.add('collapsed');
                    }
                    productTypeSection.appendChild(productTypeContent);

                    // Create weight sections
                    const sortedWeights = Array.from(weightGroups.entries())
                        .sort(([a], [b]) => (a || '').localeCompare(b || ''));

                    sortedWeights.forEach(([weight, tags]) => {
                        const weightSection = document.createElement('div');
                        weightSection.className = 'weight-section ms-3 mb-1';
                        
                        // Create weight header with checkbox and collapse functionality
                        const weightHeader = document.createElement('div');
                        weightHeader.className = 'weight-header mb-1 d-flex align-items-center cursor-pointer';
                        weightHeader.addEventListener('click', (e) => {
                            if (e.target.type === 'checkbox') return; // Don't collapse if clicking checkbox
                            if (this.state.isSearching) return; // Don't collapse while searching
                            const weightContent = weightSection.querySelector('.weight-content');
                            const isCollapsed = weightContent.classList.contains('collapsed');
                            weightContent.classList.toggle('collapsed', !isCollapsed);
                            weightHeader.querySelector('.collapse-icon').textContent = isCollapsed ? '▼' : '▶';
                            
                            // Remove the instructional blurb when any chevron is clicked
                            this.removeDropdownInstructionBlurb();
                        });
                        
                        const weightCheckbox = document.createElement('input');
                        weightCheckbox.type = 'checkbox';
                        weightCheckbox.className = 'select-all-checkbox me-2';
                        weightCheckbox.addEventListener('change', (e) => {
                            const isChecked = e.target.checked;
                            // Only iterate over tag checkboxes for speed
                            const checkboxes = weightSection.querySelectorAll('input.tag-checkbox');
                            checkboxes.forEach(checkbox => {
                                checkbox.checked = isChecked;
                                if (checkbox.classList.contains('tag-checkbox')) {
                                    const tag = this.state.tags.find(t => t['Product Name*'] === checkbox.value);
                                    if (tag) {
                                        if (isChecked) {
                                            if (!this.state.persistentSelectedTags.includes(tag['Product Name*'])) {
                                                this.state.persistentSelectedTags.push(tag['Product Name*']);
                                            }
                                        } else {
                                            const index = this.state.persistentSelectedTags.indexOf(tag['Product Name*']);
                                            if (index > -1) {
                                                this.state.persistentSelectedTags.splice(index, 1);
                                            }
                                        }
                                    }
                                }
                            });
                            this.state.selectedTags = new Set(this.state.persistentSelectedTags);
                            const selectedTagObjects = this.state.persistentSelectedTags.map(name =>
                                this.state.tags.find(t => t['Product Name*'] === name)
                            ).filter(Boolean);
                            this.updateSelectedTags(selectedTagObjects);
                            this.efficientlyUpdateAvailableTagsDisplay();
                        });
                        
                        weightHeader.appendChild(weightCheckbox);
                        weightHeader.appendChild(document.createTextNode(weight));
                        weightHeader.appendChild(document.createElement('span')).className = 'collapse-icon ms-auto';
                        
                        // Weight sections should always start expanded
                        const shouldStartCollapsed = false;
                        
                        weightHeader.querySelector('.collapse-icon').textContent = shouldStartCollapsed ? '▶' : '▼';
                        productTypeContent.appendChild(weightSection);
                        weightSection.appendChild(weightHeader);

                        // Create weight content container
                        const weightContent = document.createElement('div');
                        weightContent.className = 'weight-content';
                        if (shouldStartCollapsed) {
                            weightContent.classList.add('collapsed');
                        }
                        weightSection.appendChild(weightContent);

                        // Add individual tags (sorted by likeness if a reference name is present)
                        const tagsToRender = this._sortByLikenessIfRef(tags);
                        tagsToRender.forEach(tag => {
                            const tagElement = this.createTagElement(tag, false);
                            weightContent.appendChild(tagElement);
                        });
                    });
                });
            });
        });

        availableTagsContainer.appendChild(tagList);

        // Add event listeners
        this.updateSelectAllCheckboxes();
        this.initializeSelectAllCheckbox();
    },

    createTagElement(tag, isForSelectedTags = false) {
        // For JSON matched tags and educated guess tags, prioritize the matched database display information
        let displayName;
        if (tag.Source && (tag.Source.includes('JSON Match') || tag.Source.includes('Educated Guess'))) {
            // JSON matched tags and educated guess tags: use matched database product name
            displayName = tag.displayName || tag['Product Name*'] || tag.ProductName || tag.Description || 'Unnamed Product';
        } else {
            // Regular tags: use standard fallback chain
            displayName = tag.displayName || tag['Product Name*'] || tag.ProductName || tag.Description || 'Unnamed Product';
        }
        
        console.log('Creating tag element for:', displayName);
        
        // Create the row container
        const row = document.createElement('div');
        row.className = 'tag-row d-flex align-items-center';

        // Checkbox (leftmost)
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'tag-checkbox me-2';
        
        // Use the cleaned display name for the checkbox value
        checkbox.value = displayName;
        checkbox.checked = this.state.persistentSelectedTags.includes(displayName);
        console.log('Checkbox created for:', displayName, 'value:', checkbox.value, 'checked:', checkbox.checked);
        
        // Add event listener with proper error handling and improved logic
        const handleCheckboxChange = async (e) => {
            console.log('=== TAG CHECKBOX EVENT TRIGGERED ===');
            console.log('Tag checkbox changed:', displayName, 'checked:', e.target.checked);
            console.log('Event target:', e.target);
            console.log('Event type:', e.type);
            console.log('Event bubbles:', e.bubbles);
            console.log('Event cancelable:', e.cancelable);
            
            // Prevent event handling during drag operations
            if (e.target.hasAttribute('data-reordering') || e.target.hasAttribute('data-drag-disabled')) {
                console.log('Ignoring tag selection change during drag operation');
                return;
            }
            
            // Save current state for undo before making changes
            try {
                await fetch('/api/save-selection-state', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action_type: 'checkbox_selection'
                    })
                });
                console.log('Selection state saved for undo');
            } catch (error) {
                console.warn('Failed to save selection state for undo:', error);
                // Continue with the operation even if undo save fails
            }
            
            // Ensure the checkbox state is properly updated
            const isChecked = e.target.checked;
            console.log('Processing checkbox change:', displayName, 'checked:', isChecked);
            
            // Update persistent selected tags with proper array handling
            if (isChecked) {
                if (!this.state.persistentSelectedTags.includes(displayName)) {
                    this.state.persistentSelectedTags.push(displayName);
                    console.log('Added tag to persistent selected tags:', displayName);
                    console.log('Current persistentSelectedTags:', this.state.persistentSelectedTags);
                }
            } else {
                const index = this.state.persistentSelectedTags.indexOf(displayName);
                if (index > -1) {
                    this.state.persistentSelectedTags.splice(index, 1);
                    console.log('Removed tag from persistent selected tags:', displayName);
                    console.log('Current persistentSelectedTags:', this.state.persistentSelectedTags);
                }
            }
            
            // Update the regular selectedTags set to match persistent ones
            this.state.selectedTags = new Set(this.state.persistentSelectedTags);
            console.log('Updated selectedTags set:', this.state.selectedTags);
            
            // Call the main handler
            this.handleTagSelection(e, tag);
        };
        
        // Bind change handler only for available tags. For selected tags we use a delegated handler.
        if (!isForSelectedTags) {
            checkbox.removeEventListener('change', handleCheckboxChange);
            checkbox.addEventListener('change', handleCheckboxChange);
        } else {
            // For selected list, prevent any per-checkbox change handlers from firing
            checkbox.addEventListener('change', (e) => {
                if (typeof e.stopImmediatePropagation === 'function') e.stopImmediatePropagation();
                e.stopPropagation();
                e.preventDefault();
            }, { capture: true });
        }
        
        // Ensure the checkbox is not disabled by drag-and-drop manager
        checkbox.style.pointerEvents = 'auto';
        checkbox.removeAttribute('data-drag-disabled');
        checkbox.removeAttribute('data-reordering');
        
        // Store the checkbox state in a data attribute for debugging
        checkbox.setAttribute('data-tag-name', displayName);
        checkbox.setAttribute('data-is-selected-tag', isForSelectedTags.toString());
        
        // Also add a click event listener for debugging
        const handleCheckboxClick = (e) => {
            console.log('=== TAG CHECKBOX CLICK EVENT ===');
            console.log('Tag checkbox clicked:', displayName);
            console.log('Checkbox checked state:', e.target.checked);
            console.log('Event target:', e.target);
            console.log('Event type:', e.type);
            console.log('Event bubbles:', e.bubbles);
            console.log('Event cancelable:', e.cancelable);
            console.log('Event defaultPrevented:', e.defaultPrevented);
        };
        
        const handleCheckboxMouseDown = (e) => {
            console.log('=== TAG CHECKBOX MOUSEDOWN EVENT ===');
            console.log('Tag checkbox mousedown:', displayName);
            console.log('Event target:', e.target);
        };
        
        // Remove any existing event listeners to prevent duplicates
        checkbox.removeEventListener('click', handleCheckboxClick);
        checkbox.removeEventListener('mousedown', handleCheckboxMouseDown);
        
        // Add event listeners
        checkbox.addEventListener('click', handleCheckboxClick);
        checkbox.addEventListener('mousedown', handleCheckboxMouseDown);
        console.log('Event listener attached to checkbox for:', displayName);

        // Tag entry (colored)
        const tagElement = document.createElement('div');
        tagElement.className = 'tag-item d-flex align-items-center p-1 mb-1';
        
        // Add special styling for JSON matched tags and educated guess tags
        if (tag.Source && (tag.Source === 'JSON Match' || tag.Source.includes('Educated Guess'))) {
          tagElement.classList.add('json-matched-tag');
          tagElement.style.border = '2px solid #28a745';
          tagElement.style.backgroundColor = 'rgba(40, 167, 69, 0.1)';
          tagElement.style.borderRadius = '8px';
        }
        
        // Set data-lineage attribute for CSS coloring on both row and tagElement
        const lineage = tag.lineage || tag.Lineage || 'MIXED';
        let displayLineage = lineage;
        
        // Force nonclassic products to show MIXED (dark blue) instead of CBD (yellow)
        const productType = tag['Product Type*'] || tag.productType || '';
        const classicTypes = ['flower', 'pre-roll', 'concentrate', 'infused pre-roll', 'solventless concentrate', 'vape cartridge', 'rso/co2 tankers'];
        const isNonclassic = !classicTypes.map(ct => ct.toLowerCase()).includes(productType.toLowerCase());
        
        if (isNonclassic && (lineage === 'CBD' || lineage === 'CBD_BLEND')) {
          displayLineage = 'MIXED';
        }
        
        // Keep HYBRID as HYBRID - hybrids should be green, not blue
        // Only nonclassic products should be MIXED (blue)
        
        if (displayLineage) {
          tagElement.dataset.lineage = displayLineage.toUpperCase();
          row.dataset.lineage = displayLineage.toUpperCase();  // Add lineage to row element too
        } else {
          tagElement.dataset.lineage = 'MIXED';
          row.dataset.lineage = 'MIXED';  // Add lineage to row element too
        }
        tagElement.dataset.tagId = tag.tagId;
        tagElement.dataset.vendor = tag.vendor;
        tagElement.dataset.brand = tag.brand;
        tagElement.dataset.productType = tag.productType;
        tagElement.dataset.weight = tag.weight;

        // Make the entire tag element clickable to toggle checkbox (but only for available tags)
        // For selected tags, only allow checkbox clicking to toggle selection
        if (!isForSelectedTags) {
            tagElement.style.cursor = 'pointer';
            tagElement.addEventListener('click', (e) => {
                try {
                    // Don't trigger if clicking on the checkbox itself, lineage dropdown, or DOH dropdown
                    if (e.target === checkbox || e.target.classList.contains('lineage-select') || 
                        e.target.closest('.lineage-select') || e.target.classList.contains('lineage-dropdown') ||
                        e.target.closest('.lineage-dropdown') || e.target.classList.contains('doh-select') ||
                        e.target.closest('.doh-select') || e.target.classList.contains('doh-dropdown') ||
                        e.target.closest('.doh-dropdown')) {
                        return;
                    }
                    
                    // Prevent if drag operation is in progress
                    if (checkbox.hasAttribute('data-reordering') || checkbox.hasAttribute('data-drag-disabled')) {
                        console.log('Ignoring tag element click during drag operation');
                        return;
                    }
                    
                    // Toggle the checkbox
                    checkbox.checked = !checkbox.checked;
                    // Trigger the change event
                    checkbox.dispatchEvent(new Event('change', { bubbles: true }));
                } catch (error) {
                    console.error('Error in tag element click handler:', error);
                    // Prevent the error from causing the page to exit
                    e.preventDefault();
                    e.stopPropagation();
                }
            });
        } else {
            // For selected tags, only allow checkbox clicking to toggle selection
            tagElement.style.cursor = 'default';
        }

        const tagInfo = document.createElement('div');
        tagInfo.className = 'tag-info flex-grow-1 d-flex align-items-center';
        const tagName = document.createElement('div');
        tagName.className = 'tag-name d-inline-block me-2';
        
        // Update checkbox value to use the cleaned display name
        checkbox.value = displayName;
        checkbox.checked = this.state.persistentSelectedTags.includes(displayName);
        
        // Log JSON matched tag display logic
        if (tag.Source && (tag.Source.includes('JSON Match') || tag.Source.includes('Educated Guess'))) {
            console.log('JSON matched/educated guess tag display logic:', {
                source: tag.Source,
                displayName: tag.displayName,
                productName: tag['Product Name*'],
                finalDisplayName: displayName
            });
        }
        
        // Remove 'by ...' patterns (with or without hyphen)
        let cleanedName = displayName.replace(/ by [^-]*$/i, ''); // Remove "by ..." at the end
        cleanedName = cleanedName.replace(/ by [^-]+(?= -)/i, ''); // Remove "by ..." before hyphen
        cleanedName = cleanedName.replace(/-/g, '\u2011');
        tagName.textContent = cleanedName;
        tagInfo.appendChild(tagName);
        

        

        
        // Add DOH and High CBD/THC images if applicable
        const dohValue = (tag.DOH || '').toString().toUpperCase();
        const productTypeForImages = (tag['Product Type*'] || '').toString().toLowerCase();
        
        // Create image container for dynamic updates
        const imageContainer = document.createElement('span');
        imageContainer.className = 'doh-image-container';
        
        // Function to update images based on DOH status with performance optimization
        const updateDohImage = (status) => {
            const startTime = performanceUtils.startTiming();
            
            // Clear existing images efficiently
            while (imageContainer.firstChild) {
                imageContainer.removeChild(imageContainer.firstChild);
            }
            
            if (status === 'CBD') {
                // Add High CBD image with optimized loading
                const highCbdImg = document.createElement('img');
                highCbdImg.src = '/static/img/HighCBD.png';
                highCbdImg.alt = 'High CBD';
                highCbdImg.title = 'High CBD Product';
                highCbdImg.loading = 'lazy'; // Native lazy loading
                highCbdImg.style.cssText = 'height:24px;width:auto;margin-left:6px;vertical-align:middle';
                imageContainer.appendChild(highCbdImg);
            } else if (status === 'THC') {
                // Add High THC image with optimized loading
                const highThcImg = document.createElement('img');
                highThcImg.src = '/static/img/HighTHC.png';
                highThcImg.alt = 'High THC';
                highThcImg.title = 'High THC Product';
                highThcImg.loading = 'lazy';
                highThcImg.style.cssText = 'height:24px;width:auto;margin-left:6px;vertical-align:middle';
                imageContainer.appendChild(highThcImg);
            } else if (status === 'DOH') {
                // Add regular DOH image with optimized loading
                const dohImg = document.createElement('img');
                dohImg.src = '/static/img/DOH.png';
                dohImg.alt = 'DOH Compliant';
                dohImg.title = 'DOH Compliant Product';
                dohImg.loading = 'lazy';
                dohImg.style.cssText = 'height:21px;width:auto;margin-left:6px;vertical-align:middle';
                imageContainer.appendChild(dohImg);
            }
            // NONE shows no image
            
            performanceUtils.endTiming(startTime, 'DOH image update');
        };
        
        // Set initial image based on current DOH status
        let initialDohStatus = 'NONE'; // Default to NONE
        
        // Check explicit DOH field first
        if (dohValue === 'DOH' || dohValue === 'YES' || dohValue === 'Y') {
            initialDohStatus = 'DOH';
        } else if (dohValue === 'THC') {
            initialDohStatus = 'THC';
        } else if (dohValue === 'CBD') {
            initialDohStatus = 'CBD';
        } 
        // Then check product type for High CBD/THC indicators (DOH High CBD, DOH High THC)
        else if (productTypeForImages.startsWith('high cbd') || productTypeForImages.includes('doh high cbd')) {
            initialDohStatus = 'CBD';
        } else if (productTypeForImages.startsWith('high thc') || productTypeForImages.includes('doh high thc') || productTypeForImages.includes('high thc')) {
            initialDohStatus = 'THC';
        }
        
        updateDohImage(initialDohStatus);
        tagInfo.appendChild(imageContainer);
        
        // Add JSON match indicator if this tag came from JSON matching or educated guessing
        if (tag.Source && (tag.Source.includes('JSON Match') || tag.Source.includes('Educated Guess'))) {
          const jsonBadge = document.createElement('span');
          jsonBadge.className = 'badge bg-success me-2';
          jsonBadge.style.fontSize = '0.7rem';
          jsonBadge.style.padding = '2px 6px';
          jsonBadge.textContent = tag.Source.includes('Educated Guess') ? 'AI' : 'JSON';
          jsonBadge.title = `This item was ${tag.Source.includes('Educated Guess') ? 'inferred by AI' : 'matched from JSON data'} (${tag.Source})`;
          tagInfo.appendChild(jsonBadge);
        }
        // Create lineage dropdown
        const lineageSelect = document.createElement('select');
        lineageSelect.className = 'form-select form-select-sm lineage-select lineage-dropdown lineage-dropdown-mini';
        lineageSelect.style.height = '28px';
        lineageSelect.style.backgroundColor = 'rgba(255, 255, 255, 0.15)';
        lineageSelect.style.border = '1px solid rgba(255, 255, 255, 0.2)';
        lineageSelect.style.borderRadius = '6px';
        lineageSelect.style.cursor = 'pointer';
        lineageSelect.style.color = '#fff';
        lineageSelect.style.backdropFilter = 'blur(10px)';
        lineageSelect.style.transition = 'all 0.2s ease';
        lineageSelect.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
        // Style the dropdown options
        const style = document.createElement('style');
        style.textContent = `
            .lineage-select option {
                background-color: rgba(30, 30, 30, 0.95);
                color: #fff;
                padding: 8px;
            }
            .lineage-select:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.3);
            }
            .lineage-select:focus {
                background-color: rgba(255, 255, 255, 0.25);
                border-color: rgba(255, 255, 255, 0.4);
                box-shadow: 0 0 0 0.2rem rgba(255, 255, 255, 0.1);
            }
        `;
        document.head.appendChild(style);
        // Add lineage options
        const uniqueLineages = [
            { value: 'SATIVA', label: 'S' },
            { value: 'INDICA', label: 'I' },
            { value: 'HYBRID', label: 'H' },
            { value: 'HYBRID/INDICA', label: 'H/I' },
            { value: 'HYBRID/SATIVA', label: 'H/S' },
            { value: 'CBD', label: 'CBD' },
            { value: 'PARA', label: 'P' },
            { value: 'MIXED', label: 'THC' }
        ];
        uniqueLineages.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option.value;
            optionElement.textContent = option.label;
            if ((lineage === option.value) || (option.value === 'CBD' && lineage === 'CBD_BLEND')) {
                optionElement.selected = true;
            }
            lineageSelect.appendChild(optionElement);
        });
        lineageSelect.value = lineage;
        if (tag.productType === 'Paraphernalia' || tag['Product Type*'] === 'Paraphernalia') {
            lineageSelect.disabled = true;
            lineageSelect.style.opacity = '0.7';
        }
        lineageSelect.addEventListener('change', async (e) => {
            const newLineage = e.target.value;
            const prevValue = lineage;
            lineageSelect.disabled = true;
            // Show temporary 'Saving...' option
            const savingOption = document.createElement('option');
            savingOption.value = '';
            savingOption.textContent = 'Saving...';
            savingOption.selected = true;
            savingOption.disabled = true;
            lineageSelect.appendChild(savingOption);
            try {
                await this.updateLineageOnBackend(tag['Product Name*'], newLineage);
                // On success, update tag lineage in state
                tag.lineage = newLineage;
                tag.Lineage = newLineage;
                lineageSelect.value = newLineage;
                // Update the data-lineage attribute
                tagElement.dataset.lineage = newLineage.toUpperCase();
                
                // Remove saving option
                lineageSelect.removeChild(savingOption);
            } catch (error) {
                console.error('Failed to update lineage:', error);
                // On failure, revert to previous value
                lineageSelect.value = prevValue;
                // Show error message
                alert('Failed to update lineage: ' + error.message);
                // Remove saving option
                if (savingOption.parentNode) {
                    lineageSelect.removeChild(savingOption);
                }
            } finally {
                lineageSelect.disabled = false;
            }
        });
        tagInfo.appendChild(lineageSelect);

        // Create DOH dropdown (same style as lineage dropdown)
        const dohSelect = document.createElement('select');
        dohSelect.className = 'form-select form-select-sm doh-select doh-dropdown doh-dropdown-mini';
        dohSelect.style.height = '28px';
        dohSelect.style.backgroundColor = 'rgba(255, 255, 255, 0.15)';
        dohSelect.style.border = '1px solid rgba(255, 255, 255, 0.2)';
        dohSelect.style.borderRadius = '6px';
        dohSelect.style.cursor = 'pointer';
        dohSelect.style.color = '#fff';
        dohSelect.style.backdropFilter = 'blur(10px)';
        dohSelect.style.transition = 'all 0.2s ease';
        dohSelect.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
        dohSelect.style.marginLeft = '4px';
        dohSelect.style.minWidth = '60px';

        // Add DOH options
        const dohOptions = [
            { value: 'NONE', label: '' },
            { value: 'DOH', label: 'DOH' },
            { value: 'THC', label: 'THC' },
            { value: 'CBD', label: 'CBD' }
        ];
        
        // Use the same logic as initialDohStatus to determine current dropdown state
        let currentDropdownStatus = 'NONE'; // Default to NONE
        
        // Check explicit DOH field first
        if (dohValue === 'DOH' || dohValue === 'YES' || dohValue === 'Y') {
            currentDropdownStatus = 'DOH';
        } else if (dohValue === 'THC') {
            currentDropdownStatus = 'THC';
        } else if (dohValue === 'CBD') {
            currentDropdownStatus = 'CBD';
        } 
        // Then check product type for High CBD/THC indicators (DOH High CBD, DOH High THC)
        else if (productTypeForImages.startsWith('high cbd') || productTypeForImages.includes('doh high cbd')) {
            currentDropdownStatus = 'CBD';
        } else if (productTypeForImages.startsWith('high thc') || productTypeForImages.includes('doh high thc') || productTypeForImages.includes('high thc')) {
            currentDropdownStatus = 'THC';
        }
        
        dohOptions.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option.value;
            optionElement.textContent = option.label;
            if (currentDropdownStatus === option.value) {
                optionElement.selected = true;
            }
            dohSelect.appendChild(optionElement);
        });

        // Prevent DOH dropdown clicks from bubbling up to tag element (optimized)
        dohSelect.addEventListener('click', (e) => {
            e.stopPropagation();
        }, { passive: true }); // Use passive listener for better performance
        
        dohSelect.addEventListener('change', async (e) => {
            const newDohStatus = e.target.value;
            const prevValue = currentDohStatus;
            
            // Immediate UI feedback - update image first for responsiveness
            updateDohImage(newDohStatus);
            
            dohSelect.disabled = true;
            
            // Show temporary 'Saving...' option
            const savingOption = document.createElement('option');
            savingOption.value = '';
            savingOption.textContent = 'Saving...';
            savingOption.selected = true;
            savingOption.disabled = true;
            dohSelect.appendChild(savingOption);
            
            try {
                const response = await fetch('/api/update-doh', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        product_name: displayName,
                        doh_status: newDohStatus
                    })
                });
                
                const data = await response.json();
                if (data.success) {
                    // On success, update tag DOH status in state
                    tag.DOH = newDohStatus;
                    tag.doh = newDohStatus;
                    dohSelect.value = newDohStatus;
                    console.log(`✅ DOH status updated for "${displayName}" to: ${newDohStatus}`);
                    
                    // Image already updated above for immediate feedback
                } else {
                    // Revert image on failure
                    updateDohImage(prevValue);
                    throw new Error(data.message || 'Failed to update DOH status');
                }
                
                // Remove saving option
                dohSelect.removeChild(savingOption);
            } catch (error) {
                console.error('Failed to update DOH status:', error);
                // On failure, revert to previous value
                dohSelect.value = prevValue;
                alert('Failed to update DOH status: ' + error.message);
                // Remove saving option
                if (savingOption.parentNode) {
                    dohSelect.removeChild(savingOption);
                }
            } finally {
                dohSelect.disabled = false;
            }
        });
        
        tagInfo.appendChild(dohSelect);
        tagElement.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            if (window.lineageEditor) {
                window.lineageEditor.openEditor(tag['Product Name*'], tag.lineage);
            }
        });
        tagInfo.appendChild(lineageSelect);
        tagElement.appendChild(checkbox);
        tagElement.appendChild(tagInfo);
        row.appendChild(tagElement);
        return row;
    },

    getLineageBadgeLabel(lineage) {
        const map = {
            'SATIVA': 'S',
            'INDICA': 'I',
            'HYBRID': 'H',
            'HYBRID/SATIVA': 'H/S',
            'HYBRID/INDICA': 'H/I',
            'CBD': 'CBD',
            'PARA': 'P',
            'MIXED': 'THC',
            'CBD_BLEND': 'CBD'
        };
        return map[(lineage || '').toUpperCase()] || '';
    },

    handleTagSelection(e, tag) {
        console.log('=== HANDLE TAG SELECTION CALLED ===');
        console.log('Event:', e);
        console.log('Tag:', tag);
        
        // Ignore changes during drag-and-drop reordering
        if (e.target.hasAttribute('data-reordering') || e.target.hasAttribute('data-drag-disabled')) {
            console.log('Ignoring tag selection change during drag operation');
            return;
        }
        
        const isChecked = e.target.checked;
        console.log('Tag selection changed:', tag && tag['Product Name*'] ? tag['Product Name*'] : 'UNDEFINED', 'checked:', isChecked);
        
        // Safety check: ensure tag exists and has required properties
        if (!tag || !tag['Product Name*']) {
            console.error('Invalid tag object received:', tag);
            return;
        }
        
        // Prevent rapid deselection issues
        if (this.isMovingTags) {
            console.log('Ignoring tag selection during tag move operation');
            return;
        }
        
        // Add debouncing for rapid deselection to prevent UI issues
        if (this.tagSelectionTimeout) {
            clearTimeout(this.tagSelectionTimeout);
        }
        
        this.tagSelectionTimeout = setTimeout(() => {
            // Update select all checkbox states after tag selection changes
            this.updateSelectAllCheckboxes();
            
            // Note: The persistent selected tags are already updated in the checkbox event handler
            // This function now focuses on UI updates and backend synchronization
            
            console.log('Persistent selected tags after change:', this.state.persistentSelectedTags);
            
            // Only use backend data - never fall back to frontend persistent tags
            // Get selected tags from backend
            console.log('=== SELECTED TAGS DEBUG ===');
            console.log('persistentSelectedTags:', this.state.persistentSelectedTags);
            console.log('this.state.tags length:', this.state.tags.length);
            console.log('this.state.originalTags length:', this.state.originalTags.length);
            
            // Debug: Show first few tags in state
            if (this.state.tags.length > 0) {
                console.log('First 3 tags in this.state.tags:');
                this.state.tags.slice(0, 3).forEach(tag => {
                    console.log(`  "${tag && tag['Product Name*'] ? tag['Product Name*'] : 'UNDEFINED'}"`);
                });
            }
            
            if (this.state.originalTags.length > 0) {
                console.log('First 3 tags in this.state.originalTags:');
                this.state.originalTags.slice(0, 3).forEach(tag => {
                    console.log(`  "${tag && tag['Product Name*'] ? tag['Product Name*'] : 'UNDEFINED'}"`);
                });
            }
            
            const selectedTagObjects = this.state.persistentSelectedTags.map(name => {
                // Safety check: ensure name is valid
                if (!name || typeof name !== 'string') {
                    console.warn('Invalid name in persistentSelectedTags:', name);
                    return null;
                }
                
                // Only use tags that exist in the current backend data
                let foundTag = this.state.tags.find(t => t && t['Product Name*'] && t['Product Name*'] === name) || 
                              this.state.originalTags.find(t => t && t['Product Name*'] && t['Product Name*'] === name);
                
                // If not found, try case-insensitive search
                if (!foundTag) {
                    foundTag = this.state.tags.find(t => t && t['Product Name*'] && t['Product Name*'].toLowerCase() === name.toLowerCase()) || 
                              this.state.originalTags.find(t => t && t['Product Name*'] && t['Product Name*'].toLowerCase() === name.toLowerCase());
                }
                
                // If still not found, create a minimal tag object for the selected tag
                if (!foundTag) {
                    console.log(`Tag "${name}" not found in state, creating minimal tag object`);
                    foundTag = {
                        'Product Name*': name,
                        'Product Brand': 'Unknown',
                        'Vendor': 'Unknown',
                        'Product Type*': 'Unknown',
                        'Lineage': 'MIXED',
                        'Source': 'Frontend Selection'
                    };
                }
                
                console.log(`Looking for tag "${name}":`, foundTag ? 'FOUND' : 'NOT FOUND');
                if (!foundTag) {
                    console.log(`  Tag name length: ${name.length}`);
                    console.log(`  Tag name characters: ${Array.from(name).map(c => c.charCodeAt(0)).join(', ')}`);
                }
                return foundTag;
            }).filter(Boolean); // Filter out null values from invalid names
            
            console.log('selectedTagObjects:', selectedTagObjects);
            console.log('selectedTagObjects length:', selectedTagObjects.length);
            
            this.updateSelectedTags(selectedTagObjects);
            
            // FIXED: Don't hide selected tags from available display - keep all items visible
            // This allows users to see all available options even after making selections
            if (isChecked && e.target.closest('#availableTags')) {
                console.log('FIXED: Not hiding selected tag from available display - keeping all items visible');
                // Tag remains visible in available list even after selection
            }
            
            // If tag was unchecked in selected list, show it in available display
            if (!isChecked && e.target.closest('#selectedTags') && tag && tag['Product Name*']) {
                // Find and show the tag in available list
                const availableTagElement = document.querySelector(`#availableTags .tag-checkbox[value="${tag['Product Name*']}"]`);
                if (availableTagElement) {
                    const tagElement = availableTagElement.closest('.tag-item');
                    if (tagElement) {
                        tagElement.style.display = 'block';
                    }
                }
                
                // Clear corresponding filters when tag is deselected
                this.clearFiltersForDeselectedTag(tag);
                
                // For JSON matched items and educated guess items, also ensure they appear in available tags
                // This is important for items that might not exist in the original Excel data
                if (tag.Source && (tag.Source === 'JSON Match' || tag.Source.includes('Educated Guess'))) {
                    console.log(`${tag.Source.includes('Educated Guess') ? 'Educated guess' : 'JSON matched'} item deselected: ${tag['Product Name*']}`);
                    // Sync with backend to ensure deselection is persisted
                    this.syncDeselectionWithBackend(tag['Product Name*']);
                }
            }
        }, 50); // 50ms debounce delay for individual tag selection
    },

    updateTagLineage(tag, lineage) {
        // Update the lineage in the tag object
        tag.lineage = lineage;
        
        // Update the color based on the new lineage
        const newColor = this.getLineageColor(lineage);
        this.updateTagColor(tag, newColor);
    },

    handleLineageChange(tagName, newLineage) {
        const tag = this.state.tags.find(t => t['Product Name*'] === tagName);
        if (tag) {
            // Update the lineage in the tag object
            tag.lineage = newLineage;
            
            // Update the color based on the new lineage
            const newColor = this.getLineageColor(newLineage);
            this.updateTagColor(tag, newColor);
            
            // Send update to backend
            this.updateLineageOnBackend(tagName, newLineage);
        }
    },

    async updateLineageOnBackend(tagName, newLineage) {
        try {
            console.log(`🔄 Updating lineage for ${tagName} to ${newLineage}`);
            
            const payload = {
                tag_name: tagName,
                "Product Name*": tagName,
                lineage: newLineage
            };
            const response = await fetch('/api/update-lineage', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error(`❌ API Error: ${errorData.error || 'Failed to update lineage'}`);
                throw new Error(errorData.error || 'Failed to update lineage');
            }

            // Update the tag in original tags as well
            const originalTag = this.state.originalTags.find(t => t['Product Name*'] === tagName);
            if (originalTag) {
                originalTag.lineage = newLineage;
                console.log(`📝 Updated tag in originalTags`);
            }

            // Update the tag in current tags list
            const currentTag = this.state.tags.find(t => t['Product Name*'] === tagName);
            if (currentTag) {
                currentTag.lineage = newLineage;
                console.log(`📝 Updated tag in current tags`);
            }

            // Optimized: Only update the specific tag elements instead of rebuilding everything
            this.updateTagLineageInUI(tagName, newLineage);
            console.log(`🎨 Updated UI elements for ${tagName}`);

            // CRITICAL FIX: Don't refresh available tags - just update the UI directly
            // This prevents the available tags list from being wiped when lineage changes
            console.log('✅ Lineage updated successfully - skipping full refresh to preserve available tags');

        } catch (error) {
            console.error('Error updating lineage:', error);
            if (window.Toast) {
                console.error('Failed to update lineage:', error.message);
            }
        }
    },

    // Optimized function to update only the specific tag's lineage in the UI
    updateTagLineageInUI(tagName, newLineage) {
        // Update lineage badge in available tags
        const availableTagElement = document.querySelector(`#availableTags [data-tag-name="${tagName}"]`);
        if (availableTagElement) {
            const lineageBadge = availableTagElement.querySelector('.lineage-badge');
            if (lineageBadge) {
                lineageBadge.textContent = newLineage;
                lineageBadge.className = `badge lineage-badge ${this.getLineageColor(newLineage)}`;
            }
        }

        // Update lineage badge in selected tags
        const selectedTagElement = document.querySelector(`#selectedTags [data-tag-name="${tagName}"]`);
        if (selectedTagElement) {
            const lineageBadge = selectedTagElement.querySelector('.lineage-badge');
            if (lineageBadge) {
                lineageBadge.textContent = newLineage;
                lineageBadge.className = `badge lineage-badge ${this.getLineageColor(newLineage)}`;
            }
        }
    },

    updateSelectedTags(tags) {
        if (!tags || !Array.isArray(tags)) {
            console.warn('updateSelectedTags called with invalid tags:', tags);
            tags = [];
        }
        
        // Prevent updates during tag move operations to avoid race conditions
        if (this.isMovingTags) {
            console.log('Ignoring updateSelectedTags during tag move operation');
            return;
        }
        
        // Performance optimization: Check if the update is actually needed
        const container = document.getElementById('selectedTags');
        if (!container) {
            console.error('Selected tags container not found');
            return;
        }
        
        // Check if the current content matches what we're about to render
        const currentTagCount = container.querySelectorAll('.tag-item').length;
        if (currentTagCount === tags.length && tags.length > 0) {
            // Quick check: if we have the same number of tags and they're not empty, 
            // we might not need to update (this is a heuristic to avoid unnecessary updates)
            const currentTagNames = Array.from(container.querySelectorAll('.tag-item')).map(el => 
                el.querySelector('.tag-checkbox')?.value || el.getAttribute('data-tag-name')
            ).filter(Boolean);
            
            const newTagNames = tags.map(tag => tag['Product Name*']).filter(Boolean);
            
            if (currentTagNames.length === newTagNames.length && 
                currentTagNames.every((name, index) => name === newTagNames[index])) {
                console.log('updateSelectedTags: No changes detected, skipping update');
                console.timeEnd('updateSelectedTags');
                return;
            }
        }
        
        // Dispatch event to notify drag and drop manager that tag updates are starting
        document.dispatchEvent(new CustomEvent('updateSelectedTags'));
        
        console.time('updateSelectedTags');
        console.log('updateSelectedTags called with tags:', tags);

        // Clear existing content
        container.innerHTML = '';

        // For JSON matched items, we want to keep them even if they don't exist in Excel data
        // So we'll be more permissive with validation
        const validTags = [];
        
        // Create a Set for O(1) lookup performance instead of O(n) .some() calls
        const originalTagNames = new Set(this.state.originalTags.map(tag => tag['Product Name*']));
        
        for (const tag of tags) {
            if (tag && tag['Product Name*']) {
                // Check if this tag exists in the original tags (Excel data) - O(1) lookup
                const existsInExcel = originalTagNames.has(tag['Product Name*']);
                
                if (existsInExcel) {
                    validTags.push(tag);
                } else {
                    // For JSON matched items, we'll keep them but mark them as "external"
                    console.log(`Tag not found in Excel data (likely JSON matched): ${tag['Product Name*']}`);
                    // Don't add to invalidTags - we'll keep these
                    validTags.push(tag);
                }
            }
        }

        // Update the regular selectedTags set to match persistent ones
        this.state.selectedTags = new Set(this.state.persistentSelectedTags);

        // Use all tags for display (including JSON matched ones)
        // IMPORTANT: For selected tags, we want to preserve the exact order from the backend
        // This is crucial for drag-and-drop reordering to work properly
        tags = validTags;
        
        // NOTE: We do NOT apply filtering to selected tags here
        // Display the selected tags in the same order as the available list for consistency
        // Filtering is only applied to available tags, not selected tags
        console.log('Displaying selected tags in available list order (no filtering applied):', tags);
        
        if (tags.length === 0) {
            // Check if we have persistent selected tags that should be displayed
            if (this.state.persistentSelectedTags && this.state.persistentSelectedTags.length > 0) {
                console.log('No backend tags but persistent tags exist, rebuilding from persistent state');
                // Rebuild from persistent state - optimized with Maps for O(1) lookup
                const tagsMap = new Map(this.state.tags.map(tag => [tag['Product Name*'], tag]));
                const originalTagsMap = new Map(this.state.originalTags.map(tag => [tag['Product Name*'], tag]));
                
                const persistentTagObjects = this.state.persistentSelectedTags.map(name => {
                    return tagsMap.get(name) || originalTagsMap.get(name);
                }).filter(Boolean);
                
                if (persistentTagObjects.length > 0) {
                    console.log('Rebuilding selected tags from persistent state:', persistentTagObjects.length);
                    // Continue with the persistent tags instead of showing empty
                    tags = persistentTagObjects;
                } else {
                    console.log('No persistent tags found, showing empty selected tags list');
                    container.innerHTML = `
                    <div class="d-flex align-items-center justify-content-center" style="min-height: 100%;">
                        <div class="text-center p-4" style="max-width: 500px;">
                            <h5 class="text-secondary fw-bold mb-4">Quick Start Guide</h5>
                            
                            <div class="text-start">
                                <div class="mb-4">
                                    <h6 class="text-secondary mb-3">1. Upload Product Data</h6>
                                    <div style="color: #b8b8b8;">
                                        <p class="mb-2 fw-bold fst-italic">📥 Download LOTs Data:</p>
                                        <ol class="ms-3 fst-italic">
                                            <li class="mb-2">Log in to app.posabit.com</li>
                                            <li class="mb-2">Navigate to Inventory → LOTs</li>
                                            <li class="mb-2">Set "Select State" to Active</li>
                                            <li class="mb-2">Click the green Search button</li>
                                            <li class="mb-2">Click the blue Download CSV button</li>
                                            <li class="mb-2">Upload the downloaded file here using the "Upload Data" button</li>
                                        </ol>
                                    </div>
                                </div>

                                <div>
                                    <h6 class="text-secondary mb-3">2. Create Labels</h6>
                                    <ol class="fst-italic ms-3" style="color: #b8b8b8;">
                                        <li class="mb-2">Browse products in the left panel</li>
                                        <li class="mb-2">Check boxes next to products to label</li>
                                        <li class="mb-2">Use filters above to find specific items</li>
                                        <li class="mb-2">Drag and drop to reorder if needed</li>
                                        <li>Click "Generate Labels" when ready</li>
                                    </ol>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                    this.updateTagCount('selected', 0);
                    return;
                }
            } else {
                console.log('No backend tags and no persistent tags, showing empty selected tags list');
                container.innerHTML = `
                    <div class="d-flex align-items-center justify-content-center" style="min-height: 100%;">
                        <div class="text-center p-4" style="max-width: 500px;">
                            <h5 class="text-secondary fw-bold mb-3">Quick Start Guide</h5>
                            
                            <div class="text-start">
                                <div class="mb-4">
                                    <h6 class="text-secondary mb-3">1. Upload Product Data</h6>
                                    <div style="color: #b8b8b8;">
                                        <p class="mb-2 fw-bold fst-italic">📥 Download LOTs Data:</p>
                                        <ol class="ms-3 fst-italic">
                                            <li class="mb-2">Log in to app.posabit.com</li>
                                            <li class="mb-2">Navigate to Inventory → LOTs</li>
                                            <li class="mb-2">Set "Select State" to Active</li>
                                            <li class="mb-2">Click the green Search button</li>
                                            <li class="mb-2">Click the blue Download CSV button</li>
                                            <li class="mb-2">Upload the downloaded file here using the "Upload Data" button</li>
                                        </ol>
                                    </div>
                                </div>

                                <div>
                                    <h6 class="text-secondary mb-3">2. Create Labels</h6>
                                    <ol class="fst-italic ms-3" style="color: #b8b8b8;">
                                        <li class="mb-2">Browse products in the left panel</li>
                                        <li class="mb-2">Check boxes next to products to label</li>
                                        <li class="mb-2">Use filters above to find specific items</li>
                                        <li class="mb-2">Drag and drop to reorder if needed</li>
                                        <li>Click "Generate Labels" when ready</li>
                                    </ol>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                this.updateTagCount('selected', 0);
                return;
            }
        }
        
        // Store the select all containers before clearing
        const selectAllSelectedContainer = container.querySelector('.select-all-container');
        
        // Clear existing content but preserve the select all container
        container.innerHTML = '';
        
        // Re-add the select all container if it existed
        if (selectAllSelectedContainer) {
            container.appendChild(selectAllSelectedContainer);
        } else {
            // Create select all container if it doesn't exist
            const selectAllContainer = document.createElement('div');
            selectAllContainer.className = 'd-flex align-items-center gap-3 mb-2 px-3';
            selectAllContainer.innerHTML = `
                <label class="d-flex align-items-center gap-2 cursor-pointer mb-0 select-all-container">
                    <input type="checkbox" id="selectAllSelected" class="custom-checkbox">
                    <span class="text-secondary fw-semibold">SELECT ALL</span>
                </label>
            `;
            container.appendChild(selectAllContainer);
        }

        // Add global select all checkbox
        const topSelectAll = document.getElementById('selectAllSelected');
        
        if (topSelectAll && !topSelectAll.hasAttribute('data-listener-added')) {
            topSelectAll.setAttribute('data-listener-added', 'true');
            topSelectAll.addEventListener('change', (e) => {
                const isChecked = e.target.checked;
                
                // Prevent operation if tags are being moved
                if (this.isMovingTags) {
                    return;
                }
                
                const tagCheckboxes = document.querySelectorAll('#selectedTags .tag-checkbox');
                
                tagCheckboxes.forEach(checkbox => {
                    checkbox.checked = isChecked;
                    const tag = this.state.tags.find(t => t['Product Name*'] === checkbox.value);
                    if (tag) {
                        if (isChecked) {
                            if (!this.state.persistentSelectedTags.includes(tag['Product Name*'])) {
                                this.state.persistentSelectedTags.push(tag['Product Name*']);
                            }
                        } else {
                            const index = this.state.persistentSelectedTags.indexOf(tag['Product Name*']);
                            if (index > -1) {
                                this.state.persistentSelectedTags.splice(index, 1);
                            }
                        }
                    }
                });
                
                // Update the regular selectedTags set to match persistent ones
                this.state.selectedTags = new Set(this.state.persistentSelectedTags);
                
                // Update selected tags display
                const selectedTagObjects = Array.from(this.state.persistentSelectedTags).map(name =>
                    this.state.tags.find(t => t['Product Name*'] === name)
                ).filter(Boolean);
                
                this.updateSelectedTags(selectedTagObjects);
                
                // Efficiently update available tags visibility without full rebuild
                this.efficientlyUpdateAvailableTagsDisplay();
            });
        }

        // Handle new tags being passed in (e.g., from JSON matching)
        // Add new tags to persistentSelectedTags without clearing existing ones
        if (tags.length > 0) {
            console.log('Adding new tags to persistentSelectedTags:', tags);
            tags.forEach(tag => {
                if (tag && tag['Product Name*']) {
                    if (!this.state.persistentSelectedTags.includes(tag['Product Name*'])) {
                        this.state.persistentSelectedTags.push(tag['Product Name*']);
                    }
                }
            });
            // Update the regular selectedTags set to match persistent ones
            this.state.selectedTags = new Set(this.state.persistentSelectedTags);
        }

        // Use the tags and display in the same order as the available list for consistency
        let fullTags = tags;
        if (tags && tags.length > 0) {
            console.log('Using tags for display (available list order):', tags);
            // Keep selected tags in the same order as the available list for consistency
            fullTags = [...tags];
            // Keep selectedTags set in sync with persistent without reordering
            this.state.selectedTags = new Set(this.state.persistentSelectedTags);
        } else {
            // If no backend tags, show empty selected tags list
            console.log('No backend tags, showing empty selected tags list');
            fullTags = [];
            this.state.persistentSelectedTags = [];
            this.state.selectedTags = new Set();
        }
        
        // If no tags, just return
        if (!fullTags || fullTags.length === 0) {
            console.log('No tags to display in selected tags');
            this.updateTagCount('selected', 0);
            console.timeEnd('updateSelectedTags');
            return;
        }

        // Organize tags into hierarchical groups (same as available tags)
        const groupedTags = this.organizeBrandCategories(fullTags);
        console.log('Grouped selected tags:', groupedTags);

        // Sort vendors alphabetically
        const sortedVendors = Array.from(groupedTags.entries())
            .sort(([a], [b]) => (a || '').localeCompare(b || ''));

        // Create vendor sections
        sortedVendors.forEach(([vendor, brandGroups]) => {
            console.log('Processing vendor:', vendor, 'with brand groups:', brandGroups);
            
            const vendorSection = document.createElement('div');
            vendorSection.className = 'vendor-section mb-3';
            
            // Create vendor header with integrated checkbox and collapse functionality
            const vendorHeader = document.createElement('h5');
            vendorHeader.className = 'vendor-header mb-2 d-flex align-items-center collapsible-header';
            vendorHeader.setAttribute('data-collapse-target', 'vendor-' + vendor.replace(/[^a-zA-Z0-9]/g, '_'));
            
            const vendorCheckbox = document.createElement('input');
            vendorCheckbox.type = 'checkbox';
            vendorCheckbox.className = 'select-all-checkbox me-2';
            vendorCheckbox.addEventListener('change', (e) => {
                const isChecked = e.target.checked;
                
                // Select all descendant checkboxes (including subcategories and tags)
                const checkboxes = vendorSection.querySelectorAll('input[type="checkbox"]');
                
                checkboxes.forEach(checkbox => {
                    checkbox.checked = isChecked;
                    // Only update persistentSelectedTags for tag-checkboxes
                    if (checkbox.classList.contains('tag-checkbox')) {
                        const tag = this.state.tags.find(t => t['Product Name*'] === checkbox.value);
                        if (tag) {
                            if (isChecked) {
                                if (!this.state.persistentSelectedTags.includes(tag['Product Name*'])) {
                                    this.state.persistentSelectedTags.push(tag['Product Name*']);
                                }
                            } else {
                                const index = this.state.persistentSelectedTags.indexOf(tag['Product Name*']);
                                if (index > -1) {
                                    this.state.persistentSelectedTags.splice(index, 1);
                                }
                            }
                        }
                    }
                });
                
                // Update the regular selectedTags set to match persistent ones
                this.state.selectedTags = new Set(this.state.persistentSelectedTags);
                
                // Update selected tags display
                const selectedTagObjects = Array.from(this.state.persistentSelectedTags).map(name =>
                    this.state.tags.find(t => t['Product Name*'] === name)
                ).filter(Boolean);
                
                this.updateSelectedTags(selectedTagObjects);
                
                // FIXED: Don't filter out selected tags from available tags - keep all items visible
                // This allows users to see all available options even after making selections
                console.log('FIXED: Not filtering out selected tags - keeping all items visible in available list');
                this._updateAvailableTags(this.state.originalTags, this.state.originalTags);
            });
            
            // Add collapse/expand icon (will be placed to the right of the vendor name)
            const vendorCollapseIcon = document.createElement('span');
            vendorCollapseIcon.className = 'collapse-icon ms-auto';
            vendorCollapseIcon.textContent = '▼';
            vendorCollapseIcon.style.transition = 'opacity 0.2s ease';

            // Build header: [checkbox] [vendor name (flex-grow)] [collapse icon aligned right]
            vendorHeader.appendChild(vendorCheckbox);
            const vendorNameSpan = document.createElement('span');
            vendorNameSpan.className = 'vendor-title flex-grow-1 text-truncate';
            vendorNameSpan.textContent = vendor;
            vendorHeader.appendChild(vendorNameSpan);
            vendorHeader.appendChild(vendorCollapseIcon);
            
            // Add click handler for collapse/expand
            vendorHeader.addEventListener('click', (e) => {
                if (e.target.classList.contains('select-all-checkbox') || e.target.closest('.select-all-checkbox')) {
                    return; // Don't collapse if clicking checkbox
                }
                const targetSection = vendorSection.querySelector('.collapsible-content');
                const isCollapsed = targetSection.classList.contains('collapsed');
                
                if (isCollapsed) {
                    targetSection.classList.remove('collapsed');
                    vendorCollapseIcon.textContent = '▼';
                } else {
                    targetSection.classList.add('collapsed');
                    vendorCollapseIcon.textContent = '▶';
                }
                
                // Remove the instructional blurb when any chevron is clicked
                this.removeDropdownInstructionBlurb();
            });
            
            vendorSection.appendChild(vendorHeader);

            // Create collapsible content container for vendor
            const vendorContent = document.createElement('div');
            vendorContent.className = 'collapsible-content expanded';
            vendorSection.appendChild(vendorContent);

            // Create brand sections
            const sortedBrands = Array.from(brandGroups.entries())
                .sort(([a], [b]) => (a || '').localeCompare(b || ''));

            sortedBrands.forEach(([brand, productTypeGroups]) => {
                const brandSection = document.createElement('div');
                brandSection.className = 'brand-section ms-3 mb-2';
                
                // Create brand header with integrated checkbox and collapse functionality
                const brandHeader = document.createElement('h6');
                brandHeader.className = 'brand-header mb-2 d-flex align-items-center collapsible-header';
                brandHeader.setAttribute('data-collapse-target', 'brand-' + brand.replace(/[^a-zA-Z0-9]/g, '_'));
                
                const brandCheckbox = document.createElement('input');
                brandCheckbox.type = 'checkbox';
                brandCheckbox.className = 'select-all-checkbox me-2';
                brandCheckbox.addEventListener('change', (e) => {
                    const isChecked = e.target.checked;
                    
                    // Select all descendant checkboxes (including subcategories and tags)
                    const checkboxes = brandSection.querySelectorAll('input[type="checkbox"]');
                    
                    checkboxes.forEach(checkbox => {
                        checkbox.checked = isChecked;
                        // Only update persistentSelectedTags for tag-checkboxes
                        if (checkbox.classList.contains('tag-checkbox')) {
                            const tag = this.state.tags.find(t => t['Product Name*'] === checkbox.value);
                            if (tag) {
                                if (isChecked) {
                                    if (!this.state.persistentSelectedTags.includes(tag['Product Name*'])) {
                                        this.state.persistentSelectedTags.push(tag['Product Name*']);
                                    }
                                } else {
                                    const index = this.state.persistentSelectedTags.indexOf(tag['Product Name*']);
                                    if (index > -1) {
                                        this.state.persistentSelectedTags.splice(index, 1);
                                    }
                                }
                            }
                        }
                    });
                    
                    // Update the regular selectedTags set to match persistent ones
                    this.state.selectedTags = new Set(this.state.persistentSelectedTags);
                    
                    // Update selected tags display
                    const selectedTagObjects = Array.from(this.state.persistentSelectedTags).map(name =>
                        this.state.tags.find(t => t['Product Name*'] === name)
                    ).filter(Boolean);
                    
                    this.updateSelectedTags(selectedTagObjects);
                    
                    // Efficiently update available tags visibility without full rebuild
                    this.efficientlyUpdateAvailableTagsDisplay();
                });
                
                // Add collapse/expand icon (to the right of the brand name)
                const brandCollapseIcon = document.createElement('span');
                brandCollapseIcon.className = 'collapse-icon ms-auto';
                brandCollapseIcon.textContent = '▼';
                brandCollapseIcon.style.transition = 'opacity 0.2s ease';

                brandHeader.appendChild(brandCheckbox);
                const brandNameSpan = document.createElement('span');
                brandNameSpan.className = 'brand-title flex-grow-1 text-truncate';
                brandNameSpan.textContent = brand;
                brandHeader.appendChild(brandNameSpan);
                brandHeader.appendChild(brandCollapseIcon);
                
                // Add click handler for collapse/expand
                brandHeader.addEventListener('click', (e) => {
                    if (e.target.classList.contains('select-all-checkbox') || e.target.closest('.select-all-checkbox')) {
                        return; // Don't collapse if clicking checkbox
                    }
                    const targetSection = brandSection.querySelector('.collapsible-content');
                    const isExpanded = targetSection.classList.contains('expanded');
                    
                    if (!isExpanded) {
                        targetSection.classList.add('expanded');
                        targetSection.classList.remove('collapsed');
                        brandCollapseIcon.textContent = '▼';
                    } else {
                        targetSection.classList.remove('expanded');
                        targetSection.classList.add('collapsed');
                        brandCollapseIcon.textContent = '▶';
                    }
                    
                    // Remove the instructional blurb when any chevron is clicked
                    this.removeDropdownInstructionBlurb();
                });
                
                brandSection.appendChild(brandHeader);

                // Create collapsible content container for brand
                const brandContent = document.createElement('div');
                brandContent.className = 'collapsible-content expanded';
                brandSection.appendChild(brandContent);

                // Create product type sections
                const sortedProductTypes = Array.from(productTypeGroups.entries())
                    .sort(([a], [b]) => (a || '').localeCompare(b || ''));

                sortedProductTypes.forEach(([productType, weightGroups]) => {
                    const productTypeSection = document.createElement('div');
                    productTypeSection.className = 'product-type-section ms-3 mb-2';
                    
                    // Create product type header with integrated checkbox and collapse functionality
                    const typeHeader = document.createElement('div');
                    typeHeader.className = 'product-type-header mb-2 d-flex align-items-center collapsible-header';
                    typeHeader.setAttribute('data-collapse-target', 'type-' + productType.replace(/[^a-zA-Z0-9]/g, '_'));
                    
                    const productTypeCheckbox = document.createElement('input');
                    productTypeCheckbox.type = 'checkbox';
                    productTypeCheckbox.className = 'select-all-checkbox me-2';
                    productTypeCheckbox.addEventListener('change', (e) => {
                        const isChecked = e.target.checked;
                        
                        // Select all descendant checkboxes (including subcategories and tags)
                        const checkboxes = productTypeSection.querySelectorAll('input[type="checkbox"]');
                        
                        checkboxes.forEach(checkbox => {
                            checkbox.checked = isChecked;
                            // Only update persistentSelectedTags for tag-checkboxes
                            if (checkbox.classList.contains('tag-checkbox')) {
                                const tag = this.state.tags.find(t => t['Product Name*'] === checkbox.value);
                                if (tag) {
                                    if (isChecked) {
                                        if (!this.state.persistentSelectedTags.includes(tag['Product Name*'])) {
                                            this.state.persistentSelectedTags.push(tag['Product Name*']);
                                        }
                                    } else {
                                        const index = this.state.persistentSelectedTags.indexOf(tag['Product Name*']);
                                        if (index > -1) {
                                            this.state.persistentSelectedTags.splice(index, 1);
                                        }
                                    }
                                }
                            }
                        });
                        
                        // Update the regular selectedTags set to match persistent ones
                        this.state.selectedTags = new Set(this.state.persistentSelectedTags);
                        
                        // Update selected tags display
                        const selectedTagObjects = Array.from(this.state.persistentSelectedTags).map(name =>
                            this.state.tags.find(t => t['Product Name*'] === name)
                        ).filter(Boolean);
                        
                        this.updateSelectedTags(selectedTagObjects);
                        
                        // Efficiently update available tags visibility without full rebuild
                        this.efficientlyUpdateAvailableTagsDisplay();
                    });
                    
                    // Add collapse/expand icon (to the right of the product type)
                    const typeCollapseIcon = document.createElement('span');
                    typeCollapseIcon.className = 'collapse-icon ms-auto';
                    typeCollapseIcon.textContent = '▼';
                    typeCollapseIcon.style.transition = 'opacity 0.2s ease';

                    typeHeader.appendChild(productTypeCheckbox);
                    const typeNameSpan = document.createElement('span');
                    typeNameSpan.className = 'type-title flex-grow-1 text-truncate';
                    typeNameSpan.textContent = productType;
                    typeHeader.appendChild(typeNameSpan);
                    typeHeader.appendChild(typeCollapseIcon);
                    
                    // Add click handler for collapse/expand
                    typeHeader.addEventListener('click', (e) => {
                        if (e.target.classList.contains('select-all-checkbox') || e.target.closest('.select-all-checkbox')) {
                            return; // Don't collapse if clicking checkbox
                        }
                        const targetSection = productTypeSection.querySelector('.collapsible-content');
                        const isCollapsed = targetSection.classList.contains('collapsed');
                        
                        if (isCollapsed) {
                            targetSection.classList.remove('collapsed');
                            typeCollapseIcon.textContent = '▼';
                        } else {
                            targetSection.classList.add('collapsed');
                            typeCollapseIcon.textContent = '▶';
                        }
                        
                        // Remove the instructional blurb when any chevron is clicked
                        this.removeDropdownInstructionBlurb();
                    });
                    
                    productTypeSection.appendChild(typeHeader);

                    // Create collapsible content container for product type
                    const productTypeContent = document.createElement('div');
                    productTypeContent.className = 'collapsible-content';
                    productTypeSection.appendChild(productTypeContent);

                    // Create weight sections
                    const sortedWeights = Array.from(weightGroups.entries())
                        .sort(([a], [b]) => (a || '').localeCompare(b || ''));

                    sortedWeights.forEach(([weight, tags]) => {
                        const weightSection = document.createElement('div');
                        weightSection.className = 'weight-section ms-3 mb-1';
                        
                        // Create weight header with integrated checkbox and collapse functionality
                        const weightHeader = document.createElement('div');
                        weightHeader.className = 'weight-header mb-1 d-flex align-items-center collapsible-header';
                        weightHeader.setAttribute('data-collapse-target', 'weight-' + weight.replace(/[^a-zA-Z0-9]/g, '_'));
                        
                        const weightCheckbox = document.createElement('input');
                        weightCheckbox.type = 'checkbox';
                        weightCheckbox.className = 'select-all-checkbox me-2';
                        weightCheckbox.addEventListener('change', (e) => {
                            const isChecked = e.target.checked;
                            // Only iterate tag checkboxes for performance
                            const checkboxes = weightSection.querySelectorAll('input.tag-checkbox');
                            
                            checkboxes.forEach(checkbox => {
                                checkbox.checked = isChecked;
                                // Only update persistentSelectedTags for tag-checkboxes
                                if (checkbox.classList.contains('tag-checkbox')) {
                                    const tag = this.state.tags.find(t => t['Product Name*'] === checkbox.value);
                                    if (tag) {
                                        if (isChecked) {
                                            if (!this.state.persistentSelectedTags.includes(tag['Product Name*'])) {
                                                this.state.persistentSelectedTags.push(tag['Product Name*']);
                                            }
                                        } else {
                                            const index = this.state.persistentSelectedTags.indexOf(tag['Product Name*']);
                                            if (index > -1) {
                                                this.state.persistentSelectedTags.splice(index, 1);
                                            }
                                        }
                                    }
                                }
                            });
                            
                            // Update the regular selectedTags set to match persistent ones
                            this.state.selectedTags = new Set(this.state.persistentSelectedTags);
                            
                            // Update the selected tags display
                            const selectedTagObjects = Array.from(this.state.persistentSelectedTags).map(name =>
                                this.state.tags.find(t => t['Product Name*'] === name)
                            ).filter(Boolean);
                            this.updateSelectedTags(selectedTagObjects);
                            
                            // Use efficient update instead of rebuilding entire DOM
                            this.efficientlyUpdateAvailableTagsDisplay();
                        });
                        
                        // Add collapse/expand icon (to the right of the weight)
                        const weightCollapseIcon = document.createElement('span');
                        weightCollapseIcon.className = 'collapse-icon ms-auto';
                        weightCollapseIcon.textContent = '▼';
                        weightCollapseIcon.style.transition = 'opacity 0.2s ease';

                        weightHeader.appendChild(weightCheckbox);
                        const weightNameSpan = document.createElement('span');
                        weightNameSpan.className = 'weight-title flex-grow-1 text-truncate';
                        weightNameSpan.textContent = weight;
                        weightHeader.appendChild(weightNameSpan);
                        weightHeader.appendChild(weightCollapseIcon);
                        
                        // Add click handler for collapse/expand
                        weightHeader.addEventListener('click', (e) => {
                            if (e.target.classList.contains('select-all-checkbox') || e.target.closest('.select-all-checkbox')) {
                                return; // Don't collapse if clicking checkbox
                            }
                            const targetSection = weightSection.querySelector('.collapsible-content');
                            const isCollapsed = targetSection.classList.contains('collapsed');
                            
                            if (isCollapsed) {
                                targetSection.classList.remove('collapsed');
                                weightCollapseIcon.textContent = '▼';
                            } else {
                                weightSection.classList.add('collapsed');
                                weightCollapseIcon.textContent = '▶';
                            }
                            
                            // Remove the instructional blurb when any chevron is clicked
                            this.removeDropdownInstructionBlurb();
                        });
                        
                        weightSection.appendChild(weightHeader);
                        
                        // Create collapsible content container for weight
                        const weightContent = document.createElement('div');
                        weightContent.className = 'collapsible-content';
                        weightSection.appendChild(weightContent);
                        
                        // Always render tags as leaf nodes - maintain the same order as available list
                        if (tags && tags.length > 0) {
                            // Keep tags in the same order as the available list for consistency
                            const orderedTags = [...tags];
                            
                            orderedTags.forEach(tag => {
                                const tagElement = this.createTagElement(tag, true); // true = isForSelectedTags
                                const checkbox = tagElement.querySelector('.tag-checkbox');
                                const shouldBeChecked = this.state.persistentSelectedTags.includes(tag['Product Name*']);
                                checkbox.checked = shouldBeChecked;
                                console.log(`Setting checkbox for "${tag['Product Name*']}" to checked: ${shouldBeChecked}`);
                                
                                // Ensure the checkbox is properly initialized
                                if (shouldBeChecked) {
                                    checkbox.setAttribute('data-checked', 'true');
                                } else {
                                    checkbox.removeAttribute('data-checked');
                                }
                                
                                // Add a small delay to ensure the checkbox is properly rendered
                                setTimeout(() => {
                                    // Double-check the checkbox state
                                    if (shouldBeChecked && !checkbox.checked) {
                                        console.log(`Fixing checkbox state for "${tag['Product Name*']}" - should be checked but isn't`);
                                        checkbox.checked = true;
                                    } else if (!shouldBeChecked && checkbox.checked) {
                                        console.log(`Fixing checkbox state for "${tag['Product Name*']}" - should not be checked but is`);
                                        checkbox.checked = false;
                                    }
                                }, 10);
                                
                                weightContent.appendChild(tagElement);
                            });
                        }
                        
                        productTypeContent.appendChild(weightSection);
                    });
                    
                    brandContent.appendChild(productTypeSection);
                });
                
                vendorContent.appendChild(brandSection);
            });
            
            
            container.appendChild(vendorSection);
        });

        this.updateTagCount('selected', fullTags.length);
        console.timeEnd('updateSelectedTags');

        // Attach a delegated change handler to handle deselection within selectedTags
        // Install a single delegated deselection handler once (idempotent)
        if (!container._hasDeselectionHandler) {
            // Toggle by clicking anywhere on the row (not on dropdowns)
            container.addEventListener('click', (e) => {
                const t = e.target;
                // Ignore clicks on lineage dropdowns
                if (t.closest('.lineage-dropdown')) return;
                const row = t.closest('.tag-item, .tag-row');
                if (!row) return;
                const cb = row.querySelector('input[type="checkbox"].tag-checkbox');
                if (!cb) return;
                if (t === cb) return; // checkbox itself will emit change
                cb.checked = !cb.checked;
                cb.dispatchEvent(new Event('change', { bubbles: true }));
            });
            // Capture-phase to intercept before individual checkbox handlers
            container.addEventListener('change', (e) => {
                const target = e.target;
                if (!target || !target.matches('input[type="checkbox"].tag-checkbox')) return;
                const tagName = target.value;
                if (target.checked) return;
                // Update state without triggering full re-render
                const idx = this.state.persistentSelectedTags.indexOf(tagName);
                if (idx > -1) this.state.persistentSelectedTags.splice(idx, 1);
                this.state.selectedTags.delete(tagName);
                // Remove DOM row
                const row = target.closest('.tag-item, .tag-row');
                if (row) row.remove();
                // Update counts minimally
                this.updateTagCount('selected', this.state.persistentSelectedTags.length);
                // Stop this change from bubbling to any global listeners that might reload data
                if (typeof e.stopImmediatePropagation === 'function') e.stopImmediatePropagation();
                e.stopPropagation();
                e.preventDefault();
                // Sync the corresponding checkbox in availableTags (if present) so Brand rows don't reflow
                const availCb = document.querySelector(`#availableTags .tag-checkbox[value="${CSS.escape(tagName)}"]`);
                if (availCb) availCb.checked = false;
            }, { capture: true });
            Object.defineProperty(container, '_hasDeselectionHandler', { value: true, enumerable: false });
        }

        // After rendering, update all select-all checkboxes to reflect the state of their descendant tag checkboxes
        // Helper to set select-all checkbox state
        function updateSelectAllCheckboxState(section) {
            const selectAll = section.querySelector('.select-all-checkbox');
            if (!selectAll) return;
            const tagCheckboxes = section.querySelectorAll('.tag-checkbox');
            if (tagCheckboxes.length === 0) {
                selectAll.checked = false;
                selectAll.indeterminate = false;
                return;
            }
            const checkedCount = Array.from(tagCheckboxes).filter(cb => cb.checked).length;
            if (checkedCount === tagCheckboxes.length) {
                selectAll.checked = true;
                selectAll.indeterminate = false;
            } else if (checkedCount === 0) {
                selectAll.checked = false;
                selectAll.indeterminate = false;
            } else {
                selectAll.checked = false;
                selectAll.indeterminate = true;
            }
        }
        // Update all group-level select all checkboxes
        container.querySelectorAll('.vendor-section, .brand-section, .product-type-section, .weight-section').forEach(section => {
            updateSelectAllCheckboxState(section);
        });
        // Update the top-level select all
        updateSelectAllCheckboxState(container);
        
        // Update select all checkbox states
        this.updateSelectAllCheckboxes();
        
        // Dispatch event to notify drag and drop manager that tag updates are complete
        document.dispatchEvent(new CustomEvent('updateSelectedTagsComplete'));
        
        // Also directly reinitialize drag and drop to ensure it's working
        if (window.dragAndDropManager) {
            setTimeout(() => {
                console.log('Reinitializing drag and drop after updateSelectedTags');
                window.dragAndDropManager.reinitializeTagDragAndDrop();
            }, 100);
        }
    },

    updateTagCount(type, count) {
        const countElement = document.getElementById(`${type}TagsCount`);
        if (countElement) {
            countElement.textContent = `(${count})`;
        }
    },

    addCheckboxListeners(containerId) {
        document.querySelectorAll(`${containerId} input[type="checkbox"]`).forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                if (this.checked) {
                    if (!TagManager.state.persistentSelectedTags.includes(this.value)) {
                    TagManager.state.persistentSelectedTags.push(this.value);
                };
                } else {
                    const index = TagManager.state.persistentSelectedTags.indexOf(this.value);
                if (index > -1) {
                    TagManager.state.persistentSelectedTags.splice(index, 1);
                };
                }
                // Update the regular selectedTags set to match persistent ones
                TagManager.state.selectedTags = new Set(TagManager.state.persistentSelectedTags);
                TagManager.updateTagCheckboxes();
            });
        });
    },

    updateTagCheckboxes() {
        console.log('updateTagCheckboxes called');
        // Update available tags checkboxes
        document.querySelectorAll('#availableTags input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = TagManager.state.persistentSelectedTags.includes(checkbox.value);
            
            // Ensure checkbox is properly enabled
            checkbox.style.pointerEvents = 'auto';
            checkbox.removeAttribute('data-drag-disabled');
            checkbox.removeAttribute('data-reordering');
        });
        
        // Update selected tags checkboxes
        document.querySelectorAll('#selectedTags input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = TagManager.state.persistentSelectedTags.includes(checkbox.value);
            
            // Ensure checkbox is properly enabled
            checkbox.style.pointerEvents = 'auto';
            checkbox.removeAttribute('data-drag-disabled');
            checkbox.removeAttribute('data-reordering');
        });
        
        // Also ensure tag items are properly enabled
        document.querySelectorAll('.tag-item').forEach(tagItem => {
            tagItem.style.pointerEvents = 'auto';
            tagItem.removeAttribute('data-drag-disabled');
            tagItem.removeAttribute('data-reordering');
        });
        
        console.log('All checkboxes and tag items updated and enabled');
    },

    async fetchAndUpdateAvailableTags() {
        try {
            console.log('=== fetchAndUpdateAvailableTags START ===');
            
            // Check if we're in JSON matching mode and have JSON matched tags
            const hasJsonMatchedTags = this.state.persistentSelectedTags && this.state.persistentSelectedTags.length > 0;
            const hasJsonMatchedData = this.state.tags && this.state.tags.length > 0 && 
                this.state.tags.some(tag => tag.Source === 'JSON Match' || (tag.Source && tag.Source.includes('Educated Guess')));
            
            // Additional checks for JSON matched data
            const hasJsonMatchedInOriginal = this.state.originalTags && this.state.originalTags.length > 0 && 
                this.state.originalTags.some(tag => tag.Source === 'JSON Match' || (tag.Source && tag.Source.includes('Educated Guess')));
            
            // Check if we have any tags with JSON Match source
                    const jsonMatchedCount = this.state.tags ? this.state.tags.filter(tag => tag.Source === 'JSON Match' || (tag.Source && tag.Source.includes('Educated Guess'))).length : 0;
        const originalJsonMatchedCount = this.state.originalTags ? this.state.originalTags.filter(tag => tag.Source === 'JSON Match' || (tag.Source && tag.Source.includes('Educated Guess'))).length : 0;
            
            console.log('JSON matching detection:', {
                hasJsonMatchedTags,
                hasJsonMatchedData,
                hasJsonMatchedInOriginal,
                jsonMatchedCount,
                originalJsonMatchedCount,
                tagsLength: this.state.tags ? this.state.tags.length : 0,
                originalTagsLength: this.state.originalTags ? this.state.originalTags.length : 0
            });
            
            // Only skip if we have actual JSON matched data, not just persistent tags
            if (hasJsonMatchedData || hasJsonMatchedInOriginal || jsonMatchedCount > 0) {
                console.log('Skipping fetchAndUpdateAvailableTags - JSON matched data detected, preserving current state');
                console.log('=== fetchAndUpdateAvailableTags END (SKIPPED) ===');
                return true;
            }
            
            console.log('Fetching available tags...');
            const timestamp = Date.now();
            const response = await fetch(`/api/available-tags?t=${timestamp}`);
            console.log('Available tags response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const tags = await response.json();
            console.log('Available tags response data:', tags);
            
            if (!tags || !Array.isArray(tags) || tags.length === 0) {
                console.error('No tags loaded from backend or invalid response format');
                // Clear existing tags if no new data
                this.state.tags = [];
                this.state.originalTags = [];
                this._updateAvailableTags([]);
                return false;
            }
            
            console.log(`Fetched ${tags.length} available tags`);
            
            // Debug: Check lineage data for first few tags
            console.log('Sample lineage data:');
            tags.slice(0, 5).forEach(tag => {
                console.log(`  ${tag['Product Name*']}: lineage=${tag.lineage}, Lineage=${tag.Lineage}`);
            });
            
            // Clear existing state and set new data
            this.state.tags = [...tags];
            this.state.originalTags = [...tags]; // Store original tags for validation
            
            // Preserve selected tags if they exist and are valid (optimized)
            const currentSelectedTags = [...this.state.persistentSelectedTags];
            this.state.persistentSelectedTags = [];
            this.state.selectedTags = new Set();

            if (currentSelectedTags.length > 0) {
                // Build a fast lookup map of product name -> true
                const tagNameSet = new Set(tags.map(t => t['Product Name*']));
                for (const tagName of currentSelectedTags) {
                    if (tagNameSet.has(tagName)) {
                        this.state.persistentSelectedTags.push(tagName);
                        this.state.selectedTags.add(tagName);
                    }
                }
            }
            
            this.validateSelectedTags();
            
            // Update the UI with new tags
            this._updateAvailableTags(tags);
            
            // Update tag counts
            this.updateTagCount('available', tags.length);
            this.updateTagCount('selected', this.state.persistentSelectedTags.length);
            
            console.log(`Successfully updated available tags: ${tags.length} tags`);
            console.log('=== fetchAndUpdateAvailableTags END ===');
            return true;
        } catch (error) {
            console.error('Error fetching available tags:', error);
            console.log('=== fetchAndUpdateAvailableTags ERROR ===');
            return false;
        }
    },

    async fetchAndUpdateSelectedTags() {
        try {
            console.log('Fetching selected tags...');
            const timestamp = Date.now();
            const response = await fetch(`/api/selected-tags?t=${timestamp}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const selectedTags = await response.json();
            
            if (!selectedTags || !Array.isArray(selectedTags)) {
                console.warn('No selected tags found - data may not be loaded yet');
                this.updateSelectedTags([]);
                return true;
            }
            
            console.log(`Fetched ${selectedTags.length} selected tags:`, selectedTags.map(tag => tag['Product Name*']));
            
            // Update persistentSelectedTags with the fetched tags from backend
            console.log('Updating persistentSelectedTags with fetched tags:', selectedTags.map(tag => tag['Product Name*']));
            this.state.persistentSelectedTags = selectedTags.map(tag => tag['Product Name*']);
            this.state.selectedTags = new Set(this.state.persistentSelectedTags);
            console.log('persistentSelectedTags after update:', this.state.persistentSelectedTags);
            console.log('selectedTags after update:', this.state.selectedTags);
            
            this.updateSelectedTags(selectedTags);
            
            // Ensure drag and drop is working after fetching tags
            if (window.dragAndDropManager && selectedTags.length > 0) {
                setTimeout(() => {
                    console.log('Reinitializing drag and drop after fetchAndUpdateSelectedTags');
                    window.dragAndDropManager.reinitializeTagDragAndDrop();
                }, 300);
            }
            
            return true;
        } catch (error) {
            console.error('Error fetching selected tags:', error);
            this.updateSelectedTags([]);
            return false;
        }
    },

    async fetchAndPopulateFilters() {
        try {
            // Use the filter options API with cache refresh and timestamp to ensure updated weight formatting
            const timestamp = Date.now();
            const response = await fetch(`/api/filter-options?refresh=true&t=${timestamp}`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            if (!response.ok) {
                throw new Error('Failed to fetch filter options');
            }
            const filterOptions = await response.json();
            console.log('Fetched filter options:', filterOptions);
            this.updateFilters(filterOptions, true); // Preserve existing filter values
        } catch (error) {
            console.error('Error fetching filter options:', error);
            alert('Failed to load filter options');
        }
    },

    async downloadExcel() {
        // Collect filter values from dropdowns (adjust IDs as needed)
        const filters = {
            vendor: document.getElementById('vendorFilter')?.value || null,
            brand: document.getElementById('brandFilter')?.value || null,
            productType: document.getElementById('productTypeFilter')?.value || null,
            lineage: document.getElementById('lineageFilter')?.value || null,
            weight: document.getElementById('weightFilter')?.value || null,
        };

        // Remove null/empty values
        Object.keys(filters).forEach(key => {
            if (!filters[key] || filters[key] === '') {
                delete filters[key];
            }
        });

        // Collect selected tags from the persistent selected tags
        const allTags = Array.from(this.state.persistentSelectedTags);

        try {
            const response = await fetch('/api/download-processed-excel', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filters,
                    selected_tags: allTags
                })
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to download Excel');
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            // Let the server set the filename via Content-Disposition header
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error downloading Excel:', error);
            alert(error.message || 'Failed to download Excel');
        }
    },

    // Initialize the tag manager
    init() {
        console.log('=== TAGMANAGER INIT FUNCTION CALLED ===');
        console.log('TagManager initialized');
        console.log('DOM ready, checking for available tags container...');
        const availableTagsContainer = document.getElementById('availableTags');
        console.log('Available tags container found:', !!availableTagsContainer);
        if (availableTagsContainer) {
            console.log('Container innerHTML:', availableTagsContainer.innerHTML);
        }
        
        // Show application splash screen
        AppLoadingSplash.show();
        AppLoadingSplash.startAutoAdvance();
        
        // Initialize empty state first
        this.initializeEmptyState();
        AppLoadingSplash.nextStep(); // Templates loaded
        
        // Check if there's already data loaded (e.g., from a previous session or default file)
        this.checkForExistingData();
        
        // Ensure all filters default to 'All' on page load
        this.state.filters = {
            vendor: 'All',
            brand: 'All',
            productType: 'All',
            lineage: 'All',
            weight: 'All'
        };
        // Set each filter dropdown to 'All' (or '')
        const filterIds = ['vendorFilter', 'brandFilter', 'productTypeFilter', 'lineageFilter', 'weightFilter', 'dohFilter', 'highCbdFilter'];
        filterIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
        // Don't apply filters immediately - let checkForExistingData handle it
        // this.applyFilters();
        
        // Add filter change event listeners for cascading filters after filters are populated
        setTimeout(() => {
            console.log('=== SETTING UP FILTER EVENT LISTENERS ===');
            this.setupFilterEventListeners();
            console.log('=== FILTER EVENT LISTENERS SETUP COMPLETE ===');
        }, 1000);
        
        // Add search event listeners
        this.setupSearchEventListeners();
        
        // Update table header if TagsTable is available
        setTimeout(() => {
            // Also update table header if TagsTable is available
            if (typeof TagsTable !== 'undefined' && TagsTable.updateTableHeader) {
                TagsTable.updateTableHeader();
            }
        }, 100);

        // Initialize drag and drop manager
        setTimeout(() => {
            if (window.dragAndDropManager) {
                window.dragAndDropManager.setupTagDragAndDrop();
            }
        }, 200);

        // JSON matching is now handled by the modal - removed old above-tags-list logic
        
        // Emergency initialization fix - force complete after 15 seconds
        setTimeout(() => {
            if (AppLoadingSplash && AppLoadingSplash.isVisible) {
                console.log('Emergency initialization fix: forcing splash completion');
                AppLoadingSplash.stopAutoAdvance();
                AppLoadingSplash.complete();
            }
        }, 15000);
        
        // Additional emergency fix for stuck initialization
        window.addEventListener('load', () => {
            setTimeout(() => {
                const splash = document.getElementById('appLoadingSplash');
                if (splash && splash.style.display !== 'none') {
                    console.log('Emergency fix: hiding stuck splash screen');
                    splash.style.display = 'none';
                    const mainContent = document.getElementById('mainContent');
                    if (mainContent) {
                        mainContent.style.display = 'block';
                    }
                }
            }, 20000); // 20 second emergency timeout
        });
    },

    // Show a simple loading indicator
    showLoadingIndicator() {
        const availableTagsContainer = document.getElementById('availableTags');
        if (availableTagsContainer) {
            availableTagsContainer.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2 text-muted">Loading product data...</p>
                </div>
            `;
        }
    },

    // Hide loading indicator
    hideLoadingIndicator() {
        const availableTagsContainer = document.getElementById('availableTags');
        if (availableTagsContainer) {
            // Check if we have any tags loaded
            if (this.state.tags && this.state.tags.length > 0) {
                // Data is loaded, no need to show upload prompt
                return;
            }
            
            // No data loaded, show upload prompt
            availableTagsContainer.innerHTML = `
                <div class="text-center py-5">
                    <div class="upload-prompt">
                        <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
                        <h5 class="text-muted">No product data loaded</h5>
                        <p class="text-muted">Upload an Excel file to get started</p>
                        <button class="btn btn-primary" onclick="document.getElementById('fileInput').click()">
                            <i class="fas fa-upload me-2"></i>Upload Excel File
                        </button>
                    </div>
                </div>
            `;
        }
    },

    // Set loading state (used by enhanced-ui.js)
    setLoading(isLoading) {
        if (isLoading) {
            this.showLoadingIndicator();
        } else {
            this.hideLoadingIndicator();
        }
    },

    // Initialize with empty state to prevent undefined errors
    initializeEmptyState() {
        console.log('Initializing empty state...');
        
        // Initialize with empty arrays to prevent undefined errors
        this.state.tags = [];
        this.state.originalTags = [];
        this.state.selectedTags = new Set();
        this.state.persistentSelectedTags = []; // Changed from Set to Array to preserve order
        
        // Clear any persistent storage
        if (window.localStorage) {
            localStorage.removeItem('selectedTags');
            localStorage.removeItem('selected_tags');
        }
        if (window.sessionStorage) {
            sessionStorage.removeItem('selectedTags');
            sessionStorage.removeItem('selected_tags');
        }
        
        // Don't update UI immediately - let checkForExistingData handle it
        // this.debouncedUpdateAvailableTags([], null);
        // this.updateSelectedTags([]);
        
        // Initialize filters with empty options
        const emptyFilters = {
            vendor: [],
            brand: [],
            productType: [],
            lineage: [],
            weight: []
        };
        this.updateFilters(emptyFilters, false); // Don't preserve values when initializing empty state
        
        console.log('Empty state initialized');
    },

    // Check if there's existing data and load it
    async checkForExistingData() {
        console.log('=== CHECK FOR EXISTING DATA FUNCTION CALLED ===');
        console.log('Checking for existing data...');
        
        // Add timeout protection
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Initialization timeout')), 10000); // 10 second timeout
        });
        
        try {
            // Use the new initial-data endpoint for faster loading with timeout
            const response = await Promise.race([
                fetch('/api/initial-data'),
                timeoutPromise
            ]);
            
            if (response.ok) {
                const data = await response.json();
                console.log('Initial data response:', data);
                if (data.success && data.available_tags && Array.isArray(data.available_tags) && data.available_tags.length > 0) {
                    console.log(`Found ${data.available_tags.length} existing tags, loading data...`);
                    
                    // Update splash progress for data loading
                    AppLoadingSplash.updateProgress(60, 'Loading product data...');
                    
                    // Show action splash for initial tag population
                    this.showActionSplash('Loading product tags...');
                    
                    // Update available tags
                    AppLoadingSplash.updateProgress(75, 'Processing tags...');
                    this.debouncedUpdateAvailableTags(data.available_tags, null);
                    
                    // Restore previously selected tags from backend
                    AppLoadingSplash.updateProgress(85, 'Restoring selections...');
                    console.log('About to fetch and update selected tags...');
                    const selectedTagsResult = await this.fetchAndUpdateSelectedTags();
                    console.log('fetchAndUpdateSelectedTags result:', selectedTagsResult);
                    console.log('persistentSelectedTags after restore:', this.state.persistentSelectedTags);
                    
                    // Update filters
                    AppLoadingSplash.updateProgress(90, 'Setting up filters...');
                    this.updateFilters(data.filters || {
                        vendor: [],
                        brand: [],
                        productType: [],
                        lineage: [],
                        weight: []
                    }, true); // Preserve existing values when loading initial data
                    
                    // Update file info text to show the loaded filename
                    if (data.filename) {
                        const fileInfoText = document.getElementById('fileInfoText');
                        if (fileInfoText) {
                            fileInfoText.textContent = data.filename;
                        }
                    }
                    
                    // Complete splash loading
                    AppLoadingSplash.stopAutoAdvance();
                    AppLoadingSplash.complete();
                    
                    // Hide action splash after a short delay to ensure smooth transition
                    setTimeout(() => {
                        this.hideActionSplash();
                    }, 200);
                    
                    console.log('Initial data loaded successfully');
                    return;
                } else {
                    console.log('No initial data available:', data.message || 'No data found');
                    // Complete splash loading even if no data
                    AppLoadingSplash.stopAutoAdvance();
                    AppLoadingSplash.complete();
                    
                    // Load test data since no initial data was found
                    this.loadTestData();
                    return;
                }
            } else {
                console.log('Initial data endpoint returned error:', response.status);
                // Complete splash loading on error
                AppLoadingSplash.stopAutoAdvance();
                AppLoadingSplash.complete();
                
                // Load test data since initial data failed
                this.loadTestData();
                return;
            }
        } catch (error) {
            console.log('Error loading initial data:', error.message);
            
            // Handle timeout specifically
            if (error.message === 'Initialization timeout') {
                console.log('Initialization timed out, proceeding with empty state');
                AppLoadingSplash.updateProgress(100, 'Ready to upload files');
            }
            
            // Complete splash loading on error
            AppLoadingSplash.stopAutoAdvance();
            AppLoadingSplash.complete();
            
            // Load test data since initial data failed
            this.loadTestData();
            return;
        }
        
    },

    loadTestData() {
        console.log('=== LOAD TEST DATA FUNCTION CALLED ===');
        console.log('Loading test data automatically...');
        
        // Automatically load test data for demonstration
        try {
            const testData = [
                {
                    'Product Name*': 'Blue Dream Flower',
                    'Product Brand': 'Green Valley',
                    'Vendor': 'ABC Dispensary',
                    'Product Type*': 'flower',
                    'Lineage': 'SATIVA',
                    'Weight*': '3.5g',
                    'DOH': 'YES'
                },
                {
                    'Product Name*': 'Purple Kush Concentrate',
                    'Product Brand': 'Purple Labs',
                    'Vendor': 'XYZ Cannabis',
                    'Product Type*': 'concentrate',
                    'Lineage': 'INDICA',
                    'Weight*': '1g',
                    'DOH': 'NO'
                },
                {
                    'Product Name*': 'CBD Gummies',
                    'Product Brand': 'Wellness Co',
                    'Vendor': 'Health Store',
                    'Product Type*': 'edible',
                    'Lineage': 'CBD',
                    'Weight*': '10mg',
                    'DOH': 'YES'
                },
                {
                    'Product Name*': 'Sour Diesel Pre-Roll',
                    'Product Brand': 'Fire Brand',
                    'Vendor': 'Local Dispensary',
                    'Product Type*': 'pre-roll',
                    'Lineage': 'SATIVA',
                    'Weight*': '1g',
                    'DOH': 'YES'
                },
                {
                    'Product Name*': 'OG Kush Flower',
                    'Product Brand': 'OG Farms',
                    'Vendor': 'Premium Cannabis',
                    'Product Type*': 'flower',
                    'Lineage': 'HYBRID',
                    'Weight*': '7g',
                    'DOH': 'NO'
                },
                {
                    'Product Name*': 'Mint Chocolate Chip Edible',
                    'Product Brand': 'Sweet Treats',
                    'Vendor': 'Edibles Plus',
                    'Product Type*': 'edible',
                    'Lineage': 'HYBRID',
                    'Weight*': '50mg',
                    'DOH': 'YES'
                },
                {
                    'Product Name*': 'Lemon Haze Vape Cartridge',
                    'Product Brand': 'Vape Pro',
                    'Vendor': 'Vape Shop',
                    'Product Type*': 'vape cartridge',
                    'Lineage': 'SATIVA',
                    'Weight*': '0.5g',
                    'DOH': 'YES'
                },
                {
                    'Product Name*': 'Granddaddy Purple Concentrate',
                    'Product Brand': 'Purple Labs',
                    'Vendor': 'Premium Cannabis',
                    'Product Type*': 'concentrate',
                    'Lineage': 'INDICA',
                    'Weight*': '2g',
                    'DOH': 'NO'
                }
            ];
            
            console.log('Loading test data automatically...');
            console.log('Test data:', testData);
            if (testData.length > 0) {
                console.log('First test data item fields:', Object.keys(testData[0]));
            }
            
            // Set the test data
            this.state.tags = [...testData];
            this.state.originalTags = [...testData];
            
            console.log('State after loading test data:', {
                tagsLength: this.state.tags.length,
                originalTagsLength: this.state.originalTags.length
            });
            
            // Clear selected tags for fresh start
            this.state.persistentSelectedTags = [];
            this.state.selectedTags = new Set();
            
            // Update the UI with test data
            console.log('Calling _updateAvailableTags with test data...');
            this._updateAvailableTags(testData);
            
            // Update tag counts
            this.updateTagCount('available', testData.length);
            this.updateTagCount('selected', 0);
            
            // Update filters with test data options
            const filters = {
                vendor: [...new Set(testData.map(tag => tag.Vendor || tag.vendor || ''))],
                brand: [...new Set(testData.map(tag => tag['Product Brand'] || tag.brand || ''))],
                productType: [...new Set(testData.map(tag => tag['Product Type*'] || tag.productType || ''))],
                lineage: [...new Set(testData.map(tag => tag.Lineage || tag.lineage || ''))],
                weight: [...new Set(testData.map(tag => tag['Weight*'] || tag.weight || ''))],
                doh: [...new Set(testData.map(tag => tag.DOH || tag.doh || ''))],
                highCbd: ['Non-High CBD Products']
            };
            
            console.log('Test data filters:', filters);
            this.updateFilters(filters, false); // Don't preserve values when loading test data
            
            console.log('Test data loaded successfully:', testData.length, 'tags');
            console.log('Test data sample:', testData[0]);
            
        } catch (error) {
            console.error('Error loading test data:', error);
        }
        
        // Complete splash loading
        AppLoadingSplash.stopAutoAdvance();
        AppLoadingSplash.complete();
    },

    // Debounced version of the label generation logic
    debouncedGenerate: debounce(async function() {
        // Check if tags are loaded before attempting generation
        if (!this.state.tags || !Array.isArray(this.state.tags) || this.state.tags.length === 0) {
            console.error('Cannot generate: No tags loaded. Please upload a file first.');
            return;
        }

        // Force refresh persistentSelectedTags from UI checkboxes before generation
        const checkedFromUI = Array.from(document.querySelectorAll('#selectedTags input[type="checkbox"].tag-checkbox:checked')).map(cb => cb.value);
        if (checkedFromUI.length > 0) {
            this.state.persistentSelectedTags = checkedFromUI;
        }

        console.time('debouncedGenerate');
        const generateBtn = document.getElementById('generateBtn');
        const splashModal = document.getElementById('generationSplashModal');
        const splashCanvas = document.getElementById('generation-splash-canvas');

        // Add generation lock to prevent multiple simultaneous requests
        if (this.isGenerating) {
            console.log('Generation already in progress, ignoring duplicate request');
            return;
        }
        this.isGenerating = true;

        try {
            // Always use the latest persistentSelectedTags for generation
            let checkedTags = [...this.state.persistentSelectedTags];

            console.log('Generation request - persistentSelectedTags:', checkedTags);
            console.log('Generation request - persistentSelectedTags count:', checkedTags.length);

            if (checkedTags.length === 0) {
                console.error('Please select at least one tag to generate');
                return;
            }

            // Get template, scale, and format info
            const templateType = document.getElementById('templateSelect')?.value || 'horizontal';
            const scaleFactor = parseFloat(document.getElementById('scaleInput')?.value) || 1.0;

            // Show enhanced generation splash
            this.showEnhancedGenerationSplash(checkedTags.length, templateType);

            // Disable button and show loading spinner
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
            // Always use DOCX generation
            const apiEndpoint = '/api/generate';

            const response = await fetch(apiEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    selected_tags: checkedTags,
                    template_type: templateType,
                    scale_factor: scaleFactor
                })
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to generate labels');
            }
            const blob = await response.blob();
            
            // Extract filename from Content-Disposition header
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'labels.docx'; // Default filename
            
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="([^"]+)"/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1];
                }
            }
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename; // Set the filename for download
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error generating labels:', error);
        } finally {
            // Hide enhanced generation splash
            this.hideEnhancedGenerationSplash();
            generateBtn.disabled = false;
            generateBtn.innerHTML = 'Generate Tags';
            this.isGenerating = false; // Release generation lock
            console.timeEnd('debouncedGenerate');
        }
    }, 2000), // 2-second debounce delay

    updateTagColor(tag, color) {
        const tagElement = document.querySelector(`[data-tag-id="${tag.id}"]`);
        if (tagElement) {
            // Update the color in the tag object
            tag.color = color;
            
            // Update the color in the UI
            tagElement.style.backgroundColor = color;
            
            // Update the color in the tag list
            const tagListItem = document.querySelector(`[data-tag-id="${tag.id}"]`);
            if (tagListItem) {
                tagListItem.style.backgroundColor = color;
            }
            
            // Update the color in the tag editor if it's open
            const tagEditor = document.getElementById('tagEditor');
            if (tagEditor && tagEditor.dataset.tagId === tag.id) {
                const colorInput = tagEditor.querySelector('#tagColor');
                if (colorInput) {
                    colorInput.value = color;
                }
            }
        }
    },

    getLineageColor(lineage) {
        return this.state.lineageColors[lineage] || 'var(--lineage-mixed)';
    },

    async moveToSelected() {
        console.log('[DEBUG] moveToSelected function called');
        
        // Get checked tags in availableTags
        const checked = Array.from(document.querySelectorAll('#availableTags input[type="checkbox"].tag-checkbox:checked')).map(cb => cb.value);
        console.log('[DEBUG] Found checked tags:', checked);
        
        if (checked.length === 0) {
            console.error('No tags selected to move');
            return;
        }
        
        try {
            // Show action splash for better UX
            this.showActionSplash('Moving tags to selected...');
            
            // Add tags to persistent selected tags (independent of filters)
            checked.forEach(tagName => {
                // Ensure persistentSelectedTags is an array
                if (!Array.isArray(this.state.persistentSelectedTags)) {
                    this.state.persistentSelectedTags = [];
                }
                if (!this.state.persistentSelectedTags.includes(tagName)) {
                    this.state.persistentSelectedTags.push(tagName);
                }
            });
            
            // Update the regular selectedTags set to match persistent ones
            this.state.selectedTags = new Set(this.state.persistentSelectedTags);
            
            // Get the full tag objects for the selected tags - optimized with Map for O(1) lookup
            const tagsMap = new Map(this.state.tags.map(t => [t['Product Name*'], t]));
            const originalTagsMap = new Map(this.state.originalTags.map(t => [t['Product Name*'], t]));
            
            const selectedTagObjects = Array.from(this.state.persistentSelectedTags).map(name => {
                // Safety check: ensure name is valid
                if (!name || typeof name !== 'string') {
                    console.warn('Invalid name in persistentSelectedTags:', name);
                    return null;
                }
                
                // O(1) lookup instead of O(n) find operation
                return tagsMap.get(name) || originalTagsMap.get(name);
            }).filter(Boolean);
            
            // Update the selected tags display
            this.updateSelectedTags(selectedTagObjects);
            
            // Hide selected tags from available tags display for better performance - batched DOM operations
            const availableTagsContainer = document.getElementById('availableTags');
            if (availableTagsContainer) {
                // FIXED: Don't hide selected tags from available display - keep all items visible
                // This allows users to see all available options even after making selections
                console.log('FIXED: Not hiding selected tags from available display - keeping all items visible');
                // All tags remain visible in available list even after selection
            }
            
            // Make API call to backend to persist the changes - non-blocking for better performance
            console.log('[DEBUG] Making API call to /api/move-tags with direction: to_selected');
            console.log('[DEBUG] Tags being moved:', checked);
            console.log('[DEBUG] Current persistent selected tags before move:', this.state.persistentSelectedTags);
            
            // Fire and forget API call for better performance
            fetch('/api/move-tags', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tags: checked,
                    direction: 'to_selected'
                })
            }).then(response => {
                console.log('[DEBUG] API response status:', response.status);
                if (!response.ok) {
                    console.error('Failed to sync with backend:', response.statusText);
                } else {
                    console.log('Successfully synced with backend');
                }
            }).catch(error => {
                console.error('Failed to sync with backend:', error);
            });
            
            // Successfully moved tags to selected
            console.log(`Moved ${checked.length} tags to selected list. Total selected: ${this.state.persistentSelectedTags.length}`);
        } catch (error) {
            console.error('Failed to move tags:', error.message);
        } finally {
            // Hide action splash
            setTimeout(() => {
                this.hideActionSplash();
            }, 300);
        }
    },

    async moveToAvailable() {
        console.log('[DEBUG] moveToAvailable function called');
        
        // Get checked tags in selectedTags
        const checked = Array.from(document.querySelectorAll('#selectedTags input[type="checkbox"].tag-checkbox:checked')).map(cb => cb.value);
        console.log('[DEBUG] Found checked tags:', checked);
        
        if (checked.length === 0) {
            console.error('No tags selected to move');
            return;
        }
        
        // Prevent multiple simultaneous operations
        if (this.isMovingTags) {
            console.log('[DEBUG] Already moving tags, ignoring request');
            return;
        }
        
        this.isMovingTags = true;
        
        try {
            // Show action splash for better UX
            this.showActionSplash('Moving tags to available...');
            
            // Store original state for rollback if needed
            const originalPersistentTags = [...this.state.persistentSelectedTags];
            
            // Remove tags from persistent selected tags
            checked.forEach(tagName => {
                // Ensure persistentSelectedTags is an array
                if (!Array.isArray(this.state.persistentSelectedTags)) {
                    this.state.persistentSelectedTags = [];
                }
                const index = this.state.persistentSelectedTags.indexOf(tagName);
                if (index > -1) {
                    this.state.persistentSelectedTags.splice(index, 1);
                }
            });
            
            // Update the regular selectedTags set to match persistent ones
            this.state.selectedTags = new Set(this.state.persistentSelectedTags);
            
            // Get the full tag objects for the remaining selected tags - optimized with Map for O(1) lookup
            const tagsMap = new Map(this.state.tags.map(t => [t['Product Name*'], t]));
            const originalTagsMap = new Map(this.state.originalTags.map(t => [t['Product Name*'], t]));
            
            const selectedTagObjects = Array.from(this.state.persistentSelectedTags).map(name => {
                // Safety check: ensure name is valid
                if (!name || typeof name !== 'string') {
                    console.warn('Invalid name in persistentSelectedTags:', name);
                    return null;
                }
                
                // O(1) lookup instead of O(n) find operation
                return tagsMap.get(name) || originalTagsMap.get(name);
            }).filter(Boolean);
            
            // Update the selected tags display
            this.updateSelectedTags(selectedTagObjects);
            
            // Get the tag objects for the moved back tags and add them to available tags - optimized with Map
            const movedBackTags = checked.map(tagName => originalTagsMap.get(tagName)).filter(Boolean);
            
            // Show moved back tags in available tags display for better performance - batched DOM operations
            const availableTagsContainer = document.getElementById('availableTags');
            if (availableTagsContainer) {
                const tagElementsToShow = checked.map(tagName => 
                    availableTagsContainer.querySelector(`.tag-checkbox[value="${tagName}"]`)?.closest('.tag-item')
                ).filter(Boolean);
                
                // Batch DOM updates
                tagElementsToShow.forEach(tagItem => {
                    tagItem.style.display = 'block';
                });
            }
            
            // Make API call to backend to persist the changes - non-blocking for better performance
            console.log('[DEBUG] Making API call to /api/move-tags with direction: to_available');
            console.log('[DEBUG] Tags being moved:', checked);
            console.log('[DEBUG] Current persistent selected tags before move:', this.state.persistentSelectedTags);
            
            // Fire and forget API call for better performance
            fetch('/api/move-tags', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tags: checked,
                    direction: 'to_available'
                })
            }).then(response => {
                console.log('[DEBUG] API response status:', response.status);
                if (!response.ok) {
                    console.error('Failed to sync with backend:', response.statusText);
                    // Rollback to original state if backend call failed
                    this.state.persistentSelectedTags = originalPersistentTags;
                    this.state.selectedTags = new Set(originalPersistentTags);
                    
                    // Revert the UI to show the original selected tags
                    const originalSelectedTagObjects = originalPersistentTags.map(name => originalTagsMap.get(name)).filter(Boolean);
                    this.updateSelectedTags(originalSelectedTagObjects);
                    
                    // Show error message to user
                    Toast.show('error', 'Failed to deselect tags. Please try again.');
                } else {
                    console.log('Successfully synced with backend');
                }
                        }).catch(error => {
                console.error('Failed to sync with backend:', error);
                // Rollback to original state if backend call failed
                this.state.persistentSelectedTags = originalPersistentTags;
                this.state.selectedTags = new Set(originalPersistentTags);
                
                // Revert the UI to show the original selected tags
                const originalSelectedTagObjects = originalPersistentTags.map(name => originalTagsMap.get(name)).filter(Boolean);
                this.updateSelectedTags(originalSelectedTagObjects);
                
                // Show error message to user
                Toast.show('error', 'Failed to deselect tags. Please try again.');
            });
            
            // Successfully moved tags to available
            console.log(`Moved ${checked.length} tags to available list. Total selected: ${this.state.persistentSelectedTags.length}`);
        } catch (error) {
            console.error('Failed to move tags:', error.message);
            // Rollback to original state if there was an error
            if (originalPersistentTags) {
                this.state.persistentSelectedTags = originalPersistentTags;
                this.state.selectedTags = new Set(originalPersistentTags);
                
                const originalSelectedTagObjects = originalPersistentTags.map(name => originalTagsMap.get(name)).filter(Boolean);
                this.updateSelectedTags(originalSelectedTagObjects);
            }
            
            Toast.show('error', 'Failed to deselect tags. Please try again.');
        } finally {
            // Reset the moving flag
            this.isMovingTags = false;
            
            // Hide action splash
            setTimeout(() => {
                this.hideActionSplash();
            }, 300);
        }
    },

    async undoMove() {
        try {
            console.log('Starting undo operation...');
            // Show loading splash
            this.showActionSplash('Undoing last action...');
            
            // Call the backend API to undo the last move
            const response = await fetch('/api/undo-move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            console.log('Undo API response status:', response.status);
            
            if (response.ok) {
                const data = await response.json();
                console.log('Undo API response data:', data);
                
                if (data.success) {
                    // Update the persistent selected tags with the restored state
                    this.state.persistentSelectedTags = data.selected_tags;
                    this.state.selectedTags = new Set(data.selected_tags);
                    
                    // Update the selected tags display immediately
                    this.updateSelectedTags(data.selected_tags.map(tagName => 
                        this.state.tags.find(t => t['Product Name*'] === tagName)
                    ).filter(Boolean));
                    
                    // Update available tags with optimized approach
                    this.updateAvailableTagsOptimized(data.available_tags);
                    
                    console.log('Undo completed - restored previous state');
                    
                    // Show success message
                    if (window.Toast) {
                        Toast.show('success', 'Undo completed successfully');
                    }
                } else {
                    console.error('Failed to undo move:', data.error);
                    if (window.Toast) {
                        Toast.show('error', `Undo failed: ${data.error}`);
                    }
                }
            } else {
                const errorData = await response.json();
                console.log('Undo API error response:', errorData);
                
                if (response.status === 400 && errorData.error === 'No undo history available') {
                    console.log('Nothing to undo');
                    if (window.Toast) {
                        Toast.show('info', 'No actions to undo. Try moving some tags first, then use the undo button.');
                    } else {
                        // Fallback if Toast is not available
                        alert('No actions to undo. Try moving some tags first, then use the undo button.');
                    }
                } else {
                    console.error('Failed to undo move on server:', errorData.error);
                    if (window.Toast) {
                        Toast.show('error', `Undo failed: ${errorData.error}`);
                    } else {
                        // Fallback if Toast is not available
                        alert(`Undo failed: ${errorData.error}`);
                    }
                }
            }
        } catch (error) {
            console.error('Failed to undo move:', error.message);
            if (window.Toast) {
                Toast.show('error', `Undo failed: ${error.message}`);
            } else {
                // Fallback if Toast is not available
                alert(`Undo failed: ${error.message}`);
            }
        } finally {
            // Hide loading splash
            this.hideActionSplash();
        }
    },

    async clearSelected() {
        try {
            // Call the backend API to clear selected tags
            const response = await fetch('/api/clear-filters', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Clear persistent selected tags
                this.state.persistentSelectedTags = [];
                this.state.selectedTags.clear();
                
                // Update the selected tags display immediately
                this.updateSelectedTags([]);
                
                // Clear all checkboxes in available tags section
                const availableCheckboxes = document.querySelectorAll('#availableTags input[type="checkbox"]');
                availableCheckboxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
                
                // Clear all checkboxes in selected tags section
                const selectedCheckboxes = document.querySelectorAll('#selectedTags input[type="checkbox"]');
                selectedCheckboxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
                
                // Show all available tags (in case some were hidden)
                const availableTagItems = document.querySelectorAll('#availableTags .tag-item');
                availableTagItems.forEach(item => {
                    item.style.display = 'block';
                });
                
                // Clear filter cache to ensure fresh data
                this.state.filterCache = null;
                
                // Update available tags display to reflect cleared state
                this.efficientlyUpdateAvailableTagsDisplay();
                
                // Update select all checkboxes to unchecked state
                this.updateSelectAllCheckboxes();
                
                console.log('Cleared all selected tags and checkboxes');
            } else {
                console.error('Failed to clear selected tags on server');
            }
        } catch (error) {
            console.error('Failed to clear selected tags:', error.message);
        }
    },

    showExcelLoadingSplash(filename) {
        const splash = document.getElementById('excelLoadingSplash');
        const filenameElement = document.getElementById('excelLoadingFilename');
        const statusElement = document.getElementById('excelLoadingStatus');
        
        if (splash && filenameElement && statusElement) {
            filenameElement.textContent = filename;
            statusElement.textContent = 'Processing...';
            splash.style.display = 'flex';
        }
    },

    hideExcelLoadingSplash() {
        const splash = document.getElementById('excelLoadingSplash');
        
        if (splash) {
            // Hide splash immediately
            splash.style.display = 'none';
        }
    },

    updateExcelLoadingStatus(status) {
        const statusElement = document.getElementById('excelLoadingStatus');
        if (statusElement) {
            statusElement.textContent = status;
        }
    },

    // Action splash screen for clear/undo operations
    showActionSplash(message) {
        // Create splash if it doesn't exist
        let splash = document.getElementById('actionSplash');
        if (!splash) {
            splash = document.createElement('div');
            splash.id = 'actionSplash';
            splash.className = 'action-splash';
            splash.innerHTML = `
                <div class="action-splash-content">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <div class="action-splash-message">${message}</div>
                </div>
            `;
            document.body.appendChild(splash);
        } else {
            const messageElement = splash.querySelector('.action-splash-message');
            if (messageElement) {
                messageElement.textContent = message;
            }
        }
        
        splash.style.display = 'flex';
    },

    hideActionSplash() {
        const splash = document.getElementById('actionSplash');
        if (splash) {
            splash.style.display = 'none';
        }
    },

    showEnhancedGenerationSplash(labelCount, templateType, retryCount = 0) {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.showEnhancedGenerationSplash(labelCount, templateType, retryCount);
            });
            return;
        }
        
        const splashModal = document.getElementById('generationSplashModal');
        
        if (!splashModal) {
            console.error('Generation splash modal not found');
            return;
        }
        
        // Show the modal with loading splash style
        splashModal.style.display = 'flex';
        splashModal.innerHTML = `
            <div class="background-pattern"></div>
            
            <div id="splash-container" style="position: relative; width: 500px; height: 350px; border-radius: 24px; overflow: hidden; background: rgba(22, 33, 62, 0.95); border: 1px solid rgba(0, 212, 170, 0.2); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(0, 212, 170, 0.1); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); z-index: 2;">
                <div class="splash-content" style="position: relative; width: 100%; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 40px; color: white; text-align: center;">
                    <div class="logo-container" style="position: relative; margin-bottom: 20px;">
                        <div class="logo-icon" style="width: 60px; height: 60px; background: linear-gradient(135deg, #00d4aa, #0099cc); border-radius: 15px; display: flex; align-items: center; justify-content: center; font-size: 28px; box-shadow: 0 15px 35px rgba(0, 212, 170, 0.3), 0 0 0 1px rgba(0, 212, 170, 0.2); animation: logo-float 3s ease-in-out infinite; position: relative;">🏷️</div>
                    </div>
                    
                    <h1 class="app-title" style="color: #fff; font-weight: 900; letter-spacing: 3px; font-size: 2.5rem; margin-bottom: 12px; text-shadow: 0 4px 12px rgba(0,0,0,0.5), 0 6px 20px rgba(0,0,0,0.4), 0 2px 4px rgba(160,132,232,0.4), 0 0 30px rgba(160,132,232,0.3); filter: drop-shadow(0 6px 12px rgba(0,0,0,0.4));">AGT DESIGNER</h1>
                    <p class="app-subtitle" style="color: #fff; font-size: 1.2rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 20px; text-shadow: 0 3px 8px rgba(0,0,0,0.5), 0 4px 16px rgba(0,0,0,0.4), 0 2px 4px rgba(139,92,246,0.4), 0 0 20px rgba(139,92,246,0.3); filter: drop-shadow(0 3px 6px rgba(0,0,0,0.4));">AUTO-GENERATING TAG DESIGNER</p>
                    
                    <div class="loading-container" style="width: 100%; max-width: 300px; margin-bottom: 20px;">
                        <div class="loading-bar" style="width: 100%; height: 6px; background: rgba(255, 255, 255, 0.1); border-radius: 3px; overflow: hidden; margin-bottom: 15px; position: relative;">
                            <div class="loading-progress" style="height: 100%; background: linear-gradient(90deg, #00d4aa, #0099cc, #00d4aa); border-radius: 3px; animation: loading-animation 3s ease-in-out infinite; position: relative;"></div>
                        </div>
                        <div class="loading-text" style="font-size: 14px; font-weight: 500; opacity: 0.8; margin-bottom: 15px; transition: opacity 0.3s ease;">Template: ${templateType.toUpperCase()}</div>
                        <div class="loading-text" style="font-size: 14px; font-weight: 500; opacity: 0.8; margin-bottom: 15px; transition: opacity 0.3s ease;">Labels: ${labelCount}</div>
                    </div>
                    
                    <div class="loading-dots" style="display: flex; gap: 6px; justify-content: center; margin-bottom: 15px;">
                        <div class="dot" style="width: 6px; height: 6px; border-radius: 50%; background: rgba(0, 212, 170, 0.6); animation: dot-pulse 1.6s ease-in-out infinite both;"></div>
                        <div class="dot" style="width: 6px; height: 6px; border-radius: 50%; background: rgba(0, 212, 170, 0.6); animation: dot-pulse 1.6s ease-in-out infinite both; animation-delay: -0.16s;"></div>
                        <div class="dot" style="width: 6px; height: 6px; border-radius: 50%; background: rgba(0, 212, 170, 0.6); animation: dot-pulse 1.6s ease-in-out infinite both; animation-delay: -0.32s;"></div>
                    </div>
                    
                    <!-- Copyright text matching title card -->
                    <p style="font-size: 0.9rem; color: rgba(255, 255, 255, 0.8); margin-top: 0.5rem; font-weight: 500; letter-spacing: 1px; text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5), 0 1px 2px rgba(160,132,232,0.3); opacity: 0.9; margin-bottom: 15px;">©2025 Created by Adam Cordova for A Greener Today</p>
                    
                    <div class="features" style="display: flex; gap: 20px; margin-top: 10px;">
                        <div class="feature" style="text-align: center; opacity: 0.6;">
                            <div class="feature-icon" style="font-size: 16px; margin-bottom: 4px;">⚡</div>
                            <div class="feature-text" style="font-size: 10px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">Fast</div>
                        </div>
                        <div class="feature" style="text-align: center; opacity: 0.6;">
                            <div class="feature-icon" style="font-size: 16px; margin-bottom: 4px;">🎯</div>
                            <div class="feature-text" style="font-size: 10px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">Precise</div>
                        </div>
                        <div class="feature" style="text-align: center; opacity: 0.6;">
                            <div class="feature-icon" style="font-size: 16px; margin-bottom: 4px;">🛡️</div>
                            <div class="feature-text" style="font-size: 10px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">Reliable</div>
                        </div>
                    </div>
                </div>
                
                <div class="version-badge" style="position: absolute; top: 15px; right: 15px; background: rgba(0, 212, 170, 0.15); padding: 4px 8px; border-radius: 8px; font-size: 10px; font-weight: 600; backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border: 1px solid rgba(0, 212, 170, 0.2); color: #00d4aa;">v2.0.0</div>
                <div class="status-indicator" style="position: absolute; top: 15px; left: 15px; display: flex; align-items: center; gap: 4px; background: rgba(0, 212, 170, 0.15); padding: 4px 8px; border-radius: 8px; font-size: 10px; font-weight: 600; backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border: 1px solid rgba(0, 212, 170, 0.2); color: #00d4aa;">
                    <div class="status-dot" style="width: 4px; height: 4px; border-radius: 50%; background: #00d4aa; animation: status-pulse 2s ease-in-out infinite;"></div>
                    <span>Processing</span>
                </div>
                <button id="exitGenerationBtn" onclick="TagManager.hideEnhancedGenerationSplash()" style="position: absolute; bottom: 15px; right: 15px; background: rgba(220, 53, 69, 0.8); border: 1px solid rgba(220, 53, 69, 0.8); color: white; padding: 6px 12px; border-radius: 8px; font-size: 11px; font-weight: 600; cursor: pointer; transition: all 0.3s ease; backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);" onmouseover="this.style.background='rgba(220, 53, 69, 1)'; this.style.transform='scale(1.05)'" onmouseout="this.style.background='rgba(220, 53, 69, 0.8)'; this.style.transform='scale(1)'">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 4px;">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                    Exit
                </button>
            </div>
            
            <style>
                .background-pattern {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    opacity: 0.1;
                    background-image: 
                        radial-gradient(circle at 20% 80%, #00d4aa 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, #00d4aa 0%, transparent 50%),
                        radial-gradient(circle at 40% 40%, #00d4aa 0%, transparent 50%);
                    animation: background-shift 8s ease-in-out infinite;
                }
                
                @keyframes background-shift {
                    0%, 100% { transform: scale(1) rotate(0deg); }
                    50% { transform: scale(1.1) rotate(180deg); }
                }
                
                @keyframes logo-float {
                    0%, 100% { 
                        transform: translateY(0px) scale(1);
                    }
                    50% { 
                        transform: translateY(-6px) scale(1.02);
                    }
                }
                
                @keyframes loading-animation {
                    0% { width: 0%; }
                    50% { width: 100%; }
                    100% { width: 0%; }
                }
                
                @keyframes dot-pulse {
                    0%, 80%, 100% {
                        transform: scale(0.8);
                        opacity: 0.4;
                    }
                    40% {
                        transform: scale(1.2);
                        opacity: 1;
                    }
                }
                
                @keyframes status-pulse {
                    0%, 100% { opacity: 0.5; }
                    50% { opacity: 1; }
                }
            </style>
        `;
        
        // Start animated loading text
        const loadingTexts = [
            'Preparing templates...',
            'Processing data...',
            'Generating labels...',
            'Finalizing output...'
        ];
        
        let textIndex = 0;
        const loadingTextElements = splashModal.querySelectorAll('.loading-text');
        
        function updateLoadingText() {
            if (loadingTextElements[1]) {
                loadingTextElements[1].style.opacity = '0';
                setTimeout(() => {
                    loadingTextElements[1].textContent = loadingTexts[textIndex];
                    loadingTextElements[1].style.opacity = '1';
                    textIndex = (textIndex + 1) % loadingTexts.length;
                }, 300);
            }
        }
        
        // Update text every 1.5 seconds
        this._loadingTextInterval = setInterval(updateLoadingText, 1500);
        updateLoadingText(); // Start immediately
    },

    hideEnhancedGenerationSplash() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.hideEnhancedGenerationSplash();
            });
            return;
        }
        
        // Clear the loading text interval
        if (this._loadingTextInterval) {
            clearInterval(this._loadingTextInterval);
            this._loadingTextInterval = null;
        }
        
        const splashModal = document.getElementById('generationSplashModal');
        if (splashModal) {
            splashModal.style.display = 'none';
            console.log('Generation splash hidden successfully');
        } else {
            console.warn('Generation splash modal not found when trying to hide');
        }
    },

    showSimpleGenerationSplash(labelCount, templateType) {
        const splashModal = document.getElementById('generationSplashModal');
        if (!splashModal) {
            console.error('Cannot show simple splash - modal not found');
            return;
        }
        
        // Show a simple text-based splash
        splashModal.style.display = 'flex';
        splashModal.innerHTML = `
            <div class="generation-splash-popup" style="background: rgba(22, 33, 62, 0.95); border-radius: 24px; padding: 40px; text-align: center; color: white; border: 1px solid rgba(0, 212, 170, 0.2); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(0, 212, 170, 0.1);">
                <h1 style="color: #fff; font-weight: 900; letter-spacing: 3px; font-size: 2.5rem; margin-bottom: 12px; text-shadow: 0 4px 12px rgba(0,0,0,0.5), 0 6px 20px rgba(0,0,0,0.4), 0 2px 4px rgba(160,132,232,0.4), 0 0 30px rgba(160,132,232,0.3); filter: drop-shadow(0 6px 12px rgba(0,0,0,0.4));">AGT DESIGNER</h1>
                <p style="color: #fff; font-size: 1.2rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 20px; text-shadow: 0 3px 8px rgba(0,0,0,0.5), 0 4px 16px rgba(0,0,0,0.4), 0 2px 4px rgba(139,92,246,0.4), 0 0 20px rgba(139,92,246,0.3); filter: drop-shadow(0 3px 6px rgba(0,0,0,0.4));">AUTO-GENERATING TAG DESIGNER</p>
                <p style="margin-bottom: 15px;">Generating Labels...</p>
                <p style="margin-bottom: 15px;">Template: ${templateType.toUpperCase()}</p>
                <p style="margin-bottom: 20px;">Labels: ${labelCount}</p>
                <p style="font-size: 1rem; color: rgba(255, 255, 255, 0.8); margin-top: 0.5rem; font-weight: 500; letter-spacing: 1px; text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5), 0 1px 2px rgba(160,132,232,0.3); opacity: 0.9; margin-bottom: 20px;">©2025 Created by Adam Cordova for A Greener Today</p>
                <div style="margin: 20px 0;">
                    <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px;">
                        <div style="width: 100%; height: 100%; background: linear-gradient(90deg, #00d4aa, #0099cc); border-radius: 3px; animation: progress 2s ease-in-out infinite;"></div>
                    </div>
                </div>
                <button onclick="TagManager.hideEnhancedGenerationSplash()" style="background: rgba(220, 53, 69, 0.8); border: 1px solid rgba(220, 53, 69, 0.8); color: white; padding: 8px 16px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.3s ease; margin-top: 15px;" onmouseover="this.style.background='rgba(220, 53, 69, 1)'; this.style.transform='scale(1.05)'" onmouseout="this.style.background='rgba(220, 53, 69, 0.8)'; this.style.transform='scale(1)'">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 6px; vertical-align: middle;">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                    Exit Generation
                </button>
                <style>
                    @keyframes progress { 0% { width: 0%; } 50% { width: 100%; } 100% { width: 0%; } }
                </style>
            </div>
        `;
    },

    // Optimized version of updateAvailableTags that skips complex DOM manipulation
    updateAvailableTagsOptimized(availableTags) {
        if (!availableTags || !Array.isArray(availableTags)) {
            console.warn('updateAvailableTagsOptimized called with invalid availableTags:', availableTags);
            return;
        }
        
        console.time('updateAvailableTagsOptimized');
        
        // Show action splash for optimized tag updates
        this.showActionSplash('Updating tags...');
        
        // Use requestAnimationFrame for smooth performance
        requestAnimationFrame(() => {
            // CRITICAL FIX: Don't filter out JSON matched tags from available tags
            // FIXED: Don't filter out selected tags - keep all items visible in available list
            // This allows users to see all available options even after making selections
            console.log('FIXED: Not filtering out selected tags - keeping all items visible in available list');
            
            // Update state with all available tags (no filtering)
            this.state.tags = [...availableTags];
            
            // Rebuild the available tags display with all tags visible
            this._updateAvailableTags(this.state.originalTags, availableTags);
            
            console.timeEnd('updateAvailableTagsOptimized');
            
            // Hide splash after a short delay
            setTimeout(() => {
                this.hideActionSplash();
            }, 50);
        });
    },

    // Efficient helper to update available tags display without DOM rebuilding
    efficientlyUpdateAvailableTagsDisplay() {
        // FIXED: Don't hide selected tags from available display - keep all items visible
        // This allows users to see all available options even after making selections
        console.log('FIXED: Not hiding selected tags from available display - keeping all items visible');
        
        const availableTagElements = document.querySelectorAll('#availableTags .tag-item');
        
        // Show all tags regardless of selection status
        availableTagElements.forEach(tagElement => {
            tagElement.style.display = 'block';
        });
        
        // Update select all checkboxes state
        this.updateSelectAllCheckboxes();
    },

    // Update select all checkboxes state
    updateSelectAllCheckboxes() {
        // FIXED: Don't filter out hidden elements since we're not hiding any elements anymore
        const availableCheckboxes = document.querySelectorAll('#availableTags .tag-checkbox');
        const checkedCheckboxes = document.querySelectorAll('#availableTags .tag-checkbox:checked');
        
        // Update global select all for available tags
        const selectAllAvailable = document.getElementById('selectAllAvailable');
        if (selectAllAvailable && availableCheckboxes.length > 0) {
            selectAllAvailable.checked = checkedCheckboxes.length === availableCheckboxes.length;
            selectAllAvailable.indeterminate = checkedCheckboxes.length > 0 && checkedCheckboxes.length < availableCheckboxes.length;
        }
        
        // Update selected tags select all checkbox
        const selectedCheckboxes = document.querySelectorAll('#selectedTags .tag-checkbox');
        const selectedChecked = document.querySelectorAll('#selectedTags .tag-checkbox:checked');
        const selectAllSelected = document.getElementById('selectAllSelected');
        
        if (selectAllSelected && selectedCheckboxes.length > 0) {
            selectAllSelected.checked = selectedChecked.length === selectedCheckboxes.length;
            selectAllSelected.indeterminate = selectedChecked.length > 0 && selectedChecked.length < selectedCheckboxes.length;
        }
        
        // Update vendor and brand select all checkboxes for available tags
        const vendorSections = document.querySelectorAll('#availableTags .vendor-section');
        vendorSections.forEach(vendorSection => {
            const vendorCheckboxes = vendorSection.querySelectorAll('.tag-checkbox');
            const vendorChecked = vendorSection.querySelectorAll('.tag-checkbox:checked');
            const vendorSelectAll = vendorSection.querySelector('.select-all-checkbox');
            
            if (vendorSelectAll && vendorCheckboxes.length > 0) {
                vendorSelectAll.checked = vendorChecked.length === vendorCheckboxes.length;
                vendorSelectAll.indeterminate = vendorChecked.length > 0 && vendorChecked.length < vendorCheckboxes.length;
            }
        });
        
        const brandSections = document.querySelectorAll('#availableTags .brand-section');
        brandSections.forEach(brandSection => {
            const brandCheckboxes = brandSection.querySelectorAll('.tag-checkbox');
            const brandChecked = brandSection.querySelectorAll('.tag-checkbox:checked');
            const brandSelectAll = brandSection.querySelector('.select-all-checkbox');
            
            if (brandSelectAll && brandCheckboxes.length > 0) {
                brandSelectAll.checked = brandChecked.length === brandCheckboxes.length;
                brandSelectAll.indeterminate = brandChecked.length > 0 && brandChecked.length < brandCheckboxes.length;
            }
        });
    },

    // Initialize Select All checkbox with proper event listener
    initializeSelectAllCheckbox() {
        const selectAllAvailable = document.getElementById('selectAllAvailable');
        if (selectAllAvailable && !selectAllAvailable.hasAttribute('data-listener-added')) {
            console.log('Initializing Select All Available checkbox');
            selectAllAvailable.setAttribute('data-listener-added', 'true');
            selectAllAvailable.addEventListener('change', (e) => {
                console.log('Select All Available checkbox changed:', e.target.checked);
                const isChecked = e.target.checked;
                
                // Get all visible tag checkboxes in available tags
                const availableCheckboxes = document.querySelectorAll('#availableTags .tag-checkbox');
                console.log('Found available tag checkboxes:', availableCheckboxes.length);
                
                availableCheckboxes.forEach(checkbox => {
                    checkbox.checked = isChecked;
                    const tag = this.state.tags.find(t => t['Product Name*'] === checkbox.value);
                    if (tag) {
                        if (isChecked) {
                            if (!this.state.persistentSelectedTags.includes(tag['Product Name*'])) {
                                this.state.persistentSelectedTags.push(tag['Product Name*']);
                            }
                        } else {
                            const index = this.state.persistentSelectedTags.indexOf(tag['Product Name*']);
                            if (index > -1) {
                                this.state.persistentSelectedTags.splice(index, 1);
                            }
                        }
                    }
                });
                
                // Update the regular selectedTags set to match persistent ones
                this.state.selectedTags = new Set(this.state.persistentSelectedTags);
                
                // Update selected tags display
                const selectedTagObjects = this.state.persistentSelectedTags.map(name =>
                    this.state.tags.find(t => t['Product Name*'] === name)
                ).filter(Boolean);
                
                this.updateSelectedTags(selectedTagObjects);
                
                // Update available tags display to reflect selection changes
                this.efficientlyUpdateAvailableTagsDisplay();
                
                // Update select all checkbox state
                this.updateSelectAllCheckboxes();
            });
        } else if (selectAllAvailable) {
            console.log('Select All Available checkbox already has listener');
        } else {
            console.log('Select All Available checkbox not found, will retry later');
            // Retry after a short delay in case the DOM hasn't loaded yet
            setTimeout(() => this.initializeSelectAllCheckbox(), 100);
        }
    },

    async uploadFile(file) {
        try {
            console.log(`🚀 Starting LIGHTNING upload:`, file.name, 'Size:', file.size, 'bytes');
            
            // Show Excel loading splash screen
            this.showExcelLoadingSplash(file.name);
            
            // Phase 1: Lightning-fast upload (save file only)
            this.updateUploadUI(`⚡ Lightning upload: ${file.name}...`);
            
            const formData = new FormData();
            formData.append('file', file);
            
            console.log('🚀 Sending lightning upload request...');
            
            const uploadResponse = await fetch('/upload-lightning', {
                method: 'POST',
                body: formData
            });
            
            const uploadData = await uploadResponse.json();
            console.log('⚡ Lightning upload response:', uploadData);
            
            if (!uploadResponse.ok) {
                throw new Error(uploadData.error || 'Lightning upload failed');
            }
            
            // Phase 2: Background processing
            this.updateUploadUI(`🔄 Processing ${file.name}...`);
            console.log('🔄 Starting background processing...');
            
            const processResponse = await fetch('/process-lightning', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    file_path: uploadData.file_path,
                    filename: uploadData.filename
                })
            });
            
            const processData = await processResponse.json();
            console.log('✅ Processing response:', processData);
            
            if (!processResponse.ok) {
                throw new Error(processData.error || 'Processing failed');
            }
            
            // Success!
            this.updateUploadUI(`✅ ${file.name} ready!`, 'File processed successfully', 'success');
            console.log(`✅ Lightning upload completed! Upload: ${uploadData.upload_time?.toFixed(3)}s, Process: ${processData.process_time?.toFixed(3)}s`);
            
            // Refresh the page to show new data
            setTimeout(() => {
                console.log('🔄 Refreshing page to show new data...');
                window.location.reload();
            }, 1000);
            
            return; // Success!
        } catch (error) {
            console.error('⚡ Lightning upload error:', error);
            this.hideExcelLoadingSplash();
            this.updateUploadUI('Upload failed: ' + error.message, 'error');
            return;
        }
    },
    // Fallback upload method for PythonAnywhere
    async uploadFileFallback(file) {
        try {
            console.log('Using fallback upload method for:', file.name);
            
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok && data.status === 'ready') {
                console.log('Fallback upload successful');
                this.updateUploadUI(file.name, 'File uploaded successfully', 'success');
                // Refresh the page to load the new file
                window.location.reload();
                return true;
            } else {
                console.error('Fallback upload failed:', data.error);
                this.updateUploadUI('Upload failed: ' + (data.error || 'Unknown error'), 'error');
                return false;
            }
        } catch (error) {
            console.error('Fallback upload error:', error);
            this.updateUploadUI('Upload failed: ' + error.message, 'error');
            return false;
        }
    },

    async pollUploadStatusAndUpdateUI(filename, displayName) {
        console.log(`Polling upload status for: ${filename}`);
        
        const maxAttempts = 60; // 3 minutes max (3 seconds * 60 = 3 minutes)
        let attempts = 0;
        let consecutiveErrors = 0;
        const maxConsecutiveErrors = 5;
        
        // Add debug logging for upload processing
        console.log(`[UPLOAD DEBUG] Starting status polling for: ${filename}`);
        
        while (attempts < maxAttempts) {
            try {
                const response = await fetch(`/api/upload-status?filename=${encodeURIComponent(filename)}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                const status = data.status;
                const age = data.age_seconds || 0;
                const totalFiles = data.total_processing_files || 0;
                
                console.log(`Upload status: ${status} (age: ${age}s, total files: ${totalFiles})`);
                consecutiveErrors = 0; // Reset error counter on successful response
                
                if (status === 'ready' || status === 'done') {
                    // File is ready for basic operations
                    console.log(`[UPLOAD DEBUG] File marked as ready: ${filename}`);
                    this.hideExcelLoadingSplash();
                    this.updateUploadUI(displayName, 'File ready!', 'success');
                    // Toast.show('success', 'File uploaded and ready!'); // Removed notification
                    
                    // Load the data - ensure all operations complete successfully
                    // Force a small delay to ensure backend processing is complete
                    console.log(`[UPLOAD DEBUG] Waiting 1 second before finalizing...`);
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    // Show action splash for upload completion
                    console.log(`[UPLOAD DEBUG] Starting finalization process...`);
                    this.showActionSplash('Finalizing upload...');
                    
                    // Clear any cached data to force fresh data from backend
                    try {
                        await fetch('/api/clear-cache', { method: 'POST' });
                        console.log('Cleared backend cache after upload');
                    } catch (cacheError) {
                        console.warn('Failed to clear cache:', cacheError);
                    }
                    
                    console.log(`[UPLOAD DEBUG] Loading available tags...`);
                    const availableTagsLoaded = await this.fetchAndUpdateAvailableTags();
                    console.log(`[UPLOAD DEBUG] Available tags loaded: ${availableTagsLoaded}`);
                    
                    console.log(`[UPLOAD DEBUG] Loading selected tags...`);
                    const selectedTagsLoaded = await this.fetchAndUpdateSelectedTags();
                    console.log(`[UPLOAD DEBUG] Selected tags loaded: ${selectedTagsLoaded}`);
                    
                    console.log(`[UPLOAD DEBUG] Loading filter options...`);
                    await this.fetchAndPopulateFilters();
                    console.log(`[UPLOAD DEBUG] Filter options loaded`);
                    
                    // Force refresh lineage colors by re-rendering tags
                    if (availableTagsLoaded && this.state.tags && this.state.tags.length > 0) {
                        console.log('[UPLOAD DEBUG] Forcing lineage color refresh after upload...');
                        this._updateAvailableTags(this.state.tags);
                    }
                    
                    if (!availableTagsLoaded) {
                        console.error('[UPLOAD DEBUG] Failed to load available tags after upload');
                        console.error('Failed to load product data. Please try refreshing the page.');
                        return;
                    }
                    
                    console.log('[UPLOAD DEBUG] Upload processing complete');
                    return;
                } else if (status === 'processing') {
                    // Still processing, show progress
                    this.updateUploadUI(`Processing ${displayName}...`);
                    this.updateExcelLoadingStatus('Processing Excel data...');
                    
                } else if (status === 'not_found') {
                    // File not found in processing status - might be a race condition
                    console.warn(`File not found in processing status: ${filename} (age: ${age}s, total files: ${totalFiles})`);
                    
                    // If we've had a successful 'ready' status before, the file might have been processed
                    // Try to load the data anyway to see if it's available
                    if (attempts > 5) {
                        console.log('Attempting to load data despite not_found status...');
                        try {
                            const availableTagsLoaded = await this.fetchAndUpdateAvailableTags();
                            if (availableTagsLoaded && this.state.tags && this.state.tags.length > 0) {
                                console.log('Data loaded successfully despite not_found status');
                                this.hideExcelLoadingSplash();
                                this.updateUploadUI(displayName, 'File ready!', 'success');
                                return;
                            }
                        } catch (loadError) {
                            console.warn('Failed to load data despite not_found status:', loadError);
                        }
                    }
                    
                    if (attempts < 20) { // Give it more attempts for race conditions (increased from 15)
                        this.updateUploadUI(`Processing ${displayName}...`);
                        this.updateExcelLoadingStatus('Waiting for processing to start...');
                    } else {
                        this.hideExcelLoadingSplash();
                        this.updateUploadUI('Upload failed', 'File processing status lost', 'error');
                        console.error('Upload failed: Processing status lost. Please try again.');
                        return;
                    }
                    
                } else {
                    console.warn(`Unknown status: ${status}`);
                }
                
            } catch (error) {
                console.error('Error polling upload status:', error);
                consecutiveErrors++;
                
                if (consecutiveErrors >= maxConsecutiveErrors) {
                    this.hideExcelLoadingSplash();
                    this.updateUploadUI('Upload failed', 'Network error', 'error');
                    console.error('Upload failed: Network error. Please try again.');
                    return;
                }
                
                // Continue polling but with longer delay on errors
                await new Promise(resolve => setTimeout(resolve, 3000));
                continue;
            }
            
            attempts++;
            await new Promise(resolve => setTimeout(resolve, 3000)); // Poll every 3 seconds
        }
        
        // Timeout
        this.hideExcelLoadingSplash();
        this.updateUploadUI('Upload timed out', 'Processing took too long', 'error');
                            console.error('Upload timed out. Please try again.');
    },

    updateUploadUI(fileName, statusMessage, statusType) {
        const currentFileInfo = document.getElementById('currentFileInfo');
        const fileInfoText = document.getElementById('fileInfoText');
        
        if (currentFileInfo) {
            // Keep the default filename instead of showing the uploaded file name
            // Only show status messages, not the uploaded filename
            if (statusMessage && statusType) {
                // Show status message temporarily
                const originalText = currentFileInfo.textContent;
                currentFileInfo.textContent = statusMessage;
                currentFileInfo.classList.add(statusType);
                setTimeout(() => {
                    currentFileInfo.textContent = originalText;
                    currentFileInfo.classList.remove(statusType);
                }, 3000);
            } else if (statusMessage && !statusType) {
                // This is likely an error or "No file selected" message
                currentFileInfo.textContent = statusMessage;
            }
            // Don't update the filename for successful uploads - keep the default filename
        }
        
        // Update the file info text if a filename is provided
        if (fileName && fileInfoText) {
            fileInfoText.textContent = fileName;
        }
    },

    moveToSelected: function(tagsToMove) {
        tagsToMove.forEach(tag => {
            // Remove from available, add to selected
            // (implement your logic here)
            this.state.selectedTags.add(tag);
            // Optionally, remove from availableTags set/list
        });
        // Refresh UI
        this.fetchAndUpdateAvailableTags();
        this.fetchAndUpdateSelectedTags();
    },

    onTagsLoaded: function(tags) {
        TagsTable.updateTagsList('availableTags', tags);
        // Auto check all available tags call removed
    },

    setupFilterEventListeners() {
        const filterIds = ['vendorFilter', 'brandFilter', 'productTypeFilter', 'lineageFilter', 'weightFilter', 'dohFilter', 'highCbdFilter'];
        
        console.log('Setting up filter event listeners...');
        console.log('TagManager instance:', this);
        console.log('this.applyFilters:', typeof this.applyFilters);
        
        // Create a debounced version of the filter update function
        const debouncedFilterUpdate = debounce(async (filterType, value) => {
            console.log('Filter changed:', filterType, value);
            
            // Update table header if TagsTable is available
            if (filterType === 'productType' && typeof TagsTable !== 'undefined' && TagsTable.updateTableHeader) {
                TagsTable.updateTableHeader();
            }
            
            // Update filter options for cascading behavior
            await this.updateFilterOptions();
            
            // Apply the filters to the tag lists
            this.applyFilters();
            this.renderActiveFilters();
        }, 150); // 150ms debounce delay
        
        filterIds.forEach(filterId => {
            const filterElement = document.getElementById(filterId);
            console.log(`Filter element ${filterId}:`, filterElement);
            console.log(`Filter element ${filterId} exists:`, !!filterElement);
            console.log(`Filter element ${filterId} value:`, filterElement?.value);
            console.log(`Filter element ${filterId} options:`, filterElement?.options?.length);
            
            if (filterElement) {
                // Remove any existing event listeners first
                filterElement.removeEventListener('change', filterElement._filterChangeHandler);
                
                // Create new event handler
                const self = this; // Capture 'this' context
                filterElement._filterChangeHandler = (event) => {
                    console.log(`Filter ${filterId} changed to:`, event.target.value);
                    const filterType = self.getFilterTypeFromId(filterId);
                    const value = event.target.value;
                    
                    // Special handling for vendor filter - reset all other filters when vendor changes
                    if (filterId === 'vendorFilter' && value && value.trim() !== '' && value.toLowerCase() !== 'all') {
                        console.log('Vendor filter changed, resetting all other filters...');
                        self.resetAllOtherFilters();
                    }
                    
                    // Only use debounced filter updates to prevent race conditions
                    debouncedFilterUpdate(filterType, value);
                };
                
                filterElement.addEventListener('change', filterElement._filterChangeHandler);
                console.log(`Event listener attached to ${filterId}`);
            } else {
                console.warn(`Filter element ${filterId} not found`);
            }
        });
    },

    setupSearchEventListeners() {
        console.log('Setting up search event listeners...');
        
        // Add search event listeners for available tags
        const availableTagsSearch = document.getElementById('availableTagsSearch');
        if (availableTagsSearch) {
            availableTagsSearch.removeEventListener('input', this.handleAvailableTagsSearch.bind(this));
            availableTagsSearch.addEventListener('input', this.handleAvailableTagsSearch.bind(this));
            console.log('Added event listener to availableTagsSearch');
        } else {
            console.warn('Available tags search element not found');
        }
        
        // Add search event listeners for selected tags
        const selectedTagsSearch = document.getElementById('selectedTagsSearch');
        if (selectedTagsSearch) {
            selectedTagsSearch.removeEventListener('input', this.handleSelectedTagsSearch.bind(this));
            selectedTagsSearch.addEventListener('input', this.handleSelectedTagsSearch.bind(this));
            console.log('Added event listener to selectedTagsSearch');
        } else {
            console.warn('Selected tags search element not found');
        }
    },

    getFilterTypeFromId(filterId) {
        const idToType = {
            'vendorFilter': 'vendor',
            'brandFilter': 'brand',
            'productTypeFilter': 'productType',
            'lineageFilter': 'lineage',
            'weightFilter': 'weight',
            'dohFilter': 'doh',
            'highCbdFilter': 'highCbd'
        };
        return idToType[filterId] || filterId;
    },

    // Add this function to render active filters above the Available list
    renderActiveFilters() {
        const filterIds = [
            { id: 'vendorFilter', label: 'Vendor' },
            { id: 'brandFilter', label: 'Brand' },
            { id: 'productTypeFilter', label: 'Type' },
            { id: 'lineageFilter', label: 'Lineage' },
            { id: 'weightFilter', label: 'Weight' },
            { id: 'dohFilter', label: 'DOH' },
            { id: 'highCbdFilter', label: 'High CBD' }
        ];
        let container = document.getElementById('activeFiltersContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'activeFiltersContainer';
            container.style.display = 'flex';
            container.style.gap = '0.5rem';
            container.style.marginBottom = '0.5rem';
            container.style.alignItems = 'center';
            container.style.flexWrap = 'wrap';
            const availableTags = document.getElementById('availableTags');
            if (availableTags && availableTags.parentNode) {
                availableTags.parentNode.insertBefore(container, availableTags);
            }
        }
        container.innerHTML = '';
        
        // Add "Clear All Filters" button if any filters are active
        const activeFilters = filterIds.filter(({ id }) => {
            const select = document.getElementById(id);
            return select && select.value && select.value !== '' && select.value.toLowerCase() !== 'all';
        });
        
        if (activeFilters.length > 0) {
            const clearAllBtn = document.createElement('button');
            clearAllBtn.textContent = 'Clear All Filters';
            clearAllBtn.style.background = 'rgba(255,255,255,0.1)';
            clearAllBtn.style.border = '1px solid rgba(255,255,255,0.3)';
            clearAllBtn.style.borderRadius = '6px';
            clearAllBtn.style.padding = '4px 8px';
            clearAllBtn.style.fontSize = '0.8em';
            clearAllBtn.style.color = '#fff';
            clearAllBtn.style.cursor = 'pointer';
            clearAllBtn.style.marginRight = '0.5rem';
            clearAllBtn.addEventListener('click', () => {
                this.clearAllFilters();
            });
            container.appendChild(clearAllBtn);
        }
        
        filterIds.forEach(({ id, label }) => {
            const select = document.getElementById(id);
            if (select && select.value && select.value !== '' && select.value.toLowerCase() !== 'all') {
                const filterDiv = document.createElement('div');
                filterDiv.style.display = 'flex';
                filterDiv.style.alignItems = 'center';
                filterDiv.style.background = 'rgba(255,255,255,0.08)';
                filterDiv.style.borderRadius = '8px';
                filterDiv.style.padding = '2px 8px';
                filterDiv.style.fontSize = '0.85em';
                filterDiv.style.color = '#fff';
                filterDiv.style.fontWeight = '500';
                filterDiv.style.gap = '0.25em';
                filterDiv.innerHTML = `${label}: ${select.value}`;
                const closeBtn = document.createElement('span');
                closeBtn.textContent = '×';
                closeBtn.style.cursor = 'pointer';
                closeBtn.style.marginLeft = '4px';
                closeBtn.style.fontSize = '1em';
                closeBtn.setAttribute('aria-label', `Clear ${label} filter`);
                closeBtn.addEventListener('click', () => {
                    select.value = '';
                    // Trigger change event to update filters
                    select.dispatchEvent(new Event('change', { bubbles: true }));
                });
                filterDiv.appendChild(closeBtn);
                container.appendChild(filterDiv);
            }
        });
    },

    // Add function to clear all filters at once
    clearAllFilters() {
        console.log('Clearing all filters...');
        
        const filterIds = ['vendorFilter', 'brandFilter', 'productTypeFilter', 'lineageFilter', 'weightFilter', 'dohFilter', 'highCbdFilter'];
        
        // Clear each filter dropdown
        filterIds.forEach(filterId => {
            const filterElement = document.getElementById(filterId);
            if (filterElement) {
                filterElement.value = '';
            }
        });
        
        // Apply the cleared filters
        this.applyFilters();
        this.renderActiveFilters();
        
        // Also update the filter dropdowns to reflect the cleared state
        if (this.state.originalFilterOptions.vendor) {
            this.updateFilters(this.state.originalFilterOptions, false); // Don't preserve values when clearing
        }
        
        // Success message removed to prevent popup
        
        // Add visual feedback to the button
        const clearBtn = document.getElementById('clearFiltersBtn');
        if (clearBtn) {
            clearBtn.style.transform = 'scale(0.95)';
            setTimeout(() => {
                clearBtn.style.transform = 'scale(1)';
            }, 150);
        }
        
        console.log('All filters cleared successfully');
    },

    // Function to reset all other filters when vendor changes (but keep vendor filter)
    resetAllOtherFilters() {
        console.log('Resetting all other filters while keeping vendor filter...');
        
        // Get the current vendor filter value to preserve it
        const vendorFilter = document.getElementById('vendorFilter');
        const currentVendorValue = vendorFilter ? vendorFilter.value : '';
        
        // List of all filters except vendor
        const otherFilterIds = ['brandFilter', 'productTypeFilter', 'lineageFilter', 'weightFilter', 'dohFilter', 'highCbdFilter'];
        
        // Clear all other filter dropdowns
        otherFilterIds.forEach(filterId => {
            const filterElement = document.getElementById(filterId);
            if (filterElement) {
                filterElement.value = '';
                console.log(`Cleared ${filterId}`);
            }
        });
        
        // Update filter options to reflect the new vendor selection
        this.updateFilterOptions();
        
        // Apply the updated filters (vendor only)
        this.applyFilters();
        this.renderActiveFilters();
        
        console.log('All other filters reset successfully, vendor filter preserved:', currentVendorValue);
    },

    // Emergency function to clear stuck upload UI
    forceClearUploadUI() {
        console.log('Force clearing upload UI state...');
        
        // Hide any loading splash
        this.hideExcelLoadingSplash();
        
        // Clear the file info display
        const currentFileInfo = document.getElementById('currentFileInfo');
        const fileInfoText = document.getElementById('fileInfoText');
        
        if (currentFileInfo) {
            currentFileInfo.textContent = 'No file selected';
            currentFileInfo.className = ''; // Remove any status classes
        }
        
        if (fileInfoText) {
            fileInfoText.textContent = '';
        }
        
        // Force refresh the data
        this.fetchAndUpdateAvailableTags();
        this.fetchAndUpdateSelectedTags();
        this.fetchAndPopulateFilters();
        
        console.log('Upload UI state cleared');
    },

    // Clear all UI state when a new file is uploaded
    clearUIStateForNewFile(preserveFilters = false) {
        console.log('Clearing UI state for new file upload, preserveFilters:', preserveFilters);
        
        // Clear persistent selected tags
        this.state.persistentSelectedTags = [];
        this.state.selectedTags.clear();
        
        // Clear tag displays
        const availableContainer = document.getElementById('availableTags');
        const selectedContainer = document.getElementById('selectedTags');
        
        if (availableContainer) {
            // Clear available tags but keep the select all container
            const selectAllContainer = availableContainer.querySelector('.select-all-container');
            availableContainer.innerHTML = '';
            if (selectAllContainer) {
                availableContainer.appendChild(selectAllContainer);
            }
        }
        
        if (selectedContainer) {
            selectedContainer.innerHTML = '';
        }
        
        // Clear search inputs
        const searchInputs = document.querySelectorAll('input[type="text"]');
        searchInputs.forEach(input => {
            if (input.placeholder && input.placeholder.includes('Search')) {
                input.value = '';
            }
        });
        
        // Only clear filters if explicitly requested (for actual new file uploads)
        if (!preserveFilters) {
            console.log('Clearing filter settings for new file upload');
            const filterSelects = document.querySelectorAll('select[id*="Filter"]');
            filterSelects.forEach(select => {
                select.value = '';
            });
            
            // Reset filter state to defaults
            this.state.filters = {
                vendor: 'All',
                brand: 'All',
                productType: 'All',
                lineage: 'All',
                weight: 'All',
                doh: 'All',
                highCbd: 'All'
            };
        } else {
            console.log('Preserving filter settings during UI refresh');
        }
        
        // Update tag counts
        this.updateTagCount('available', 0);
        this.updateTagCount('selected', 0);
        
        console.log('UI state cleared for new file');
    },

    // Validate and clean up selected tags against current Excel data
    validateSelectedTags() {
        // Add safeguard to prevent clearing tags that were just added via JSON matching
        const hasJsonMatchedTags = this.state.persistentSelectedTags.length > 0;
        
        if (!this.state.originalTags || this.state.originalTags.length === 0) {
            // No Excel data loaded, but don't clear if we have JSON matched tags
            if (!hasJsonMatchedTags) {
                this.state.persistentSelectedTags = [];
                this.state.selectedTags.clear();
            } else {
                console.log('Preserving JSON matched tags even though no Excel data is loaded yet');
            }
            return;
        }

        // Create case-insensitive lookup maps
        const validProductNamesLower = new Map();
        this.state.originalTags.forEach(tag => {
            const name = tag['Product Name*'];
            if (name) {
                validProductNamesLower.set(name.toLowerCase(), name); // Store original case
            }
        });

        const invalidTags = [];
        const validTags = [];
        const correctedTags = new Set();

        // Check each selected tag with case-insensitive comparison
        for (const tagName of this.state.persistentSelectedTags) {
            const tagNameLower = tagName.toLowerCase();
            const originalName = validProductNamesLower.get(tagNameLower);
            
            if (originalName) {
                // Tag exists, use the original case from Excel data
                validTags.push(originalName);
                correctedTags.add(originalName);
            } else {
                invalidTags.push(tagName);
            }
        }

        // Only clear and update if we actually found invalid tags
        if (invalidTags.length > 0) {
            // Remove invalid tags and update with corrected case
            this.state.persistentSelectedTags = [];
            correctedTags.forEach(tagName => {
                if (!this.state.persistentSelectedTags.includes(tagName)) {
                                this.state.persistentSelectedTags.push(tagName);
                            };
            });

            // Update the regular selectedTags set
            this.state.selectedTags = new Set(this.state.persistentSelectedTags);

            // Show warning if invalid tags were found
            console.warn(`Removed ${invalidTags.length} tags that don't exist in current Excel data:`, invalidTags);
            if (window.Toast) {
                window.Toast.show(`Removed ${invalidTags.length} tags that don't exist in current data`, 'warning');
            }

            // Update the UI to reflect the cleaned selections
            const validTagObjects = validTags.map(name => 
                this.state.originalTags.find(t => t['Product Name*'] === name)
            ).filter(Boolean);
            
            this.updateSelectedTags(validTagObjects);
        }
    },

    async syncDeselectionWithBackend(tagName) {
        // Synchronize deselection of JSON matched items with the backend
        try {
            console.log(`Syncing deselection of JSON matched item: ${tagName}`);
            
            // Call the move tags API to ensure backend state is updated
            const response = await fetch('/api/move-tags', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tags: [tagName],
                    direction: 'to_available'
                })
            });
            
            if (!response.ok) {
                console.warn(`Failed to sync deselection with backend for ${tagName}`);
            } else {
                console.log(`Successfully synced deselection of ${tagName} with backend`);
            }
        } catch (error) {
            console.error(`Error syncing deselection with backend: ${error}`);
        }
    },

    updateTagLineage(tag, lineage) {
        // Update the lineage in the tag object
        tag.lineage = lineage;
        
        // Update the color based on the new lineage
        const newColor = this.getLineageColor(lineage);
        this.updateTagColor(tag, newColor);
    },

    // Ensure proper scrolling behavior for tag containers
    hasActiveFilters() {
        // Check if any filters are currently active (not set to "All")
        const vendorFilter = document.getElementById('vendorFilter')?.value || '';
        const brandFilter = document.getElementById('brandFilter')?.value || '';
        const productTypeFilter = document.getElementById('productTypeFilter')?.value || '';
        const lineageFilter = document.getElementById('lineageFilter')?.value || '';
        const weightFilter = document.getElementById('weightFilter')?.value || '';
        const dohFilter = document.getElementById('dohFilter')?.value || '';
        const highCbdFilter = document.getElementById('highCbdFilter')?.value || '';
        
        const filters = [vendorFilter, brandFilter, productTypeFilter, lineageFilter, weightFilter, dohFilter, highCbdFilter];
        
        // Return true if any filter is not empty and not "All"
        return filters.some(filter => filter && filter.trim() !== '' && filter.toLowerCase() !== 'all');
    },

    clearFiltersForDeselectedTag(tag) {
        /**
         * Clear filters that match the deselected tag's properties.
         * This ensures that when a tag is deselected, the corresponding
         * filters in Current Inventory are also cleared.
         */
        console.log('Clearing filters for deselected tag:', tag['Product Name*']);
        
        let filtersCleared = false;
        
        // Check and clear vendor filter if it matches the deselected tag
        const vendorFilter = document.getElementById('vendorFilter');
        if (vendorFilter && vendorFilter.value && vendorFilter.value.trim() !== '') {
            const tagVendor = (tag.Vendor || tag.vendor || '').toString().trim();
            if (tagVendor.toLowerCase() === vendorFilter.value.toLowerCase()) {
                console.log(`Clearing vendor filter: ${vendorFilter.value} (matches deselected tag)`);
                vendorFilter.value = '';
                filtersCleared = true;
            }
        }
        
        // Check and clear brand filter if it matches the deselected tag
        const brandFilter = document.getElementById('brandFilter');
        if (brandFilter && brandFilter.value && brandFilter.value.trim() !== '') {
            const tagBrand = (tag['Product Brand'] || tag.productBrand || '').toString().trim();
            if (tagBrand.toLowerCase() === brandFilter.value.toLowerCase()) {
                console.log(`Clearing brand filter: ${brandFilter.value} (matches deselected tag)`);
                brandFilter.value = '';
                filtersCleared = true;
            }
        }
        
        // Check and clear product type filter if it matches the deselected tag
        const productTypeFilter = document.getElementById('productTypeFilter');
        if (productTypeFilter && productTypeFilter.value && productTypeFilter.value.trim() !== '') {
            const tagProductType = (tag['Product Type*'] || tag.productType || '').toString().trim();
            if (tagProductType.toLowerCase() === productTypeFilter.value.toLowerCase()) {
                console.log(`Clearing product type filter: ${productTypeFilter.value} (matches deselected tag)`);
                productTypeFilter.value = '';
                filtersCleared = true;
            }
        }
        
        // Check and clear lineage filter if it matches the deselected tag
        const lineageFilter = document.getElementById('lineageFilter');
        if (lineageFilter && lineageFilter.value && lineageFilter.value.trim() !== '') {
            const tagLineage = (tag.Lineage || tag.lineage || '').toString().trim();
            if (tagLineage.toLowerCase() === lineageFilter.value.toLowerCase()) {
                console.log(`Clearing lineage filter: ${lineageFilter.value} (matches deselected tag)`);
                lineageFilter.value = '';
                filtersCleared = true;
            }
        }
        
        // Check and clear weight filter if it matches the deselected tag
        const weightFilter = document.getElementById('weightFilter');
        if (weightFilter && weightFilter.value && weightFilter.value.trim() !== '') {
            // CRITICAL FIX: Check all possible weight field variations when clearing filters
            const tagWeight = (tag.WeightUnits || tag.WeightWithUnits || tag.weightWithUnits || 
                             tag.CombinedWeight || tag.weightUnits || '').toString().trim();
            if (tagWeight.toLowerCase() === weightFilter.value.toLowerCase()) {
                console.log(`Clearing weight filter: ${weightFilter.value} (matches deselected tag)`);
                weightFilter.value = '';
                filtersCleared = true;
            }
        }
        
        // Check and clear DOH filter if it matches the deselected tag
        const dohFilter = document.getElementById('dohFilter');
        if (dohFilter && dohFilter.value && dohFilter.value.trim() !== '') {
            const tagDoh = (tag.DOH || tag.doh || '').toString().toUpperCase();
            const filterDoh = dohFilter.value.toUpperCase();
            if (tagDoh === filterDoh) {
                console.log(`Clearing DOH filter: ${dohFilter.value} (matches deselected tag)`);
                dohFilter.value = '';
                filtersCleared = true;
            }
        }
        
        // Check and clear High CBD filter if it matches the deselected tag
        const highCbdFilter = document.getElementById('highCbdFilter');
        if (highCbdFilter && highCbdFilter.value && highCbdFilter.value.trim() !== '') {
            const tagProductType = (tag['Product Type*'] || tag.productType || '').toString().toLowerCase();
            const filterHighCbd = highCbdFilter.value.toLowerCase();
            if (tagProductType.startsWith('high cbd') && filterHighCbd === 'yes') {
                console.log(`Clearing High CBD filter: ${highCbdFilter.value} (matches deselected tag)`);
                highCbdFilter.value = '';
                filtersCleared = true;
            }
        }
        
        // If any filters were cleared, apply the updated filters to refresh the inventory
        if (filtersCleared) {
            console.log('Filters cleared, applying updated filters to refresh inventory...');
            this.applyFilters();
            this.renderActiveFilters();
        }
    },

    ensureProperScrolling() {
        const containers = document.querySelectorAll('.tag-list-container');
        containers.forEach(container => {
            // Remove any height restrictions
            container.style.maxHeight = 'none';
            container.style.height = 'auto';
            
            // Ensure overflow is set to visible to prevent scrollbars
            container.style.overflowY = 'visible';
            container.style.overflowX = 'hidden';
            
            // Force a reflow to ensure changes take effect
            container.offsetHeight;
            
            // Also ensure all child elements can expand
            const children = container.querySelectorAll('*');
            children.forEach(child => {
                child.style.maxHeight = 'none';
                child.style.height = 'auto';
            });
        });
        
        // Also ensure parent containers can expand
        const parentContainers = document.querySelectorAll('.glass-card, .card-body, .col-lg-5');
        parentContainers.forEach(container => {
            container.style.height = 'auto';
            container.style.maxHeight = 'none';
        });
    },

    removeDropdownInstructionBlurb() {
        // Remove the instructional blurb when any chevron is clicked
        const blurb = document.getElementById('dropdownInstructionBlurb');
        if (blurb && !blurb.classList.contains('hidden')) {
            blurb.classList.add('hidden');
            
            // Remove the element from DOM after animation completes
            setTimeout(() => {
                if (blurb && blurb.parentNode) {
                    blurb.parentNode.removeChild(blurb);
                }
            }, 300); // Match the CSS transition duration
        }
    },
};

// Expose TagManager to global scope
window.TagManager = TagManager;
window.updateAvailableTags = TagManager.debouncedUpdateAvailableTags.bind(TagManager);
window.updateFilters = TagManager.updateFilters.bind(TagManager);
window.fetchAndUpdateSelectedTags = TagManager.fetchAndUpdateSelectedTags.bind(TagManager);

function attachSelectedTagsCheckboxListeners() {
    const container = document.getElementById('selectedTags');
    if (!container) return;

    // Parent checkboxes
    container.querySelectorAll('.select-all-checkbox').forEach(parentCheckbox => {
        parentCheckbox.disabled = false;
        const newCheckbox = parentCheckbox.cloneNode(true);
        parentCheckbox.parentNode.replaceChild(newCheckbox, parentCheckbox);

        newCheckbox.addEventListener('change', function(e) {
            console.log('Parent checkbox clicked in selected tags', this);
            const isChecked = e.target.checked;
            // Find the closest section (vendor, brand, product type, or weight)
            const parentSection = newCheckbox.closest('.vendor-section, .brand-section, .product-type-section, .weight-section');
            if (!parentSection) {
                console.warn('No parent section found for parent checkbox in selected tags', this);
                return;
            }
            const checkboxes = parentSection.querySelectorAll('input[type="checkbox"]');
            checkboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
                if (checkbox.classList.contains('tag-checkbox')) {
                    const tag = TagManager.state.tags.find(t => t['Product Name*'] === checkbox.value);
                    if (tag) {
                        if (isChecked) {
                            TagManager.state.selectedTags.add(tag['Product Name*']);
                        } else {
                            TagManager.state.selectedTags.delete(tag['Product Name*']);
                        }
                    }
                }
            });
            TagManager.updateSelectedTags(Array.from(TagManager.state.selectedTags).map(name =>
                TagManager.state.tags.find(t => t['Product Name*'] === name)
            ));
        });
        console.log('Attached parent checkbox listener in selected tags', newCheckbox);
    });

    // Child tag checkboxes
    container.querySelectorAll('input[type="checkbox"].tag-checkbox').forEach(checkbox => {
        const newCheckbox = checkbox.cloneNode(true);
        checkbox.parentNode.replaceChild(newCheckbox, checkbox);

        newCheckbox.addEventListener('change', function() {
            if (this.checked) {
                TagManager.state.selectedTags.add(this.value);
            } else {
                TagManager.state.selectedTags.delete(this.value);
            }
            // Only update selected tags panel
            TagManager.updateSelectedTags(Array.from(TagManager.state.selectedTags).map(name =>
                TagManager.state.tags.find(t => t['Product Name*'] === name)
            ));
        });
    });
}

TagManager.state.selectedTags.clear();
TagManager.debouncedUpdateAvailableTags(TagManager.state.originalTags, TagManager.state.tags);
TagManager.updateSelectedTags([]);

console.log('Original tags:', TagManager.state.originalTags);

// Lineage abbreviation mapping (matching Python version)
const ABBREVIATED_LINEAGE = {
    "SATIVA": "S",
    "INDICA": "I", 
    "HYBRID": "H",
    "HYBRID/SATIVA": "H/S",
    "HYBRID/INDICA": "H/I",
    "CBD": "CBD",
    "CBD_BLEND": "CBD",
    "MIXED": "THC",
    "PARA": "P"
};

// When populating the lineage filter dropdown, use abbreviated lineage names
function populateLineageFilterOptions(options) {
  const lineageFilter = document.getElementById('lineageFilter');
  if (!lineageFilter) return;
  lineageFilter.innerHTML = '';
  const defaultOption = document.createElement('option');
  defaultOption.value = '';
  defaultOption.textContent = 'All Lineages';
  lineageFilter.appendChild(defaultOption);
  options.forEach(opt => {
    const option = document.createElement('option');
    option.value = opt;
    const displayName = ABBREVIATED_LINEAGE[opt] || opt;
    option.textContent = displayName;
    lineageFilter.appendChild(option);
  });
}

function hyphenNoBreakBeforeQuantity(text) {
    // Replace " - 1g" with " -\u00A01g"
    return text.replace(/ - (\d[\w.]*)/g, ' -\u00A0$1');
}

// Only add event listener if the button exists
const addSelectedTagsBtn = document.getElementById('addSelectedTagsBtn');
if (addSelectedTagsBtn) {
    addSelectedTagsBtn.addEventListener('click', function() {
        // Get all checked checkboxes in the available tags container
        const checked = document.querySelectorAll('#availableTags .tag-checkbox:checked');
        const tagsToMove = Array.from(checked).map(cb => cb.value);
        TagManager.moveToSelected(tagsToMove);
    });
}

// Auto check all available tags functionality removed

// Only update if filteredTags is defined
if (typeof filteredTags !== 'undefined' && filteredTags) {
    TagsTable.updateTagsList('availableTags', filteredTags);
}
// Auto check all available tags call removed

// Test function for Select All functionality
window.testSelectAll = function() {
  console.log('Testing Select All functionality...');
  
  // Test Available Select All
  const selectAllAvailable = document.getElementById('selectAllAvailable');
  console.log('Select All Available checkbox:', selectAllAvailable);
  if (selectAllAvailable) {
    console.log('Available checkbox checked state:', selectAllAvailable.checked);
    console.log('Available checkbox visible:', selectAllAvailable.offsetParent !== null);
    console.log('Available checkbox style:', window.getComputedStyle(selectAllAvailable));
    
    // Manually trigger the change event
    selectAllAvailable.checked = !selectAllAvailable.checked;
    selectAllAvailable.dispatchEvent(new Event('change', { bubbles: true }));
    console.log('Manually triggered Available change event');
  } else {
    console.error('Select All Available checkbox not found!');
  }
  
  // Test Selected Select All
  const selectAllSelected = document.getElementById('selectAllSelected');
  console.log('Select All Selected checkbox:', selectAllSelected);
  if (selectAllSelected) {
    console.log('Selected checkbox checked state:', selectAllSelected.checked);
    console.log('Selected checkbox visible:', selectAllSelected.offsetParent !== null);
    console.log('Selected checkbox style:', window.getComputedStyle(selectAllSelected));
    
    // Manually trigger the change event
    selectAllSelected.checked = !selectAllSelected.checked;
    selectAllSelected.dispatchEvent(new Event('change', { bubbles: true }));
    console.log('Manually triggered Selected change event');
  } else {
    console.error('Select All Selected checkbox not found!');
  }
};

async function handleJsonPasteInput(input) {
    let jsonText = input.trim();
    let json;
    
    // If input looks like a URL, fetch the JSON
    if (jsonText.startsWith('http')) {
        try {
            const response = await fetch(jsonText);
            jsonText = await response.text();
        } catch (e) {
            console.error('Failed to fetch JSON from URL.');
            return;
        }
    }
    
    try {
        json = JSON.parse(jsonText);
    } catch (e) {
        console.error('Invalid JSON format. Please paste valid JSON.');
        return;
    }
    
    // Show loading state
    const loadingModal = document.createElement('div');
    loadingModal.className = 'modal fade';
    loadingModal.id = 'jsonLoadingModal';
    loadingModal.innerHTML = `
        <div class="modal-dialog modal-sm">
            <div class="modal-content">
                <div class="modal-body text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Processing JSON data...</p>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(loadingModal);
    
    const loadingInstance = new bootstrap.Modal(loadingModal);
    loadingInstance.show();
    
    try {
        // Send JSON data to backend for matching
        const response = await fetch('/api/json-match', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: jsonText.startsWith('http') ? jsonText : null, json_data: json })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const matchResult = await response.json();
        
        if (matchResult.success) {
            console.log('JSON matching successful:', {
                matchedCount: matchResult.matched_count,
                availableTagsCount: matchResult.available_tags ? matchResult.available_tags.length : 0,
                selectedTagsCount: matchResult.selected_tags ? matchResult.selected_tags.length : 0,
                jsonMatchedTagsCount: matchResult.json_matched_tags ? matchResult.json_matched_tags.length : 0
            });
            
            // Use the selected tags from the JSON match response
            if (matchResult.selected_tags && matchResult.selected_tags.length > 0) {
                console.log('Using selected tags from JSON match response:', matchResult.selected_tags);
                TagManager.updateSelectedTags(matchResult.selected_tags);
            } else {
                console.log('No selected tags in response, clearing selected tags');
                TagManager.state.persistentSelectedTags = [];
                TagManager.state.selectedTags = new Set();
                
                // Clear the selected tags display
                const selectedTagsContainer = document.getElementById('selectedTags');
                if (selectedTagsContainer) {
                    selectedTagsContainer.innerHTML = '';
                }
            }
            
            // Only update available tags if they are provided and different from selected tags
            if (matchResult.available_tags && matchResult.available_tags.length > 0 && 
                matchResult.available_tags !== matchResult.selected_tags) {
                console.log('Updating available tags with new data');
                TagManager._updateAvailableTags(matchResult.available_tags, null);
            } else {
                console.log('Skipping available tags update to avoid duplication');
            }
            
            // Show a notification to the user
            const notificationDiv = document.createElement('div');
            notificationDiv.className = 'alert alert-success alert-dismissible fade show';
            notificationDiv.innerHTML = `
                <strong>JSON Matching Complete!</strong> 
                ${matchResult.matched_count} products were matched and automatically selected for label generation. 
                You can review and modify the selected items as needed.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            // Insert notification at the top of the main content area
            const mainContent = document.querySelector('.container-fluid') || document.querySelector('.container');
            if (mainContent) {
                mainContent.insertBefore(notificationDiv, mainContent.firstChild);
            }
            
            // Auto-dismiss notification after 10 seconds
            setTimeout(() => {
                if (notificationDiv.parentNode) {
                    notificationDiv.remove();
                }
            }, 10000);
            
            // Show the JSON filter toggle button
            if (typeof updateJsonFilterToggleVisibility === 'function') {
                updateJsonFilterToggleVisibility();
            }
            
            // Force update the toggle button visibility after a short delay to ensure backend state is updated
            setTimeout(() => {
                if (typeof updateJsonFilterToggleVisibility === 'function') {
                    updateJsonFilterToggleVisibility();
                }
            }, 1000);
            
            console.log('JSON match response received successfully');
            
        } else {
            throw new Error(matchResult.error || 'JSON matching failed');
        }
        
    } catch (error) {
        console.error('JSON matching error:', error);
        
        // Show error notification
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.innerHTML = `
            <strong>JSON Matching Failed!</strong> 
            ${error.message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert error notification at the top of the main content area
        const mainContent = document.querySelector('.container-fluid') || document.querySelector('.container');
        if (mainContent) {
            mainContent.insertBefore(errorDiv, mainContent.firstChild);
        }
        
    } finally {
        // Hide loading modal
        if (loadingInstance) {
            loadingInstance.hide();
        }
        if (loadingModal && loadingModal.parentNode) {
            loadingModal.parentNode.removeChild(loadingModal);
        }
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Show splash screen immediately
    AppLoadingSplash.show();
    
    // Initialize TagManager (which will handle the splash loading)
    TagManager.init();
    
    // Ensure proper scrolling behavior
    TagManager.ensureProperScrolling();
    
    // Initialize sticky filter bar behavior
    initializeStickyFilterBar();

    // Add event listener for the clear button
    const clearButton = document.getElementById('clear-filters-btn');
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            if (window.TagManager && TagManager.clearSelected) {
                TagManager.clearSelected();
            }
        });
        console.log('Clear button event listener attached');
    } else {
        console.error('Clear button not found');
    }

    // Add Esc key event listener for clear filters shortcut
    document.addEventListener('keydown', function(event) {
        // Check if Esc key is pressed and no modal is open
        if (event.key === 'Escape' || event.keyCode === 27) {
            // Check if any modal is currently open
            const openModals = document.querySelectorAll('.modal.show, .modal[style*="display: flex"], .modal[style*="display: block"]');
            const isModalOpen = openModals.length > 0;
            
            // Only clear filters if no modal is open
            if (!isModalOpen) {
                console.log('Esc key pressed - clearing filters');
                if (window.TagManager && TagManager.clearAllFilters) {
                    TagManager.clearAllFilters();
                } else if (window.TagManager && TagManager.clearSelected) {
                    TagManager.clearSelected();
                }
                event.preventDefault(); // Prevent default Esc behavior
            }
        }
    });
    console.log('Esc key shortcut for clear filters attached');

    // Add event listener for the undo button with retry mechanism
    function attachUndoButtonListener() {
        const undoButton = document.getElementById('undo-move-btn');
        if (undoButton) {
            // Remove any existing listeners to prevent duplicates
            const newButton = undoButton.cloneNode(true);
            undoButton.parentNode.replaceChild(newButton, undoButton);
            
            newButton.addEventListener('click', function() {
                console.log('Undo button clicked');
                if (window.TagManager && TagManager.undoMove) {
                    console.log('Calling TagManager.undoMove()');
                    TagManager.undoMove();
                } else {
                    console.error('TagManager or undoMove method not available');
                    // Fallback: try to call the undo function directly
                    if (typeof undoMove === 'function') {
                        console.log('Calling undoMove() directly');
                        undoMove();
                    } else {
                        console.error('No undo function available');
                        alert('Undo functionality is not available. Please try refreshing the page.');
                    }
                }
            });
            console.log('Undo button event listener attached successfully');
            return true;
        } else {
            console.error('Undo button not found in DOM');
            return false;
        }
    }
    
    // Try to attach the listener immediately
    if (!attachUndoButtonListener()) {
        // If not found, retry after a short delay
        setTimeout(() => {
            if (!attachUndoButtonListener()) {
                console.warn('Undo button still not found after retry');
            }
        }, 1000);
    }

    // Note: Select All event listeners are now handled in the TagManager._updateAvailableTags and updateSelectedTags methods
    // to ensure proper state management and prevent duplicate listeners
    
    // Fallback: ensure splash screen completes even if there are issues
    setTimeout(() => {
        if (AppLoadingSplash.isVisible) {
            console.log('Fallback: completing splash screen after timeout');
            AppLoadingSplash.stopAutoAdvance();
            AppLoadingSplash.complete();
        }
    }, 10000); // 10 second fallback
});

// Global functions for debugging
window.AppLoadingSplash = AppLoadingSplash;
window.emergencyHideSplash = () => AppLoadingSplash.emergencyHide();

// Global undo function as fallback
window.undoMove = async function() {
    console.log('Global undoMove function called');
    if (window.TagManager && TagManager.undoMove) {
        return TagManager.undoMove();
    } else {
        console.error('TagManager not available for undo');
        alert('Undo functionality is not available. Please try refreshing the page.');
    }
};

// Debug function to check undo stack status
window.checkUndoStack = async function() {
    try {
        const response = await fetch('/api/undo-move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.status === 400) {
            const errorData = await response.json();
            console.log('Undo stack status:', errorData.error);
            return errorData.error;
        } else {
            console.log('Undo stack has items available');
            return 'Has undo items';
        }
    } catch (error) {
        console.error('Error checking undo stack:', error);
        return 'Error checking undo stack';
    }
};

// Test function to manually trigger a move and then check undo
window.testUndoFunctionality = async function() {
    console.log('Testing undo functionality...');
    
    // First, check if there are any tags to move
    const availableCheckboxes = document.querySelectorAll('#availableTags input[type="checkbox"].tag-checkbox');
    if (availableCheckboxes.length === 0) {
        console.log('No available tags to test with');
        return;
    }
    
    // Check current undo stack
    console.log('Initial undo stack status:', await window.checkUndoStack());
    
    // Move one tag to selected
    const firstCheckbox = availableCheckboxes[0];
    firstCheckbox.checked = true;
    
    console.log('Moving tag:', firstCheckbox.value);
    
    // Trigger move to selected
    if (window.TagManager && TagManager.moveToSelected) {
        console.log('Calling TagManager.moveToSelected()...');
        await TagManager.moveToSelected();
        
        // Wait a moment, then check undo stack
        setTimeout(async () => {
            console.log('After move - undo stack status:', await window.checkUndoStack());
        }, 1000);
    } else {
        console.error('TagManager.moveToSelected not available');
    }
};

// Test function to check if move buttons are working
window.testMoveButtons = function() {
    console.log('Testing move buttons...');
    
    // Check if move buttons exist
    const moveToSelectedBtn = document.querySelector('button[onclick*="moveToSelected"]') || 
                              document.querySelector('button[title*="Move to Selected"]') ||
                              document.querySelector('button:contains(">")');
    
    const moveToAvailableBtn = document.querySelector('button[onclick*="moveToAvailable"]') || 
                               document.querySelector('button[title*="Move to Available"]') ||
                               document.querySelector('button:contains("<")');
    
    console.log('Move to Selected button found:', !!moveToSelectedBtn);
    console.log('Move to Available button found:', !!moveToAvailableBtn);
    
    // Check if TagManager is available
    console.log('TagManager available:', !!window.TagManager);
    console.log('TagManager.moveToSelected available:', !!(window.TagManager && window.TagManager.moveToSelected));
    console.log('TagManager.moveToAvailable available:', !!(window.TagManager && window.TagManager.moveToAvailable));
    
    // Check for available tags
    const availableCheckboxes = document.querySelectorAll('#availableTags input[type="checkbox"].tag-checkbox');
    console.log('Available checkboxes found:', availableCheckboxes.length);
    
    return {
        moveToSelectedBtn: !!moveToSelectedBtn,
        moveToAvailableBtn: !!moveToAvailableBtn,
        tagManager: !!window.TagManager,
        availableTags: availableCheckboxes.length
    };
};

// Function to clear stuck uploads
async function clearStuckUploads() {
    try {
        console.log('Clearing stuck uploads...');
        const response = await fetch('/api/clear-upload-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('Upload status cleared:', result.message);
            
            // Show a toast notification
            if (window.Toast) {
                Toast.show('success', result.message);
            } else {
                alert(result.message);
            }
            
            // Refresh the page to reset the UI state
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            console.error('Failed to clear upload status:', response.statusText);
            alert('Failed to clear stuck uploads. Please try again.');
        }
    } catch (error) {
        console.error('Error clearing stuck uploads:', error);
        alert('Error clearing stuck uploads. Please try again.');
    }
}

// Initialize sticky filter bar behavior
function initializeStickyFilterBar() {
    const stickyFilterBar = document.querySelector('.sticky-filter-bar');
    const tagList = document.getElementById('availableTags');
    
    if (stickyFilterBar && tagList) {
        // Add scroll event listener to the tag list
        tagList.addEventListener('scroll', function() {
            const rect = stickyFilterBar.getBoundingClientRect();
            const cardHeader = document.querySelector('.card-header');
            
            if (cardHeader) {
                const headerRect = cardHeader.getBoundingClientRect();
                
                // Check if the filter bar should be sticky
                if (headerRect.bottom <= 0) {
                    stickyFilterBar.classList.add('is-sticky');
                } else {
                    stickyFilterBar.classList.remove('is-sticky');
                }
            }
        });
        
        // Also listen for window scroll for better cross-browser compatibility
        window.addEventListener('scroll', function() {
            const rect = stickyFilterBar.getBoundingClientRect();
            const cardHeader = document.querySelector('.card-header');
            
            if (cardHeader) {
                const headerRect = cardHeader.getBoundingClientRect();
                
                if (headerRect.bottom <= 0) {
                    stickyFilterBar.classList.add('is-sticky');
                } else {
                    stickyFilterBar.classList.remove('is-sticky');
                }
            }
        });
    }
}

function clearUIState() {
    // Clear selected tags
    if (window.TagManager && TagManager.clearSelected) TagManager.clearSelected();
    // Clear search fields
    document.querySelectorAll('input[type="text"]').forEach(el => el.value = '');
    // Reset filters
    document.querySelectorAll('select').forEach(el => el.selectedIndex = 0);
    // Clear checkboxes
    document.querySelectorAll('input[type="checkbox"]').forEach(el => el.checked = false);
    // Clear localStorage/sessionStorage
    if (window.localStorage) localStorage.clear();
    if (window.sessionStorage) sessionStorage.clear();
}

// Call clearUIState after export or upload success
// Example: after successful AJAX response for export/upload
// clearUIState();

// Removed conflicting file info text initialization - now handled by checkForExistingData()

// Global function to clear stuck upload UI (can be called from browser console)
window.clearStuckUploadUI = function() {
    if (typeof TagManager !== 'undefined' && TagManager.forceClearUploadUI) {
        TagManager.forceClearUploadUI();
        console.log('Stuck upload UI cleared via global function');
    } else {
        console.error('TagManager not available');
    }
};

// Global function to check upload status
window.checkUploadStatus = function(filename) {
    fetch(`/api/upload-status?filename=${encodeURIComponent(filename)}`)
        .then(response => response.json())
        .then(data => {
            console.log('Upload status:', data);
        })
        .catch(error => {
            console.error('Error checking upload status:', error);
        });
};

// Event listeners for drag-and-drop reordering
document.addEventListener('selectedTagsReordered', function(event) {
    console.log('selectedTagsReordered event received:', event.detail);
    // This event is triggered when tags are reordered via drag-and-drop
    // The UI refresh is handled by the drag-and-drop manager
});

document.addEventListener('forceRefreshSelectedTags', function(event) {
    console.log('forceRefreshSelectedTags event received');
    // Force refresh the selected tags display
    if (window.TagManager && window.TagManager.fetchAndUpdateSelectedTags) {
        console.log('Forcing refresh of selected tags...');
        window.TagManager.fetchAndUpdateSelectedTags();
    }
});

// JSON Matching Function - Global function for JSON product matching
window.performJsonMatch = function() {
    const jsonUrlInput = document.getElementById('jsonUrlInput');
    const matchBtn = document.querySelector('#jsonMatchModal .btn-modern2');
    const resultsDiv = document.getElementById('jsonMatchResults');
    const matchCount = document.getElementById('matchCount');
    const matchedProductsList = document.getElementById('matchedProductsList');
    
    if (!jsonUrlInput || !matchBtn) {
        console.error('JSON match modal elements not found');
        return;
    }
    
    let jsonUrl = jsonUrlInput.value.trim();
    if (!jsonUrl) {
        console.error('Please enter a JSON URL first.');
        return;
    }

    // Validate URL format - support both HTTP URLs and data URLs
    // Also auto-prepend https:// if no protocol is specified
    if (!jsonUrl.startsWith('http://') && !jsonUrl.startsWith('https://') && !jsonUrl.startsWith('data:')) {
        // Auto-prepend https:// for URLs without protocol
        jsonUrl = 'https://' + jsonUrl;
        console.log('Auto-prepending https:// to URL:', jsonUrl);
    }
    
    // Final validation
    if (!/^(https?:\/\/|data:)/i.test(jsonUrl)) {
        console.error('Please enter a valid URL starting with http://, https://, or data:');
        return;
    }

    // Show loading state
    matchBtn.disabled = true;
    matchBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
    
    // Show progress message
    resultsDiv.classList.remove('d-none');
    matchCount.textContent = 'Processing...';
    matchedProductsList.innerHTML = '<div class="text-info">Matching products from JSON URL. This may take up to 2 minutes for large datasets. Progress will be logged in the browser console.</div>';

    // Add timeout to prevent hanging
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 minutes timeout
    
    // Use the json-match endpoint
    fetch('/api/json-match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: String(jsonUrl) }),
        signal: controller.signal
    })
    .then(response => {
        if (!response.ok) {
            // Clone the response so we can read it multiple times if needed
            const responseClone = response.clone();
            return response.json().then(error => {
                // Handle both string and object error responses
                const errorMessage = typeof error === 'string' ? error : (error.error || 'JSON matching failed');
                throw new Error(errorMessage);
            }).catch(jsonError => {
                // If JSON parsing fails, try to get text response from the cloned response
                return responseClone.text().then(text => {
                    throw new Error(`Server error: ${text || 'Unknown error'}`);
                });
            });
        }
        return response.json().catch(jsonError => {
            console.error('JSON parsing error:', jsonError);
            console.error('Response status:', response.status);
            console.error('Response headers:', response.headers);
            
            // Clone the response before reading it to avoid "body stream already read" error
            const responseClone = response.clone();
            return responseClone.text().then(text => {
                console.error('Response text:', text);
                throw new Error(`Invalid JSON response from server: ${jsonError.message}. Response: ${text.substring(0, 200)}...`);
            }).catch(textError => {
                console.error('Error reading response text:', textError);
                throw new Error(`Invalid JSON response from server: ${jsonError.message}. Unable to read response text.`);
            });
        });
    })
    .then(matchResult => {
        // Safety check: ensure matchResult is an object
        if (typeof matchResult !== 'object' || matchResult === null) {
            console.error('Invalid matchResult:', matchResult);
            throw new Error('Invalid response format from server');
        }
        
        // Show results
        matchCount.textContent = matchResult.matched_count || 0;
        
        // Populate matched products list with note about where they were added
        if (matchResult.matched_names && matchResult.matched_names.length > 0) {
            matchedProductsList.innerHTML = `
                <div class="alert alert-success mb-3">
                    <strong>Success!</strong> ${matchResult.matched_count} products were matched and added to the <strong>Available Tags</strong> list.
                    <br>Please review the available tags and select the items you need.
                </div>
                <div class="mb-2"><strong>Matched Products:</strong></div>
                ${matchResult.matched_names
                    .map(product => `<div class="mb-1">• ${product}</div>`)
                    .join('')}
            `;
        } else {
            matchedProductsList.innerHTML = '<div class="text-muted">No specific product details available</div>';
        }
        
        resultsDiv.classList.remove('d-none');
        
        // Successfully matched products from JSON URL
        
        // Clear the input
        jsonUrlInput.value = '';
        
        // Refresh the UI with new data
        if (typeof TagManager !== 'undefined') {
            console.log('JSON matched products added to available tags for manual selection');
            console.log('Matched names:', matchResult.matched_names);
            console.log('JSON matched tags:', matchResult.json_matched_tags);
            
            // Update available tags with the new JSON matched items
            console.log('Updating available tags with JSON matched data:', {
                availableTagsCount: matchResult.available_tags ? matchResult.available_tags.length : 0,
                matchedCount: matchResult.matched_count,
                sampleTags: matchResult.available_tags ? matchResult.available_tags.slice(0, 3).map(t => t['Product Name*']) : []
            });
            
            // For JSON matching, we want to show JSON matched items by default
            // The backend sends all JSON matched items in available_tags
            console.log('JSON match response analysis:');
            console.log('- matched_count:', matchResult.matched_count);
            console.log('- available_tags length:', matchResult.available_tags ? matchResult.available_tags.length : 0);
            console.log('- json_matched_tags length:', matchResult.json_matched_tags ? matchResult.json_matched_tags.length : 0);
            
            // Use available_tags as the primary source (backend sets this to JSON matched items)
            let tagsToShow = matchResult.available_tags || [];
            
            // Fallback to json_matched_tags if available_tags is empty
            if (!tagsToShow || tagsToShow.length === 0) {
                console.log('available_tags is empty, falling back to json_matched_tags');
                tagsToShow = matchResult.json_matched_tags || [];
            }
            
            // Fallback to existing tags if both are empty
            if (!tagsToShow || tagsToShow.length === 0) {
                console.log('No JSON matched items found, showing existing tags');
                tagsToShow = TagManager.state.originalTags || [];
            }
            
            console.log(`Showing ${tagsToShow.length} items in available tags`);
            TagManager._updateAvailableTags(tagsToShow, null);
            
            // For JSON matching, we want to show all matched tags in available tags
            // Clear current selected tags first to ensure all JSON matched tags are visible
            TagManager.state.persistentSelectedTags = [];
            TagManager.state.selectedTags = new Set();
            
            // Clear the selected tags display
            const selectedTagsContainer = document.getElementById('selectedTags');
            if (selectedTagsContainer) {
                selectedTagsContainer.innerHTML = '';
            }
            
            // CRITICAL FIX: For JSON matched sessions, don't filter out selected tags
            // This ensures all 14 tags remain visible in the available list
            TagManager.state.isJsonMatchedSession = true;
            
            // CRITICAL FIX: Automatically select ALL JSON matched tags
            // This ensures all 14 tags are selected for generation
            if (tagsToShow && tagsToShow.length > 0) {
                // Select all available tags
                TagManager.state.persistentSelectedTags = tagsToShow.map(tag => tag['Product Name*'] || tag.ProductName || tag.Description || '');
                TagManager.state.selectedTags = new Set(TagManager.state.persistentSelectedTags);
                
                // Update the UI to reflect the selection
                TagManager.updateSelectedTags(tagsToShow);
                
                console.log(`✅ Auto-selected all ${TagManager.state.persistentSelectedTags.length} JSON matched tags`);
            }
            
            // Show a notification to the user
            const notificationDiv = document.createElement('div');
            notificationDiv.className = 'alert alert-success alert-dismissible fade show';
            notificationDiv.innerHTML = `
                <strong>JSON Matching Complete!</strong> 
                ${matchResult.matched_count} products were matched and are now available in the Available Tags list. 
                <strong>All ${matchResult.matched_count} tags have been automatically selected for you!</strong>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            // Insert the notification at the top of the page
            const container = document.querySelector('.container-fluid') || document.querySelector('.container');
            if (container) {
                container.insertBefore(notificationDiv, container.firstChild);
                
                // Auto-dismiss after 10 seconds
                setTimeout(() => {
                    if (notificationDiv.parentNode) {
                        notificationDiv.remove();
                    }
                }, 10000);
            }
            
            // Show the JSON filter toggle button
            if (typeof updateJsonFilterToggleVisibility === 'function') {
                updateJsonFilterToggleVisibility();
            }
            
            // Force update the toggle button visibility after a short delay to ensure backend state is updated
            setTimeout(() => {
                if (typeof updateJsonFilterToggleVisibility === 'function') {
                    updateJsonFilterToggleVisibility();
                }
            }, 1000);
        }
        
        console.log('Available tags updated with JSON matched items');
    })
    .catch(error => {
        console.error('JSON matching error:', error);
        
        // Show error message to user
        matchCount.textContent = 'Error';
        matchedProductsList.innerHTML = `
            <div class="alert alert-danger">
                <strong>Error:</strong> ${error.message}
            </div>
        `;
        resultsDiv.classList.remove('d-none');
    })
    .finally(() => {
        // Reset button state
        matchBtn.disabled = false;
        matchBtn.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="me-2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            Match Products
        `;
        
        // Clear timeout
        clearTimeout(timeoutId);
    });
};

// Accessibility fix for JSON Match Modal
document.addEventListener('DOMContentLoaded', function() {
    const jsonMatchModal = document.getElementById('jsonMatchModal');
    if (jsonMatchModal) {
        // Store the element that had focus before the modal opened
        let previouslyFocusedElement = null;
        
        // Handle modal show event
        jsonMatchModal.addEventListener('show.bs.modal', function() {
            // Store the currently focused element
            previouslyFocusedElement = document.activeElement;
            
            // Ensure modal is properly accessible
            jsonMatchModal.removeAttribute('aria-hidden');
            jsonMatchModal.removeAttribute('inert');
            jsonMatchModal.setAttribute('aria-modal', 'true');
        });
        
        // Handle modal shown event
        jsonMatchModal.addEventListener('shown.bs.modal', function() {
            // Focus the first focusable element in the modal
            const firstFocusable = jsonMatchModal.querySelector('input, button, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (firstFocusable) {
                firstFocusable.focus();
            }
        });
        
        // Handle modal hide event
        jsonMatchModal.addEventListener('hide.bs.modal', function() {
            // Move focus away from any focused element inside the modal
            const focusedElement = jsonMatchModal.querySelector(':focus');
            if (focusedElement) {
                focusedElement.blur();
            }
        });
        
        // Handle modal hidden event
        jsonMatchModal.addEventListener('hidden.bs.modal', function() {
            // Set aria-hidden and inert after modal is fully hidden
            jsonMatchModal.setAttribute('aria-hidden', 'true');
            jsonMatchModal.setAttribute('inert', '');
            jsonMatchModal.removeAttribute('aria-modal');
            
            // Restore focus to the previously focused element
            if (previouslyFocusedElement && previouslyFocusedElement.focus) {
                // Use setTimeout to ensure the modal is fully hidden before restoring focus
                setTimeout(() => {
                    try {
                        previouslyFocusedElement.focus();
                    } catch (e) {
                        // If the previously focused element is no longer available, focus the body
                        document.body.focus();
                    }
                }, 100);
            }
        });
        
        // Handle close button clicks to ensure proper focus management
        const closeButtons = jsonMatchModal.querySelectorAll('[data-bs-dismiss="modal"]');
        closeButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Move focus away from the button before the modal starts hiding
                setTimeout(() => {
                    this.blur();
                }, 0);
            });
        });
    }
    
    // Also fix the JSON Inventory Modal
    const jsonInventoryModal = document.getElementById('jsonInventoryModal');
    if (jsonInventoryModal) {
        // Store the element that had focus before the modal opened
        let previouslyFocusedElement = null;
        
        // Handle modal show event
        jsonInventoryModal.addEventListener('show.bs.modal', function() {
            // Store the currently focused element
            previouslyFocusedElement = document.activeElement;
            
            // Ensure modal is properly accessible
            jsonInventoryModal.removeAttribute('aria-hidden');
            jsonInventoryModal.removeAttribute('inert');
            jsonInventoryModal.setAttribute('aria-modal', 'true');
        });
        
        // Handle modal shown event
        jsonInventoryModal.addEventListener('shown.bs.modal', function() {
            // Focus the first focusable element in the modal
            const firstFocusable = jsonInventoryModal.querySelector('input, button, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (firstFocusable) {
                firstFocusable.focus();
            }
        });
        
        // Handle modal hide event
        jsonInventoryModal.addEventListener('hide.bs.modal', function() {
            // Move focus away from any focused element inside the modal
            const focusedElement = jsonInventoryModal.querySelector(':focus');
            if (focusedElement) {
                focusedElement.blur();
            }
        });
        
        // Handle modal hidden event
        jsonInventoryModal.addEventListener('hidden.bs.modal', function() {
            // Set aria-hidden and inert after modal is fully hidden
            jsonInventoryModal.setAttribute('aria-hidden', 'true');
            jsonInventoryModal.setAttribute('inert', '');
            jsonInventoryModal.removeAttribute('aria-modal');
            
            // Restore focus to the previously focused element
            if (previouslyFocusedElement && previouslyFocusedElement.focus) {
                // Use setTimeout to ensure the modal is fully hidden before restoring focus
                setTimeout(() => {
                    try {
                        previouslyFocusedElement.focus();
                    } catch (e) {
                        // If the previously focused element is no longer available, focus the body
                        document.body.focus();
                    }
                }, 100);
            }
        });
        
        // Handle close button clicks to ensure proper focus management
        const closeButtons = jsonInventoryModal.querySelectorAll('[data-bs-dismiss="modal"]');
        closeButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Move focus away from the button before the modal starts hiding
                setTimeout(() => {
                    this.blur();
                }, 0);
            });
        });
    }
});

// JSON Filter Toggle Function
window.toggleJsonFilter = function() {
    const toggleBtn = document.getElementById('jsonFilterToggleBtn');
    const toggleText = document.getElementById('jsonFilterToggleText');
    
    if (!toggleBtn) {
        console.error('JSON filter toggle button not found');
        return;
    }
    
    // Show loading state
    toggleBtn.disabled = true;
    const originalText = toggleText.textContent;
    toggleText.textContent = 'Toggling...';
    
    // Call the toggle API
    fetch('/api/toggle-json-filter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filter_mode: 'toggle' })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            console.log('JSON filter toggled successfully:', data);
            console.log('Available tags count:', data.available_tags ? data.available_tags.length : 0);
            
            // Update the available tags with the new filtered data
            if (typeof TagManager !== 'undefined' && data.available_tags) {
                console.log('Updating TagManager with new tags...');
                
                // Update the TagManager state with the new tags
                TagManager.state.originalTags = [...data.available_tags];
                TagManager.state.tags = [...data.available_tags];
                
                console.log('TagManager state updated. Original tags:', TagManager.state.originalTags.length);
                console.log('TagManager state updated. Current tags:', TagManager.state.tags.length);
                
                // Use requestAnimationFrame to ensure DOM is ready before updating
                requestAnimationFrame(() => {
                    // Call the update function to refresh the display
                    TagManager._updateAvailableTags(data.available_tags, null);
                    
                    // Update tag counts
                    TagManager.updateTagCount('available', data.available_tags.length);
                    
                    console.log('TagManager display updated successfully');
                });
            } else {
                console.warn('TagManager not available or no available_tags in response');
            }
            
            // Update the toggle button text
            toggleText.textContent = data.mode_name || 'Toggle Filter';
            
            // Update the filter button visibility
            if (typeof updateJsonFilterToggleVisibility === 'function') {
                updateJsonFilterToggleVisibility();
            }
            
            // Show notification
            const notificationDiv = document.createElement('div');
            notificationDiv.className = 'alert alert-info alert-dismissible fade show';
            notificationDiv.innerHTML = `
                <strong>Filter Updated!</strong> 
                Now showing ${data.available_count} items in ${data.mode_name}.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            // Insert notification at the top of the main content area
            const mainContent = document.querySelector('.container-fluid') || document.querySelector('.container');
            if (mainContent) {
                mainContent.insertBefore(notificationDiv, mainContent.firstChild);
            }
            
            // Auto-dismiss notification after 5 seconds
            setTimeout(() => {
                if (notificationDiv.parentNode) {
                    notificationDiv.remove();
                }
            }, 5000);
            
        } else {
            throw new Error(data.error || 'Toggle failed');
        }
    })
    .catch(error => {
        console.error('JSON filter toggle error:', error);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack,
            name: error.name
        });
        
        // Show error notification
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.innerHTML = `
            <strong>Filter Toggle Error!</strong> 
            ${error.message || 'An unknown error occurred while toggling the filter.'}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert error notification at the top of the main content area
        const mainContent = document.querySelector('.container-fluid') || document.querySelector('.container');
        if (mainContent) {
            mainContent.insertBefore(errorDiv, mainContent.firstChild);
        }
        
        // Reset button text
        toggleText.textContent = originalText;
        
        // Auto-dismiss error notification after 8 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 8000);
    })
    .finally(() => {
        // Reset button state
        toggleBtn.disabled = false;
    });
};

// Function to show/hide JSON filter toggle button based on filter status
window.updateJsonFilterToggleVisibility = function() {
    fetch('/api/get-filter-status')
        .then(response => response.json())
        .then(data => {
            const toggleBtn = document.getElementById('jsonFilterToggleBtn');
            const toggleText = document.getElementById('jsonFilterToggleText');
            
            if (toggleBtn && toggleText) {
                if (data.can_toggle) {
                    toggleBtn.style.display = 'block';
                    toggleText.textContent = data.current_mode === 'json_matched' ? 'Show Full List' : 'Show JSON Matched';
                } else {
                    toggleBtn.style.display = 'none';
                }
            }
        })
        .catch(error => {
            console.error('Error checking filter status:', error);
        });
};

// Global error handler to prevent page from exiting
window.addEventListener('error', function(e) {
    console.error('Global error caught:', e.error);
    // Prevent the error from causing the page to exit
    e.preventDefault();
    return false;
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    // Prevent the error from causing the page to exit
    e.preventDefault();
});

// TagManager is already initialized in the main DOMContentLoaded event listener above
// This duplicate initialization has been removed to prevent conflicts

// Add click event listener to title header for page reload
document.addEventListener('DOMContentLoaded', function() {
    const titleElement = document.querySelector('.vibrant-title');
    if (titleElement) {
        titleElement.style.cursor = 'pointer';
        titleElement.title = 'Click to reload the application';
        
        titleElement.addEventListener('click', function() {
            // Add a subtle visual feedback
            titleElement.style.opacity = '0.7';
            titleElement.style.transform = 'scale(0.98)';
            
            // Reset visual state after a brief moment
            setTimeout(() => {
                titleElement.style.opacity = '1';
                titleElement.style.transform = 'scale(1)';
            }, 150);
            
            // Reload the page after a brief delay for visual feedback
            setTimeout(() => {
                window.location.reload();
            }, 200);
        });
    }
});