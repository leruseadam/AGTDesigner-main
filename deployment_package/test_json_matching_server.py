#!/usr/bin/env python3
"""
Simple test server to test JSON matching improvements without database dependencies.
"""

from flask import Flask, request, jsonify, render_template_string
import sys
import os
import json
import logging
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
app.secret_key = 'test-key-for-json-matching'

# Configure logging
logging.basicConfig(level=logging.INFO)

# Mock Excel data for testing
MOCK_EXCEL_DATA = [
    {
        'Product Name*': 'Blue Dream Live Resin Cartridge - 1g',
        'Vendor/Supplier*': 'Dank Czar',
        'Product Type*': 'Vape Cartridge',
        'Strain*': 'Blue Dream',
        'Weight*': '1g'
    },
    {
        'Product Name*': 'Wedding Cake Sugar Wax - 1g',
        'Vendor/Supplier*': 'Dank Czar', 
        'Product Type*': 'Concentrate',
        'Strain*': 'Wedding Cake',
        'Weight*': '1g'
    },
    {
        'Product Name*': 'Purple Haze Flower - 3.5g',
        'Vendor/Supplier*': 'Lifted Cannabis',
        'Product Type*': 'Flower', 
        'Strain*': 'Purple Haze',
        'Weight*': '3.5g'
    },
    {
        'Product Name*': 'OG Kush Pre-Roll - 1g',
        'Vendor/Supplier*': 'Lifted Cannabis',
        'Product Type*': 'Pre-Roll',
        'Strain*': 'OG Kush', 
        'Weight*': '1g'
    },
    {
        'Product Name*': 'Gelato Rosin Cartridge - 0.5g',
        'Vendor/Supplier*': 'Omega Labs',
        'Product Type*': 'Vape Cartridge',
        'Strain*': 'Gelato',
        'Weight*': '0.5g'
    }
]

# Mock JSON data that would come from a typical cannabis inventory API
MOCK_JSON_DATA = [
    {
        'product_name': 'Blue Dream Live Resin Cart - 1g',
        'vendor': 'Dank Czar',
        'brand': 'Dank Czar',
        'strain_name': 'Blue Dream',
        'inventory_type': 'Concentrate for Inhalation',
        'weight': '1g'
    },
    {
        'product_name': 'Wedding Cake Sugar Wax 1g',
        'vendor': 'Dank Czar',
        'brand': 'Dank Czar', 
        'strain_name': 'Wedding Cake',
        'inventory_type': 'Concentrate',
        'weight': '1g'
    },
    {
        'product_name': 'Purple Haze Flower 3.5g',
        'vendor': 'Lifted Cannabis',
        'brand': 'Lifted Cannabis',
        'strain_name': 'Purple Haze',
        'inventory_type': 'Flower',
        'weight': '3.5g'
    },
    {
        'product_name': 'Random Unmatched Product',
        'vendor': 'Unknown Vendor',
        'brand': 'Unknown Brand',
        'strain_name': 'Unknown Strain',
        'inventory_type': 'Unknown',
        'weight': '1g'
    },
    {
        'product_name': 'Different Vendor Blue Dream',
        'vendor': 'Different Company',
        'brand': 'Different Company', 
        'strain_name': 'Blue Dream',
        'inventory_type': 'Concentrate for Inhalation',
        'weight': '1g'
    }
]

@app.route('/')
def index():
    """Serve the test page."""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>JSON Matching Test</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</head>
<body>
    <div class="container mt-5">
        <h1>🧪 JSON Matching Accuracy Test</h1>
        <p class="lead">Test the improved JSON matching with before/after comparisons</p>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>📋 Available Excel Data</h5>
                    </div>
                    <div class="card-body" style="max-height: 300px; overflow-y: auto;">
                        <div id="excelData">Loading...</div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>📥 Mock JSON Data</h5>
                    </div>
                    <div class="card-body" style="max-height: 300px; overflow-y: auto;">
                        <div id="jsonData">Loading...</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="text-center mt-4">
            <button class="btn btn-primary btn-lg" onclick="testDetailedMatching()">
                🔍 Test Detailed JSON Matching
            </button>
            <button class="btn btn-outline-secondary ms-2" onclick="testQuickMatching()">
                ⚡ Test Quick Matching
            </button>
        </div>
        
        <div id="results" class="mt-4" style="display: none;">
            <!-- Results will appear here -->
        </div>
    </div>

    <script>
    // Load mock data on page load
    window.addEventListener('DOMContentLoaded', function() {
        loadMockData();
    });
    
    function loadMockData() {
        // Load Excel data
        fetch('/api/excel-data')
            .then(r => r.json())
            .then(data => {
                const html = data.map(item => 
                    `<div class="border-bottom pb-2 mb-2">
                        <strong>${item['Product Name*']}</strong><br>
                        <small class="text-muted">
                            ${item['Vendor/Supplier*']} • ${item['Product Type*']} • ${item['Weight*']}
                        </small>
                    </div>`
                ).join('');
                document.getElementById('excelData').innerHTML = html;
            });
            
        // Load JSON data
        fetch('/api/json-data')
            .then(r => r.json())
            .then(data => {
                const html = data.map(item => 
                    `<div class="border-bottom pb-2 mb-2">
                        <strong>${item.product_name}</strong><br>
                        <small class="text-muted">
                            ${item.vendor} • ${item.inventory_type} • ${item.weight}
                        </small>
                    </div>`
                ).join('');
                document.getElementById('jsonData').innerHTML = html;
            });
    }
    
    function testDetailedMatching() {
        const resultsDiv = document.getElementById('results');
        resultsDiv.style.display = 'block';
        resultsDiv.innerHTML = '<div class="text-center"><div class="spinner-border"></div><p>Testing detailed matching...</p></div>';
        
        fetch('/api/json-match-detailed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: 'test' })
        })
        .then(r => r.json())
        .then(data => {
            displayDetailedResults(data);
        })
        .catch(err => {
            resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${err.message}</div>`;
        });
    }
    
    function testQuickMatching() {
        const resultsDiv = document.getElementById('results');
        resultsDiv.style.display = 'block';
        resultsDiv.innerHTML = '<div class="text-center"><div class="spinner-border"></div><p>Testing quick matching...</p></div>';
        
        fetch('/api/json-match', {
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: 'test' })
        })
        .then(r => r.json())
        .then(data => {
            resultsDiv.innerHTML = `
                <div class="alert alert-info">
                    <h5>Quick Match Results</h5>
                    <p><strong>Matches:</strong> ${data.matched_count}</p>
                    <p><strong>Threshold:</strong> 0.4 (40%)</p>
                    ${data.matched_names ? '<p><strong>Matched Products:</strong><br>' + data.matched_names.join('<br>') + '</p>' : ''}
                </div>
            `;
        })
        .catch(err => {
            resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${err.message}</div>`;
        });
    }
    
    function displayDetailedResults(data) {
        const resultsDiv = document.getElementById('results');
        
        let html = `
            <div class="alert alert-success">
                <h5>🎯 Detailed Match Results</h5>
                <div class="row">
                    <div class="col-6">
                        <strong>JSON Items:</strong> ${data.total_json_items}
                    </div>
                    <div class="col-6">
                        <strong>High Quality Matches:</strong> ${data.total_matches}
                    </div>
                </div>
                <small>Threshold: ${data.threshold} (${(data.threshold * 100)}%)</small>
            </div>
        `;
        
        data.detailed_matches.forEach((match, i) => {
            const statusClass = match.is_match ? 'success' : 'warning';
            const statusIcon = match.is_match ? '✅' : '⚠️';
            
            html += `
                <div class="card mb-3 border-${statusClass}">
                    <div class="card-header d-flex justify-content-between">
                        <strong>Match ${i + 1}</strong>
                        <span class="badge bg-${statusClass}">${statusIcon} Score: ${(match.best_score * 100).toFixed(1)}%</span>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6 class="text-primary">📥 JSON Item:</h6>
                                <div class="bg-light p-3 rounded">
                                    <strong>${match.json_name}</strong><br>
                                    <small>
                                        Vendor: ${match.json_data.vendor || 'N/A'}<br>
                                        Type: ${match.json_data.inventory_type || 'N/A'}
                                    </small>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <h6 class="text-success">📊 Excel Match:</h6>
                                ${match.best_match ? `
                                    <div class="bg-light p-3 rounded">
                                        <strong>${match.best_match['Product Name*']}</strong><br>
                                        <small>
                                            Vendor: ${match.best_match['Vendor/Supplier*'] || 'N/A'}<br>
                                            Type: ${match.best_match['Product Type*'] || 'N/A'}
                                        </small>
                                    </div>
                                ` : '<div class="bg-light p-3 rounded"><em>No match found</em></div>'}
                            </div>
                        </div>
                        ${match.top_candidates && match.top_candidates.length > 1 ? `
                            <div class="mt-3">
                                <h6>Alternative Matches:</h6>
                                <div class="row">
                                    ${match.top_candidates.slice(1, 4).map(alt => `
                                        <div class="col-md-4">
                                            <div class="card">
                                                <div class="card-body p-2">
                                                    <small>
                                                        <strong>${alt.excel_name}</strong><br>
                                                        Score: ${(alt.score * 100).toFixed(1)}%
                                                    </small>
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        });
        
        resultsDiv.innerHTML = html;
    }
    </script>
</body>
</html>
    ''')

@app.route('/api/excel-data')
def get_excel_data():
    """Return mock Excel data."""
    return jsonify(MOCK_EXCEL_DATA)

@app.route('/api/json-data') 
def get_json_data():
    """Return mock JSON data."""
    return jsonify(MOCK_JSON_DATA)

@app.route('/api/json-match-detailed', methods=['POST'])
def json_match_detailed():
    """Test the detailed JSON matching with mock data."""
    try:
        from src.core.data.json_matcher import JSONMatcher
        from src.core.data.excel_processor import ExcelProcessor
        
        # Create mock Excel processor
        mock_excel_processor = MagicMock()
        mock_excel_processor.df = MagicMock()
        mock_excel_processor.df.to_dict.return_value = MOCK_EXCEL_DATA
        
        # Create JSON matcher
        matcher = JSONMatcher(mock_excel_processor)
        
        # Process each JSON item
        detailed_matches = []
        high_confidence_matches = []
        
        for json_item in MOCK_JSON_DATA:
            json_name = json_item.get('product_name', '')
            
            best_score = 0.0
            best_match = None
            all_scores = []
            
            # Test against all Excel items
            for excel_item in MOCK_EXCEL_DATA:
                excel_name = excel_item.get('Product Name*', '')
                
                # Create cache item format
                cache_item = {
                    'original_name': excel_name,
                    'vendor': excel_item.get('Vendor/Supplier*', ''),
                    'product_type': excel_item.get('Product Type*', ''),
                    'key_terms': matcher._extract_key_terms(excel_name),
                    'norm': matcher._normalize(excel_name)
                }
                
                score = matcher._calculate_match_score(json_item, cache_item)
                all_scores.append({
                    'excel_name': excel_name,
                    'score': score,
                    'excel_data': excel_item
                })
                
                if score > best_score:
                    best_score = score
                    best_match = excel_item
            
            # Sort scores
            all_scores.sort(key=lambda x: x['score'], reverse=True)
            
            match_info = {
                'json_name': json_name,
                'json_data': json_item,
                'best_score': best_score,
                'best_match': best_match,
                'top_candidates': all_scores[:5],
                'is_match': best_score >= 0.4,
                'match_reason': 'High confidence match' if best_score >= 0.4 else 'Below threshold'
            }
            
            detailed_matches.append(match_info)
            
            if best_score >= 0.4:
                high_confidence_matches.append(best_match)
        
        return jsonify({
            'success': True,
            'total_json_items': len(MOCK_JSON_DATA),
            'total_matches': len(high_confidence_matches),
            'threshold': 0.4,
            'detailed_matches': detailed_matches,
            'high_confidence_matches': high_confidence_matches
        })
        
    except Exception as e:
        logging.error(f"Detailed matching error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/json-match', methods=['POST'])
def json_match():
    """Test the quick JSON matching."""
    try:
        from src.core.data.json_matcher import JSONMatcher
        
        # Create mock Excel processor  
        mock_excel_processor = MagicMock()
        mock_excel_processor.df = MagicMock()
        mock_excel_processor.df.to_dict.return_value = MOCK_EXCEL_DATA
        
        # Create JSON matcher
        matcher = JSONMatcher(mock_excel_processor)
        
        # Quick matching logic
        matched_products = []
        
        for json_item in MOCK_JSON_DATA:
            best_score = 0.0
            best_match = None
            
            for excel_item in MOCK_EXCEL_DATA:
                cache_item = {
                    'original_name': excel_item.get('Product Name*', ''),
                    'vendor': excel_item.get('Vendor/Supplier*', ''),
                    'product_type': excel_item.get('Product Type*', ''),
                    'key_terms': matcher._extract_key_terms(excel_item.get('Product Name*', '')),
                    'norm': matcher._normalize(excel_item.get('Product Name*', ''))
                }
                
                score = matcher._calculate_match_score(json_item, cache_item)
                
                if score > best_score:
                    best_score = score
                    best_match = excel_item
            
            # Use 0.4 threshold
            if best_score >= 0.4:
                matched_products.append(best_match)
        
        matched_names = [p.get('Product Name*', '') for p in matched_products]
        
        return jsonify({
            'success': True,
            'matched_count': len(matched_products),
            'matched_names': matched_names,
            'available_tags': matched_products,
            'selected_tags': matched_products,
            'threshold': 0.4
        })
        
    except Exception as e:
        logging.error(f"Quick matching error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting JSON Matching Test Server")
    print("=" * 50)
    print("Features being tested:")
    print("  • Improved matching accuracy (threshold 0.4)")
    print("  • Enhanced vendor validation")
    print("  • Before/after comparison display")
    print("  • Detailed scoring information")
    print()
    print("Visit: http://localhost:5555")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5555, debug=True)