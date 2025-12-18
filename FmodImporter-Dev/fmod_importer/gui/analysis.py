"""
GUI Analysis Mixin Module
Handles the analysis workflow for matching audio files to events.
"""

import os
import tkinter as tk
from tkinter import messagebox

from ..naming import NamingPattern
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

            # Get and validate naming pattern
            pattern_str = self.pattern_var.get()
            pattern = NamingPattern(pattern_str)
            valid, error = pattern.validate()
            if not valid:
                messagebox.showerror("Invalid Pattern", f"The naming pattern is invalid:\n{error}")
                return

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

            # Get bus
            if not self.selected_bus_id:
                messagebox.showwarning("Warning", "Please select a bus")
                return
            bus = self.bus_var.get()

            # Clear existing preview and orphan lists
            for item in self.preview_tree.get_children():
                self.preview_tree.delete(item)
            self.orphan_events_list.delete(0, tk.END)
            self.orphan_media_list.delete(0, tk.END)

            # Get template folder
            if not self.selected_template_id:
                messagebox.showwarning("Warning", "Please select a template folder")
                return

            # Load events from template folder
            template_events = self.project.get_events_in_folder(self.selected_template_id)

            if not template_events:
                messagebox.showwarning("Warning", "No events found in template folder")
                return

            # Collect audio files
            audio_files = AudioMatcher.collect_audio_files(media_path)

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
            # The matcher will handle matching by normalized suffix
            expected_events = {}
            for template_event in template_events:
                template_name = template_event['name']
                expected_events[template_name] = template_event

            # Get asset pattern (optional - for parsing files with different separators)
            asset_pattern_str = self._get_entry_value(self.asset_pattern_entry, "(Optional - leave empty to use Event Pattern)")
            parse_pattern = pattern  # Default: use same pattern for parsing
            if asset_pattern_str:
                # User provided a different pattern for parsing assets
                parse_pattern = NamingPattern(asset_pattern_str)
                valid, error = parse_pattern.validate()
                if not valid:
                    messagebox.showerror("Invalid Asset Pattern", f"The asset pattern is invalid:\n{error}")
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

            # Populate preview tree
            for event_name, match_data in sorted_matches:
                files = match_data['files']
                confidence = match_data.get('confidence', 0.8)
                from_template = match_data.get('from_template', False)

                # Sort audio files by filename (A-Z)
                sorted_files = sorted(files, key=lambda x: x['filename'])

                # Format display based on whether it matches a template
                if from_template:
                    matched_events.add(event_name)
                    # Track which template was matched
                    matched_template = match_data.get('matched_template')
                    if matched_template:
                        matched_templates.add(matched_template)
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

                # Insert parent item (event)
                parent = self.preview_tree.insert('', 'end', text=event_display,
                                                   values=(bank_name, bus))

                # Insert child items (audio files)
                for file_info in sorted_files:
                    self.preview_tree.insert(parent, 'end', text=f"  -> {file_info['filename']}",
                                             values=('', ''))
                    assigned_media.add(file_info['filename'])

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
            success_msg += f"Template events: {len(expected_events)}\n"
            success_msg += f"Matched events: {matched_count}\n"
            success_msg += f"Orphan events: {orphan_events_count}\n"
            if auto_created_count > 0:
                success_msg += f"Auto-created events: {auto_created_count}\n"
            success_msg += f"\nAudio files found: {len(audio_files)}\n"
            success_msg += f"Audio files assigned: {len(assigned_media)}\n"
            success_msg += f"Orphan media files: {orphan_media_count}\n\n"
            success_msg += f"Destination: {dest_folder_name}\n"
            success_msg += f"Bank: {bank_name}\n"
            success_msg += f"Bus: {bus}"

            messagebox.showinfo("Success", success_msg)

        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed:\n{str(e)}")
