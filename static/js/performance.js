/**
 * Performance optimization utilities for the frontend
 */

class PerformanceOptimizer {
    constructor() {
        this.debounceTimers = new Map();
        this.throttleTimers = new Map();
        this.cache = new Map();
        this.maxCacheSize = 100;
        this.uploadProgress = null;
    }

    /**
     * Debounce function calls to prevent excessive API requests
     */
    debounce(func, delay, key = 'default') {
        return (...args) => {
            if (this.debounceTimers.has(key)) {
                clearTimeout(this.debounceTimers.get(key));
            }
            
            const timer = setTimeout(() => {
                func.apply(this, args);
                this.debounceTimers.delete(key);
            }, delay);
            
            this.debounceTimers.set(key, timer);
        };
    }

    /**
     * Throttle function calls to limit frequency
     */
    throttle(func, delay, key = 'default') {
        return (...args) => {
            if (this.throttleTimers.has(key)) {
                return;
            }
            
            func.apply(this, args);
            
            const timer = setTimeout(() => {
                this.throttleTimers.delete(key);
            }, delay);
            
            this.throttleTimers.set(key, timer);
        };
    }

    /**
     * Cache API responses to reduce server load
     */
    async cachedFetch(url, options = {}, ttl = 300000) { // 5 minutes default TTL
        const cacheKey = `${url}_${JSON.stringify(options)}`;
        const cached = this.cache.get(cacheKey);
        
        if (cached && Date.now() - cached.timestamp < ttl) {
            return cached.data;
        }
        
        try {
            const response = await fetch(url, options);
            const data = await response.json();
            
            // Store in cache
            this.cache.set(cacheKey, {
                data: data,
                timestamp: Date.now()
            });
            
            // Clean up old cache entries
            this.cleanupCache();
            
            return data;
        } catch (error) {
            console.error('Cached fetch error:', error);
            throw error;
        }
    }

    /**
     * Clean up old cache entries
     */
    cleanupCache() {
        if (this.cache.size > this.maxCacheSize) {
            const entries = Array.from(this.cache.entries());
            entries.sort((a, b) => a[1].timestamp - b[1].timestamp);
            
            // Remove oldest 25% of entries
            const toRemove = Math.floor(entries.length * 0.25);
            for (let i = 0; i < toRemove; i++) {
                this.cache.delete(entries[i][0]);
            }
        }
    }

    /**
     * Optimized file upload with progress tracking
     */
    async uploadFile(file, endpoint = '/upload-optimized', onProgress = null) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);
            
            const xhr = new XMLHttpRequest();
            
            // Track upload progress
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && onProgress) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    onProgress(percentComplete);
                }
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (error) {
                        reject(new Error('Invalid response format'));
                    }
                } else {
                    try {
                        const error = JSON.parse(xhr.responseText);
                        reject(new Error(error.error || 'Upload failed'));
                    } catch (e) {
                        reject(new Error(`Upload failed with status ${xhr.status}`));
                    }
                }
            });
            
            xhr.addEventListener('error', () => {
                reject(new Error('Network error during upload'));
            });
            
            xhr.addEventListener('timeout', () => {
                reject(new Error('Upload timeout'));
            });
            
            xhr.timeout = 300000; // 5 minutes
            xhr.open('POST', endpoint);
            xhr.send(formData);
        });
    }

    /**
     * Show loading state with smooth transitions
     */
    showLoading(element, message = 'Loading...') {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element) {
            element.style.opacity = '0.6';
            element.style.pointerEvents = 'none';
            
            // Add loading spinner
            const spinner = document.createElement('div');
            spinner.className = 'loading-spinner';
            spinner.innerHTML = `
                <div class="spinner"></div>
                <div class="loading-text">${message}</div>
            `;
            spinner.style.cssText = `
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
                z-index: 1000;
            `;
            
            element.style.position = 'relative';
            element.appendChild(spinner);
        }
    }

    /**
     * Hide loading state
     */
    hideLoading(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element) {
            element.style.opacity = '1';
            element.style.pointerEvents = 'auto';
            
            const spinner = element.querySelector('.loading-spinner');
            if (spinner) {
                spinner.remove();
            }
        }
    }

    /**
     * Optimize form validation with debouncing
     */
    setupFormValidation(formSelector, validationRules) {
        const form = document.querySelector(formSelector);
        if (!form) return;

        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            const validateField = this.debounce((field) => {
                this.validateField(field, validationRules);
            }, 300, `validate_${input.name}`);
            
            input.addEventListener('input', () => validateField(input));
            input.addEventListener('blur', () => validateField(input));
        });
    }

    /**
     * Validate individual form field
     */
    validateField(field, rules) {
        const value = field.value.trim();
        const fieldRules = rules[field.name] || {};
        let isValid = true;
        let errorMessage = '';

        // Required validation
        if (fieldRules.required && !value) {
            isValid = false;
            errorMessage = fieldRules.requiredMessage || 'This field is required';
        }

        // Pattern validation
        if (isValid && value && fieldRules.pattern) {
            const regex = new RegExp(fieldRules.pattern);
            if (!regex.test(value)) {
                isValid = false;
                errorMessage = fieldRules.patternMessage || 'Invalid format';
            }
        }

        // Length validation
        if (isValid && value && fieldRules.minLength && value.length < fieldRules.minLength) {
            isValid = false;
            errorMessage = fieldRules.minLengthMessage || `Minimum ${fieldRules.minLength} characters required`;
        }

        if (isValid && value && fieldRules.maxLength && value.length > fieldRules.maxLength) {
            isValid = false;
            errorMessage = fieldRules.maxLengthMessage || `Maximum ${fieldRules.maxLength} characters allowed`;
        }

        // Update UI
        this.updateFieldValidation(field, isValid, errorMessage);
        
        return isValid;
    }

    /**
     * Update field validation UI
     */
    updateFieldValidation(field, isValid, errorMessage) {
        // Remove existing validation classes
        field.classList.remove('is-valid', 'is-invalid');
        
        // Remove existing error message
        const existingError = field.parentNode.querySelector('.invalid-feedback');
        if (existingError) {
            existingError.remove();
        }

        if (isValid) {
            field.classList.add('is-valid');
        } else {
            field.classList.add('is-invalid');
            
            // Add error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.textContent = errorMessage;
            field.parentNode.appendChild(errorDiv);
        }
    }

    /**
     * Get performance metrics
     */
    async getPerformanceMetrics() {
        try {
            const response = await this.cachedFetch('/api/performance/status');
            return response;
        } catch (error) {
            console.error('Failed to get performance metrics:', error);
            return null;
        }
    }

    /**
     * Clear performance cache
     */
    async clearCache() {
        try {
            const response = await fetch('/api/performance/clear-cache', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            const result = await response.json();
            console.log('Cache cleared:', result);
            return result;
        } catch (error) {
            console.error('Failed to clear cache:', error);
            return null;
        }
    }
}

// Global performance optimizer instance
window.performanceOptimizer = new PerformanceOptimizer();

// Add CSS for loading spinner
const style = document.createElement('style');
style.textContent = `
    .loading-spinner .spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 2s linear infinite;
        margin: 0 auto 10px;
    }
    
    .loading-text {
        color: #666;
        font-size: 14px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .is-valid {
        border-color: #28a745;
    }
    
    .is-invalid {
        border-color: #dc3545;
    }
    
    .invalid-feedback {
        display: block;
        width: 100%;
        margin-top: 0.25rem;
        font-size: 0.875rem;
        color: #dc3545;
    }
`;
document.head.appendChild(style);

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceOptimizer;
}
