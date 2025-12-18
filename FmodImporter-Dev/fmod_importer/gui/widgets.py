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

        # Project selection
        ttk.Label(main_frame, text="FMOD Project (.fspro):").grid(row=0, column=0, sticky=tk.W, pady=5)

        project_frame = ttk.Frame(main_frame)
        project_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.project_entry = ttk.Entry(project_frame, width=40)
        self.project_entry.grid(row=0, column=0, padx=(0, 5))
        ttk.Button(project_frame, text="Browse...", command=self.browse_project).grid(row=0, column=1, padx=5)
        ttk.Button(project_frame, text="Load", command=self.load_project).grid(row=0, column=2, padx=5)
        ttk.Button(project_frame, text="Reload Scripts", command=self.reload_fmod_scripts).grid(row=0, column=3, padx=5)

        # Media files path
        ttk.Label(main_frame, text="Media Files Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        media_frame = ttk.Frame(main_frame)
        media_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.media_entry = ttk.Entry(media_frame, width=60)
        self.media_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(media_frame, text="Browse...", command=self.browse_media).grid(row=0, column=1, padx=5)
        media_frame.columnconfigure(0, weight=1)

        # Template folder
        ttk.Label(main_frame, text="Template Folder:").grid(row=4, column=0, sticky=tk.W, pady=5)
        template_frame = ttk.Frame(main_frame)
        template_frame.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.template_var = tk.StringVar(value="(No folder selected)")
        self.template_label = ttk.Label(template_frame, textvariable=self.template_var, relief="sunken", width=55)
        self.template_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(template_frame, text="Select...", command=self.select_template_folder).grid(row=0, column=1, padx=5)
        template_frame.columnconfigure(0, weight=1)

        # Prefix
        ttk.Label(main_frame, text="Prefix:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.prefix_entry = ttk.Entry(main_frame, width=60)
        self.prefix_entry.insert(0, "")
        # Add placeholder effect
        self.prefix_entry.insert(0, "e.g. Cat")
        self.prefix_entry.config(foreground='gray')
        self.prefix_entry.bind('<FocusIn>', lambda e: self._clear_placeholder(self.prefix_entry, 'e.g. Cat'))
        self.prefix_entry.bind('<FocusOut>', lambda e: self._restore_placeholder(self.prefix_entry, 'e.g. Cat'))
        self.prefix_entry.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Feature name
        ttk.Label(main_frame, text="Feature Name:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.feature_entry = ttk.Entry(main_frame, width=60)
        self.feature_entry.insert(0, "e.g. FeatureName, Feature_Name, feature_name, ...")
        self.feature_entry.config(foreground='gray')
        self.feature_entry.bind('<FocusIn>', lambda e: self._clear_placeholder(self.feature_entry, 'e.g. FeatureName, Feature_Name, feature_name, ...'))
        self.feature_entry.bind('<FocusOut>', lambda e: self._restore_placeholder(self.feature_entry, 'e.g. FeatureName, Feature_Name, feature_name, ...'))
        self.feature_entry.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Event Pattern (defines template/event naming structure)
        ttk.Label(main_frame, text="Event Pattern:").grid(row=5, column=0, sticky=tk.W, pady=5)
        pattern_frame = ttk.Frame(main_frame)
        pattern_frame.grid(row=5, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.pattern_var = tk.StringVar(value="$prefix_$feature_$action")
        self.pattern_entry = ttk.Entry(pattern_frame, textvariable=self.pattern_var, width=40)
        self.pattern_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        # Help button
        self.pattern_help_btn = ttk.Button(pattern_frame, text="?", width=2, command=self.show_pattern_help)
        self.pattern_help_btn.grid(row=0, column=1, padx=2)

        # Preview label
        ttk.Label(pattern_frame, text="Preview:").grid(row=0, column=2, padx=(10, 5))
        self.pattern_preview_var = tk.StringVar(value="[prefix]_[feature]_[action]")
        self.pattern_preview_label = ttk.Label(pattern_frame, textvariable=self.pattern_preview_var,
                                                foreground='gray', font=('TkDefaultFont', 9, 'italic'))
        self.pattern_preview_label.grid(row=0, column=3, sticky=tk.W)

        pattern_frame.columnconfigure(0, weight=1)

        # Bind pattern/prefix/feature changes to update preview
        self.pattern_var.trace_add('write', self._update_pattern_preview)
        self.prefix_entry.bind('<KeyRelease>', lambda e: self._update_pattern_preview())
        self.feature_entry.bind('<KeyRelease>', lambda e: self._update_pattern_preview())

        # Asset Pattern (optional - for parsing files with different format than events)
        ttk.Label(main_frame, text="Asset Pattern:").grid(row=6, column=0, sticky=tk.W, pady=5)
        asset_pattern_frame = ttk.Frame(main_frame)
        asset_pattern_frame.grid(row=6, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.asset_pattern_entry = ttk.Entry(asset_pattern_frame, width=40)
        self.asset_pattern_entry.insert(0, "(Optional - leave empty to use Event Pattern)")
        self.asset_pattern_entry.config(foreground='gray')
        self.asset_pattern_entry.bind('<FocusIn>', lambda e: self._clear_placeholder(self.asset_pattern_entry, "(Optional - leave empty to use Event Pattern)"))
        self.asset_pattern_entry.bind('<FocusOut>', lambda e: self._restore_placeholder(self.asset_pattern_entry, "(Optional - leave empty to use Event Pattern)"))
        self.asset_pattern_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        # Help button
        asset_pattern_help_btn = ttk.Button(asset_pattern_frame, text="?", width=2, command=self.show_asset_pattern_help)
        asset_pattern_help_btn.grid(row=0, column=1, padx=2)

        # Note label
        asset_note_label = ttk.Label(asset_pattern_frame, text="Use this if your audio files have different separators than events",
                                      foreground='gray', font=('TkDefaultFont', 8, 'italic'))
        asset_note_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(2, 0))

        asset_pattern_frame.columnconfigure(0, weight=1)

        # Destination folder (moved before Bank)
        ttk.Label(main_frame, text="Event Folder:").grid(row=7, column=0, sticky=tk.W, pady=5)
        dest_frame = ttk.Frame(main_frame)
        dest_frame.grid(row=7, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.dest_var = tk.StringVar(value="(No folder selected)")
        self.dest_label = ttk.Label(dest_frame, textvariable=self.dest_var, relief="sunken", width=55)
        self.dest_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(dest_frame, text="Select...", command=self.select_destination_folder).grid(row=0, column=1, padx=5)
        dest_frame.columnconfigure(0, weight=1)

        # Bank selection
        ttk.Label(main_frame, text="Bank:").grid(row=8, column=0, sticky=tk.W, pady=5)
        bank_frame = ttk.Frame(main_frame)
        bank_frame.grid(row=8, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.bank_var = tk.StringVar(value="(No bank selected)")
        self.bank_label = ttk.Label(bank_frame, textvariable=self.bank_var, relief="sunken", width=55)
        self.bank_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(bank_frame, text="Select...", command=self.select_bank).grid(row=0, column=1, padx=5)
        bank_frame.columnconfigure(0, weight=1)

        # Bus assignment
        ttk.Label(main_frame, text="Bus:").grid(row=9, column=0, sticky=tk.W, pady=5)
        bus_frame = ttk.Frame(main_frame)
        bus_frame.grid(row=9, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.bus_var = tk.StringVar(value="(No bus selected)")
        self.bus_label = ttk.Label(bus_frame, textvariable=self.bus_var, relief="sunken", width=55)
        self.bus_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(bus_frame, text="Select...", command=self.select_bus).grid(row=0, column=1, padx=5)
        bus_frame.columnconfigure(0, weight=1)

        # Audio Asset Folder
        ttk.Label(main_frame, text="Audio Asset Folder:").grid(row=10, column=0, sticky=tk.W, pady=5)
        asset_frame = ttk.Frame(main_frame)
        asset_frame.grid(row=10, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.asset_var = tk.StringVar(value="(No asset folder selected)")
        self.asset_label = ttk.Label(asset_frame, textvariable=self.asset_var, relief="sunken", width=55)
        self.asset_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(asset_frame, text="Select...", command=self.select_asset_folder).grid(row=0, column=1, padx=5)
        asset_frame.columnconfigure(0, weight=1)

        # Preview section - Events matched to media
        preview_header_frame = ttk.Frame(main_frame)
        preview_header_frame.grid(row=11, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))

        ttk.Label(preview_header_frame, text="Preview - Matched Events:").pack(side=tk.LEFT)
        ttk.Label(preview_header_frame, text="  |  Confidence: ✓ High (≥95%)  ~ Good (≥85%)  ? Uncertain (≥70%)  |  + Auto-created (Double-click to rename)",
                 foreground="gray").pack(side=tk.LEFT, padx=(10, 0))

        preview_frame = ttk.Frame(main_frame)
        preview_frame.grid(row=12, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Create Treeview with 2 columns (removed 'Events → Assets' column)
        columns = ('bank', 'bus')
        self.preview_tree = ttk.Treeview(preview_frame, columns=columns, show='tree headings', height=8)

        # Define headings
        self.preview_tree.heading('#0', text='Event Name')
        self.preview_tree.heading('bank', text='Bank')
        self.preview_tree.heading('bus', text='Bus')

        # Define column widths
        self.preview_tree.column('#0', width=500)
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

        # Double-click to rename event
        self.preview_tree.bind('<Double-Button-1>', self._on_preview_tree_double_click)

        # F2 key to rename event (standard shortcut)
        self.preview_tree.bind('<F2>', self._on_preview_tree_f2)

        # Right-click context menu for preview tree
        self.preview_tree_menu = tk.Menu(self.root, tearoff=0)
        self.preview_tree.bind('<Button-3>', self._show_preview_tree_context_menu)

        # Orphans section
        ttk.Label(main_frame, text="Orphans:").grid(row=13, column=0, sticky=tk.NW, pady=10)

        orphans_frame = ttk.Frame(main_frame)
        orphans_frame.grid(row=14, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Left side - Orphan Events
        orphan_events_frame = ttk.Frame(orphans_frame)
        orphan_events_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))

        ttk.Label(orphan_events_frame, text="Orphan Events (no media assigned)").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.orphan_events_list = tk.Listbox(orphan_events_frame, height=8, selectmode=tk.EXTENDED)
        self.orphan_events_list.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        events_scrollbar = ttk.Scrollbar(orphan_events_frame, orient=tk.VERTICAL, command=self.orphan_events_list.yview)
        events_scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S))
        self.orphan_events_list['yscrollcommand'] = events_scrollbar.set

        # Mouse wheel scrolling support
        self.orphan_events_list.bind('<MouseWheel>', self._on_mousewheel)
        self.orphan_events_list.bind('<Button-4>', self._on_mousewheel)  # Linux scroll up
        self.orphan_events_list.bind('<Button-5>', self._on_mousewheel)  # Linux scroll down

        orphan_events_frame.columnconfigure(0, weight=1)
        orphan_events_frame.rowconfigure(2, weight=1)  # Row 2 contains the Listbox

        # Right side - Orphan Media Files
        orphan_media_frame = ttk.Frame(orphans_frame)
        orphan_media_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))

        ttk.Label(orphan_media_frame, text="Orphan Media Files (Drag to assign, or Right-click)").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        self.orphan_media_list = tk.Listbox(orphan_media_frame, height=8, selectmode=tk.EXTENDED)
        self.orphan_media_list.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        media_scrollbar = ttk.Scrollbar(orphan_media_frame, orient=tk.VERTICAL, command=self.orphan_media_list.yview)
        media_scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S))
        self.orphan_media_list['yscrollcommand'] = media_scrollbar.set

        # Context menu for orphan media files
        self.orphan_media_menu = tk.Menu(self.root, tearoff=0)
        self.orphan_media_list.bind('<Button-3>', self._show_orphan_media_context_menu)

        # Drag & Drop support for orphan media
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

        orphan_media_frame.columnconfigure(0, weight=1)
        orphan_media_frame.rowconfigure(2, weight=1)  # Row 2 contains the Listbox

        # Configure orphans_frame columns to split equally
        orphans_frame.columnconfigure(0, weight=1)
        orphans_frame.columnconfigure(1, weight=1)
        orphans_frame.rowconfigure(0, weight=1)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=15, column=0, columnspan=3, pady=10)

        ttk.Button(button_frame, text="Analyze", command=self.analyze, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Import", command=self.import_assets, width=15).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Settings", command=self.open_settings, width=15).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.root.quit, width=15).grid(row=0, column=3, padx=5)

        # Version label (bottom-right)
        version_label = tk.Label(main_frame, text=f"v{VERSION}", fg="#666666")
        version_label.grid(row=16, column=2, sticky=tk.E, pady=(5, 0))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(12, weight=1)  # Preview row
        main_frame.rowconfigure(14, weight=1)  # Orphans row
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

    def _update_pattern_preview(self, *args):
        """Update the pattern preview label based on current values"""
        # Import here to avoid circular imports
        from ..naming import NamingPattern

        # Guard: skip if widgets not yet initialized
        if not hasattr(self, 'pattern_preview_label') or not hasattr(self, 'pattern_preview_var'):
            return

        try:
            pattern_str = self.pattern_var.get()
            pattern = NamingPattern(pattern_str)

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
