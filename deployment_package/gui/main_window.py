import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional
import logging

from src.core.data.excel_processor import ExcelProcessor
from src.gui.components.filter_panel import FilterPanel
from src.gui.components.tag_panel import TagPanel
from src.gui.components.action_panel import ActionPanel

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.excel_processor = ExcelProcessor()
        self._setup_ui()
        self._bind_events()
        self._load_default_file()
        
    def _setup_ui(self):
        self.root.title("AGT Price Tag Transformer")
        self.root.geometry("1200x800")
        self.root.configure(bg="#228B22")
        
        # Create frames
        self.left_frame = FilterPanel(self.root, self.on_filter_change)
        self.center_frame = TagPanel(self.root)
        self.right_frame = ActionPanel(self.root)
        
        self._layout_frames()

    def _load_default_file(self):
        downloads_dir = Path.home() / "Downloads"
        matching_files = sorted(
            downloads_dir.glob("A Greener Today*.xlsx"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        
        if matching_files:
            try:
                self.excel_processor.load_file(matching_files[0])
                self.left_frame.populate_dropdowns()
                self.center_frame.populate_tags()
                logging.debug(f"Default file loaded: {matching_files[0]}")
            except Exception as e:
                logging.error(f"Error reading default file: {e}")
                messagebox.showerror("Error", f"Failed to load default file: {e}")