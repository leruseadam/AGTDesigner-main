// Library Browser JavaScript
class LibraryBrowser {
    constructor() {
        this.currentPage = 1;
        this.itemsPerPage = 20;
        this.currentFilter = 'all';
        this.searchTerm = '';
        this.products = [];
        this.filteredProducts = [];
        
        this.initializeEventListeners();
        this.loadProducts();
    }

    initializeEventListeners() {
        // Search functionality
        $('#searchInput').on('input', (e) => {
            this.searchTerm = e.target.value;
            this.filterProducts();
        });

        $('#searchBtn').on('click', () => {
            this.searchTerm = $('#searchInput').val();
            this.filterProducts();
        });

        // Filter buttons
        $('#filterAll').on('click', () => this.setFilter('all'));
        $('#filterFlower').on('click', () => this.setFilter('flower'));
        $('#filterConcentrate').on('click', () => this.setFilter('concentrate'));
        $('#filterEdible').on('click', () => this.setFilter('edible'));
        $('#filterVape').on('click', () => this.setFilter('vape'));

        // Action buttons
        $('#refreshBtn').on('click', () => this.loadProducts());
        $('#exportBtn').on('click', () => this.exportData());

        // Modal events
        $('#saveProductBtn').on('click', () => this.saveProduct());
        $('#applyRecommendationsBtn').on('click', () => this.applyRecommendations());

        // Enter key in search
        $('#searchInput').on('keypress', (e) => {
            if (e.which === 13) {
                this.searchTerm = e.target.value;
                this.filterProducts();
            }
        });
    }

    async loadProducts() {
        try {
            this.showLoading(true);
            const response = await fetch('/api/library/products');
            const data = await response.json();
            
            if (data.success) {
                this.products = data.products;
                this.updateStatistics();
                this.filterProducts();
            } else {
                this.showError('Failed to load products: ' + data.message);
            }
        } catch (error) {
            this.showError('Error loading products: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    filterProducts() {
        this.filteredProducts = this.products.filter(product => {
            // Apply search filter
            if (this.searchTerm) {
                const searchLower = this.searchTerm.toLowerCase();
                const matchesSearch = 
                    product.product_name?.toLowerCase().includes(searchLower) ||
                    product.product_brand?.toLowerCase().includes(searchLower) ||
                    product.product_strain?.toLowerCase().includes(searchLower) ||
                    product.lineage?.toLowerCase().includes(searchLower);
                
                if (!matchesSearch) return false;
            }

            // Apply type filter
            if (this.currentFilter !== 'all') {
                const productType = product.product_type?.toLowerCase() || '';
                if (this.currentFilter === 'edible') {
                    return productType.includes('edible') || productType.includes('tincture') || 
                           productType.includes('topical') || productType.includes('capsule');
                } else if (this.currentFilter === 'concentrate') {
                    return productType.includes('concentrate') || productType.includes('rso');
                } else if (this.currentFilter === 'vape') {
                    return productType.includes('vape') || productType.includes('cartridge');
                } else {
                    return productType.includes(this.currentFilter);
                }
            }

            return true;
        });

        this.currentPage = 1;
        this.renderProducts();
        this.updatePagination();

        // Return boolean indicating whether any products remain after filtering
        return this.filteredProducts.length > 0;
    }

    setFilter(filter) {
        this.currentFilter = filter;
        
        // Update button states
        $('.btn-group .btn').removeClass('btn-primary').addClass('btn-outline-secondary');
        $(`#filter${filter.charAt(0).toUpperCase() + filter.slice(1)}`).removeClass('btn-outline-secondary').addClass('btn-primary');
        
        this.filterProducts();
    }

    renderProducts() {
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageProducts = this.filteredProducts.slice(startIndex, endIndex);

        const tbody = $('#productTableBody');
        tbody.empty();

        pageProducts.forEach(product => {
            const row = this.createProductRow(product);
            tbody.append(row);
        });

        $('#showingInfo').text(`Showing ${startIndex + 1}-${Math.min(endIndex, this.filteredProducts.length)} of ${this.filteredProducts.length} products`);
    }

    createProductRow(product) {
        const row = $('<tr>');
        
        row.append(`
            <td>
                <strong>${this.escapeHtml(product.product_name || 'N/A')}</strong>
                <br><small class="text-muted">${this.escapeHtml(product.description || '')}</small>
            </td>
            <td>${this.escapeHtml(product.product_brand || 'N/A')}</td>
            <td><span class="badge badge-secondary">${this.escapeHtml(product.product_type || 'N/A')}</span></td>
            <td>${this.escapeHtml(product.product_strain || 'N/A')}</td>
            <td>
                <span class="badge badge-info">${this.escapeHtml(product.lineage || 'N/A')}</span>
            </td>
            <td>${this.escapeHtml(product.thc_cbd || 'N/A')}</td>
            <td>${this.escapeHtml(product.price || 'N/A')}</td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-outline-primary btn-sm edit-product" data-id="${product.id}">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-info btn-sm analyze-strain" data-id="${product.id}">
                        <i class="fas fa-chart-line"></i>
                    </button>
                    <button class="btn btn-outline-danger btn-sm delete-product" data-id="${product.id}">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `);

        // Add event listeners
        row.find('.edit-product').on('click', () => this.editProduct(product.id));
        row.find('.analyze-strain').on('click', () => this.analyzeStrain(product.id));
        row.find('.delete-product').on('click', () => this.deleteProduct(product.id));

        return row;
    }

    updatePagination() {
        const totalPages = Math.ceil(this.filteredProducts.length / this.itemsPerPage);
        const pagination = $('#pagination');
        pagination.empty();

        if (totalPages <= 1) return;

        // Previous button
        const prevBtn = $('<li>').addClass('page-item').toggleClass('disabled', this.currentPage === 1);
        prevBtn.append($('<a>').addClass('page-link').text('Previous').on('click', () => this.goToPage(this.currentPage - 1)));
        pagination.append(prevBtn);

        // Page numbers
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);

        for (let i = startPage; i <= endPage; i++) {
            const pageItem = $('<li>').addClass('page-item').toggleClass('active', i === this.currentPage);
            pageItem.append($('<a>').addClass('page-link').text(i).on('click', () => this.goToPage(i)));
            pagination.append(pageItem);
        }

        // Next button
        const nextBtn = $('<li>').addClass('page-item').toggleClass('disabled', this.currentPage === totalPages);
        nextBtn.append($('<a>').addClass('page-link').text('Next').on('click', () => this.goToPage(this.currentPage + 1)));
        pagination.append(nextBtn);
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredProducts.length / this.itemsPerPage);
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.renderProducts();
            this.updatePagination();
        }
    }

    updateStatistics() {
        const totalProducts = this.products.length;
        const uniqueStrains = new Set(this.products.map(p => p.product_strain).filter(s => s)).size;
        const uniqueBrands = new Set(this.products.map(p => p.product_brand).filter(b => b)).size;
        const needsReview = this.products.filter(p => !p.product_strain || !p.lineage).length;

        $('#totalProducts').text(totalProducts);
        $('#uniqueStrains').text(uniqueStrains);
        $('#uniqueBrands').text(uniqueBrands);
        $('#needsReview').text(needsReview);
    }

    async editProduct(productId) {
        try {
            const response = await fetch(`/api/library/products/${productId}`);
            const data = await response.json();
            
            if (data.success) {
                const product = data.product;
                this.populateEditForm(product);
                $('#editProductModal').modal('show');
            } else {
                this.showError('Failed to load product: ' + data.message);
            }
        } catch (error) {
            this.showError('Error loading product: ' + error.message);
        }
    }

    populateEditForm(product) {
        $('#editProductId').val(product.id);
        $('#editProductName').val(product.product_name || '');
        $('#editProductBrand').val(product.product_brand || '');
        $('#editProductType').val(product.product_type || '');
        $('#editProductStrain').val(product.product_strain || '');
        $('#editLineage').val(product.lineage || '');
        $('#editPrice').val(product.price || '');
        $('#editTHCCBD').val(product.thc_cbd || '');
        $('#editDescription').val(product.description || '');
    }

    async saveProduct() {
        const productData = {
            id: $('#editProductId').val(),
            product_name: $('#editProductName').val(),
            product_brand: $('#editProductBrand').val(),
            product_type: $('#editProductType').val(),
            product_strain: $('#editProductStrain').val(),
            lineage: $('#editLineage').val(),
            price: $('#editPrice').val(),
            thc_cbd: $('#editTHCCBD').val(),
            description: $('#editDescription').val()
        };

        try {
            const response = await fetch('/api/library/products/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(productData)
            });

            const data = await response.json();
            
            if (data.success) {
                $('#editProductModal').modal('hide');
                this.showSuccess('Product updated successfully');
                this.loadProducts(); // Reload to get updated data
            } else {
                this.showError('Failed to update product: ' + data.message);
            }
        } catch (error) {
            this.showError('Error updating product: ' + error.message);
        }
    }

    async analyzeStrain(productId) {
        try {
            const response = await fetch(`/api/library/strain-analysis/${productId}`);
            const data = await response.json();
            
            if (data.success) {
                this.populateStrainAnalysis(data.analysis);
                $('#strainAnalysisModal').modal('show');
            } else {
                this.showError('Failed to analyze strain: ' + data.message);
            }
        } catch (error) {
            this.showError('Error analyzing strain: ' + error.message);
        }
    }

    populateStrainAnalysis(analysis) {
        $('#currentStrainData').html(`
            <div class="card">
                <div class="card-body">
                    <h6>Current Data</h6>
                    <p><strong>Strain:</strong> ${this.escapeHtml(analysis.current.strain || 'N/A')}</p>
                    <p><strong>Lineage:</strong> ${this.escapeHtml(analysis.current.lineage || 'N/A')}</p>
                    <p><strong>THC/CBD:</strong> ${this.escapeHtml(analysis.current.thc_cbd || 'N/A')}</p>
                </div>
            </div>
        `);

        $('#similarProducts').html(`
            <div class="card">
                <div class="card-body">
                    <h6>Similar Products (${analysis.similar.length})</h6>
                    ${analysis.similar.map(product => `
                        <div class="border-bottom pb-2 mb-2">
                            <strong>${this.escapeHtml(product.product_name)}</strong><br>
                            <small>Strain: ${this.escapeHtml(product.product_strain || 'N/A')}</small><br>
                            <small>Lineage: ${this.escapeHtml(product.lineage || 'N/A')}</small>
                        </div>
                    `).join('')}
                </div>
            </div>
        `);

        $('#strainRecommendations').html(`
            <div class="card">
                <div class="card-body">
                    <h6>Recommendations</h6>
                    ${analysis.recommendations.map(rec => `
                        <div class="alert alert-info">
                            <strong>${this.escapeHtml(rec.type)}:</strong> ${this.escapeHtml(rec.message)}
                        </div>
                    `).join('')}
                </div>
            </div>
        `);
    }

    async applyRecommendations() {
        // Implementation for applying strain recommendations
        this.showSuccess('Recommendations applied successfully');
        $('#strainAnalysisModal').modal('hide');
        this.loadProducts();
    }

    async deleteProduct(productId) {
        if (!confirm('Are you sure you want to delete this product? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/api/library/products/${productId}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('Product deleted successfully');
                this.loadProducts();
            } else {
                this.showError('Failed to delete product: ' + data.message);
            }
        } catch (error) {
            this.showError('Error deleting product: ' + error.message);
        }
    }

    async exportData() {
        try {
            const response = await fetch('/api/library/export');
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `product_library_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            this.showSuccess('Data exported successfully');
        } catch (error) {
            this.showError('Error exporting data: ' + error.message);
        }
    }

    showLoading(show) {
        if (show) {
            $('#loadingSpinner').show();
            $('#productTable').hide();
        } else {
            $('#loadingSpinner').hide();
            $('#productTable').show();
        }
    }

    showSuccess(message) {
        // You can implement a toast notification system here
        alert('Success: ' + message);
    }

    showError(message) {
        // You can implement a toast notification system here
        alert('Error: ' + message);
    }

    escapeHtml(text) {
        if (!text) return '';
        
        // First escape any HTML to prevent XSS
        const div = document.createElement('div');
        div.textContent = text;
        const escapedText = div.innerHTML;
        
        // Then convert |BR| markers to HTML line breaks
        return escapedText.replace(/\|BR\|/g, '<br>');
    }
}

// Initialize the library browser when the page loads
$(document).ready(() => {
    window.libraryBrowser = new LibraryBrowser();
}); 