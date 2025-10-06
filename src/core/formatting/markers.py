# Field markers for template replacement
FIELD_MARKERS = {
    'PRODUCTNAME': ('PRODUCTNAME_START', 'PRODUCTNAME_END'),
    'PRODUCTBRAND': ('PRODUCTBRAND_START', 'PRODUCTBRAND_END'),
    'PRODUCTBRAND_CENTER': ('PRODUCTBRAND_CENTER_START', 'PRODUCTBRAND_CENTER_END'),
    'PRODUCTSTRAIN': ('PRODUCTSTRAIN_START', 'PRODUCTSTRAIN_END'),
    'PRODUCTTYPE': ('PRODUCTTYPE_START', 'PRODUCTTYPE_END'),
    'PRODUCTVENDOR': ('PRODUCTVENDOR_START', 'PRODUCTVENDOR_END'),
    'LINEAGE': ('LINEAGE_START', 'LINEAGE_END'),
    'WEIGHTUNITS': ('WEIGHTUNITS_START', 'WEIGHTUNITS_END'),
    'PRICE': ('PRICE_START', 'PRICE_END'),
    'DOH': ('DOH_START', 'DOH_END'),
    'DESC': ('DESC_START', 'DESC_END'),
    'THC_CBD': ('THC_CBD_START', 'THC_CBD_END'),
    'RATIO': ('RATIO_START', 'RATIO_END'),
    'JOINT_RATIO': ('JOINT_RATIO_START', 'JOINT_RATIO_END'),
    'THC': ('THC_START', 'THC_END'),
    'CBD': ('CBD_START', 'CBD_END')
}

# Map field names to their markers
MARKER_MAP = {
    'ProductName': 'PRODUCTNAME',
    'ProductBrand': 'PRODUCTBRAND',
    'ProductBrand_Center': 'PRODUCTBRAND_CENTER',
    'ProductStrain': 'PRODUCTSTRAIN',
    'ProductType': 'PRODUCTTYPE',
    'ProductVendor': 'PRODUCTVENDOR',
    'Lineage': 'LINEAGE',
    'WeightUnits': 'WEIGHTUNITS',
    'Price': 'PRICE',
    'DOH': 'DOH',
    'Description': 'DESC',
    'DescAndWeight': 'DESC',  # Map DescAndWeight to DESC marker
    'Ratio_or_THC_CBD': 'THC_CBD',  # Map Ratio_or_THC_CBD to THC_CBD marker for proper font sizing
    'THC_CBD': 'THC_CBD',
    'Ratio': 'RATIO',
    'JointRatio': 'JOINT_RATIO',
    'THC': 'THC',
    'CBD': 'CBD'
}

def wrap_with_marker(text, marker):
    """Wrap text with start and end markers."""
    if not text:
        return ""
    safe_text = str(text).replace('&', '&amp;')
    return f"{marker}_START{safe_text}{marker}_END"

def unwrap_marker(value, marker):
    """Remove markers from a value if present."""
    if not isinstance(value, str):
        return value
    start_marker = f"{marker}_START"
    end_marker = f"{marker}_END"
    if start_marker in value and end_marker in value:
        start_idx = value.find(start_marker) + len(start_marker)
        end_idx = value.find(end_marker)
        unwrapped = value[start_idx:end_idx]
        # Only strip for non-JointRatio and non-THC/CBD markers to preserve line breaks
        if marker not in ['JOINT_RATIO', 'THC_CBD', 'RATIO']:
            unwrapped = unwrapped.strip()
        # Restore ampersands
        return unwrapped.replace('&amp;', '&')
    return value

def is_already_wrapped(value, marker):
    """Check if a value is already wrapped with markers."""
    if not isinstance(value, str):
        return False
    start_marker = f"{marker}_START"
    end_marker = f"{marker}_END"
    return start_marker in value and end_marker in value