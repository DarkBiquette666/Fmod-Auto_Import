"""
GUI Settings Mixin Module
Handles settings management for FmodImporterGUI.
"""

import os
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class SettingsMixin:
    """
    Mixin class providing settings functionality.

    These methods are mixed into FmodImporterGUI via multiple inheritance.
    All methods access shared state through 'self'.
    """

    def _load_default_settings(self):
        """Load default settings and populate UI fields at startup"""
        settings = self.load_settings()

        if settings.get('default_project_path'):
            self.project_entry.delete(0, tk.END)
            self.project_entry.insert(0, settings['default_project_path'])
            # Auto-load project if path exists
            if os.path.exists(settings['default_project_path']):
                self.load_project()

        if settings.get('default_media_path'):
            self.media_entry.delete(0, tk.END)
            self.media_entry.insert(0, settings['default_media_path'])

        # Load FMOD Studio executable path
        if settings.get('fmod_exe_path'):
            self.fmod_exe_entry.delete(0, tk.END)
            self.fmod_exe_entry.insert(0, settings['fmod_exe_path'])

        # Apply default template folder if project is loaded
        if settings.get('default_template_folder_id') and self.project:
            template_id = settings['default_template_folder_id']
            if template_id in self.project.event_folders:
                self.template_var.set(self.project.event_folders[template_id]['name'])
                self.selected_template_id = template_id

        # Apply default bank if project is loaded
        if settings.get('default_bank_id') and self.project:
            bank_id = settings['default_bank_id']
            if bank_id in self.project.banks:
                self.bank_var.set(self.project.banks[bank_id]['name'])
                self.selected_bank_id = bank_id

        # Apply default destination folder if project is loaded
        if settings.get('default_destination_folder_id') and self.project:
            dest_id = settings['default_destination_folder_id']
            if dest_id in self.project.event_folders:
                self.dest_var.set(self.project.event_folders[dest_id]['name'])
                self.selected_dest_id = dest_id

        # Apply default bus if project is loaded
        if settings.get('default_bus_id') and self.project:
            bus_id = settings['default_bus_id']
            if bus_id in self.project.buses:
                self.bus_var.set(self.project.buses[bus_id]['name'])
                self.selected_bus_id = bus_id

        # Apply default event pattern
        if settings.get('default_event_pattern') and hasattr(self, 'pattern_var'):
            self.pattern_var.set(settings['default_event_pattern'])

        # Apply default asset pattern
        if settings.get('default_asset_pattern') and hasattr(self, 'asset_pattern_entry'):
            self.asset_pattern_entry.delete(0, tk.END)
            self.asset_pattern_entry.insert(0, settings['default_asset_pattern'])
            self.asset_pattern_entry.config(foreground='black')

        # Apply default event separator
        if settings.get('default_event_separator') and hasattr(self, 'event_separator_entry'):
            self.event_separator_entry.delete(0, tk.END)
            self.event_separator_entry.insert(0, settings['default_event_separator'])

        # Apply default asset separator
        if settings.get('default_asset_separator') and hasattr(self, 'asset_separator_entry'):
            self.asset_separator_entry.delete(0, tk.END)
            self.asset_separator_entry.insert(0, settings['default_asset_separator'])

    def load_settings(self):
        """Load settings from JSON file"""
        settings_file = Path.home() / ".fmod_importer_settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings
            except Exception as e:
                print(f"Failed to load settings: {e}")
        return {
            'default_project_path': '',
            'default_media_path': '',
            'default_template_folder_id': '',
            'default_bank_id': '',
            'default_destination_folder_id': '',
            'default_bus_id': '',
            'fmod_exe_path': '',
            'default_event_pattern': '$prefix$feature$action',
            'default_asset_pattern': '',
            'default_event_separator': '',
            'default_asset_separator': ''
        }

    def save_settings(self, settings: dict):
        """Save settings to JSON file"""
        settings_file = Path.home() / ".fmod_importer_settings.json"
        try:
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{str(e)}")
            return False

    def open_settings(self):
        """Open settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("600x550")
        settings_window.transient(self.root)
        settings_window.grab_set()
        self._center_dialog(settings_window)

        frame = ttk.Frame(settings_window, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Load current settings
        current_settings = self.load_settings()

        # ==================== SECTION 1: PATHS ====================
        paths_frame = ttk.LabelFrame(frame, text="Paths", padding="10")
        paths_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Default project path
        ttk.Label(paths_frame, text="Default FMOD Project:").grid(row=0, column=0, sticky=tk.W, pady=5)
        project_entry = ttk.Entry(paths_frame, width=50)
        project_entry.insert(0, current_settings.get('default_project_path', ''))
        project_entry.grid(row=0, column=1, pady=5, padx=5)

        def browse_default_project():
            filename = filedialog.askopenfilename(
                title="Select Default FMOD Project",
                filetypes=[("FMOD Project", "*.fspro"), ("All Files", "*.*")]
            )
            if filename:
                project_entry.delete(0, tk.END)
                project_entry.insert(0, filename)

        ttk.Button(paths_frame, text="Browse...", command=browse_default_project).grid(row=0, column=2, padx=5)

        # FMOD executable path
        ttk.Label(paths_frame, text="FMOD Studio Executable:").grid(row=1, column=0, sticky=tk.W, pady=5)
        fmod_entry = ttk.Entry(paths_frame, width=50)
        fmod_entry.insert(0, current_settings.get('fmod_exe_path', ''))
        fmod_entry.grid(row=1, column=1, pady=5, padx=5)

        def browse_fmod_exe():
            filename = filedialog.askopenfilename(
                title="Select FMOD Studio Executable",
                filetypes=[("FMOD Studio", "FMOD Studio*.exe"), ("All Files", "*.*")]
            )
            if filename:
                fmod_entry.delete(0, tk.END)
                fmod_entry.insert(0, filename)

        ttk.Button(paths_frame, text="Browse...", command=browse_fmod_exe).grid(row=1, column=2, padx=5)

        # Default media path
        ttk.Label(paths_frame, text="Default Media Directory:").grid(row=2, column=0, sticky=tk.W, pady=5)
        media_entry = ttk.Entry(paths_frame, width=50)
        media_entry.insert(0, current_settings.get('default_media_path', ''))
        media_entry.grid(row=2, column=1, pady=5, padx=5)

        def browse_default_media():
            dirname = filedialog.askdirectory(title="Select Default Media Directory")
            if dirname:
                media_entry.delete(0, tk.END)
                media_entry.insert(0, dirname)

        ttk.Button(paths_frame, text="Browse...", command=browse_default_media).grid(row=2, column=2, padx=5)

        paths_frame.columnconfigure(1, weight=1)

        # ==================== SECTION 2: PATTERN SETUP ====================
        pattern_setup_frame = ttk.LabelFrame(frame, text="Pattern Setup", padding="10")
        pattern_setup_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Default template folder
        ttk.Label(pattern_setup_frame, text="Default Template Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)

        template_folder_var = tk.StringVar()
        template_folder_id_var = tk.StringVar()

        # Try to get folder name from ID if project is loaded
        saved_template_id = current_settings.get('default_template_folder_id', '')
        if saved_template_id and self.project and saved_template_id in self.project.event_folders:
            template_folder_var.set(self.project.event_folders[saved_template_id]['name'])
            template_folder_id_var.set(saved_template_id)
        else:
            template_folder_var.set("(No folder selected)")

        template_label = ttk.Label(pattern_setup_frame, textvariable=template_folder_var, relief="sunken", width=45)
        template_label.grid(row=0, column=1, pady=5, padx=5)

        def browse_template_folder():
            if not self.project:
                messagebox.showwarning("Warning", "Please load a FMOD project first")
                return

            selected = self._show_folder_tree_dialog("Select Default Template Folder")
            if selected:
                folder_name, folder_id = selected
                template_folder_var.set(folder_name)
                template_folder_id_var.set(folder_id)

        ttk.Button(pattern_setup_frame, text="Select...", command=browse_template_folder).grid(row=0, column=2, padx=5)

        # Event Pattern + Separator on same line
        ttk.Label(pattern_setup_frame, text="Event Pattern:").grid(row=1, column=0, sticky=tk.W, pady=5)
        event_pattern_frame = ttk.Frame(pattern_setup_frame)
        event_pattern_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        event_pattern_entry = ttk.Entry(event_pattern_frame, width=30)
        event_pattern_entry.insert(0, current_settings.get('default_event_pattern', '$prefix$feature$action'))
        event_pattern_entry.grid(row=0, column=0, padx=(0, 10))

        ttk.Label(event_pattern_frame, text="Separator:").grid(row=0, column=1, padx=(0, 5))
        event_sep_entry = ttk.Entry(event_pattern_frame, width=8)
        event_sep_entry.insert(0, current_settings.get('default_event_separator', ''))
        event_sep_entry.grid(row=0, column=2, padx=(0, 10))

        # Asset Pattern + Separator on same line
        ttk.Label(pattern_setup_frame, text="Asset Pattern:").grid(row=2, column=0, sticky=tk.W, pady=5)
        asset_pattern_frame = ttk.Frame(pattern_setup_frame)
        asset_pattern_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        asset_pattern_entry = ttk.Entry(asset_pattern_frame, width=30)
        asset_pattern_value = current_settings.get('default_asset_pattern', '')
        if asset_pattern_value:
            asset_pattern_entry.insert(0, asset_pattern_value)
            asset_pattern_entry.config(foreground='black')
        else:
            asset_pattern_entry.insert(0, "(Optional)")
            asset_pattern_entry.config(foreground='gray')

        # Placeholder handlers
        def clear_asset_pattern_placeholder(event):
            if asset_pattern_entry.get() == "(Optional)" and asset_pattern_entry.cget('foreground') == 'gray':
                asset_pattern_entry.delete(0, tk.END)
                asset_pattern_entry.config(foreground='black')

        def restore_asset_pattern_placeholder(event):
            if not asset_pattern_entry.get():
                asset_pattern_entry.insert(0, "(Optional)")
                asset_pattern_entry.config(foreground='gray')

        asset_pattern_entry.bind('<FocusIn>', clear_asset_pattern_placeholder)
        asset_pattern_entry.bind('<FocusOut>', restore_asset_pattern_placeholder)
        asset_pattern_entry.grid(row=0, column=0, padx=(0, 10))

        ttk.Label(asset_pattern_frame, text="Separator:").grid(row=0, column=1, padx=(0, 5))
        asset_sep_entry = ttk.Entry(asset_pattern_frame, width=8)
        asset_sep_entry.insert(0, current_settings.get('default_asset_separator', ''))
        asset_sep_entry.grid(row=0, column=2, padx=(0, 10))

        pattern_setup_frame.columnconfigure(1, weight=1)

        # ==================== SECTION 3: IMPORT SETUP ====================
        import_setup_frame = ttk.LabelFrame(frame, text="Import Setup", padding="10")
        import_setup_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # Default bank
        ttk.Label(import_setup_frame, text="Default Bank:").grid(row=0, column=0, sticky=tk.W, pady=5)

        bank_var = tk.StringVar()
        bank_id_var = tk.StringVar()

        saved_bank_id = current_settings.get('default_bank_id', '')
        if saved_bank_id and self.project and saved_bank_id in self.project.banks:
            bank_var.set(self.project.banks[saved_bank_id]['name'])
            bank_id_var.set(saved_bank_id)
        else:
            bank_var.set("(No bank selected)")

        bank_label = ttk.Label(import_setup_frame, textvariable=bank_var, relief="sunken", width=45)
        bank_label.grid(row=0, column=1, pady=5, padx=5)

        def browse_bank():
            if not self.project:
                messagebox.showwarning("Warning", "Please load a FMOD project first")
                return

            selected = self._show_hierarchical_dialog(
                "Select Default Bank",
                self.project.banks,
                create_fn=lambda name, parent_id: self.project.create_bank(name),
                delete_fn=lambda item_id: self.project.delete_bank(item_id)
            )
            if selected:
                selected_name, selected_id = selected
                bank_var.set(selected_name)
                bank_id_var.set(selected_id)

        ttk.Button(import_setup_frame, text="Select...", command=browse_bank).grid(row=0, column=2, padx=5)

        # Default destination folder
        ttk.Label(import_setup_frame, text="Default Destination Folder:").grid(row=1, column=0, sticky=tk.W, pady=5)

        dest_folder_var = tk.StringVar()
        dest_folder_id_var = tk.StringVar()

        saved_dest_id = current_settings.get('default_destination_folder_id', '')
        if saved_dest_id and self.project and saved_dest_id in self.project.event_folders:
            dest_folder_var.set(self.project.event_folders[saved_dest_id]['name'])
            dest_folder_id_var.set(saved_dest_id)
        else:
            dest_folder_var.set("(No folder selected)")

        dest_label = ttk.Label(import_setup_frame, textvariable=dest_folder_var, relief="sunken", width=45)
        dest_label.grid(row=1, column=1, pady=5, padx=5)

        def browse_dest_folder():
            if not self.project:
                messagebox.showwarning("Warning", "Please load a FMOD project first")
                return

            selected = self._show_folder_tree_dialog("Select Default Destination Folder")
            if selected:
                folder_name, folder_id = selected
                dest_folder_var.set(folder_name)
                dest_folder_id_var.set(folder_id)

        ttk.Button(import_setup_frame, text="Select...", command=browse_dest_folder).grid(row=1, column=2, padx=5)

        # Default bus
        ttk.Label(import_setup_frame, text="Default Bus:").grid(row=2, column=0, sticky=tk.W, pady=5)

        bus_var = tk.StringVar()
        bus_id_var = tk.StringVar()

        saved_bus_id = current_settings.get('default_bus_id', '')
        if saved_bus_id and self.project and saved_bus_id in self.project.buses:
            bus_var.set(self.project.buses[saved_bus_id]['name'])
            bus_id_var.set(saved_bus_id)
        else:
            bus_var.set("(No bus selected)")

        bus_label = ttk.Label(import_setup_frame, textvariable=bus_var, relief="sunken", width=45)
        bus_label.grid(row=2, column=1, pady=5, padx=5)

        def browse_bus():
            if not self.project:
                messagebox.showwarning("Warning", "Please load a FMOD project first")
                return

            selected = self._show_hierarchical_dialog(
                "Select Default Bus",
                self.project.buses,
                create_fn=lambda name, parent_id: self.project.create_bus(name),
                delete_fn=lambda item_id: self.project.delete_bus(item_id)
            )
            if selected:
                selected_name, selected_id = selected
                bus_var.set(selected_name)
                bus_id_var.set(selected_id)

        ttk.Button(import_setup_frame, text="Select...", command=browse_bus).grid(row=2, column=2, padx=5)

        import_setup_frame.columnconfigure(1, weight=1)

        # Save button
        def save_and_close():
            new_settings = {
                'default_project_path': project_entry.get(),
                'default_media_path': media_entry.get(),
                'default_template_folder_id': template_folder_id_var.get(),
                'default_bank_id': bank_id_var.get(),
                'default_destination_folder_id': dest_folder_id_var.get(),
                'default_bus_id': bus_id_var.get(),
                'fmod_exe_path': fmod_entry.get(),
                'default_event_pattern': event_pattern_entry.get(),
                'default_asset_pattern': asset_pattern_entry.get() if asset_pattern_entry.get() != "(Optional)" else '',
                'default_event_separator': event_sep_entry.get(),
                'default_asset_separator': asset_sep_entry.get()
            }
            if self.save_settings(new_settings):
                # Apply settings to current UI
                if new_settings['default_project_path']:
                    self.project_entry.delete(0, tk.END)
                    self.project_entry.insert(0, new_settings['default_project_path'])
                if new_settings['default_media_path']:
                    self.media_entry.delete(0, tk.END)
                    self.media_entry.insert(0, new_settings['default_media_path'])

                # Apply all defaults if project is loaded
                if self.project:
                    # Template folder
                    if new_settings['default_template_folder_id']:
                        template_id = new_settings['default_template_folder_id']
                        if template_id in self.project.event_folders:
                            self.template_var.set(self.project.event_folders[template_id]['name'])
                            self.selected_template_id = template_id

                    # Bank
                    if new_settings['default_bank_id']:
                        selected_bank_id = new_settings['default_bank_id']
                        if selected_bank_id in self.project.banks:
                            self.bank_var.set(self.project.banks[selected_bank_id]['name'])
                            self.selected_bank_id = selected_bank_id

                    # Destination folder
                    if new_settings['default_destination_folder_id']:
                        selected_dest_id = new_settings['default_destination_folder_id']
                        if selected_dest_id in self.project.event_folders:
                            self.dest_var.set(self.project.event_folders[selected_dest_id]['name'])
                            self.selected_dest_id = selected_dest_id

                    # Bus
                    if new_settings['default_bus_id']:
                        selected_bus_id = new_settings['default_bus_id']
                        if selected_bus_id in self.project.buses:
                            self.bus_var.set(self.project.buses[selected_bus_id]['name'])
                            self.selected_bus_id = selected_bus_id

                # Apply pattern settings to current UI
                if new_settings.get('default_event_pattern') and hasattr(self, 'pattern_var'):
                    self.pattern_var.set(new_settings['default_event_pattern'])

                if new_settings.get('default_asset_pattern') and hasattr(self, 'asset_pattern_entry'):
                    self.asset_pattern_entry.delete(0, tk.END)
                    self.asset_pattern_entry.insert(0, new_settings['default_asset_pattern'])
                    self.asset_pattern_entry.config(foreground='black')
                elif hasattr(self, 'asset_pattern_entry'):
                    # Restore placeholder if empty
                    self.asset_pattern_entry.delete(0, tk.END)
                    self.asset_pattern_entry.insert(0, "(Optional)")
                    self.asset_pattern_entry.config(foreground='gray')

                # Apply separator settings to current UI
                if new_settings.get('default_event_separator') and hasattr(self, 'event_separator_entry'):
                    self.event_separator_entry.delete(0, tk.END)
                    self.event_separator_entry.insert(0, new_settings['default_event_separator'])

                if new_settings.get('default_asset_separator') and hasattr(self, 'asset_separator_entry'):
                    self.asset_separator_entry.delete(0, tk.END)
                    self.asset_separator_entry.insert(0, new_settings['default_asset_separator'])

                messagebox.showinfo("Success", "Settings saved successfully!")
                settings_window.destroy()

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        ttk.Button(button_frame, text="Save", command=save_and_close, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=settings_window.destroy, width=15).grid(row=0, column=1, padx=5)

        settings_window.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
