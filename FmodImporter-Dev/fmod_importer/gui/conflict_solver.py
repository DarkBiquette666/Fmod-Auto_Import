"Conflict Solver Module
Provides a dialog to resolve filename conflicts when multiple files have the same name.
"

import os
import tkinter as tk
from tkinter import ttk

class ConflictResolutionDialog(tk.Toplevel):
    """
    Modal dialog to resolve file conflicts.
    
    Args:
        parent: Parent window
        conflicts: Dictionary {filename: [full_path1, full_path2, ...]}}
        media_root: Root directory to calculate relative paths for display
    """
    def __init__(self, parent, conflicts, media_root):
        super().__init__(parent)
        self.title("Resolve File Conflicts")
        self.geometry("600x500")
        self.transient(parent)
        self.grab_set()
        
        self.conflicts = conflicts
        self.media_root = media_root
        self.result = None  # Will hold {filename: selected_full_path}
        
        self._create_widgets()
        
        # Center the window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
        # Handle X button as cancel
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Block until closed
        self.wait_window(self)

    def _create_widgets(self):
        # Header
        header_frame = ttk.Frame(self, padding=10)
        header_frame.pack(fill=tk.X)
        
        ttk.Label(
            header_frame, 
            text="⚠️ Duplicate filenames detected", 
            font=('TkDefaultFont', 10, 'bold'),
            foreground="#FF8C00" # Dark Orange
        ).pack(anchor=tk.W)
        
        ttk.Label(
            header_frame, 
            text="The following files appear in multiple locations.\nPlease select which version to use for import:", 
            padding=(0, 5)
        ).pack(anchor=tk.W)
        
        # Scrollable container
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Mousewheel support
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=canvas.winfo_reqwidth())
        
        # Configure resizing
        def _on_canvas_configure(event):
            canvas.itemconfig(canvas.find_withtag("all")[0], width=event.width)
        
        canvas.bind("<Configure>", _on_canvas_configure)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate conflicts
        self.selections = {} # filename -> StringVar
        
        for filename in sorted(self.conflicts.keys()):
            paths = self.conflicts[filename]
            
            # Frame for this file
            file_frame = ttk.LabelFrame(self.scrollable_frame, text=filename, padding=5)
            file_frame.pack(fill=tk.X, expand=True, pady=5, padx=5)
            
            # Variable for selection (default to first)
            var = tk.StringVar(value=paths[0])
            self.selections[filename] = var
            
            for path in paths:
                # Display relative path for readability
                try:
                    rel_path = os.path.relpath(path, self.media_root)
                except ValueError:
                    rel_path = path # Fallback if different drive
                
                # Use a Frame for the radio button to ensure proper layout
                rb_frame = ttk.Frame(file_frame)
                rb_frame.pack(fill=tk.X, anchor=tk.W)
                
                rb = ttk.Radiobutton(rb_frame, text=rel_path, variable=var, value=path)
                rb.pack(anchor=tk.W, padx=10, pady=2)
        
        # Footer / Buttons
        btn_frame = ttk.Frame(self, padding=15)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Confirm Selection", command=self._on_confirm).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel Analysis", command=self._on_cancel).pack(side=tk.RIGHT, padx=5)

    def _on_confirm(self):
        # Unbind global mousewheel
        self.unbind_all("<MouseWheel>")
        
        # Gather results
        self.result = {fname: var.get() for fname, var in self.selections.items()}
        self.destroy()

    def _on_cancel(self):
        # Unbind global mousewheel
        self.unbind_all("<MouseWheel>")
        
        self.result = None
        self.destroy()
