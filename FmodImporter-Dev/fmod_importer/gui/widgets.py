"""
GUI Widgets Mixin Module
Handles widget creation and placeholder management for FmodImporterGUI.
"""

import tkinter as tk
from tkinter import ttk, messagebox


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

        paths_frame.columnconfigure(1, weight=1)

        # ==================== SECTION 3: PATTERN SETUP ====================
        pattern_setup_frame = ttk.LabelFrame(main_frame, text="Pattern Setup", padding="10")
        pattern_setup_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Fuzzy matching note
        note_label = ttk.Label(
            pattern_setup_frame,
            text="NOTE: Template folder is optional. Without templates, events will be created from scratch with minimal structure. The system will fuzzy match when templates are provided.",
            foreground='#0066CC',
            font=('TkDefaultFont', 9, 'italic'),
            wraplength=900
        )
        note_label.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        # Template Folder (OPTIONAL)
        ttk.Label(pattern_setup_frame, text="Template Folder (Optional):").grid(row=1, column=0, sticky=tk.W, pady=5)
        template_frame = ttk.Frame(pattern_setup_frame)
        template_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.template_var = tk.StringVar(value="(No folder selected)")
        self.template_label = ttk.Label(template_frame, textvariable=self.template_var, relief="sunken")
        self.template_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(template_frame, text="Select...", command=self.select_template_folder).grid(row=0, column=1, padx=5)

        # Auto-create toggle checkbox
        self.auto_create_var = tk.BooleanVar(value=True)
        self.auto_create_checkbox = ttk.Checkbutton(
            template_frame,
            text="Auto-create events",
            variable=self.auto_create_var
        )
        self.auto_create_checkbox.grid(row=0, column=2, padx=(10, 0))

        template_frame.columnconfigure(0, weight=1)

        # Prefix
        ttk.Label(pattern_setup_frame, text="Prefix:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.prefix_entry = ttk.Entry(pattern_setup_frame, width=60)
        self.prefix_entry.insert(0, "e.g. Sfx")
        self.prefix_entry.config(foreground='gray')
        self.prefix_entry.bind('<FocusIn>', lambda e: self._clear_placeholder(self.prefix_entry, 'e.g. Sfx'))
        self.prefix_entry.bind('<FocusOut>', lambda e: self._restore_placeholder(self.prefix_entry, 'e.g. Sfx'))
        self.prefix_entry.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # FeatureName
        ttk.Label(pattern_setup_frame, text="FeatureName:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.feature_entry = ttk.Entry(pattern_setup_frame, width=60)
        self.feature_entry.insert(0, "e.g. BlueEyesDragon")
        self.feature_entry.config(foreground='gray')
        self.feature_entry.bind('<FocusIn>', lambda e: self._clear_placeholder(self.feature_entry, 'e.g. BlueEyesDragon'))
        self.feature_entry.bind('<FocusOut>', lambda e: self._restore_placeholder(self.feature_entry, 'e.g. BlueEyesDragon'))
        self.feature_entry.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Event Pattern - ALL ON ONE LINE
        ttk.Label(pattern_setup_frame, text="Event Pattern:").grid(row=4, column=0, sticky=tk.W, pady=5)
        pattern_frame = ttk.Frame(pattern_setup_frame)
        pattern_frame.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Pattern entry (fixed width)
        self.pattern_var = tk.StringVar(value="$prefix$feature$action")
        self.pattern_entry = ttk.Entry(pattern_frame, textvariable=self.pattern_var, width=30)
        self.pattern_entry.grid(row=0, column=0, padx=(0, 10))

        # Separator label + entry
        ttk.Label(pattern_frame, text="Separator:").grid(row=0, column=1, padx=(0, 5))
        self.event_separator_entry = ttk.Entry(pattern_frame, width=8)
        self.event_separator_entry.insert(0, "")  # Empty by default (CamelCase)
        self.event_separator_entry.grid(row=0, column=2, padx=(0, 10))

        # Help button
        self.pattern_help_btn = ttk.Button(pattern_frame, text="?", width=2, command=self.show_pattern_help)
        self.pattern_help_btn.grid(row=0, column=3, padx=(0, 10))

        # Preview (wraps text at 600px to prevent column resize)
        ttk.Label(pattern_frame, text="Preview:").grid(row=0, column=4, padx=(10, 5))
        self.pattern_preview_var = tk.StringVar(value="[prefix][feature][action]")
        self.pattern_preview_label = ttk.Label(pattern_frame, textvariable=self.pattern_preview_var,
                                                foreground='gray', font=('TkDefaultFont', 9, 'italic'),
                                                wraplength=600)
        self.pattern_preview_label.grid(row=0, column=5, sticky=tk.W)

        # Asset Pattern - ALL ON ONE LINE
        ttk.Label(pattern_setup_frame, text="Asset Pattern:").grid(row=5, column=0, sticky=tk.W, pady=5)
        asset_pattern_frame = ttk.Frame(pattern_setup_frame)
        asset_pattern_frame.grid(row=5, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Pattern entry with placeholder (fixed width)
        self.asset_pattern_entry = ttk.Entry(asset_pattern_frame, width=30)
        self.asset_pattern_entry.insert(0, "(Optional)")
        self.asset_pattern_entry.config(foreground='gray')
        self.asset_pattern_entry.bind('<FocusIn>', lambda e: self._clear_placeholder(self.asset_pattern_entry, "(Optional)"))
        self.asset_pattern_entry.bind('<FocusOut>', lambda e: self._restore_placeholder(self.asset_pattern_entry, "(Optional)"))
        self.asset_pattern_entry.grid(row=0, column=0, padx=(0, 10))

        # Separator label + entry
        ttk.Label(asset_pattern_frame, text="Separator:").grid(row=0, column=1, padx=(0, 5))
        self.asset_separator_entry = ttk.Entry(asset_pattern_frame, width=8)
        self.asset_separator_entry.insert(0, "")  # Empty by default
        self.asset_separator_entry.grid(row=0, column=2, padx=(0, 10))

        # Help button
        asset_pattern_help_btn = ttk.Button(asset_pattern_frame, text="?", width=2, command=self.show_asset_pattern_help)
        asset_pattern_help_btn.grid(row=0, column=3, padx=(0, 10))

        # Preview (wraps text at 600px to prevent column resize)
        ttk.Label(asset_pattern_frame, text="Preview:").grid(row=0, column=4, padx=(10, 5))
        self.asset_pattern_preview_var = tk.StringVar(value="[same as Event Pattern]")
        self.asset_pattern_preview_label = ttk.Label(asset_pattern_frame, textvariable=self.asset_pattern_preview_var,
                                                       foreground='gray', font=('TkDefaultFont', 9, 'italic'),
                                                       wraplength=600)
        self.asset_pattern_preview_label.grid(row=0, column=5, sticky=tk.W)

        # Note on second row
        asset_note_label = ttk.Label(asset_pattern_frame, text="Use this if your audio files have different pattern than events",
                                      foreground='gray', font=('TkDefaultFont', 8, 'italic'))
        asset_note_label.grid(row=1, column=0, columnspan=6, sticky=tk.W, pady=(2, 0))

        # Bind pattern/prefix/feature changes to update preview
        self.pattern_var.trace_add('write', self._update_pattern_preview)
        self.prefix_entry.bind('<KeyRelease>', lambda e: self._update_pattern_preview())
        self.feature_entry.bind('<KeyRelease>', lambda e: self._update_pattern_preview())
        self.event_separator_entry.bind('<KeyRelease>', lambda e: self._update_pattern_preview())

        # Bind asset pattern changes to update preview
        self.asset_pattern_entry.bind('<KeyRelease>', lambda e: self._update_asset_pattern_preview())
        self.asset_separator_entry.bind('<KeyRelease>', lambda e: self._update_asset_pattern_preview())

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
                 foreground="gray").pack(side=tk.LEFT, padx=(10, 0))

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
                  foreground="gray", font=('TkDefaultFont', 8, 'italic')).grid(
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
                  foreground="gray", font=('TkDefaultFont', 8, 'italic')).grid(
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
        version_label = tk.Label(main_frame, text=f"v{VERSION}", fg="#666666")
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

    def _clear_placeholder(self, entry: ttk.Entry, placeholder: str):
        """Clear placeholder text when entry gets focus"""
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(foreground='black')

    def _restore_placeholder(self, entry: ttk.Entry, placeholder: str):
        """Restore placeholder if entry is empty"""
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(foreground='gray')

    def _get_entry_value(self, entry: ttk.Entry, placeholder: str) -> str:
        """Get actual value from entry (excluding placeholder)"""
        value = entry.get()
        return '' if value == placeholder else value

    def _validate_separator(self, separator: str):
        """
        Validate separator character/string.

        Validation rules:
        - Empty string is OK (CamelCase mode)
        - Reject "$" (reserved for tags)
        - Reject newline, tab, carriage return
        - Reject control characters
        - Maximum 3 characters
        - Warning for regex special characters (but allow)

        Args:
            separator: Separator string to validate

        Returns:
            Tuple of (is_valid: bool, message: str)
            - is_valid: False if rejected, True otherwise
            - message: Error message if invalid, warning message if warning, empty if valid
        """
        # Empty is valid (CamelCase mode)
        if separator == '':
            return True, ''

        # Check for forbidden characters
        if '$' in separator:
            return False, 'Cannot contain $ (reserved for tags)'

        if '\n' in separator or '\r' in separator or '\t' in separator:
            return False, 'Cannot contain newline or tab'

        # Check for control characters
        if any(ord(c) < 32 for c in separator):
            return False, 'Cannot contain control characters'

        # Length check
        if len(separator) > 3:
            return False, 'Maximum 3 characters'

        # Warning for regex special characters (but allow them)
        regex_special = set('[]()+.?*|^\\')
        if any(c in regex_special for c in separator):
            return True, 'Special character - verify pattern works'

        # All checks passed
        return True, ''

    def _create_separator_field(self, parent_frame, row: int,
                               label_text: str, var_name: str,
                               default_value: str = '_'):
        """
        Create a separator input field with validation.

        Args:
            parent_frame: Parent frame to add widgets to
            row: Grid row number for this field
            label_text: Label text (e.g., "Separator:")
            var_name: Variable name for storing entry reference (e.g., 'event_separator_entry')
            default_value: Default separator value

        Returns:
            The created Entry widget
        """
        # Label (indented to show it's a sub-field)
        ttk.Label(parent_frame, text=label_text).grid(
            row=row, column=0, sticky=tk.W, pady=5, padx=(20, 5)
        )

        # Entry field
        entry = ttk.Entry(parent_frame, width=10)
        entry.insert(0, default_value)
        entry.grid(row=row, column=1, sticky=tk.W, pady=5)

        # Validation feedback label (hidden by default)
        validation_label = ttk.Label(
            parent_frame, text="", foreground="red",
            font=('TkDefaultFont', 8, 'italic')
        )
        validation_label.grid(row=row, column=2, sticky=tk.W, padx=(5, 0))

        # Real-time validation
        def validate_on_change(event=None):
            value = entry.get()
            valid, msg = self._validate_separator(value)

            if not valid:
                entry.config(foreground='red')
                validation_label.config(text=f"⚠ {msg}", foreground='red')
            elif msg:  # Warning
                entry.config(foreground='#FF8C00')  # Dark orange
                validation_label.config(text=f"⚠ {msg}", foreground='#FF8C00')
            else:
                entry.config(foreground='black')
                validation_label.config(text='')

        entry.bind('<KeyRelease>', validate_on_change)
        # Also trigger pattern preview update
        entry.bind('<KeyRelease>', lambda e: self._update_pattern_preview(), add='+')

        # Store reference
        setattr(self, var_name, entry)

        return entry

    def _update_pattern_preview(self, *args):
        """Update the pattern preview label based on current values"""
        # Import here to avoid circular imports
        from ..naming import NamingPattern

        # Guard: skip if widgets not yet initialized
        if not hasattr(self, 'pattern_preview_label') or not hasattr(self, 'pattern_preview_var'):
            return

        try:
            pattern_str = self.pattern_var.get()

            # Get separator value if event_separator_entry exists
            event_separator = None
            if hasattr(self, 'event_separator_entry'):
                event_separator = self.event_separator_entry.get()
                # Empty string is valid (CamelCase), so pass it as-is

            pattern = NamingPattern(pattern_str, separator=event_separator)

            # Get user values (excluding placeholders)
            prefix = self._get_entry_value(self.prefix_entry, 'e.g. Cat')
            feature = self._get_entry_value(self.feature_entry, 'e.g. FeatureName, Feature_Name, feature_name, ...')

            user_values = {}
            if prefix:
                user_values['prefix'] = prefix
            if feature:
                user_values['feature'] = feature.replace(' ', '_')

            preview = pattern.get_pattern_preview(user_values)
            self.pattern_preview_var.set(preview)

            # Validate pattern and update color
            valid, error = pattern.validate()
            if valid:
                self.pattern_preview_label.config(foreground='gray')
            else:
                self.pattern_preview_label.config(foreground='red')
        except Exception:
            pass  # Silently ignore errors during initialization

    def _update_asset_pattern_preview(self, *args):
        """
        Update the asset pattern preview label based on current values.
        Similar to _update_pattern_preview but for asset pattern.
        """
        # Import here to avoid circular imports
        from ..naming import NamingPattern

        # Guard: skip if widgets not yet initialized
        if not hasattr(self, 'asset_pattern_preview_label') or not hasattr(self, 'asset_pattern_preview_var'):
            return

        try:
            asset_pattern_str = self._get_entry_value(self.asset_pattern_entry, "(Optional)")

            # If empty or placeholder, show default message
            if not asset_pattern_str:
                self.asset_pattern_preview_var.set("[same as Event Pattern]")
                self.asset_pattern_preview_label.config(foreground='gray')
                return

            # Get separator value if asset_separator_entry exists
            asset_separator = None
            if hasattr(self, 'asset_separator_entry'):
                asset_separator = self.asset_separator_entry.get()
                # Empty string is valid (CamelCase), so pass it as-is

            pattern = NamingPattern(asset_pattern_str, separator=asset_separator)

            # Get user values (excluding placeholders)
            prefix = self._get_entry_value(self.prefix_entry, 'e.g. Sfx')
            feature = self._get_entry_value(self.feature_entry, 'e.g. BlueEyesDragon')

            user_values = {}
            if prefix:
                user_values['prefix'] = prefix
            if feature:
                user_values['feature'] = feature.replace(' ', '_')

            preview = pattern.get_pattern_preview(user_values)
            self.asset_pattern_preview_var.set(preview)

            # Validate pattern and update color
            valid, error = pattern.validate()
            if valid:
                self.asset_pattern_preview_label.config(foreground='gray')
            else:
                self.asset_pattern_preview_label.config(foreground='red')
        except Exception:
            pass  # Silently ignore errors during initialization

    def show_pattern_help(self):
        """Show help dialog explaining the event pattern system"""
        help_text = """EVENT PATTERN HELP

The pattern defines how your FMOD events will be named based on your audio files.

SUPPORTED TAGS:
  $prefix      - Project/character prefix (you provide this)
  $feature     - Feature name (you provide this)
  $action      - Action name like Attack, Spawn, Death (auto-extracted)
  $variation   - Variation letter A, B, C... (auto-extracted, optional)

EXAMPLES:

Pattern: $prefix_$feature_$action
  Files: Mechaflora_StrongRepair_Attack_01.wav
         Mechaflora_StrongRepair_Attack_02.wav
         Mechaflora_StrongRepair_Spawn.wav
  Events: Mechaflora_StrongRepair_Attack
          Mechaflora_StrongRepair_Spawn

Pattern: $prefix_$feature_$action_$variation
  Files: Mechaflora_StrongRepair_Attack_A_01.wav
         Mechaflora_StrongRepair_Attack_A_02.wav
         Mechaflora_StrongRepair_Attack_B_01.wav
  Events: Mechaflora_StrongRepair_Attack_A
          Mechaflora_StrongRepair_Attack_B

NOTES:
- Iterator numbers (_01, _02, etc.) are automatically stripped
- Multiple audio files with same event name are grouped together
- The separator is always underscore (_)
"""
        messagebox.showinfo("Event Pattern Help", help_text)

    def show_asset_pattern_help(self):
        """Show help dialog explaining the asset pattern system"""
        help_text = """ASSET PATTERN HELP

The Asset Pattern is OPTIONAL and used when your audio files use different
separators/formatting than how you want your FMOD events named.

WHEN TO USE THIS:
- Event names: MechafloraStrongRepairAlert (no underscores)
- File names: Mechaflora_Strong_Repair_Alert_01.wav (with underscores)

EXAMPLE:

Event Pattern: $prefix$feature$action
  → Events will be named: MechafloraStrongRepairAlert

Asset Pattern: $prefix_$feature_$action
  → Files will be parsed as: Mechaflora_Strong_Repair_Alert_01.wav

The tool will:
1. Parse the file using Asset Pattern → extract action="Alert"
2. Build event name using Event Pattern → MechafloraStrongRepairAlert
3. Match them intelligently (normalizes StrongRepair = Strong_Repair)

LEAVE EMPTY if your files already match your event pattern.
"""
        messagebox.showinfo("Asset Pattern Help", help_text)

    def _get_combined_name(self) -> str:
        """Get combined Prefix + Feature Name for pre-filling dialogs

        Returns empty string if either field is empty or contains placeholder text.
        Performs direct concatenation without separator.
        Examples:
            - "Mechaflora" + "Boss_Duo" = "MechafloraBoss_Duo"
            - "Mecha flora" + "Boss Duo" = "Mecha floraBoss Duo"
        """
        prefix = self._get_entry_value(self.prefix_entry, 'e.g. Cat')
        feature = self._get_entry_value(self.feature_entry, 'e.g. FeatureName, Feature_Name, feature_name, ...')

        if not prefix or not feature:
            return ''

        return f"{prefix}{feature}"
