# Unified Font Sizing System

## Overview

The Unified Font Sizing System prevents ANY full word from being split across lines in any template and automatically reduces font size to fit content within containers. This system ensures consistent, readable text across all label templates.

## Features

- **Prevents Word Splitting**: No words are ever broken across lines
- **Automatic Font Sizing**: Dynamically adjusts font size to fit content
- **Template-Aware**: Different sizing rules for different template types
- **Responsive**: Adapts to container size changes
- **Performance Optimized**: Uses efficient algorithms for real-time adjustments

## CSS Classes

### Base Classes

```css
.text-container          /* Universal text container */
.critical-text          /* Text that must always fit */
.responsive-text        /* Responsive font sizing */
.dynamic-font           /* JavaScript-controlled sizing */
.auto-size-text        /* Automatic size adjustment */
.container-aware-text   /* Container-aware sizing */
```

### Font Size Classes

```css
.font-size-auto         /* Automatic sizing */
.font-size-small        /* Small text (8px-14px) */
.font-size-medium       /* Medium text (10px-16px) */
.font-size-large        /* Large text (12px-20px) */
.font-size-xlarge       /* Extra large (14px-24px) */
```

### Special Classes

```css
.no-text-overflow       /* Prevents text overflow */
.multi-line-text        /* Allows controlled line wrapping */
.prevent-word-split     /* Forces no word breaking */
```

## Template-Specific Sizing

### Horizontal Template
- Base font size: 8px-12px
- Adjustment factor: 0.85
- Optimized for wide, short containers

### Vertical Template
- Base font size: 9px-14px
- Adjustment factor: 0.9
- Optimized for tall, narrow containers

### Mini Template
- Base font size: 7px-10px
- Adjustment factor: 0.75
- Optimized for small containers

### Double Template
- Base font size: 8px-13px
- Adjustment factor: 0.8
- Optimized for medium containers

## JavaScript API

### Global Object
```javascript
window.unifiedFontSizing
window.FontSizingUtils
```

### Methods

#### Adjust Specific Element
```javascript
// Adjust a single element
unifiedFontSizing.adjustElement(element);

// Using utility function
FontSizingUtils.adjustElement(element);
```

#### Process New Elements
```javascript
// Process all new text elements
unifiedFontSizing.processNewElements();

// Using utility function
FontSizingUtils.processNewElements();
```

#### Refresh All Elements
```javascript
// Refresh all text elements
unifiedFontSizing.refresh();

// Using utility function
FontSizingUtils.refresh();
```

#### Cleanup
```javascript
// Clean up observers and event listeners
unifiedFontSizing.destroy();

// Using utility function
FontSizingUtils.destroy();
```

## Usage Examples

### Basic Implementation

```html
<!-- Simple text container -->
<div class="text-container">
  Long product name that needs to fit
</div>

<!-- Critical text that must always fit -->
<div class="critical-text">
  Important label text
</div>

<!-- Responsive text -->
<div class="responsive-text">
  Text that adapts to container size
</div>
```

### Template-Specific Usage

```html
<!-- Horizontal template -->
<div class="template-horizontal">
  <div class="text-container">
    Product name here
  </div>
</div>

<!-- Vertical template -->
<div class="template-vertical">
  <div class="text-container">
    Product name here
  </div>
</div>

<!-- Mini template -->
<div class="template-mini">
  <div class="text-container">
    Product name here
  </div>
</div>

<!-- Double template -->
<div class="template-double">
  <div class="text-container">
    Product name here
  </div>
</div>
```

### Dynamic Content

```html
<!-- Auto-sizing text -->
<div class="auto-size-text">
  Dynamic content that adjusts automatically
</div>

<!-- Container-aware text -->
<div class="container-aware-text">
  Text that knows about its container
</div>
```

## CSS Variables

### Base Variables
```css
:root {
  --base-font-size: 12px;
  --min-font-size: 8px;
  --max-font-size: 24px;
  --line-height-ratio: 1.2;
  --word-spacing: 0.1em;
  --letter-spacing: 0.02em;
}
```

### Dynamic Variables
```css
--dynamic-font-size: /* Set by JavaScript */
```

## Event Handling

### Automatic Events
The system automatically handles:
- Window resize events
- DOM content changes
- Template generation events
- Label generation events
- Dynamic content updates

### Custom Events
```javascript
// Trigger when templates are generated
document.dispatchEvent(new Event('templateGenerated'));

// Trigger when labels are generated
document.dispatchEvent(new Event('labelsGenerated'));

// Trigger when content is updated
document.dispatchEvent(new Event('contentUpdated'));
```

## Performance Considerations

### Optimization Features
- **ResizeObserver**: Efficient container size monitoring
- **Debounced Events**: Prevents excessive recalculations
- **Binary Search**: Fast font size calculation
- **Temporary Elements**: Efficient text measurement
- **Caching**: Reuses calculated values when possible

### Best Practices
1. Use appropriate CSS classes for text elements
2. Avoid inline styles that conflict with the system
3. Ensure containers have defined dimensions
4. Use semantic HTML structure
5. Test with various content lengths

## Browser Support

### Required Features
- CSS `clamp()` function
- CSS custom properties (variables)
- ResizeObserver API
- MutationObserver API

### Supported Browsers
- Chrome 66+
- Firefox 69+
- Safari 13.1+
- Edge 79+

## Troubleshooting

### Common Issues

#### Text Still Overflowing
```javascript
// Force refresh of specific element
unifiedFontSizing.adjustElement(element);
```

#### Font Size Too Small
```css
/* Adjust minimum font size */
:root {
  --min-font-size: 10px; /* Increase from 8px */
}
```

#### Font Size Too Large
```css
/* Adjust maximum font size */
:root {
  --max-font-size: 18px; /* Decrease from 24px */
}
```

#### Performance Issues
```javascript
// Reduce update frequency
unifiedFontSizing.resizeTimeout = 200; // Increase from 100ms
```

### Debug Mode
```javascript
// Enable debug logging
unifiedFontSizing.debug = true;
```

## Integration with Existing Code

### Automatic Integration
The system automatically integrates with:
- Existing template generation
- Label creation processes
- Dynamic content updates
- UI interactions

### Manual Integration
```javascript
// Integrate with custom template generation
function generateTemplate() {
  // ... template generation code ...
  
  // Process new elements
  unifiedFontSizing.processNewElements();
}

// Integrate with custom label creation
function createLabels() {
  // ... label creation code ...
  
  // Process new elements
  unifiedFontSizing.processNewElements();
}
```

## Advanced Configuration

### Custom Font Size Ranges
```css
:root {
  --min-font-size: 6px;    /* Custom minimum */
  --max-font-size: 20px;   /* Custom maximum */
  --base-font-size: 10px;  /* Custom base */
}
```

### Template-Specific Adjustments
```css
/* Custom template adjustments */
.template-custom .text-container {
  font-size: clamp(9px, 2.5vw, 15px) !important;
}
```

### Custom Event Handling
```javascript
// Custom event handler
document.addEventListener('customTemplateEvent', () => {
  setTimeout(() => {
    unifiedFontSizing.processNewElements();
  }, 150);
});
```

## Testing

### Test Cases
1. **Short Text**: "ABC"
2. **Medium Text**: "Product Name"
3. **Long Text**: "Very Long Product Name That Exceeds Container Width"
4. **Very Long Text**: "Extremely Long Product Name That Will Definitely Exceed Container Width And Need Significant Font Reduction"

### Test Scenarios
- Different container sizes
- Various template types
- Dynamic content changes
- Window resize events
- Mobile vs desktop layouts

## Future Enhancements

### Planned Features
- **Multi-language Support**: Better handling of different languages
- **Font Family Awareness**: Consider different font characteristics
- **Advanced Algorithms**: Machine learning for optimal sizing
- **Accessibility**: WCAG compliance considerations
- **Print Optimization**: Special handling for print layouts

### Extension Points
- Custom font size calculation algorithms
- Template-specific sizing rules
- Integration with design systems
- Performance monitoring and analytics 