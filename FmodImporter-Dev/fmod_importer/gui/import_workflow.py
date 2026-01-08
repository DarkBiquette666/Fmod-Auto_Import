"""
GUI Import Workflow Mixin Module
Handles the import workflow for importing audio assets to FMOD.
"""

import os
import shutil
import threading
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from ..naming import NamingPattern
from .utils import ProgressDialog


class ImportMixin:
    """
    Mixin class providing import workflow functionality.

    These methods are mixed into FmodImporterGUI via multiple inheritance.
    All methods access shared state through 'self'.
    """

    def _check_fmod_project_running(self) -> bool:
        """
        Check if FMOD Studio is running with the current project.

        Returns:
            True if the same project is open in FMOD Studio (should block import)
            False otherwise (safe to proceed)
        """
        import re
        import platform
        import subprocess

        try:
            # Get current project path (normalized for comparison)
            current_project = str(self.project.project_path)

            if platform.system() == "Windows":
                # Windows: Use PowerShell to get FMOD Studio processes with command line
                ps_cmd = (
                    "Get-CimInstance Win32_Process | "
                    "Where-Object { $_.Name -like '*FMOD*Studio*' } | "
                    "Select-Object -ExpandProperty CommandLine"
                )

                result = subprocess.run(
                    ['powershell', '-Command', ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                if result.returncode != 0 or not result.stdout.strip():
                    return False

                current_project_norm = current_project.lower().replace('/', '\\')
                process_list = result.stdout.strip().split('\n')

            else:
                # macOS/Linux: Use pgrep to get command line
                # -f matches against full command line, -l lists the process name/cmdline
                try:
                    result = subprocess.run(
                        ['pgrep', '-fl', 'FMOD Studio'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                except FileNotFoundError:
                    # pgrep might not be available, try ps
                    result = subprocess.run(
                        ['ps', '-A', '-o', 'command'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                if result.returncode != 0 or not result.stdout.strip():
                    return False

                current_project_norm = current_project.lower() # Unix paths are case-sensitive usually, but FMOD might normalize
                process_list = result.stdout.strip().split('\n')

            # Check each command line for matching project
            for line in process_list:
                line = line.strip()
                if not line:
                    continue

                # Look for .fspro file in command line
                if '.fspro' in line.lower():
                    # Extract project path using regex
                    # Windows: drive letter or UNC
                    # Unix: /path/to/file
                    if platform.system() == "Windows":
                        match = re.search(r'([A-Za-z]:[^"]*\.fspro)', line, re.IGNORECASE)
                    else:
                        # Match absolute path starting with /
                        match = re.search(r'(/[^"]*\.fspro)', line, re.IGNORECASE)

                    if match:
                        running_project = match.group(1).lower()
                        if platform.system() == "Windows":
                            running_project = running_project.replace('/', '\\')
                        
                        # Compare normalized paths
                        # On Mac, paths might be /Users/name/... or /System/Volumes/Data/Users/...
                        # Simple substring check is safer than exact equality
                        if current_project_norm in running_project or running_project in current_project_norm:
                            return True  # Same project is running!

            return False  # Different project or no project detected

        except Exception as e:
            print(f"Warning: Failed to check running process: {e}")
            return False  # Fail-safe: don't block on detection errors

    def import_assets(self):
        """Import assets using Python-based XML manipulation"""
        try:
            # 1. Validate inputs
            if not self.project:
                messagebox.showerror("Error", "No FMOD Studio project is loaded.")
                return

            # Check for version mismatch (should have been caught during analysis)
            if getattr(self, '_version_mismatch', False):
                messagebox.showerror("Error", "Cannot import due to FMOD Studio version mismatch. Please run Analysis again with matching versions.")
                return

            # Check if FMOD Studio is running with this project
            # CRITICAL for Python-based import as we modify XMLs directly
            if self._check_fmod_project_running():
                messagebox.showerror(
                    "FMOD Studio Running",
                    "FMOD Studio is currently open with this project.\n\n"
                    "Crucial Safety Warning:\n"
                    "You MUST close FMOD Studio before importing to prevent project corruption.\n"
                    "This tool modifies project XML files directly."
                )
                return

            asset_id = getattr(self, "selected_asset_id", None)
            if not asset_id:
                messagebox.showerror("Error", "Please select an audio asset folder.")
                return

            # 1.5. Commit any pending folders before import (BEFORE checking if asset folder exists)
            try:
                event_count, asset_count, bank_count, bus_count = self.project.commit_pending_folders()
                if any([event_count, asset_count, bank_count, bus_count]):
                    print(f"Committed changes: {event_count} event folders, {asset_count} asset folders, {bank_count} banks, {bus_count} buses")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to commit pending folders:\n{str(e)}")
                return

            # Now check if asset folder exists (after committing pending folders)
            asset_info = self.project.asset_folders.get(asset_id)
            if not asset_info:
                messagebox.showerror("Error", "Selected audio asset folder could not be found.")
                return

            asset_folder = asset_info["path"] or ""
            if asset_folder and not asset_folder.endswith(("/", "\\\\")):
                asset_folder += "/"

            media_path_input = self.media_entry.get()
            media_root = Path(media_path_input) if media_path_input else None

            # 2. Get event-audio mapping from preview tree
            event_audio_map = {}
            for item in self.preview_tree.get_children():
                event_name_raw = self.preview_tree.item(item, "text")
                event_name = self._clean_event_name(event_name_raw)

                # Get matched template from parent values (4th column, index 3)
                parent_values = self.preview_tree.item(item, "values") or []
                matched_template = parent_values[3] if len(parent_values) > 3 else ''

                audio_files = []
                for child in self.preview_tree.get_children(item):
                    audio_label = self.preview_tree.item(child, "text") or ""
                    if "->" in audio_label:
                        audio_label = audio_label.split("->", 1)[1]
                    audio_label = audio_label.strip()

                    values = self.preview_tree.item(child, "values") or []
                    audio_path = values[0] if len(values) > 0 and values[0] else None

                    if not audio_path:
                        if media_root:
                            audio_path = str((media_root / audio_label).resolve())
                        else:
                            audio_path = audio_label

                    audio_path = os.path.normpath(audio_path)
                    audio_files.append((audio_label, audio_path))

                if audio_files:
                    event_audio_map[event_name] = {
                        'audio_files': audio_files,
                        'matched_template': matched_template
                    }

            if not event_audio_map:
                messagebox.showerror("Error", "No events in the preview tree to import.")
                return

            # 3. Validate other fields
            media_path = media_path_input
            if not media_path or not os.path.exists(media_path):
                messagebox.showerror("Error", "Please specify a valid media path.")
                return

            template_folder_id = getattr(self, "selected_template_id", None)
            dest_folder_id = getattr(self, "selected_dest_id", None)
            bank_id = getattr(self, "selected_bank_id", None)
            bus_id = getattr(self, "selected_bus_id", None)

            if not all([dest_folder_id, bank_id, bus_id]):
                messagebox.showerror("Error", "Please select destination folder, bank, and bus.")
                return

            # Check if IDs actully exist (validation against stale presets)
            if dest_folder_id not in self.project.event_folders:
                 messagebox.showerror("Error", f"Selected destination folder not found in project.\nID: {dest_folder_id}")
                 return
            
            if bank_id not in self.project.banks:
                 messagebox.showerror("Error", f"Selected Bank not found in project.\nID: {bank_id}")
                 return

            if bus_id not in self.project.buses:
                 messagebox.showerror("Error", f"Selected Bus not found in project.\nID: {bus_id}")
                 return

            # 4. Load templates
            template_events = []
            if template_folder_id:
                template_events = self.project.get_events_in_folder(template_folder_id)

            # Build template map by name for direct lookup
            template_by_name = {}
            for tmpl in template_events:
                template_by_name[tmpl["name"]] = tmpl

            # 5. Build list of events to process
            events_to_process = []

            # Check if any events are selected
            if not any(item in self.preview_checked_items for item in self.preview_tree.get_children()):
                messagebox.showwarning("Warning", "No events selected for import. Please check at least one event in the preview.")
                return

            skipped_count = 0
            for item in self.preview_tree.get_children():
                # Skip unchecked items
                if item not in self.preview_checked_items:
                    skipped_count += 1
                    continue

                event_name_raw = self.preview_tree.item(item, "text")
                event_name = self._clean_event_name(event_name_raw)

                if event_name not in event_audio_map:
                    continue

                event_data = event_audio_map[event_name]
                audio_entries = event_data['audio_files']
                matched_template = event_data.get('matched_template')

                # Find the template by name
                tmpl = None
                if matched_template and matched_template in template_by_name:
                    tmpl = template_by_name[matched_template]

                # Resolve audio file paths
                audio_paths = []
                for label, path_str in audio_entries:
                    resolved_path = Path(path_str)
                    if not resolved_path.is_absolute():
                        resolved_path = Path(media_path) / resolved_path
                    if not resolved_path.exists():
                        continue
                    audio_paths.append(str(resolved_path.resolve()))

                if not audio_paths:
                    continue

                # Support Auto-Create (no template)
                template_id = tmpl['id'] if tmpl else None
                
                events_to_process.append({
                    'name': event_name,
                    'template_id': template_id,
                    'audio_files': audio_paths
                })

            if not events_to_process:
                messagebox.showerror("Error", "No valid events to import.\n\nEnsure selected events have valid audio files and matching templates.")
                return

            # Confirm action
            if not messagebox.askyesno("Confirm Import",
                                     f"Ready to import {len(events_to_process)} events.\n\n"
                                     "FMOD Studio MUST be closed.\n"
                                     "Project files will be modified directly.\n\n"
                                     "Proceed?"):
                return

            # 6. Execute Import Loop
            num_events = len(events_to_process)
            progress = ProgressDialog(
                self.root,
                "Importing Assets",
                f"Preparing to import {num_events} events..."
            )

            # Define worker function
            def _do_import_in_thread():
                results = {
                    'success': 0,
                    'failed': 0,
                    'errors': []
                }

                try:
                    for i, event in enumerate(events_to_process):
                        msg = f"Importing {i+1}/{num_events}: {event['name']}"
                        self.root.after(0, lambda m=msg: progress.update_message(m))

                        try:
                            # Python-based deep copy and audio assignment
                            if event['template_id']:
                                self.project.copy_event_from_template(
                                    template_event_id=event['template_id'],
                                    new_name=event['name'],
                                    dest_folder_id=dest_folder_id,
                                    bank_id=bank_id,
                                    bus_id=bus_id,
                                    audio_files=event['audio_files'],  # Source paths
                                    audio_asset_folder=asset_folder    # Dest folder relative to Assets/
                                )
                            else:
                                # Auto-Create (from scratch)
                                self.project.create_event_from_scratch(
                                    new_name=event['name'],
                                    dest_folder_id=dest_folder_id,
                                    bank_id=bank_id,
                                    bus_id=bus_id,
                                    audio_files=event['audio_files'],
                                    audio_asset_folder=asset_folder
                                )
                            
                            results['success'] += 1

                        except Exception as e:
                            results['failed'] += 1
                            error_msg = f"{event['name']}: {str(e)}"
                            results['errors'].append(error_msg)
                            print(f"Error importing {event['name']}: {e}")
                            traceback.print_exc()

                except Exception as fatal_e:
                    self.root.after(0, lambda: messagebox.showerror("Fatal Error", f"Import crashed: {str(fatal_e)}"))
                    traceback.print_exc()

                finally:
                    self.root.after(0, progress.close)

                    # Show summary
                    def _show_summary():
                        if results['failed'] == 0:
                            messagebox.showinfo("Import Complete",
                                              f"Successfully imported {results['success']} events.")
                        else:
                            error_text = "\n".join(results['errors'][:5])
                            if len(results['errors']) > 5:
                                error_text += f"\n...and {len(results['errors']) - 5} more."
                            
                            messagebox.showwarning("Import Completed with Errors",
                                                 f"Imported: {results['success']}\n"
                                                 f"Failed: {results['failed']}\n\n"
                                                 f"Errors:\n{error_text}")
                        
                        # Optionally open project?
                        # Since we modified XMLs directly, user opens FMOD manually usually.
                        if messagebox.askyesno("Open Project", "Import complete. Open FMOD Studio now?"):
                            self._open_fmod_project()

                    self.root.after(0, _show_summary)

            # Start thread
            import_thread = threading.Thread(target=_do_import_in_thread, daemon=True)
            import_thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start import: {str(e)}")
            traceback.print_exc()

    def _get_folder_path(self, folder_id):
        """Get full path of an event folder (excluding master folder)"""
        parts = []
        current_id = folder_id
        master_folder_id = self.project.workspace['masterEventFolder']

        while current_id and current_id in self.project.event_folders:
            # Don't include the master folder itself
            if current_id == master_folder_id:
                break

            folder = self.project.event_folders[current_id]
            parts.insert(0, folder['name'])
            current_id = folder.get('parent')

        return '/'.join(parts)

    def _get_bus_path(self, bus_id):
        """Get full path of a bus (excluding master bus)"""
        parts = []
        current_id = bus_id
        master_bus_id = self.project._get_master_bus_id()

        while current_id and current_id in self.project.buses:
            # Don't include the master bus itself
            if current_id == master_bus_id:
                break

            bus = self.project.buses[current_id]
            parts.insert(0, bus['name'])
            current_id = bus.get('parent')

        return '/'.join(parts)


