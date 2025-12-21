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
    def create(name: str, parent_id: str, metadata_path: Path, banks_dict: Dict) -> str:
        """
        Create a new bank folder (BankFolder object).

        Args:
            name: Name of the bank folder
            parent_id: Parent bank folder ID (can be None)
            metadata_path: Path to the Metadata directory
            banks_dict: Dictionary of banks to update

        Returns:
            UUID of the created bank folder
        """
        bank_id = "{" + str(uuid.uuid4()) + "}"

        # Create XML
        root = ET.Element('objects', serializationModel="Studio.02.02.00")
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
        banks_dict[bank_id] = {
            'name': name,
            'path': bank_file,
            'parent': parent_id,
            'type': 'folder'
        }

        return bank_id

    @staticmethod
    def create_bank(name: str, parent_id: str, metadata_path: Path, banks_dict: Dict) -> str:
        """
        Create a new individual bank (Bank object).

        Args:
            name: Name of the bank
            parent_id: Parent bank folder ID (can be None)
            metadata_path: Path to the Metadata directory
            banks_dict: Dictionary of banks to update

        Returns:
            UUID of the created bank
        """
        bank_id = "{" + str(uuid.uuid4()) + "}"

        # Create XML
        root = ET.Element('objects', serializationModel="Studio.02.02.00")
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
        banks_dict[bank_id] = {
            'name': name,
            'path': bank_file,
            'parent': parent_id,
            'type': 'bank'
        }

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
