# FMOD Importer Architecture

**Last Updated**: 2024-12-21
**Version**: 0.8.0

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Design Principles](#design-principles)
4. [Module Structure](#module-structure)
5. [Design Patterns](#design-patterns)
6. [Data Flow](#data-flow)
7. [Key Design Decisions](#key-design-decisions)
8. [Extension Points](#extension-points)
9. [Known Issues and Technical Debt](#known-issues-and-technical-debt)
10. [Future Improvements](#future-improvements)

---

## Overview

FMOD Importer is a Python-based desktop application that facilitates importing audio assets into FMOD Studio projects. It uses a pattern-based matching system to automatically create events from audio files, supporting both template-based workflows and manual matching.

### Key Characteristics

- **Language**: Python 3.x (standard library only, no external dependencies)
- **GUI Framework**: tkinter (included in Python stdlib)
- **Architecture Pattern**:
  - Mixin-based composition for GUI (10 mixins)
  - Modular core logic (9 specialized managers with facade pattern)
  - Stateless managers with delegation
- **Lines of Code**: ~8,000 Python LOC
- **Platforms**: Windows (standalone .exe via PyInstaller)
- **Distribution**: Standalone executable (~25 MB, no Python installation required)

---

## Project Structure

```
fmod-importer/
├── FmodImporter-Dev/              # Main development directory
│   ├── fmod_importer/             # Core Python package
│   │   ├── __init__.py            # Package initialization, VERSION
│   │   ├── project.py             # FMOD project facade (186 lines) ← UPDATED v0.5.0
│   │   ├── naming.py              # Pattern-based name parsing (710 lines)
│   │   ├── matcher.py             # Audio file matching logic (473 lines)
│   │   ├── core/                  # Core business logic modules ← NEW v0.5.0
│   │   │   ├── __init__.py
│   │   │   ├── xml_writer.py      # XML formatting utilities
│   │   │   ├── xml_loader.py      # XML parsing for FMOD metadata
│   │   │   ├── pending_folder_manager.py  # Transaction staging
│   │   │   ├── event_folder_manager.py    # Event folder CRUD
│   │   │   ├── asset_folder_manager.py    # Asset folder CRUD
│   │   │   ├── bus_manager.py             # Bus CRUD
│   │   │   ├── bank_manager.py            # Bank CRUD
│   │   │   ├── event_creator.py           # Event template cloning
│   │   │   └── audio_file_manager.py      # Audio file XML entries
│   │   └── gui/                   # GUI components package
│   │       ├── __init__.py
│   │       ├── main.py            # Main GUI class (355 lines)
│   │       ├── widgets.py         # Widget creation (762 lines)
│   │       ├── dialogs.py         # CRUD dialogs (699 lines)
│   │       ├── asset_dialogs.py   # Asset folder tree dialog (394 lines)
│   │       ├── drag_drop.py       # Drag & drop (641 lines)
│   │       ├── analysis.py        # Analysis workflow (239 lines)
│   │       ├── import_workflow.py # Import workflow (430 lines)
│   │       ├── settings.py        # Settings management (379 lines)
│   │       ├── utils.py           # Utility methods (378 lines)
│   │       ├── presets.py         # Preset system (757 lines)
│   │       └── preset_resolver.py # UUID resolution (349 lines)
│   │
│   ├── Script/
│   │   └── _Internal/
│   │       └── FmodImportFromJson.js  # FMOD Studio JavaScript API (424 lines)
│   │
│   ├── fmod_importer.py           # Backward-compatible entry point
│   ├── launch.bat                 # Windows launcher
│   └── launch.sh                  # Unix launcher
│
├── FmodImporterTool-Package/      # Distribution package
│   ├── README.md
│   └── docs/
│       ├── INDEX.md
│       ├── QUICKSTART.md
│       ├── VERSION.txt
│       ├── LICENSE.txt
│       └── requirements.txt
│
├── .claude/
│   └── skills/                    # Development protocol skills
│       ├── _protocol-rules.md     # Global protocol rules
│       ├── fmod-feature.md        # /fmod-feature skill
│       ├── fmod-debug.md          # /fmod-debug skill
│       ├── fmod-refactor.md       # /fmod-refactor skill
│       └── fmod-review.md         # /fmod-review skill
│
├── .github/
│   └── workflows/
│       └── build-release.yml      # CI/CD for multi-platform builds
│
├── CHANGELOG.md                   # Version history
├── docs/
│   └── ARCHITECTURE.md            # This file
└── .gitignore
```

---

## Design Principles

The FMOD Importer follows these architectural principles:

### SOLID Principles

1. **Single Responsibility Principle (SRP)**
   - Each mixin handles ONE aspect of GUI functionality
   - Core modules (project, naming, matcher) have distinct responsibilities
   - Example: WidgetsMixin creates widgets, DialogsMixin manages dialogs

2. **Open/Closed Principle (OCP)**
   - New GUI features added via new mixins (extension)
   - Existing mixins rarely modified for new features
   - Example: Adding drag & drop required new DragDropMixin, not modifying existing code

3. **Liskov Substitution Principle (LSP)**
   - Mixins are composable in any order without breaking functionality
   - No order-dependent initialization

4. **Interface Segregation Principle (ISP)**
   - Each mixin exposes focused interface
   - No "god classes" with unrelated methods
   - Example: SettingsMixin only handles settings persistence

5. **Dependency Inversion Principle (DIP)**
   - GUI layer depends on core logic (project, naming, matcher)
   - Core logic is GUI-agnostic (no tkinter imports)
   - Clean separation: GUI → Core (one-way dependency)

### Additional Principles

- **DRY (Don't Repeat Yourself)**: Shared logic extracted to utilities
- **KISS (Keep It Simple, Stupid)**: Prefer simple solutions over complex ones
- **WYSIWYG**: Code behavior matches its appearance
- **SSOT (Single Source of Truth)**: VERSION in `__init__.py` only
- **Modularity**: 800-line threshold enforced for files

---

## Module Structure

### Core Modules (Business Logic)

#### 1. **project.py** - FMODProject Facade (186 lines) ← UPDATED v0.5.0
**Purpose**: Facade for FMOD Studio project operations, delegates to core managers

**Responsibilities**:
- Load and parse FMOD Studio project files (.fspro)
- Facade pattern: delegates to specialized core modules
- Maintain backward compatibility with GUI layer
- Coordinate operations across multiple managers

**Key Methods** (unchanged - all delegate to core):
```python
__init__(project_path)                    # Load project, initialize managers
get_events_in_folder(folder_id)           # → event_folder_manager
create_event_folder(name, parent)         # → event_folder_manager
create_bank(name, parent)                 # → bank_manager
create_bus(name, parent)                  # → bus_manager
create_asset_folder(name, path)           # → asset_folder_manager
copy_event_from_template(...)             # → event_creator
commit_pending_folders()                  # → pending_folder_manager
```

**Design Patterns**:
- Facade pattern (single interface to core subsystem)
- Delegation pattern (forwards all operations)
- Lazy loading (@property decorators)

**Refactoring Impact (v0.5.0)**:
- Reduced from 1,075 → 186 lines (84% reduction)
- All business logic extracted to 9 core modules
- 100% backward compatibility (GUI unchanged)
- SOLID principles (Single Responsibility)

---

#### 1.1. **core/xml_writer.py** - XMLWriter Utilities (NEW v0.5.0)
**Purpose**: Shared XML formatting utilities

**Responsibilities**:
- Format XML attributes consistently
- Ensure consistent XML output across all managers
- Utility functions for XML generation

---

#### 1.2. **core/xml_loader.py** - XMLLoader (NEW v0.5.0)
**Purpose**: Centralized XML parsing for all FMOD metadata

**Responsibilities**:
- Parse events, banks, buses, folders from XML
- Unified XML parsing logic (DRY principle)
- Error handling for malformed XML
- Performance-optimized parsing

---

#### 1.3. **core/pending_folder_manager.py** - PendingFolderManager (NEW v0.5.0)
**Purpose**: Transaction-like staging system for folder creation

**Responsibilities**:
- Stage folder operations (create, delete) before commit
- Batch multiple operations into single XML write
- Rollback support for failed operations
- Atomicity guarantee (all or nothing)

**Design Pattern**: Pending Operations / Transaction pattern

---

#### 1.4. **core/event_folder_manager.py** - EventFolderManager (NEW v0.5.0)
**Purpose**: CRUD operations for event folders

**Responsibilities**:
- Create event folders with hierarchy
- Get events in folder (recursive)
- Validate folder structure
- XML manipulation for event folder metadata

---

#### 1.5. **core/asset_folder_manager.py** - AssetFolderManager (NEW v0.5.0)
**Purpose**: CRUD operations for asset folders

**Responsibilities**:
- Create audio asset folders
- Link asset folders to events
- Manage asset folder hierarchy
- XML manipulation for asset metadata

---

#### 1.6. **core/bus_manager.py** - BusManager (NEW v0.5.0)
**Purpose**: CRUD operations for mixer buses

**Responsibilities**:
- Create mixer buses
- Auto-detect buses from templates (v0.4.0 feature)
- Bus hierarchy management
- XML manipulation for bus metadata

---

#### 1.7. **core/bank_manager.py** - BankManager (NEW v0.5.0)
**Purpose**: CRUD operations for bank folders

**Responsibilities**:
- Create bank folders with hierarchy
- Validate bank references
- XML manipulation for bank metadata

---

#### 1.8. **core/event_creator.py** - EventCreator (NEW v0.5.0)
**Purpose**: Complex event cloning from templates

**Responsibilities**:
- Copy events with all effects and parameters
- Clone timeline modules
- Preserve event relationships
- Manual template cloning (v0.6.1 fix)

---

#### 1.9. **core/audio_file_manager.py** - AudioFileManager (NEW v0.5.0)
**Purpose**: Audio file XML entry creation

**Responsibilities**:
- Create audio file references in FMOD XML
- Link audio files to events
- Validate audio file paths

---

#### 2. **naming.py** - NamingPattern Class (710 lines)
**Purpose**: Pattern-based parsing and building of event names

**Responsibilities**:
- Define and validate naming patterns (e.g., `$prefix_$feature_$action_$variation`)
- Parse audio filenames to extract components
- Build event names from components
- Support multiple separators (underscore, dash, CamelCase)
- Strip iterator numbers (_01, _02)

**Supported Tags**:
- `$prefix` - Project prefix (user input)
- `$feature` - Feature name (user input)
- `$action` - Action/suffix (auto-extracted from filename)
- `$variation` - Variation letter A, B, C... (auto-extracted, optional)

**Key Methods**:
```python
parse_asset(asset_name, user_values)      # Parse filename to components
parse_asset_flexible(...)                 # Flexible parsing with variants
build(**components)                       # Build event name from parts
validate()                                # Validate pattern syntax
```

**Design Patterns**:
- Strategy pattern (multiple parsing strategies with fallback)
- Builder pattern (build event names from components)

---

#### 3. **matcher.py** - AudioMatcher Class (473 lines)
**Purpose**: Intelligent matching between audio files and event templates

**Responsibilities**:
- Fuzzy string matching between filenames and event names
- Feature name variant generation
- Similarity scoring (0.0 to 1.0)
- Audio file collection from directories
- Suffix extraction from basenames

**Key Methods**:
```python
normalize_string(s)                              # Normalize for fuzzy matching
get_feature_variants(feature)                    # Generate name variants
calculate_similarity(str1, str2)                 # Similarity score
collect_audio_files(directory)                   # Scan directory
match_files_to_events(audio_files, ...)          # Match files to templates
```

**Design Patterns**:
- Strategy pattern (multi-strategy suffix extraction)
- Template method (matching workflow with pluggable strategies)

---

### GUI Modules (User Interface)

The GUI uses a **Mixin Pattern** for composition:

```python
class FmodImporterGUI(
    UtilsMixin,           # Utility methods, context menus
    WidgetsMixin,         # Widget creation, placeholders
    DialogsMixin,         # CRUD dialogs for FMOD items
    AssetDialogsMixin,    # Asset folder tree dialog
    DragDropMixin,        # Drag & drop functionality
    AnalysisMixin,        # Audio file analysis workflow
    ImportMixin,          # Asset import workflow
    SettingsMixin         # Settings persistence
):
    """Main GUI class - functionality via mixins"""
    pass
```

#### Mixin Breakdown

| Mixin | Lines | Responsibility |
|-------|-------|----------------|
| **WidgetsMixin** | 762 | Widget creation, FMOD exe path field (v0.6.0) |
| **PresetsMixin** | 757 | Configuration presets save/load (v0.3.0) |
| **DialogsMixin** | 699 | CRUD dialogs for banks, buses, folders |
| **DragDropMixin** | 641 | Drag & drop between widgets, keyboard navigation |
| **ImportMixin** | 430 | Import workflow, progress dialog (v0.8.0) |
| **AssetDialogsMixin** | 394 | Asset folder tree dialog |
| **SettingsMixin** | 379 | Settings persistence (JSON in user home) |
| **UtilsMixin** | 378 | Utility methods, ProgressDialog class (v0.8.0) |
| **AnalysisMixin** | 239 | Analysis workflow, version detection (v0.7.0) |
| **PresetResolverMixin** | 349 | Smart UUID resolution for presets (v0.3.0) |

**Benefits of Mixin Pattern**:
-Each mixin < 1,000 lines (maintainable)
-Clear separation of concerns
-Easy to test individually
-Composable and reusable

---

### JavaScript Integration

#### **FmodImportFromJson.js** (424 lines)
**Purpose**: FMOD Studio JavaScript API integration

**Integration Flow**:
```
Python GUI → JSON file → FMOD Console → JavaScript → FMOD Project
```

**Responsibilities**:
- Read JSON import data from Python tool
- Use FMOD Studio JavaScript API to create events
- Assign audio files to events
- Set banks, buses, asset folders
- Return import results

---

## Design Patterns

### 1. Mixin Pattern (GUI Architecture)

**Purpose**: Compose complex GUI class from focused mixins

**Implementation**:
```python
class FmodImporterGUI(MixinA, MixinB, MixinC, ...):
    def __init__(self):
        # Initialize all mixins
        super().__init__()
```

**Benefits**:
- Avoids monolithic 3000+ line class
- Each mixin maintains SRP
- Easy to add features (new mixin)

---

### 2. Lazy Loading Pattern (Performance)

**Purpose**: Defer expensive operations until needed

**Implementation**:
```python
@property
def banks(self) -> Dict[str, Dict]:
    if self._banks is None:
        self._banks = self._load_banks()
    return self._banks
```

**Benefits**:
- Faster initial project load
- Only load what's needed
- Memory efficient

---

### 3. Caching Pattern (Performance)

**Purpose**: Cache expensive XML parsing for faster subsequent loads

**Implementation**:
```python
if cache_path.exists():
    data = load_from_cache(cache_path)  # 10x faster
else:
    data = parse_xml(xml_path)
    save_cache(data, cache_path)
```

**Benefits**:
- 10x faster project loading for large projects
- Automatic cache invalidation on XML change

---

### 4. Strategy Pattern (Flexible Matching)

**Purpose**: Multiple parsing/matching strategies with fallback

**Implementation**:
```python
def parse_asset(self, asset_name):
    # Try exact match
    result = self._parse_exact(asset_name)
    if result: return result

    # Try flexible match
    result = self._parse_flexible(asset_name)
    if result: return result

    # Try fuzzy match
    return self._parse_fuzzy(asset_name)
```

**Benefits**:
- Robust matching even with inconsistent naming
- Graceful degradation
- Easy to add new strategies

---

### 5. Builder Pattern (Event Names)

**Purpose**: Construct event names from components

**Implementation**:
```python
pattern = NamingPattern("$prefix_$feature_$action")
event_name = pattern.build(
    prefix="Sfx",
    feature="Attack",
    action="Heavy"
)
# → "Sfx_Attack_Heavy"
```

**Benefits**:
- Consistent name construction
- Validation at build time
- Flexible component combination

---

### 6. Pending Operations Pattern (Batch Processing)

**Purpose**: Batch multiple operations into single write

**Implementation**:
```python
project.create_event_folder(..., commit=False)  # Pending
project.create_asset_folder(..., commit=False)  # Pending
project.commit_pending_folders()                # Single write
```

**Benefits**:
- Performance (single XML write vs many)
- Atomicity (all or nothing)
- Cleaner undo/redo support

---

## Data Flow

### Analysis Workflow

```
User Selects Media Directory
    ↓
AnalysisMixin.analyze_media()
    ↓
AudioMatcher.collect_audio_files(directory)
    ↓
[Template Selected?]
    ├─ YES: AudioMatcher.match_files_to_events(files, template_events)
    │         ↓
    │      For each file:
    │         - NamingPattern.parse_asset(filename)
    │         - Calculate similarity with template events
    │         - Assign best match
    │
    └─ NO:  NamingPattern.parse_asset(filename) for each file
            Create event structure from pattern
    ↓
Populate preview tree with matches
    ↓
Display orphaned media (unmatched audio)
Display orphaned events (unmatched templates)
```

### Import Workflow

```
User Clicks Import
    ↓
ImportMixin.import_assets()
    ↓
Validate inputs (project, destination, patterns)
    ↓
FMODProject.commit_pending_folders()
    ↓
Build event-audio mapping from preview tree
    ↓
Generate JSON import data:
    {
      "events": [...],
      "audioFiles": [...],
      "folders": [...],
      "banks": {...},
      "buses": {...}
    }
    ↓
Save JSON to temp file
    ↓
Launch FMOD Studio with JavaScript:
    fmodstudiocl.exe --execute FmodImportFromJson.js
    ↓
JavaScript reads JSON, creates events in FMOD
    ↓
Import results returned to Python
    ↓
Display success/error messages to user
```

---

## Key Design Decisions

### ADR 001: Mixin-Based GUI Architecture

**Status**: Accepted

**Context**:
Original monolithic GUI class exceeded 3000 lines, violating maintainability principles.

**Decision**:
Split into 8 focused mixins using Python's multiple inheritance.

**Consequences**:
-Each mixin < 1000 lines
-Clear separation of concerns
-Easy to add features (new mixin)
-Slightly more complex initialization
-Need to manage method name conflicts (rare)

**Alternatives Considered**:
- Single class with better organization (rejected: still too large)
- Separate classes with delegation (rejected: more boilerplate)

---

### ADR 002: Zero External Dependencies

**Status**: Accepted

**Context**:
Wanted maximum portability and easy distribution.

**Decision**:
Use only Python standard library (tkinter for GUI, no external packages).

**Consequences**:
-Works on any Python installation (no pip install needed)
-Easy distribution (PyInstaller creates standalone exe)
-No dependency conflicts or updates needed
-Can't use advanced libraries (e.g., Qt for GUI, pandas for data)

**Alternatives Considered**:
- PyQt/PySide (rejected: external dependency, licensing)
- Electron/web-based (rejected: overhead, complexity)

---

### ADR 003: JSON Cache for Project Loading

**Status**: Accepted

**Context**:
Large FMOD projects (1000+ events) took 10+ seconds to load via XML parsing.

**Decision**:
Implement JSON cache for project metadata, fallback to XML if cache invalid.

**Consequences**:
-10x faster project loading (10s → 1s)
-Automatic cache invalidation on XML change
-Cache files take disk space (~500KB per project)
-Must maintain cache consistency

**Alternatives Considered**:
- No caching (rejected: too slow for large projects)
- SQLite cache (rejected: overkill, adds complexity)

---

### ADR 004: Pattern-Based Naming System

**Status**: Accepted

**Context**:
Different studios use different naming conventions for audio files.

**Decision**:
Implement flexible pattern system with user-defined tags (`$prefix`, `$feature`, etc.).

**Consequences**:
-Supports any naming convention
-User can customize patterns
-Multiple parsing strategies for robustness
-Learning curve for pattern syntax
-Complex parsing logic

**Alternatives Considered**:
- Hard-coded naming convention (rejected: not flexible)
- Regex patterns (rejected: too complex for users)

---

### ADR 005: Core Module Extraction (v0.5.0)

**Status**: Accepted

**Context**:
project.py exceeded 1000 lines (1,137 lines), violating modularity principle and SRP.

**Decision**:
Extract business logic into 9 specialized core modules, keep project.py as facade.

**Consequences**:
-project.py: 1,137 → 186 lines (84% reduction)
-Each core module < 400 lines (highly maintainable)
-Clear SRP (Single Responsibility Principle)
-100% backward compatible (GUI unchanged)
-Easy to test individual managers
-More files to navigate (9 core modules vs 1)
-Slightly more complex initialization

**Alternatives Considered**:
- Better organization within single file (rejected: still too large)
- Separate classes without facade (rejected: breaks existing GUI code)

---

### ADR 006: Threading for Import Progress (v0.8.0)

**Status**: Accepted

**Context**:
Import operations (1-5 minutes) froze GUI, creating poor user experience.

**Decision**:
Implement ProgressDialog with threading - run FMOD Studio execution in background thread.

**Consequences**:
-Responsive UI during import (no freeze)
-Visual feedback with animated progress bar
-Status message updates at each stage
-Better user experience
-Thread safety considerations (use tkinter.after() for UI updates)
-Cannot cancel import mid-process (prevents project corruption)

**Implementation**:
- New ProgressDialog class in utils.py
- Thread-safe UI updates via root.after(0, callback)
- Modal dialog prevents user interaction during import

**Alternatives Considered**:
- Asynchronous execution with asyncio (rejected: tkinter not async-friendly)
- Multiprocessing (rejected: overkill, harder to manage)

---

### ADR 007: Version Mismatch Detection (v0.7.0)

**Status**: Accepted

**Context**:
Users could import events with mismatched FMOD versions, causing compatibility issues.

**Decision**:
Detect FMOD project version vs executable version, warn/block import on mismatch.

**Consequences**:
-Prevents compatibility issues from version mismatches
-Clear UI feedback (version display component)
-Auto-detection when project loads
-Users must ensure version compatibility before import
-May require FMOD Studio updates

**Implementation**:
- Parse FMOD version from project XML
- Detect FMOD Studio executable version
- Display versions in main UI
- Block import if versions don't match (configurable)

**Alternatives Considered**:
- No version check (rejected: causes cryptic errors)
- Warning only without blocking (rejected: users ignore warnings)

---

### ADR 008: FMOD Executable Path on Main UI (v0.6.0)

**Status**: Accepted

**Context**:
Users with non-standard FMOD installations couldn't find executable path buried in Settings.

**Decision**:
Add FMOD Studio Executable path field with browse button to main UI.

**Consequences**:
-Easier to configure for non-standard installations
-More visible when path detection fails
-Browses all .exe files by default (user-friendly)
-Main UI slightly more cluttered
-Duplicate of Settings option (acceptable tradeoff)

**Implementation**:
- Added to WidgetsMixin in main UI layout
- Browse button with file dialog (all .exe filter)
- Synced with Settings persistence

**Alternatives Considered**:
- Keep in Settings only (rejected: not discoverable enough)
- Auto-detect only (rejected: fails for custom installations)

---

## Extension Points

### Adding New GUI Features

**Method 1: Extend Existing Mixin** (if related functionality)
```python
# In widgets.py
class WidgetsMixin:
    def _create_new_widget(self, parent):
        # Add new widget creation method
        pass
```

**Method 2: Create New Mixin** (if distinct responsibility)
```python
# Create gui/new_feature.py
class NewFeatureMixin:
    def feature_method(self):
        pass

# Update gui/main.py
class FmodImporterGUI(..., NewFeatureMixin):
    pass
```

---

### Adding New Core Functionality

**Method 1: Extend Core Module**
```python
# In project.py
class FMODProject:
    def new_operation(self):
        # Add new project operation
        pass
```

**Method 2: Create New Core Module**
```python
# Create new_module.py
class NewFeature:
    pass

# Use in GUI
from fmod_importer.new_module import NewFeature
```

---

### Adding New Patterns/Strategies

```python
# In naming.py
class NamingPattern:
    def _parse_new_strategy(self, asset_name):
        # New parsing strategy
        pass

    def parse_asset(self, asset_name):
        # Add to fallback chain
        result = self._parse_new_strategy(asset_name)
        if result: return result
        # ... existing strategies
```

---

## Known Issues and Technical Debt

### 1. ~~project.py Exceeds Size Threshold~~ RESOLVED v0.5.0
- **Status**: RESOLVED
- **Resolution**: Extracted to 9 core modules, reduced from 1,075 → 186 lines

### 2. widgets.py Approaching Threshold
- **Issue**: 762 lines (95% of 800-line threshold)
- **Impact**: Close to violating modularity principle
- **Plan**: Monitor for further growth, extract if exceeds 800
- **Effort**: Medium (3-4 hours if needed)
- **Priority**: MEDIUM

### 3. presets.py Approaching Threshold
- **Issue**: 757 lines (95% of 800-line threshold)
- **Impact**: Close to violating modularity principle
- **Status**: Already extracted PresetResolver (349 lines) in v0.3.0
- **Priority**: LOW (unlikely to grow significantly)

### 4. No Automated Tests
- **Issue**: No unit or integration tests
- **Impact**: Manual testing only, risk of regressions
- **Plan**: Add pytest infrastructure and core module tests
- **Effort**: High (1-2 days)
- **Priority**: HIGH (now more feasible with modular core)

### 5. Error Messages Not Centralized
- **Issue**: Error message strings duplicated across files
- **Impact**: Inconsistency, harder to update messages
- **Plan**: Create error_messages.py constants file
- **Effort**: Medium (2-3 hours)
- **Priority**: LOW

---

## Future Improvements

### Short-Term (Next Month)

1. **Refactor project.py**
   - Extract XML handler module
   - Extract cache manager module
   - Target: < 500 lines per module

2. **Add CHANGELOG Automation**
   - Automatically update CHANGELOG from git commits
   - Parse conventional commit messages

3. **Improve Documentation**
   - Add examples to complex function docstrings
   - Create video tutorials for common workflows

### Medium-Term (Next Quarter)

1. **Test Infrastructure**
   - Add pytest framework
   - Unit tests for core modules (project, naming, matcher)
   - Integration tests for workflows

2. **Performance Optimization**
   - Profile analysis and import workflows
   - Optimize slow operations
   - Consider threading for long operations

3. **Plugin Architecture**
   - Allow custom import strategies
   - Support for custom naming patterns
   - Extension hooks for advanced users

### Long-Term (Next Year)

1. **Database Integration**
   - Store project metadata in SQLite
   - Faster queries and analysis
   - Historical tracking of imports

2. **Advanced Matching**
   - Machine learning for improved matching
   - User feedback to train matcher
   - Support for more complex naming patterns

3. **Cloud Integration**
   - Sync settings across machines
   - Collaborative workflows
   - Cloud storage for templates

---

## Development Protocol

See `.claude/skills/` for comprehensive development protocol including:

- `/fmod-feature` - Workflow for adding new features
- `/fmod-debug` - Structured debugging process
- `/fmod-refactor` - Code refactoring guidelines
- `/fmod-review` - Code review checklist

**Principles**:
- SOLID, DRY, KISS, WYSIWYG, SSOT
- 800-line file threshold
- Conventional commits
- Comprehensive documentation

---

## References

- [FMOD Studio API Documentation](https://www.fmod.com/docs/2.02/studio/)
- [Python tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Document History**:
- 2024-12-20: Initial creation as part of development protocol implementation
