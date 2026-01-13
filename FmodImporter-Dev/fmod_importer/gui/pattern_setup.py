"""
GUI Pattern Setup Mixin Module
Handles pattern configuration widgets and logic for FmodImporterGUI.
Extracted from widgets.py to maintain modularity.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .themes import ThemeManager

class PatternSetupMixin:
    """
    Mixin class providing pattern setup widgets and logic.

    These methods are mixed into FmodImporterGUI via multiple inheritance.
    All methods access shared state through 'self'.
    """

    def _create_pattern_input_widgets(self, parent_frame, start_row):
        """
        Create Event Pattern and Asset Pattern input widgets.

        Args:
            parent_frame: The parent frame to add widgets to
            start_row: The row number to start adding widgets at
        """
        # Store start_row for use in _on_mode_changed
        self._pattern_start_row = start_row
        self._pattern_parent_frame = parent_frame

        # Event Pattern - ALL ON ONE LINE
        self.event_pattern_label = ttk.Label(parent_frame, text="Event Pattern:")
        self.event_pattern_label.grid(row=start_row, column=0, sticky=tk.W, pady=5)
        self.event_pattern_frame = ttk.Frame(parent_frame)
        self.event_pattern_frame.grid(row=start_row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Pattern entry (fixed width)
        self.pattern_var = tk.StringVar(value="$prefix$feature$action")
        self.pattern_entry = ttk.Entry(self.event_pattern_frame, textvariable=self.pattern_var, width=30)
        self.pattern_entry.grid(row=0, column=0, padx=(0, 10))

        # Separator label + entry
        self.event_separator_label = ttk.Label(self.event_pattern_frame, text="Separator:")
        self.event_separator_label.grid(row=0, column=1, padx=(0, 5))
        self.event_separator_entry = ttk.Entry(self.event_pattern_frame, width=8)
        self.event_separator_entry.insert(0, "")  # Empty by default (CamelCase)
        self.event_separator_entry.grid(row=0, column=2, padx=(0, 10))

        # Help button
        self.pattern_help_btn = ttk.Button(self.event_pattern_frame, text="?", width=2, command=self.show_pattern_help)
        self.pattern_help_btn.grid(row=0, column=3, padx=(0, 10))

        # Preview (wraps text at 600px to prevent column resize)
        ttk.Label(self.event_pattern_frame, text="Preview:").grid(row=0, column=4, padx=(10, 5))
        self.pattern_preview_var = tk.StringVar(value="[prefix][feature][action]")
        self.pattern_preview_label = ttk.Label(self.event_pattern_frame, textvariable=self.pattern_preview_var,
                                                foreground=ThemeManager.get_color('gray'), font=('TkDefaultFont', 9, 'italic'),
                                                wraplength=600)
        self.pattern_preview_label.grid(row=0, column=5, sticky=tk.W)

        # Asset Pattern - ALL ON ONE LINE
        self.asset_pattern_label = ttk.Label(parent_frame, text="Asset Pattern:")
        self.asset_pattern_label.grid(row=start_row+1, column=0, sticky=tk.W, pady=5)
        self.asset_pattern_frame = ttk.Frame(parent_frame)
        self.asset_pattern_frame.grid(row=start_row+1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Pattern entry with placeholder (fixed width)
        self.asset_pattern_entry = ttk.Entry(self.asset_pattern_frame, width=30)
        self.asset_pattern_entry.insert(0, "(Optional)")
        self.asset_pattern_entry.config(foreground=ThemeManager.get_color('gray'))
        self.asset_pattern_entry.bind('<FocusIn>', lambda e: self._clear_placeholder(self.asset_pattern_entry, "(Optional)"))
        self.asset_pattern_entry.bind('<FocusOut>', lambda e: self._restore_placeholder(self.asset_pattern_entry, "(Optional)"))
        self.asset_pattern_entry.grid(row=0, column=0, padx=(0, 10))

        # Separator label + entry
        self.asset_separator_label = ttk.Label(self.asset_pattern_frame, text="Separator:")
        self.asset_separator_label.grid(row=0, column=1, padx=(0, 5))
        self.asset_separator_entry = ttk.Entry(self.asset_pattern_frame, width=8)
        self.asset_separator_entry.insert(0, "")  # Empty by default
        self.asset_separator_entry.grid(row=0, column=2, padx=(0, 10))

        # Help button
        self.asset_pattern_help_btn = ttk.Button(self.asset_pattern_frame, text="?", width=2, command=self.show_asset_pattern_help)
        self.asset_pattern_help_btn.grid(row=0, column=3, padx=(0, 10))

        # Preview (wraps text at 600px to prevent column resize)
        ttk.Label(self.asset_pattern_frame, text="Preview:").grid(row=0, column=4, padx=(10, 5))
        self.asset_pattern_preview_var = tk.StringVar(value="[same as Event Pattern]")
        self.asset_pattern_preview_label = ttk.Label(self.asset_pattern_frame, textvariable=self.asset_pattern_preview_var,
                                                       foreground=ThemeManager.get_color('gray'), font=('TkDefaultFont', 9, 'italic'),
                                                       wraplength=600)
        self.asset_pattern_preview_label.grid(row=0, column=5, sticky=tk.W)

        # Note on second row (will be updated based on mode)
        self.asset_note_label = ttk.Label(self.asset_pattern_frame, text="Use this if your audio files have different pattern than events",
                                      foreground=ThemeManager.get_color('gray'), font=('TkDefaultFont', 8, 'italic'))
        self.asset_note_label.grid(row=1, column=0, columnspan=6, sticky=tk.W, pady=(2, 0))

        # Bind pattern/prefix/feature changes to update preview
        self.pattern_var.trace_add('write', self._update_pattern_preview)
        self.prefix_entry.bind('<KeyRelease>', lambda e: self._update_pattern_preview())
        self.feature_entry.bind('<KeyRelease>', lambda e: self._update_pattern_preview())
        self.event_separator_entry.bind('<KeyRelease>', lambda e: self._update_pattern_preview())

        # Bind asset pattern changes to update preview
        self.asset_pattern_entry.bind('<KeyRelease>', lambda e: self._update_asset_pattern_preview())
        self.asset_separator_entry.bind('<KeyRelease>', lambda e: self._update_asset_pattern_preview())

    def _on_mode_changed(self):
        """Handle import mode change (Template vs Pattern)"""
        if not hasattr(self, 'import_mode_var'):
            return

        mode = self.import_mode_var.get()
        
        if mode == "template":
            # Enable and SHOW template widgets
            if hasattr(self, 'template_label_title'): 
                self.template_label_title.grid()
                self.template_label_title.config(state='normal')
            if hasattr(self, 'template_frame'): 
                self.template_frame.grid()
            if hasattr(self, 'template_path_label'): self.template_path_label.config(state='normal')
            if hasattr(self, 'template_btn'): self.template_btn.config(state='normal')
            if hasattr(self, 'auto_create_checkbox'): self.auto_create_checkbox.config(state='normal')
            
            # Update note
            if hasattr(self, 'note_label'):
                self.note_label.config(
                    text="NOTE: Matches files to existing events in the Template Folder using fuzzy logic."
                )
            
            # Update Asset Pattern placeholder to Optional (Template Mode)
            if hasattr(self, 'asset_pattern_entry'):
                current_val = self.asset_pattern_entry.get()
                # Clear if it was the pattern-mode default
                if current_val == "e.g. $prefix_$feature_$action":
                    self.asset_pattern_entry.delete(0, tk.END)
                
                # Set Optional placeholder
                if not self.asset_pattern_entry.get():
                    self.asset_pattern_entry.insert(0, "(Optional)")
                    self.asset_pattern_entry.config(foreground=ThemeManager.get_color('gray'))
                
                # Rebind focus events for Optional placeholder
                self.asset_pattern_entry.bind('<FocusIn>', lambda e: self._clear_placeholder(self.asset_pattern_entry, "(Optional)"))
                self.asset_pattern_entry.bind('<FocusOut>', lambda e: self._restore_placeholder(self.asset_pattern_entry, "(Optional)"))

            # Reset Event Pattern if it was empty/optional (Template Mode default is explicit)
            if hasattr(self, 'pattern_var'):
                 if not self.pattern_var.get() or self.pattern_var.get() == "(Optional)":
                     self.pattern_var.set("$prefix$feature$action")

            # SHOW separator fields (Template Mode)
            if hasattr(self, 'event_separator_label'):
                self.event_separator_label.grid()
            if hasattr(self, 'event_separator_entry'):
                self.event_separator_entry.grid()
            if hasattr(self, 'asset_separator_label'):
                self.asset_separator_label.grid()
            if hasattr(self, 'asset_separator_entry'):
                self.asset_separator_entry.grid()

            # REORDER: Event Pattern first, Asset Pattern second (Template Mode)
            if hasattr(self, '_pattern_start_row'):
                start_row = self._pattern_start_row
                # Event Pattern at row start_row
                if hasattr(self, 'event_pattern_label'):
                    self.event_pattern_label.grid_configure(row=start_row)
                    self.event_pattern_label.config(text="Event Pattern:")
                if hasattr(self, 'event_pattern_frame'):
                    self.event_pattern_frame.grid_configure(row=start_row)
                # Asset Pattern at row start_row+1
                if hasattr(self, 'asset_pattern_label'):
                    self.asset_pattern_label.grid_configure(row=start_row+1)
                    self.asset_pattern_label.config(text="Asset Pattern:")
                if hasattr(self, 'asset_pattern_frame'):
                    self.asset_pattern_frame.grid_configure(row=start_row+1)

            # Update asset note for Template mode
            if hasattr(self, 'asset_note_label'):
                self.asset_note_label.config(text="Use this if your audio files have different pattern than events")

        else:
            # Disable and HIDE template widgets
            if hasattr(self, 'template_label_title'): 
                self.template_label_title.grid_remove() # Hide the label
            if hasattr(self, 'template_frame'): 
                self.template_frame.grid_remove() # Hide the frame with entry/buttons
            
            # Update note
            if hasattr(self, 'note_label'):
                self.note_label.config(
                    text="NOTE: Uses Asset Name Pattern to parse files and Event Name Pattern to name new events."
                )

            # Update Asset Pattern placeholder to Mandatory (Pattern Mode)
            if hasattr(self, 'asset_pattern_entry'):
                current_val = self.asset_pattern_entry.get()
                # Clear if it was the template-mode optional placeholder
                if current_val == "(Optional)":
                    self.asset_pattern_entry.delete(0, tk.END)
                
                # Set default pattern if empty
                if not self.asset_pattern_entry.get():
                    self.asset_pattern_entry.insert(0, "$prefix_$feature_$action")
                    self.asset_pattern_entry.config(foreground=ThemeManager.get_color('input_fg')) # Actual value, not placeholder
                
                # Rebind focus events (no placeholder behavior needed for default value)
                self.asset_pattern_entry.bind('<FocusIn>', lambda e: None)
                self.asset_pattern_entry.bind('<FocusOut>', lambda e: None)

            # Reset Event Pattern to Optional (Pattern Mode)
            if hasattr(self, 'pattern_var'):
                 # In Pattern mode, Event Pattern is optional (defaults to Asset Pattern)
                 if self.pattern_var.get() == "$prefix$feature$action":
                     self.pattern_var.set("")

            # HIDE separator fields (Pattern Mode)
            if hasattr(self, 'event_separator_label'):
                self.event_separator_label.grid_remove()
            if hasattr(self, 'event_separator_entry'):
                self.event_separator_entry.grid_remove()
            if hasattr(self, 'asset_separator_label'):
                self.asset_separator_label.grid_remove()
            if hasattr(self, 'asset_separator_entry'):
                self.asset_separator_entry.grid_remove()

            # REORDER: Asset Pattern first, Event Pattern second (Pattern Mode - INVERTED)
            if hasattr(self, '_pattern_start_row'):
                start_row = self._pattern_start_row
                # Asset Pattern at row start_row (SOURCE - how files are named)
                if hasattr(self, 'asset_pattern_label'):
                    self.asset_pattern_label.grid_configure(row=start_row)
                    self.asset_pattern_label.config(text="Asset Name Pattern:")
                if hasattr(self, 'asset_pattern_frame'):
                    self.asset_pattern_frame.grid_configure(row=start_row)
                # Event Pattern at row start_row+1 (DESTINATION - how events will be named)
                if hasattr(self, 'event_pattern_label'):
                    self.event_pattern_label.grid_configure(row=start_row+1)
                    self.event_pattern_label.config(text="Event Name Pattern:")
                if hasattr(self, 'event_pattern_frame'):
                    self.event_pattern_frame.grid_configure(row=start_row+1)

            # Update asset note for Pattern mode
            if hasattr(self, 'asset_note_label'):
                self.asset_note_label.config(text="Define how your audio files are named (this is the SOURCE pattern)")

        # Force update of previews
        self._update_asset_pattern_preview()
        self._update_pattern_preview()

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
                entry.config(foreground=ThemeManager.get_color('input_fg'))
                validation_label.config(text='')

        entry.bind('<KeyRelease>', validate_on_change)
        # Also trigger pattern preview update
        entry.bind('<KeyRelease>', lambda e: self._update_pattern_preview(), add='+')

        # Store reference
        setattr(self, var_name, entry)

        return entry

    def _update_pattern_preview(self, *args):
        """Update the EVENT pattern preview label based on current values"""
        # Import here to avoid circular imports
        from ..naming import NamingPattern

        # Guard: skip if widgets not yet initialized
        if not hasattr(self, 'pattern_preview_label') or not hasattr(self, 'pattern_preview_var'):
            return

        try:
            pattern_str = self.pattern_var.get()
            import_mode = self.import_mode_var.get() if hasattr(self, 'import_mode_var') else "template"

            # Check for empty pattern logic based on mode
            if not pattern_str:
                if import_mode == "pattern":
                    self.pattern_preview_var.set("[same as Asset Name Pattern]")
                    self.pattern_preview_label.config(foreground=ThemeManager.get_color('gray'))
                    return
                else:
                    # In template mode, empty pattern is usually invalid or just empty
                    self.pattern_preview_var.set("")
                    return

            # Get separator ONLY in template mode
            event_separator = None
            if import_mode == "template" and hasattr(self, 'event_separator_entry'):
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
                self.pattern_preview_label.config(foreground=ThemeManager.get_color('gray'))
            else:
                self.pattern_preview_label.config(foreground='red')
        except Exception:
            pass  # Silently ignore errors during initialization

    def _update_asset_pattern_preview(self, *args):
        """
        Update the ASSET pattern preview label based on current values.
        """
        # Import here to avoid circular imports
        from ..naming import NamingPattern

        # Guard: skip if widgets not yet initialized
        if not hasattr(self, 'asset_pattern_preview_label') or not hasattr(self, 'asset_pattern_preview_var'):
            return

        try:
            import_mode = self.import_mode_var.get() if hasattr(self, 'import_mode_var') else "template"
            
            # Determine placeholder based on mode for fetching value
            placeholder = "(Optional)" if import_mode == "template" else "e.g. $prefix_$feature_$action"
            
            asset_pattern_str = self._get_entry_value(self.asset_pattern_entry, placeholder)

            # Logic branching based on mode
            if import_mode == "template":
                # Template Mode: Asset Pattern is Optional (falls back to Event Pattern)
                if not asset_pattern_str:
                    self.asset_pattern_preview_var.set("[same as Event Name Pattern]")
                    self.asset_pattern_preview_label.config(foreground=ThemeManager.get_color('gray'))
                    return
            else:
                # Pattern Mode: Asset Pattern is Mandatory (Source of Truth)
                if not asset_pattern_str:
                    self.asset_pattern_preview_var.set("[Required in this mode]")
                    self.asset_pattern_preview_label.config(foreground='red')
                    return

            # Get separator ONLY in template mode
            asset_separator = None
            if import_mode == "template" and hasattr(self, 'asset_separator_entry'):
                asset_separator = self.asset_separator_entry.get()
                # Empty string is valid (CamelCase), so pass it as-is

            pattern = NamingPattern(asset_pattern_str, separator=asset_separator)

            # Get user values (excluding placeholders)
            prefix = self._get_entry_value(self.prefix_entry, 'e.g. Sfx')
            feature = self._get_entry_value(self.feature_entry, 'e.g. BlueEyesWhiteDragon')

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
                self.asset_pattern_preview_label.config(foreground=ThemeManager.get_color('gray'))
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

    def refresh_pattern_theme(self):
        """Refreshes colors for Pattern Setup widgets"""
        
        # Labels
        if hasattr(self, 'note_label'):
            self.note_label.config(foreground=ThemeManager.get_color('fg'))
            
        if hasattr(self, 'asset_note_label'):
            self.asset_note_label.config(foreground=ThemeManager.get_color('gray'))
            
        # Entry Placeholders
        # 1. Prefix
        if hasattr(self, 'prefix_entry'):
            if self.prefix_entry.get() == "e.g. Sfx":
                self.prefix_entry.config(foreground=ThemeManager.get_color('gray'))
            else:
                self.prefix_entry.config(foreground=ThemeManager.get_color('input_fg'))
                
        # 2. Feature
        if hasattr(self, 'feature_entry'):
            if self.feature_entry.get() == "e.g. BlueEyesWhiteDragon":
                 self.feature_entry.config(foreground=ThemeManager.get_color('gray'))
            else:
                 self.feature_entry.config(foreground=ThemeManager.get_color('input_fg'))
         
        # 3. Asset Pattern
        if hasattr(self, 'asset_pattern_entry'):
             val = self.asset_pattern_entry.get()
             if val == "(Optional)" or val == "e.g. $prefix_$feature_$action":
                 self.asset_pattern_entry.config(foreground=ThemeManager.get_color('gray'))
             else:
                 self.asset_pattern_entry.config(foreground=ThemeManager.get_color('input_fg'))

        # Previews
        # Calling update methods will re-validate and set correct colors (red or gray)
        self._update_pattern_preview()
        self._update_asset_pattern_preview()
