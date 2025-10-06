import tkinter as tk
from tkinter import ttk

class Theme:
    def __init__(self):
        # Color palette
        self.colors = {
            'primary': '#2196F3',      # Blue
            'secondary': '#FF4081',    # Pink
            'background': '#121212',   # Dark background
            'surface': '#1E1E1E',      # Slightly lighter dark
            'text': '#FFFFFF',         # White text
            'text_secondary': '#B0B0B0', # Gray text
            'accent': '#00BCD4',       # Cyan
            'error': '#F44336',        # Red
            'success': '#4CAF50',      # Green
            'warning': '#FFC107',      # Amber
        }
        
        # Font definitions
        self.fonts = {
            'heading': ('Helvetica', 24, 'bold'),
            'subheading': ('Helvetica', 18, 'bold'),
            'body': ('Helvetica', 12),
            'small': ('Helvetica', 10),
            'button': ('Helvetica', 12, 'bold'),
        }
        
        # Configure ttk styles
        self._configure_styles()
        
    def _configure_styles(self):
        """Configure ttk styles for modern look"""
        style = ttk.Style()
        
        # Configure common elements
        style.configure(
            '.',
            background=self.colors['background'],
            foreground=self.colors['text'],
            font=self.fonts['body']
        )
        
        # Button style
        style.configure(
            'Modern.TButton',
            background=self.colors['primary'],
            foreground=self.colors['text'],
            font=self.fonts['button'],
            padding=10,
            borderwidth=0
        )
        style.map(
            'Modern.TButton',
            background=[('active', self.colors['accent'])],
            foreground=[('active', self.colors['text'])]
        )
        
        # Entry style
        style.configure(
            'Modern.TEntry',
            fieldbackground=self.colors['surface'],
            foreground=self.colors['text'],
            borderwidth=0,
            padding=5
        )
        
        # Combobox style
        style.configure(
            'Modern.TCombobox',
            background=self.colors['surface'],
            foreground=self.colors['text'],
            arrowcolor=self.colors['text'],
            borderwidth=0,
            padding=5
        )
        style.map(
            'Modern.TCombobox',
            fieldbackground=[('readonly', self.colors['surface'])],
            selectbackground=[('readonly', self.colors['primary'])]
        )
        
        # Checkbutton style
        style.configure(
            'Modern.TCheckbutton',
            background=self.colors['background'],
            foreground=self.colors['text'],
            indicatorcolor=self.colors['surface'],
            indicatorbackground=self.colors['surface']
        )
        style.map(
            'Modern.TCheckbutton',
            indicatorcolor=[('selected', self.colors['primary'])],
            indicatorbackground=[('selected', self.colors['primary'])]
        )
        
        # Scale style
        style.configure(
            'Modern.TScale',
            background=self.colors['background'],
            troughcolor=self.colors['surface'],
            sliderthickness=20,
            borderwidth=0
        )
        
    def create_button(self, parent, text, command=None, **kwargs):
        """Create a modern button"""
        btn = ttk.Button(
            parent,
            text=text,
            command=command,
            style='Modern.TButton',
            **kwargs
        )
        return btn
        
    def create_entry(self, parent, **kwargs):
        """Create a modern entry widget"""
        entry = ttk.Entry(
            parent,
            style='Modern.TEntry',
            **kwargs
        )
        return entry
        
    def create_combobox(self, parent, **kwargs):
        """Create a modern combobox"""
        combo = ttk.Combobox(
            parent,
            style='Modern.TCombobox',
            **kwargs
        )
        return combo
        
    def create_checkbutton(self, parent, text, variable, **kwargs):
        """Create a modern checkbutton"""
        check = ttk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            style='Modern.TCheckbutton',
            **kwargs
        )
        return check
        
    def create_scale(self, parent, **kwargs):
        """Create a modern scale widget"""
        scale = ttk.Scale(
            parent,
            style='Modern.TScale',
            **kwargs
        )
        return scale
        
    def create_label(self, parent, text, font=None, **kwargs):
        """Create a modern label"""
        if font is None:
            font = self.fonts['body']
        label = tk.Label(
            parent,
            text=text,
            font=font,
            bg=self.colors['background'],
            fg=self.colors['text'],
            **kwargs
        )
        return label
        
    def create_frame(self, parent, **kwargs):
        """Create a modern frame"""
        frame = tk.Frame(
            parent,
            bg=self.colors['background'],
            **kwargs
        )
        return frame 