"""
GUI Import Workflow Mixin Module
Handles the import workflow for importing audio assets to FMOD.
"""

import os
import json
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from ..naming import NamingPattern


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

        try:
            # Use PowerShell to get FMOD Studio processes with command line
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
                return False  # No FMOD Studio running, safe to proceed

            # Get current project path (normalized for comparison)
            current_project = str(self.project.project_path).lower().replace('/', '\\')

            # Check each command line for matching project
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue

                # Look for .fspro file in command line
                if '.fspro' in line.lower():
                    # Extract project path using regex
                    match = re.search(r'([A-Za-z]:[^"]*\.fspro)', line, re.IGNORECASE)
                    if match:
                        running_project = match.group(1).lower().replace('/', '\\')
                        if running_project == current_project:
                            return True  # Same project is running!

            return False  # Different project or no project detected

        except Exception:
            return False  # Fail-safe: don't block on detection errors

    def import_assets(self):
        """Import assets using FMOD JavaScript API via auto-execute script"""
        import threading
        from .utils import ProgressDialog

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
            if self._check_fmod_project_running():
                messagebox.showerror(
                    "FMOD Studio Running",
                    "FMOD Studio is currently open with this project.\n\n"
                    "Please close FMOD Studio before importing to avoid conflicts."
                )
                return

            asset_id = getattr(self, "selected_asset_id", None)
            if not asset_id:
                messagebox.showerror("Error", "Please select an audio asset folder.")
                return

            # 1.5. Commit any pending folders before import (BEFORE checking if asset folder exists)
            try:
                event_count, asset_count = self.project.commit_pending_folders()
                if event_count > 0 or asset_count > 0:
                    print(f"Committed {event_count} event folder(s) and {asset_count} asset folder(s)")
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

            prefix = self._get_entry_value(self.prefix_entry, "e.g. Mechaflora")
            feature = self._get_entry_value(self.feature_entry, "e.g. FeatureName, Feature_Name, feature_name, ...")
            if not prefix or not feature:
                messagebox.showerror("Error", "Please specify prefix and feature name.")
                return

            template_folder_id = getattr(self, "selected_template_id", None)
            dest_folder_id = getattr(self, "selected_dest_id", None)
            bank_id = getattr(self, "selected_bank_id", None)
            bus_id = getattr(self, "selected_bus_id", None)

            if not all([dest_folder_id, bank_id, bus_id]):
                messagebox.showerror("Error", "Please select destination folder, bank, and bus.")
                return

            # 4. Load templates (OPTIONAL)
            template_events = []
            if template_folder_id:
                template_events = self.project.get_events_in_folder(template_folder_id)
                # Empty template folder is OK - events without matches will be created from scratch

            # Build template map by name for direct lookup
            template_by_name = {}
            for tmpl in template_events:
                template_by_name[tmpl["name"]] = tmpl

            # 5. Build import data using direct template linkage from matched_template field
            import_events = []
            template_folder_path = self._get_folder_path(template_folder_id)
            dest_folder_path = self._get_folder_path(dest_folder_id)
            bank_name = self.project.banks[bank_id]["name"]
            bus_name = self.project.buses[bus_id]["name"]
            bus_path = self._get_bus_path(bus_id)  # Full path for hierarchical creation

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

                # Get event name from tree (clean it from checkbox/confidence symbols)
                event_name_raw = self.preview_tree.item(item, "text")
                event_name = self._clean_event_name(event_name_raw)

                if event_name not in event_audio_map:
                    continue

                event_data = event_audio_map[event_name]
                audio_entries = event_data['audio_files']
                matched_template = event_data.get('matched_template')

                # Find the template by name (may be None for auto-created events)
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
                    audio_paths.append(resolved_path.resolve().as_posix())

                if not audio_paths:
                    continue

                # Build event payload
                event_payload = {
                    "newEventName": event_name,
                    "destFolderPath": dest_folder_path,
                    "audioFilePaths": audio_paths,
                    "assetFolderPath": asset_folder,
                    "bankName": bank_name,
                    "busName": bus_path or bus_name,
                    "isMulti": len(audio_paths) > 1,
                }

                # Add templateEventPath ONLY if template exists
                if tmpl:
                    event_payload["templateEventPath"] = f"{template_folder_path}/{tmpl['name']}"

                import_events.append(event_payload)

            if not import_events:
                # Debug: show what went wrong
                debug_info = "No events matched templates.\n\n"
                debug_info += f"Total events in preview: {len(event_audio_map)}\n"
                debug_info += f"Auto-created events (skipped): {skipped_count}\n\n"
                debug_info += f"Template names ({len(template_events)}):\n"
                for tmpl in template_events[:5]:
                    debug_info += f"  - {tmpl['name']}\n"
                debug_info += f"\nEvent -> Template mappings:\n"
                for ev_name, ev_data in list(event_audio_map.items())[:5]:
                    matched = ev_data['matched_template']
                    debug_info += f"  - {ev_name} -> {matched or '(auto-created)'}\n"
                if len(event_audio_map) > 5:
                    debug_info += f"  ... and {len(event_audio_map) - 5} more\n"
                messagebox.showerror("Error", debug_info)
                return

            # 6. Copy audio files to FMOD Assets folder
            project_dir = self.project.project_path.parent
            assets_dir = project_dir / "Assets"

            for event in import_events:
                # Create destination folder
                dest_folder = assets_dir / event["assetFolderPath"]
                dest_folder.mkdir(parents=True, exist_ok=True)

                # Copy each audio file and update paths
                copied_paths = []
                for source_path in event["audioFilePaths"]:
                    source = Path(source_path)
                    dest = dest_folder / source.name

                    # Copy file (overwrites automatically if exists)
                    shutil.copy2(source, dest)
                    copied_paths.append(str(dest.as_posix()))

                # Update paths to point to copied files
                event["audioFilePaths"] = copied_paths

            # 7. Create JSON and auto-exec script
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            json_path = temp_dir / f"fmod_import_data_{uuid.uuid4().hex}.json"
            result_path = temp_dir / f"fmod_import_result_{uuid.uuid4().hex}.json"

            import_payload = {
                "projectPath": str(self.project.project_path),
                "resultPath": str(result_path),
                "bankName": bank_name,
                "busName": bus_path or bus_name,  # Full path for hierarchical bus creation
                "defaultDestFolderPath": dest_folder_path,
                "events": import_events,
            }

            with open(json_path, "w", encoding="utf-8") as fh:
                json.dump(import_payload, fh, indent=2)

            # Write debug log for Python side
            debug_log_path = temp_dir / f"fmod_import_python_debug_{uuid.uuid4().hex}.txt"
            with open(debug_log_path, "w", encoding="utf-8") as fh:
                fh.write("=" * 80 + "\n")
                fh.write("PYTHON IMPORT GENERATION DEBUG\n")
                fh.write("=" * 80 + "\n\n")
                fh.write(f"Timestamp: {uuid.uuid4()}\n")
                fh.write(f"Project: {self.project.project_path}\n")
                fh.write(f"JSON Path: {json_path}\n")
                fh.write(f"Result Path: {result_path}\n\n")

                fh.write(f"[USER SELECTIONS]\n")
                fh.write(f"  Prefix: {prefix}\n")
                fh.write(f"  Feature Name: {feature}\n")
                fh.write(f"  Media Path: {media_path}\n")
                fh.write(f"  Asset Folder ID: {asset_id}\n")
                fh.write(f"  Asset Folder Path: {asset_folder}\n")
                fh.write(f"  Template Folder ID: {template_folder_id}\n")
                fh.write(f"  Template Folder Path: {template_folder_path}\n")
                fh.write(f"  Dest Folder ID: {dest_folder_id}\n")
                fh.write(f"  Dest Folder Path: {dest_folder_path}\n")
                fh.write(f"  Bank ID: {bank_id}\n")
                fh.write(f"  Bank Name: {bank_name}\n")
                fh.write(f"  Bus ID: {bus_id}\n")
                fh.write(f"  Bus Name: {bus_name}\n")
                fh.write(f"  Bus Path: {bus_path}\n\n")

                fh.write(f"[EVENTS TO IMPORT] ({len(import_events)} total)\n")
                for event in import_events:
                    fh.write(f"\n  Event: {event['newEventName']}\n")
                    fh.write(f"    Template: {event.get('templateEventPath', '(auto-created)')}\n")
                    fh.write(f"    Dest Folder: {event['destFolderPath']}\n")
                    fh.write(f"    Asset Folder: {event['assetFolderPath']}\n")
                    fh.write(f"    Bank: {event['bankName']}\n")
                    fh.write(f"    Bus Path: {event['busName']}\n")
                    fh.write(f"    Is Multi: {event['isMulti']}\n")
                    fh.write(f"    Audio Files: {len(event['audioFilePaths'])}\n")
                    for i, path in enumerate(event['audioFilePaths'], 1):
                        fh.write(f"      {i}. {path}\n")

                fh.write(f"\n[JSON PAYLOAD]\n")
                fh.write(json.dumps(import_payload, indent=2))

            # 7. Execute import directly via FMOD Studio command line
            num_events = len(import_events)

            # Find FMOD Studio executable
            fmod_exe = self._find_fmod_studio_exe()
            if not fmod_exe:
                msg = (f"Import JSON created for {num_events} event(s).\\n\\n"
                       "Could not find FMOD Studio executable.\\n"
                       "Please set it in Settings or import manually:\\n"
                       "  Scripts > FMOD Importer: Import JSON")
                messagebox.showwarning("Manual Import Required", msg)
                return

            # Execute the import script via FMOD Studio
            # Determine base path (handles both dev and PyInstaller)
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                base_path = sys._MEIPASS
            else:
                # Running in development
                base_path = Path(__file__).resolve().parent.parent.parent

            script_path = Path(base_path) / "Script" / "_Internal" / "FmodImportFromJson.js"

            # Create progress dialog
            progress = ProgressDialog(
                self.root,
                "Import in Progress",
                f"Preparing to import {num_events} event(s)...\n\nPlease wait, this may take several minutes."
            )

            # Define import function to run in background thread
            def _do_import_in_thread():
                """Execute import in background thread to prevent UI freeze"""
                nonlocal result_path  # Required: allows reassignment of outer scope variable
                try:
                    # Update progress message
                    self.root.after(0, lambda: progress.update_message(
                        f"Copying audio files to FMOD Assets folder...\n\nPlease wait, this may take several minutes."
                    ))

                    # Create a temporary wrapper script that includes the JSON path
                    # This is needed because fmodstudiocl.exe doesn't pass arguments to scripts
                    wrapper_script_path = json_path.parent / "_temp_import_wrapper.js"

                    # Read the main import script content (Python can access _MEIPASS, FMOD Studio cannot)
                    with open(script_path, 'r', encoding='utf-8') as f:
                        import_script_content = f.read()

                    # Embed the script content directly in the wrapper
                    # This works around PyInstaller's temp folder being inaccessible to external processes
                    wrapper_script_content = f"""
// Temporary wrapper script - auto-generated
// Embeds the import script content directly (PyInstaller workaround)

// Set global variables expected by the import script
var FMOD_IMPORTER_JSON_PATH = "{str(json_path).replace(chr(92), '/')}";
var resultPath = "{str(result_path).replace(chr(92), '/')}";

// === EMBEDDED IMPORT SCRIPT START ===
{import_script_content}
// === EMBEDDED IMPORT SCRIPT END ===
"""

                    with open(wrapper_script_path, 'w', encoding='utf-8') as f:
                        f.write(wrapper_script_content)

                    # Build command: fmodstudiocl.exe -script wrapper.js project.fspro
                    cmd = [
                        str(fmod_exe),
                        "-script",
                        str(wrapper_script_path),
                        str(self.project.project_path)
                    ]

                    # Update progress message
                    self.root.after(0, lambda: progress.update_message(
                        f"Executing FMOD Studio import for {num_events} event(s)...\n\nPlease wait, this may take several minutes."
                    ))
                    print(f"Executing command: {' '.join(cmd)}")

                    # Execute the command
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minute timeout
                    )

                    # Clean up wrapper script
                    try:
                        if wrapper_script_path.exists():
                            wrapper_script_path.unlink()
                    except:
                        pass

                    # Print output for debugging
                    print("STDOUT:", result.stdout)
                    print("STDERR:", result.stderr)
                    print("Return code:", result.returncode)

                    # Wait for result file to be written (with timeout)
                    print(f"DEBUG: Waiting for result file: {result_path}")
                    result_found = False
                    wait_time = 0
                    max_wait = 10  # 10 seconds should be enough since FMOD has already exited

                    while wait_time < max_wait:
                        if result_path.exists():
                            print(f"DEBUG: Result file found after {wait_time}s")
                            result_found = True
                            break

                        time.sleep(1)
                        wait_time += 1

                    # Close progress dialog
                    self.root.after(0, lambda: progress.close())

                    # If not found in temp, search for fallback files
                    if not result_found:
                        print(f"WARNING: Result file not found in temp after {max_wait}s")

                        # Search in temp directory first
                        import glob
                        temp_dir = result_path.parent
                        pattern = str(temp_dir / "fmod_import_result_*.json")
                        recent_results = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)

                        if recent_results:
                            result_path = Path(recent_results[0])
                            result_found = True
                            print(f"DEBUG: Found fallback result in temp: {result_path}")

                    # If still not found, search in project directory
                    if not result_found:
                        project_dir = Path(self.project.project_path).parent
                        fallback_patterns = [
                            "fmod_import_result_fallback.json",
                            "fmod_import_result_emergency.json",
                            "fmod_import_result_*.json"
                        ]

                        print(f"DEBUG: Searching for fallback result files in: {project_dir}")

                        for pattern in fallback_patterns:
                            fallback_files = list(project_dir.glob(pattern))
                            if fallback_files:
                                # Prendre le plus récent
                                result_path = max(fallback_files, key=lambda p: p.stat().st_mtime)
                                result_found = True
                                print(f"DEBUG: Found fallback result in project: {result_path}")
                                break

                    # Check result file
                    if result_found and result_path.exists():
                        with open(result_path, 'r', encoding='utf-8') as f:
                            import_result = json.load(f)

                        success_msg = (f"Import Complete!\n\n"
                                     f"Imported: {import_result.get('imported', 0)}\n"
                                     f"Failed: {import_result.get('failed', 0)}")

                        if import_result.get('messages'):
                            success_msg += "\n\nMessages:\n" + "\n".join(import_result['messages'][:5])

                        # Show success message and ask if user wants to open the project
                        def _show_success():
                            if messagebox.askyesno("Import Complete", success_msg + "\n\nDo you want to open the project in FMOD Studio?"):
                                self._open_fmod_project()

                        self.root.after(0, _show_success)
                    else:
                        # No result file found after all attempts - create emergency result
                        print("WARNING: Creating emergency result file (import status unknown)")

                        # Get number of events that were supposed to be imported
                        num_events_attempted = len(self.preview_tree.get_children())

                        emergency_result = {
                            "success": False,
                            "error": "Result file not created by FMOD Studio script",
                            "imported": 0,
                            "skipped": 0,
                            "failed": num_events_attempted,
                            "messages": [
                                "CRITICAL: FMOD Studio did not create result file",
                                "Possible causes:",
                                "- Script execution failed silently",
                                "- FMOD Studio crashed during import",
                                "- Permissions issue preventing file write",
                                "",
                                f"Result file expected at: {result_path}",
                                f"Also searched in project directory: {Path(self.project.project_path).parent}",
                                "",
                                "Please check:",
                                "1. FMOD Studio installation is working correctly",
                                "2. You have write permissions in temp and project directories",
                                "3. Antivirus is not blocking FMOD Studio scripts",
                                "",
                                "Recommendation: Try importing again with FMOD Studio closed."
                            ]
                        }

                        # Try to save emergency result in project directory
                        try:
                            emergency_path = Path(self.project.project_path).parent / "fmod_import_result_emergency.json"
                            with open(emergency_path, 'w', encoding='utf-8') as f:
                                json.dump(emergency_result, f, indent=2)
                            print(f"DEBUG: Emergency result saved to: {emergency_path}")
                        except Exception as e:
                            print(f"ERROR: Could not save emergency result: {e}")

                        # Show error message to user
                        error_msg = (
                            "Import Status Unknown - No result file created\n\n"
                            "FMOD Studio executed but did not create a result file.\n\n"
                            "Possible causes:\n"
                            "• Script execution failed silently\n"
                            "• FMOD Studio crashed during import\n"
                            "• Permissions issue preventing file write\n\n"
                            f"Searched locations:\n"
                            f"• Temp: {result_path}\n"
                            f"• Project: {Path(self.project.project_path).parent}\n\n"
                            "Recommendation:\n"
                            "1. Close FMOD Studio completely\n"
                            "2. Check file permissions\n"
                            "3. Try importing again"
                        )

                        self.root.after(0, lambda: messagebox.showwarning(
                            "Import Status Unknown",
                            error_msg
                        ))

                except subprocess.TimeoutExpired:
                    self.root.after(0, lambda: progress.close())
                    self.root.after(0, lambda: messagebox.showerror(
                        "Import Timeout",
                        "Import operation timed out after 5 minutes.\n"
                        "The project may be too large."
                    ))
                except Exception as e:
                    self.root.after(0, lambda: progress.close())
                    error_msg = f"Failed to execute import:\n{str(e)}\n\n" \
                                "You can try manual import:\n" \
                                "Scripts > FMOD Importer: Import JSON"
                    self.root.after(0, lambda: messagebox.showerror("Import Failed", error_msg))

            # Start import in background thread (daemon=True ensures proper cleanup)
            import_thread = threading.Thread(target=_do_import_in_thread, daemon=True)
            import_thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to prepare import: {str(e)}")
            import traceback
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
