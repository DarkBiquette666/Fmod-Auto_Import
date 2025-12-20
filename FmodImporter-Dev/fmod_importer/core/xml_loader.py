"""XML loading module for FMOD project metadata.

Handles loading all XML data structures from FMOD project metadata files.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict


class XMLLoader:
    """Loads and parses FMOD project XML metadata files."""

    def __init__(self, metadata_path: Path):
        """
        Initialize the XML loader.

        Args:
            metadata_path: Path to the FMOD project Metadata directory
        """
        self.metadata_path = metadata_path

    def load_workspace(self) -> Dict:
        """
        Load workspace.xml to get master folder references.

        Returns:
            Dictionary containing workspace ID and master folder references

        Raises:
            ValueError: If Workspace.xml is not found or invalid
        """
        workspace_file = self.metadata_path / "Workspace.xml"
        if not workspace_file.exists():
            raise ValueError("Workspace.xml not found")

        tree = ET.parse(workspace_file)
        root = tree.getroot()

        workspace_obj = root.find(".//object[@class='Workspace']")
        if workspace_obj is None:
            raise ValueError("Workspace object not found")

        return {
            'id': workspace_obj.get('id'),
            'masterEventFolder': workspace_obj.find(".//relationship[@name='masterEventFolder']/destination").text,
            'masterBankFolder': workspace_obj.find(".//relationship[@name='masterBankFolder']/destination").text,
            'masterAssetFolder': workspace_obj.find(".//relationship[@name='masterAssetFolder']/destination").text
        }

    def load_event_folders(self) -> Dict[str, Dict]:
        """
        Load all event folders from the EventFolder directory.

        Returns:
            Dictionary mapping folder IDs to folder information
        """
        folders = {}
        event_folder_dir = self.metadata_path / "EventFolder"

        if not event_folder_dir.exists():
            return folders

        for xml_file in event_folder_dir.glob("*.xml"):
            tree = ET.parse(xml_file)
            root = tree.getroot()

            for obj in root.findall(".//object"):
                folder_id = obj.get('id')
                name_elem = obj.find(".//property[@name='name']/value")
                name = name_elem.text if name_elem is not None else "Unnamed"

                # Get parent folder
                parent_rel = obj.find(".//relationship[@name='folder']/destination")
                parent_id = parent_rel.text if parent_rel is not None else None

                folders[folder_id] = {
                    'name': name,
                    'parent': parent_id,
                    'path': xml_file,
                    'items': []
                }

        return folders

    def load_banks(self) -> Dict[str, Dict]:
        """
        Load all banks from the Bank directory.

        Returns:
            Dictionary mapping bank IDs to bank information
        """
        banks = {}
        bank_dir = self.metadata_path / "Bank"

        if not bank_dir.exists():
            return banks

        for xml_file in bank_dir.glob("*.xml"):
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Look for both MasterBank and Bank classes
            for obj in root.findall(".//object"):
                obj_class = obj.get('class')
                if obj_class in ['MasterBank', 'Bank']:
                    bank_id = obj.get('id')
                    name_elem = obj.find(".//property[@name='name']/value")
                    name = name_elem.text if name_elem is not None else "Unnamed"

                    # Get parent relationship if exists
                    parent_rel = obj.find(".//relationship[@name='folder']/destination")
                    parent_id = parent_rel.text if parent_rel is not None else None

                    banks[bank_id] = {
                        'name': name,
                        'path': xml_file,
                        'parent': parent_id
                    }

        return banks

    def load_buses(self) -> Dict[str, Dict]:
        """
        Load all mixer buses from Master.xml and Group directory.

        Returns:
            Dictionary mapping bus IDs to bus information
        """
        buses = {}

        # Load master bus from Master.xml
        master_file = self.metadata_path / "Master.xml"
        if master_file.exists():
            tree = ET.parse(master_file)
            root = tree.getroot()

            for obj in root.findall(".//object"):
                obj_class = obj.get('class')
                if obj_class == 'MixerMaster':
                    bus_id = obj.get('id')
                    name_elem = obj.find(".//property[@name='name']/value")
                    name = name_elem.text if name_elem is not None else "Master Bus"

                    buses[bus_id] = {
                        'name': name,
                        'path': master_file,
                        'parent': None  # Master has no parent
                    }

        # Load other buses from Group directory
        group_dir = self.metadata_path / "Group"
        if group_dir.exists():
            for xml_file in group_dir.glob("*.xml"):
                tree = ET.parse(xml_file)
                root = tree.getroot()

                for obj in root.findall(".//object"):
                    obj_class = obj.get('class')
                    if obj_class == 'MixerGroup':
                        bus_id = obj.get('id')
                        name_elem = obj.find(".//property[@name='name']/value")
                        name = name_elem.text if name_elem is not None else "Unnamed"

                        # Get parent relationship (output)
                        parent_rel = obj.find(".//relationship[@name='output']/destination")
                        parent_id = parent_rel.text if parent_rel is not None else None

                        buses[bus_id] = {
                            'name': name,
                            'path': xml_file,
                            'parent': parent_id
                        }

        return buses

    def load_asset_folders(self) -> Dict[str, Dict]:
        """
        Load all asset folders from the Asset directory.

        Returns:
            Dictionary mapping asset IDs to asset folder information
        """
        asset_folders = {}
        asset_dir = self.metadata_path / "Asset"

        if not asset_dir.exists():
            return asset_folders

        for xml_file in asset_dir.glob("*.xml"):
            tree = ET.parse(xml_file)
            root = tree.getroot()

            for obj in root.findall(".//object[@class='EncodableAsset']"):
                asset_id = obj.get('id')
                path_elem = obj.find(".//property[@name='assetPath']/value")
                asset_path = path_elem.text if path_elem is not None else ""

                master_folder_rel = obj.find(".//relationship[@name='masterAssetFolder']/destination")
                master_folder_id = master_folder_rel.text if master_folder_rel is not None else None

                asset_folders[asset_id] = {
                    'path': asset_path,
                    'xml_path': xml_file,
                    'master_folder': master_folder_id
                }

        return asset_folders
