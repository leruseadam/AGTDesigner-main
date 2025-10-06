"""
Centralized field/column mapping for Excel, DB, and JSON matching.
Import and use this everywhere instead of local mapping dicts.
"""

# Canonical field names (keys) and all possible aliases (values)
FIELD_ALIASES = {
    "Product Name*": ["Product Name*", "product_name", "ProductName", "name", "description"],
    "Product Brand": ["Product Brand", "brand", "ProductBrand", "product_brand", "Brand"],
    "Vendor/Supplier*": ["Vendor/Supplier*", "Vendor", "vendor", "vendor_name", "supplier", "Supplier", "Vendor/Supplier"],
    "Product Type*": ["Product Type*", "product_type", "ProductType", "inventory_type", "inventory_category", "C"],
    "Weight*": ["Weight*", "weight", "Weight", "unit_weight"],
    "Weight Unit* (grams/gm or ounces/oz)": ["Weight Unit* (grams/gm or ounces/oz)", "units", "unit_weight_uom", "uom"],
    "Product Strain": ["Product Strain", "strain", "Strain", "strain_name", "Strain Name"],
    "Lineage": ["Lineage", "lineage", "canonical_lineage"],
    "Price* (Tier Name for Bulk)": ["Price* (Tier Name for Bulk)", "price", "Price", "line_price"],
    "Internal Product Identifier": ["Internal Product Identifier", "product_sku", "inventory_id", "id"],
    "Description": ["Description", "description", "desc"],
    "Units": ["Units", "units"],
    "Quantity*": ["Quantity*", "quantity", "qty"],
    # Add more as needed
}

# Reverse mapping: alias -> canonical
ALIAS_TO_CANONICAL = {}
for canonical, aliases in FIELD_ALIASES.items():
    for alias in aliases:
        ALIAS_TO_CANONICAL[alias] = canonical

def get_canonical_field(field_name):
    """
    Given any field/column name, return the canonical field name.
    If not found, return the original name.
    """
    return ALIAS_TO_CANONICAL.get(field_name, field_name)

def get_all_aliases(canonical_field):
    """
    Return all aliases for a canonical field name.
    """
    return FIELD_ALIASES.get(canonical_field, [canonical_field])
