# FMOD Importer Architecture

**Last Updated**: 2024-12-20
**Version**: 0.1.9 (development)

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
- **Architecture Pattern**: Mixin-based composition for GUI, modular core logic
- **Lines of Code**: ~8,000 Python LOC
- **Platforms**: Windows, macOS, Linux (cross-platform)

---

## Project Structure

```
fmod-importer/
├── FmodImporter-Dev/              # Main development directory
│   ├── fmod_importer/             # Core Python package
│   │   ├── __init__.py            # Package initialization, VERSION
│   │   ├── project.py             # FMOD project XML manipulation (1,075 lines)
│   │   ├── naming.py              # Pattern-based name parsing (710 lines)
│   │   ├── matcher.py             # Audio file matching logic (473 lines)
│   │   └── gui/                   # GUI components package
│   │       ├── __init__.py
│   │       ├── main.py            # Main GUI class (355 lines)
│   │       ├── widgets.py         # Widget creation (709 lines)
│   │       ├── dialogs.py         # CRUD dialogs (699 lines)
│   │       ├── asset_dialogs.py   # Asset folder tree dialog (394 lines)
│   │       ├── drag_drop.py       # Drag & drop (641 lines)
│   │       ├── analysis.py        # Analysis workflow (239 lines)
│   │       ├── import_workflow.py # Import workflow (430 lines)
│   │       ├── settings.py        # Settings management (379 lines)
│   │       └── utils.py           # Utility methods (378 lines)
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

#### 1. **project.py** - FMODProject Class (1,075 lines)
**Purpose**: FMOD Studio project XML manipulation and metadata management

**Responsibilities**:
- Load and parse FMOD Studio project files (.fspro)
- XML manipulation for Events, Banks, Buses, Asset Folders
- Cache system for performance optimization
- CRUD operations for project entities
- Pending folder management

**Key Methods**:
```python
__init__(project_path)                    # Load project with caching
get_events_in_folder(folder_id)           # Get events recursively
create_event_folder(name, parent)         # Create event folder
create_bank(name, parent)                 # Create bank
create_bus(name, parent)                  # Create bus
create_asset_folder(name, path)           # Create asset folder
copy_event_from_template(...)             # Clone event with effects
commit_pending_folders()                  # Write pending folders to XML
```

**Design Patterns**:
- Lazy loading (@property decorators)
- Caching pattern (JSON cache for fast loading)
- Pending operations (batch folder creation)

**Known Issues**:
- ⚠️ File exceeds 800-line threshold (1,075 lines)
- 🔧 **Planned**: Extract XML handling and caching to separate modules

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
| **WidgetsMixin** | 709 | Widget creation, placeholder management, UI layout |
| **DialogsMixin** | 699 | CRUD dialogs for banks, buses, folders |
| **DragDropMixin** | 641 | Drag & drop between widgets, keyboard navigation |
| **ImportMixin** | 430 | Import workflow, JSON generation, FMOD integration |
| **AssetDialogsMixin** | 394 | Asset folder tree dialog |
| **SettingsMixin** | 379 | Settings persistence (JSON in user home) |
| **UtilsMixin** | 378 | Utility methods, context menus |
| **AnalysisMixin** | 239 | Audio analysis workflow, matching |

**Benefits of Mixin Pattern**:
- ✅ Each mixin < 1,000 lines (maintainable)
- ✅ Clear separation of concerns
- ✅ Easy to test individually
- ✅ Composable and reusable

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
- ✅ Each mixin < 1000 lines
- ✅ Clear separation of concerns
- ✅ Easy to add features (new mixin)
- ⚠️ Slightly more complex initialization
- ⚠️ Need to manage method name conflicts (rare)

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
- ✅ Works on any Python installation (no pip install needed)
- ✅ Easy distribution (PyInstaller creates standalone exe)
- ✅ No dependency conflicts or updates needed
- ⚠️ Can't use advanced libraries (e.g., Qt for GUI, pandas for data)

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
- ✅ 10x faster project loading (10s → 1s)
- ✅ Automatic cache invalidation on XML change
- ⚠️ Cache files take disk space (~500KB per project)
- ⚠️ Must maintain cache consistency

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
- ✅ Supports any naming convention
- ✅ User can customize patterns
- ✅ Multiple parsing strategies for robustness
- ⚠️ Learning curve for pattern syntax
- ⚠️ Complex parsing logic

**Alternatives Considered**:
- Hard-coded naming convention (rejected: not flexible)
- Regex patterns (rejected: too complex for users)

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

### 1. project.py Exceeds Size Threshold
- **Issue**: 1,075 lines (exceeds 800-line threshold)
- **Impact**: Violates modularity, harder to maintain
- **Plan**: Extract XML handling and caching to separate modules
- **Effort**: Medium (4-6 hours)
- **Priority**: HIGH

### 2. Duplicate normalize_string() Function
- **Issue**: Same function in naming.py and matcher.py
- **Impact**: DRY violation, maintenance burden
- **Plan**: Extract to shared utils module
- **Effort**: Low (30 minutes)
- **Priority**: MEDIUM

### 3. No Automated Tests
- **Issue**: No unit or integration tests
- **Impact**: Manual testing only, risk of regressions
- **Plan**: Add pytest infrastructure and core module tests
- **Effort**: High (1-2 days)
- **Priority**: MEDIUM

### 4. Error Messages Not Centralized
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
