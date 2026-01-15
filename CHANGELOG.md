# Changelog

All notable changes to FMOD Importer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.12.0] - 2026-01-15

### Added
- **Recursive Scan Toggle**: Added a "Recursive" checkbox to the Media Files section. Default is now OFF (non-recursive), preventing accidental deep scanning. Check the box to enable recursive scanning of subdirectories.

## [0.11.0] - 2026-01-09

### Added
- **Dark Mode Support**: Full Dark Mode implementation with "Theme" selector in Settings. Uses dynamic color system via `ThemeManager`.
- **Refactoring**: Extracted `PatternSetupMixin` to new module to improve maintainability.

### Fixed
- **Settings UI**: Adjusted window size and styling to ensure all controls are visible and readable in both Light and Dark modes.
- **Stability**: Fixed crash in `widgets.py` caused by missing import.

## [0.10.6] - 2026-01-08

### Fixed
- **XML Validation (Critical)**: Fixed "Invalid Component" errors for auto-created events by removing invalid Fader from Mixer Input and adding default Automatable Properties.
- **Project Compatibility**: Template-based import now also respects the project's serialization version (e.g. 2.03) instead of forcing legacy version 2.02, preventing corruption of copied events.
## [0.10.5] - 2026-01-08

### Fixed
- **XML Version Mismatch**: Auto-created events now use the project's actual serialization version (e.g., "Studio.02.03.00") instead of a hardcoded value, preventing "malformed" flags in newer FMOD Studio versions.
- **XML Cleanup**: Removed empty `markerTracks` relationship that could cause validation warnings.
## [0.10.4] - 2026-01-08

### Fixed
- **Invalid Event XML**: Fixed "malformed component" errors in auto-created events by adding missing `start` and `voiceStealing` properties to `MultiSound` objects.
- **Bank Assignment**: Added validation to verify that selected Bank, Bus, and Destination Folder IDs actually exist in the current project before importing. This prevents silent failures when using Presets with outdated IDs.
## [0.10.3] - 2026-01-08

### Fixed
- **Auto-Create Events**: Fixed regression where events without templates were ignored during import.
  - Implemented `create_from_scratch` in Python event creator to handle file-to-event generation without templates.
## [0.10.2] - 2026-01-08

### Fixed
- **Import Regression**: Reverted to Python-based XML manipulation to fix regression where events were not being created.
- **FX Copying**: Implemented deep XML copy in Python to ensure FX and assignments are correctly preserved from templates.
- **Robustness**: Import now runs in a separate thread with a progress dialog and ensures FMOD Studio is closed to prevent corruption.

## [0.10.1] - 2025-01-08

### Fixed
- **Template Import**: Fixed template events being created from scratch instead of duplicated
  - Previously only copied volume/pitch, missing all effects (compressor, EQ, reverb, etc.)
  - Now uses FMOD Studio's native Duplicate action to preserve ALL template properties
  - Master track effects, group track effects, mixer settings, and parameters are now correctly copied

## [0.10.0] - 2025-01-08

### Added
- **Import Mode Selection**: New "Generate from Pattern" mode alongside existing "Match Template" mode
  - **Match Template**: Matches audio files to existing FMOD events using fuzzy logic (original behavior)
  - **Generate from Pattern**: Creates new events based on asset file naming patterns
- **Dynamic Pattern Field Order**: Pattern fields reorder based on selected mode
  - Template mode: Event Pattern first, Asset Pattern second
  - Pattern mode: Asset Name Pattern first (SOURCE), Event Name Pattern second (DESTINATION)
- **Separator fields**: Restored separator fields for Template mode pattern matching
- **Smart inheritance**: In Pattern mode, if Event Pattern is empty, it inherits from Asset Pattern

### Fixed
- Fixed missing `_create_pattern_input_widgets` method that was causing application crash
- Restored separator field functionality for Template mode (was accidentally removed)

### Changed
- Updated labels dynamically based on mode ("Event Pattern" vs "Event Name Pattern", etc.)
- Improved note text to explain each mode's behavior

## [0.9.0] - 2025-01-07

### Added
- macOS application bundle support with proper icon

## [0.8.0] - 2024-12-20

### Added
- **Progress Dialog**: Import progress dialog with animated progress bar
  - Prevents UI freeze during import by running FMOD Studio execution in background thread
  - Shows modal dialog with indeterminate progress bar (pulse animation)
  - Updates status messages at different import stages ("Preparing...", "Copying files...", "Executing FMOD...")
  - Thread-safe UI updates using tkinter's after() method
  - Graceful error handling with automatic dialog cleanup
  - User can see that the import is actively running instead of frozen window
  - Improves user experience during 1-5 minute import operations

### Technical
- New `ProgressDialog` class in [utils.py](FmodImporter-Dev/fmod_importer/gui/utils.py) (125 lines)
- Modified `import_assets()` in [import_workflow.py](FmodImporter-Dev/fmod_importer/gui/import_workflow.py) to use threading
- Uses Python stdlib threading module (no external dependencies)
- Maintains SOLID principles and mixin architecture

## [0.5.0] - 2024-12-20

### Refactored
- **Core Architecture**: Extracted project.py business logic into 8 specialized core modules
  - Reduced project.py from 1137 lines to 186 lines (84% reduction)
  - Improved modularity and maintainability following SOLID principles
  - Created core/ directory with specialized managers:
    - `xml_writer.py`: Shared XML formatting utilities
    - `xml_loader.py`: Centralized XML parsing for all FMOD metadata
    - `pending_folder_manager.py`: Transaction-like staging system with commit/rollback
    - `event_folder_manager.py`: CRUD operations for event folders
    - `asset_folder_manager.py`: CRUD operations for asset folders
    - `bus_manager.py`: CRUD operations for mixer buses
    - `bank_manager.py`: CRUD operations for bank folders
    - `event_creator.py`: Complex event copying from templates
    - `audio_file_manager.py`: Audio file XML entry creation
  - All backward compatibility maintained (GUI code unchanged)
  - Pattern: Facade pattern with delegation to stateless managers
  - Zero external dependencies preserved (stdlib only)

## [0.4.0] - 2024-12-20

### Fixed
- **UI Layout**: Corrected grid layout after preset system addition
  - Fixed orphans container to span rows 0-4 (rowspan=5) to cover full height up to preview header
  - Corrected row weight configuration to row 5 (preview tree) for proper vertical expansion
  - Moved button frame to row 6 to prevent overlap with preview tree content

## [0.3.0] - 2024-12-20

### Added
- **Preset System**: Complete configuration snapshot save/load functionality
  - Save entire configuration including paths, patterns, and FMOD references
  - Category-based organization for managing multiple presets
  - Dropdown selector with auto-load on selection
  - Smart UUID resolution: automatically creates missing FMOD elements (folders, banks, buses)
  - Override warning when saving over existing presets
  - Preset files stored in `~/.fmod_importer_presets/` as human-readable JSON
- New PresetsMixin following the 8-mixin architecture pattern
- Preset UI section added to main interface with Save and Manage buttons

### Changed
- **Refactored preset system** for code quality compliance
  - Extracted UUID resolution logic to separate [preset_resolver.py](FmodImporter-Dev/fmod_importer/gui/preset_resolver.py) module (349 lines)
  - Reduced [presets.py](FmodImporter-Dev/fmod_importer/gui/presets.py) from 1057 → 757 lines (below 800-line threshold)
  - Improved separation of concerns: PresetResolver handles FMOD reference resolution, PresetsMixin handles UI and persistence

### Technical
- Added preset_resolver.py (349 lines) - handles smart UUID resolution for FMOD references
- presets.py: 1057 → 757 lines (28% reduction, now complies with <800 guideline)
- widgets.py: 724 → 755 lines (94% of 800-line threshold)
- Maintains all SOLID principles and zero external dependencies

## [0.2.0] - 2025-12-20

### Added
- Development protocol with skills (/new-feature, /debug, /refactor, /review)
- Automated version bump system with /version-bump skill
- Automatic post-commit version bump proposals for feat/fix commits
- English-only coding standard for all code (variables, functions, comments)
- Automated code quality checks and SOLID principles enforcement
- Comprehensive documentation standards
- Conventional commit format (without signatures)

## [0.1.9] - 2024-12-19

### Added
- Reorganized UI layout with orphans panel on right side
- Customizable separator fields for Event and Asset patterns
- Optional template folder with checkbox selection for events

### Changed
- Refactored separator system - frontend for preview only, backend receives separator parameter
- Improved preview text handling to prevent left column resize

### Fixed
- Prevented left column resize when preview text changes

## [0.1.8] - 2024-12-19

### Fixed
- Improved template duplication robustness in import script
- Commit pending folders before checking asset folder existence

## [0.1.7] - 2024-12-18

### Fixed
- Format template placeholder names with user values for matching

## [0.1.0 - 0.1.6] - 2024-12-XX

### Added
- Initial FMOD Importer functionality
- Mixin-based GUI architecture
- Template-based event creation
- Audio file matching system
- Drag and drop support
- Settings persistence
- Event and asset folder management
- Pattern-based naming system
- Orphan media/event tracking

### Changed
- Various improvements to import workflow
- Enhanced audio file matching algorithms
- Refined UI layout and organization

### Fixed
- Multiple bug fixes in audio import process
- Timeline module relationship fixes
- Audio file visibility improvements
- Event creation robustness

## [0.9.0] - Earlier Version

Early development version with core functionality.

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backward compatible manner
- **PATCH** version for backward compatible bug fixes

## How to Update This File

When making changes, add entries under the `[Unreleased]` section following these categories:

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes

When releasing a new version:
1. Change `[Unreleased]` to the new version number and date: `[X.Y.Z] - YYYY-MM-DD`
2. Add a new `[Unreleased]` section at the top
3. Update VERSION in `fmod_importer/__init__.py`
4. Create a git tag for the release
