"""
GUI Main Module
Contains the main FmodImporterGUI class that combines all mixins.
"""

import os
import platform
import subprocess
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


class FmodImporterGUI(
    UtilsMixin,
    WidgetsMixin,
    DialogsMixin,
    AssetDialogsMixin,
    DragDropMixin,
    AnalysisMixin,
    ImportMixin,
    SettingsMixin
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

        # Set window size to 4:3 ratio (1440x1080)
        self.root.geometry("1440x1080")
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

    def select_template_folder(self):
        """Open tree dialog to select template folder"""
        if not self.project:
            messagebox.showwarning("Warning", "Please load a FMOD project first")
            return

        selected = self._show_folder_tree_dialog("Select Template Folder")
        if selected:
            folder_name, folder_id = selected
            self.template_var.set(folder_name)
            self.selected_template_id = folder_id

    def select_destination_folder(self):
        """Open tree dialog to select destination folder"""
        if not self.project:
            messagebox.showwarning("Warning", "Please load a FMOD project first")
            return

        selected = self._show_folder_tree_dialog("Select Destination Folder")
        if selected:
            folder_name, folder_id = selected
            self.dest_var.set(folder_name)
            self.selected_dest_id = folder_id

    def select_bank(self):
        """Open tree dialog to select bank"""
        if not self.project:
            messagebox.showwarning("Warning", "Please load a FMOD project first")
            return

        selected = self._show_hierarchical_dialog(
            "Select Bank",
            self.project.banks,
            create_fn=lambda name, parent_id: self.project.create_bank(name),
            delete_fn=lambda item_id: self.project.delete_bank(item_id)
        )
        if selected:
            bank_name, bank_id = selected
            self.bank_var.set(bank_name)
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
            self.bus_var.set(bus_name)
            self.selected_bus_id = bus_id

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

            # Project loaded successfully - no popup needed

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load project:\n{str(e)}")

    def _on_closing(self):
        """Handle window close event - clear pending folders"""
        if self.project:
            count = self.project.clear_pending_folders()
            if count > 0:
                print(f"Cleared {count} uncommitted folder(s)")
        self.root.destroy()
