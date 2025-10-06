import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from pathlib import Path
import logging
from src.core.constants import PRODUCT_TYPE_EMOJIS

class FileUploadPanel(ttk.Frame):
    def __init__(self, parent, theme):
        super().__init__(parent, width=350)  # Match width to FilterPanel for alignment
        self.theme = theme
        self.current_file = None
        self.create_widgets()
        
    def create_widgets(self):
        """Create the file upload panel widgets"""
        # Upload button
        self.upload_btn = self.theme.create_button(
            self,
            "Upload Spreadsheet",
            self.on_upload,
            width=20
        )
        self.upload_btn.pack(pady=(0, 20))
        
        # File label
        self.file_label = self.theme.create_label(
            self,
            "No file selected",
            font=self.theme.fonts['small']
        )
        self.file_label.pack(pady=(0, 10))
        
        # Add database management buttons
        self.delete_entry_btn = self.theme.create_button(
            self,
            "Delete DB Entry",
            self.delete_database_entry,
            width=20
        )
        self.delete_entry_btn.pack(pady=(10, 2))

        self.delete_all_btn = self.theme.create_button(
            self,
            "Delete ALL DB Entries",
            self.delete_all_database_entries,
            width=20
        )
        self.delete_all_btn.pack(pady=(2, 10))
        
    def on_upload(self):
        """Handle file upload"""
        path = filedialog.askopenfilename(
            filetypes=[("Excel Files", "*.xlsx"), ("CSV Files", "*.csv")]
        )
        if path:
            self.set_file(path)
            self.load_file(path)
            
    def set_file(self, path):
        """Set the current file path"""
        self.current_file = path
        self.file_label.config(text=Path(path).name)
        
    def load_file(self, path):
        """Load the spreadsheet file and update the database with backup."""
        try:
            if path.endswith('.xlsx'):
                self.df = pd.read_excel(path)
            else:
                self.df = pd.read_csv(path)
            logging.info(f"Successfully loaded file: {path}")

            # --- Database and backup logic ---
            db_path = Path.home() / "Downloads" / "file_database.csv"
            backup_path = Path.home() / "Downloads" / f"file_database_backup.csv"

            # Backup current database if it exists
            if db_path.exists():
                db_path.replace(backup_path)

            # Add new file info to database (avoid duplicates)
            new_entry = {'filename': Path(path).name, 'filepath': str(path)}
            if db_path.exists():
                db_df = pd.read_csv(db_path)
                if not ((db_df['filename'] == new_entry['filename']) & (db_df['filepath'] == new_entry['filepath'])).any():
                    db_df = db_df.append(new_entry, ignore_index=True)
                    db_df.to_csv(db_path, index=False)
            else:
                pd.DataFrame([new_entry]).to_csv(db_path, index=False)
            # --- End database logic ---
        except Exception as e:
            logging.error(f"Error loading file: {e}")
            raise

    def prompt_for_pin(self):
        """Prompt the user for a PIN and return True if correct."""
        from tkinter.simpledialog import askstring
        pin = askstring("PIN Required", "Enter admin PIN to proceed:", show='*')
        return pin == "6989"

    def delete_database_entry(self):
        """Delete a selected database entry after PIN verification."""
        from tkinter.simpledialog import askstring
        import pandas as pd
        db_path = Path.home() / "Downloads" / "file_database.csv"
        if not db_path.exists():
            messagebox.showinfo("No Database", "No database file found.")
            return
        if not self.prompt_for_pin():
            messagebox.showerror("Access Denied", "Incorrect PIN.")
            return
        # Ask for filename to delete
        filename = askstring("Delete Entry", "Enter filename to delete from database:")
        if not filename:
            return
        db_df = pd.read_csv(db_path)
        new_df = db_df[db_df['filename'] != filename]
        if len(new_df) == len(db_df):
            messagebox.showinfo("Not Found", f"No entry found for filename: {filename}")
            return
        new_df.to_csv(db_path, index=False)
        messagebox.showinfo("Deleted", f"Entry for {filename} deleted.")

    def delete_all_database_entries(self):
        """Delete all database entries after PIN verification."""
        db_path = Path.home() / "Downloads" / "file_database.csv"
        if not db_path.exists():
            messagebox.showinfo("No Database", "No database file found.")
            return
        if not self.prompt_for_pin():
            messagebox.showerror("Access Denied", "Incorrect PIN.")
            return
        db_path.unlink()
        messagebox.showinfo("Deleted", "All database entries deleted.")

class FilterPanel(ttk.Frame):
    def __init__(self, parent, theme):
        super().__init__(parent, width=350)  # Increased width for wider filter panel
        self.theme = theme
        self.create_widgets()
        
    def create_widgets(self):
        """Create the filter panel widgets"""
        # Filter sections
        self.create_filter_sections()
        
        # Clear filters button
        self.clear_btn = self.theme.create_button(
            self,
            "Clear Filters",
            self.on_clear_filters,
            width=20
        )
        self.clear_btn.pack(pady=20)
        
    def create_filter_sections(self):
        """Create filter sections"""
        filter_defs = [
            ("Vendor", "vendor_filter"),
            ("Brand", "brand_filter"),
            ("Product Type", "type_filter"),
            ("Lineage", "lineage_filter"),
            ("CBD Blend", "strain_filter"),
            ("Weight", "weight_filter")
        ]
        
        for label, var_name in filter_defs:
            # Create section frame
            section = self.theme.create_frame(self)
            section.pack(fill="x", pady=5)
            
            # Label
            self.theme.create_label(
                section,
                label,
                font=self.theme.fonts['subheading']
            ).pack(anchor="w")
            
            # Dropdown
            setattr(self, var_name, tk.StringVar(value="All"))
            dropdown = self.theme.create_combobox(
                section,
                textvariable=getattr(self, var_name),
                values=["All"],
                state="readonly",
                width=28  # Increased width for wider dropdowns
            )
            dropdown.pack(fill="x", pady=(5, 0))
            
        # Quantity filter checkbox
        self.quantity_filter = tk.BooleanVar(value=True)
        self.theme.create_checkbutton(
            self,
            "Only show products with Quantity > 0",
            self.quantity_filter
        ).pack(pady=10, anchor="w")
        
    def on_clear_filters(self):
        """Clear all filters"""
        for var_name in [
            "vendor_filter", "brand_filter", "type_filter",
            "lineage_filter", "strain_filter", "weight_filter"
        ]:
            getattr(self, var_name).set("All")
        self.quantity_filter.set(True)

    def populate_dropdowns(self, filter_options):
        # filter_options is a dict like: {'vendor': [...], 'brand': [...], ...}
        self.vendor_filter.set("All")
        self.brand_filter.set("All")
        self.type_filter.set("All")
        self.lineage_filter.set("All")
        self.strain_filter.set("All")
        self.weight_filter.set("All")
        # Now update the actual dropdown widgets' values (not just the StringVar)
        # You may need to keep references to the Combobox widgets to do this
        self.vendor_combobox['values'] = ["All"] + filter_options.get('vendor', [])
        self.brand_combobox['values'] = ["All"] + filter_options.get('brand', [])
        # ...repeat for other filters

class TagListPanel(ttk.Frame):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self.create_widgets()
        
    def create_widgets(self):
        """Create the tag list panel widgets"""
        # Create tag panels container
        self.tags_frame = self.theme.create_frame(self)
        self.tags_frame.pack(fill="both", expand=True)
        
        # Available tags panel
        self.create_available_tags_panel()
        
        # Move buttons panel
        self.create_move_buttons_panel()
        
        # Selected tags panel
        self.create_selected_tags_panel()
        
        # Centered Download Excel button
        self.download_btn = self.theme.create_button(
            self,
            "Download Excel",
            self.on_download_excel,
            width=24
        )
        self.download_btn.pack(pady=20)
        
    def create_available_tags_panel(self):
        """Create the available tags panel"""
        self.available_panel = self.theme.create_frame(self.tags_frame)
        self.available_panel.pack(side="left", fill="both", expand=True)
        
        # Header
        self.theme.create_label(
            self.available_panel,
            "Available Tags",
            font=self.theme.fonts['subheading']
        ).pack(pady=(0, 10))
        
        # Select all checkbox
        self.available_tags_all = tk.BooleanVar(value=True)
        self.theme.create_checkbutton(
            self.available_panel,
            "Select All",
            self.available_tags_all
        ).pack(anchor="w", padx=5)
        
        # Tags list
        self.available_canvas = tk.Canvas(
            self.available_panel,
            bg=self.theme.colors['surface'],
            highlightthickness=0
        )
        self.available_canvas.pack(side="left", fill="both", expand=True)
        
        # Scrollbar
        self.available_scrollbar = ttk.Scrollbar(
            self.available_panel,
            orient="vertical",
            command=self.available_canvas.yview
        )
        self.available_scrollbar.pack(side="right", fill="y")
        
        # Configure canvas
        self.available_canvas.configure(yscrollcommand=self.available_scrollbar.set)
        
        # Container for tags
        self.available_tags_container = self.theme.create_frame(self.available_canvas)
        self.available_canvas.create_window(
            (0, 0),
            window=self.available_tags_container,
            anchor="nw"
        )
        # Make sure the container fills the canvas
        self.available_tags_container.pack(fill="both", expand=True)
        
    def create_move_buttons_panel(self):
        """Create the move buttons panel"""
        self.move_btn_frame = self.theme.create_frame(self.tags_frame, width=100)
        self.move_btn_frame.pack(side="left", fill="y", padx=10)
        
        # Button container
        self.button_container = self.theme.create_frame(self.move_btn_frame)
        self.button_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Create buttons
        self.theme.create_button(
            self.button_container,
            ">",
            self.on_move_to_selected
        ).pack(pady=5)
        
        self.theme.create_button(
            self.button_container,
            "<",
            self.on_move_to_available
        ).pack(pady=5)
        
        self.theme.create_button(
            self.button_container,
            "Clear",
            self.on_clear_selected
        ).pack(pady=5)
        
        self.theme.create_button(
            self.button_container,
            "Undo",
            self.on_undo
        ).pack(pady=5)
        
        self.theme.create_button(
            self.button_container,
            "?",
            self.on_show_instructions
        ).pack(pady=5)
        
    def create_selected_tags_panel(self):
        """Create the selected tags panel"""
        self.selected_panel = self.theme.create_frame(self.tags_frame)
        self.selected_panel.pack(side="left", fill="both", expand=True)
        
        # Header
        self.theme.create_label(
            self.selected_panel,
            "Selected Tags",
            font=self.theme.fonts['subheading']
        ).pack(pady=(0, 10))
        
        # Select all checkbox
        self.selected_tags_all = tk.BooleanVar(value=True)
        self.theme.create_checkbutton(
            self.selected_panel,
            "Select All",
            self.selected_tags_all
        ).pack(anchor="w", padx=5)
        
        # Tags list
        self.selected_canvas = tk.Canvas(
            self.selected_panel,
            bg=self.theme.colors['surface'],
            highlightthickness=0
        )
        self.selected_canvas.pack(side="left", fill="both", expand=True)
        
        # Scrollbar
        self.selected_scrollbar = ttk.Scrollbar(
            self.selected_panel,
            orient="vertical",
            command=self.selected_canvas.yview
        )
        self.selected_scrollbar.pack(side="right", fill="y")
        
        # Configure canvas
        self.selected_canvas.configure(yscrollcommand=self.selected_scrollbar.set)
        
        # Container for tags
        self.selected_tags_container = self.theme.create_frame(self.selected_canvas)
        self.selected_canvas.create_window(
            (0, 0),
            window=self.selected_tags_container,
            anchor="nw"
        )
        # Make sure the container fills the canvas
        self.selected_tags_container.pack(fill="both", expand=True)
        
    def on_move_to_selected(self):
        """Move selected tags to selected panel"""
        # This functionality is handled by the web interface
        pass
        
    def on_move_to_available(self):
        """Move selected tags back to available panel"""
        # This functionality is handled by the web interface
        pass
        
    def on_clear_selected(self):
        """Clear all selected tags"""
        # This functionality is handled by the web interface
        pass
        
    def on_undo(self):
        """Undo last action"""
        # This functionality is handled by the web interface
        pass
        
    def on_show_instructions(self):
        """Show instructions popup"""
        # This functionality is handled by the web interface
        pass

    def on_download_excel(self):
        """Download the processed Excel file (placeholder)"""
        # This functionality is handled by the web interface
        pass

    def populate_selected_tags(self, tag_names):
        """Populate the selected tags panel with a list of tag names, sorted by lineage, price, then alphabetically."""
        # Clear the current selected tags container
        for widget in self.selected_tags_container.winfo_children():
            widget.destroy()

        # Try to access the DataFrame from the FileUploadPanel (assume parent.main_frame.file_panel.df)
        df = None
        parent = self.master
        while parent is not None:
            if hasattr(parent, 'file_panel') and hasattr(parent.file_panel, 'df'):
                df = parent.file_panel.df
                break
            parent = getattr(parent, 'master', None)

        # Define the desired lineage order
        lineage_order = [
            "SATIVA", "HYBRID/SATIVA", "HYBRID", "HYBRID/INDICA", "INDICA", "CBD", "MIXED", "PARAPHERNALIA"
        ]
        lineage_rank = {lin: i for i, lin in enumerate(lineage_order)}

        def get_lineage(name):
            if df is not None and "Product Name*" in df.columns and "Lineage" in df.columns:
                try:
                    val = str(df.loc[df["Product Name*"] == name, "Lineage"].iloc[0]).upper()
                except Exception:
                    val = "MIXED"
                # Treat CBD_BLEND as CBD
                if val == "CBD_BLEND":
                    val = "CBD"
                if val not in lineage_rank:
                    val = "MIXED"
                return val
            return "MIXED"

        def get_price(name):
            if df is not None and "Product Name*" in df.columns and "Price" in df.columns:
                try:
                    price_val = df.loc[df["Product Name*"] == name, "Price"].iloc[0]
                    return float(price_val) if price_val not in [None, "", "nan"] else float('inf')
                except Exception:
                    return float('inf')
            return float('inf')

        # Sort tag_names by lineage order, then price (ascending), then alphabetically
        tag_names_sorted = sorted(
            tag_names,
            key=lambda name: (
                lineage_rank.get(get_lineage(name), 99),
                get_price(name),
                name
            )
        )

        # Add each tag as a label (customize as needed)
        for name in tag_names_sorted:
            lbl = tk.Label(self.selected_tags_container, text=name, bg=self.theme.colors['surface'], fg=self.theme.colors['text'])
            lbl.pack(fill="x", padx=5, pady=2)

class ActionPanel(ttk.Frame):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self.create_widgets()
        
    def create_widgets(self):
        """Create the action panel widgets"""
        # Vendor back checkbox
        self.print_vendor_back = tk.BooleanVar(value=False)
        self.theme.create_checkbutton(
            self,
            "Print Vendor to Back",
            self.print_vendor_back
        ).pack(pady=10, anchor="w")
        
        # Scale factor
        self.theme.create_label(
            self,
            "Font Scale Factor",
            font=self.theme.fonts['body']
        ).pack(pady=(10, 0))
        
        self.scale_factor = tk.DoubleVar(value=1.0)
        self.scale_slider = self.theme.create_scale(
            self,
            from_=0.5,
            to=2.0,
            resolution=0.05,
            orient="horizontal",
            length=180,
            command=self.on_scale_change
        )
        self.scale_slider.pack(pady=(0, 10))
        
        # Reset scale button
        self.theme.create_button(
            self,
            "Reset Scale",
            lambda: self.on_scale_change(1.0)
        ).pack(pady=(0, 20))
        
        # Action buttons
        self.theme.create_button(
            self,
            "Horizontal Tags",
            lambda: self.on_generate_tags("horizontal")
        ).pack(pady=10, fill="x")
        
        self.theme.create_button(
            self,
            "Vertical Tags",
            lambda: self.on_generate_tags("vertical")
        ).pack(pady=10, fill="x")
        
        self.theme.create_button(
            self,
            "Mini Tags",
            lambda: self.on_generate_tags("mini")
        ).pack(pady=10, fill="x")
        
    def on_scale_change(self, value):
        """Handle scale factor changes"""
        self.scale_factor.set(float(value))
        # This functionality is handled by the web interface
        
    def on_generate_tags(self, tag_type):
        """Generate tags of specified type"""
        # This functionality is handled by the web interface
        pass 

def render_tag_row_with_emoji(parent, tag):
    """
    Render a single tag row with the product type emoji and name, plus other tag info.
    Args:
        parent: The parent tkinter frame to add the row to.
        tag: The tag dictionary (should have 'productType' key).
    """
    product_type = tag.get('productType', '').strip().lower()
    emoji = PRODUCT_TYPE_EMOJIS.get(product_type, '')
    display_text = product_type.title()
    row = tk.Frame(parent)
    row.pack(fill="x", pady=2)
    # Product type label with emoji
    tk.Label(row, text=display_text, font=("Arial", 12, "bold"), anchor="w").pack(side="left", padx=6)
    # Add more tag info as needed, e.g. product name, weight, etc.
    # Example:
    product_name = tag.get('Product Name*', '')
    tk.Label(row, text=product_name, font=("Arial", 12), anchor="w").pack(side="left", padx=6)
    # You can add more fields here as desired
    return row 