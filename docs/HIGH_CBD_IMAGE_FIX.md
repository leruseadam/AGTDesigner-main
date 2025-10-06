# High CBD Image Fix

## Issue
High CBD products were incorrectly using `DOH.png` instead of `HighCBD.png` for their DOH compliance image.

## Root Cause
The issue was caused by inconsistent logic across multiple files for determining when to use the High CBD image:

1. **`formatting_utils.py`** - Used a restrictive list of specific product types that included "doh compliant"
2. **`text_processing.py`** - Used the correct logic of checking if product type starts with "high cbd"
3. **`template_processor.py`** - Had incorrect logic that passed 'HIGH_CBD' as a parameter instead of the actual DOH value
4. **`tag_generator.py`** - Used the same restrictive logic as formatting_utils.py

## Solution
Updated all files to use consistent logic:

### 1. Fixed `formatting_utils.py`
- Changed from checking specific product type strings to checking if product type starts with "high cbd"
- This makes the logic more flexible and consistent

### 2. Fixed `template_processor.py`
- Removed the incorrect conditional logic that passed 'HIGH_CBD' as a parameter
- Now directly calls `process_doh_image(doh_value, product_type)` with the actual values

### 3. Fixed `tag_generator.py`
- Updated to use the same flexible logic as the other files
- Now checks if product type starts with "high cbd" instead of specific strings

## Test Results
Created and ran `test_high_cbd_fix.py` which verifies:

✅ High CBD products now correctly use `HighCBD.png`:
- "high cbd edible" → HighCBD.png
- "High CBD Topical" → HighCBD.png  
- "HIGH CBD CONCENTRATE" → HighCBD.png
- "high cbd tincture" → HighCBD.png
- "High CBD Flower" → HighCBD.png

✅ Non-High CBD products still use `DOH.png`:
- "regular flower" → DOH.png
- "concentrate" → DOH.png
- "edible" → DOH.png

✅ Products with DOH="NO" or empty correctly show no image

## Files Modified
- `src/core/generation/formatting_utils.py`
- `src/core/generation/template_processor.py`  
- `src/core/generation/tag_generator.py`

## Impact
High CBD products will now correctly display the High CBD compliance image instead of the generic DOH image, providing better visual distinction for these specialized products. 