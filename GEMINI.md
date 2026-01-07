# FMOD Importer Tool

## Project Overview

**FMOD Importer Tool** is a standalone Windows application designed to automate and intelligently import audio assets into FMOD Studio projects. It streamlines the workflow by automatically creating events, assigning banks and buses, and organizing assets based on file naming patterns.

*   **Type:** Python Desktop Application (GUI)
*   **Key Technologies:** Python 3.x, tkinter (Standard Library), XML (ElementTree), FMOD Studio Scripting API (JavaScript)
*   **Architecture:** Modular Core Logic + Mixin-based GUI
*   **Status:** Active Development (v0.8.x)

## Getting Started

### Prerequisites

*   **Python 3.x**: The application relies entirely on the Python standard library. No external `pip` packages are required.
*   **FMOD Studio**: Required to verify and use the imported assets.

### Installation

1.  Clone the repository.
2.  Navigate to the `FmodImporter-Dev` directory.

### Running the Application

To run the application from source:

```bash
cd FmodImporter-Dev
python fmod_importer.py
```

Alternatively, use the provided launcher scripts:
*   **Windows:** `launch.bat`
*   **Linux/Mac:** `launch.sh`

## Project Structure

*   **`FmodImporter-Dev/`**: Main development directory containing the source code.
    *   **`fmod_importer.py`**: The application entry point.
    *   **`fmod_importer/`**: The core Python package.
        *   **`core/`**: Business logic modules (e.g., `project.py`, `bank_manager.py`, `xml_loader.py`).
        *   **`gui/`**: GUI components implemented as Mixins (e.g., `main.py`, `widgets.py`, `dialogs.py`).
        *   **`matcher.py`**: Audio file matching logic.
        *   **`naming.py`**: Pattern-based name parsing.
    *   **`Script/_Internal/FmodImportFromJson.js`**: JavaScript file used to interface with FMOD Studio's scripting API.
*   **`FmodImporterTool-Package/`**: Contains the distributed standalone executable (`FmodImporter.exe`) and end-user documentation.
*   **`docs/`**: Project documentation, including `ARCHITECTURE.md` and `QUICKSTART.md`.
*   **`.claude/`**: Development protocols and "skills" documentation.

## Development Workflow

### Core Principles

*   **No External Dependencies:** The project strictly uses the Python standard library to ensure portability and ease of distribution.
*   **Modular Architecture:**
    *   **Core:** Business logic is split into specialized managers (Bank, Bus, Event, etc.) coordinated by `project.py`.
    *   **GUI:** The interface is built using a Mixin pattern to keep file sizes manageable and responsibilities clear.
*   **FMOD Integration:** The tool directly manipulates FMOD's XML files for structure and uses FMOD's JavaScript API for final asset assignment.
*   **Deferred Creation (Transactional):** All resource creation (Folders, Banks, Buses) is staged in memory first. Disk writes only happen when the user explicitly clicks "Import" or manually commits via dialogs.

### Building

The project is distributed as a standalone `.exe`. While the exact build script isn't explicitly detailed in the root, it likely uses `PyInstaller` (implied by the standalone nature and lack of dependencies).

## Key Features

*   **Intelligent Matching:** Matches audio files to existing event templates or creates new ones based on naming conventions.
*   **Pattern-Based Naming:** Supports flexible naming patterns (e.g., `$prefix_$feature_$action`).
*   **Automated Organization:** Automatically handles folder structures, bank assignments, and bus routing.
*   **Version Safety:** Detects mismatches between the FMOD Project version and the installed FMOD Studio executable to prevent compatibility issues.

## Critical Safety Warnings

*   **CLOSE FMOD STUDIO:** Always close FMOD Studio before running an import. The tool modifies XML files directly, and concurrent access can lead to project corruption.
*   **Backups:** Always backup your FMOD project before using the tool.

## Development Protocol

This project follows strict architecture and code quality principles. **Apply these rules automatically** for all code modifications.

### Architecture Principles (ALWAYS Enforce)

- **SOLID**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **DRY**: Extract repeated code at 3rd occurrence → create reusable component
- **KISS**: Prefer simple solutions over complex ones
- **SSOT**: Single Source of Truth (one VERSION location, centralized config)
- **Modularity**: 800-line threshold per file

### Automatic Checks (PROACTIVE - After ANY Code Modification)

After modifying code, **immediately check**:

1. **Line Count**: Use `wc -l` or count during Read
   - **[CRITICAL]**: >1000 lines → MUST refactor immediately
   - **[RECOMMEND]**: >900 lines → Strong suggestion to refactor
   - **[SUGGEST]**: >800 lines → Propose extraction
   - **[INFO]**: >750 lines → Alert approaching threshold

2. **Code Duplication**: Search for repeated patterns
   - 3+ occurrences → Extract to shared function/module
   - Flag location and suggest consolidation

3. **SOLID Violations**: Check Single Responsibility
   - Mixed concerns in one class/file → Suggest extraction
   - Example: project.py has XML parsing + cache + core logic

4. **Documentation**: Update automatically
   - Docstrings for new/modified functions
   - README.md for new features
   - CHANGELOG.md for all changes
   - docs/ARCHITECTURE.md for architectural changes

### Skills Decision Tree (Use Automatically)

When user requests work, **read and apply the appropriate skill**:

- **Bug fix / Error / Debug** → Read `.claude/skills/fmod-debug.md`
- **New feature / Add functionality** → Read `.claude/skills/fmod-feature.md`
- **Refactor / Code quality** → Read `.claude/skills/fmod-refactor.md`
- **Code review / Quality check** → Read `.claude/skills/fmod-review.md`

Global rules are in `.claude/skills/_protocol-rules.md`.

### Commit Strategy

- **Format**: `type(scope): subject` (conventional commits)
- **Types**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
- **Strategy**: Group by milestone (M1: core, M2: GUI, M3: docs)
- **Version**: Bump version for feat/fix (semantic versioning)

### Critical Files to Monitor

Current file sizes (updated 2024-12-20):
- ✅ **project.py**: 186 lines - OK (refactored, was 1075 lines)
- ⚠️ **widgets.py**: 762 lines - 95% of threshold
- ⚠️ **presets.py**: 757 lines - 95% of threshold
- ⚠️ **naming.py**: 710 lines - 89% of threshold
- ⚠️ **dialogs.py**: 699 lines - 87% of threshold

### Proactive Suggestions Format

Use severity levels in suggestions:

```
[SEVERITY] Issue Type: Description

Current state:
- Metric or measurement

Suggested improvement:
- Specific recommendation

Benefit:
- Impact on code quality

Effort: Low/Medium/High
Skill to use: /fmod-[skill-name]
```

### Important Notes

- **Zero external dependencies** - stdlib only
- **Mixin architecture** - 8 GUI mixins, keep separation clean
- **Lazy loading** - Properties loaded on first access
- **Test before commit** - Ensure tool still works after changes
- **English-only** - All code, comments, and commits in English

---

**Remember**: Be proactive. Check thresholds and suggest improvements without waiting to be asked.
