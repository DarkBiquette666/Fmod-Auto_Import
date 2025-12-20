# Changelog

All notable changes to the FMOD Importer Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
