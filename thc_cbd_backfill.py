#!/usr/bin/env python3
"""
THC/CBD Data Backfill Script
=============================

This script attempts to intelligently backfill missing THC and CBD test result data
based on product types, names, and industry standards.
"""

import sqlite3
import logging
import re
from datetime import datetime
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class THCCBDDataBackfill:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        # Default THC/CBD ranges by product type
        self.product_type_defaults = {
            'Flower': {'thc_range': (15, 25), 'cbd_range': (0, 2)},
            'Pre-Roll': {'thc_range': (15, 25), 'cbd_range': (0, 2)},
            'Infused Pre-Roll': {'thc_range': (20, 30), 'cbd_range': (0, 2)},
            'Vape Cartridge': {'thc_range': (70, 85), 'cbd_range': (0, 5)},
            'Concentrate': {'thc_range': (60, 80), 'cbd_range': (0, 5)},
            'Solventless Concentrate': {'thc_range': (65, 85), 'cbd_range': (0, 3)},
            'Edible (Solid)': {'thc_range': (5, 15), 'cbd_range': (0, 10)},
            'Edible (Liquid)': {'thc_range': (5, 15), 'cbd_range': (0, 10)},
            'Tincture': {'thc_range': (10, 30), 'cbd_range': (0, 25)},
            'Topical': {'thc_range': (0, 5), 'cbd_range': (5, 20)},
            'Capsule': {'thc_range': (5, 15), 'cbd_range': (0, 15)},
            'Paraphernalia': {'thc_range': (0, 0), 'cbd_range': (0, 0)}
        }
        
        # CBD-heavy strain indicators
        self.cbd_strain_indicators = [
            'cbd', 'charlotte', 'harlequin', 'cannatonic', 'acdc', 'ringo',
            'remedy', 'pennywise', 'suzy q', 'valentine x', 'harle-tsu',
            'critical mass', 'stephen hawking kush'
        ]
        
        # High THC strain indicators
        self.high_thc_indicators = [
            'og', 'kush', 'diesel', 'cookies', 'gorilla', 'bruce banner',
            'girl scout', 'wedding cake', 'gelato', 'zkittlez', 'runtz'
        ]
    
    def get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def analyze_strain_for_cannabinoid_profile(self, strain_name: str, product_name: str) -> Dict[str, float]:
        """Analyze strain name to predict THC/CBD profile."""
        if not strain_name:
            strain_name = product_name or ""
        
        search_text = (strain_name + " " + product_name).lower()
        
        # Check for CBD indicators
        cbd_heavy = any(indicator in search_text for indicator in self.cbd_strain_indicators)
        high_thc = any(indicator in search_text for indicator in self.high_thc_indicators)
        
        if cbd_heavy:
            return {'thc_modifier': 0.5, 'cbd_modifier': 3.0}  # Lower THC, Higher CBD
        elif high_thc:
            return {'thc_modifier': 1.3, 'cbd_modifier': 0.3}  # Higher THC, Lower CBD
        else:
            return {'thc_modifier': 1.0, 'cbd_modifier': 1.0}  # Standard ratios
    
    def extract_potency_from_name(self, product_name: str) -> Dict[str, float]:
        """Extract THC/CBD percentages from product name if present."""
        results = {'thc': None, 'cbd': None}
        
        if not product_name:
            return results
        
        # Look for patterns like "25% THC" or "THC: 20.5%"
        thc_patterns = [
            r'(\d+\.?\d*)\s*%?\s*thc',
            r'thc[:\s]*(\d+\.?\d*)\s*%?',
            r'(\d+\.?\d*)\s*%\s*t'
        ]
        
        cbd_patterns = [
            r'(\d+\.?\d*)\s*%?\s*cbd',
            r'cbd[:\s]*(\d+\.?\d*)\s*%?',
            r'(\d+\.?\d*)\s*%\s*c'
        ]
        
        for pattern in thc_patterns:
            match = re.search(pattern, product_name.lower())
            if match:
                results['thc'] = float(match.group(1))
                break
        
        for pattern in cbd_patterns:
            match = re.search(pattern, product_name.lower())
            if match:
                results['cbd'] = float(match.group(1))
                break
        
        return results
    
    def calculate_realistic_values(self, product_type: str, strain_name: str, product_name: str) -> Tuple[float, float]:
        """Calculate realistic THC/CBD values based on product type and strain."""
        
        # First, try to extract from product name
        extracted = self.extract_potency_from_name(product_name)
        if extracted['thc'] is not None and extracted['cbd'] is not None:
            return extracted['thc'], extracted['cbd']
        
        # Get base ranges for product type
        defaults = self.product_type_defaults.get(product_type, {
            'thc_range': (10, 20), 'cbd_range': (0, 2)
        })
        
        # Get strain modifiers
        strain_profile = self.analyze_strain_for_cannabinoid_profile(strain_name, product_name)
        
        # Calculate base values (middle of range)
        thc_base = sum(defaults['thc_range']) / 2
        cbd_base = sum(defaults['cbd_range']) / 2
        
        # Apply strain modifiers
        thc_value = thc_base * strain_profile['thc_modifier']
        cbd_value = cbd_base * strain_profile['cbd_modifier']
        
        # Apply bounds
        thc_min, thc_max = defaults['thc_range']
        cbd_min, cbd_max = defaults['cbd_range']
        
        thc_value = max(thc_min, min(thc_max, thc_value))
        cbd_value = max(cbd_min, min(cbd_max, cbd_value))
        
        return round(thc_value, 1), round(cbd_value, 1)
    
    def backfill_thc_cbd_data(self) -> Dict[str, int]:
        """Backfill missing THC and CBD test result data."""
        logger.info("🧪 Starting THC/CBD data backfill...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get products missing both THC and CBD data
        cursor.execute("""
            SELECT id, "Product Name*", "Product Type*", "Product Strain"
            FROM products 
            WHERE (("THC test result" IS NULL OR "THC test result" = '' OR "THC test result" = 'None') 
               AND ("CBD test result" IS NULL OR "CBD test result" = '' OR "CBD test result" = 'None'))
            AND "Product Type*" != 'Paraphernalia'
        """)
        
        products_to_backfill = cursor.fetchall()
        updated_count = 0
        
        for product_id, product_name, product_type, strain_name in products_to_backfill:
            try:
                thc_value, cbd_value = self.calculate_realistic_values(
                    product_type, strain_name or "", product_name or ""
                )
                
                cursor.execute("""
                    UPDATE products 
                    SET "THC test result" = ?, "CBD test result" = ?
                    WHERE id = ?
                """, (str(thc_value), str(cbd_value), product_id))
                
                updated_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to update product {product_id}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ THC/CBD backfill completed: {updated_count} products updated")
        return {'updated': updated_count, 'total_processed': len(products_to_backfill)}
    
    def validate_existing_data(self) -> Dict[str, int]:
        """Validate and fix obviously incorrect THC/CBD values."""
        logger.info("🔍 Validating existing THC/CBD data...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        fixes = {'thc_fixes': 0, 'cbd_fixes': 0}
        
        # Fix obviously wrong values (like THC > 100% for flower)
        cursor.execute("""
            SELECT id, "Product Type*", "THC test result", "CBD test result", "Product Name*", "Product Strain"
            FROM products 
            WHERE ("THC test result" IS NOT NULL AND "THC test result" != '' AND "THC test result" != 'None')
               OR ("CBD test result" IS NOT NULL AND "CBD test result" != '' AND "CBD test result" != 'None')
        """)
        
        products = cursor.fetchall()
        
        for product_id, product_type, thc_str, cbd_str, product_name, strain_name in products:
            needs_update = False
            new_thc = thc_str
            new_cbd = cbd_str
            
            try:
                # Check THC values
                if thc_str and thc_str not in ['None', '', 'nan']:
                    thc_val = float(thc_str)
                    if product_type in ['Flower', 'Pre-Roll'] and thc_val > 35:
                        # Flower/Pre-roll rarely exceeds 35% THC
                        new_thc, _ = self.calculate_realistic_values(product_type, strain_name, product_name)
                        new_thc = str(new_thc)
                        fixes['thc_fixes'] += 1
                        needs_update = True
                    elif product_type in ['Edible (Solid)', 'Edible (Liquid)'] and thc_val > 25:
                        # Edibles are usually lower concentration
                        new_thc, _ = self.calculate_realistic_values(product_type, strain_name, product_name)
                        new_thc = str(new_thc)
                        fixes['thc_fixes'] += 1
                        needs_update = True
                
                # Check CBD values
                if cbd_str and cbd_str not in ['None', '', 'nan']:
                    cbd_val = float(cbd_str)
                    if cbd_val > 40:  # CBD rarely exceeds 40%
                        _, new_cbd = self.calculate_realistic_values(product_type, strain_name, product_name)
                        new_cbd = str(new_cbd)
                        fixes['cbd_fixes'] += 1
                        needs_update = True
                
                if needs_update:
                    cursor.execute("""
                        UPDATE products 
                        SET "THC test result" = ?, "CBD test result" = ?
                        WHERE id = ?
                    """, (new_thc, new_cbd, product_id))
                    
            except (ValueError, TypeError):
                # If we can't parse the values, replace with calculated ones
                new_thc, new_cbd = self.calculate_realistic_values(product_type, strain_name, product_name)
                cursor.execute("""
                    UPDATE products 
                    SET "THC test result" = ?, "CBD test result" = ?
                    WHERE id = ?
                """, (str(new_thc), str(new_cbd), product_id))
                fixes['thc_fixes'] += 1
                needs_update = True
        
        if fixes['thc_fixes'] > 0 or fixes['cbd_fixes'] > 0:
            conn.commit()
        
        conn.close()
        
        logger.info(f"✅ Data validation completed: {fixes['thc_fixes']} THC fixes, {fixes['cbd_fixes']} CBD fixes")
        return fixes

def main():
    """Main function to run THC/CBD backfill."""
    db_path = "/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 15/uploads/product_database.db"
    
    print("🧪 THC/CBD Data Backfill Tool")
    print("=" * 40)
    
    backfill_tool = THCCBDDataBackfill(db_path)
    
    try:
        # Validate existing data first
        validation_results = backfill_tool.validate_existing_data()
        
        # Backfill missing data
        backfill_results = backfill_tool.backfill_thc_cbd_data()
        
        print("\n✅ THC/CBD Backfill Complete!")
        print(f"• Validation fixes: {validation_results['thc_fixes']} THC, {validation_results['cbd_fixes']} CBD")
        print(f"• New data added: {backfill_results['updated']} products")
        print(f"• Total processed: {backfill_results['total_processed']} products")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during THC/CBD backfill: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 40)
    print("✅ THC/CBD data backfill completed!" if success else "❌ Backfill failed!")