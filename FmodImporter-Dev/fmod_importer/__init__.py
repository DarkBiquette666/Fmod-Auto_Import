"""
FMOD Importer Package
A tool for importing audio assets into FMOD Studio projects.
"""

VERSION = "0.8.2"

from .project import FMODProject
from .naming import NamingPattern
from .matcher import AudioMatcher
from .gui import FmodImporterGUI

__all__ = [
    'VERSION',
    'FMODProject',
    'NamingPattern',
    'AudioMatcher',
    'FmodImporterGUI'
]


def main():
    """Entry point for the FMOD Importer application."""
    import tkinter as tk
    root = tk.Tk()
    app = FmodImporterGUI(root)
    root.mainloop()
