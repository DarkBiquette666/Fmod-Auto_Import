"""Core business logic modules for FMOD Project management.

This package contains specialized managers for different aspects of FMOD project
manipulation, extracted from the monolithic project.py for better maintainability.
"""

from .xml_loader import XMLLoader
from .xml_writer import write_pretty_xml
from .pending_folder_manager import PendingFolderManager
from .bus_manager import BusManager
from .bank_manager import BankManager
from .event_folder_manager import EventFolderManager
from .asset_folder_manager import AssetFolderManager

__all__ = [
    'XMLLoader',
    'write_pretty_xml',
    'PendingFolderManager',
    'BusManager',
    'BankManager',
    'EventFolderManager',
    'AssetFolderManager',
    'EventCreator',
    'AudioFileManager',
]
