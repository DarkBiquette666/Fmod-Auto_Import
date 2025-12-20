"""
FMOD Project Management Module
Handles FMOD Studio project XML manipulation and metadata management.
"""

import os
import json
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from xml.dom import minidom
import wave

from .core.xml_loader import XMLLoader
from .core.xml_writer import write_pretty_xml
from .core.pending_folder_manager import PendingFolderManager
from .core.bus_manager import BusManager
from .core.bank_manager import BankManager
from .core.event_folder_manager import EventFolderManager
from .core.asset_folder_manager import AssetFolderManager
from .core.event_creator import EventCreator
from .core.audio_file_manager import AudioFileManager


class FMODProject:
    """Represents a FMOD Studio project and handles XML manipulation"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.metadata_path = self.project_path.parent / "Metadata"

        if not self.metadata_path.exists():
            raise ValueError(f"Metadata folder not found: {self.metadata_path}")

        # Initialize managers
        self._xml_loader = XMLLoader(self.metadata_path)
        self._pending_manager = PendingFolderManager()

        # Load only minimal data needed for UI at startup
        self.workspace = self._xml_loader.load_workspace()
        self.event_folders = self._xml_loader.load_event_folders()

        # OPTIMIZATION: Lazy load everything else
        self._banks = None
        self._buses = None
        self._asset_folders = None
        self._events_by_folder = None


    @property
    def banks(self) -> Dict[str, Dict]:
        """Lazy load banks on first access"""
        if self._banks is None:
            self._banks = self._xml_loader.load_banks()
        return self._banks

    @property
    def buses(self) -> Dict[str, Dict]:
        """Lazy load buses on first access"""
        if self._buses is None:
            self._buses = self._xml_loader.load_buses()
        return self._buses

    @property
    def asset_folders(self) -> Dict[str, Dict]:
        """Lazy load asset folders on first access"""
        if self._asset_folders is None:
            self._asset_folders = self._xml_loader.load_asset_folders()
        return self._asset_folders

    def get_events_in_folder(self, folder_id: str) -> List[Dict]:
        """Get all events in a specific folder (delegates to EventFolderManager)"""
        return EventFolderManager.get_events_in_folder(
            folder_id, self.event_folders, self.metadata_path
        )

    def get_bus_from_template_events(self, folder_id: str) -> Tuple[Optional[str], bool, set]:
        """Analyze bus routing in template folder events (delegates to EventFolderManager)"""
        return EventFolderManager.get_bus_from_template_events(
            folder_id, self.event_folders, self.metadata_path
        )

    def _get_master_bus_id(self) -> Optional[str]:
        """Get the master bus ID (delegates to BusManager)"""
        return BusManager.get_master_bus_id(self.buses)

    def get_folder_hierarchy(self) -> List[Tuple[str, str, int]]:
        """Get event folders as a hierarchical list (delegates to EventFolderManager)"""
        master_id = self.workspace['masterEventFolder']
        return EventFolderManager.get_hierarchy(master_id, self.event_folders)

    def create_event_folder(self, name: str, parent_id: str, commit: bool = True) -> str:
        """Create a new event folder (delegates to EventFolderManager)"""
        return EventFolderManager.create(
            name, parent_id, commit, self.metadata_path,
            self.event_folders, self._pending_manager
        )

    def create_bank(self, name: str, parent_id: str = None) -> str:
        """Create a new bank folder (delegates to BankManager)"""
        return BankManager.create(name, parent_id, self.metadata_path, self.banks)

    def delete_bank(self, bank_id: str):
        """Delete a bank (delegates to BankManager)"""
        BankManager.delete(bank_id, self.banks, self.metadata_path)

    def create_asset_folder(self, name: str, parent_path: str, commit: bool = True) -> str:
        """Create a new asset folder (delegates to AssetFolderManager)"""
        return AssetFolderManager.create(
            name, parent_path, commit, self.metadata_path,
            self.asset_folders, self._pending_manager, self.workspace
        )

    def create_bus(self, name: str, parent_id: str = None) -> str:
        """Create a new bus (delegates to BusManager)"""
        # If no parent specified, route to Master Bus
        if not parent_id:
            parent_id = self._get_master_bus_id()
        return BusManager.create(name, parent_id, self.metadata_path, self.buses)

    def delete_bus(self, bus_id: str):
        """Delete a bus (delegates to BusManager)"""
        BusManager.delete(bus_id, self.buses, self.metadata_path)

    def delete_folder(self, folder_id: str):
        """Delete an event folder (delegates to EventFolderManager)"""
        EventFolderManager.delete(folder_id, self.event_folders, self.metadata_path)

    def commit_pending_folders(self) -> Tuple[int, int]:
        """
        Commit all pending folders to XML files (delegates to PendingFolderManager).

        Returns:
            Tuple of (num_event_folders_committed, num_asset_folders_committed)
        """
        return self._pending_manager.commit_all(
            self.event_folders,
            self.asset_folders,
            self.workspace,
            self.metadata_path
        )

    def clear_pending_folders(self) -> int:
        """
        Clear all pending folders without committing them (delegates to PendingFolderManager).

        Returns:
            Number of pending folders cleared
        """
        return self._pending_manager.clear_all()

    def get_all_event_folders(self) -> Dict[str, Dict]:
        """
        Get all event folders (both committed and pending).
        Useful for tree displays.
        """
        return self._pending_manager.get_all_event_folders(self.event_folders)

    def get_all_asset_folders(self) -> Dict[str, Dict]:
        """
        Get all asset folders (both committed and pending).
        Useful for tree displays.
        """
        return self._pending_manager.get_all_asset_folders(self.asset_folders)

    def is_folder_pending(self, folder_id: str) -> bool:
        """Check if a folder is pending (not yet committed to XML)"""
        return self._pending_manager.is_pending(folder_id)

    def copy_event_from_template(self, template_event_id: str, new_name: str,
                                  dest_folder_id: str, bank_id: str, bus_id: str,
                                  audio_files: List[str], audio_asset_folder: str) -> str:
        """Copy an event from template (delegates to EventCreator)"""
        return EventCreator.copy_from_template(
            template_event_id, new_name, dest_folder_id, bank_id, bus_id,
            audio_files, audio_asset_folder, self.metadata_path,
            self.project_path, self.workspace
        )

    def create_audio_file(self, audio_file_path: str, asset_relative_path: str) -> str:
        """Create an AudioFile XML entry (delegates to AudioFileManager)"""
        return AudioFileManager.create(
            audio_file_path, asset_relative_path,
            self.metadata_path, self.workspace
        )
