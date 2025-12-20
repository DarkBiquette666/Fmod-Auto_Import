"""
GUI Utilities Mixin Module
Handles utility methods and context menus for FmodImporterGUI.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from pathlib import Path
from typing import List, Dict, Optional

from ..matcher import AudioMatcher
from ..naming import NamingPattern


class UtilsMixin:
    """
    Mixin class providing utility methods and context menus.

    These methods are mixed into FmodImporterGUI via multiple inheritance.
    All methods access shared state through 'self'.
    """

    def _clean_event_name(self, event_name: str) -> str:
        """Remove confidence indicators and auto-created marker from event name"""
        # Remove confidence icons (✓, ~, ?, +)
        for icon in ['✓ ', '~ ', '? ', '+ ']:
            if event_name.startswith(icon):
                return event_name[len(icon):]
        return event_name

    def _on_preview_tree_checkbox_click(self, event):
        """Handle checkbox clicks in preview tree"""
        # Determine which item and column was clicked
        item = self.preview_tree.identify_row(event.y)
        column = self.preview_tree.identify_column(event.x)

        if not item:
            return

        # Only handle clicks on the checkbox column (#1)
        if column != '#1':
            return

        # Only handle parent items (events), not children (audio files)
        if self.preview_tree.parent(item):
            return  # This is a child item

        # Toggle checkbox state
        if item in self.preview_checked_items:
            self.preview_checked_items.remove(item)
        else:
            self.preview_checked_items.add(item)

        # Update display
        self._update_preview_tree_checkboxes()

    def _update_preview_tree_checkboxes(self):
        """Update checkbox symbols in preview tree checkbox column"""
        for item in self.preview_tree.get_children():
            # Get current values
            values = list(self.preview_tree.item(item, 'values'))

            # Update checkbox column (first column in values)
            if item in self.preview_checked_items:
                values[0] = '☑'
            else:
                values[0] = '☐'

            # Update the item with new values
            self.preview_tree.item(item, values=values)

    def _init_media_lookup(self, audio_files: List[Dict]):
        """Create lookup from filename to available file paths"""
        self.media_lookup = {}
        for info in audio_files:
            self.media_lookup.setdefault(info['filename'], []).append(info['path'])

    def _consume_media_path(self, filename: str, expected_path: Optional[str] = None) -> Optional[str]:
        """Return and remove a media path associated with the filename"""
        paths = self.media_lookup.get(filename)
        if not paths:
            return expected_path

        if expected_path and expected_path in paths:
            paths.remove(expected_path)
            path = expected_path
        else:
            path = paths.pop(0)

        if not paths:
            self.media_lookup.pop(filename, None)

        return path

    def _show_orphan_media_context_menu(self, event):
        """Show context menu for orphan media files"""
        # Get selected media files
        selected_indices = self.orphan_media_list.curselection()
        if not selected_indices:
            return

        # Clear previous menu items
        self.orphan_media_menu.delete(0, tk.END)

        # Add "Create Event from Selection" option at the top
        self.orphan_media_menu.add_command(
            label="Create Event from Selection",
            command=self._create_event_from_selection
        )
        self.orphan_media_menu.add_separator()

        # Get all orphan events and sort them A-Z
        orphan_events = []
        for i in range(self.orphan_events_list.size()):
            orphan_events.append(self.orphan_events_list.get(i))
        orphan_events.sort()

        if not orphan_events:
            self.orphan_media_menu.add_command(label="(No orphan events available)", state=tk.DISABLED)
        else:
            self.orphan_media_menu.add_command(label="Assign to event:", state=tk.DISABLED)
            self.orphan_media_menu.add_separator()

            # Add menu item for each orphan event (sorted A-Z)
            for orphan_event in orphan_events:
                self.orphan_media_menu.add_command(
                    label=orphan_event,
                    command=lambda e=orphan_event: self._assign_media_to_event(e)
                )

        # Show menu at cursor position
        try:
            self.orphan_media_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.orphan_media_menu.grab_release()

    def _assign_media_to_event(self, event_name: str):
        """Assign selected orphan media files to an orphan event"""
        # Get selected media files
        selected_indices = list(self.orphan_media_list.curselection())
        if not selected_indices:
            return

        # Get the media filenames
        selected_media = []
        for idx in selected_indices:
            media_filename = self.orphan_media_list.get(idx)
            selected_media.append(media_filename)

        # Get bank and bus from current selection
        bank_name = self.bank_var.get()
        bus_name = self.bus_var.get()

        # Check if event already exists in preview tree
        event_item = None
        for item in self.preview_tree.get_children():
            item_text = self.preview_tree.item(item, 'text')
            if self._clean_event_name(item_text) == event_name:
                event_item = item
                break

        # If event doesn't exist in tree, create it
        if event_item is None:
            event_item = self.preview_tree.insert('', 'end', text=event_name,
                                                   values=(bank_name, bus_name))

        # Add media files as children of the event
        for media_filename in selected_media:
            self.preview_tree.insert(event_item, 'end', text=f"  → {media_filename}",
                                     values=('', ''))

        # Remove from orphan media list (in reverse order to maintain indices)
        for idx in reversed(selected_indices):
            self.orphan_media_list.delete(idx)

        # Check if event should be removed from orphan events list
        # Remove it if it now has at least one media file assigned
        event_has_children = len(self.preview_tree.get_children(event_item)) > 0
        if event_has_children:
            # Remove event from orphan events list
            for i in range(self.orphan_events_list.size()):
                if self.orphan_events_list.get(i) == event_name:
                    self.orphan_events_list.delete(i)
                    break

    def _create_event_from_selection(self):
        """Create a new event from selected orphan media files"""
        # Get selected media files
        selected_indices = list(self.orphan_media_list.curselection())
        if not selected_indices:
            return

        # Get the media filenames
        selected_media = []
        for idx in selected_indices:
            media_filename = self.orphan_media_list.get(idx)
            selected_media.append(media_filename)

        # Get prefix and feature to generate event name
        prefix = self._get_entry_value(self.prefix_entry, 'e.g. Mechaflora')
        feature = self._get_entry_value(self.feature_entry, 'e.g. FeatureName, Feature_Name, feature_name, ...')

        if not prefix or not feature:
            messagebox.showwarning("Warning", "Please fill in Prefix and Feature Name first")
            return

        # Get pattern configuration for event name building
        pattern_str = self.pattern_var.get()
        event_separator = self.event_separator_entry.get() if hasattr(self, 'event_separator_entry') else None
        pattern = NamingPattern(pattern_str, separator=event_separator)

        # Validate pattern
        valid, error = pattern.validate()
        if not valid:
            messagebox.showwarning("Warning", f"Invalid naming pattern:\n{error}")
            return

        # Get asset pattern (optional - for parsing files with different separators)
        asset_pattern_str = self._get_entry_value(self.asset_pattern_entry, "(Optional)")
        asset_separator = self.asset_separator_entry.get() if hasattr(self, 'asset_separator_entry') else None

        parse_pattern = pattern  # Default: use same pattern and separator for parsing
        if asset_pattern_str:
            # User provided a different pattern for parsing assets
            parse_pattern = NamingPattern(asset_pattern_str, separator=asset_separator)
            valid, error = parse_pattern.validate()
            if not valid:
                messagebox.showwarning("Warning", f"Invalid asset pattern:\n{error}")
                return
        elif asset_separator and asset_separator != event_separator:
            # Only asset separator provided (different from event separator)
            # Use event pattern with asset separator
            parse_pattern = NamingPattern(pattern_str, separator=asset_separator)

        # Normalize feature for matching
        normalized_feature = feature.replace(' ', '_')
        user_values = {
            'prefix': prefix,
            'feature': normalized_feature
        }

        # Parse all selected files and group by action
        action_groups = {}  # {action: [file1, file2, ...]}
        failed_files = []

        for media_file in selected_media:
            basename = Path(media_file).stem

            # Parse the asset to extract the action
            parsed = parse_pattern.parse_asset_fuzzy(basename, user_values)

            if parsed and 'action' in parsed:
                action = parsed['action']
                if action not in action_groups:
                    action_groups[action] = []
                action_groups[action].append(media_file)
            else:
                # File doesn't match pattern
                failed_files.append(media_file)

        # Show warning if some files failed to parse
        if failed_files:
            expected_format = parse_pattern.get_pattern_preview(user_values)
            messagebox.showwarning("Warning",
                f"{len(failed_files)} file(s) could not be parsed:\n" +
                "\n".join(failed_files[:5]) +
                (f"\n... and {len(failed_files) - 5} more" if len(failed_files) > 5 else "") +
                f"\n\nExpected format: {expected_format}")

        # If no files could be parsed, return
        if not action_groups:
            return

        # Get bank and bus from current selection
        bank_name = self.bank_var.get()
        bus_name = self.bus_var.get()

        # Create one event per action group
        events_created = 0
        total_files_assigned = 0

        for action, files in action_groups.items():
            # Build event name using the naming pattern
            event_name = pattern.build(prefix=prefix, feature=normalized_feature, action=action)

            # Check if event already exists in preview tree
            event_item = None
            for item in self.preview_tree.get_children():
                item_text = self.preview_tree.item(item, 'text')
                if self._clean_event_name(item_text) == event_name:
                    event_item = item
                    break

            # If event doesn't exist in tree, create it with auto-created indicator
            if event_item is None:
                event_item = self.preview_tree.insert('', 'end', text=f"+ {event_name}",
                                                       values=(bank_name, bus_name))
                events_created += 1

            # Add media files as children of the event (sorted)
            sorted_files = sorted(files)
            for media_filename in sorted_files:
                self.preview_tree.insert(event_item, 'end', text=f"  → {media_filename}",
                                         values=('', ''))
            total_files_assigned += len(files)

        # Remove from orphan media list (in reverse order to maintain indices)
        for idx in reversed(selected_indices):
            self.orphan_media_list.delete(idx)

        # Success message
        if events_created == 1:
            messagebox.showinfo("Success",
                f"Created 1 event\n"
                f"Assigned {total_files_assigned} file(s)")
        else:
            messagebox.showinfo("Success",
                f"Created {events_created} events\n"
                f"Assigned {total_files_assigned} file(s)")

    def _show_preview_tree_context_menu(self, event):
        """Show context menu for preview tree"""
        # Identify the item under the cursor
        item = self.preview_tree.identify_row(event.y)
        if not item:
            return

        # Preserve selection if item is already selected (for multi-select operations)
        # Otherwise, replace selection with this item (standard Windows behavior)
        current_selection = self.preview_tree.selection()
        if item not in current_selection:
            self.preview_tree.selection_set(item)

        # Check if it's a parent (event) or child (media file)
        parent = self.preview_tree.parent(item)
        is_event = not parent  # If no parent, it's a top-level event

        # Clear previous menu items
        self.preview_tree_menu.delete(0, tk.END)

        if is_event:
            # Context menu for events
            event_text = self.preview_tree.item(item, 'text')

            # Check if it's an auto-created event (starts with '+')
            if event_text.startswith('+ '):
                self.preview_tree_menu.add_command(
                    label="Rename Event (Auto-created)",
                    command=lambda: self._rename_event(item)
                )
            else:
                self.preview_tree_menu.add_command(
                    label="Cannot rename template events",
                    state=tk.DISABLED
                )
                self.preview_tree_menu.add_command(
                    label="(Template events must match FMOD project)",
                    state=tk.DISABLED
                )
        else:
            # Context menu for media files
            self.preview_tree_menu.add_command(
                label="Remove Media File",
                command=lambda: self._remove_media_from_event(item)
            )

        # Show menu at cursor position
        try:
            self.preview_tree_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.preview_tree_menu.grab_release()

    def _on_preview_tree_double_click(self, event):
        """Handle double-click on preview tree items"""
        # Identify the item under the cursor
        item = self.preview_tree.identify_row(event.y)
        if not item:
            return

        # Check if it's a parent (event) or child (media file)
        parent = self.preview_tree.parent(item)
        is_event = not parent

        if is_event:
            event_text = self.preview_tree.item(item, 'text')
            # Only allow renaming auto-created events
            if event_text.startswith('+ '):
                self._rename_event(item)

    def _on_preview_tree_f2(self, event):
        """Handle F2 key press on preview tree items"""
        # Get currently selected item
        selected = self.preview_tree.selection()
        if not selected:
            return

        item = selected[0]

        # Check if it's a parent (event) or child (media file)
        parent = self.preview_tree.parent(item)
        is_event = not parent

        if is_event:
            event_text = self.preview_tree.item(item, 'text')
            # Only allow renaming auto-created events
            if event_text.startswith('+ '):
                self._rename_event(item)
            else:
                messagebox.showinfo(
                    "Cannot Rename",
                    "Only auto-created events (marked with '+') can be renamed.\n\n"
                    "Template events must match the FMOD project structure."
                )

    def _rename_event(self, item):
        """Rename an event in the preview tree"""
        # Get current event name
        current_text = self.preview_tree.item(item, 'text')
        current_name = self._clean_event_name(current_text)

        # Ask user for new name
        new_name = simpledialog.askstring(
            "Rename Event",
            f"Enter new name for event:\n(Current: {current_name})",
            initialvalue=current_name,
            parent=self.root
        )

        if not new_name or new_name == current_name:
            return

        # Validate the new name
        new_name = new_name.strip()
        if not new_name:
            messagebox.showwarning("Warning", "Event name cannot be empty")
            return

        # Check if name already exists
        for tree_item in self.preview_tree.get_children():
            if tree_item != item:
                existing_text = self.preview_tree.item(tree_item, 'text')
                existing_name = self._clean_event_name(existing_text)
                if existing_name == new_name:
                    messagebox.showwarning("Warning", f"An event named '{new_name}' already exists")
                    return

        # Update the item with new name (keep the '+' indicator)
        self.preview_tree.item(item, text=f"+ {new_name}")
        messagebox.showinfo("Success", f"Event renamed to: {new_name}")

    def _remove_media_from_event(self, item):
        """Remove a media file from an event"""
        # Get parent event
        parent = self.preview_tree.parent(item)
        if not parent:
            return

        # Get media filename
        media_text = self.preview_tree.item(item, 'text')
        media_filename = media_text.replace('  → ', '').strip()

        # Remove from tree
        self.preview_tree.delete(item)

        # Add back to orphan media list (sorted)
        orphan_media = list(self.orphan_media_list.get(0, tk.END))
        orphan_media.append(media_filename)
        orphan_media.sort()

        self.orphan_media_list.delete(0, tk.END)
        for media_file in orphan_media:
            self.orphan_media_list.insert(tk.END, media_file)

        # Check if parent event now has no media files
        event_name_raw = self.preview_tree.item(parent, 'text')
        event_name = self._clean_event_name(event_name_raw)
        children = self.preview_tree.get_children(parent)

        if len(children) == 0:
            # Event has no media, remove from preview tree
            self.preview_tree.delete(parent)

            # Add back to orphan events (only if not auto-created)
            if not event_name_raw.startswith('+ '):
                orphan_events = list(self.orphan_events_list.get(0, tk.END))
                if event_name not in orphan_events:
                    orphan_events.append(event_name)
                    orphan_events.sort()
                    self.orphan_events_list.delete(0, tk.END)
                    for event in orphan_events:
                        self.orphan_events_list.insert(tk.END, event)


class ProgressDialog:
    """
    Modal progress dialog with indeterminate progress bar.

    Displays an animated progress bar while a long-running operation
    executes in a background thread. Prevents UI freeze by keeping
    the dialog responsive.

    Thread Safety:
        - Call update_message() only from the main tkinter thread
        - Use root.after(0, callback) when updating from background threads

    Example:
        >>> progress = ProgressDialog(root, "Processing", "Please wait...")
        >>> # ... do work in background thread ...
        >>> progress.update_message("Almost done...")
        >>> progress.close()
    """

    def __init__(self, parent, title: str, message: str):
        """
        Create and display a modal progress dialog.

        Args:
            parent: Parent tkinter window
            title: Dialog window title
            message: Initial status message to display
        """
        from tkinter import ttk

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Prevent window close button (user must wait for operation to complete)
        self.dialog.protocol("WM_DELETE_WINDOW", lambda: None)

        # Configure dialog layout
        self.dialog.resizable(False, False)

        # Message label
        self.message_label = tk.Label(
            self.dialog,
            text=message,
            wraplength=350,
            justify=tk.LEFT,
            padx=20,
            pady=20
        )
        self.message_label.pack()

        # Indeterminate progress bar (animated pulse mode)
        self.progress = ttk.Progressbar(
            self.dialog,
            mode='indeterminate',
            length=350
        )
        self.progress.pack(padx=20, pady=(0, 20))
        self.progress.start(10)  # Animation speed (ms)

        # Center dialog relative to parent window
        self._center_on_parent(parent)

        # Force dialog to appear and update
        self.dialog.update_idletasks()

    def _center_on_parent(self, parent):
        """
        Center dialog relative to parent window.

        Args:
            parent: Parent tkinter window
        """
        self.dialog.update_idletasks()

        # Get parent position and size
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # Get dialog size
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()

        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        # Ensure dialog stays on screen (minimum 0)
        x = max(0, x)
        y = max(0, y)

        self.dialog.geometry(f"+{x}+{y}")

    def update_message(self, message: str):
        """
        Update the status message displayed in the dialog.

        IMPORTANT: Must be called from the main tkinter thread only.
        When calling from a background thread, use:
            root.after(0, lambda: progress.update_message("New message"))

        Args:
            message: New status message to display
        """
        self.message_label.config(text=message)
        self.dialog.update_idletasks()

    def close(self):
        """
        Close and destroy the progress dialog.

        Stops the progress bar animation and destroys the dialog window.
        Safe to call multiple times.
        """
        try:
            self.progress.stop()
            self.dialog.destroy()
        except:
            # Dialog may already be destroyed
            pass
