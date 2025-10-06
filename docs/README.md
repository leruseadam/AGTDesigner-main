# AGTDesigner2 - Lab## 🛠️ Installation & Setup

### Local Development
```bash
git clone https://github.com/leruseadam/AGTDesigner2.git
cd AGTDesigner2
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### PythonAnywhere Deployment
```bash
git clone https://github.com/leruseadam/AGTDesigner2.git labelmaker
cd labelmaker
python3.10 -m venv ~/labelmaker-venv
source ~/labelmaker-venv/bin/activate
chmod +x install_pythonanywhere.sh
./install_pythonanywhere.sh
```

## 📖 Documentation

- `PYTHONANYWHERE_DEPLOYMENT_COMPLETE.md` - Complete deployment guide
- `INSTALLATION_GUIDE.md` - Local installation guide
- `DEPLOYMENT_CHECKLIST.md` - Deployment checklist

## 🔧 Requirements Files

- `requirements.txt` - Main dependencies
- `requirements_web.txt` - Web-only (no GUI dependencies)
- `requirements_pythonanywhere.txt` - PythonAnywhere-specific versions
- `requirements_production.txt` - Production environmentntory Generator

A cross-platform Flask web application for cannabis product labeling and inventory management.

## 🌟 Features

- **Web-based Interface**: Modern, responsive web application
- **Product Data Management**: Load from Excel or JSON URLs
- **Multiple Label Formats**: 3×3 tags, 5×6 mini tags, 2×2 inventory slips
- **Smart Filtering**: Filter products by type, category, and attributes
- **Template Generation**: Professional Word document output
- **Lineage Management**: Automatic Sativa/Indica/Hybrid classification
- **Unit Conversions**: Automatic g → oz conversion for edibles
- **Color Coding**: Visual categorization for cannabinoids, paraphernalia, etc.
- **PythonAnywhere Ready**: Optimized for cloud deployment

## 🚀 Repository

**GitHub**: https://github.com/leruseadam/AGTDesigner2.git

1. Loads product data from Excel or JSON URLs  
2. Applies filters and lets you select products  
3. Generates:
   - 3×3 horizontal or vertical Word tag sheets  
   - 5×6 “mini” tags  
   - 2×2 inventory slips  

It also supports:
- On-the-fly lineage (Sativa/Indica/Hybrid/etc.) correction via dropdowns  
- Automatic unit conversions (g → oz for edibles)  
- Colored cell shading for cannabinoids, paraphernalia, etc.  
- Duplex-back vendor/brand printing  
- Right-click “Paste” in JSON URL entry  
- Adjustable complexity/scale slider  
- Fast multi-process rendering and smart template expansion  

---

## Features

- **Excel or JSON ingestion**: point at a POSaBit export or transfer-API URL.  
- **Dynamic filters**: vendor, brand, type, lineage, strain, weight.  
- **Selected-tag UI**: move items Available ↔ Selected, with “Select All” and undo.  
- **Lineage fixer**: correct strain lineage in bulk and log changes.  
- **Tag generation**: Word `.docx` output, smart autosizing, conditional formatting, cut-guide lines.  
- **Inventory slips**: 2×2 labels with vendor/backside duplex pages.  
- **Cross-platform**: Windows (via COM) and macOS (via AppleScript) support for overwriting open Word docs.  
- **Packaging**: can be bundled as a standalone exe/app via PyInstaller or similar.  

---

## Requirements

- **Python 3.8+**  
- **Tkinter** (should ship with standard Python)  
- **pandas**, **openpyxl**  
- **python-docx**, **docxtpl**, **docxcompose**  
- **pywin32** (Windows only, for closing open Word docs)  
- **macOS**: AppleScript support (bundled)  

Install dependencies with:

```bash
pip install pandas openpyxl python-docx docxtpl docxcompose pywin32
