"""
GUI Dialogs Mixin Module
Handles dialog windows for CRUD operations on FMOD project items.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import xml.etree.ElementTree as ET
import uuid


class DialogsMixin:
    """
    Mixin class providing dialog functionality.

    These methods are mixed into FmodImporterGUI via multiple inheritance.
    All methods access shared state through 'self'.
    """

    def _center_dialog(self, dialog: tk.Toplevel):
        """Center dialog relative to main window"""
        dialog.update_idletasks()

        # Get main window position and size
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()

        # Get dialog size
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()

        # Calculate center position
        x = main_x + (main_width - dialog_width) // 2
        y = main_y + (main_height - dialog_height) // 2

        # Ensure dialog stays on screen
        if x < 0:
            x = 0
        if y < 0:
            y = 0

        dialog.geometry(f"+{x}+{y}")

    def _show_crud_list_dialog(self, title: str, items: dict, create_fn, delete_fn):
        """Show a dialog with list view for CRUD operations"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog)

        frame = ttk.Frame(dialog, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create listbox
        list_frame = ttk.Frame(frame)
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        listbox = tk.Listbox(list_frame, selectmode='single')
        listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        listbox['yscrollcommand'] = scrollbar.set

        result = [None]

        def refresh_list():
            """Refresh the listbox sorted A-Z"""
            listbox.delete(0, tk.END)
            if items:
                # Sort items by name A-Z
                sorted_items = sorted(items.values(), key=lambda x: x['name'].lower())
                for item_data in sorted_items:
                    listbox.insert(tk.END, item_data['name'])
            else:
                listbox.insert(tk.END, "(No items found)")

        def on_new():
            """Create new item"""
            name = simpledialog.askstring("New Item", "Enter name:", parent=dialog)
            if name:
                try:
                    create_fn(name)
                    refresh_list()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create item:\n{str(e)}")

        def on_rename():
            """Rename selected item"""
            selection = listbox.curselection()
            if not selection or not items:
                return

            index = selection[0]
            item_ids = list(items.keys())
            item_id = item_ids[index]
            item_name = items[item_id]['name']

            new_name = simpledialog.askstring("Rename", "Enter new name:",
                                            initialvalue=item_name, parent=dialog)
            if new_name and new_name != item_name:
                try:
                    # Update XML directly
                    item_data = items[item_id]
                    xml_path = item_data['path']
                    tree_xml = ET.parse(xml_path)
                    root_xml = tree_xml.getroot()

                    name_elem = root_xml.find(".//property[@name='name']/value")
                    if name_elem is not None:
                        name_elem.text = new_name
                        self.project._write_pretty_xml(root_xml, xml_path)
                        item_data['name'] = new_name
                        refresh_list()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename:\n{str(e)}")

        def on_delete():
            """Delete selected item"""
            selection = listbox.curselection()
            if not selection or not items:
                return

            index = selection[0]
            item_ids = list(items.keys())
            item_id = item_ids[index]

            try:
                delete_fn(item_id)
                refresh_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete item:\n{str(e)}")

        def on_key(event):
            """Handle keyboard shortcuts"""
            if event.keysym == 'F2':
                on_rename()

        listbox.bind('<Key>', on_key)

        def on_select():
            selection = listbox.curselection()
            if selection and items:
                index = selection[0]
                item_ids = list(items.keys())
                item_id = item_ids[index]
                item_name = items[item_id]['name']
                result[0] = (item_name, item_id)
                dialog.destroy()

        def on_cancel():
            dialog.destroy()

        # Initial populate
        refresh_list()

        # Edit buttons
        edit_frame = ttk.Frame(frame)
        edit_frame.grid(row=1, column=0, pady=5)
        ttk.Button(edit_frame, text="New", command=on_new, width=12).grid(row=0, column=0, padx=5)
        ttk.Button(edit_frame, text="Rename (F2)", command=on_rename, width=12).grid(row=0, column=1, padx=5)
        ttk.Button(edit_frame, text="Delete", command=on_delete, width=12).grid(row=0, column=2, padx=5)

        # Selection buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, pady=10)
        ttk.Button(button_frame, text="Select", command=on_select, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel, width=15).grid(row=0, column=1, padx=5)

        # Configure grid weights
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        dialog.wait_window()
        return result[0]

    def _show_hierarchical_dialog(self, title: str, items: dict, create_fn, delete_fn):
        """Show a dialog with tree view for hierarchical items (Banks, Buses)"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog)

        frame = ttk.Frame(dialog, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Search field
        search_frame = ttk.Frame(frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=40)
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        search_frame.columnconfigure(1, weight=1)

        # Create treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        tree = ttk.Treeview(tree_frame, selectmode='browse')
        tree.heading('#0', text=title)
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree['yscrollcommand'] = scrollbar.set

        result = [None]

        def has_matching_descendant(item_id, search_filter):
            """Check if item or any descendant matches the search filter"""
            if not search_filter:
                return True

            # Check current item
            if item_id in items and search_filter.lower() in items[item_id]['name'].lower():
                return True

            # Check children recursively
            for child_id, child_data in items.items():
                if child_data.get('parent') == item_id:
                    if has_matching_descendant(child_id, search_filter):
                        return True

            return False

        def build_tree(parent_item, parent_id, search_filter=""):
            """Build tree hierarchy with alphabetical sorting and search filter"""
            # Get children and sort alphabetically
            children = [(item_id, item_data) for item_id, item_data in items.items()
                       if item_data.get('parent') == parent_id]
            children.sort(key=lambda x: x[1]['name'].lower())

            for item_id, item_data in children:
                # Apply search filter - show if item or any descendant matches
                if search_filter:
                    if not has_matching_descendant(item_id, search_filter):
                        continue

                node = tree.insert(parent_item, 'end', text=item_data['name'], values=(item_id,))
                build_tree(node, item_id, search_filter)

        def find_root_items():
            """Find root items (items without parent or with None parent), sorted alphabetically"""
            roots = []
            for item_id, item_data in items.items():
                parent = item_data.get('parent')
                if parent is None or parent not in items:
                    roots.append((item_id, item_data))
            roots.sort(key=lambda x: x[1]['name'].lower())
            return roots

        def get_expanded_items():
            """Get list of expanded item IDs"""
            expanded = []
            def check_item(item):
                if tree.item(item, 'open'):
                    values = tree.item(item, 'values')
                    if values:
                        expanded.append(values[0])
                for child in tree.get_children(item):
                    check_item(child)
            for item in tree.get_children():
                check_item(item)
            return expanded

        def expand_all():
            """Expand all tree items"""
            def expand_item(item):
                tree.item(item, open=True)
                for child in tree.get_children(item):
                    expand_item(child)
            for item in tree.get_children():
                expand_item(item)

        def collapse_all():
            """Collapse all tree items"""
            def collapse_item(item):
                for child in tree.get_children(item):
                    tree.item(child, open=False)
                    collapse_item(child)
            for item in tree.get_children():
                tree.item(item, open=True)
                collapse_item(item)

        def restore_expanded_state(expanded_ids):
            """Restore expanded state of items"""
            def restore_item(item):
                values = tree.item(item, 'values')
                if values and values[0] in expanded_ids:
                    tree.item(item, open=True)
                for child in tree.get_children(item):
                    restore_item(child)
            for item in tree.get_children():
                restore_item(item)

        def refresh_tree(search_filter=""):
            """Rebuild tree after changes, preserving expanded state"""
            expanded_ids = get_expanded_items()
            tree.delete(*tree.get_children())

            # Build tree from roots
            roots = find_root_items()
            for root_id, root_data in roots:
                # Apply search filter - show if root or any descendant matches
                if search_filter:
                    if not has_matching_descendant(root_id, search_filter):
                        continue

                root_node = tree.insert('', 'end', text=root_data['name'], values=(root_id,))
                build_tree(root_node, root_id, search_filter)

            restore_expanded_state(expanded_ids)
            if search_filter:
                expand_all()  # Expand all when searching

        # Bind search to refresh tree
        def on_search_change(*args):
            refresh_tree(search_var.get())

        search_var.trace('w', on_search_change)

        def on_new():
            selection = tree.selection()
            parent_id = None
            if selection:
                parent_item = selection[0]
                parent_id = tree.item(parent_item, 'values')[0]

            initial_value = self._get_combined_name()
            name = simpledialog.askstring("New Item", "Enter name:",
                                          initialvalue=initial_value, parent=dialog)
            if name:
                try:
                    new_id = create_fn(name, parent_id)
                    refresh_tree()

                    # Find and select the newly created item in the tree
                    def find_and_select(item=''):
                        """Recursively find the item with new_id and select it"""
                        for child in tree.get_children(item):
                            values = tree.item(child, 'values')
                            if values and values[0] == new_id:
                                tree.selection_set(child)
                                tree.see(child)
                                # Auto-select and close dialog
                                result[0] = (name, new_id)
                                dialog.destroy()
                                return True
                            if find_and_select(child):
                                return True
                        return False

                    find_and_select()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create:\n{str(e)}")

        def on_rename():
            selection = tree.selection()
            if not selection:
                return

            item = selection[0]
            item_name = tree.item(item, 'text')
            item_id = tree.item(item, 'values')[0]

            new_name = simpledialog.askstring("Rename", "Enter new name:",
                                            initialvalue=item_name, parent=dialog)
            if new_name and new_name != item_name:
                try:
                    item_data = items[item_id]
                    xml_path = item_data['path']
                    tree_xml = ET.parse(xml_path)
                    root_xml = tree_xml.getroot()

                    name_elem = root_xml.find(".//property[@name='name']/value")
                    if name_elem is not None:
                        name_elem.text = new_name
                        self.project._write_pretty_xml(root_xml, xml_path)
                        item_data['name'] = new_name
                        refresh_tree()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename:\n{str(e)}")

        def on_delete():
            selection = tree.selection()
            if not selection:
                return

            item = selection[0]
            item_id = tree.item(item, 'values')[0]

            try:
                delete_fn(item_id)
                refresh_tree()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete:\n{str(e)}")

        def on_select():
            selection = tree.selection()
            if selection:
                item = selection[0]
                item_name = tree.item(item, 'text')
                item_id = tree.item(item, 'values')[0]
                result[0] = (item_name, item_id)
                dialog.destroy()

        def on_cancel():
            dialog.destroy()

        def on_key(event):
            """Handle keyboard shortcuts"""
            if event.keysym == 'F2':
                on_rename()

        tree.bind('<Key>', on_key)
        tree.bind('<Double-Button-1>', lambda e: on_select())

        # Initial build
        refresh_tree()
        expand_all()

        # Edit buttons
        edit_frame = ttk.Frame(frame)
        edit_frame.grid(row=2, column=0, pady=5)
        ttk.Button(edit_frame, text="New", command=on_new, width=10).grid(row=0, column=0, padx=2)
        ttk.Button(edit_frame, text="Rename (F2)", command=on_rename, width=12).grid(row=0, column=1, padx=2)
        ttk.Button(edit_frame, text="Delete", command=on_delete, width=10).grid(row=0, column=2, padx=2)
        ttk.Button(edit_frame, text="Expand All", command=expand_all, width=10).grid(row=0, column=3, padx=2)
        ttk.Button(edit_frame, text="Collapse", command=collapse_all, width=10).grid(row=0, column=4, padx=2)

        # Selection buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=0, pady=10)
        ttk.Button(button_frame, text="Select", command=on_select, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel, width=15).grid(row=0, column=1, padx=5)

        # Configure grid weights
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        dialog.wait_window()
        return result[0]

    def _show_folder_tree_dialog(self, title: str):
        """Show a dialog with tree view for folder selection"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        self._center_dialog(dialog)

        frame = ttk.Frame(dialog, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        tree = ttk.Treeview(tree_frame, selectmode='browse')
        tree.heading('#0', text='Event Folders')
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree['yscrollcommand'] = scrollbar.set

        # Build tree hierarchy sorted A-Z
        def build_tree(parent_item, parent_folder_id):
            # Get all child folders and sort them by name A-Z
            child_folders = [(folder_id, folder_data) for folder_id, folder_data in self.project.event_folders.items()
                           if folder_data['parent'] == parent_folder_id]
            child_folders.sort(key=lambda x: x[1]['name'].lower())

            for folder_id, folder_data in child_folders:
                item = tree.insert(parent_item, 'end', text=folder_data['name'], values=(folder_id,))
                build_tree(item, folder_id)

        # Start with master folder
        master_id = self.project.workspace['masterEventFolder']
        master_name = self.project.event_folders[master_id]['name']
        root_item = tree.insert('', 'end', text=master_name, values=(master_id,))
        build_tree(root_item, master_id)

        result = [None]

        def get_expanded_items():
            """Get list of expanded item IDs"""
            expanded = []
            def check_item(item):
                if tree.item(item, 'open'):
                    values = tree.item(item, 'values')
                    if values:
                        expanded.append(values[0])
                for child in tree.get_children(item):
                    check_item(child)
            for item in tree.get_children():
                check_item(item)
            return expanded

        def expand_all():
            """Expand all tree items"""
            def expand_item(item):
                tree.item(item, open=True)
                for child in tree.get_children(item):
                    expand_item(child)
            for item in tree.get_children():
                expand_item(item)

        def collapse_all():
            """Collapse all tree items except root"""
            def collapse_item(item):
                for child in tree.get_children(item):
                    tree.item(child, open=False)
                    collapse_item(child)
            for item in tree.get_children():
                tree.item(item, open=True)  # Keep root open
                collapse_item(item)

        def restore_expanded_state(expanded_ids):
            """Restore expanded state of items"""
            def restore_item(item):
                values = tree.item(item, 'values')
                if values and values[0] in expanded_ids:
                    tree.item(item, open=True)
                for child in tree.get_children(item):
                    restore_item(child)
            for item in tree.get_children():
                restore_item(item)

        def refresh_tree():
            """Rebuild tree after changes, preserving expanded state"""
            expanded_ids = get_expanded_items()
            tree.delete(*tree.get_children())
            master_id = self.project.workspace['masterEventFolder']
            master_name = self.project.event_folders[master_id]['name']
            root_item = tree.insert('', 'end', text=master_name, values=(master_id,))
            build_tree(root_item, master_id)
            restore_expanded_state(expanded_ids)

        def on_new_folder():
            selection = tree.selection()
            if not selection:
                return

            parent_item = selection[0]
            parent_id = tree.item(parent_item, 'values')[0]

            initial_value = self._get_combined_name()
            name = simpledialog.askstring("New Folder", "Enter folder name:",
                                          initialvalue=initial_value, parent=dialog)
            if name:
                try:
                    new_id = self.project.create_event_folder(name, parent_id)
                    refresh_tree()

                    # Find and select the newly created folder in the tree
                    def find_and_select(item=''):
                        """Recursively find the folder with new_id and select it"""
                        for child in tree.get_children(item):
                            values = tree.item(child, 'values')
                            if values and values[0] == new_id:
                                tree.selection_set(child)
                                tree.see(child)
                                # Auto-select and close dialog
                                result[0] = (name, new_id)
                                dialog.destroy()
                                return True
                            if find_and_select(child):
                                return True
                        return False

                    find_and_select()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create folder:\n{str(e)}")

        def on_rename():
            selection = tree.selection()
            if not selection:
                return

            item = selection[0]
            folder_name = tree.item(item, 'text')
            folder_id = tree.item(item, 'values')[0]

            # Check if it's the master folder
            master_id = self.project.workspace['masterEventFolder']
            if folder_id == master_id:
                return

            new_name = simpledialog.askstring("Rename Folder", "Enter new name:",
                                            initialvalue=folder_name, parent=dialog)
            if new_name and new_name != folder_name:
                try:
                    # Update the name in the XML
                    folder_data = self.project.event_folders[folder_id]
                    xml_path = folder_data['path']
                    tree_xml = ET.parse(xml_path)
                    root_xml = tree_xml.getroot()

                    name_elem = root_xml.find(".//property[@name='name']/value")
                    if name_elem is not None:
                        name_elem.text = new_name
                        self.project._write_pretty_xml(root_xml, xml_path)
                        folder_data['name'] = new_name
                        refresh_tree()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename folder:\n{str(e)}")

        def on_delete_folder():
            selection = tree.selection()
            if not selection:
                return

            item = selection[0]
            folder_name = tree.item(item, 'text')
            folder_id = tree.item(item, 'values')[0]

            master_id = self.project.workspace['masterEventFolder']
            if folder_id == master_id:
                return

            try:
                self.project.delete_folder(folder_id)
                refresh_tree()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete folder:\n{str(e)}")

        def on_select():
            selection = tree.selection()
            if selection:
                item = selection[0]
                folder_name = tree.item(item, 'text')
                folder_id = tree.item(item, 'values')[0]
                result[0] = (folder_name, folder_id)
                dialog.destroy()

        def on_cancel():
            dialog.destroy()

        def on_key(event):
            """Handle keyboard shortcuts"""
            if event.keysym == 'F2':
                on_rename()

        tree.bind('<Key>', on_key)
        tree.bind('<Double-Button-1>', lambda e: on_select())

        # Expand all by default
        expand_all()

        # Edit buttons
        edit_frame = ttk.Frame(frame)
        edit_frame.grid(row=1, column=0, pady=5)
        ttk.Button(edit_frame, text="New", command=on_new_folder, width=10).grid(row=0, column=0, padx=2)
        ttk.Button(edit_frame, text="Rename (F2)", command=on_rename, width=12).grid(row=0, column=1, padx=2)
        ttk.Button(edit_frame, text="Delete", command=on_delete_folder, width=10).grid(row=0, column=2, padx=2)
        ttk.Button(edit_frame, text="Expand All", command=expand_all, width=10).grid(row=0, column=3, padx=2)
        ttk.Button(edit_frame, text="Collapse", command=collapse_all, width=10).grid(row=0, column=4, padx=2)

        # Selection buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, pady=10)
        ttk.Button(button_frame, text="Select", command=on_select, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel, width=15).grid(row=0, column=1, padx=5)

        # Configure grid weights
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        dialog.wait_window()
        return result[0]
