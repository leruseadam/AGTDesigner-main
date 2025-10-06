// Simple and Robust Drag and Drop Manager
// Focused on preventing freezing and multiple event handler issues

class DragAndDropManager {
    constructor() {
        this.isDragging = false;
        this.draggedElement = null;
        this.draggedElementText = null;
        this.draggedElementId = null;
        this.draggedElementSnapshot = null;
        this.dragStartCoords = null;
        this.dragThreshold = 5;
        this.isInitialized = false;
        this.targetPosition = null;
        this.originalIndex = null;
        this.isLineageUpdating = false;
        this._isReordering = false;
        this.dropIndicator = null;
        this.isUpdatingTags = false; // Flag to prevent reinitialization during tag updates
        
        // Single event handler approach
        this.boundHandleMouseDown = this.handleMouseDown.bind(this);
        this.boundHandleMouseMove = this.handleMouseMove.bind(this);
        this.boundHandleMouseUp = this.handleMouseUp.bind(this);
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
        
        // Listen for lineage update events
        this.setupLineageUpdateListener();
        
        // Listen for tag update events to prevent conflicts
        this.setupTagUpdateListener();
    }

    init() {
        if (this.isInitialized) return;
        
        console.log('Initializing Simple DragAndDropManager...');
        this.setupTagDragAndDrop();
        this.isInitialized = true;
    }

    setupTagDragAndDrop() {
        // Only setup for selected tags (reordering only)
        this.setupDragZone('#selectedTags');
        
        // Add checkbox change prevention during drag
        this.setupCheckboxProtection();
    }

    setupCheckboxProtection() {
        // Prevent checkbox changes during drag operations
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('tag-checkbox') && this.isDragging) {
                console.log('Preventing checkbox change during drag operation');
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                
                // Restore the original checked state
                const tagRow = e.target.closest('.tag-row');
                if (tagRow && this.draggedElement === tagRow) {
                    // Keep the checkbox checked since we're dragging a selected tag
                    e.target.checked = true;
                }
                return false;
            }
        }, true);
        
        // Prevent click events on checkboxes during drag
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tag-checkbox') && this.isDragging) {
                console.log('Preventing checkbox click during drag operation');
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                return false;
            }
        }, true);
        
        // Prevent click events on tag items during drag
        document.addEventListener('click', (e) => {
            if (e.target.closest('.tag-item') && this.isDragging) {
                console.log('Preventing tag item click during drag operation');
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                return false;
            }
        }, true);
        
        // Remove verbose debugging listeners to avoid heavy console logging
    }

    setupDragZone(selector) {
        const container = document.querySelector(selector);
        if (!container) {
            console.warn(`Container not found: ${selector}`);
            return;
        }

        // Remove any existing listeners first
        container.removeEventListener('mousedown', this.boundHandleMouseDown);
        
        // Add single event listener
        container.addEventListener('mousedown', this.boundHandleMouseDown);
        
        // Add drag handles
        this.addDragHandles(container);
        
        console.log(`Setup drag zone for ${selector}`);
    }
    
    addDragHandles(container) {
        console.log('Adding drag handles to container:', container);
        
        // Check if we're in the middle of updating tags
        if (this.isUpdatingTags) {
            console.log('Skipping drag handle addition due to ongoing tag updates');
            return;
        }
        
        // Remove existing handles
        const existingHandles = container.querySelectorAll('.drag-handle');
        existingHandles.forEach(handle => handle.remove());
        console.log(`Removed ${existingHandles.length} existing drag handles`);
        
        // Add handles to all tag rows (the actual draggable containers)
        const allTagRows = container.querySelectorAll('.tag-row');
        const tagRows = Array.from(allTagRows).filter(row => row.querySelector('.tag-checkbox'));
        console.log(`Found ${allTagRows.length} total tag rows, ${tagRows.length} with checkboxes`);
        
        if (tagRows.length === 0) {
            console.warn('No tag rows with checkboxes found in container');
            console.log('Available tag rows:', Array.from(allTagRows).map(row => ({
                text: row.textContent.trim().substring(0, 50),
                hasCheckbox: !!row.querySelector('.tag-checkbox'),
                classes: row.className,
                children: Array.from(row.children).map(child => child.className)
            })));
            return;
        }
        
        tagRows.forEach((tagRow, index) => {
            // Skip if already has handle
            if (tagRow.querySelector('.drag-handle')) {
                console.log(`Tag row ${index} already has drag handle, skipping`);
                return;
            }
            
            // Add unique identifier to tag row if not already present
            if (!tagRow.getAttribute('data-tag-id')) {
                const tagText = tagRow.textContent.trim();
                const tagId = `tag-${index}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                tagRow.setAttribute('data-tag-id', tagId);
            }
            
            // Make sure tag row has relative positioning and proper padding
            if (getComputedStyle(tagRow).position === 'static') {
                tagRow.style.position = 'relative';
            }
            
            // Ensure proper padding for drag handle
            if (!tagRow.style.paddingLeft || tagRow.style.paddingLeft === '0px') {
                tagRow.style.paddingLeft = '32px';
            }
            
            // Create drag handle with stronger styles
            const dragHandle = document.createElement('div');
            dragHandle.className = 'drag-handle';
            dragHandle.setAttribute('data-drag-handle', 'true');
            dragHandle.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
                </svg>
            `;
            
            // Apply very strong inline styles to ensure they work
            dragHandle.style.cssText = `
                position: absolute !important;
                left: 6px !important;
                top: 50% !important;
                transform: translateY(-50%) !important;
                color: rgba(79, 172, 254, 1) !important;
                opacity: 0.9 !important;
                transition: all 0.3s ease !important;
                cursor: grab !important;
                pointer-events: auto !important;
                z-index: 1000 !important;
                background: rgba(79, 172, 254, 0.25) !important;
                border-radius: 6px !important;
                padding: 6px !important;
                border: 2px solid rgba(79, 172, 254, 0.6) !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: 28px !important;
                height: 28px !important;
                box-shadow: 
                    0 3px 8px rgba(79, 172, 254, 0.3),
                    0 1px 3px rgba(0,0,0,0.2) !important;
            `;
            
            // Add enhanced hover effect with stronger styles
            dragHandle.addEventListener('mouseenter', () => {
                dragHandle.style.opacity = '1';
                dragHandle.style.background = 'rgba(79, 172, 254, 0.5)';
                dragHandle.style.transform = 'translateY(-50%) scale(1.15)';
                dragHandle.style.borderColor = 'rgba(79, 172, 254, 1)';
                dragHandle.style.boxShadow = `
                    0 6px 16px rgba(79, 172, 254, 0.5),
                    0 2px 8px rgba(0,0,0,0.2)
                `;
                dragHandle.style.color = 'white';
            });
            
            dragHandle.addEventListener('mouseleave', () => {
                dragHandle.style.opacity = '0.9';
                dragHandle.style.background = 'rgba(79, 172, 254, 0.25)';
                dragHandle.style.transform = 'translateY(-50%) scale(1)';
                dragHandle.style.borderColor = 'rgba(79, 172, 254, 0.6)';
                dragHandle.style.boxShadow = `
                    0 3px 8px rgba(79, 172, 254, 0.3),
                    0 1px 3px rgba(0,0,0,0.2)
                `;
                dragHandle.style.color = 'rgba(79, 172, 254, 1)';
            });
            
            tagRow.appendChild(dragHandle);
            console.log(`Added drag handle to tag row ${index}: ${tagRow.textContent.trim().substring(0, 30)}...`);
            
            // Verify the handle was added correctly
            const addedHandle = tagRow.querySelector('.drag-handle');
            if (addedHandle) {
                console.log(`✓ Drag handle successfully added to tag row ${index}`);
                const rect = addedHandle.getBoundingClientRect();
                console.log(`  Handle position: left=${rect.left}, top=${rect.top}, width=${rect.width}, height=${rect.height}`);
            } else {
                console.error(`✗ Failed to add drag handle to tag row ${index}`);
            }
        });
        
        console.log(`Successfully added ${tagRows.length} drag handles`);
        
        // Final verification
        const finalHandles = container.querySelectorAll('.drag-handle');
        console.log(`Final count: ${finalHandles.length} drag handles in container`);
    }

    handleMouseDown(e) {
        console.log('Mouse down event triggered:', e.target);
        
        // Only handle left mouse button
        if (e.button !== 0) {
            console.log('Not left mouse button, ignoring');
            return;
        }
        
        const tagRow = e.target.closest('.tag-row');
        if (!tagRow) {
            console.log('No tag-row found, ignoring');
            return;
        }
        
        // Check if clicking on drag handle
        const isDragHandle = e.target.closest('.drag-handle');
        if (!isDragHandle) {
            console.log('Not clicking on drag handle, ignoring');
            return;
        }
        
        console.log('Drag handle clicked!');
        
        // Check if lineage updates are happening (but allow if already dragging)
        if (this.isLineageUpdating && !this.isDragging) {
            console.log('New drag prevented - lineage update in progress');
            return;
        }
        
        // Validate that the tag row has a valid checkbox before starting drag
        const checkbox = tagRow.querySelector('.tag-checkbox');
        if (!checkbox || !checkbox.value) {
            console.log('Tag row has invalid checkbox, preventing drag');
            return;
        }
        
        console.log('Drag handle clicked for:', tagRow.textContent.trim());
        
        // Prevent default behavior and stop propagation to prevent checkbox changes
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        
        // Store initial coordinates
        this.dragStartCoords = { x: e.clientX, y: e.clientY };
        console.log('Drag start coordinates:', this.dragStartCoords);
        
        // Store original index and element reference
        const container = document.querySelector('#selectedTags');
        const tagRows = this.getDraggableTagItems(container);
        this.originalIndex = tagRows.indexOf(tagRow);
        console.log('Original index:', this.originalIndex);
        
        // Store a reference to the element's text content for validation
        this.draggedElementText = tagRow.textContent.trim();
        
        // Store additional identifying information
        this.draggedElementId = tagRow.getAttribute('data-tag-id');
        
        // Store a snapshot of the element's state
        this.draggedElementSnapshot = {
            textContent: this.draggedElementText,
            tagId: this.draggedElementId,
            index: this.originalIndex,
            parentNode: tagRow.parentNode,
            nextSibling: tagRow.nextSibling,
            previousSibling: tagRow.previousSibling,
            className: tagRow.className,
            innerHTML: tagRow.innerHTML
        };
        
        // Add dragging class and initial visual feedback
        tagRow.classList.add('dragging');
        tagRow.style.zIndex = '10000';
        tagRow.style.transition = 'none';
        tagRow.style.transform = 'scale(1.02) rotate(1deg)';
        tagRow.style.boxShadow = '0 4px 12px rgba(79, 172, 254, 0.3)';
        
        // Set dragging state
        this.isDragging = true;
        this.draggedElement = tagRow;
        
        // Disable checkbox interactions during drag
        const checkboxElement = tagRow.querySelector('.tag-checkbox');
        if (checkboxElement) {
            checkboxElement.style.pointerEvents = 'none';
            checkboxElement.setAttribute('data-drag-disabled', 'true');
        }
        
        // Disable click events on tag-item during drag to prevent conflicts
        const tagItem = tagRow.querySelector('.tag-item');
        if (tagItem) {
            tagItem.style.pointerEvents = 'none';
            tagItem.setAttribute('data-drag-disabled', 'true');
        }
        
        // Add global event listeners
        document.addEventListener('mousemove', this.boundHandleMouseMove);
        document.addEventListener('mouseup', this.boundHandleMouseUp);
        
        console.log('Drag started for:', tagRow.textContent.trim());
    }

    getDraggableTagItems(container) {
        // Get only the leaf tag items that have checkboxes (actual draggable items)
        // The structure is: tag-row > tag-item > checkbox
        // We want to return the tag-row elements (the draggable containers)
        const allTagRows = container.querySelectorAll('.tag-row');
        return Array.from(allTagRows).filter(row => row.querySelector('.tag-checkbox'));
    }

    handleMouseMove(e) {
        if (!this.isDragging || !this.draggedElement) {
            console.log('Mouse move ignored - not dragging');
            return;
        }
        
        console.log('Mouse move during drag:', e.clientX, e.clientY);
        
        // Validate the dragged element is still valid
        if (!this.isValidDraggedElement()) {
            console.log('Dragged element is no longer valid, ending drag');
            this.resetDragState();
            return;
        }
        
        // Calculate movement
        const deltaX = Math.abs(e.clientX - this.dragStartCoords.x);
        const deltaY = Math.abs(e.clientY - this.dragStartCoords.y);
        console.log('Movement delta:', deltaX, deltaY);
        
        // Enhanced visual feedback when dragging
        this.draggedElement.style.transform = 'rotate(3deg) scale(1.08)';
        this.draggedElement.style.opacity = '0.9';
        this.draggedElement.style.boxShadow = `
            0 12px 32px rgba(79, 172, 254, 0.6),
            0 0 0 3px rgba(79, 172, 254, 0.3),
            0 4px 16px rgba(0, 0, 0, 0.2)
        `;
        this.draggedElement.style.borderRadius = '12px';
        this.draggedElement.style.background = 'rgba(79, 172, 254, 0.15)';
        this.draggedElement.style.border = '2px solid rgba(79, 172, 254, 0.5)';
        this.draggedElement.style.zIndex = '10000';
        this.draggedElement.style.transition = 'none';
        
        // Find the target position for reordering
        this.findDropPosition(e.clientY);
    }

    handleMouseUp(e) {
        if (!this.isDragging || !this.draggedElement) {
            console.log('Mouse up ignored - not dragging');
            return;
        }
        
        console.log('Mouse up during drag - ending drag operation');
        console.log('Drag ended for:', this.draggedElement.textContent.trim());
        
        // Remove global event listeners
        document.removeEventListener('mousemove', this.boundHandleMouseMove);
        document.removeEventListener('mouseup', this.boundHandleMouseUp);
        
        // Re-enable checkbox interactions
        const checkbox = this.draggedElement.querySelector('.tag-checkbox');
        if (checkbox) {
            checkbox.style.pointerEvents = '';
            checkbox.removeAttribute('data-drag-disabled');
        }
        
        // Re-enable tag-item interactions
        const tagItem = this.draggedElement.querySelector('.tag-item');
        if (tagItem) {
            tagItem.style.pointerEvents = '';
            tagItem.removeAttribute('data-drag-disabled');
        }
        
        // Reset visual state
        this.draggedElement.style.transform = '';
        this.draggedElement.style.opacity = '';
        this.draggedElement.style.boxShadow = '';
        this.draggedElement.style.zIndex = '';
        this.draggedElement.style.borderRadius = '';
        this.draggedElement.style.background = '';
        this.draggedElement.style.border = '';
        this.draggedElement.style.transition = '';
        this.draggedElement.classList.remove('dragging');
        
        // Clear drop indicators
        this.clearDropIndicators();
        
        // Perform reorder if we have a valid target position
        if (this.targetPosition !== null && this.targetPosition !== this.originalIndex) {
            console.log('Performing reorder from', this.originalIndex, 'to', this.targetPosition);
            this.performReorder();
            // Add success feedback
            this.showReorderSuccess();
        } else {
            console.log('No reorder needed - target position:', this.targetPosition, 'original index:', this.originalIndex);
        }
        
        // Reset drag state
        this.resetDragState();
    }

    findDropPosition(mouseY) {
        const container = document.querySelector('#selectedTags');
        if (!container) return;
        
        // Get all tag rows in the entire selected tags container
        const allTagRows = Array.from(container.querySelectorAll('.tag-row')).filter(row => 
            row.querySelector('.tag-checkbox')
        );
        
        if (allTagRows.length === 0) return;
        
        console.log(`Found ${allTagRows.length} total tag rows across all containers`);
        
        let targetIndex = 0;
        let targetParent = null;
        
        // Find the target position across all containers
        for (let i = 0; i < allTagRows.length; i++) {
            const item = allTagRows[i];
            const rect = item.getBoundingClientRect();
            const itemMiddle = rect.top + rect.height / 2;
            
            if (mouseY < itemMiddle) {
                targetIndex = i;
                targetParent = this.findParentContainer(item);
                break;
            } else if (i === allTagRows.length - 1) {
                targetIndex = allTagRows.length;
                targetParent = this.findParentContainer(item);
            }
        }
        
        // Don't allow dropping on itself
        if (targetIndex === this.originalIndex) {
            targetIndex = this.originalIndex + 1;
        }
        
        // Ensure target index is within bounds
        targetIndex = Math.max(0, Math.min(targetIndex, allTagRows.length));
        
        if (this.targetPosition !== targetIndex) {
            this.targetPosition = targetIndex;
            this.showDropIndicator(targetIndex, targetParent, allTagRows);
        }
    }

    showDropIndicator(targetIndex, parent, allTagRows) {
        this.clearDropIndicators();
        
        if (!parent || allTagRows.length === 0) return;
        
        let targetItem;
        let position;
        
        if (targetIndex === 0) {
            targetItem = allTagRows[0];
            position = 'before';
        } else if (targetIndex >= allTagRows.length) {
            targetItem = allTagRows[allTagRows.length - 1];
            position = 'after';
        } else {
            targetItem = allTagRows[targetIndex];
            position = 'before';
        }
        
        this.createDropIndicator(targetItem, position, parent);
    }

    createDropIndicator(targetItem, position, parent) {
        // Removed blue line indicator - it was not aligning properly with cursor
        // Only keep the target area highlight for visual feedback
        if (!targetItem) return;
        
        // Add a subtle highlight to the target area
        this.highlightTargetArea(targetItem, position);
    }

    highlightTargetArea(targetItem, position) {
        // Remove any existing highlights
        this.clearTargetHighlights();
        
        // Add highlight to the target item
        targetItem.style.transition = 'all 0.3s ease';
        targetItem.style.boxShadow = '0 0 0 3px rgba(79, 172, 254, 0.4), 0 4px 16px rgba(79, 172, 254, 0.3)';
        targetItem.style.borderRadius = '8px';
        targetItem.style.background = 'rgba(79, 172, 254, 0.1)';
        targetItem.setAttribute('data-drop-target', 'true');
        
        // Add a subtle animation to the target
        targetItem.style.animation = 'targetPulse 2s ease-in-out infinite';
    }

    clearTargetHighlights() {
        const highlightedItems = document.querySelectorAll('[data-drop-target="true"]');
        highlightedItems.forEach(item => {
            item.style.boxShadow = '';
            item.style.borderRadius = '';
            item.style.background = '';
            item.style.animation = '';
            item.removeAttribute('data-drop-target');
        });
    }

    showReorderSuccess() {
        // Add a brief success animation to the reordered element
        if (this.draggedElement) {
            this.draggedElement.style.transition = 'all 0.3s ease';
            this.draggedElement.style.boxShadow = '0 0 0 3px rgba(76, 175, 80, 0.6), 0 6px 20px rgba(76, 175, 80, 0.4)';
            this.draggedElement.style.borderRadius = '8px';
            this.draggedElement.style.background = 'rgba(76, 175, 80, 0.1)';
            
            // Reset after animation
            setTimeout(() => {
                if (this.draggedElement) {
                    this.draggedElement.style.boxShadow = '';
                    this.draggedElement.style.borderRadius = '';
                    this.draggedElement.style.background = '';
                    this.draggedElement.style.transition = '';
                }
            }, 800);
        }
    }

    clearDropIndicators() {
        // Clear target highlights only (blue line indicator removed)
        this.clearTargetHighlights();
    }

    performReorder() {
        if (this.targetPosition === null || this.originalIndex === null) return;
        
        console.log(`Reordering from index ${this.originalIndex} to ${this.targetPosition}`);
        
        const container = document.querySelector('#selectedTags');
        if (!container) return;
        
        // Get all tag rows BEFORE removing anything
        const allTagRows = Array.from(container.querySelectorAll('.tag-row')).filter(row => 
            row.querySelector('.tag-checkbox')
        );
        
        if (allTagRows.length === 0) return;
        
        // Get the dragged element
        const draggedElement = allTagRows[this.originalIndex];
        if (!draggedElement) return;
        
        // Get the checkbox value for debugging
        const draggedCheckbox = draggedElement.querySelector('.tag-checkbox');
        const draggedValue = draggedCheckbox ? draggedCheckbox.value : 'unknown';
        console.log('Dragging element with value:', draggedValue);
        
        // Find the parent container of the dragged element
        const draggedParent = this.findParentContainer(draggedElement);
        console.log('Dragged element parent:', draggedParent);
        
        // Temporarily disable the checkbox to prevent interference
        if (draggedCheckbox) {
            draggedCheckbox.setAttribute('data-reordering', 'true');
            draggedCheckbox.style.pointerEvents = 'none';
        }
        
        // Store the element's data to ensure it stays in selected tags
        const elementData = {
            element: draggedElement,
            value: draggedValue,
            parent: draggedParent || container
        };
        
        // Remove from current position
        draggedElement.remove();
        
        // Calculate the correct target position after removal
        // If we're moving to a position after the original, we need to adjust for the removal
        let adjustedTargetPosition = this.targetPosition;
        if (this.targetPosition > this.originalIndex) {
            adjustedTargetPosition = this.targetPosition - 1;
        }
        
        // Ensure target position is within bounds
        adjustedTargetPosition = Math.max(0, Math.min(adjustedTargetPosition, allTagRows.length - 1));
        
        // Get the target element after removal
        const remainingTagRows = Array.from(container.querySelectorAll('.tag-row')).filter(row => 
            row.querySelector('.tag-checkbox')
        );
        
        const targetElement = remainingTagRows[adjustedTargetPosition];
        const targetParent = targetElement ? this.findParentContainer(targetElement) : null;
        
        console.log('Target element parent:', targetParent);
        console.log('Adjusted target position:', adjustedTargetPosition);
        console.log('Remaining tag rows count:', remainingTagRows.length);
        
        // Insert the dragged element at the correct position
        if (targetElement && targetParent) {
            // Insert before the target element
            targetParent.insertBefore(draggedElement, targetElement);
            console.log('Inserted before target element');
        } else if (targetParent) {
            // Append to the target parent
            targetParent.appendChild(draggedElement);
            console.log('Appended to target parent');
        } else if (remainingTagRows.length > 0) {
            // Insert before the first remaining element
            const firstElement = remainingTagRows[0];
            const firstParent = this.findParentContainer(firstElement);
            if (firstParent) {
                firstParent.insertBefore(draggedElement, firstElement);
                console.log('Inserted before first element');
            } else {
                container.appendChild(draggedElement);
                console.log('Appended to main container');
            }
        } else {
            // No remaining elements, append to main container
            container.appendChild(draggedElement);
            console.log('Appended to main container (no remaining elements)');
        }
        
        // Verify the element is still in the selected tags container
        const isStillInSelected = container.contains(draggedElement);
        console.log('Element still in selected tags:', isStillInSelected);
        
        if (!isStillInSelected) {
            console.error('Element was moved out of selected tags! Attempting to restore...');
            container.appendChild(draggedElement);
        }
        
        // Re-enable the checkbox after a short delay
        setTimeout(() => {
            if (draggedCheckbox) {
                draggedCheckbox.removeAttribute('data-reordering');
                draggedCheckbox.style.pointerEvents = '';
            }
        }, 100);
        
        // Validate tag integrity after reorder
        if (!this.validateTagIntegrity()) {
            console.error('Tag integrity validation failed after reorder!');
            // Try to restore the tag if possible
            if (draggedElement && !container.contains(draggedElement)) {
                console.log('Attempting to restore lost tag...');
                container.appendChild(draggedElement);
            }
        }
        
        // Update backend order
        this.updateBackendOrder();
        
        console.log('Reorder completed');
    }

    findParentContainer(element) {
        // Find the immediate parent container that holds tag rows
        // This could be weight-section, product-type-section, brand-section, or vendor-section
        let parent = element.parentElement;
        
        while (parent && parent !== document.querySelector('#selectedTags')) {
            if (parent.classList.contains('weight-section') || 
                parent.classList.contains('product-type-section') || 
                parent.classList.contains('brand-section') || 
                parent.classList.contains('vendor-section')) {
                return parent;
            }
            parent = parent.parentElement;
        }
        
        return null;
    }

    async updateBackendOrder() {
        const container = document.querySelector('#selectedTags');
        if (!container) return;
        
        // Collect tags in the order they appear in the DOM, respecting hierarchy
        const newOrder = [];
        
        // Walk through the DOM tree in visual order to collect tags
        const walkDOMInOrder = (element) => {
            const children = Array.from(element.children);
            for (const child of children) {
                // If this child is a tag-row, collect its checkbox value
                if (child.classList.contains('tag-row')) {
                    const checkbox = child.querySelector('.tag-checkbox');
                    if (checkbox && checkbox.value) {
                        newOrder.push(checkbox.value);
                    }
                } else {
                    // Recursively walk through child elements
                    walkDOMInOrder(child);
                }
            }
        };
        
        walkDOMInOrder(container);
        
        console.log('New order (respecting hierarchy):', newOrder);
        console.log('DOM order collection - container children:', Array.from(container.children).map(child => child.className));
        
        try {
            const response = await fetch('/api/update-selected-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ order: newOrder })
            });
            
            if (response.ok) {
                console.log('Backend order updated successfully');
                
                // Update the frontend persistentSelectedTags state to match the new order
                if (window.TagManager && window.TagManager.state && window.TagManager.state.persistentSelectedTags) {
                    // Clear the current persistentSelectedTags and add them in the new order
                    window.TagManager.state.persistentSelectedTags.length = 0; // Clear array
                    // Add items in the new order to preserve insertion order
                    newOrder.forEach(tag => {
                        window.TagManager.state.persistentSelectedTags.push(tag);
                    });
                    console.log('Frontend persistentSelectedTags updated with new order:', window.TagManager.state.persistentSelectedTags);
                    console.log('Frontend persistentSelectedTags Array length:', window.TagManager.state.persistentSelectedTags.length);
                }
                
                // Don't call updateSelectedTags here as it rebuilds the DOM and removes drag handles
                // The order is already correct in the DOM from the drag operation
            } else {
                console.error('Failed to update backend order');
            }
        } catch (error) {
            console.error('Error updating backend order:', error);
        }
    }

    triggerUIRefresh() {
        // Trigger a UI refresh to ensure everything is properly updated
        if (window.TagManager && window.TagManager.updateSelectedTags) {
            const container = document.querySelector('#selectedTags');
            if (container) {
                const tagRows = this.getDraggableTagItems(container);
                const selectedTagNames = tagRows.map(row => {
                    const checkbox = row.querySelector('.tag-checkbox');
                    return checkbox ? checkbox.value : null;
                }).filter(Boolean);
                
                // Convert tag names to tag objects for updateSelectedTags
                const selectedTagObjects = selectedTagNames.map(tagName => {
                    // First try to find in current tags (filtered view)
                    let foundTag = window.TagManager.state.tags.find(t => t['Product Name*'] === tagName);
                    // If not found in current tags, try original tags
                    if (!foundTag) {
                        foundTag = window.TagManager.state.originalTags.find(t => t['Product Name*'] === tagName);
                    }
                    // If still not found, create a minimal tag object (for JSON matched items)
                    if (!foundTag) {
                        console.warn(`Tag not found in state: ${tagName}, creating minimal tag object`);
                        foundTag = {
                            'Product Name*': tagName,
                            'Product Brand': 'Unknown',
                            'Vendor': 'Unknown',
                            'Product Type*': 'Unknown',
                            'Lineage': 'MIXED'
                        };
                    }
                    return foundTag;
                }).filter(Boolean);
                
                // Update the TagManager state
                window.TagManager.updateSelectedTags(selectedTagObjects);
            }
        }
    }

    reinitializeTagDragAndDrop() {
        if (this.isUpdatingTags) {
            console.log('Skipping reinitialization due to ongoing tag updates.');
            return;
        }
        console.log('Reinitializing tag drag and drop...');
        this.setupTagDragAndDrop();
    }

    updateIndicators() {
        // Update any visual indicators
        this.clearDropIndicators();
    }

    cleanup() {
        // Clean up any existing drag state
        this.resetDragState();
        this.clearDropIndicators();
        
        // Remove event listeners
        const container = document.querySelector('#selectedTags');
        if (container) {
            container.removeEventListener('mousedown', this.boundHandleMouseDown);
        }
        
        document.removeEventListener('mousemove', this.boundHandleMouseMove);
        document.removeEventListener('mouseup', this.boundHandleMouseUp);
    }

    resetDragState() {
        this.isDragging = false;
        this.draggedElement = null;
        this.draggedElementText = null;
        this.draggedElementId = null;
        this.draggedElementSnapshot = null;
        this.dragStartCoords = null;
        this.targetPosition = null;
        this.originalIndex = null;
        this._isReordering = false;
        
        // Remove dragging class from any elements and re-enable checkboxes
        const draggingElements = document.querySelectorAll('.tag-row.dragging');
        draggingElements.forEach(element => {
            element.classList.remove('dragging');
            element.style.transform = '';
            element.style.opacity = '';
            element.style.boxShadow = '';
            element.style.zIndex = '';
            element.style.borderRadius = '';
            element.style.background = '';
            element.style.border = '';
            element.style.transition = '';
            
            // Re-enable checkbox interactions
            const checkbox = element.querySelector('.tag-checkbox');
            if (checkbox) {
                checkbox.style.pointerEvents = 'auto';
                checkbox.removeAttribute('data-drag-disabled');
                checkbox.removeAttribute('data-reordering');
            }
            
            // Re-enable tag-item interactions
            const tagItem = element.querySelector('.tag-item');
            if (tagItem) {
                tagItem.style.pointerEvents = 'auto';
                tagItem.removeAttribute('data-drag-disabled');
                tagItem.removeAttribute('data-reordering');
            }
        });
        
        // Also re-enable any checkboxes that might have been disabled during drag
        const disabledCheckboxes = document.querySelectorAll('.tag-checkbox[data-drag-disabled="true"]');
        disabledCheckboxes.forEach(checkbox => {
            checkbox.style.pointerEvents = 'auto';
            checkbox.removeAttribute('data-drag-disabled');
            checkbox.removeAttribute('data-reordering');
        });
        
        // Re-enable all tag items that might have been disabled
        const disabledTagItems = document.querySelectorAll('.tag-item[data-drag-disabled="true"]');
        disabledTagItems.forEach(tagItem => {
            tagItem.style.pointerEvents = 'auto';
            tagItem.removeAttribute('data-drag-disabled');
            tagItem.removeAttribute('data-reordering');
        });
        
        console.log('Drag state reset - all checkboxes and tag items re-enabled');
        
        // Also re-enable any tag-items that might have been disabled during drag
        const disabledTagItems2 = document.querySelectorAll('.tag-item[data-drag-disabled="true"]');
        disabledTagItems2.forEach(tagItem => {
            tagItem.style.pointerEvents = '';
            tagItem.removeAttribute('data-drag-disabled');
        });
    }

    isValidDraggedElement() {
        if (!this.draggedElement || !this.draggedElementText) return false;
        
        // Check if the element still exists in the DOM
        if (!document.contains(this.draggedElement)) return false;
        
        // Check if the text content is still the same (basic validation)
        const currentText = this.draggedElement.textContent.trim();
        if (currentText !== this.draggedElementText) {
            console.log('Text content changed during drag:', {
                original: this.draggedElementText,
                current: currentText
            });
            return false;
        }
        
        return true;
    }

    validateTagIntegrity() {
        const container = document.querySelector('#selectedTags');
        if (!container) return false;
        
        const allTagRows = Array.from(container.querySelectorAll('.tag-row')).filter(row => 
            row.querySelector('.tag-checkbox')
        );
        
        console.log(`Validation: Found ${allTagRows.length} tag rows in selected tags`);
        
        // Check that all tag rows have valid checkboxes
        for (let i = 0; i < allTagRows.length; i++) {
            const row = allTagRows[i];
            const checkbox = row.querySelector('.tag-checkbox');
            if (!checkbox || !checkbox.value) {
                console.error(`Validation failed: Tag row ${i} has invalid checkbox`);
                return false;
            }
        }
        
        return true;
    }

    setupLineageUpdateListener() {
        // Listen for lineage update events to prevent conflicts
        document.addEventListener('lineageUpdateStart', () => {
            this.isLineageUpdating = true;
            console.log('Lineage update started, preventing new drags');
        });
        
        document.addEventListener('lineageUpdateEnd', () => {
            this.isLineageUpdating = false;
            console.log('Lineage update ended, allowing drags');
        });
    }

    setupTagUpdateListener() {
        // Listen for events that might trigger a full tag update,
        // which would require re-initializing the drag and drop manager
        document.addEventListener('updateSelectedTags', () => {
            this.isUpdatingTags = true;
            console.log('updateSelectedTags event received, preventing reinitialization.');
        });
                 document.addEventListener('updateSelectedTagsComplete', () => {
             this.isUpdatingTags = false;
             console.log('updateSelectedTagsComplete event received, allowing reinitialization.');
             // Re-initialize after a short delay to ensure all elements are ready
             setTimeout(() => {
                 this.reinitializeTagDragAndDrop();
             }, 200);
         });
    }

    destroy() {
        this.cleanup();
        this.isInitialized = false;
    }

    testDragAndDrop() {
        console.log('Testing drag and drop functionality...');
        const container = document.querySelector('#selectedTags');
        if (!container) {
            console.error('Selected tags container not found');
            return false;
        }
        
        const tagRows = this.getDraggableTagItems(container);
        console.log(`Found ${tagRows.length} draggable tag rows`);
        
        const dragHandles = container.querySelectorAll('.drag-handle');
        console.log(`Found ${dragHandles.length} drag handles`);
        
        return {
            containerFound: !!container,
            tagRowsCount: tagRows.length,
            dragHandlesCount: dragHandles.length,
            isInitialized: this.isInitialized,
            isDragging: this.isDragging
        };
    }
}

// Initialize the drag and drop manager globally
if (!window.dragAndDropManager) {
    window.dragAndDropManager = new DragAndDropManager();
    console.log('Simple DragAndDropManager initialized');
} else {
    console.log('DragAndDropManager already exists, skipping initialization');
}

// Force reinitialize after DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        if (window.dragAndDropManager) {
            console.log('Force reinitializing drag and drop after DOM load');
            window.dragAndDropManager.reinitializeTagDragAndDrop();
        }
    }, 500);
});

// Also reinitialize after a longer delay to catch any late-loading content
setTimeout(() => {
    if (window.dragAndDropManager) {
        console.log('Delayed reinitialization of drag and drop');
        window.dragAndDropManager.reinitializeTagDragAndDrop();
    }
}, 2000);

// Expose test function globally for debugging
window.testDragAndDrop = () => {
    if (window.dragAndDropManager) {
        return window.dragAndDropManager.testDragAndDrop();
    } else {
        console.error('Drag and Drop Manager not available');
        return null;
    }
};

// Add a function to manually initialize drag and drop
window.initializeDragAndDrop = () => {
    if (window.dragAndDropManager) {
        console.log('Manually initializing drag and drop...');
        window.dragAndDropManager.reinitializeTagDragAndDrop();
        return true;
    } else {
        console.error('Drag and Drop Manager not available');
        return false;
    }
};

// Add a function to check drag handle visibility
window.checkDragHandles = () => {
    const handles = document.querySelectorAll('.drag-handle');
    const visibleHandles = Array.from(handles).filter(handle => {
        const rect = handle.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
    });
    
    console.log(`Found ${handles.length} drag handles, ${visibleHandles.length} visible`);
    return { total: handles.length, visible: visibleHandles.length };
};

// Add a simple test for drop indicators
window.forceReinitializeDragAndDrop = () => {
    if (window.dragAndDropManager) {
        window.dragAndDropManager.reinitializeTagDragAndDrop();
        return true;
    } else {
        console.error('Drag and Drop Manager not available');
        return false;
    }
};

// Add a simple test for drop indicators
window.testDropIndicators = () => {
    if (window.dragAndDropManager) {
        const container = document.querySelector('#selectedTags');
        if (container) {
            const allTagRows = container.querySelectorAll('.tag-row');
            const tagRows = Array.from(allTagRows).filter(row => row.querySelector('.tag-checkbox'));
            if (tagRows.length > 0) {
                // Test showing indicator at first position
                window.dragAndDropManager.showDropIndicator(0);
                console.log('Test: Showing drop indicator at position 0');
                setTimeout(() => {
                    window.dragAndDropManager.clearDropIndicators();
                    console.log('Test: Cleared drop indicators');
                }, 2000);
            } else {
                console.log('No tag rows found to test');
            }
        } else {
            console.log('Selected tags container not found');
        }
    } else {
        console.error('Drag and Drop Manager not available');
    }
};

// Add CSS for drag and drop styling
const dragDropStyles = `
    .tag-row {
        cursor: grab;
        transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
        user-select: none;
        position: relative;
        border: 1px solid transparent;
        padding-left: 36px !important;
        margin: 4px 0;
    }
    
    .tag-row:hover {
        border-color: rgba(79, 172, 254, 0.3);
        background: rgba(79, 172, 254, 0.05);
    }
    
    .tag-row.dragging {
        cursor: grabbing;
    }
    
    .drag-handle:hover {
        opacity: 1 !important;
        background: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Removed drop-indicator CSS - blue line was not aligning properly with cursor */
    
    @keyframes targetPulse {
        0%, 100% {
            box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.4), 0 4px 16px rgba(79, 172, 254, 0.3);
        }
        50% {
            box-shadow: 0 0 0 4px rgba(79, 172, 254, 0.6), 0 6px 20px rgba(79, 172, 254, 0.5);
        }
    }
    
    .tag-row[data-drop-target="true"] {
        animation: targetPulse 2s ease-in-out infinite;
    }
`;

// Inject the styles into the document
if (!document.getElementById('drag-drop-styles')) {
    const styleElement = document.createElement('style');
    styleElement.id = 'drag-drop-styles';
    styleElement.textContent = dragDropStyles;
    document.head.appendChild(styleElement);
} 