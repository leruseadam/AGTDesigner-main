import os
import logging
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from ..utils.excel_utils import preprocess_excel

class LineageEditor:
    """Editor for managing product lineages in the tag maker application."""

    LINEAGE_MAP = {
        "SATIVA": {
            "abbr": "(S)",
            "color": "#E74C3C",
            "display": "Sativa"
        },
        "INDICA": {
            "abbr": "(I)", 
            "color": "#8E44AD",
            "display": "Indica"
        },
        "HYBRID": {
            "abbr": "(H)",
            "color": "#27AE60",
            "display": "Hybrid"
        },
        "HYBRID/SATIVA": {
            "abbr": "(S/H)",
            "color": "#E74C3C",
            "display": "Hybrid/Sativa"
        },
        "HYBRID/INDICA": {
            "abbr": "(I/H)",
            "color": "#8E44AD",
            "display": "Hybrid/Indica"
        },
        "CBD": {
            "abbr": "(CBD)",
            "color": "#F1C40F",
            "display": "CBD"
        },
        "MIXED": {
            "abbr": "(M)",
            "color": "#1E3A8A",
            "display": "Mixed"
        },
        "PARAPHERNALIA": {
            "abbr": "(P)",
            "color": "#FF69B4",
            "display": "Paraphernalia"
        }
    }

    ABBREVIATED_LINEAGE = {
        "SATIVA": "S",
        "INDICA": "I",
        "HYBRID": "H",
        "HYBRID/SATIVA": "H/S",
        "HYBRID/INDICA": "H/I",
        "CBD": "CBD",
        "CBD_BLEND": "CBD",
        "MIXED": "THC",
        "PARAPHERNALIA": "P"
    }

    # Reverse mapping for abbreviation to full value
    ABBR_TO_LINEAGE = {v: k for k, v in ABBREVIATED_LINEAGE.items()}
    # Special case: both 'CBD' and 'CBD_BLEND' abbreviate to 'CBD', so map 'CBD' to 'CBD'
    ABBR_TO_LINEAGE['CBD'] = 'CBD'

    def __init__(self, root, df, file_entry):
        """Initialize LineageEditor with main window and data references."""
        self.root = root
        self.df = df
        self.file_entry = file_entry
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.log_path = os.path.expanduser("~/Downloads/lineage_changes_log.csv")
        self.popup = None
        self.canvas = None
        self.inner_frame = None
        self.popup_vars = {}

    def show(self, selected_tags_vars):
        """Display the lineage editor dialog."""
        if self.df is None or self.df.empty:
            messagebox.showerror("Error", "No Excel file is loaded.")
            return

        self.popup = tk.Toplevel(self.root)
        self.popup.title("Change Lineage")
        self.popup.geometry("900x800")
        self.popup.protocol("WM_DELETE_WINDOW", self._on_close)

        self._setup_ui(selected_tags_vars)

        # Center window
        self.popup.update_idletasks()
        width = self.popup.winfo_width()
        height = self.popup.winfo_height()
        x = (self.popup.winfo_screenwidth() // 2) - (width // 2)
        y = (self.popup.winfo_screenheight() // 2) - (height // 2)
        self.popup.geometry(f'{width}x{height}+{x}+{y}')

        self.popup.grab_set()
        self.popup.wait_window()

    def _on_close(self):
        """Handle window close."""
        if messagebox.askokcancel("Quit", "Do you want to close without saving?"):
            self.popup.destroy()

    def _setup_ui(self, selected_tags_vars):
        """Set up the UI components."""
        self.canvas, self.inner_frame = self._create_scrollable_frame()
        self.popup_vars = {}
        self._populate_rows(self.inner_frame, selected_tags_vars)
        self._add_buttons()

    def _create_scrollable_frame(self):
        """Create scrollable frame with improved scrolling."""
        container = tk.Frame(self.popup, bg="white")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

        inner_frame = tk.Frame(canvas, bg="white")

        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_mousewheel(event):
            if canvas.winfo_height() < inner_frame.winfo_height():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        inner_frame.bind("<Configure>", _on_frame_configure)
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return canvas, inner_frame

    def _populate_rows(self, inner_frame, selected_tags_vars):
        """Populate rows with lineage options."""
        old_map = self._get_current_lineages(selected_tags_vars)

        for name in sorted(selected_tags_vars):
            old_lin = old_map.get(name, "MIXED")

            # Treat CBD_BLEND as CBD for UI
            if old_lin == "CBD_BLEND":
                old_lin = "CBD"

            # Handle paraphernalia special case
            try:
                prod_type = str(self.df.loc[
                    self.df["Product Name*"] == name, "Product Type*"
                ].iloc[0]).strip().lower()
            except Exception:
                prod_type = ""

            if prod_type == "paraphernalia":
                old_lin = "PARAPHERNALIA"

            lineage_info = self.LINEAGE_MAP.get(old_lin, {"abbr": "", "color": "#BDC3C7"})
            abbr = self.ABBREVIATED_LINEAGE.get(old_lin, "")
            bg = lineage_info.get("color", "#BDC3C7")

            # Create row
            row = tk.Frame(inner_frame, bg=bg)
            row.pack(fill="x", pady=2)

            # Add label
            label = tk.Label(
                row,
                text=f"{name}  {abbr}",
                bg=bg,
                fg="white",
                font=("Arial", 16, "bold"),
                anchor="w",
                padx=6,
                pady=4
            )
            label.pack(side="left", fill="x", expand=True)

            # Add combobox
            var = tk.StringVar(value=abbr)
            self.popup_vars[name] = var

            # Only show unique, abbreviated options (CBD and CBD_BLEND as one)
            lineage_keys = [k for k in self.LINEAGE_MAP.keys() if k != "CBD_BLEND"]
            abbr_values = [self.ABBREVIATED_LINEAGE.get(k, k) for k in lineage_keys]
            combo = ttk.Combobox(
                row,
                textvariable=var,
                values=abbr_values,
                state="readonly",
                width=6
            )
            combo.pack(side="right", padx=6, pady=4)

            # Map selection back to full lineage value
            def on_select(event, var=var, abbr_values=abbr_values):
                abbr = var.get()
                full_value = self.ABBR_TO_LINEAGE.get(abbr, "MIXED")
                var.set(abbr)  # keep the abbreviation in the combobox
                # Store the full value for saving
                self.popup_vars[name] = full_value
            combo.bind('<<ComboboxSelected>>', on_select)

        # After all combos, update popup_vars to map names to full values
        for name in self.popup_vars:
            abbr = self.popup_vars[name].get() if isinstance(self.popup_vars[name], tk.StringVar) else self.popup_vars[name]
            self.popup_vars[name] = self.ABBR_TO_LINEAGE.get(abbr, "MIXED")

    def _add_buttons(self):
        """Add Save/Cancel buttons."""
        btn_frame = tk.Frame(self.popup, bg="white")
        btn_frame.pack(fill="x", pady=10)

        tk.Button(
            btn_frame,
            text="Save Changes",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="green",
            padx=10,
            pady=5,
            command=self._save_changes
        ).pack(side="right", padx=10)

        tk.Button(
            btn_frame,
            text="Cancel",
            font=("Arial", 12),
            command=self.popup.destroy
        ).pack(side="right")

    def _save_changes(self):
        """Save lineage changes."""
        df2 = self.df.copy()
        timestamp = datetime.datetime.now().isoformat()

        changes_made = False
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

        with open(self.log_path, "a", encoding="utf-8") as log:
            for name, var in self.popup_vars.items():
                new_lin = var.get().upper()
                try:
                    old_lin = str(df2.loc[
                        df2["Product Name*"] == name, "Lineage"
                    ].iloc[0])
                except Exception:
                    old_lin = ""
                if new_lin != old_lin:
                    changes_made = True
                    df2.loc[df2["Product Name*"] == name, "Lineage"] = new_lin

                    if new_lin == "MIXED":
                        df2.loc[df2["Product Name*"] == name, "Product Type*"] = "Mixed"

                    log.write(f"{timestamp},{name},{old_lin},{new_lin}\n")

        if changes_made:
            # --- NEW: Always save lineage changes to shared data if running in same process ---
            try:
                from app import save_shared_data
                save_shared_data(df2)
            except Exception as e:
                # Warning: Could not save shared data from LineageEditor: {e}
            self._background_save(df2)
        else:
            self.popup.destroy()

    def _background_save(self, df2):
        """Save changes in background thread."""
        def save_and_reload():
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = os.path.expanduser(f"~/Downloads/{timestamp}_LineageUpdated.xlsx")
            df2.to_excel(out_path, index=False)
            cleaned = preprocess_excel(out_path)
            return out_path, pd.read_excel(cleaned, engine="openpyxl")

        future = self.executor.submit(save_and_reload)

        def on_done(fut):
            try:
                out_path, new_df = fut.result()
            except Exception as e:
                messagebox.showerror("Error", f"Save/Reload failed: {e}")
                return

            # Update global state
            global global_df
            global_df = new_df

            # Update UI
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, out_path)

            messagebox.showinfo(
                "Success",
                f"Saved to:\n{out_path}\n\n"
                f"Changes logged to:\n{self.log_path}"
            )
            self.popup.destroy()

        future.add_done_callback(lambda f: self.root.after_idle(lambda: on_done(f)))

    def _get_current_lineages(self, selected_tags_vars):
        """Get current lineages for selected tags."""
        result = {}
        for name in selected_tags_vars:
            try:
                val = str(self.df.loc[
                    self.df["Product Name*"] == name, "Lineage"
                ].iloc[0]).upper()
            except Exception:
                val = "MIXED"
            result[name] = val
        return result

    @staticmethod
    def _get_lineage_color(lineage):
        """Get color for lineage from map."""
        return LineageEditor.LINEAGE_MAP.get(lineage, {"abbr": "", "color": "#BDC3C7"}).get("color")