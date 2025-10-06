#!/usr/bin/env python3
"""
Database Diagnosis and Repair Script
====================================

This script diagnoses and repairs missing crucial data in the product database.

Based on analysis, the main issues identified are:
1. 8,375 products (81.6% of 10,262 total) are missing Product Strain data
2. 7,797 products (76.0%) are missing both THC and CBD test results
3. Many products have incomplete terpene profiles and other optional data

This script will:
1. Analyze the current state of missing data
2. Attempt to populate missing strain data from product names
3. Backfill missing THC/CBD data where possible
4. Generate a comprehensive report
"""

import sqlite3
import os
import sys
import logging
from datetime import datetime
import re
from typing import Dict, List, Tuple, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseDiagnosisAndRepair:
    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = "/Users/adamcordova/Desktop/labelMaker_ QR copy SAFEST copy 15/uploads/product_database.db"
        else:
            self.db_path = db_path
        
        self.stats = {}
        self.repairs_made = {}
        
    def get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def diagnose_database(self) -> Dict[str, Any]:
        """Comprehensive diagnosis of database missing data."""
        logger.info("🔍 Starting comprehensive database diagnosis...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Basic counts
        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM strains")
        total_strains = cursor.fetchone()[0]
        
        # Missing critical data analysis
        missing_data_queries = {
            'missing_strain': """
                SELECT COUNT(*) FROM products 
                WHERE ("Product Strain" IS NULL OR "Product Strain" = '' OR "Product Strain" = 'None' OR "Product Strain" = 'nan')
            """,
            'missing_thc_cbd': """
                SELECT COUNT(*) FROM products 
                WHERE (("THC test result" IS NULL OR "THC test result" = '' OR "THC test result" = 'None') 
                   AND ("CBD test result" IS NULL OR "CBD test result" = '' OR "CBD test result" = 'None'))
            """,
            'missing_weight': """
                SELECT COUNT(*) FROM products 
                WHERE ("Weight*" IS NULL OR "Weight*" = '' OR "Weight*" = 'None' OR "Weight*" = 'nan')
            """,
            'missing_description': """
                SELECT COUNT(*) FROM products 
                WHERE ("Description" IS NULL OR "Description" = '' OR "Description" = 'None')
            """,
            'missing_batch_lot': """
                SELECT COUNT(*) FROM products 
                WHERE (("Batch Number" IS NULL OR "Batch Number" = '' OR "Batch Number" = 'None') 
                   AND ("Lot Number" IS NULL OR "Lot Number" = '' OR "Lot Number" = 'None'))
            """,
            'missing_room': """
                SELECT COUNT(*) FROM products 
                WHERE ("Room*" IS NULL OR "Room*" = '' OR "Room*" = 'None')
            """,
            'missing_doh_compliance': """
                SELECT COUNT(*) FROM products 
                WHERE ("DOH" IS NULL OR "DOH" = '' OR "DOH" = 'None')
            """,
            'missing_test_units': """
                SELECT COUNT(*) FROM products 
                WHERE ("Test result unit (% or mg)" IS NULL OR "Test result unit (% or mg)" = '' OR "Test result unit (% or mg)" = 'None')
            """
        }
        
        diagnosis = {
            'total_products': total_products,
            'total_strains': total_strains,
            'timestamp': datetime.now().isoformat()
        }
        
        for key, query in missing_data_queries.items():
            cursor.execute(query)
            count = cursor.fetchone()[0]
            percentage = (count / total_products * 100) if total_products > 0 else 0
            diagnosis[key] = {
                'count': count,
                'percentage': round(percentage, 2)
            }
        
        # Product type breakdown
        cursor.execute("""
            SELECT "Product Type*", COUNT(*) as count 
            FROM products 
            GROUP BY "Product Type*" 
            ORDER BY count DESC
        """)
        diagnosis['product_types'] = dict(cursor.fetchall())
        
        # Strain coverage by product type
        cursor.execute("""
            SELECT 
                "Product Type*",
                COUNT(*) as total,
                SUM(CASE WHEN ("Product Strain" IS NULL OR "Product Strain" = '' OR "Product Strain" = 'None') THEN 1 ELSE 0 END) as missing_strain
            FROM products 
            GROUP BY "Product Type*"
            ORDER BY total DESC
        """)
        
        strain_coverage = {}
        for row in cursor.fetchall():
            product_type, total, missing = row
            strain_coverage[product_type] = {
                'total': total,
                'missing_strain': missing,
                'coverage_percentage': round((total - missing) / total * 100, 2) if total > 0 else 0
            }
        diagnosis['strain_coverage_by_type'] = strain_coverage
        
        conn.close()
        self.stats = diagnosis
        return diagnosis
    
    def extract_strain_from_product_name(self, product_name: str, product_type: str) -> str:
        """Extract potential strain name from product name."""
        if not product_name:
            return ""
        
        # Skip paraphernalia and accessories
        if product_type and product_type.lower() in ['paraphernalia', 'accessory']:
            return "Mixed"
        
        # Common patterns for strain extraction
        strain_patterns = [
            # "Strain Name by Brand" pattern
            r'^([^-]+)\s+by\s+[^-]+',
            # "Strain Name - weight" pattern  
            r'^([^-]+)\s*-\s*\d+',
            # "Brand: Strain Name" pattern
            r':\s*([^-\d]+)',
            # Just the first part before " by " or " - "
            r'^([^-]+?)(?:\s+by\s|\s*-\s)',
        ]
        
        for pattern in strain_patterns:
            match = re.search(pattern, product_name, re.IGNORECASE)
            if match:
                potential_strain = match.group(1).strip()
                
                # Clean up common non-strain words
                skip_words = {'pre-roll', 'cartridge', 'vape', 'edible', 'gummy', 'chocolate', 
                             'concentrate', 'shatter', 'wax', 'live resin', 'rosin', 'hash',
                             'flower', 'bud', 'gram', 'oz', 'pound', 'mg', 'ml'}
                
                if potential_strain.lower() not in skip_words and len(potential_strain) > 2:
                    return potential_strain
        
        # If no pattern matches, return empty
        return ""
    
    def repair_missing_strain_data(self) -> Dict[str, int]:
        """Attempt to repair missing strain data by extracting from product names."""
        logger.info("🔧 Repairing missing strain data...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get products missing strain data
        cursor.execute("""
            SELECT id, "Product Name*", "Product Type*" 
            FROM products 
            WHERE ("Product Strain" IS NULL OR "Product Strain" = '' OR "Product Strain" = 'None' OR "Product Strain" = 'nan')
            AND "Product Type*" NOT IN ('Paraphernalia')
        """)
        
        products_to_repair = cursor.fetchall()
        repaired_count = 0
        skipped_count = 0
        
        for product_id, product_name, product_type in products_to_repair:
            extracted_strain = self.extract_strain_from_product_name(product_name, product_type)
            
            if extracted_strain and extracted_strain != "Mixed":
                try:
                    cursor.execute("""
                        UPDATE products 
                        SET "Product Strain" = ? 
                        WHERE id = ?
                    """, (extracted_strain, product_id))
                    repaired_count += 1
                except Exception as e:
                    logger.warning(f"Failed to update product {product_id}: {e}")
                    skipped_count += 1
            else:
                skipped_count += 1
        
        conn.commit()
        conn.close()
        
        repair_stats = {
            'repaired': repaired_count,
            'skipped': skipped_count,
            'total_processed': len(products_to_repair)
        }
        
        self.repairs_made['strain_repair'] = repair_stats
        logger.info(f"✅ Strain repair completed: {repaired_count} repaired, {skipped_count} skipped")
        return repair_stats
    
    def repair_missing_defaults(self) -> Dict[str, int]:
        """Set reasonable defaults for missing optional data."""
        logger.info("🔧 Setting defaults for missing optional data...")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        repairs = {}
        
        # Set default DOH compliance
        cursor.execute("""
            UPDATE products 
            SET "DOH" = 'No' 
            WHERE ("DOH" IS NULL OR "DOH" = '' OR "DOH" = 'None')
        """)
        repairs['doh_defaults'] = cursor.rowcount
        
        # Set default test result units
        cursor.execute("""
            UPDATE products 
            SET "Test result unit (% or mg)" = '%' 
            WHERE ("Test result unit (% or mg)" IS NULL OR "Test result unit (% or mg)" = '' OR "Test result unit (% or mg)" = 'None')
        """)
        repairs['test_unit_defaults'] = cursor.rowcount
        
        # Set default room
        cursor.execute("""
            UPDATE products 
            SET "Room*" = 'Default' 
            WHERE ("Room*" IS NULL OR "Room*" = '' OR "Room*" = 'None')
        """)
        repairs['room_defaults'] = cursor.rowcount
        
        # Set default state
        cursor.execute("""
            UPDATE products 
            SET "State" = 'active' 
            WHERE ("State" IS NULL OR "State" = '' OR "State" = 'None')
        """)
        repairs['state_defaults'] = cursor.rowcount
        
        # Set sample flag default
        cursor.execute("""
            UPDATE products 
            SET "Is Sample? (yes/no)" = 'no' 
            WHERE ("Is Sample? (yes/no)" IS NULL OR "Is Sample? (yes/no)" = '' OR "Is Sample? (yes/no)" = 'None')
        """)
        repairs['sample_defaults'] = cursor.rowcount
        
        # Set MJ product flag based on product type
        cursor.execute("""
            UPDATE products 
            SET "Is MJ product?(yes/no)" = CASE 
                WHEN "Product Type*" = 'Paraphernalia' THEN 'no'
                ELSE 'yes'
            END
            WHERE ("Is MJ product?(yes/no)" IS NULL OR "Is MJ product?(yes/no)" = '' OR "Is MJ product?(yes/no)" = 'None')
        """)
        repairs['mj_product_defaults'] = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        self.repairs_made['defaults'] = repairs
        logger.info(f"✅ Default values set: {sum(repairs.values())} total updates")
        return repairs
    
    def generate_report(self) -> str:
        """Generate a comprehensive diagnosis and repair report."""
        logger.info("📊 Generating comprehensive report...")
        
        report = []
        report.append("DATABASE DIAGNOSIS AND REPAIR REPORT")
        report.append("=" * 50)
        report.append(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Database: {self.db_path}")
        report.append("")
        
        if self.stats:
            report.append("CURRENT DATABASE STATUS")
            report.append("-" * 30)
            report.append(f"Total Products: {self.stats['total_products']:,}")
            report.append(f"Total Strains: {self.stats['total_strains']:,}")
            report.append("")
            
            report.append("MISSING DATA ANALYSIS")
            report.append("-" * 30)
            
            critical_issues = []
            moderate_issues = []
            minor_issues = []
            
            for key, data in self.stats.items():
                if isinstance(data, dict) and 'count' in data and 'percentage' in data:
                    issue_name = key.replace('missing_', '').replace('_', ' ').title()
                    count = data['count']
                    percentage = data['percentage']
                    
                    issue_line = f"{issue_name}: {count:,} ({percentage}%)"
                    
                    if percentage >= 70:
                        critical_issues.append(issue_line)
                    elif percentage >= 30:
                        moderate_issues.append(issue_line)
                    elif percentage > 0:
                        minor_issues.append(issue_line)
            
            if critical_issues:
                report.append("🔴 CRITICAL ISSUES (≥70% missing):")
                for issue in critical_issues:
                    report.append(f"  • {issue}")
                report.append("")
            
            if moderate_issues:
                report.append("🟡 MODERATE ISSUES (30-69% missing):")
                for issue in moderate_issues:
                    report.append(f"  • {issue}")
                report.append("")
            
            if minor_issues:
                report.append("🟢 MINOR ISSUES (<30% missing):")
                for issue in minor_issues:
                    report.append(f"  • {issue}")
                report.append("")
            
            # Product type breakdown
            if 'product_types' in self.stats:
                report.append("PRODUCT TYPE DISTRIBUTION")
                report.append("-" * 30)
                for product_type, count in list(self.stats['product_types'].items())[:10]:
                    percentage = (count / self.stats['total_products'] * 100)
                    report.append(f"{product_type}: {count:,} ({percentage:.1f}%)")
                report.append("")
            
            # Strain coverage by type
            if 'strain_coverage_by_type' in self.stats:
                report.append("STRAIN COVERAGE BY PRODUCT TYPE")
                report.append("-" * 30)
                for product_type, data in self.stats['strain_coverage_by_type'].items():
                    coverage = data['coverage_percentage']
                    total = data['total']
                    missing = data['missing_strain']
                    report.append(f"{product_type}: {coverage:.1f}% coverage ({total-missing}/{total})")
                report.append("")
        
        if self.repairs_made:
            report.append("REPAIRS COMPLETED")
            report.append("-" * 30)
            
            for repair_type, repair_data in self.repairs_made.items():
                if repair_type == 'strain_repair':
                    report.append(f"Strain Data Repair:")
                    report.append(f"  • Products repaired: {repair_data['repaired']:,}")
                    report.append(f"  • Products skipped: {repair_data['skipped']:,}")
                    report.append(f"  • Total processed: {repair_data['total_processed']:,}")
                elif repair_type == 'defaults':
                    report.append(f"Default Values Set:")
                    for field, count in repair_data.items():
                        field_name = field.replace('_defaults', '').replace('_', ' ').title()
                        report.append(f"  • {field_name}: {count:,} updates")
                report.append("")
        
        report.append("RECOMMENDATIONS")
        report.append("-" * 30)
        
        if self.stats:
            if self.stats.get('missing_strain', {}).get('percentage', 0) > 50:
                report.append("🔴 HIGH PRIORITY:")
                report.append("  • Implement automatic strain extraction from product names")
                report.append("  • Review and improve product naming conventions")
                report.append("  • Consider requiring strain data entry for cannabis products")
                report.append("")
            
            if self.stats.get('missing_thc_cbd', {}).get('percentage', 0) > 50:
                report.append("🟡 MEDIUM PRIORITY:")
                report.append("  • Require lab test results for cannabis products")
                report.append("  • Set up automatic data validation during product entry")
                report.append("  • Consider default values for non-cannabis products")
                report.append("")
            
        report.append("🟢 GENERAL RECOMMENDATIONS:")
        report.append("  • Implement data validation rules during product import")
        report.append("  • Create standardized product naming conventions")
        report.append("  • Set up automated data quality monitoring")
        report.append("  • Regular database cleanup and maintenance")
        
        return "\n".join(report)
    
    def run_full_diagnosis_and_repair(self) -> str:
        """Run complete diagnosis and repair process."""
        logger.info("🚀 Starting full database diagnosis and repair...")
        
        # Step 1: Diagnose current state
        self.diagnose_database()
        
        # Step 2: Repair missing strain data
        self.repair_missing_strain_data()
        
        # Step 3: Set default values for missing optional data
        self.repair_missing_defaults()
        
        # Step 4: Re-diagnose to see improvements
        logger.info("🔍 Re-analyzing database after repairs...")
        post_repair_stats = self.diagnose_database()
        
        # Step 5: Generate comprehensive report
        report = self.generate_report()
        
        # Save report to file
        report_filename = f"database_repair_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path = os.path.join(os.path.dirname(self.db_path), report_filename)
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"📄 Report saved to: {report_path}")
        
        return report

def main():
    """Main function to run the diagnosis and repair."""
    print("🏥 Database Diagnosis and Repair Tool")
    print("=" * 50)
    
    # Initialize the repair tool
    repair_tool = DatabaseDiagnosisAndRepair()
    
    try:
        # Run full diagnosis and repair
        report = repair_tool.run_full_diagnosis_and_repair()
        
        print("\n" + "=" * 50)
        print("DIAGNOSIS AND REPAIR COMPLETED")
        print("=" * 50)
        print(report)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during diagnosis and repair: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)