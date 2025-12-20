"""Asset folder management for FMOD project.

Handles creation of asset folders (EncodableAsset objects with assetPath).
"""

import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict

from .xml_writer import write_pretty_xml


class AssetFolderManager:
    """Static methods for asset folder operations."""

    @staticmethod
    def create(name: str, parent_path: str, commit: bool, metadata_path: Path,
               asset_folders_dict: Dict, pending_manager, workspace: Dict) -> str:
        """
        Create a new asset folder.

        Args:
            name: Folder name (no slashes)
            parent_path: Parent folder path (e.g., "Characters/")
            commit: If True, write to XML immediately. If False, stage in memory only.
            metadata_path: Path to the Metadata directory
            asset_folders_dict: Dictionary of asset folders to update
            pending_manager: PendingFolderManager instance
            workspace: Workspace dictionary with master folder references

        Returns:
            New asset folder ID

        Raises:
            ValueError: If name is invalid or folder path already exists
        """
        # Remove any slashes from the name
        name = name.replace('/', '').replace('\\', '')
        if not name:
            raise ValueError("Invalid folder name: cannot be empty after removing slashes")

        # Build new path
        new_path = parent_path + name + '/'

        # Check for conflicts in both committed and pending folders
        all_asset_folders = pending_manager.get_all_asset_folders(asset_folders_dict)
        for asset_id, asset_data in all_asset_folders.items():
            if asset_data.get('path') == new_path:
                raise ValueError(f"Asset folder with path '{new_path}' already exists")

        asset_id = "{" + str(uuid.uuid4()) + "}"
        master_id = workspace['masterAssetFolder']

        # Build folder data
        folder_data = {
            'path': new_path,
            'xml_path': None,  # Will be set when committed
            'master_folder': master_id
        }

        if commit:
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

            # Ensure Asset directory exists
            asset_dir = metadata_path / "Asset"
            asset_dir.mkdir(exist_ok=True)

            # Write to file
            asset_file = asset_dir / f"{asset_id}.xml"
            write_pretty_xml(root_elem, asset_file)

            # Update path
            folder_data['xml_path'] = asset_file

            # Add to committed folders
            asset_folders_dict[asset_id] = folder_data
        else:
            # Stage in memory only
            pending_manager.add_asset_folder(asset_id, folder_data)

        return asset_id
