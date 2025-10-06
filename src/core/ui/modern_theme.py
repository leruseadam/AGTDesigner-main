import tkinter as tk
from tkinter import ttk
import colorsys

# Modern color palette
COLORS = {
    'primary': '#2E7D32',  # Deep green
    'primary_light': '#4CAF50',
    'primary_dark': '#1B5E20',
    'accent': '#FF4081',   # Pink accent
    'background': '#F5F5F5',
    'surface': '#FFFFFF',
    'text': '#212121',
    'text_secondary': '#757575',
    'error': '#D32F2F',
    'success': '#388E3C',
    'warning': '#FFA000',
    'info': '#1976D2'
}

# Modern fonts
FONTS = {
    'heading': ('Helvetica', 24, 'bold'),
    'subheading': ('Helvetica', 18, 'bold'),
    'body': ('Helvetica', 12),
    'button': ('Helvetica', 14, 'bold'),
    'small': ('Helvetica', 10)
}

def create_modern_button(parent, text, command, **kwargs):
    """Create a modern-looking button with hover effects."""
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=COLORS['primary'],
        fg='white',
        font=FONTS['button'],
        relief='flat',
        padx=20,
        pady=10,
        cursor='hand2',
        **kwargs
    )
    
    def on_enter(e):
        btn['bg'] = COLORS['primary_light']
        
    def on_leave(e):
        btn['bg'] = COLORS['primary']
        
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    
    return btn

def create_modern_frame(parent, **kwargs):
    """Create a modern frame with subtle shadow effect."""
    frame = tk.Frame(
        parent,
        bg=COLORS['surface'],
        relief='flat',
        **kwargs
    )
    return frame

def create_modern_label(parent, text, **kwargs):
    """Create a modern label with consistent styling."""
    label = tk.Label(
        parent,
        text=text,
        bg=COLORS['surface'],
        fg=COLORS['text'],
        font=FONTS['body'],
        **kwargs
    )
    return label

def create_modern_entry(parent, **kwargs):
    """Create a modern entry widget with consistent styling."""
    entry = tk.Entry(
        parent,
        bg=COLORS['surface'],
        fg=COLORS['text'],
        font=FONTS['body'],
        relief='flat',
        highlightthickness=1,
        highlightbackground=COLORS['primary_light'],
        **kwargs
    )
    return entry

def create_modern_checkbutton(parent, text, variable, **kwargs):
    """Create a modern checkbutton with consistent styling."""
    cb = tk.Checkbutton(
        parent,
        text=text,
        variable=variable,
        bg=COLORS['surface'],
        fg=COLORS['text'],
        font=FONTS['body'],
        selectcolor=COLORS['primary_light'],
        activebackground=COLORS['surface'],
        activeforeground=COLORS['text'],
        **kwargs
    )
    return cb

def create_modern_scale(parent, **kwargs):
    """Create a modern scale widget with consistent styling."""
    scale = tk.Scale(
        parent,
        bg=COLORS['surface'],
        fg=COLORS['text'],
        troughcolor=COLORS['primary_light'],
        highlightthickness=0,
        **kwargs
    )
    return scale

def apply_modern_theme(root):
    """Apply modern theme to the root window."""
    root.configure(bg=COLORS['background'])
    
    # Configure ttk styles
    style = ttk.Style()
    style.configure(
        'Modern.TButton',
        font=FONTS['button'],
        background=COLORS['primary'],
        foreground='white'
    )
    
    style.configure(
        'Modern.TLabel',
        font=FONTS['body'],
        background=COLORS['surface'],
        foreground=COLORS['text']
    )
    
    style.configure(
        'Modern.TFrame',
        background=COLORS['surface']
    )
    
    style.configure(
        'Modern.TNotebook',
        background=COLORS['surface'],
        tabmargins=[2, 5, 2, 0]
    )
    
    style.configure(
        'Modern.TNotebook.Tab',
        padding=[10, 5],
        font=FONTS['body']
    ) 