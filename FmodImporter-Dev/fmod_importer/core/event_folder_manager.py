"""Event folder management for FMOD project.

Handles creation, deletion, and querying of event folders (EventFolder objects).
"""

import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .xml_writer import write_pretty_xml


class EventFolderManager:
    """Static methods for event folder operations."""

    @staticmethod
    def create(name: str, parent_id: str, commit: bool, metadata_path: Path,
               event_folders_dict: Dict, pending_manager) -> str:
        """
        Create a new event folder.

        Args:
            name: Folder name
            parent_id: Parent folder ID
            commit: If True, write to XML immediately. If False, stage in memory only.
            metadata_path: Path to the Metadata directory
            event_folders_dict: Dictionary of event folders to update
            pending_manager: PendingFolderManager instance

        Returns:
            New folder ID
        """
        folder_id = "{" + str(uuid.uuid4()) + "}"

        # Build folder data
        folder_data = {
            'name': name,
            'parent': parent_id,
            'path': None,  # Will be set when committed
            'items': []
        }

        if commit:
            # Create XML
            root = ET.Element('objects', serializationModel="Studio.02.02.00")
            obj = ET.SubElement(root, 'object', {'class': 'EventFolder', 'id': folder_id})

            # Add name property
            prop = ET.SubElement(obj, 'property', name='name')
            value = ET.SubElement(prop, 'value')
            value.text = name

            # Add parent relationship
            rel = ET.SubElement(obj, 'relationship', name='folder')
            dest = ET.SubElement(rel, 'destination')
            dest.text = parent_id

            # Ensure EventFolder directory exists
            event_folder_dir = metadata_path / "EventFolder"
            event_folder_dir.mkdir(exist_ok=True)

            # Write to file
            folder_file = event_folder_dir / f"{folder_id}.xml"
            write_pretty_xml(root, folder_file)

            # Update path
            folder_data['path'] = folder_file

            # Add to committed folders
            event_folders_dict[folder_id] = folder_data
        else:
            # Stage in memory only
            pending_manager.add_event_folder(folder_id, folder_data)

        return folder_id

    @staticmethod
    def delete(folder_id: str, event_folders_dict: Dict, metadata_path: Path):
        """
        Delete an event folder.

        Args:
            folder_id: UUID of the folder to delete
            event_folders_dict: Dictionary of event folders to update
            metadata_path: Path to the Metadata directory (unused but kept for consistency)
        """
        if folder_id in event_folders_dict:
            folder_path = event_folders_dict[folder_id]['path']
            if folder_path.exists():
                folder_path.unlink()
            del event_folders_dict[folder_id]

    @staticmethod
    def get_hierarchy(master_id: str, event_folders_dict: Dict) -> List[Tuple[str, str, int]]:
        """
        Get event folders as a hierarchical list.

        Args:
            master_id: ID of the master event folder
            event_folders_dict: Dictionary of event folders

        Returns:
            List of tuples (folder_name, folder_id, depth)
        """
        def build_hierarchy(folder_id: str, depth: int = 0) -> List[Tuple[str, str, int]]:
            result = []
            if folder_id in event_folders_dict:
                folder = event_folders_dict[folder_id]
                result.append((folder['name'], folder_id, depth))

                # Find children
                for fid, fdata in event_folders_dict.items():
                    if fdata['parent'] == folder_id:
                        result.extend(build_hierarchy(fid, depth + 1))

            return result

        return build_hierarchy(master_id)

    @staticmethod
    def get_events_in_folder(folder_id: str, event_folders_dict: Dict,
                            metadata_path: Path) -> List[Dict]:
        """
        Recursively get all events in a folder and its subfolders.

        Args:
            folder_id: Starting folder ID
            event_folders_dict: Dictionary of event folders
            metadata_path: Path to the Metadata directory

        Returns:
            List of event dictionaries with 'id', 'name', 'path', 'folder_id' keys
        """
        # Get all folder IDs in the hierarchy (this folder + all subfolders)
        target_folder_ids = {folder_id}

        def collect_subfolder_ids(current_folder_id: str):
            for fid, fdata in event_folders_dict.items():
                if fdata.get('parent') == current_folder_id:
                    target_folder_ids.add(fid)
                    collect_subfolder_ids(fid)

        collect_subfolder_ids(folder_id)

        # Parse XML files directly
        event_dir = metadata_path / "Event"
        if not event_dir.exists():
            return []

        events = []

        for xml_file in event_dir.glob("*.xml"):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                for obj in root.findall(".//object[@class='Event']"):
                    folder_rel = obj.find(".//relationship[@name='folder']/destination")
                    event_folder_id = folder_rel.text if folder_rel is not None else None

                    if event_folder_id in target_folder_ids:
                        event_id = obj.get('id')
                        name_elem = obj.find(".//property[@name='name']/value")
                        event_name = name_elem.text if name_elem is not None else "Unnamed"

                        events.append({
                            'id': event_id,
                            'name': event_name,
                            'path': xml_file,
                            'folder_id': event_folder_id
                        })
            except Exception:
                continue

        return events

    @staticmethod
    def get_bus_from_template_events(folder_id: str, event_folders_dict: Dict,
                                     metadata_path: Path) -> Tuple[Optional[str], bool, set]:
        """
        Analyze bus routing in template folder events.

        Parses all event XML files in the template folder to extract their
        bus routing (MixerInput.output relationship).

        Args:
            folder_id: Template folder UUID
            event_folders_dict: Dictionary of event folders
            metadata_path: Path to the Metadata directory

        Returns:
            Tuple of (common_bus_id, all_same, all_bus_ids):
            - common_bus_id: The bus ID if all events share same bus, else None
            - all_same: True if all events route to same bus
            - all_bus_ids: Set of all unique bus IDs found
        """
        # Get all events in folder
        events = EventFolderManager.get_events_in_folder(
            folder_id, event_folders_dict, metadata_path
        )

        if not events:
            return (None, True, set())

        bus_ids = set()
        event_dir = metadata_path / "Event"

        # Parse each event's XML to find bus routing
        for event in events:
            event_id = event['id']
            event_file = event_dir / f"{event_id}.xml"

            if not event_file.exists():
                continue

            try:
                tree = ET.parse(event_file)
                root = tree.getroot()

                # Find MixerInput object's output relationship
                mixer_input = root.find(".//object[@class='MixerInput']")
                if mixer_input is not None:
                    output_rel = mixer_input.find(".//relationship[@name='output']/destination")
                    if output_rel is not None and output_rel.text:
                        bus_ids.add(output_rel.text)
            except Exception:
                # Skip problematic XML files
                continue

        # Determine if all events use same bus
        all_same = len(bus_ids) == 1
        common_bus_id = bus_ids.pop() if all_same else None
        if all_same and common_bus_id:
            bus_ids.add(common_bus_id)  # Re-add for return value

        return (common_bus_id, all_same, bus_ids)
