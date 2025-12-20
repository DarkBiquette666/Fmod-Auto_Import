# Changelog

All notable changes to the FMOD Importer Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
