"""
GUI Main Module
Contains the main FmodImporterGUI class that combines all mixins.
"""

import os
import platform
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional, Dict, List

from ..project import FMODProject
from .utils import UtilsMixin
from .widgets import WidgetsMixin
from .dialogs import DialogsMixin
from .asset_dialogs import AssetDialogsMixin
from .drag_drop import DragDropMixin
from .analysis import AnalysisMixin
from .import_workflow import ImportMixin
from .settings import SettingsMixin
from .presets import PresetsMixin


class FmodImporterGUI(
    UtilsMixin,
    WidgetsMixin,
    DialogsMixin,
    AssetDialogsMixin,
    DragDropMixin,
    AnalysisMixin,
    ImportMixin,
    SettingsMixin,
    PresetsMixin
):
    """
    Main GUI application for FMOD Importer Tool.

    This class uses the Mixin pattern to combine functionality from multiple
    specialized modules, keeping each module focused and under 1000 lines.

    Mixins provide:
    - UtilsMixin: Utility methods and context menus
    - WidgetsMixin: Widget creation and placeholder management
    - DialogsMixin: CRUD dialogs for FMOD project items
    - AssetDialogsMixin: Asset folder tree dialog
    - DragDropMixin: Drag and drop functionality
    - AnalysisMixin: Audio file analysis workflow
    - ImportMixin: Asset import workflow
    - SettingsMixin: Settings management
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("FMOD Importer Tool - Asset Importer")

        # Set window icon
        self._set_window_icon()

        # Set window size to accommodate all sections
        self.root.geometry("1440x1150")
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        self.project: Optional[FMODProject] = None
        self.config = {
            'project_path': '',
            'media_path': '',
            'template_folder_id': '',
            'prefix': 'Mechaflora',
            'feature_name': 'Weak_Ranged',
            'bank_name': 'MechafloraWeakRanged',
            'destination_folder_id': ''
        }

        # Selection tracking
        self.selected_template_id = None
        self.selected_dest_id = None
        self.selected_bank_id = None
        self.selected_bus_id = None
        self.selected_asset_id = None

        # Media lookup for matching
        self.media_lookup: Dict[str, List[str]] = {}

        # Checkbox state tracking for preview tree
        self.preview_checked_items = set()  # IDs of checked items

        # Create widgets (from WidgetsMixin)
        self._create_widgets()

        # Load default settings (from SettingsMixin)
        self._load_default_settings()

        # Populate preset combobox (from PresetsMixin)
        self._refresh_preset_combobox()

        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def browse_project(self):
        """Browse for FMOD project file"""
        filename = filedialog.askopenfilename(
            title="Select FMOD Project",
            filetypes=[("FMOD Project", "*.fspro"), ("All Files", "*.*")]
        )

        if filename:
            self.project_entry.delete(0, tk.END)
            self.project_entry.insert(0, filename)
            self.load_project(filename)

    def reload_fmod_scripts(self):
        """Force FMOD Studio to reload scripts"""
        if not self.project:
            messagebox.showwarning("Warning", "Please load a FMOD project first")
            return

        try:
            project_path = str(self.project.project_path)

            # Create a temporary empty JavaScript file to trigger script reload
            temp_script = tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8')
            temp_script.write('// Trigger script reload\nstudio.system.message("Scripts reloaded");')
            temp_script.close()

            # Execute the script via FMOD Studio console API
            if platform.system() == "Windows":
                # Use fmod_console.exe to execute the script
                console_path = self._find_fmod_console()
                if console_path:
                    subprocess.run([
                        console_path,
                        project_path,
                        "--execute-script", temp_script.name
                    ], check=True)
                    messagebox.showinfo("Success", "FMOD scripts reloaded successfully")
                else:
                    messagebox.showwarning("Warning", "FMOD Console not found. Please reload scripts manually in FMOD Studio (File > Reload Scripts)")
            else:
                messagebox.showinfo("Info", "Please reload scripts manually in FMOD Studio (File > Reload Scripts)")

            # Cleanup temp file
            try:
                os.unlink(temp_script.name)
            except:
                pass

        except Exception as e:
            messagebox.showerror("Error", f"Failed to reload scripts:\n{str(e)}\n\nPlease reload manually in FMOD Studio (File > Reload Scripts)")

    def _find_fmod_console(self) -> Optional[str]:
        """Find FMOD Console executable"""
        # Common installation paths for FMOD Studio
        possible_paths = [
            r"C:\Program Files (x86)\FMOD SoundSystem\FMOD Studio 2.02.25\fmod_console.exe",
            r"C:\Program Files\FMOD SoundSystem\FMOD Studio 2.02.25\fmod_console.exe",
            r"C:\Program Files (x86)\FMOD SoundSystem\FMOD Studio\fmod_console.exe",
            r"C:\Program Files\FMOD SoundSystem\FMOD Studio\fmod_console.exe",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    def _find_fmod_studio_exe(self) -> Optional[str]:
        """Find FMOD Studio command line executable (fmodstudiocl.exe)"""
        # Check settings first
        settings = self.load_settings()
        if settings.get('fmod_exe_path') and os.path.exists(settings['fmod_exe_path']):
            # If it's FMOD Studio.exe, try to find fmodstudiocl.exe in same directory
            if settings['fmod_exe_path'].endswith("FMOD Studio.exe"):
                cl_path = settings['fmod_exe_path'].replace("FMOD Studio.exe", "fmodstudiocl.exe")
                if os.path.exists(cl_path):
                    return cl_path
            return settings['fmod_exe_path']

        # Search for FMOD Studio CL in common installation directories
        base_dirs = [
            r"C:\Program Files\FMOD SoundSystem",
            r"C:\Program Files (x86)\FMOD SoundSystem"
        ]

        for base_dir in base_dirs:
            if os.path.exists(base_dir):
                # Look for any FMOD Studio version folder
                for folder in os.listdir(base_dir):
                    if folder.startswith("FMOD Studio"):
                        # Prefer command line version
                        cl_path = os.path.join(base_dir, folder, "fmodstudiocl.exe")
                        if os.path.exists(cl_path):
                            return cl_path
                        # Fallback to regular exe
                        exe_path = os.path.join(base_dir, folder, "FMOD Studio.exe")
                        if os.path.exists(exe_path):
                            return exe_path

        return None

    def _open_fmod_project(self):
        """Open the current FMOD project in FMOD Studio"""
        try:
            if not self.project:
                messagebox.showerror("Error", "No FMOD project is loaded.")
                return

            # Get FMOD Studio executable path (not command line version)
            settings = self.load_settings()
            fmod_exe = None

            # Check settings first
            if settings.get('fmod_exe_path') and os.path.exists(settings['fmod_exe_path']):
                fmod_path = settings['fmod_exe_path']
                # Make sure we use the GUI version, not the command line version
                if fmod_path.endswith("fmodstudiocl.exe"):
                    fmod_exe = fmod_path.replace("fmodstudiocl.exe", "FMOD Studio.exe")
                else:
                    fmod_exe = fmod_path

            # If not found in settings, search for it
            if not fmod_exe or not os.path.exists(fmod_exe):
                base_dirs = [
                    r"C:\Program Files\FMOD SoundSystem",
                    r"C:\Program Files (x86)\FMOD SoundSystem"
                ]

                for base_dir in base_dirs:
                    if os.path.exists(base_dir):
                        for folder in os.listdir(base_dir):
                            if folder.startswith("FMOD Studio"):
                                exe_path = os.path.join(base_dir, folder, "FMOD Studio.exe")
                                if os.path.exists(exe_path):
                                    fmod_exe = exe_path
                                    break
                    if fmod_exe:
                        break

            if not fmod_exe or not os.path.exists(fmod_exe):
                messagebox.showerror("Error", "FMOD Studio executable not found.\n\nPlease configure the FMOD executable path in Settings.")
                return

            # Open the project
            project_path = str(self.project.project_path)
            subprocess.Popen([fmod_exe, project_path])

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open FMOD Studio:\n{str(e)}")

    def browse_media(self):
        """Browse for media files directory"""
        directory = filedialog.askdirectory(title="Select Media Files Directory")

        if directory:
            self.media_entry.delete(0, tk.END)
            self.media_entry.insert(0, directory)

    def browse_fmod_exe(self):
        """Browse for FMOD Studio executable"""
        filename = filedialog.askopenfilename(
            title="Select FMOD Studio Executable",
            filetypes=[
                ("Executables", "*.exe"),
                ("FMOD Studio CLI", "fmodstudiocl.exe"),
                ("FMOD Studio GUI", "FMOD Studio.exe"),
                ("All Files", "*.*")
            ]
        )

        if filename:
            self.fmod_exe_entry.delete(0, tk.END)
            self.fmod_exe_entry.insert(0, filename)
            # Save to settings immediately
            self._on_fmod_exe_changed(None)

    def _on_fmod_exe_changed(self, event):
        """Save FMOD exe path to settings when it changes"""
        fmod_exe_path = self.fmod_exe_entry.get()
        if fmod_exe_path:
            settings = self.load_settings()
            settings['fmod_exe_path'] = fmod_exe_path
            self.save_settings(settings)

            # Update version display if project is loaded
            if hasattr(self, 'project') and self.project:
                settings = self.load_settings()
                exe_path = settings.get('fmod_exe_path', '')
                self._exe_version = self.project.get_executable_version(exe_path)
                if hasattr(self, 'update_version_display'):
                    self.update_version_display()

    def select_template_folder(self):
        """Open tree dialog to select template folder"""
        if not self.project:
            messagebox.showwarning("Warning", "Please load a FMOD project first")
            return

        selected = self._show_folder_tree_dialog("Select Template Folder")
        if selected:
            folder_name, folder_id = selected
            # Calculate and display full path
            from .preset_resolver import PresetResolver
            resolver = PresetResolver(self.project)
            folder_path = resolver.get_folder_path(folder_id)
            self.template_var.set(folder_path if folder_path else folder_name)
            self.selected_template_id = folder_id
            self._auto_detect_bus_from_template()

    def select_destination_folder(self):
        """Open tree dialog to select destination folder"""
        if not self.project:
            messagebox.showwarning("Warning", "Please load a FMOD project first")
            return

        selected = self._show_folder_tree_dialog("Select Destination Folder")
        if selected:
            folder_name, folder_id = selected
            # Calculate and display full path
            from .preset_resolver import PresetResolver
            resolver = PresetResolver(self.project)
            folder_path = resolver.get_folder_path(folder_id)
            self.dest_var.set(folder_path if folder_path else folder_name)
            self.selected_dest_id = folder_id

    def select_bank(self):
        """Open tree dialog to select bank"""
        if not self.project:
            messagebox.showwarning("Warning", "Please load a FMOD project first")
            return

        selected = self._show_hierarchical_dialog(
            "Select Bank",
            self.project.banks,
            create_folder_fn=lambda name, parent_id: self.project.create_bank_folder(name, parent_id),
            create_bank_fn=lambda name, parent_id: self.project.create_bank_instance(name, parent_id),
            delete_fn=lambda item_id: self.project.delete_bank(item_id)
        )
        if selected:
            bank_name, bank_id = selected
            # Calculate and display full path
            from .preset_resolver import PresetResolver
            resolver = PresetResolver(self.project)
            bank_path = resolver.get_bank_path(bank_id)
            self.bank_var.set(bank_path if bank_path else bank_name)
            self.selected_bank_id = bank_id

    def select_bus(self):
        """Open tree dialog to select bus"""
        if not self.project:
            messagebox.showwarning("Warning", "Please load a FMOD project first")
            return

        selected = self._show_hierarchical_dialog(
            "Select Bus",
            self.project.buses,
            create_fn=lambda name, parent_id: self.project.create_bus(name),
            delete_fn=lambda item_id: self.project.delete_bus(item_id)
        )
        if selected:
            bus_name, bus_id = selected
            # Calculate and display full path
            from .preset_resolver import PresetResolver
            resolver = PresetResolver(self.project)
            bus_path = resolver.get_bus_path(bus_id)
            self.bus_var.set(bus_path if bus_path else bus_name)
            self.selected_bus_id = bus_id
            self.bus_warning_label.config(text="")

    def _set_master_bus_as_default(self):
        """Set master bus as default if no bus is selected"""
        if not self.project:
            return

        master_bus_id = self.project._get_master_bus_id()
        if master_bus_id and not self.selected_bus_id:
            # Import resolver here to avoid circular imports
            from .preset_resolver import PresetResolver
            resolver = PresetResolver(self.project)

            master_path = resolver.get_bus_path(master_bus_id)
            display_name = master_path if master_path else "Master Bus"

            self.bus_var.set(display_name)
            self.selected_bus_id = master_bus_id
            self.bus_warning_label.config(text="")

    def _auto_detect_bus_from_template(self):
        """Auto-detect bus from selected template folder"""
        if not self.project or not self.selected_template_id:
            return

        # Get bus routing from template events
        common_bus_id, all_same, bus_ids = self.project.get_bus_from_template_events(
            self.selected_template_id
        )

        if not bus_ids:  # No events in template folder
            self.bus_warning_label.config(text="")
            return

        if all_same and common_bus_id:
            # Check if bus exists in current project
            if common_bus_id in self.project.buses:
                # Auto-populate bus field
                from .preset_resolver import PresetResolver
                resolver = PresetResolver(self.project)
                bus_path = resolver.get_bus_path(common_bus_id)

                self.bus_var.set(bus_path if bus_path else self.project.buses[common_bus_id]['name'])
                self.selected_bus_id = common_bus_id
                self.bus_warning_label.config(text="")
            else:
                # Bus doesn't exist - warn user
                self.bus_warning_label.config(
                    text="⚠ Template bus not found in project - please select a bus"
                )
                self.bus_var.set("(No bus selected)")
                self.selected_bus_id = None
        else:
            # Different buses detected
            self.bus_warning_label.config(
                text=f"⚠ Template events use {len(bus_ids)} different buses"
            )

    def select_asset_folder(self):
        """Open tree dialog to select asset folder"""
        if not self.project:
            messagebox.showwarning("Warning", "Please load a FMOD project first")
            return

        selected = self._show_asset_tree_dialog("Select Audio Asset Folder")
        if selected:
            asset_path, asset_id = selected
            self.asset_var.set(asset_path)
            self.selected_asset_id = asset_id

    def load_project(self, project_path: str = None):
        """Load FMOD project and populate dropdowns"""
        try:
            # Use provided path or get from entry field
            if project_path is None:
                project_path = self.project_entry.get()

            if not project_path or not os.path.exists(project_path):
                messagebox.showwarning("Warning", "Please select a valid FMOD project file")
                return

            self.project = FMODProject(project_path)

            # Initialize selection variables
            self.selected_template_id = None
            self.selected_dest_id = None
            self.selected_bank_id = None
            self.selected_bus_id = None
            self.selected_asset_id = None

            # Auto-populate bus with master bus
            self._set_master_bus_as_default()

            # Project loaded successfully - no popup needed

            # Update version display with project version
            settings = self.load_settings()
            exe_path = settings.get('fmod_exe_path', '')
            self._project_version = self.project.get_project_version()
            self._exe_version = self.project.get_executable_version(exe_path)
            if hasattr(self, 'update_version_display'):
                self.update_version_display()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load project:\n{str(e)}")

    def _set_window_icon(self):
        """Set the window icon for the application."""
        try:
            # Determine the base path (handles both dev and PyInstaller)
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                base_path = sys._MEIPASS
            else:
                # Running in development
                base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

            icon_path = os.path.join(base_path, 'Logo', 'FmodImporterLogo.ico')

            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            # Silently fail if icon cannot be set
            print(f"Warning: Could not set window icon: {e}")

    def _on_closing(self):
        """Handle window close event - clear pending folders"""
        if self.project:
            count = self.project.clear_pending_folders()
            if count > 0:
                print(f"Cleared {count} uncommitted folder(s)")
        self.root.destroy()
