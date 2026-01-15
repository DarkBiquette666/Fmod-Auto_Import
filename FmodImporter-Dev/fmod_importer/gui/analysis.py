"""
GUI Analysis Mixin Module
Handles the analysis workflow for matching audio files to events.
"""

import os
import tkinter as tk
from tkinter import messagebox

from ..naming import NamingPattern, format_template_name
from ..matcher import AudioMatcher


class AnalysisMixin:
    """
    Mixin class providing analysis functionality.

    These methods are mixed into FmodImporterGUI via multiple inheritance.
    All methods access shared state through 'self'.
    """

    def analyze(self):
        """Analyze what will be imported and populate preview tree"""
        try:
            # Validate inputs
            if not self.project:
                messagebox.showwarning("Warning", "Please load a FMOD project first")
                return

            # VERSION VALIDATION - Check for FMOD Studio version mismatch
            project_version = self.project.get_project_version()
            settings = self.load_settings()
            exe_path = settings.get('fmod_exe_path', '')
            exe_version = self.project.get_executable_version(exe_path)

            # Store versions for UI display
            self._project_version = project_version
            self._exe_version = exe_version

            if project_version and exe_version:
                versions_match = self.project.compare_versions(project_version, exe_version)

                if not versions_match:
                    # Extract major.minor for display (e.g., "2.03.00" -> "2.03")
                    project_ver_short = '.'.join(project_version.split('.')[:2])
                    exe_ver_short = '.'.join(exe_version.split('.')[:2])

                    error_msg = (
                        f"FMOD Studio Version Mismatch\n\n"
                        f"Project Version: {project_ver_short}\n"
                        f"Executable Version: {exe_ver_short}\n\n"
                        f"Import will fail with mismatched versions.\n\n"
                        f"Please update the FMOD Studio Executable path in the Paths section "
                        f"to use FMOD Studio {project_ver_short}.xx"
                    )

                    messagebox.showerror("Version Mismatch", error_msg)

                    # Mark mismatch for UI state management
                    self._version_mismatch = True

                    # Update version display
                    if hasattr(self, 'update_version_display'):
                        self.update_version_display()

                    # Import button will be disabled by update_import_button_state()
                    return  # BLOCK ANALYSIS - don't continue
            else:
                # Version detection failed - allow import but don't mark as mismatch
                self._version_mismatch = False

            # Update version display if versions were detected
            if hasattr(self, 'update_version_display'):
                self.update_version_display()

            media_path = self.media_entry.get()
            if not media_path or not os.path.exists(media_path):
                messagebox.showwarning("Warning", "Please select a valid media directory")
                return

            # Get config values (check for placeholders)
            prefix = self._get_entry_value(self.prefix_entry, 'e.g. Mechaflora')
            feature = self._get_entry_value(self.feature_entry, 'e.g. FeatureName, Feature_Name, feature_name, ...')

            if not prefix or not feature:
                messagebox.showwarning("Warning", "Please fill in Prefix and Feature Name")
                return

            # Get event pattern string (validation deferred)
            pattern_str = self.pattern_var.get()

            # Check Import Mode to determine if we need separators
            import_mode = self.import_mode_var.get() if hasattr(self, 'import_mode_var') else 'template'

            # Normalize feature and prepare user values for pattern matching
            normalized_feature = feature.replace(' ', '_')
            user_values = {
                'prefix': prefix,
                'feature': normalized_feature
            }

            # Get destination folder
            if not self.selected_dest_id:
                messagebox.showwarning("Warning", "Please select a destination folder")
                return
            dest_folder_name = self.dest_var.get()
            dest_folder_id = self.selected_dest_id

            # Get bank
            if not self.selected_bank_id:
                messagebox.showwarning("Warning", "Please select a bank")
                return
            bank_name = self.bank_var.get()

            # Get bus (auto-populate master if not selected)
            if not self.selected_bus_id:
                self._set_master_bus_as_default()
                if not self.selected_bus_id:  # Still no bus? Error!
                    messagebox.showerror("Error", "No buses found in project")
                    return
            bus = self.bus_var.get()

            # Clear existing preview and orphan lists
            for item in self.preview_tree.get_children():
                self.preview_tree.delete(item)
            self.orphan_events_list.delete(0, tk.END)
            self.orphan_media_list.delete(0, tk.END)

            # Get template folder (OPTIONAL)
            template_events = []
            
            if import_mode == 'template':
                if self.selected_template_id:
                    # Load events from template folder
                    template_events = self.project.get_events_in_folder(self.selected_template_id)
                    # Note: empty template folder is OK - just means all events will be auto-created
            else:
                # Pattern mode: Ignore template folder
                template_events = []

            # Collect audio files
            recursive = self.recursive_var.get() if hasattr(self, 'recursive_var') else False
            audio_files = AudioMatcher.collect_audio_files(media_path, recursive=recursive)

            if not audio_files:
                messagebox.showinfo("Info", "No audio files found in the selected directory")
                return

            # Build expected events mapping
            # With the generic approach, we pass template names directly to the matcher
            # The matcher will use suffix matching: template.endswith(file_action)
            # This works for any action name without hardcoding

            # Normalize feature name for event creation (replace spaces with underscores)
            normalized_feature = feature.replace(' ', '_')

            # Map template names to their event data
            # Format template placeholder names with user values for matching
            # e.g., "PrefixFeatureNameAlert" -> "MechafloraStrongRepairAlert"
            expected_events = {}
            for template_event in template_events:
                placeholder_name = template_event['name']
                # Format template name with user values for matching
                formatted_name = format_template_name(placeholder_name, prefix, normalized_feature)
                # Store with formatted name as key, keep original placeholder for import
                template_event_copy = dict(template_event)
                template_event_copy['original_placeholder'] = placeholder_name
                expected_events[formatted_name] = template_event_copy

            # Get asset pattern (optional - for parsing files with different separators)
            # Handle different placeholders based on mode
            asset_placeholder = "(Optional)" if import_mode == 'template' else "e.g. $prefix_$feature_$action"
            asset_pattern_str = self._get_entry_value(self.asset_pattern_entry, asset_placeholder)

            # Validate Asset Pattern in Pattern Mode
            if import_mode == 'pattern' and not asset_pattern_str:
                messagebox.showerror("Missing Information", "In 'Generate from Pattern' mode, the Asset Name Pattern is mandatory.\n\nPlease specify how your audio files are named (e.g. $prefix_$feature_$action).")
                return

            # Determine patterns based on mode and availability
            if import_mode == 'pattern':
                # Mode: Generate from Pattern (NO separators)
                # Asset Pattern is Source (Parsing)
                parse_pattern = NamingPattern(asset_pattern_str, separator=None)

                # Event Pattern is Destination (Building)
                # If Event Pattern is empty, inherit from Asset Pattern
                if not pattern_str:
                    pattern = NamingPattern(asset_pattern_str, separator=None)
                else:
                    pattern = NamingPattern(pattern_str, separator=None)

            else:
                # Mode: Match Template (WITH separators)
                # Get separators from UI
                event_separator = self.event_separator_entry.get() if hasattr(self, 'event_separator_entry') else None
                asset_separator = self.asset_separator_entry.get() if hasattr(self, 'asset_separator_entry') else None

                # Event Pattern is Source (and usually Destination)
                pattern = NamingPattern(pattern_str, separator=event_separator)

                # Asset Pattern is optional override for parsing
                if asset_pattern_str:
                    # Use asset separator if provided, otherwise use event separator
                    if asset_separator and asset_separator != event_separator:
                        parse_pattern = NamingPattern(asset_pattern_str, separator=asset_separator)
                    else:
                        # Use event separator for consistency
                        parse_pattern = NamingPattern(asset_pattern_str, separator=event_separator)
                else:
                    parse_pattern = pattern

            # Validate generated patterns
            valid, error = parse_pattern.validate()
            if not valid:
                messagebox.showerror("Invalid Asset Pattern", f"The asset/parse pattern is invalid:\n{error}")
                return
                
            valid, error = pattern.validate()
            if not valid:
                messagebox.showerror("Invalid Event Pattern", f"The event/build pattern is invalid:\n{error}")
                return

            # Match audio files to events using the naming patterns
            # parse_pattern: used to extract components from asset filenames
            # pattern: used to build event names
            matches, unmatched_files = AudioMatcher.match_files_with_pattern(
                audio_files, parse_pattern, pattern, user_values, expected_events
            )

            # Track which events and media were matched
            matched_events = set()
            matched_templates = set()  # Track which template names were used
            assigned_media = set()
            auto_created_count = 0

            # Sort matches by event name (A-Z) for consistent display
            sorted_matches = sorted(matches.items(), key=lambda x: x[0])

            # Check if auto-create is enabled
            auto_create_enabled = self.auto_create_var.get()

            # Populate preview tree
            for event_name, match_data in sorted_matches:
                files = match_data['files']
                confidence = match_data.get('confidence', 0.8)
                from_template = match_data.get('from_template', False)

                # Skip auto-created events if auto-create is disabled
                if not from_template and not auto_create_enabled:
                    # Add these files to unmatched for display in orphan media
                    unmatched_files.extend(files)
                    continue

                # Sort audio files by filename (A-Z)
                sorted_files = sorted(files, key=lambda x: x['filename'])

                # Get matched template (if any) - this is the FORMATTED name after our fix
                matched_template_formatted = match_data.get('matched_template', '')

                # Get the original placeholder name for import (FMOD needs the original name)
                original_placeholder = ''
                if matched_template_formatted and matched_template_formatted in expected_events:
                    original_placeholder = expected_events[matched_template_formatted].get('original_placeholder', matched_template_formatted)

                # Format display based on whether it matches a template
                if from_template:
                    matched_events.add(event_name)
                    # Track which template was matched (use formatted name for orphan tracking)
                    if matched_template_formatted:
                        matched_templates.add(matched_template_formatted)
                    # Format confidence indicator
                    if confidence >= 0.95:
                        confidence_icon = "✓"  # High confidence
                    elif confidence >= 0.85:
                        confidence_icon = "~"  # Good confidence
                    elif confidence >= 0.7:
                        confidence_icon = "?"  # Uncertain match
                    else:
                        confidence_icon = ""
                    event_display = f"{confidence_icon} {event_name}" if confidence_icon else event_name
                else:
                    # Auto-created event (no template match)
                    event_display = f"+ {event_name}"
                    auto_created_count += 1

                # Insert parent item (event) - store ORIGINAL placeholder for import phase
                # Import needs the original FMOD template name, not the formatted one
                # values = (checkbox, bank, bus, original_placeholder)
                parent = self.preview_tree.insert('', 'end', text=event_display,
                                                   values=('☑', bank_name, bus, original_placeholder))

                # Auto-check all events by default
                self.preview_checked_items.add(parent)

                # Insert child items (audio files)
                # values = (audio_path, '', '', '') - reuse checkbox column for audio path storage
                for file_info in sorted_files:
                    self.preview_tree.insert(parent, 'end', text=f"  -> {file_info['filename']}",
                                             values=('', '', '', ''))
                    assigned_media.add(file_info['filename'])

            # Update checkbox display for all events
            self._update_preview_tree_checkboxes()

            # Find orphan events (template events without matching media) - sorted A-Z
            # Use matched_templates (template names) instead of matched_events (constructed names)
            orphan_events = [name for name in expected_events.keys() if name not in matched_templates]
            orphan_events.sort()
            for expected_name in orphan_events:
                self.orphan_events_list.insert(tk.END, expected_name)

            # Add unmatched files to orphan media list (sorted A-Z)
            orphan_media = sorted([f['filename'] for f in unmatched_files])
            for media_file in orphan_media:
                self.orphan_media_list.insert(tk.END, media_file)

            orphan_media_count = self.orphan_media_list.size()
            orphan_events_count = self.orphan_events_list.size()
            matched_count = len(matched_events)

            # Build success message
            success_msg = f"Analysis complete!\n\n"
            if len(expected_events) > 0:
                success_msg += f"Template events: {len(expected_events)}\n"
                success_msg += f"Matched events: {matched_count}\n"
                success_msg += f"Orphan events: {orphan_events_count}\n"
            if auto_created_count > 0:
                success_msg += f"Auto-created events: {auto_created_count}\n"
            success_msg += f"\nTotal events ready to import: {matched_count + auto_created_count}\n"
            success_msg += f"(Click checkboxes in preview to select which events to import)\n\n"
            success_msg += f"Audio files found: {len(audio_files)}\n"
            success_msg += f"Audio files assigned: {len(assigned_media)}\n"
            success_msg += f"Orphan media files: {orphan_media_count}\n\n"
            success_msg += f"Destination: {dest_folder_name}\n"
            success_msg += f"Bank: {bank_name}\n"
            success_msg += f"Bus: {bus}"

            messagebox.showinfo("Success", success_msg)

        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed:\n{str(e)}")
