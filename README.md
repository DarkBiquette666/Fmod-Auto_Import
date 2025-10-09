# FMOD Moco Auto Import

Automated audio asset importer for FMOD Studio 2.02 projects.

## Features

- Python GUI for selecting audio files and configuring import settings
- Automatic event creation from templates
- Multi-sound and single-sound support
- Batch import with progress tracking
- Comprehensive debug logging

## Components

- **moco_auto_import.py** - Main Python GUI application
- **Script/MocoImportFromJson.js** - FMOD Studio JavaScript import script
- **debug_pipeline.py** - Debug tool for analyzing import pipeline

## Usage

1. Open `moco_auto_import.py` with Python
2. Select FMOD project, audio files, templates, and destination folders
3. Configure bank and bus settings
4. Click "Import Assets"
5. FMOD Studio will execute the import automatically

## Requirements

- Python 3.7+
- FMOD Studio 2.02
- tkinter (usually included with Python)

## Status

**Work in Progress** - Audio files are imported and copied to Assets folder, events are created. Current issue: GroupTracks not being created properly.

## Author

Created with assistance from Claude (Anthropic)
