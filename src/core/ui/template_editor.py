import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from pathlib import Path
from typing import Dict, Any

class TemplateEditor:
    """Editor for managing template settings in the tag maker application."""
    
    # Define template settings exactly as in MAIN.py
    DEFAULT_SETTINGS = {
        "horizontal": {
            "font_family": "Arial",
            "description_size": 14,
            "weight_size": 12,
            "lineage_size": 12,
            "strain_size": 12,
            "min_size": 10,
            "max_size": 16,
            "spacing": 1.15,
            "margin": 0.1
        },
        "vertical": {
            "font_family": "Arial",
            "description_size": 16,
            "weight_size": 14,
            "lineage_size": 14,
            "strain_size": 14,
            "min_size": 12,
            "max_size": 18,
            "spacing": 1.2,
            "margin": 0.15
        },
        "mini": {
            "font_family": "Arial",
            "description_size": 12,
            "weight_size": 10,
            "lineage_size": 10,
            "strain_size": 10,
            "min_size": 8,
            "max_size": 14,
            "spacing": 1.1,
            "margin": 0.08
        }
    }

    def __init__(self, root):
        self.root = root
        self.settings = self._load_settings()
        self.template_vars = {}
        
    def show(self):
        """Display template editor dialog."""
        self.dialog = tk.Toplevel(self.root)
        self.dialog.title("Template Settings")
        self.dialog.geometry("800x600")
        
        # Create notebook for template tabs
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create tabs for each template type
        for template_type in ["horizontal", "vertical", "mini", "double"]:
            self._create_template_tab(notebook, template_type)
            
        # Add buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            button_frame,
            text="Save",
            command=self._save_settings
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        # Make dialog modal
        self.dialog.transient(self.root)
        self.dialog.grab_set()
        self.root.wait_window(self.dialog)
        
    def _create_template_tab(self, notebook, template_type):
        """Create settings tab for a template type."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=template_type.capitalize())
        
        # Initialize variables for this template
        self.template_vars[template_type] = {}
        settings = self.settings.get(template_type, self.DEFAULT_SETTINGS[template_type])
        
        # Create settings fields
        row = 0
        for key, default in self.DEFAULT_SETTINGS[template_type].items():
            ttk.Label(
                frame,
                text=f"{key.replace('_', ' ').title()}:"
            ).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            
            var = tk.StringVar(value=str(settings.get(key, default)))
            self.template_vars[template_type][key] = var
            
            if isinstance(default, (int, float)):
                widget = ttk.Entry(frame, textvariable=var, width=10)
            else:
                widget = ttk.Entry(frame, textvariable=var, width=30)
            
            widget.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
            row += 1
            
    def _load_settings(self):
        """Load settings from file or use defaults."""
        settings_path = Path.home() / "Downloads" / "template_settings.json"
        if settings_path.exists():
            try:
                with open(settings_path) as f:
                    return json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load settings: {str(e)}")
        return self.DEFAULT_SETTINGS.copy()
        
    def _save_settings(self):
        """Save current settings to file."""
        try:
            settings = {}
            for template_type, vars in self.template_vars.items():
                settings[template_type] = {k: v.get() for k, v in vars.items()}
            settings_path = Path.home() / "Downloads" / "template_settings.json"
            with open(settings_path, "w") as f:
                json.dump(settings, f)
            messagebox.showinfo("Success", "Settings saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

    def build_context(self, record, label_key):
        """Build context for the template."""
        context = {}
        context[label_key] = {
            'Description': '',
            'WeightUnits': '',
            'ProductBrand': '',
            'Price': '',
            'Lineage': '',
            'DOH': '',
            'Ratio_or_THC_CBD': ''  # <-- Use this field name
        }
        return context