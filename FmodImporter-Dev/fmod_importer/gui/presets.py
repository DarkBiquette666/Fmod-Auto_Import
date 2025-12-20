"""
GUI Presets Mixin Module
Handles preset management for saving/loading complete FMOD Importer configurations.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime
from .preset_resolver import PresetResolver


class PresetsMixin:
    """
    Mixin class providing preset management functionality.

    Allows users to save and load complete configuration snapshots including:
    - Project paths (FMOD project, media directory, FMOD executable)
    - Pattern configuration (prefix, feature, patterns, separators)
    - FMOD references (folders, banks, buses) with smart UUID resolution

    These methods are mixed into FmodImporterGUI via multiple inheritance.
    All methods access shared state through 'self'.
    """

    # ==================== DIRECTORY MANAGEMENT ====================

    def _get_presets_directory(self) -> Path:
        """
        Get the presets directory path, creating it if it doesn't exist.

        Returns:
            Path to ~/.fmod_importer_presets/
        """
        presets_dir = Path.home() / ".fmod_importer_presets"
        presets_dir.mkdir(exist_ok=True)
        return presets_dir

    def _list_categories(self) -> List[str]:
        """
        Scan for category folders in the presets directory.

        Returns:
            List of category folder names (sorted alphabetically)
        """
        presets_dir = self._get_presets_directory()
        categories = []

        for item in presets_dir.iterdir():
            if item.is_dir():
                categories.append(item.name)

        return sorted(categories)

    def _create_category(self, name: str) -> Path:
        """
        Create a new category folder.

        Args:
            name: Category folder name

        Returns:
            Path to created category folder

        Raises:
            ValueError: If category name contains invalid characters
        """
        # Validate category name
        is_valid, error_msg = self._validate_category_name(name)
        if not is_valid:
            raise ValueError(error_msg)

        # Create category folder
        presets_dir = self._get_presets_directory()
        category_path = presets_dir / name
        category_path.mkdir(exist_ok=True)

        return category_path

    # ==================== PRESET OPERATIONS ====================

    def list_available_presets(self) -> List[Dict]:
        """
        Scan and return all available presets with folder structure.

        Returns:
            List of dicts with keys:
            - 'name': Display name (e.g., "Mechaflora/StrongRepair")
            - 'path': Full Path to JSON file
            - 'category': Category folder name

        Example:
            [
                {'name': 'Mechaflora/StrongRepair',
                 'path': Path('~/.fmod_importer_presets/Mechaflora/StrongRepair.json'),
                 'category': 'Mechaflora'},
                ...
            ]
        """
        presets = []
        presets_dir = self._get_presets_directory()

        # Scan all category folders
        for category_dir in presets_dir.iterdir():
            if not category_dir.is_dir():
                continue

            category_name = category_dir.name

            # Scan for JSON files in this category
            for preset_file in category_dir.glob('*.json'):
                preset_name = preset_file.stem  # Filename without .json
                display_name = f"{category_name}/{preset_name}"

                presets.append({
                    'name': display_name,
                    'path': preset_file,
                    'category': category_name
                })

        # Sort by display name
        presets.sort(key=lambda x: x['name'])

        return presets

    def save_preset(self, name: str, category: str, description: str = "") -> bool:
        """
        Save current configuration to preset file.

        Args:
            name: Preset name (without .json extension)
            category: Category folder name
            description: Optional description

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create category folder if needed
            category_path = self._create_category(category)

            # Serialize current config
            preset_data = self._serialize_current_config()

            # Add name and description
            preset_data['name'] = name
            preset_data['category'] = category
            preset_data['description'] = description

            # Save to file
            preset_file = category_path / f"{name}.json"
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, indent=2)

            return True

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save preset:\n{str(e)}")
            return False

    def load_preset(self, preset_path: Path) -> bool:
        """
        Load preset from file and apply to UI.

        Workflow:
        1. Load paths (project_path, media_path, fmod_exe_path)
        2. Validate project path exists
        3. Load FMOD project
        4. Apply pattern configuration
        5. Resolve and validate FMOD references (create if missing)

        Args:
            preset_path: Path to preset JSON file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load JSON
            with open(preset_path, 'r', encoding='utf-8') as f:
                preset_data = json.load(f)

            # Validate structure
            is_valid, error_msg = self._validate_preset_structure(preset_data)
            if not is_valid:
                messagebox.showerror("Invalid Preset", f"Preset file is invalid:\n{error_msg}")
                return False

            # Deserialize and apply to UI
            self._deserialize_preset(preset_data)

            return True

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load preset:\n{str(e)}")
            return False

    def delete_preset(self, preset_path: Path) -> bool:
        """
        Delete a preset file.

        Args:
            preset_path: Path to preset JSON file

        Returns:
            True if successful, False otherwise
        """
        try:
            if preset_path.exists():
                preset_path.unlink()
            return True
        except Exception as e:
            messagebox.showerror("Delete Error", f"Failed to delete preset:\n{str(e)}")
            return False

    def rename_category(self, old_name: str, new_name: str) -> bool:
        """
        Rename a category folder (moves all presets).

        Args:
            old_name: Current category name
            new_name: New category name

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate new name
            is_valid, error_msg = self._validate_category_name(new_name)
            if not is_valid:
                messagebox.showerror("Invalid Name", error_msg)
                return False

            presets_dir = self._get_presets_directory()
            old_path = presets_dir / old_name
            new_path = presets_dir / new_name

            if new_path.exists():
                messagebox.showerror("Error", f"Category '{new_name}' already exists")
                return False

            old_path.rename(new_path)
            return True

        except Exception as e:
            messagebox.showerror("Rename Error", f"Failed to rename category:\n{str(e)}")
            return False

    # ==================== SERIALIZATION ====================

    def _serialize_current_config(self) -> dict:
        """
        Convert current UI state to preset JSON structure.

        Captures complete configuration including:
        - All paths (project_path, media_path, fmod_exe_path)
        - Pattern configuration
        - FMOD references with BOTH UUIDs and paths for validation

        Returns:
            Dict ready for JSON serialization
        """
        # Get paths
        project_path = self.project_entry.get() if hasattr(self, 'project_entry') else ""
        media_path = self.media_entry.get() if hasattr(self, 'media_entry') else ""

        # Get fmod_exe_path from settings
        settings = self.load_settings() if hasattr(self, 'load_settings') else {}
        fmod_exe_path = settings.get('fmod_exe_path', '')

        # Get pattern configuration
        prefix = self._get_entry_value(self.prefix_entry, 'e.g. Sfx') if hasattr(self, 'prefix_entry') else ""
        feature_name = self._get_entry_value(self.feature_entry, 'e.g. BlueEyesDragon') if hasattr(self, 'feature_entry') else ""

        event_pattern = self.pattern_var.get() if hasattr(self, 'pattern_var') else ""
        event_separator = self.event_separator_entry.get() if hasattr(self, 'event_separator_entry') else ""

        asset_pattern = self._get_entry_value(self.asset_pattern_entry, '') if hasattr(self, 'asset_pattern_entry') else ""
        asset_separator = self.asset_separator_entry.get() if hasattr(self, 'asset_separator_entry') else ""

        auto_create = self.auto_create_var.get() if hasattr(self, 'auto_create_var') else True

        # Build FMOD references (with both UUIDs and paths)
        fmod_refs = {}

        # Create resolver for path building
        resolver = PresetResolver(self.project) if self.project else None

        # Template folder (optional)
        if hasattr(self, 'selected_template_id') and self.selected_template_id and resolver:
            template_path = resolver.get_folder_path(self.selected_template_id)
            fmod_refs['template_folder'] = {
                'id': self.selected_template_id,
                'path': template_path
            }
        else:
            fmod_refs['template_folder'] = {'id': '', 'path': ''}

        # Destination folder
        if hasattr(self, 'selected_dest_id') and self.selected_dest_id and resolver:
            dest_path = resolver.get_folder_path(self.selected_dest_id)
            fmod_refs['destination_folder'] = {
                'id': self.selected_dest_id,
                'path': dest_path
            }
        else:
            fmod_refs['destination_folder'] = {'id': '', 'path': ''}

        # Bank
        if hasattr(self, 'selected_bank_id') and self.selected_bank_id and resolver:
            bank_name, parent_id = resolver.get_bank_name_and_parent(self.selected_bank_id)
            parent_name = ""
            if parent_id and parent_id in self.project.banks:
                parent_name = self.project.banks[parent_id]['name']

            fmod_refs['bank'] = {
                'id': self.selected_bank_id,
                'name': bank_name,
                'parent_id': parent_id or '',
                'parent_name': parent_name
            }
        else:
            fmod_refs['bank'] = {'id': '', 'name': '', 'parent_id': '', 'parent_name': ''}

        # Bus
        if hasattr(self, 'selected_bus_id') and self.selected_bus_id and resolver:
            bus_path = resolver.get_bus_path(self.selected_bus_id)
            fmod_refs['bus'] = {
                'id': self.selected_bus_id,
                'path': bus_path
            }
        else:
            fmod_refs['bus'] = {'id': '', 'path': ''}

        # Asset folder
        if hasattr(self, 'selected_asset_id') and self.selected_asset_id and self.project:
            # Check both committed and pending asset folders
            asset_data = self.project.asset_folders.get(self.selected_asset_id)
            if not asset_data and hasattr(self.project, '_pending_asset_folders'):
                asset_data = self.project._pending_asset_folders.get(self.selected_asset_id)

            asset_path = asset_data.get('path', '') if asset_data else ''
            fmod_refs['asset_folder'] = {
                'id': self.selected_asset_id,
                'path': asset_path
            }
        else:
            fmod_refs['asset_folder'] = {'id': '', 'path': ''}

        # Build complete preset structure
        preset_data = {
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'paths': {
                'project_path': project_path,
                'media_path': media_path,
                'fmod_exe_path': fmod_exe_path
            },
            'pattern_config': {
                'prefix': prefix,
                'feature_name': feature_name,
                'event_pattern': event_pattern,
                'event_separator': event_separator,
                'asset_pattern': asset_pattern,
                'asset_separator': asset_separator,
                'auto_create_var': auto_create
            },
            'fmod_references': fmod_refs
        }

        return preset_data

    def _deserialize_preset(self, data: dict) -> None:
        """
        Apply preset data to UI.

        Steps:
        1. Load paths (project_path, media_path, fmod_exe_path)
        2. Load FMOD project if path exists
        3. Apply pattern configuration
        4. Resolve and validate FMOD references (create if missing)

        Args:
            data: Preset data dictionary from JSON
        """
        # Step 1: Load paths
        paths = data.get('paths', {})
        project_path = paths.get('project_path', '')
        media_path = paths.get('media_path', '')
        fmod_exe_path = paths.get('fmod_exe_path', '')

        # Apply project path to UI
        if hasattr(self, 'project_entry'):
            self.project_entry.delete(0, tk.END)
            self.project_entry.insert(0, project_path)

        # Apply media path to UI
        if hasattr(self, 'media_entry'):
            self.media_entry.delete(0, tk.END)
            self.media_entry.insert(0, media_path)

        # Save fmod_exe_path to settings (it's not in UI)
        if fmod_exe_path and hasattr(self, 'save_settings'):
            settings = self.load_settings() if hasattr(self, 'load_settings') else {}
            settings['fmod_exe_path'] = fmod_exe_path
            self.save_settings(settings)

        # Step 2: Validate and load FMOD project
        if project_path:
            if not Path(project_path).exists():
                messagebox.showwarning(
                    "Project Not Found",
                    f"FMOD project not found:\n{project_path}\n\n"
                    "Pattern configuration will be loaded, but FMOD references will be skipped."
                )
                # Continue loading pattern config only
            else:
                # Load the project
                if hasattr(self, 'load_project'):
                    try:
                        self.load_project()
                    except Exception as e:
                        messagebox.showerror(
                            "Project Load Error",
                            f"Failed to load FMOD project:\n{str(e)}"
                        )
                        return

        # Step 3: Apply pattern configuration
        pattern_config = data.get('pattern_config', {})

        # Apply prefix
        prefix = pattern_config.get('prefix', '')
        if prefix and hasattr(self, 'prefix_entry'):
            self.prefix_entry.delete(0, tk.END)
            self.prefix_entry.insert(0, prefix)
            self.prefix_entry.config(foreground='black')

        # Apply feature name
        feature_name = pattern_config.get('feature_name', '')
        if feature_name and hasattr(self, 'feature_entry'):
            self.feature_entry.delete(0, tk.END)
            self.feature_entry.insert(0, feature_name)
            self.feature_entry.config(foreground='black')

        # Apply event pattern
        event_pattern = pattern_config.get('event_pattern', '')
        if event_pattern and hasattr(self, 'pattern_var'):
            self.pattern_var.set(event_pattern)

        # Apply event separator
        event_separator = pattern_config.get('event_separator', '')
        if hasattr(self, 'event_separator_entry'):
            self.event_separator_entry.delete(0, tk.END)
            self.event_separator_entry.insert(0, event_separator)

        # Apply asset pattern
        asset_pattern = pattern_config.get('asset_pattern', '')
        if hasattr(self, 'asset_pattern_entry'):
            self.asset_pattern_entry.delete(0, tk.END)
            if asset_pattern:
                self.asset_pattern_entry.insert(0, asset_pattern)
                self.asset_pattern_entry.config(foreground='black')

        # Apply asset separator
        asset_separator = pattern_config.get('asset_separator', '')
        if hasattr(self, 'asset_separator_entry'):
            self.asset_separator_entry.delete(0, tk.END)
            self.asset_separator_entry.insert(0, asset_separator)

        # Apply auto_create toggle
        auto_create = pattern_config.get('auto_create_var', True)
        if hasattr(self, 'auto_create_var'):
            self.auto_create_var.set(auto_create)

        # Step 4: Resolve FMOD references (only if project loaded)
        if self.project:
            fmod_refs = data.get('fmod_references', {})
            resolver = PresetResolver(self.project)

            # Resolve template folder
            template_ref = fmod_refs.get('template_folder', {})
            if template_ref.get('id') or template_ref.get('path'):
                resolved_id = resolver.resolve_folder_reference(template_ref)
                if resolved_id and hasattr(self, 'template_var'):
                    # Check both committed and pending folders
                    folder_data = self.project.event_folders.get(resolved_id)
                    if not folder_data and hasattr(self.project, '_pending_event_folders'):
                        folder_data = self.project._pending_event_folders.get(resolved_id)

                    if folder_data:
                        folder_name = folder_data['name']
                        self.template_var.set(folder_name)
                        self.selected_template_id = resolved_id

            # Resolve destination folder
            dest_ref = fmod_refs.get('destination_folder', {})
            if dest_ref.get('id') or dest_ref.get('path'):
                resolved_id = resolver.resolve_folder_reference(dest_ref)
                if resolved_id and hasattr(self, 'dest_var'):
                    # Check both committed and pending folders
                    folder_data = self.project.event_folders.get(resolved_id)
                    if not folder_data and hasattr(self.project, '_pending_event_folders'):
                        folder_data = self.project._pending_event_folders.get(resolved_id)

                    if folder_data:
                        folder_name = folder_data['name']
                        self.dest_var.set(folder_name)
                        self.selected_dest_id = resolved_id

            # Resolve bank
            bank_ref = fmod_refs.get('bank', {})
            if bank_ref.get('id') or bank_ref.get('name'):
                resolved_id = resolver.resolve_bank_reference(bank_ref)
                if resolved_id and hasattr(self, 'bank_var'):
                    bank_name = self.project.banks[resolved_id]['name']
                    self.bank_var.set(bank_name)
                    self.selected_bank_id = resolved_id

            # Resolve bus
            bus_ref = fmod_refs.get('bus', {})
            if bus_ref.get('id') or bus_ref.get('path'):
                resolved_id = resolver.resolve_bus_reference(bus_ref)
                if resolved_id and hasattr(self, 'bus_var'):
                    bus_name = self.project.buses[resolved_id]['name']
                    self.bus_var.set(bus_name)
                    self.selected_bus_id = resolved_id

            # Resolve asset folder
            asset_ref = fmod_refs.get('asset_folder', {})
            if asset_ref.get('id') or asset_ref.get('path'):
                resolved_id = resolver.resolve_asset_folder_reference(asset_ref)
                if resolved_id and hasattr(self, 'asset_var'):
                    asset_path = self.project.asset_folders[resolved_id].get('path', '')
                    self.asset_var.set(asset_path)
                    self.selected_asset_id = resolved_id

        # Trigger pattern preview update if available
        if hasattr(self, '_update_pattern_preview'):
            self._update_pattern_preview()

    # ==================== UI DIALOGS ====================

    def open_preset_save_dialog(self) -> None:
        """
        Show save preset dialog with category selection.

        Allows user to:
        - Select or create category
        - Name the preset
        - Add optional description
        - Handles override warnings
        """
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Save Configuration Preset")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog)

        frame = ttk.Frame(dialog, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Category selection
        ttk.Label(frame, text="Category:").grid(row=0, column=0, sticky=tk.W, pady=5)

        category_frame = ttk.Frame(frame)
        category_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)

        categories = self._list_categories()
        category_var = tk.StringVar(value=categories[0] if categories else "")

        category_combo = ttk.Combobox(category_frame, textvariable=category_var, width=30)
        category_combo['values'] = categories + ["(New Category...)"]
        category_combo.grid(row=0, column=0, padx=(0, 5))

        # Preset name
        ttk.Label(frame, text="Preset Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(frame, width=35)

        # Auto-fill with prefix_feature if available
        prefix = self._get_entry_value(self.prefix_entry, 'e.g. Sfx') if hasattr(self, 'prefix_entry') else ""
        feature = self._get_entry_value(self.feature_entry, 'e.g. BlueEyesDragon') if hasattr(self, 'feature_entry') else ""
        if prefix and feature:
            name_entry.insert(0, f"{prefix}_{feature}")

        name_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)

        # Description
        ttk.Label(frame, text="Description:").grid(row=2, column=0, sticky=(tk.W, tk.N), pady=5)
        desc_text = tk.Text(frame, width=35, height=5)
        desc_text.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))

        def on_save():
            category = category_var.get()
            name = name_entry.get().strip()
            description = desc_text.get("1.0", tk.END).strip()

            if not name:
                messagebox.showerror("Error", "Preset name cannot be empty")
                return

            # Handle new category
            if category == "(New Category...)":
                new_category = simpledialog.askstring("New Category", "Enter category name:", parent=dialog)
                if not new_category:
                    return
                category = new_category.strip()

            if not category:
                messagebox.showerror("Error", "Category cannot be empty")
                return

            # Check if preset exists
            preset_file = self._get_presets_directory() / category / f"{name}.json"
            if preset_file.exists():
                if not messagebox.askyesno("Preset Exists",
                    f"A preset named '{name}' already exists in '{category}'.\n\nDo you want to overwrite it?"):
                    return

            # Save preset
            if self.save_preset(name, category, description):
                messagebox.showinfo("Success", f"Preset '{name}' saved successfully!")
                self._refresh_preset_combobox()
                dialog.destroy()

        ttk.Button(button_frame, text="Save", command=on_save, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, width=15).grid(row=0, column=1, padx=5)

    def load_selected_preset(self) -> None:
        """
        Load preset selected in combobox (auto-load on selection).

        Called when user selects a preset from the dropdown.
        """
        if not hasattr(self, 'preset_combobox') or not hasattr(self, 'preset_var'):
            return

        selection = self.preset_var.get()
        if not selection or selection.startswith("("):
            return

        # Find preset path
        presets = self.list_available_presets()
        for preset in presets:
            if preset['name'] == selection:
                self.load_preset(preset['path'])
                break

    def open_presets_manager(self) -> None:
        """
        Show preset management dialog with treeview.

        Provides:
        - Treeview of categories and presets
        - Details panel showing preset metadata
        - Load/Delete/Rename operations
        """
        # TODO: Implement full management dialog with treeview
        # For now, show a simple list dialog
        messagebox.showinfo("Presets Manager", "Full preset manager dialog coming soon!\n\nFor now, use the dropdown to load presets.")

    def _refresh_preset_combobox(self) -> None:
        """
        Refresh the preset combobox with available presets.

        Updates combobox values with current preset list.
        Maintains selection if possible.
        """
        if not hasattr(self, 'preset_combobox'):
            return

        presets = self.list_available_presets()

        if not presets:
            self.preset_combobox['values'] = ["(No presets - click Save to create one)"]
            self.preset_var.set("(No presets - click Save to create one)")
        else:
            preset_names = [p['name'] for p in presets]
            self.preset_combobox['values'] = preset_names

            # Keep current selection if still valid
            current = self.preset_var.get()
            if current not in preset_names and preset_names:
                self.preset_var.set(preset_names[0])

    # ==================== VALIDATION ====================

    def _validate_preset_structure(self, data: dict) -> Tuple[bool, str]:
        """
        Validate preset JSON structure.

        Checks for required keys and data types.

        Args:
            data: Preset data dictionary

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if structure is valid
            - error_message: Description of error if invalid, empty string if valid
        """
        # Check required top-level keys
        required_keys = ['version', 'paths', 'pattern_config', 'fmod_references']
        for key in required_keys:
            if key not in data:
                return False, f"Missing required key: '{key}'"

        # Check paths structure
        if not isinstance(data['paths'], dict):
            return False, "'paths' must be a dictionary"

        # Check pattern_config structure
        if not isinstance(data['pattern_config'], dict):
            return False, "'pattern_config' must be a dictionary"

        # Check fmod_references structure
        if not isinstance(data['fmod_references'], dict):
            return False, "'fmod_references' must be a dictionary"

        return True, ""

    def _validate_category_name(self, name: str) -> Tuple[bool, str]:
        """
        Validate category name for filesystem safety.

        Args:
            name: Proposed category name

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for empty name
        if not name or not name.strip():
            return False, "Category name cannot be empty"

        # Check for invalid filesystem characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            if char in name:
                return False, f"Category name cannot contain: {' '.join(invalid_chars)}"

        # Check for reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL',
                          'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                          'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        if name.upper() in reserved_names:
            return False, f"'{name}' is a reserved system name"

        return True, ""
