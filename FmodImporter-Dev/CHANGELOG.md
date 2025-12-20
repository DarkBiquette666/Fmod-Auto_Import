# Changelog

All notable changes to the FMOD Importer Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2024-12-20

### Added
- **FMOD Studio version mismatch detection** during analysis phase
  - Extracts project version from Workspace.xml `serializationModel` attribute
  - Extracts executable version from FMOD Studio executable path
  - Compares major.minor versions (e.g., 2.03 vs 2.02)
  - Shows error dialog with version details if mismatch detected
  - Blocks import until versions match
  - Added Version Info section to UI (Paths section) showing:
    - Project version
    - Executable version
    - Color-coded status indicator (✓ green or ✗ red)

### Changed
- Analysis now validates FMOD Studio version compatibility before template analysis
- Import workflow now blocks execution if version mismatch detected

### Technical Details
**Version Detection Flow:**
```
1. User clicks "Analyze"
2. Extract project version from Workspace.xml (e.g., "2.03.00")
3. Extract exe version from path (e.g., "2.02.30")
4. Compare major.minor only (ignore patch differences)
5. If mismatch → show error, block analysis/import
6. Update UI with detected versions and status
```

**Example Error:**
```
FMOD Studio Version Mismatch

Project Version: 2.03
Executable Version: 2.02

Import will fail with mismatched versions.

Please update the FMOD Studio Executable path in the Paths section
to use FMOD Studio 2.03.xx
```

## [0.6.3] - 2024-12-20

### Fixed
- **CRITICAL**: Fix audio import regression for files already in Assets/ folder
  - Root cause: `importAudioFile()` API fails on files already in FMOD project
  - Solution: Search for existing audio files first before attempting import
  - Added `findOrImportAudioFile()` helper function for smart audio handling
  - Result: Events now created successfully, audio marked as "used" in FMOD

### Added
- Always write result JSON file (even on JavaScript errors) for reliable Python feedback
- Comprehensive DEBUG logging throughout import flow for easier diagnostics
- Defensive template cloning with null checks and per-operation error handling
- Detailed error messages in result file for all failure points

### Technical Details
**Before (broken):**
```
1. Python copies audio to Assets/
2. JavaScript calls importAudioFile() on files in Assets/
3. API returns null (files already in project)
4. audioAssets.length === 0 → event skipped
5. No result file → Python shows misleading "Configuration Error"
```

**After (fixed):**
```
1. Python copies audio to Assets/
2. JavaScript searches for existing files first
3. Files found → use existing AudioFile objects
4. Files not found → import as external
5. Events created with audio attached
6. Result file always written with detailed status
```

## [0.6.2] - 2024-12-20

### Fixed
- Remove incorrect GUI vs console version detection that blocked imports
  - FMOD Studio.exe works fine for imports (used successfully in v0.2.x-v0.5.x)
  - Added fallback to search for most recent result file if path mismatch occurs
  - Removed proactive warnings about using Studio.exe instead of fmodstudiocl.exe

## [0.6.1] - 2024-12-20

### Fixed
- **CRITICAL**: Fix template duplication failure causing empty events
  - UI action `studio.window.triggerAction(Duplicate)` doesn't work in script/headless mode
  - Replaced with manual template cloning that copies properties directly
  - Now properly copies template properties: isOneshot, isStream, 3D settings, volume, pitch
  - Ensures events are actually created with correct structure from templates

## [0.6.0] - 2024-12-20

### Added
- Add FMOD Studio Executable field to main UI in Paths section
- FMOD executable path now visible and editable directly in main window
- Browse button for selecting FMOD Studio executable (prioritizes fmodstudiocl.exe)
- Auto-save FMOD executable path to settings on change
- FMOD executable path already included in preset save/load system

### Changed
- FMOD executable path no longer hidden in settings dialog
- Path is now part of the visible UI for better accessibility

## [0.5.1] - 2024-12-20

### Fixed
- Fix KeyError when importing events without matched templates (auto-created events)
- Add proactive detection of FMOD Studio GUI vs console version with auto-fix option
- Improve error messages when import fails due to GUI version usage
- Add detailed diagnostic messages for import failures with specific guidance

## [0.5.0] - 2024-12-20

### Added
- Complete refactoring of project.py into modular components
- Added preset system for complete configuration snapshots
- Added bus auto-detection from templates
- Added UserPromptSubmit hook for protocol enforcement

### Fixed
- Fix UI layout issues with preset controls
- Fix orphans container rowspan and preview weight
- Update placeholder text for feature entry field

## [0.4.0] - 2024-12-XX

### Added
- Initial preset system implementation

## [0.3.0] - 2024-12-XX

### Added
- Protocol enforcement via claude.md

## Earlier versions

See git history for changes prior to v0.3.0.
