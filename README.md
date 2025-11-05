# FMOD Moco Auto Import

Automated audio asset importer for FMOD Studio projects with Python GUI.

## Features

- **One-Click Import** - Complete import process from Python GUI
- **Intelligent Matching** - Smart event name parsing and audio file matching
- **Template Support** - Create events from templates with automatic configuration
- **Multi-Sound Support** - Automatically creates MultiSound for multiple audio files
- **Bank & Bus Assignment** - Automatic bank and bus routing configuration
- **Progress Tracking** - Real-time import status and comprehensive logging
- **Auto-Cleanup** - Temporary files deleted after successful import

## Components

- **moco_auto_import.py** - Main Python GUI application
- **Script/_Internal/MocoImportFromJson.js** - FMOD Studio JavaScript import script
- **launch_moco.bat** - Quick launcher for the GUI

## Workflow

1. **Launch GUI**: Run `launch_moco.bat` or `python moco_auto_import.py`
2. **Load Project**: Select your FMOD `.fspro` file
3. **Configure Settings**:
   - Select audio asset folder from FMOD project
   - Choose template folder (optional)
   - Select destination folder for new events
   - Set bank and bus routing
4. **Preview & Import**:
   - Review the event-to-audio mapping in the preview tree
   - Click **"Prepare Import"**
   - Import executes automatically via FMOD Studio command line
   - Success dialog shows import results

## How It Works

1. Python GUI analyzes your audio files and FMOD project structure
2. Generates a JSON payload with import instructions
3. Launches `fmodstudiocl.exe` with a JavaScript import script
4. Script uses FMOD API to create events, tracks, and assign audio files
5. Project is saved and results are returned to the GUI

## Requirements

- **Python 3.7+** with tkinter
- **FMOD Studio 2.02+** (automatically detected)
- Windows OS (paths are Windows-specific)

## File Structure

```
Fmod Scripts/
├── moco_auto_import.py          # Main application
├── launch_moco.bat              # Quick launcher
├── Script/
│   └── _Internal/
│       └── MocoImportFromJson.js  # FMOD import script
└── README.md
```

## Settings

Settings are automatically saved to `~/.moco_auto_import_settings.json` including:
- Last used project path
- Last used media path
- Default template folder
- Default destination folder
- Default bank and bus selections

## Troubleshooting

**Import fails with "FMOD Studio not found"**
- Go to Settings and manually select `fmodstudiocl.exe` path
- Usually located at: `C:\Program Files\FMOD SoundSystem\FMOD Studio X.XX.XX\fmodstudiocl.exe`

**Events created but no audio**
- Check that audio files exist in the specified media path
- Verify the asset folder is properly scanned in FMOD

## Status

✅ **Production Ready** - Fully functional import pipeline using FMOD Studio API

## Author

Created with assistance from Claude (Anthropic)
