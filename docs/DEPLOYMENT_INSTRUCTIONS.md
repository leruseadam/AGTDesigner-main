
# Deployment Instructions for Default File

## Selected File: A Greener Today - Bothell_inventory_07-07-2025 10_19 AM.xlsx
- Size: 0.85 MB
- Path: uploads/A Greener Today - Bothell_inventory_07-07-2025 10_19 AM.xlsx

## Option 1: Manual Upload (Recommended)
1. Go to https://www.agtpricetags.com
2. Click the upload button
3. Select the file: A Greener Today - Bothell_inventory_07-07-2025 10_19 AM.xlsx
4. The application will load the data and API endpoints will work

## Option 2: Server Deployment
If you want the file to be available by default:

1. **Upload to PythonAnywhere:**
   - Log into your PythonAnywhere account
   - Go to the Files tab
   - Navigate to your project directory
   - Create an 'uploads' folder if it doesn't exist
   - Upload the file: A Greener Today - Bothell_inventory_07-07-2025 10_19 AM.xlsx

2. **Or use the PythonAnywhere console:**
   ```bash
   # In your PythonAnywhere console
   cd /home/yourusername/yourproject
   mkdir -p uploads
   # Upload the file via the Files interface
   ```

3. **Restart your web app** after uploading the file

## Option 3: Include in Git Repository
If you want the file to be part of your deployment:

1. Copy the file to your project:
   ```bash
   cp "uploads/A Greener Today - Bothell_inventory_07-07-2025 10_19 AM.xlsx" uploads/default_inventory.xlsx
   ```

2. Add to git (if the file is not sensitive):
   ```bash
   git add uploads/default_inventory.xlsx
   git commit -m "Add default inventory file"
   git push
   ```

3. Modify the get_default_upload_file() function to look for this specific file

## Testing
After deployment, test the API endpoints:
- https://www.agtpricetags.com/api/status
- https://www.agtpricetags.com/api/available-tags
- https://www.agtpricetags.com/api/selected-tags

## Notes
- The file size (0.85 MB) is reasonable for web loading
- Make sure the file contains the expected columns (Product Name*, Vendor, etc.)
- Consider if this data should be publicly accessible
