/**
 * Unified Font Sizing System
 * Prevents word splitting and automatically adjusts font sizes
 */

class UnifiedFontSizing {
  constructor() {
    this.minFontSize = 8;
    this.maxFontSize = 24;
    this.baseFontSize = 12;
    this.observer = null;
    this.resizeTimeout = null;
    
    this.init();
  }
  
  init() {
    this.setupResizeObserver();
    this.setupEventListeners();
    this.processAllTextElements();
  }
  
  setupResizeObserver() {
    // Observe container size changes
    this.observer = new ResizeObserver((entries) => {
      entries.forEach(entry => {
        this.adjustFontSize(entry.target);
      });
    });
  }
  
  setupEventListeners() {
    // Handle window resize
    window.addEventListener('resize', () => {
      clearTimeout(this.resizeTimeout);
      this.resizeTimeout = setTimeout(() => {
        this.processAllTextElements();
      }, 100);
    });
    
    // Handle content changes
    document.addEventListener('DOMContentLoaded', () => {
      this.processAllTextElements();
    });
    
    // Handle dynamic content updates
    const observer = new MutationObserver(() => {
      this.processAllTextElements();
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['class', 'style']
    });
  }
  
  processAllTextElements() {
    const textElements = document.querySelectorAll(`
      .text-container,
      .tag-name,
      .vendor-name,
      .brand-name,
      .product-name,
      .weight-text,
      .lineage-text,
      .price-text,
      .description-text,
      .label-text,
      .header-text,
      .title-text,
      .subtitle-text,
      .content-text,
      .critical-text,
      .responsive-text,
      .dynamic-font,
      .auto-size-text,
      .container-aware-text
    `);
    
    textElements.forEach(element => {
      this.adjustFontSize(element);
      this.observeElement(element);
    });
  }
  
  observeElement(element) {
    if (this.observer) {
      this.observer.observe(element);
    }
  }
  
  adjustFontSize(element) {
    if (!element || !element.textContent) return;
    
    const container = this.getContainer(element);
    const text = element.textContent.trim();
    
    if (!text || !container) return;
    
    // Get container dimensions
    const containerWidth = container.offsetWidth;
    const containerHeight = container.offsetHeight;
    
    // Calculate optimal font size
    const optimalSize = this.calculateOptimalFontSize(
      text,
      containerWidth,
      containerHeight,
      element
    );
    
    // Apply the font size
    this.applyFontSize(element, optimalSize);
    
    // Ensure no word splitting
    this.preventWordSplitting(element);
  }
  
  calculateOptimalFontSize(text, containerWidth, containerHeight, element) {
    // Start with base font size
    let fontSize = this.baseFontSize;
    
    // Create temporary element to measure text
    const tempElement = element.cloneNode(true);
    tempElement.style.position = 'absolute';
    tempElement.style.visibility = 'hidden';
    tempElement.style.whiteSpace = 'nowrap';
    tempElement.style.fontSize = fontSize + 'px';
    document.body.appendChild(tempElement);
    
    // Binary search for optimal font size
    let minSize = this.minFontSize;
    let maxSize = this.maxFontSize;
    let optimalSize = fontSize;
    
    while (minSize <= maxSize) {
      fontSize = Math.floor((minSize + maxSize) / 2);
      tempElement.style.fontSize = fontSize + 'px';
      
      const textWidth = tempElement.offsetWidth;
      const textHeight = tempElement.offsetHeight;
      
      if (textWidth <= containerWidth && textHeight <= containerHeight) {
        optimalSize = fontSize;
        minSize = fontSize + 1;
      } else {
        maxSize = fontSize - 1;
      }
    }
    
    document.body.removeChild(tempElement);
    
    // Apply template-specific adjustments
    optimalSize = this.applyTemplateAdjustments(element, optimalSize);
    
    return Math.max(this.minFontSize, Math.min(this.maxFontSize, optimalSize));
  }
  
  applyTemplateAdjustments(element, fontSize) {
    const template = this.getTemplateType(element);
    
    switch (template) {
      case 'horizontal':
        return fontSize * 0.85;
      case 'vertical':
        return fontSize * 0.9;
      case 'mini':
        return fontSize * 0.75;
      case 'double':
        return fontSize * 0.8;
      default:
        return fontSize;
    }
  }
  
  getTemplateType(element) {
    const container = this.getContainer(element);
    if (!container) return 'default';
    
    const classes = container.className.toLowerCase();
    
    if (classes.includes('horizontal')) return 'horizontal';
    if (classes.includes('vertical')) return 'vertical';
    if (classes.includes('mini')) return 'mini';
    if (classes.includes('double')) return 'double';
    
    return 'default';
  }
  
  getContainer(element) {
    // Find the nearest container element
    let container = element.closest('.template-container, .tag-item, .vendor-section, .brand-section, .product-type-section, .weight-section, .glass-card, .card-body');
    
    if (!container) {
      container = element.parentElement;
    }
    
    return container;
  }
  
  applyFontSize(element, fontSize) {
    // Set CSS custom property for dynamic font sizing
    element.style.setProperty('--dynamic-font-size', fontSize + 'px');
    
    // Apply the font size directly
    element.style.fontSize = fontSize + 'px';
    
    // Ensure text fits within container
    this.ensureTextFit(element);
  }
  
  ensureTextFit(element) {
    const container = this.getContainer(element);
    if (!container) return;
    
    const containerWidth = container.offsetWidth;
    const elementWidth = element.offsetWidth;
    
    // If text is still too wide, reduce font size further
    if (elementWidth > containerWidth) {
      const scaleFactor = containerWidth / elementWidth;
      const currentSize = parseFloat(getComputedStyle(element).fontSize);
      const newSize = Math.max(this.minFontSize, currentSize * scaleFactor * 0.95);
      
      element.style.fontSize = newSize + 'px';
      element.style.setProperty('--dynamic-font-size', newSize + 'px');
    }
  }
  
  preventWordSplitting(element) {
    // Ensure no word breaking
    element.style.whiteSpace = 'nowrap';
    element.style.wordBreak = 'keep-all';
    element.style.hyphens = 'none';
    element.style.webkitHyphens = 'none';
    element.style.mozHyphens = 'none';
    element.style.msHyphens = 'none';
    
    // Handle overflow
    element.style.overflow = 'hidden';
    element.style.textOverflow = 'ellipsis';
  }
  
  // Public method to manually adjust specific elements
  adjustElement(element) {
    this.adjustFontSize(element);
  }
  
  // Public method to process new elements
  processNewElements() {
    this.processAllTextElements();
  }
  
  // Public method to refresh all elements
  refresh() {
    this.processAllTextElements();
  }
  
  // Cleanup method
  destroy() {
    if (this.observer) {
      this.observer.disconnect();
    }
    if (this.resizeTimeout) {
      clearTimeout(this.resizeTimeout);
    }
  }
}

// Initialize the unified font sizing system
const unifiedFontSizing = new UnifiedFontSizing();

// Export for use in other scripts
window.unifiedFontSizing = unifiedFontSizing;

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    unifiedFontSizing.init();
  });
} else {
  unifiedFontSizing.init();
}

// Handle template generation events
document.addEventListener('templateGenerated', () => {
  setTimeout(() => {
    unifiedFontSizing.processNewElements();
  }, 100);
});

// Handle label generation events
document.addEventListener('labelsGenerated', () => {
  setTimeout(() => {
    unifiedFontSizing.processNewElements();
  }, 100);
});

// Handle dynamic content updates
document.addEventListener('contentUpdated', () => {
  setTimeout(() => {
    unifiedFontSizing.processNewElements();
  }, 100);
});

// Utility functions for external use
window.FontSizingUtils = {
  adjustElement: (element) => unifiedFontSizing.adjustElement(element),
  processNewElements: () => unifiedFontSizing.processNewElements(),
  refresh: () => unifiedFontSizing.refresh(),
  destroy: () => unifiedFontSizing.destroy()
}; 