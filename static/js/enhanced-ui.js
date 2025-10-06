// Enhanced UI JavaScript
// This file contains all the enhanced UI functionality

// Enhanced file upload with drag and drop
const fileDropZone = document.getElementById('fileDropZone');
const fileInput = document.getElementById('fileInput');
const currentFileInfo = document.getElementById('currentFileInfo');
const currentFile = document.getElementById('currentFile');

// Drag and drop handlers
if (fileDropZone) {
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    fileDropZone.addEventListener(eventName, preventDefaults, false);
  });
}

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

if (fileDropZone) {
  ['dragenter', 'dragover'].forEach(eventName => {
    fileDropZone.addEventListener(eventName, highlight, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    fileDropZone.addEventListener(eventName, unhighlight, false);
  });
}

function highlight(e) {
  fileDropZone.classList.add('dragover');
}

function unhighlight(e) {
  fileDropZone.classList.remove('dragover');
}

if (fileDropZone) {
  fileDropZone.addEventListener('drop', handleDrop, false);
}

function handleDrop(e) {
  const dt = e.dataTransfer;
  const files = dt.files;
  handleFiles(files);
}

if (fileInput) {
  fileInput.addEventListener('change', function() {
    handleFiles(this.files);
  });
}

async function handleFiles(files) {
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

    // Handle file upload
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      TagManager.setLoading(true);
      
      // Clear UI state immediately when upload starts
      if (typeof TagManager !== 'undefined' && TagManager.clearUIStateForNewFile) {
        TagManager.clearUIStateForNewFile(true); // Preserve filters during upload
      }
      
      const response = await fetch('/upload', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      
      if (response.ok) {
        // File uploaded successfully, now poll for processing status
        const filename = data.filename;
        console.log(`File uploaded: ${filename}, polling for processing status...`);
        console.log('Upload response data:', data);
        
        // Update splash screen status
        if (typeof TagManager !== 'undefined' && TagManager.updateExcelLoadingStatus) {
          TagManager.updateExcelLoadingStatus('Processing file...');
        }
        
        // Start polling for upload status
        pollUploadStatus(filename);
        
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
      } else {
        // Hide splash screen on error
        if (typeof TagManager !== 'undefined' && TagManager.hideExcelLoadingSplash) {
          TagManager.hideExcelLoadingSplash();
        }
        showToast("error", data.error || 'Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      // Hide splash screen on error
      if (typeof TagManager !== 'undefined' && TagManager.hideExcelLoadingSplash) {
        TagManager.hideExcelLoadingSplash();
      }
      showToast("error", 'Upload failed');
    } finally {
      TagManager.setLoading(false);
    }
  }
}

// Add smooth scrolling
document.querySelectorAll('.tag-list-container').forEach(container => {
  container.addEventListener('wheel', (e) => {
    e.preventDefault();
    container.scrollTop += e.deltaY * 0.5;
  });
});

// Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey || e.metaKey) {
    switch(e.key) {
      case 'g':
        e.preventDefault();
        document.getElementById('generateBtn').click();
        break;
      case 'z':
        e.preventDefault();
        document.getElementById('undo-move-btn').click();
        break;
      case 'h':
        e.preventDefault();
        document.getElementById('help-btn').click();
        break;
    }
  }
});

// Initialize tooltips
const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl);
});

// Page load animations
window.addEventListener('DOMContentLoaded', function() {
  window.scrollTo(0, 0);
  
  // Add staggered fade-in animation
  document.querySelectorAll('.fade-in').forEach((el, index) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    setTimeout(() => {
      el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      el.style.opacity = '1';
      el.style.transform = 'translateY(0)';
    }, index * 100);
  });
});

// Enhanced button click feedback
document.querySelectorAll('.btn').forEach(button => {
  button.addEventListener('click', function(e) {
    // Create ripple effect
    const ripple = document.createElement('span');
    const rect = this.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple');
    
    this.appendChild(ripple);
    
    setTimeout(() => {
      ripple.remove();
    }, 600);
  });
});

// Enhanced form control interactions
document.querySelectorAll('.form-control-modern, .form-select-modern').forEach(control => {
  control.addEventListener('focus', function() {
    this.style.transform = 'translateY(-1px)';
  });
  
  control.addEventListener('blur', function() {
    this.style.transform = 'translateY(0)';
  });
});

// Enhanced tag item interactions
document.querySelectorAll('.tag-item').forEach(tag => {
  tag.addEventListener('mouseenter', function() {
    this.style.transform = 'translateY(-1px)';
  });
  
  tag.addEventListener('mouseleave', function() {
    this.style.transform = 'translateY(0)';
  });
});

// Auto-upload functionality
// Auto upload check functionality removed

// Auto upload check functionality removed

// Enhanced modal animations
const modals = document.querySelectorAll('.modal');
modals.forEach(modal => {
  modal.addEventListener('show.bs.modal', function() {
    // Store the currently focused element before opening modal
    const activeElement = document.activeElement;
    if (activeElement && !modal.contains(activeElement)) {
      activeElement.setAttribute('data-bs-focus-prev', 'true');
    }
    
    this.style.opacity = '0';
    setTimeout(() => {
      this.style.transition = 'opacity 0.3s ease';
      this.style.opacity = '1';
    }, 10);
  });
  
  modal.addEventListener('shown.bs.modal', function() {
    // Remove aria-hidden when modal is fully shown
    this.removeAttribute('aria-hidden');
  });
  
  modal.addEventListener('hidden.bs.modal', function() {
    // Use inert attribute instead of aria-hidden for better accessibility
    this.setAttribute('inert', '');
    this.removeAttribute('aria-hidden');
    
    // Ensure focus is moved outside the modal
    const previouslyFocusedElement = document.querySelector('[data-bs-focus-prev]');
    if (previouslyFocusedElement) {
      previouslyFocusedElement.focus();
      previouslyFocusedElement.removeAttribute('data-bs-focus-prev');
    }
    
    console.log('Modal hidden with accessibility fix:', this.id);
  });
});

// Poll upload status and update UI when processing is complete
function pollUploadStatus(filename) {
  let pollCount = 0;
  const maxPolls = 120; // Poll for up to 2 minutes (120 * 1 second)
  
  const poll = async () => {
    try {
      const response = await fetch(`/api/upload-status?filename=${encodeURIComponent(filename)}`);
      const data = await response.json();
      
      console.log(`Upload status for ${filename}: ${data.status}`);
      console.log('Upload status response:', data);
      
      if (data.status === 'ready') {
        // File processing is complete, fetch updated data
        console.log(`File processing complete for ${filename}, fetching updated data...`);
        
        // Clear any existing UI state to ensure fresh start
        if (typeof TagManager !== 'undefined') {
          // Use the new comprehensive UI clearing function
          TagManager.clearUIStateForNewFile(true); // Preserve filters during UI refresh
        }
        
        console.log('File processing complete, updating UI...');

        // Fetch all updated data in parallel to avoid serial bottlenecks
        console.time('post-ready-data-fetch');
        await Promise.all([
          // Available tags
          (async () => {
            console.log('Fetching available tags...');
            const res = await TagManager.fetchAndUpdateAvailableTags();
            console.log('Available tags result:', res);
          })(),
          // Selected tags
          (async () => {
            console.log('Fetching selected tags...');
            const res = await TagManager.fetchAndUpdateSelectedTags();
            console.log('Selected tags result:', res);
          })(),
          // Filter options
          (async () => {
            console.log('Fetching filter options...');
            await TagManager.fetchAndPopulateFilters();
            console.log('Filter options updated');
          })()
        ]);
        console.timeEnd('post-ready-data-fetch');
        
        // Hide splash screen on success
        if (typeof TagManager !== 'undefined' && TagManager.hideExcelLoadingSplash) {
          TagManager.hideExcelLoadingSplash();
        }
        
        // Show success message
        showToast('success', `File "${filename}" loaded successfully!`);
        
        return; // Stop polling
      } else if (data.status === 'error') {
        // Processing failed
        console.error(`File processing failed for ${filename}: ${data.error || 'Unknown error'}`);
        
        // Hide splash screen on error
        if (typeof TagManager !== 'undefined' && TagManager.hideExcelLoadingSplash) {
          TagManager.hideExcelLoadingSplash();
        }
        
        showToast('error', `File processing failed: ${data.error || 'Unknown error'}`);
        return; // Stop polling
      } else if (data.status === 'processing') {
        // Still processing, continue polling
        pollCount++;
        
        // Update splash screen status with progress
        if (typeof TagManager !== 'undefined' && TagManager.updateExcelLoadingStatus) {
          const progressPercent = Math.min((pollCount / maxPolls) * 100, 95);
          // Remove numeric percent from splash per request; keep animated dots
          TagManager.updateExcelLoadingStatus('Processing file...');
        }
        
        if (pollCount >= maxPolls) {
          console.error(`File processing timeout for ${filename} after ${maxPolls} polls`);
          
          // Hide splash screen on timeout
          if (typeof TagManager !== 'undefined' && TagManager.hideExcelLoadingSplash) {
            TagManager.hideExcelLoadingSplash();
          }
          
          showToast('error', `File processing timeout. Please try again.`);
          return; // Stop polling
        }
        
        // Continue polling in 1 second for faster response
        setTimeout(poll, 1000);
      } else if (data.status === 'not_found') {
        // File not found in processing status - check if it exists
        console.warn(`File not found in processing status: ${filename}`);
        console.log('Upload status details:', data);
        
        if (data.file_exists) {
          // File exists but status was cleared - treat as ready
          console.log(`File ${filename} exists but status was cleared - treating as ready`);
          showToast('success', `File "${filename}" loaded successfully!`);
          return; // Stop polling
        } else {
          // File doesn't exist - stop polling
          console.error(`File ${filename} does not exist in uploads directory`);
          
          // Hide splash screen on file not found
          if (typeof TagManager !== 'undefined' && TagManager.hideExcelLoadingSplash) {
            TagManager.hideExcelLoadingSplash();
          }
          
          showToast('error', `File "${filename}" not found. Please upload again.`);
          return; // Stop polling
        }
      } else {
        // Unknown status
        console.warn(`Unknown upload status for ${filename}: ${data.status}`);
        pollCount++;
        if (pollCount >= maxPolls) {
          // Hide splash screen on unknown status timeout
          if (typeof TagManager !== 'undefined' && TagManager.hideExcelLoadingSplash) {
            TagManager.hideExcelLoadingSplash();
          }
          
          showToast('error', `File processing failed: Unknown status`);
          return; // Stop polling
        }
        
        // Continue polling in 1 second for faster response
        setTimeout(poll, 1000);
      }
    } catch (error) {
      console.error(`Error polling upload status for ${filename}:`, error);
      pollCount++;
      if (pollCount >= maxPolls) {
        // Hide splash screen on network error timeout
        if (typeof TagManager !== 'undefined' && TagManager.hideExcelLoadingSplash) {
          TagManager.hideExcelLoadingSplash();
        }
        
        showToast('error', `File processing failed: Network error`);
        return; // Stop polling
      }
      
      // Continue polling in 1 second for faster response
      setTimeout(poll, 1000);
    }
  };
  
  // Start polling
  poll();
}

// Add hover sound effects (optional - requires adding audio files)
function addHoverSound() {
  const hoverSound = new Audio('/static/sounds/hover.mp3');
  hoverSound.volume = 0.1;
  
  document.querySelectorAll('.btn, .tag-item').forEach(element => {
    element.addEventListener('mouseenter', () => {
      hoverSound.currentTime = 0;
      hoverSound.play().catch(() => {});
    });
  });
}

// Particle effect on button clicks (optional)
function createParticles(x, y) {
  const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c'];
  
  for (let i = 0; i < 10; i++) {
    const particle = document.createElement('div');
    particle.style.position = 'fixed';
    particle.style.left = x + 'px';
    particle.style.top = y + 'px';
    particle.style.width = '5px';
    particle.style.height = '5px';
    particle.style.background = colors[Math.floor(Math.random() * colors.length)];
    particle.style.borderRadius = '50%';
    particle.style.pointerEvents = 'none';
    particle.style.zIndex = '9999';
    
    const angle = (Math.PI * 2 * i) / 10;
    const velocity = 2 + Math.random() * 2;
    const vx = Math.cos(angle) * velocity;
    const vy = Math.sin(angle) * velocity;
    
    document.body.appendChild(particle);
    
    let opacity = 1;
    const animate = () => {
      particle.style.left = (parseFloat(particle.style.left) + vx) + 'px';
      particle.style.top = (parseFloat(particle.style.top) + vy) + 'px';
      opacity -= 0.02;
      particle.style.opacity = opacity;
      
      if (opacity > 0) {
        requestAnimationFrame(animate);
      } else {
        particle.remove();
      }
    };
    
    requestAnimationFrame(animate);
  }
}

// Add particle effect to important buttons
document.getElementById('generateBtn')?.addEventListener('click', function(e) {
  createParticles(e.clientX, e.clientY);
});

// Auto-save functionality indicator
let autoSaveTimer;
function showAutoSave() {
  const indicator = document.createElement('div');
  indicator.className = 'auto-save-indicator';
  indicator.textContent = 'Auto-saved';
  indicator.style.cssText = `
    position: fixed;
    bottom: 20px;
    left: 20px;
    background: var(--glass-bg);
    backdrop-filter: blur(10px);
    border: 1px solid var(--glass-border);
    padding: 10px 20px;
    border-radius: 8px;
    color: #4facfe;
    font-weight: 600;
    opacity: 0;
    transition: opacity 0.3s ease;
    z-index: 1000;
  `;
  
  document.body.appendChild(indicator);
  
  setTimeout(() => {
    indicator.style.opacity = '1';
  }, 10);
  
  setTimeout(() => {
    indicator.style.opacity = '0';
    setTimeout(() => {
      indicator.remove();
    }, 300);
  }, 2000);
}

// Dynamic background based on time of day (optional)
function setDynamicBackground() {
  const hour = new Date().getHours();
  const body = document.body;
  
  if (hour >= 6 && hour < 12) {
    // Morning
    body.style.setProperty('--bg-gradient', 'linear-gradient(-45deg, #0a0a0a, #1a0033, #330066, #4d0080)');
  } else if (hour >= 12 && hour < 18) {
    // Afternoon
    body.style.setProperty('--bg-gradient', 'linear-gradient(-45deg, #0a0a0a, #1a0033, #4d0033, #660033)');
  } else {
    // Evening/Night
    body.style.setProperty('--bg-gradient', 'linear-gradient(-45deg, #0a0a0a, #0a0a1a, #1a0a2a, #2a0a3a)');
  }
}

// Initialize enhanced features
document.addEventListener('DOMContentLoaded', function() {
  // Optional: Enable hover sounds
  // addHoverSound();
  
  // Optional: Set dynamic background
  // setDynamicBackground();
  
  // Welcome animation removed - redundant with splash screen
});

// Toast notification function
function showToast(type, message) {
    const toastEl = document.createElement('div');
    toastEl.className = `toast toast-modern ${type} show`;
    toastEl.setAttribute('role', 'alert');
    toastEl.innerHTML = `
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    const container = document.getElementById('toast-container') || (() => {
        const cont = document.createElement('div');
        cont.id = 'toast-container';
        cont.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 1050;';
        document.body.appendChild(cont);
        return cont;
    })();
    
    container.appendChild(toastEl);
    
    setTimeout(() => {
        toastEl.remove();
    }, 3000);
}

