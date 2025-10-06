// Database synchronization and analytics functions

async function openDatabaseAnalytics() {
  console.log('Opening database analytics...');
  
  // Show loading state
  const loadingHtml = `
    <div class="text-center">
      <div class="spinner-border text-info" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-3">Loading database analytics...</p>
    </div>
  `;
  showDatabaseModal('Database Analytics', loadingHtml);
  
  try {
    // Fetch all required data in parallel
    const [healthResponse, statsResponse, vendorStatsResponse, analyticsResponse] = await Promise.all([
      fetch('/api/database-health'),
      fetch('/api/database-stats'),
      fetch('/api/database-vendor-stats'),
      fetch('/api/database-analytics')
    ]);
    
    const health = await healthResponse.json();
    const stats = await statsResponse.json();
    const vendorStats = await vendorStatsResponse.json();
    const analytics = await analyticsResponse.json();
    
    // Create health status indicator
    const healthColor = health.status === 'healthy' ? 'success' : 
                       health.status === 'warning' ? 'warning' : 'danger';
    const healthIcon = health.status === 'healthy' ? 'check-circle' : 
                      health.status === 'warning' ? 'exclamation-circle' : 'x-circle';
                      
    const healthHtml = `
      <div class="row mb-4">
        <div class="col-md-6">
          <div class="card glass-card">
            <div class="card-body text-center">
              <div class="d-flex align-items-center justify-content-center mb-3">
                <i class="bi bi-${healthIcon} text-${healthColor} fs-1"></i>
              </div>
              <h3 class="text-${healthColor}">${health.health_score}%</h3>
              <p class="mb-0">Database Health</p>
              <div class="mt-3">
                <small class="text-muted">
                  Size: ${health.metrics ? `${health.metrics.database_size_mb.toFixed(1)} MB` : 'N/A'}<br>
                  Memory: ${health.metrics ? `${health.metrics.memory_usage_mb.toFixed(1)} MB` : 'N/A'}
                </small>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card glass-card">
            <div class="card-body">
              <h6 class="mb-3">Recent Activity</h6>
              <div class="d-flex justify-content-between align-items-center mb-2">
                <span>New Products (24h)</span>
                <span class="badge bg-primary">${health.metrics ? health.metrics.products_last_24h : 'N/A'}</span>
              </div>
              <div class="d-flex justify-content-between align-items-center mb-2">
                <span>Total Products</span>
                <span class="badge bg-success">${health.metrics ? health.metrics.total_products : 'N/A'}</span>
              </div>
              <div class="d-flex justify-content-between align-items-center">
                <span>Total Strains</span>
                <span class="badge bg-info">${health.metrics ? health.metrics.total_strains : 'N/A'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    // Create vendor statistics section
    const vendorStatsHtml = `
      <div class="row mb-4">
        <div class="col-md-6">
          <div class="card glass-card">
            <div class="card-header">
              <h6 class="mb-0">All Vendors (${vendorStats.vendors ? vendorStats.vendors.length : 0})</h6>
            </div>
            <div class="card-body" style="max-height: 300px; overflow-y: auto;">
              ${vendorStats.vendors && vendorStats.vendors.length > 0 ? 
                vendorStats.vendors.map((vendor, index) => 
                  `<div class="d-flex justify-content-between align-items-center py-2 ${index < vendorStats.vendors.length - 1 ? 'border-bottom' : ''}">
                    <div>
                      <strong>${vendor.vendor || 'Unknown'}</strong>
                      <small class="text-muted d-block">${vendor.unique_brands || 0} brands, ${vendor.unique_product_types || 0} types</small>
                    </div>
                    <span class="badge bg-primary">${vendor.product_count || 0}</span>
                  </div>`
                ).join('') : 
                '<p class="text-muted">No vendor data available. Upload Excel files to see vendor statistics.</p>'
              }
            </div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="card glass-card">
            <div class="card-header">
              <h6 class="mb-0">All Product Types (${vendorStats.product_types ? vendorStats.product_types.length : 0})</h6>
            </div>
            <div class="card-body" style="max-height: 300px; overflow-y: auto;">
              ${vendorStats.product_types && vendorStats.product_types.length > 0 ? 
                vendorStats.product_types.map((type, index) => 
                  `<div class="d-flex justify-content-between align-items-center py-2 ${index < vendorStats.product_types.length - 1 ? 'border-bottom' : ''}">
                    <div>
                      <strong>${type.product_type || 'Unknown'}</strong>
                      <small class="text-muted d-block">${type.unique_vendors || 0} vendors, ${type.unique_brands || 0} brands</small>
                    </div>
                    <span class="badge bg-success">${type.product_count || 0}</span>
                  </div>`
                ).join('') : 
                '<p class="text-muted">No product type data available. Upload Excel files to see product analytics.</p>'
              }
            </div>
          </div>
        </div>
      </div>
    `;

    // Create daily usage graph section
    const vendorBrandsHtml = `
      <div class="row">
        <div class="col-12">
          <div class="card glass-card">
            <div class="card-header">
              <h6 class="mb-0">Daily App Usage</h6>
            </div>
            <div class="card-body">
              <div style="height: 250px;">
                <canvas id="usageChart"></canvas>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    // Create summary section
    const summaryHtml = `
      <div class="row mt-4">
        <div class="col-12">
          <div class="alert alert-info">
            <h6>Analytics Summary</h6>
            <p class="mb-0">
              ${health.metrics && health.metrics.total_products > 0 ? 
                `This comprehensive dashboard shows real-time statistics from your product database with ${health.metrics.total_products} products currently loaded. Data is automatically updated each time you upload new Excel files.` :
                'Upload Excel files to populate the database and unlock detailed vendor analytics, strain statistics, and performance metrics.'
              }
            </p>
            ${stats.error || vendorStats.error || analytics.error ? 
              `<small class="text-warning d-block mt-2">Some data may be limited due to: ${[stats.error, vendorStats.error, analytics.error].filter(e => e).join(', ')}</small>` : 
              ''
            }
          </div>
        </div>
      </div>
    `;

    // Add export button
    const exportButtonHtml = `
      <div class="row mt-4">
        <div class="col-12 text-end">
          <button class="btn btn-primary" onclick="exportDatabase()">
            <i class="bi bi-download"></i> Export Database
          </button>
        </div>
      </div>
    `;

    // Combine all sections
    const modalContent = `
      ${healthHtml}
      ${vendorStatsHtml}
      ${vendorBrandsHtml}
      ${summaryHtml}
      ${exportButtonHtml}
    `;

    // Update modal content
    showDatabaseModal('Database Analytics', modalContent);
    
    // Initialize the usage chart after the modal is shown
    const modal = document.getElementById('databaseModal');
    modal.addEventListener('shown.bs.modal', function () {
      // Get historical usage data - handle case where upload_stats might not exist
      const usageData = (window.upload_stats && window.upload_stats.historical) ? window.upload_stats.historical : [];
      
      // Only create chart if we have valid data
      if (usageData && usageData.length > 0) {
        const dates = usageData.map(d => new Date(d.date).toLocaleDateString());

        const ctx = document.getElementById('usageChart').getContext('2d');
        new Chart(ctx, {
        type: 'line',
        data: {
          labels: dates,
          datasets: [
            {
              label: 'File Uploads',
              data: usageData.map(d => d.ready_files),
              borderColor: 'rgba(75, 192, 192, 1)',
              tension: 0.4,
              fill: false
            },
            {
              label: 'Products Added',
              data: usageData.map(d => d.total_files),
              borderColor: 'rgba(54, 162, 235, 1)',
              tension: 0.4,
              fill: false
            },
            {
              label: 'Memory Usage (MB)',
              data: usageData.map(d => d.memory_usage_mb),
              borderColor: 'rgba(255, 99, 132, 1)',
              tension: 0.4,
              fill: false
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top',
              labels: {
                color: 'rgba(255, 255, 255, 0.8)'
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              grid: {
                color: 'rgba(255, 255, 255, 0.1)'
              },
              ticks: {
                color: 'rgba(255, 255, 255, 0.8)'
              }
            },
            x: {
              grid: {
                color: 'rgba(255, 255, 255, 0.1)'
              },
              ticks: {
                color: 'rgba(255, 255, 255, 0.8)'
              }
            }
          }
        }
      });
        } else {
          // No historical data available
          const chartContainer = document.getElementById('usageChart');
          if (chartContainer) {
            chartContainer.innerHTML = '<div class="text-center text-muted p-4">No historical usage data available</div>';
          }
        }
      });

  } catch (error) {
    console.error('Error loading database analytics:', error);
    showDatabaseModal('Database Analytics', `
      <div class="alert alert-danger">
        <h6>Error Loading Analytics</h6>
        <p class="mb-0">Failed to load database analytics: ${error.message}</p>
      </div>
    `);
  }
}

async function exportDatabase() {
  // Show splash screen
  showExportSplash();
  
  try {
    const response = await fetch('/api/database-export');
    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }
    
    // Get the filename from the Content-Disposition header
    const contentDisposition = response.headers.get('Content-Disposition');
    const filenameMatch = contentDisposition && contentDisposition.match(/filename="(.+)"/);
    const filename = filenameMatch ? filenameMatch[1] : 'product_database_export.xlsx';
    
    // Create a blob from the response
    const blob = await response.blob();
    
    // Create a download link and trigger it
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
    
    // Hide splash screen and show success message
    hideExportSplash();
    const successToast = new bootstrap.Toast(document.getElementById('successToast'));
    document.getElementById('successToastMessage').textContent = 'Database exported successfully';
    successToast.show();
    
  } catch (error) {
    console.error('Error exporting database:', error);
    hideExportSplash();
    const errorToast = new bootstrap.Toast(document.getElementById('errorToast'));
    document.getElementById('errorToastMessage').textContent = `Failed to export database: ${error.message}`;
    errorToast.show();
  }
}

function showExportSplash() {
  // Create splash screen HTML
  const splashHtml = `
    <div id="exportSplash" class="export-splash-overlay">
      <div class="export-splash-content">
        <div class="export-splash-icon">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
        </div>
        <h4 class="export-splash-title">Exporting Database</h4>
        <p class="export-splash-message">Preparing your database export...</p>
        <div class="export-splash-progress">
          <div class="progress">
            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                 role="progressbar" style="width: 0%"></div>
          </div>
        </div>
      </div>
    </div>
  `;
  
  // Add to body
  document.body.insertAdjacentHTML('beforeend', splashHtml);
  
  // Animate progress bar
  const progressBar = document.querySelector('#exportSplash .progress-bar');
  let progress = 0;
  const interval = setInterval(() => {
    progress += Math.random() * 15;
    if (progress > 90) progress = 90;
    progressBar.style.width = progress + '%';
  }, 200);
  
  // Store interval ID for cleanup
  document.getElementById('exportSplash').dataset.intervalId = interval;
}

function hideExportSplash() {
  const splash = document.getElementById('exportSplash');
  if (splash) {
    // Clear progress animation
    const intervalId = splash.dataset.intervalId;
    if (intervalId) {
      clearInterval(parseInt(intervalId));
    }
    
    // Animate out
    splash.style.opacity = '0';
    splash.style.transform = 'scale(0.8)';
    
    setTimeout(() => {
      splash.remove();
    }, 300);
  }
}

// Helper function to show database modal
function showDatabaseModal(title, content) {
  const modal = document.getElementById('databaseModal');
  if (!modal) {
    console.error('Database modal element not found');
    return;
  }
  
  const modalTitle = modal.querySelector('.modal-title');
  const modalBody = modal.querySelector('.modal-body');
  
  if (modalTitle) modalTitle.textContent = title;
  if (modalBody) modalBody.innerHTML = content;
  
  const bsModal = new bootstrap.Modal(modal);
  bsModal.show();
}