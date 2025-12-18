"""
GUI Asset Dialogs Mixin Module
Handles asset folder tree dialog for FMOD project items.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import xml.etree.ElementTree as ET
import uuid


class AssetDialogsMixin:
    """
    Mixin class providing asset folder dialog functionality.

    These methods are mixed into FmodImporterGUI via multiple inheritance.
    All methods access shared state through 'self'.
    """

    def _show_asset_tree_dialog(self, title: str):
        """Show a dialog with tree view for asset folder selection"""
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
        tree.heading('#0', text='Asset Folders')
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree['yscrollcommand'] = scrollbar.set

        def build_path_hierarchy():
            """Build a hierarchical structure from asset paths"""
            # Create a dict to store path components: path -> (asset_id, full_path)
            path_tree = {}

            # First pass: collect all unique path components
            for asset_id, asset_data in self.project.asset_folders.items():
                asset_path = asset_data['path']
                if not asset_path:
                    continue

                # Split path into components (e.g., "Characters/Cat Boss Rich/" -> ["Characters", "Cat Boss Rich"])
                parts = [p for p in asset_path.split('/') if p]

                # Build intermediate paths
                for i in range(len(parts)):
                    partial_path = '/'.join(parts[:i+1]) + '/'
                    # Only store if it's the actual asset folder
                    if partial_path == asset_path:
                        path_tree[partial_path] = (asset_id, asset_path)
                    elif partial_path not in path_tree:
                        # Create placeholder for intermediate paths
                        path_tree[partial_path] = (None, partial_path)

            return path_tree

        def build_tree():
            """Build tree view from path hierarchy"""
            path_tree = build_path_hierarchy()

            # Get master asset folder ID
            master_id = self.project.workspace['masterAssetFolder']

            # Find master asset folder name (it should be in asset_folders)
            master_name = "Master Asset Folder"
            for asset_id, asset_data in self.project.asset_folders.items():
                if asset_id == master_id:
                    master_name = asset_data['path'].rstrip('/') if asset_data['path'] else master_name
                    break

            # Insert root (master asset folder)
            root_item = tree.insert('', 'end', text=master_name, values=(master_id, ''))

            # Create a mapping from path to tree item
            item_map = {'': root_item}

            # Sort paths to ensure parents are processed before children (case-insensitive A-Z)
            sorted_paths = sorted(path_tree.keys(), key=lambda x: x.lower())

            for path in sorted_paths:
                asset_id, full_path = path_tree[path]

                # Get display name (last component of path)
                display_name = path.rstrip('/').split('/')[-1] if path.rstrip('/') else path

                # Find parent path
                parts = [p for p in path.split('/') if p]
                if len(parts) > 1:
                    parent_path = '/'.join(parts[:-1]) + '/'
                else:
                    parent_path = ''

                # Get parent item
                parent_item = item_map.get(parent_path, root_item)

                # Insert item
                item = tree.insert(parent_item, 'end', text=display_name, values=(asset_id or '', full_path))
                item_map[path] = item

        build_tree()

        result = [None]

        def get_expanded_items():
            """Get list of expanded item paths"""
            expanded = []
            def check_item(item):
                if tree.item(item, 'open'):
                    values = tree.item(item, 'values')
                    if values and len(values) > 1:
                        expanded.append(values[1])  # Store the path
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

        def restore_expanded_state(expanded_paths):
            """Restore expanded state of items by path"""
            def restore_item(item):
                values = tree.item(item, 'values')
                if values and len(values) > 1 and values[1] in expanded_paths:
                    tree.item(item, open=True)
                for child in tree.get_children(item):
                    restore_item(child)
            for item in tree.get_children():
                restore_item(item)

        def refresh_tree():
            """Rebuild tree after changes, preserving expanded state"""
            expanded_paths = get_expanded_items()
            tree.delete(*tree.get_children())
            build_tree()
            restore_expanded_state(expanded_paths)

        def on_new_folder():
            """Create a new asset folder"""
            selection = tree.selection()
            if not selection:
                return

            parent_item = selection[0]
            values = tree.item(parent_item, 'values')
            parent_path = values[1] if len(values) > 1 else ''

            initial_value = self._get_combined_name()
            name = simpledialog.askstring("New Asset Folder", "Enter folder name:",
                                          initialvalue=initial_value, parent=dialog)
            if name:
                # Remove any slashes from the name
                name = name.replace('/', '')
                if not name:
                    messagebox.showerror("Error", "Invalid folder name")
                    return

                try:
                    # Create new path
                    new_path = parent_path + name + '/'

                    # Check if path already exists
                    for asset_data in self.project.asset_folders.values():
                        if asset_data['path'] == new_path:
                            messagebox.showerror("Error", "Asset folder with this path already exists")
                            return

                    # Create new asset folder
                    asset_id = "{" + str(uuid.uuid4()) + "}"
                    master_id = self.project.workspace['masterAssetFolder']

                    # Create XML structure
                    root_elem = ET.Element('objects', serializationModel="Studio.02.02.00")
                    obj = ET.SubElement(root_elem, 'object', {'class': 'EncodableAsset', 'id': asset_id})

                    # Add assetPath property
                    prop = ET.SubElement(obj, 'property', name='assetPath')
                    value = ET.SubElement(prop, 'value')
                    value.text = new_path

                    # Add masterAssetFolder relationship
                    rel = ET.SubElement(obj, 'relationship', name='masterAssetFolder')
                    dest = ET.SubElement(rel, 'destination')
                    dest.text = master_id

                    # Write to file
                    asset_file = self.project.metadata_path / "Asset" / f"{asset_id}.xml"
                    self.project._write_pretty_xml(root_elem, asset_file)

                    # Update internal structure
                    self.project.asset_folders[asset_id] = {
                        'path': new_path,
                        'xml_path': asset_file,
                        'master_folder': master_id
                    }

                    refresh_tree()

                    # Find and select the newly created asset folder in the tree
                    def find_and_select(item=''):
                        """Recursively find the asset folder with asset_id and select it"""
                        for child in tree.get_children(item):
                            values = tree.item(child, 'values')
                            if values and len(values) >= 2 and values[0] == asset_id:
                                tree.selection_set(child)
                                tree.see(child)
                                # Auto-select and close dialog
                                result[0] = (new_path, asset_id)
                                dialog.destroy()
                                return True
                            if find_and_select(child):
                                return True
                        return False

                    find_and_select()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create asset folder:\n{str(e)}")

        def on_rename():
            """Rename an existing asset folder"""
            selection = tree.selection()
            if not selection:
                return

            item = selection[0]
            values = tree.item(item, 'values')

            if len(values) < 2:
                return

            asset_id = values[0]
            current_path = values[1]

            # Can't rename master folder or empty paths
            if not asset_id or not current_path:
                return

            # Check if it's the master asset folder
            master_id = self.project.workspace['masterAssetFolder']
            if asset_id == master_id:
                return

            # Get current name (last component)
            current_name = current_path.rstrip('/').split('/')[-1]

            new_name = simpledialog.askstring("Rename Asset Folder", "Enter new name:",
                                            initialvalue=current_name, parent=dialog)
            if new_name and new_name != current_name:
                # Remove any slashes from the name
                new_name = new_name.replace('/', '')
                if not new_name:
                    messagebox.showerror("Error", "Invalid folder name")
                    return

                try:
                    # Build new path
                    parts = current_path.rstrip('/').split('/')
                    parts[-1] = new_name
                    new_path = '/'.join(parts) + '/'

                    # Check if new path already exists
                    for aid, asset_data in self.project.asset_folders.items():
                        if aid != asset_id and asset_data['path'] == new_path:
                            messagebox.showerror("Error", "Asset folder with this path already exists")
                            return

                    # Update the XML
                    asset_data = self.project.asset_folders[asset_id]
                    xml_path = asset_data['xml_path']
                    tree_xml = ET.parse(xml_path)
                    root_xml = tree_xml.getroot()

                    path_elem = root_xml.find(".//property[@name='assetPath']/value")
                    if path_elem is not None:
                        path_elem.text = new_path
                        self.project._write_pretty_xml(root_xml, xml_path)
                        asset_data['path'] = new_path

                        # Also update any child folders
                        for aid, adata in self.project.asset_folders.items():
                            if aid != asset_id and adata['path'].startswith(current_path):
                                # Update child path
                                child_xml_path = adata['xml_path']
                                child_tree = ET.parse(child_xml_path)
                                child_root = child_tree.getroot()
                                child_path_elem = child_root.find(".//property[@name='assetPath']/value")
                                if child_path_elem is not None:
                                    old_child_path = child_path_elem.text
                                    new_child_path = old_child_path.replace(current_path, new_path, 1)
                                    child_path_elem.text = new_child_path
                                    self.project._write_pretty_xml(child_root, child_xml_path)
                                    adata['path'] = new_child_path

                        refresh_tree()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename asset folder:\n{str(e)}")

        def on_delete_folder():
            """Delete an asset folder"""
            selection = tree.selection()
            if not selection:
                return

            item = selection[0]
            values = tree.item(item, 'values')

            if len(values) < 2:
                return

            asset_id = values[0]
            current_path = values[1]

            # Can't delete master folder or empty
            if not asset_id or not current_path:
                return

            master_id = self.project.workspace['masterAssetFolder']
            if asset_id == master_id:
                return

            try:
                # Delete the XML file
                asset_data = self.project.asset_folders[asset_id]
                xml_path = asset_data['xml_path']
                if xml_path.exists():
                    xml_path.unlink()

                # Remove from internal structure
                del self.project.asset_folders[asset_id]

                refresh_tree()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete asset folder:\n{str(e)}")

        def on_select():
            """Select the current asset folder"""
            selection = tree.selection()
            if selection:
                item = selection[0]
                values = tree.item(item, 'values')
                if len(values) >= 2:
                    asset_id = values[0]
                    asset_path = values[1]
                    # Check if this is a valid FMOD asset folder (not an intermediate/placeholder)
                    if not asset_id:
                        messagebox.showwarning("Invalid Selection",
                            "This folder doesn't exist in FMOD. Please select an actual asset folder, "
                            "or create a new one using the 'New' button.")
                        return
                    result[0] = (asset_path, asset_id)
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
