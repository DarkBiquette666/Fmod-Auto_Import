"""
GUI Widgets Mixin Module
Handles widget creation and placeholder management for FmodImporterGUI.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .themes import ThemeManager


class WidgetsMixin:
    """
    Mixin class providing widget creation and placeholder utilities.

    These methods are mixed into FmodImporterGUI via multiple inheritance.
    All methods access shared state through 'self'.
    """

    def _create_widgets(self):
        """Create GUI widgets"""
        # Import here to avoid circular imports
        from .. import VERSION
        from ..naming import NamingPattern

        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # ==================== SECTION 1: PRESETS ====================
        presets_frame = ttk.LabelFrame(main_frame, text="Presets", padding="10")
        presets_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(presets_frame, text="Configuration Preset:").grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))

        # Preset combobox with buttons
        preset_controls_frame = ttk.Frame(presets_frame)
        preset_controls_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)

        self.preset_var = tk.StringVar(value="(No preset selected)")
        self.preset_combobox = ttk.Combobox(
            preset_controls_frame,
            textvariable=self.preset_var,
            state='readonly',
            width=50
        )
        self.preset_combobox.grid(row=0, column=0, padx=(0, 5))
        self.preset_combobox.bind('<<ComboboxSelected>>',
            lambda e: self.load_selected_preset())

        ttk.Button(preset_controls_frame, text="Save...",
                   command=self.open_preset_save_dialog, width=10).grid(
            row=0, column=1, padx=5)
        ttk.Button(preset_controls_frame, text="Manage...",
                   command=self.open_presets_manager, width=10).grid(
            row=0, column=2, padx=5)

        presets_frame.columnconfigure(1, weight=1)

        # ==================== SECTION 2: PATHS ====================
        paths_frame = ttk.LabelFrame(main_frame, text="Paths", padding="10")
        paths_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # FMOD Project
        ttk.Label(paths_frame, text="FMOD Project (.fspro):").grid(row=0, column=0, sticky=tk.W, pady=5)
        project_frame = ttk.Frame(paths_frame)
        project_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.project_entry = ttk.Entry(project_frame, width=40)
        self.project_entry.grid(row=0, column=0, padx=(0, 5))
        ttk.Button(project_frame, text="Browse...", command=self.browse_project).grid(row=0, column=1, padx=5)
        ttk.Button(project_frame, text="Load", command=self.load_project).grid(row=0, column=2, padx=5)
        ttk.Button(project_frame, text="Reload Scripts", command=self.reload_fmod_scripts).grid(row=0, column=3, padx=5)

        # Media Files Directory
        ttk.Label(paths_frame, text="Media Files Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        media_frame = ttk.Frame(paths_frame)
        media_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.media_entry = ttk.Entry(media_frame, width=60)
        self.media_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(media_frame, text="Browse...", command=self.browse_media).grid(row=0, column=1, padx=5)
        media_frame.columnconfigure(0, weight=1)

        # FMOD Studio Executable
        ttk.Label(paths_frame, text="FMOD Studio Executable:").grid(row=2, column=0, sticky=tk.W, pady=5)
        fmod_exe_frame = ttk.Frame(paths_frame)
        fmod_exe_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.fmod_exe_entry = ttk.Entry(fmod_exe_frame, width=60)
        self.fmod_exe_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(fmod_exe_frame, text="Browse...", command=self.browse_fmod_exe).grid(row=0, column=1, padx=5)
        fmod_exe_frame.columnconfigure(0, weight=1)

        # Bind change event to save to settings
        self.fmod_exe_entry.bind('<FocusOut>', self._on_fmod_exe_changed)

        # VERSION INFO SECTION
        version_frame = ttk.LabelFrame(paths_frame, text="Version Info")
        version_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10,0))

        # Project version
        ttk.Label(version_frame, text="Project:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.project_version_label = ttk.Label(version_frame, text="(not loaded)", foreground=ThemeManager.get_color('gray'))
        self.project_version_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)

        # Executable version
        ttk.Label(version_frame, text="Executable:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.exe_version_label = ttk.Label(version_frame, text="(not detected)", foreground=ThemeManager.get_color('gray'))
        self.exe_version_label.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        # Status indicator
        self.version_status_label = ttk.Label(version_frame, text="")
        self.version_status_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        paths_frame.columnconfigure(1, weight=1)

        # ==================== SECTION 3: PATTERN SETUP ====================
        pattern_setup_frame = ttk.LabelFrame(main_frame, text="Pattern Setup", padding="10")
        pattern_setup_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Mode Selection
        mode_frame = ttk.Frame(pattern_setup_frame)
        mode_frame.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        ttk.Label(mode_frame, text="Import Mode:").pack(side=tk.LEFT, padx=(0, 10))

        self.import_mode_var = tk.StringVar(value="template")
        self.mode_template_rb = ttk.Radiobutton(mode_frame, text="Match Template",
                                                variable=self.import_mode_var, value="template",
                                                command=self._on_mode_changed)
        self.mode_template_rb.pack(side=tk.LEFT, padx=5)

        self.mode_pattern_rb = ttk.Radiobutton(mode_frame, text="Generate from Pattern",
                                               variable=self.import_mode_var, value="pattern",
                                               command=self._on_mode_changed)
        self.mode_pattern_rb.pack(side=tk.LEFT, padx=5)

        # Fuzzy matching note
        self.note_label = ttk.Label(
            pattern_setup_frame,
            text="NOTE: Matches files to existing events in the Template Folder using fuzzy logic.",
            foreground=ThemeManager.get_color('fg'),
            font=('TkDefaultFont', 9, 'italic'),
            wraplength=900
        )
        self.note_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        # Template Folder (OPTIONAL)
        self.template_label_title = ttk.Label(pattern_setup_frame, text="Template Folder:")
        self.template_label_title.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.template_frame = ttk.Frame(pattern_setup_frame)
        self.template_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.template_var = tk.StringVar(value="(No folder selected)")
        self.template_path_label = ttk.Label(self.template_frame, textvariable=self.template_var, relief="sunken")
        self.template_path_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.template_btn = ttk.Button(self.template_frame, text="Select...", command=self.select_template_folder)
        self.template_btn.grid(row=0, column=1, padx=5)

        # Auto-create toggle checkbox
        self.auto_create_var = tk.BooleanVar(value=True)
        self.auto_create_checkbox = ttk.Checkbutton(
            self.template_frame,
            text="Auto-create missing events",
            variable=self.auto_create_var
        )
        self.auto_create_checkbox.grid(row=0, column=2, padx=(10, 0))

        self.template_frame.columnconfigure(0, weight=1)

        # Prefix
        ttk.Label(pattern_setup_frame, text="Prefix:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.prefix_entry = ttk.Entry(pattern_setup_frame, width=60)
        self.prefix_entry.insert(0, "e.g. Sfx")
        self.prefix_entry.config(foreground=ThemeManager.get_color('gray'))
        self.prefix_entry.bind('<FocusIn>', lambda e: self._clear_placeholder(self.prefix_entry, 'e.g. Sfx'))
        self.prefix_entry.bind('<FocusOut>', lambda e: self._restore_placeholder(self.prefix_entry, 'e.g. Sfx'))
        self.prefix_entry.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # FeatureName
        ttk.Label(pattern_setup_frame, text="FeatureName:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.feature_entry = ttk.Entry(pattern_setup_frame, width=60)
        self.feature_entry.insert(0, "e.g. BlueEyesWhiteDragon")
        self.feature_entry.config(foreground=ThemeManager.get_color('gray'))
        self.feature_entry.bind('<FocusIn>', lambda e: self._clear_placeholder(self.feature_entry, 'e.g. BlueEyesWhiteDragon'))
        self.feature_entry.bind('<FocusOut>', lambda e: self._restore_placeholder(self.feature_entry, 'e.g. BlueEyesWhiteDragon'))
        self.feature_entry.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Delegate pattern pattern UI creation to a separate method
        self._create_pattern_input_widgets(pattern_setup_frame, start_row=5)

        pattern_setup_frame.columnconfigure(1, weight=1)

        # ==================== SECTION 4: IMPORT SETUP ====================
        import_setup_frame = ttk.LabelFrame(main_frame, text="Import Setup", padding="10")
        import_setup_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Event Folder
        ttk.Label(import_setup_frame, text="Event Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        dest_frame = ttk.Frame(import_setup_frame)
        dest_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.dest_var = tk.StringVar(value="(No folder selected)")
        self.dest_label = ttk.Label(dest_frame, textvariable=self.dest_var, relief="sunken", width=55)
        self.dest_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(dest_frame, text="Select...", command=self.select_destination_folder).grid(row=0, column=1, padx=5)
        dest_frame.columnconfigure(0, weight=1)

        # Asset Folder
        ttk.Label(import_setup_frame, text="Asset Folder:").grid(row=1, column=0, sticky=tk.W, pady=5)
        asset_frame = ttk.Frame(import_setup_frame)
        asset_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.asset_var = tk.StringVar(value="(No asset folder selected)")
        self.asset_label = ttk.Label(asset_frame, textvariable=self.asset_var, relief="sunken", width=55)
        self.asset_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(asset_frame, text="Select...", command=self.select_asset_folder).grid(row=0, column=1, padx=5)
        asset_frame.columnconfigure(0, weight=1)

        # Bank
        ttk.Label(import_setup_frame, text="Bank:").grid(row=2, column=0, sticky=tk.W, pady=5)
        bank_frame = ttk.Frame(import_setup_frame)
        bank_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.bank_var = tk.StringVar(value="(No bank selected)")
        self.bank_label = ttk.Label(bank_frame, textvariable=self.bank_var, relief="sunken", width=55)
        self.bank_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(bank_frame, text="Select...", command=self.select_bank).grid(row=0, column=1, padx=5)
        bank_frame.columnconfigure(0, weight=1)

        # Bus
        ttk.Label(import_setup_frame, text="Bus:").grid(row=3, column=0, sticky=tk.W, pady=5)
        bus_frame = ttk.Frame(import_setup_frame)
        bus_frame.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.bus_var = tk.StringVar(value="(No bus selected)")
        self.bus_label = ttk.Label(bus_frame, textvariable=self.bus_var, relief="sunken", width=55)
        self.bus_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(bus_frame, text="Select...", command=self.select_bus).grid(row=0, column=1, padx=5)
        bus_frame.columnconfigure(0, weight=1)

        # Bus warning label (inside bus_frame, row 1)
        self.bus_warning_label = ttk.Label(
            bus_frame, text="", foreground="#FF8C00",
            font=('TkDefaultFont', 8, 'italic')
        )
        self.bus_warning_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(2, 0))

        import_setup_frame.columnconfigure(1, weight=1)

        # ==================== ORPHANS CONTAINER (RIGHT SIDE) ====================
        # Create container for orphans that spans rows 0-4 in column 1
        orphans_container = ttk.Frame(main_frame, padding="0")
        orphans_container.grid(row=0, column=1, rowspan=5, sticky=(tk.N, tk.S, tk.W, tk.E), padx=(10, 0))

        # Configure orphans container to split vertically
        orphans_container.rowconfigure(0, weight=1)  # Orphan Events
        orphans_container.rowconfigure(1, weight=1)  # Orphan Assets
        orphans_container.columnconfigure(0, weight=1)

        # ==================== PREVIEW SECTION (FULL WIDTH) ====================
        # Preview section - Events matched to media
        preview_header_frame = ttk.Frame(main_frame)
        preview_header_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

        ttk.Label(preview_header_frame, text="Preview - Matched Events:").pack(side=tk.LEFT)
        ttk.Label(preview_header_frame, text="  |  Click ☑ column to toggle import  |  Confidence: ✓ High (≥95%)  ~ Good (≥85%)  ? Uncertain (≥70%)  |  + Auto-created (Double-click to rename)",
                 foreground=ThemeManager.get_color('gray')).pack(side=tk.LEFT, padx=(10, 0))

        preview_frame = ttk.Frame(main_frame)
        preview_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Create Treeview with checkbox column + bank/bus columns
        columns = ('checkbox', 'bank', 'bus')
        self.preview_tree = ttk.Treeview(preview_frame, columns=columns, show='tree headings', height=8)

        # Define headings
        self.preview_tree.heading('#0', text='Event Name')
        self.preview_tree.heading('checkbox', text='☑', anchor='center')
        self.preview_tree.heading('bank', text='Bank')
        self.preview_tree.heading('bus', text='Bus')

        # Define column widths
        self.preview_tree.column('#0', width=450)
        self.preview_tree.column('checkbox', width=40, anchor='center', stretch=False)
        self.preview_tree.column('bank', width=150)
        self.preview_tree.column('bus', width=150)

        self.preview_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.preview_tree['yscrollcommand'] = scrollbar.set

        # Drag & Drop support for preview tree (for media files only)
        self.preview_tree.bind('<ButtonPress-1>', self._on_preview_tree_press)
        self.preview_tree.bind('<B1-Motion>', self._on_preview_tree_drag)
        self.preview_tree.bind('<ButtonRelease-1>', self._on_preview_tree_release)

        # Delete key support for removing media files from preview tree
        self.preview_tree.bind('<Delete>', self._on_preview_tree_delete)

        # Checkbox toggle on click (first column only)
        self.preview_tree.bind('<Button-1>', self._on_preview_tree_checkbox_click, add='+')

        # Double-click to rename event
        self.preview_tree.bind('<Double-Button-1>', self._on_preview_tree_double_click)

        # F2 key to rename event (standard shortcut)
        self.preview_tree.bind('<F2>', self._on_preview_tree_f2)

        # Right-click context menu for preview tree
        self.preview_tree_menu = tk.Menu(self.root, tearoff=0)
        self.preview_tree.bind('<Button-3>', self._show_preview_tree_context_menu)

        # ==================== ORPHAN EVENTS (TOP OF RIGHT COLUMN) ====================
        orphan_events_section = ttk.LabelFrame(orphans_container, text="Orphan Events", padding="5")
        orphan_events_section.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E), pady=(0, 5))

        ttk.Label(orphan_events_section, text="(no media assigned)",
                  foreground=ThemeManager.get_color('gray'), font=('TkDefaultFont', 8, 'italic')).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 3)
        )

        # Listbox with scrollbar
        orphan_events_frame = ttk.Frame(orphan_events_section)
        orphan_events_frame.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))

        self.orphan_events_list = tk.Listbox(orphan_events_frame, height=10, selectmode=tk.EXTENDED)
        self.orphan_events_list.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))

        scrollbar_events = ttk.Scrollbar(orphan_events_frame, orient=tk.VERTICAL,
                                         command=self.orphan_events_list.yview)
        scrollbar_events.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.orphan_events_list.config(yscrollcommand=scrollbar_events.set)

        # Mouse wheel scrolling support
        self.orphan_events_list.bind('<MouseWheel>', self._on_mousewheel)
        self.orphan_events_list.bind('<Button-4>', self._on_mousewheel)  # Linux scroll up
        self.orphan_events_list.bind('<Button-5>', self._on_mousewheel)  # Linux scroll down

        orphan_events_frame.columnconfigure(0, weight=1)
        orphan_events_frame.rowconfigure(0, weight=1)
        orphan_events_section.columnconfigure(0, weight=1)
        orphan_events_section.rowconfigure(1, weight=1)

        # ==================== ORPHAN ASSETS (BOTTOM OF RIGHT COLUMN) ====================
        orphan_assets_section = ttk.LabelFrame(orphans_container, text="Orphan Assets", padding="5")
        orphan_assets_section.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.W, tk.E), pady=(5, 0))

        ttk.Label(orphan_assets_section, text="(no event assigned)",
                  foreground=ThemeManager.get_color('gray'), font=('TkDefaultFont', 8, 'italic')).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 3)
        )

        # Listbox with scrollbar
        orphan_assets_frame = ttk.Frame(orphan_assets_section)
        orphan_assets_frame.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))

        self.orphan_media_list = tk.Listbox(orphan_assets_frame, height=10, selectmode=tk.EXTENDED)
        self.orphan_media_list.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))

        scrollbar_assets = ttk.Scrollbar(orphan_assets_frame, orient=tk.VERTICAL,
                                        command=self.orphan_media_list.yview)
        scrollbar_assets.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.orphan_media_list.config(yscrollcommand=scrollbar_assets.set)

        # Context menu for orphan assets
        self.orphan_media_menu = tk.Menu(self.root, tearoff=0)
        self.orphan_media_list.bind('<Button-3>', self._show_orphan_media_context_menu)

        # Drag & Drop support for orphan assets
        # Use ButtonPress-1 to capture initial position, then detect drag in Motion
        self.orphan_media_list.bind('<ButtonPress-1>', self._on_listbox_press)
        self.orphan_media_list.bind('<B1-Motion>', self._on_drag_motion)
        self.orphan_media_list.bind('<ButtonRelease-1>', self._on_listbox_release)

        # Mouse wheel scrolling support
        self.orphan_media_list.bind('<MouseWheel>', self._on_mousewheel)
        self.orphan_media_list.bind('<Button-4>', self._on_mousewheel)  # Linux scroll up
        self.orphan_media_list.bind('<Button-5>', self._on_mousewheel)  # Linux scroll down

        # Override the default Listbox bindings that cause drag-select behavior
        # By changing bindtags order, our handlers run first and can prevent default behavior
        bindtags = list(self.orphan_media_list.bindtags())
        bindtags.remove('Listbox')  # Remove default Listbox class bindings
        self.orphan_media_list.bindtags(tuple(bindtags))

        # Add keyboard navigation bindings since we removed default Listbox bindings
        self.orphan_media_list.bind('<Up>', self._on_listbox_up)
        self.orphan_media_list.bind('<Down>', self._on_listbox_down)
        self.orphan_media_list.bind('<Control-a>', self._on_listbox_select_all)

        orphan_assets_frame.columnconfigure(0, weight=1)
        orphan_assets_frame.rowconfigure(0, weight=1)
        orphan_assets_section.columnconfigure(0, weight=1)
        orphan_assets_section.rowconfigure(1, weight=1)

        # Drop targets
        self.preview_tree.bind('<Enter>', lambda e: self._set_drop_target('preview'))
        self.orphan_events_list.bind('<Enter>', lambda e: self._set_drop_target('orphan'))

        # Store drag data
        self._drag_data = {
            'items': [],
            'indices': [],
            'start_x': 0,
            'start_y': 0,
            'dragging': False,
            'drop_target': None,
            'source_widget': None  # Track which widget initiated the drag
        }
        self._drag_threshold = 5  # pixels to move before starting drag
        self._drag_highlight_items = []  # Store items to highlight during drag

        # Create drag feedback label (hidden by default)
        self._drag_label = tk.Label(self.root, text="", bg="lightyellow", relief=tk.RIDGE,
                                     borderwidth=2, font=('Segoe UI', 9))
        self._drag_label.place_forget()  # Hide initially

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Analyze", command=self.analyze, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Import", command=self.import_assets, width=15).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Settings", command=self.open_settings, width=15).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.root.quit, width=15).grid(row=0, column=3, padx=5)

        # Version label (bottom-right)
        version_label = tk.Label(main_frame, text=f"v{VERSION}", fg=ThemeManager.get_color('gray'))
        version_label.grid(row=6, column=1, sticky=tk.E, pady=(5, 0))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Main frame columns: 60/40 split
        main_frame.columnconfigure(0, weight=2)  # Left column (~60-65%)
        main_frame.columnconfigure(1, weight=1)  # Right column (orphans, ~35-40%)

        # Main frame rows
        main_frame.rowconfigure(5, weight=1)  # Preview row (expands)

        # Preview frame internal
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)


    def update_version_display(self):
        """Update version info labels."""
        project_version = getattr(self, '_project_version', None)
        exe_version = getattr(self, '_exe_version', None)

        # Update project version label
        if project_version:
            ver_short = '.'.join(project_version.split('.')[:2])  # "2.03"
            self.project_version_label.config(text=ver_short, foreground=ThemeManager.get_color('fg'))
        else:
            self.project_version_label.config(text="(not loaded)", foreground=ThemeManager.get_color('gray'))

        # Update exe version label
        if exe_version:
            ver_short = '.'.join(exe_version.split('.')[:2])  # "2.02"
            self.exe_version_label.config(text=ver_short, foreground=ThemeManager.get_color('fg'))
        else:
            self.exe_version_label.config(text="(not detected)", foreground=ThemeManager.get_color('gray'))

        # Update status indicator
        if project_version and exe_version:
            if hasattr(self, 'project') and self.project:
                versions_match = self.project.compare_versions(project_version, exe_version)
                if versions_match:
                    self.version_status_label.config(text="✓ Versions match", foreground="green")
                else:
                    self.version_status_label.config(text="✗ Mismatch - import blocked", foreground="red")
        else:
            self.version_status_label.config(text="", foreground=ThemeManager.get_color('gray'))


