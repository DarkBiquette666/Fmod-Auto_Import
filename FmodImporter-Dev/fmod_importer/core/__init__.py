"""Core business logic modules for FMOD Project management.

This package contains specialized managers for different aspects of FMOD project
manipulation, extracted from the monolithic project.py for better maintainability.
"""

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
