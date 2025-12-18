#!/usr/bin/env python3
"""
FMOD Importer Tool - Entry Point

This file provides backwards-compatible entry point for the FMOD Importer application.
The actual implementation is in the fmod_importer package.

Usage:
    python fmod_importer.py
"""

# Re-export everything from the package for backwards compatibility
from fmod_importer import (
    VERSION,
    FMODProject,
    NamingPattern,
    AudioMatcher,
    FmodImporterGUI,
    main
)

__all__ = [
    'VERSION',
    'FMODProject',
    'NamingPattern',
    'AudioMatcher',
    'FmodImporterGUI',
    'main'
]

if __name__ == "__main__":
    main()
