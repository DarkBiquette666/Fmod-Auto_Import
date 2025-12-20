"""Pending folder management for FMOD project.

Manages folders that are staged but not yet committed to XML files.
Provides transaction-like semantics for folder creation.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Tuple

from .xml_writer import write_pretty_xml


class PendingFolderManager:
    """Manages pending (uncommitted) event and asset folders."""

    def __init__(self):
        """Initialize the pending folder manager."""
        self._pending_event_folders = {}
        self._pending_asset_folders = {}

    def add_event_folder(self, folder_id: str, folder_data: Dict):
        """
        Add an event folder to the pending list.

        Args:
            folder_id: UUID of the folder
            folder_data: Dictionary containing folder information
        """
        self._pending_event_folders[folder_id] = folder_data

    def add_asset_folder(self, asset_id: str, folder_data: Dict):
        """
        Add an asset folder to the pending list.

        Args:
            asset_id: UUID of the asset folder
            folder_data: Dictionary containing folder information
        """
        self._pending_asset_folders[asset_id] = folder_data

    def commit_all(self, event_folders_dict: Dict, asset_folders_dict: Dict,
                   workspace: Dict, metadata_path: Path) -> Tuple[int, int]:
        """
        Commit all pending folders to XML files.

        This uses topological sorting to ensure parent folders are created
        before their children.

        Args:
            event_folders_dict: Dictionary of committed event folders
            asset_folders_dict: Dictionary of committed asset folders
            workspace: Workspace dictionary with master folder references
            metadata_path: Path to the Metadata directory

        Returns:
            Tuple of (num_event_folders_committed, num_asset_folders_committed)

        Raises:
            ValueError: If there are folders with missing parents
            RuntimeError: If commit fails (with rollback)
        """
        event_count = 0
        asset_count = 0
        committed_event_ids = []
        committed_asset_ids = []

        try:
            # Phase 1: Commit event folders with topological sort
            pending_event_items = list(self._pending_event_folders.items())

            while pending_event_items:
                made_progress = False
                remaining = []

                for folder_id, folder_data in pending_event_items:
                    parent_id = folder_data['parent']

                    # Check if parent is committed
                    parent_committed = (parent_id in event_folders_dict or
                                       parent_id in committed_event_ids or
                                       parent_id == workspace.get('masterEventFolder'))

                    if parent_committed:
                        # Create XML
                        root = ET.Element('objects', serializationModel="Studio.02.02.00")
                        obj = ET.SubElement(root, 'object', {'class': 'EventFolder', 'id': folder_id})

                        # Add name property
                        prop = ET.SubElement(obj, 'property', name='name')
                        value = ET.SubElement(prop, 'value')
                        value.text = folder_data['name']

                        # Add parent relationship
                        rel = ET.SubElement(obj, 'relationship', name='folder')
                        dest = ET.SubElement(rel, 'destination')
                        dest.text = parent_id

                        # Write to file
                        folder_file = metadata_path / "EventFolder" / f"{folder_id}.xml"
                        write_pretty_xml(root, folder_file)

                        # Update data and move to committed
                        folder_data['path'] = folder_file
                        event_folders_dict[folder_id] = folder_data
                        committed_event_ids.append(folder_id)
                        event_count += 1
                        made_progress = True
                    else:
                        remaining.append((folder_id, folder_data))

                # Deadlock detection
                if not made_progress and remaining:
                    orphaned = [f"{fdata['name']} (parent: {fdata['parent']})"
                               for fid, fdata in remaining]
                    raise ValueError(f"Cannot commit folders with missing parents: {orphaned}")

                pending_event_items = remaining

            # Phase 2: Commit asset folders
            for asset_id, folder_data in self._pending_asset_folders.items():
                # Create XML structure
                root_elem = ET.Element('objects', serializationModel="Studio.02.02.00")
                obj = ET.SubElement(root_elem, 'object', {'class': 'EncodableAsset', 'id': asset_id})

                # Add assetPath property
                prop = ET.SubElement(obj, 'property', name='assetPath')
                value = ET.SubElement(prop, 'value')
                value.text = folder_data['path']

                # Add masterAssetFolder relationship
                rel = ET.SubElement(obj, 'relationship', name='masterAssetFolder')
                dest = ET.SubElement(rel, 'destination')
                dest.text = folder_data['master_folder']

                # Write to file
                asset_file = metadata_path / "Asset" / f"{asset_id}.xml"
                write_pretty_xml(root_elem, asset_file)

                # Update data and move to committed
                folder_data['xml_path'] = asset_file
                asset_folders_dict[asset_id] = folder_data
                committed_asset_ids.append(asset_id)
                asset_count += 1

            # Clear pending folders
            self._pending_event_folders.clear()
            self._pending_asset_folders.clear()

            return (event_count, asset_count)

        except Exception as e:
            # Rollback: delete created files
            for folder_id in committed_event_ids:
                if folder_id in event_folders_dict:
                    folder_path = event_folders_dict[folder_id].get('path')
                    if folder_path and folder_path.exists():
                        folder_path.unlink()
                    del event_folders_dict[folder_id]

            for asset_id in committed_asset_ids:
                if asset_id in asset_folders_dict:
                    asset_path = asset_folders_dict[asset_id].get('xml_path')
                    if asset_path and asset_path.exists():
                        asset_path.unlink()
                    del asset_folders_dict[asset_id]

            raise RuntimeError(f"Failed to commit pending folders: {e}")

    def clear_all(self) -> int:
        """
        Clear all pending folders without committing them.

        Returns:
            Number of pending folders cleared
        """
        count = len(self._pending_event_folders) + len(self._pending_asset_folders)
        self._pending_event_folders.clear()
        self._pending_asset_folders.clear()
        return count

    def is_pending(self, folder_id: str) -> bool:
        """
        Check if a folder is pending (not yet committed to XML).

        Args:
            folder_id: UUID of the folder to check

        Returns:
            True if the folder is pending
        """
        return (folder_id in self._pending_event_folders or
                folder_id in self._pending_asset_folders)

    def get_all_event_folders(self, committed_folders: Dict) -> Dict:
        """
        Get all event folders (both committed and pending).

        Args:
            committed_folders: Dictionary of committed event folders

        Returns:
            Combined dictionary of committed and pending folders
        """
        return {**committed_folders, **self._pending_event_folders}

    def get_all_asset_folders(self, committed_folders: Dict) -> Dict:
        """
        Get all asset folders (both committed and pending).

        Args:
            committed_folders: Dictionary of committed asset folders

        Returns:
            Combined dictionary of committed and pending folders
        """
        return {**committed_folders, **self._pending_asset_folders}
