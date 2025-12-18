"""
GUI Drag & Drop Mixin Module
Handles drag and drop functionality between widgets.
"""

import tkinter as tk


class DragDropMixin:
    """
    Mixin class providing drag and drop functionality.

    These methods are mixed into FmodImporterGUI via multiple inheritance.
    All methods access shared state through 'self'.
    """

    def _set_drop_target(self, target):
        """Set the current drop target"""
        if self._drag_data['dragging']:
            self._drag_data['drop_target'] = target

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling for Listbox widgets"""
        # Get the widget that triggered the event
        widget = event.widget

        # Determine scroll direction and amount
        if event.num == 5 or event.delta < 0:
            # Scroll down
            widget.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            # Scroll up
            widget.yview_scroll(-1, "units")

        return "break"

    def _on_listbox_up(self, event):
        """Handle Up arrow key navigation"""
        current = self.orphan_media_list.curselection()
        if not current:
            # Select first item
            if self.orphan_media_list.size() > 0:
                self.orphan_media_list.selection_set(0)
                self.orphan_media_list.see(0)
        else:
            current_idx = current[0]
            if current_idx > 0:
                self.orphan_media_list.selection_clear(0, tk.END)
                self.orphan_media_list.selection_set(current_idx - 1)
                self.orphan_media_list.see(current_idx - 1)
        return "break"

    def _on_listbox_down(self, event):
        """Handle Down arrow key navigation"""
        current = self.orphan_media_list.curselection()
        size = self.orphan_media_list.size()
        if not current:
            # Select first item
            if size > 0:
                self.orphan_media_list.selection_set(0)
                self.orphan_media_list.see(0)
        else:
            current_idx = current[0]
            if current_idx < size - 1:
                self.orphan_media_list.selection_clear(0, tk.END)
                self.orphan_media_list.selection_set(current_idx + 1)
                self.orphan_media_list.see(current_idx + 1)
        return "break"

    def _on_listbox_select_all(self, event):
        """Handle Ctrl+A to select all"""
        self.orphan_media_list.selection_set(0, tk.END)
        return "break"

    def _on_listbox_press(self, event):
        """Handle initial press on listbox - store position and selection"""
        # Store initial position
        self._drag_data['start_x'] = event.x
        self._drag_data['start_y'] = event.y
        self._drag_data['dragging'] = False
        self._drag_data['click_index'] = None

        # Get the index under cursor
        index = self.orphan_media_list.nearest(event.y)

        # Handle selection manually to prevent drag-select behavior
        # Check if item is already selected
        if index in self.orphan_media_list.curselection():
            # Already selected
            # Check for modifiers
            if event.state & 0x4:  # Ctrl key - deselect immediately
                self.orphan_media_list.selection_clear(index)
            elif event.state & 0x1:  # Shift key - do nothing, wait for release
                pass
            else:
                # Normal click - store index to potentially deselect others on release
                # This allows drag of multiple items but also single-click to deselect others
                self._drag_data['click_index'] = index
            return "break"
        else:
            # Not selected, select it
            # Check for Ctrl or Shift modifiers
            if event.state & 0x4:  # Ctrl key
                # Toggle selection (add to selection)
                self.orphan_media_list.selection_set(index)
            elif event.state & 0x1:  # Shift key
                # Range selection from last selected to current
                current = self.orphan_media_list.curselection()
                if current:
                    start = current[0]
                    end = index
                    if start > end:
                        start, end = end, start
                    self.orphan_media_list.selection_clear(0, tk.END)
                    for i in range(start, end + 1):
                        self.orphan_media_list.selection_set(i)
                else:
                    self.orphan_media_list.selection_set(index)
            else:
                # Normal click - clear and select
                self.orphan_media_list.selection_clear(0, tk.END)
                self.orphan_media_list.selection_set(index)

            return "break"

    def _on_drag_motion(self, event):
        """Handle drag motion - start drag if moved beyond threshold"""
        if self._drag_data['dragging']:
            # Already dragging, update label position
            root_x = self.root.winfo_rootx()
            root_y = self.root.winfo_rooty()
            x = event.x_root - root_x + 10
            y = event.y_root - root_y + 10
            self._drag_label.place(x=x, y=y)

            # Update drop target highlight
            self._update_drop_target_highlight(event.x_root, event.y_root)

            return "break"

        # Check if moved beyond threshold
        dx = abs(event.x - self._drag_data['start_x'])
        dy = abs(event.y - self._drag_data['start_y'])

        if dx > self._drag_threshold or dy > self._drag_threshold:
            # Start dragging
            selected_indices = self.orphan_media_list.curselection()
            if not selected_indices:
                return "break"

            # Store selected media files
            self._drag_data['items'] = [self.orphan_media_list.get(idx) for idx in selected_indices]
            self._drag_data['indices'] = list(selected_indices)
            self._drag_data['dragging'] = True
            self._drag_data['source_widget'] = 'orphan_media'

            # Show drag feedback label
            count = len(self._drag_data['items'])
            if count == 1:
                label_text = f"  {self._drag_data['items'][0]}"
            else:
                label_text = f"  {count} files"
            self._drag_label.config(text=label_text)

            # Position label near cursor (convert screen coords to root widget coords)
            root_x = self.root.winfo_rootx()
            root_y = self.root.winfo_rooty()
            x = event.x_root - root_x + 10
            y = event.y_root - root_y + 10
            self._drag_label.place(x=x, y=y)

            # Change cursor to indicate dragging
            self.orphan_media_list.config(cursor='hand2')

            # Highlight selected items with a different background
            for idx in selected_indices:
                self.orphan_media_list.itemconfig(idx, bg='lightblue')

        # Prevent default drag-select behavior
        return "break"

    def _on_preview_tree_press(self, event):
        """Handle initial press on preview tree"""
        # Store initial position
        self._drag_data['start_x'] = event.x
        self._drag_data['start_y'] = event.y
        self._drag_data['dragging'] = False

        # Let default selection happen
        return

    def _on_preview_tree_drag(self, event):
        """Handle drag from preview tree - only media files can be dragged"""
        if self._drag_data['dragging']:
            # Already dragging, update label position
            root_x = self.root.winfo_rootx()
            root_y = self.root.winfo_rooty()
            x = event.x_root - root_x + 10
            y = event.y_root - root_y + 10
            self._drag_label.place(x=x, y=y)

            # Update drop target highlight
            self._update_drop_target_highlight(event.x_root, event.y_root)
            return

        # Check if moved beyond threshold
        dx = abs(event.x - self._drag_data['start_x'])
        dy = abs(event.y - self._drag_data['start_y'])

        if dx > self._drag_threshold or dy > self._drag_threshold:
            # Get selected item
            selected = self.preview_tree.selection()
            if not selected:
                return

            # Only allow dragging media files (child items starting with "  -> ")
            media_items = []
            media_files = []
            for item in selected:
                text = self.preview_tree.item(item, 'text')
                if text.startswith('  -> '):
                    media_items.append(item)
                    # Extract filename (remove "  -> " prefix)
                    filename = text[4:]
                    media_files.append(filename)

            if not media_files:
                # No media files selected, don't start drag
                return

            # Store media files for dragging
            self._drag_data['items'] = media_files
            self._drag_data['tree_items'] = media_items  # Store tree items for deletion
            self._drag_data['dragging'] = True
            self._drag_data['source_widget'] = 'preview_tree'

            # Show drag feedback label
            count = len(media_files)
            if count == 1:
                label_text = f"  {media_files[0]}"
            else:
                label_text = f"  {count} files"
            self._drag_label.config(text=label_text)

            # Position label near cursor (convert screen coords to root widget coords)
            root_x = self.root.winfo_rootx()
            root_y = self.root.winfo_rooty()
            x = event.x_root - root_x + 10
            y = event.y_root - root_y + 10
            self._drag_label.place(x=x, y=y)

            # Change cursor
            self.preview_tree.config(cursor='hand2')

    def _on_preview_tree_release(self, event):
        """Handle release from preview tree drag"""
        if not self._drag_data['dragging'] or self._drag_data['source_widget'] != 'preview_tree':
            return

        # Restore cursor
        self.preview_tree.config(cursor='')

        # Check if dropped over orphan media list
        x_root = event.x_root
        y_root = event.y_root

        try:
            media_x = self.orphan_media_list.winfo_rootx()
            media_y = self.orphan_media_list.winfo_rooty()
            media_width = self.orphan_media_list.winfo_width()
            media_height = self.orphan_media_list.winfo_height()

            if (media_x <= x_root <= media_x + media_width and
                media_y <= y_root <= media_y + media_height):
                # Valid drop - move media files back to orphan list
                self._drop_preview_to_orphan()
                return
        except:
            pass

        # Not a valid drop, cancel
        self._clear_drag_data()

    def _drop_preview_to_orphan(self):
        """Move media files from preview tree back to orphan media list"""
        if not self._drag_data['items']:
            return

        # Add files to orphan media list
        for filename in self._drag_data['items']:
            self.orphan_media_list.insert(tk.END, filename)

        # Sort the orphan media list
        items = list(self.orphan_media_list.get(0, tk.END))
        items.sort()
        self.orphan_media_list.delete(0, tk.END)
        for item in items:
            self.orphan_media_list.insert(tk.END, item)

        # Remove from preview tree
        for tree_item in self._drag_data.get('tree_items', []):
            # Get parent event
            parent = self.preview_tree.parent(tree_item)
            # Delete the media item
            self.preview_tree.delete(tree_item)

            # Check if parent event now has no media files
            if parent:
                event_name_raw = self.preview_tree.item(parent, 'text')
                event_name = self._clean_event_name(event_name_raw)
                children = self.preview_tree.get_children(parent)
                if len(children) == 0:
                    # Event has no media, remove from preview tree
                    self.preview_tree.delete(parent)

                    # Add back to orphan events
                    orphan_events = list(self.orphan_events_list.get(0, tk.END))
                    if event_name not in orphan_events:
                        orphan_events.append(event_name)
                        orphan_events.sort()
                        self.orphan_events_list.delete(0, tk.END)
                        for event in orphan_events:
                            self.orphan_events_list.insert(tk.END, event)

        self._clear_drag_data()

    def _on_preview_tree_delete(self, event):
        """Handle Delete key press on preview tree - remove media files and move to orphan list"""
        selected = self.preview_tree.selection()
        if not selected:
            return

        # Filter to only media files (child items starting with "  -> ")
        media_items = []
        media_files = []
        for item in selected:
            text = self.preview_tree.item(item, 'text')
            if text.startswith('  -> '):
                media_items.append(item)
                # Extract filename (remove "  -> " prefix)
                filename = text[4:]
                media_files.append(filename)

        if not media_files:
            # No media files selected, nothing to delete
            return

        # Add files back to orphan media list
        for filename in media_files:
            self.orphan_media_list.insert(tk.END, filename)

        # Sort the orphan media list
        items = list(self.orphan_media_list.get(0, tk.END))
        items.sort()
        self.orphan_media_list.delete(0, tk.END)
        for item in items:
            self.orphan_media_list.insert(tk.END, item)

        # Track parent events that might become orphans
        parent_events = set()

        # Remove from preview tree
        for tree_item in media_items:
            # Get parent event before deleting
            parent = self.preview_tree.parent(tree_item)
            if parent:
                parent_events.add(parent)
            # Delete the media item
            self.preview_tree.delete(tree_item)

        # Check if any parent events now have no media files
        for parent in parent_events:
            event_name_raw = self.preview_tree.item(parent, 'text')
            event_name = self._clean_event_name(event_name_raw)
            children = self.preview_tree.get_children(parent)
            if len(children) == 0:
                # Event has no media, remove from preview tree
                self.preview_tree.delete(parent)

                # Add back to orphan events
                orphan_events = list(self.orphan_events_list.get(0, tk.END))
                if event_name not in orphan_events:
                    orphan_events.append(event_name)
                    orphan_events.sort()
                    self.orphan_events_list.delete(0, tk.END)
                    for event in orphan_events:
                        self.orphan_events_list.insert(tk.END, event)

        return "break"  # Prevent default behavior

    def _on_listbox_release(self, event):
        """Handle release - perform drop if dragging, otherwise allow normal selection"""
        if not self._drag_data['dragging']:
            # Not dragging - check if it was a simple click on already selected item
            if self._drag_data.get('click_index') is not None:
                # Simple click on selected item - deselect others and keep only this one
                index = self._drag_data['click_index']
                self.orphan_media_list.selection_clear(0, tk.END)
                self.orphan_media_list.selection_set(index)
                self._drag_data['click_index'] = None
            return

        # Restore cursor
        self.orphan_media_list.config(cursor='')

        # Determine drop location based on cursor position
        # Convert event coordinates to screen coordinates
        x_root = event.x_root
        y_root = event.y_root

        # Check if over preview tree
        try:
            preview_x = self.preview_tree.winfo_rootx()
            preview_y = self.preview_tree.winfo_rooty()
            preview_width = self.preview_tree.winfo_width()
            preview_height = self.preview_tree.winfo_height()

            if (preview_x <= x_root <= preview_x + preview_width and
                preview_y <= y_root <= preview_y + preview_height):
                # Drop on preview tree
                # Convert to widget-relative coordinates
                widget_y = y_root - preview_y
                self._drop_on_preview(widget_y)
                return
        except:
            pass

        # Check if over orphan events list
        try:
            orphan_x = self.orphan_events_list.winfo_rootx()
            orphan_y = self.orphan_events_list.winfo_rooty()
            orphan_width = self.orphan_events_list.winfo_width()
            orphan_height = self.orphan_events_list.winfo_height()

            if (orphan_x <= x_root <= orphan_x + orphan_width and
                orphan_y <= y_root <= orphan_y + orphan_height):
                # Drop on orphan events
                widget_y = y_root - orphan_y
                self._drop_on_orphan_event(widget_y)
                return
        except:
            pass

        # Not over a valid drop target, cancel drag
        self._clear_drag_data()

    def _drop_on_preview(self, widget_y):
        """Drop orphan media onto preview tree event"""
        if not self._drag_data['items']:
            return

        # Identify the item under the cursor
        item = self.preview_tree.identify_row(widget_y)
        if not item:
            self._clear_drag_data()
            return

        # Get the top-level parent (event item)
        parent = self.preview_tree.parent(item)
        event_item = item if not parent else parent

        # Get event name (clean from confidence indicators)
        event_name_raw = self.preview_tree.item(event_item, 'text')
        event_name = self._clean_event_name(event_name_raw)

        # Add media files to this event
        for media_filename in self._drag_data['items']:
            self.preview_tree.insert(event_item, 'end', text=f"  -> {media_filename}",
                                     values=('', ''))

        # Remove from orphan media list
        for idx in reversed(self._drag_data['indices']):
            self.orphan_media_list.delete(idx)

        # Check if event should be removed from orphan events list
        event_has_children = len(self.preview_tree.get_children(event_item)) > 0
        if event_has_children:
            for i in range(self.orphan_events_list.size()):
                if self.orphan_events_list.get(i) == event_name:
                    self.orphan_events_list.delete(i)
                    break

        self._clear_drag_data()

    def _drop_on_orphan_event(self, widget_y):
        """Drop orphan media onto orphan event"""
        if not self._drag_data['items']:
            return

        # Get the event under cursor
        index = self.orphan_events_list.nearest(widget_y)
        if index < 0:
            self._clear_drag_data()
            return

        event_name = self.orphan_events_list.get(index)

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

        # Add media files to this event
        for media_filename in self._drag_data['items']:
            self.preview_tree.insert(event_item, 'end', text=f"  -> {media_filename}",
                                     values=('', ''))

        # Remove from orphan media list
        for idx in reversed(self._drag_data['indices']):
            self.orphan_media_list.delete(idx)

        # Check if event should be removed from orphan events list
        event_has_children = len(self.preview_tree.get_children(event_item)) > 0
        if event_has_children:
            for i in range(self.orphan_events_list.size()):
                if self.orphan_events_list.get(i) == event_name:
                    self.orphan_events_list.delete(i)
                    break

        self._clear_drag_data()

    def _update_drop_target_highlight(self, x_root, y_root):
        """Highlight valid drop targets when hovering during drag"""
        # Clear previous highlights
        self._clear_drop_highlights()

        source = self._drag_data.get('source_widget')

        # If dragging from orphan_media, highlight preview tree and orphan events
        if source == 'orphan_media':
            # Check if over preview tree
            try:
                preview_x = self.preview_tree.winfo_rootx()
                preview_y = self.preview_tree.winfo_rooty()
                preview_width = self.preview_tree.winfo_width()
                preview_height = self.preview_tree.winfo_height()

                if (preview_x <= x_root <= preview_x + preview_width and
                    preview_y <= y_root <= preview_y + preview_height):
                    # Highlight the preview tree
                    widget_y = y_root - preview_y
                    item = self.preview_tree.identify_row(widget_y)
                    if item:
                        # Get the top-level parent (event item)
                        parent = self.preview_tree.parent(item)
                        event_item = item if not parent else parent
                        # Highlight this event
                        self.preview_tree.selection_set(event_item)
                        self._drag_highlight_items.append(('preview_tree', event_item))
                    return
            except:
                pass

            # Check if over orphan events list
            try:
                orphan_x = self.orphan_events_list.winfo_rootx()
                orphan_y = self.orphan_events_list.winfo_rooty()
                orphan_width = self.orphan_events_list.winfo_width()
                orphan_height = self.orphan_events_list.winfo_height()

                if (orphan_x <= x_root <= orphan_x + orphan_width and
                    orphan_y <= y_root <= orphan_y + orphan_height):
                    # Highlight the orphan events list
                    widget_y = y_root - orphan_y
                    index = self.orphan_events_list.nearest(widget_y)
                    if index >= 0 and index < self.orphan_events_list.size():
                        self.orphan_events_list.selection_clear(0, tk.END)
                        self.orphan_events_list.selection_set(index)
                        self._drag_highlight_items.append(('orphan_events', index))
                    return
            except:
                pass

        # If dragging from preview_tree, highlight orphan media list
        elif source == 'preview_tree':
            try:
                media_x = self.orphan_media_list.winfo_rootx()
                media_y = self.orphan_media_list.winfo_rooty()
                media_width = self.orphan_media_list.winfo_width()
                media_height = self.orphan_media_list.winfo_height()

                if (media_x <= x_root <= media_x + media_width and
                    media_y <= y_root <= media_y + media_height):
                    # Highlight the entire orphan media list
                    self.orphan_media_list.config(bg='lightyellow')
                    self._drag_highlight_items.append(('orphan_media_list', None))
                    return
            except:
                pass

    def _clear_drop_highlights(self):
        """Clear all drop target highlights"""
        for widget_type, item in self._drag_highlight_items:
            if widget_type == 'preview_tree':
                self.preview_tree.selection_remove(item)
            elif widget_type == 'orphan_events':
                self.orphan_events_list.selection_clear(item)
            elif widget_type == 'orphan_media_list':
                self.orphan_media_list.config(bg='white')
        self._drag_highlight_items = []

    def _clear_drag_data(self):
        """Clear drag data after drop or cancel"""
        # Hide drag label
        self._drag_label.place_forget()

        # Restore cursors based on source
        source = self._drag_data.get('source_widget')
        if source == 'orphan_media':
            self.orphan_media_list.config(cursor='')
        elif source == 'preview_tree':
            self.preview_tree.config(cursor='')

        # Clear item highlights
        for idx in self._drag_data.get('indices', []):
            try:
                self.orphan_media_list.itemconfig(idx, bg='white')
            except:
                pass  # Item may have been deleted

        # Clear drop target highlights
        self._clear_drop_highlights()

        # Reset drag data
        self._drag_data['items'] = []
        self._drag_data['indices'] = []
        self._drag_data['dragging'] = False
        self._drag_data['drop_target'] = None
        self._drag_data['source_widget'] = None
