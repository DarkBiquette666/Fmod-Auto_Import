"""Bank management for FMOD project.

Handles creation and deletion of bank folders (BankFolder objects).
"""

import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict

from .xml_writer import write_pretty_xml


class BankManager:
    """Static methods for bank and bank folder operations."""

    @staticmethod
    def create(name: str, parent_id: str, commit: bool, metadata_path: Path,
               banks_dict: Dict, pending_manager, serialization_model: str = "Studio.02.02.00") -> str:
        """
        Create a new bank folder (BankFolder object).

        Args:
            name: Name of the bank folder
            parent_id: Parent bank folder ID (can be None)
            commit: If True, write to XML immediately.
            metadata_path: Path to the Metadata directory
            banks_dict: Dictionary of banks to update
            pending_manager: PendingFolderManager instance
            serialization_model: FMOD serialization model version string

        Returns:
            UUID of the created bank folder
        """
        # Validate parent
        # Check committed AND pending
        all_banks = pending_manager.get_all_banks(banks_dict)
        if parent_id and parent_id in all_banks:
            parent_data = all_banks[parent_id]
            if parent_data.get('type') == 'bank':
                raise ValueError(f"Cannot create folder '{name}' inside a Bank ('{parent_data['name']}'). Please select a Folder.")

        # Check duplicates
        for bid, bdata in banks_dict.items():
            if bdata['name'] == name and bdata.get('parent') == parent_id:
                if commit:
                    raise ValueError(f"Bank folder '{name}' already exists")
                return bid
        
        pending_id = pending_manager.find_bank(name, parent_id)
        if pending_id:
            if commit:
                raise ValueError(f"Bank folder '{name}' is already pending creation")
            return pending_id

        bank_id = "{" + str(uuid.uuid4()) + "}"

        bank_data = {
            'name': name,
            'path': None,
            'parent': parent_id,
            'type': 'folder'
        }

        if commit:
            # Create XML
            root = ET.Element('objects', serializationModel=serialization_model)
            obj = ET.SubElement(root, 'object', {'class': 'BankFolder', 'id': bank_id})

            # Add name property
            prop = ET.SubElement(obj, 'property', name='name')
            value = ET.SubElement(prop, 'value')
            value.text = name

            # Add parent relationship if exists
            if parent_id:
                rel = ET.SubElement(obj, 'relationship', name='folder')
                dest = ET.SubElement(rel, 'destination')
                dest.text = parent_id

            # Ensure BankFolder directory exists
            bank_folder_dir = metadata_path / "BankFolder"
            bank_folder_dir.mkdir(exist_ok=True)

            # Write to file in BankFolder directory
            bank_file = bank_folder_dir / f"{bank_id}.xml"
            write_pretty_xml(root, bank_file)

            # Update internal structure
            bank_data['path'] = bank_file
            banks_dict[bank_id] = bank_data
        else:
            pending_manager.add_bank(bank_id, bank_data)

        return bank_id

    @staticmethod
    def create_bank(name: str, parent_id: str, commit: bool, metadata_path: Path,
                   banks_dict: Dict, pending_manager, serialization_model: str = "Studio.02.02.00") -> str:
        """
        Create a new individual bank (Bank object).

        Args:
            name: Name of the bank
            parent_id: Parent bank folder ID (can be None)
            commit: If True, write to XML immediately.
            metadata_path: Path to the Metadata directory
            banks_dict: Dictionary of banks to update
            pending_manager: PendingFolderManager instance
            serialization_model: FMOD serialization model version string

        Returns:
            UUID of the created bank
        """
        # Validate parent
        all_banks = pending_manager.get_all_banks(banks_dict)
        if parent_id and parent_id in all_banks:
            parent_data = all_banks[parent_id]
            if parent_data.get('type') == 'bank':
                raise ValueError(f"Cannot create bank '{name}' inside another Bank ('{parent_data['name']}'). Please select a Folder.")

        # Check duplicates
        for bid, bdata in banks_dict.items():
            if bdata['name'] == name and bdata.get('parent') == parent_id:
                if commit:
                    raise ValueError(f"Bank '{name}' already exists")
                return bid
        
        pending_id = pending_manager.find_bank(name, parent_id)
        if pending_id:
            if commit:
                raise ValueError(f"Bank '{name}' is already pending creation")
            return pending_id

        bank_id = "{" + str(uuid.uuid4()) + "}"

        bank_data = {
            'name': name,
            'path': None,
            'parent': parent_id,
            'type': 'bank'
        }

        if commit:
            # Create XML
            root = ET.Element('objects', serializationModel=serialization_model)
            obj = ET.SubElement(root, 'object', {'class': 'Bank', 'id': bank_id})

            # Add name property
            prop = ET.SubElement(obj, 'property', name='name')
            value = ET.SubElement(prop, 'value')
            value.text = name

            # Add parent folder relationship if exists
            if parent_id:
                rel = ET.SubElement(obj, 'relationship', name='folder')
                dest = ET.SubElement(rel, 'destination')
                dest.text = parent_id

            # Ensure Bank directory exists
            bank_dir = metadata_path / "Bank"
            bank_dir.mkdir(exist_ok=True)

            # Write to file in Bank directory
            bank_file = bank_dir / f"{bank_id}.xml"
            write_pretty_xml(root, bank_file)

            # Update internal structure
            bank_data['path'] = bank_file
            banks_dict[bank_id] = bank_data
        else:
            pending_manager.add_bank(bank_id, bank_data)

        return bank_id

    @staticmethod
    def delete(bank_id: str, banks_dict: Dict, metadata_path: Path):
        """
        Delete a bank.

        Args:
            bank_id: UUID of the bank to delete
            banks_dict: Dictionary of banks to update
            metadata_path: Path to the Metadata directory (unused but kept for consistency)
        """
        if bank_id in banks_dict:
            bank_path = banks_dict[bank_id]['path']
            if bank_path.exists():
                bank_path.unlink()
            del banks_dict[bank_id]

    @staticmethod
    def add_event_to_bank(bank_id: str, event_id: str, metadata_path: Path):
        """
        Add an event to a bank's XML relationship.

        Args:
            bank_id: UUID of the bank
            event_id: UUID of the event to add
            metadata_path: Path to the Metadata directory
        """
        bank_path = metadata_path / "Bank" / f"{bank_id}.xml"
        if not bank_path.exists():
            # Might be a bank folder instead of a bank
            return

        try:
            tree = ET.parse(bank_path)
            root = tree.getroot()
            
            bank_obj = root.find(".//object[@class='Bank']")
            if bank_obj is None:
                return

            rel_events = bank_obj.find("relationship[@name='events']")
            if rel_events is None:
                rel_events = ET.SubElement(bank_obj, 'relationship', {'name': 'events'})
            
            # Check if already exists
            exists = False
            for dest in rel_events.findall('destination'):
                if dest.text == event_id:
                    exists = True
                    break
            
            if not exists:
                dest = ET.SubElement(rel_events, 'destination')
                dest.text = event_id
                write_pretty_xml(root, bank_path)
                
        except Exception as e:
            print(f"Error adding event {event_id} to bank {bank_id}: {e}")
