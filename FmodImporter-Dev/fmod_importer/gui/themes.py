"""
GUI Themes Module
Handles theme management (Light/Dark mode) for FmodImporterGUI.
"""

import tkinter as tk
from tkinter import ttk

class ThemeManager:
    """
    Manages application themes (colors, styles).
    """

    # Color Palettes
    COLORS = {
        'light': {
            'bg': '#f0f0f0',           # Window background
            'fg': '#000000',           # Text color
            'input_bg': '#ffffff',     # Entry/Listbox background
            'input_fg': '#000000',     # Entry/Listbox text
            'select_bg': '#0078d7',    # Selection background
            'select_fg': '#ffffff',    # Selection text
            'gray': '#808080',         # Disabled/Placeholder text
            'frame_bg': '#f0f0f0',     # Frame background (matches default)
            'button_bg': '#e1e1e1',    # Button background (Windows default-ish)
        },
        'dark': {
            'bg': '#2b2b2b',           # Dark gray background
            'fg': '#e0e0e0',           # Light gray text
            'input_bg': '#3c3c3c',     # Slightly lighter for inputs
            'input_fg': '#ffffff',     # White text
            'select_bg': '#406080',    # Muted blue for selection
            'select_fg': '#ffffff',    # White text
            'gray': '#a0a0a0',         # Lighter gray for placeholders
            'frame_bg': '#2b2b2b',     # Dark gray
            'button_bg': '#444444',    # Dark button
        }
    }

    # Current active theme
    CURRENT_THEME = 'light'

    @staticmethod
    def apply_theme(root: tk.Tk, theme_name: str = 'light'):
        """
        Apply the specified theme to the root window and all children.
        
        Args:
            root: The root Tk window
            theme_name: 'light' or 'dark'
        """
        if theme_name not in ThemeManager.COLORS:
            theme_name = 'light'
        
        ThemeManager.CURRENT_THEME = theme_name
        colors = ThemeManager.COLORS[theme_name]
        style = ttk.Style(root)
        
        # Configure standard Tkinter widgets globally options
        # This acts as a default for new widgets
        root.option_add("*Background", colors['bg'])
        root.option_add("*Foreground", colors['fg'])
        root.option_add("*Entry.Background", colors['input_bg'])
        root.option_add("*Entry.Foreground", colors['input_fg'])
        root.option_add("*Listbox.Background", colors['input_bg'])
        root.option_add("*Listbox.Foreground", colors['input_fg'])
        root.option_add("*Text.Background", colors['input_bg'])
        root.option_add("*Text.Foreground", colors['input_fg'])
        root.option_add("*Button.Background", colors['button_bg'])
        root.option_add("*Button.Foreground", colors['fg'])
        
        # Configure Root window
        root.configure(bg=colors['bg'])
        
        # Configure Ttk Styles
        if theme_name == 'dark':
             # Use 'clam' or 'alt' as base for dark mode since 'vista'/'winnative' 
             # are hard to override colors on Windows
            try:
                style.theme_use('clam')
            except:
                pass
            
            # General Ttk configuration
            style.configure('.',
                background=colors['bg'],
                foreground=colors['fg'],
                fieldbackground=colors['input_bg'],
                darkcolor=colors['bg'],
                lightcolor=colors['bg'],
                selectbackground=colors['select_bg'],
                selectforeground=colors['select_fg'],
            )
            
            # Specific Widgets
            style.configure('TFrame', background=colors['bg'])
            style.configure('TLabelframe', background=colors['bg'], foreground=colors['fg'])
            style.configure('TLabelframe.Label', background=colors['bg'], foreground=colors['fg'])
            style.configure('TLabel', background=colors['bg'], foreground=colors['fg'])
            style.configure('TButton', background=colors['button_bg'], foreground=colors['fg'], borderwidth=1)
            style.map('TButton',
                background=[('active', '#555555'), ('pressed', '#666666')],
                foreground=[('disabled', colors['gray'])]
            )
            style.configure('TEntry', fieldbackground=colors['input_bg'], foreground=colors['input_fg'])
            style.configure('TCheckbutton', background=colors['bg'], foreground=colors['fg'])
            style.map('TCheckbutton', background=[('active', colors['bg'])])
            
            # Treeview
            style.configure('Treeview', 
                background=colors['input_bg'], 
                foreground=colors['input_fg'], 
                fieldbackground=colors['input_bg']
            )
            style.map('Treeview', 
                background=[('selected', colors['select_bg'])], 
                foreground=[('selected', colors['select_fg'])]
            )
            style.configure('Treeview.Heading', 
                background=colors['button_bg'], 
                foreground=colors['fg'],
                relief="flat"
            )
            
        else:
            # Light mode - usually default system theme
            # On Windows, 'vista' or 'winnative' is good
            if 'vista' in style.theme_names():
                style.theme_use('vista')
            elif 'winnative' in style.theme_names():
                style.theme_use('winnative')
            else:
                style.theme_use('default')
                
            # Allow system defaults to take over, but enforce our palette where possible
            # if explicit overrides are needed. For now, rely on system default for Light.
            
            # Checkbox background fix for some themes
            style.configure('TCheckbutton', background=colors['bg'])
            style.configure('TFrame', background=colors['bg'])

        # Apply Combobox styling
        ThemeManager._apply_combobox_style(root, colors, theme_name)

    @staticmethod
    def _apply_combobox_style(root, colors, theme_name):
        """Apply specific styling for Comboboxes and their popdowns"""
        style = ttk.Style(root)
        
        if theme_name == 'dark':
            # Main Combobox style
            style.configure('TCombobox', 
                fieldbackground=colors['input_bg'],
                background=colors['button_bg'], # Arrow button bg
                foreground=colors['input_fg'],
                arrowcolor=colors['fg']
            )
            style.map('TCombobox', 
                fieldbackground=[('readonly', colors['input_bg'])],
                foreground=[('readonly', colors['input_fg'])],
                background=[('active', colors['button_bg'])]
            )
            
            # Popdown Listbox styling (Native Tk widget, not Ttk)
            # This is global for the application
            root.option_add('*TCombobox*Listbox.background', colors['input_bg'])
            root.option_add('*TCombobox*Listbox.foreground', colors['input_fg'])
            root.option_add('*TCombobox*Listbox.selectBackground', colors['select_bg'])
            root.option_add('*TCombobox*Listbox.selectForeground', colors['select_fg'])
        else:
            # Reset/Default for light mode
            # We can't easily "reset" option_add, so we overwrite with light colors
            root.option_add('*TCombobox*Listbox.background', colors['input_bg'])
            root.option_add('*TCombobox*Listbox.foreground', colors['input_fg'])
            root.option_add('*TCombobox*Listbox.selectBackground', colors['select_bg'])
            root.option_add('*TCombobox*Listbox.selectForeground', colors['select_fg'])

        # Recursive update for existing widgets that don't respect global options automatically
        # (Tkinter standard widgets created *before* option_add might need config update)
        # But usually apply_theme is called at startup or triggers a restart/reload.
        # For dynamic switching, we'd need to iterate widgets.

    @staticmethod
    def get_color(key: str, theme_name: str = None) -> str:
        """Get a specific color from the theme palette"""
        if theme_name is None:
            theme_name = ThemeManager.CURRENT_THEME
            
        if theme_name not in ThemeManager.COLORS:
            theme_name = 'light'
        return ThemeManager.COLORS[theme_name].get(key, '#ff00ff') # Magenta debug default
