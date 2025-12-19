# Changelog

All notable changes to FMOD Importer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Development protocol with skills (/new-feature, /debug, /refactor, /review)
- Automated code quality checks and SOLID principles enforcement
- Comprehensive documentation standards
- Conventional commit format

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

## Contributing

See development protocol in `.claude/skills/` for contribution guidelines.
