# Skill: /fmod-refactor

Improves code structure, reduces complexity, and enforces SOLID principles without changing functional behavior.

## Objective

Restructure code to improve maintainability, readability, and modularity while preserving existing behavior.

## When to Use This Skill

- ✅ Code smell detected (duplication, complexity, excessive size)
- ✅ File exceeds 800 lines
- ✅ SOLID/DRY/KISS principle violations
- ✅ User requests "refactor", "clean up", "restructure", "improve code"
- ❌ Not for bugs (use `/fmod-debug`)
- ❌ Not for new features (use `/fmod-feature`)

## Workflow

### Step 1: Refactoring Target Identification

**Actions**:

1. **Identify code smell or architectural problem**:
   - File too large (>800 lines)?
   - Function too complex (>50 lines, nesting >3)?
   - Duplicated code (3+ occurrences)?
   - SOLID violation (mixed responsibilities)?
   - God class (too many unrelated methods)?
   - Tight coupling between modules?

2. **Measure current state**:
   ```bash
   # Line counts
   wc -l fmod_importer/**/*.py

   # Check specific file
   wc -l fmod_importer/project.py
   # Output: 1075 fmod_importer/project.py

   # Find large functions
   grep -n "^    def " fmod_importer/project.py | wc -l
   ```

3. **Define success criteria**:
   - Target line count for files
   - Maximum complexity metrics
   - SOLID principles improved
   - Specific duplications eliminated

4. **Determine scope**:
   - Single file?
   - Multiple files?
   - Entire module?
   - Specific class/function?

**Checklist**:
- [ ] Code smell identified and documented
- [ ] Current state measured (line counts, complexity)
- [ ] Success criteria defined
- [ ] Scope determined

**Refactoring Triggers** (see `_protocol-rules.md`):
- File >800 lines
- Function >50 lines
- Nesting depth >3 levels
- Parameters >5
- Code duplication 3+ times
- GUI code in core modules
- Business logic in GUI

---

### Step 2: Impact Analysis

**Actions**:

1. **Identify all dependents of code to be refactored**:
   ```bash
   # Find imports of target module
   grep -r "from fmod_importer.project import" fmod_importer/
   grep -r "import fmod_importer.project" fmod_importer/

   # Find usages of target class
   grep -r "FMODProject" fmod_importer/
   ```

2. **Check for potential breaking changes**:
   - Will public API change?
   - Are function signatures modified?
   - Data structure changed?
   - External behavior affected?

3. **Plan backward-compatible approach if possible**:
   - Keep old API temporarily with deprecation warnings?
   - Create adapter/wrapper for compatibility?
   - Gradual migration possible?

4. **Assess risk level**:
   - **Low**: Internal changes only, no API changes
   - **Medium**: API changes but backward-compatible possible
   - **High**: Breaking changes necessary

**Checklist**:
- [ ] All dependents identified
- [ ] Potential breaking changes listed
- [ ] Backward-compatible approach planned if possible
- [ ] Risk level assessed

**Risk Assessment Template**:
```
Refactoring: [Description]

Dependents:
- [Module1]: Uses [API/class/function]
- [Module2]: Uses [API/class/function]
- ...

Breaking changes:
- [Change 1]: [Impact]
- [Change 2]: [Impact]

Mitigation:
- [Strategy to maintain compatibility]

Risk level: [Low/Medium/High]
```

---

### Step 3: Refactoring Strategy Selection

**Common Strategies**:

#### Strategy 1: Extract Function
**When**: Function too long (>50 lines) or repeated logic

**Pattern**:
```python
# Before: Long function
def process_data(data):
    # 80 lines of mixed logic
    # - validation
    # - transformation
    # - calculation
    # - formatting

# After: Extracted functions
def process_data(data):
    validated = validate_data(data)
    transformed = transform_data(validated)
    calculated = calculate_results(transformed)
    return format_results(calculated)

def validate_data(data):
    # 10 lines of validation

def transform_data(data):
    # 15 lines of transformation

def calculate_results(data):
    # 20 lines of calculation

def format_results(data):
    # 10 lines of formatting
```

**Benefits**: Readability, testability, reusability

---

#### Strategy 2: Extract Class
**When**: Cohesive group of functions and data

**Pattern**:
```python
# Before: Functions scattered in module
def load_cache(path):
    # ...

def save_cache(data, path):
    # ...

def invalidate_cache(path):
    # ...

# After: Extracted class
class CacheManager:
    def __init__(self, cache_path):
        self.cache_path = cache_path

    def load(self):
        # ...

    def save(self, data):
        # ...

    def invalidate(self):
        # ...
```

**Benefits**: Encapsulation, state management, SRP

---

#### Strategy 3: Extract Mixin
**When**: Large GUI class with distinct responsibilities

**Pattern**:
```python
# Before: God class
class FmodGUI:
    # 2000 lines
    # - widgets creation
    # - dialog handling
    # - drag & drop
    # - analysis
    # - import
    # - settings

# After: Mixin pattern (already used in project!)
class FmodGUI(WidgetsMixin, DialogsMixin, DragDropMixin,
              AnalysisMixin, ImportMixin, SettingsMixin):
    # 200 lines - just coordination
    pass

class WidgetsMixin:
    # 700 lines - widget creation only

class DialogsMixin:
    # 600 lines - dialog handling only
# ... etc
```

**Benefits**: Separation of responsibilities, maintainability, modularity

---

#### Strategy 4: Extract Module
**When**: File >800 lines with distinct responsibilities

**Pattern**:
```python
# Before: project.py (1075 lines)
# - FMODProject class
# - XML parsing functions
# - Cache management
# - Event manipulation
# - Folder management

# After: Split into modules
# project.py (420 lines) - Core FMODProject class
# xml_handler.py (350 lines) - XML operations
# cache.py (240 lines) - Cache management
```

**Benefits**: Smaller files, SRP, modularity

---

#### Strategy 5: Introduce Parameter Object
**When**: Function with >5 parameters

**Pattern**:
```python
# Before: Too many parameters
def create_event(self, name, path, bank_id, bus_id, asset_folder, color, priority):
    # ...

# After: Parameter object
class EventConfig:
    def __init__(self, name, path, bank_id, bus_id, asset_folder,
                 color=None, priority=0):
        self.name = name
        self.path = path
        self.bank_id = bank_id
        self.bus_id = bus_id
        self.asset_folder = asset_folder
        self.color = color
        self.priority = priority

def create_event(self, config: EventConfig):
    # ...

# Usage
config = EventConfig(
    name="Event1",
    path="/path",
    bank_id="{guid}",
    bus_id="{guid}",
    asset_folder="/assets"
)
project.create_event(config)
```

**Benefits**: Readability, extensibility, centralized validation

---

#### Strategy 6: Move Method
**When**: Method in wrong class

**Pattern**:
```python
# Before: Method in wrong class
class FmodGUI:
    def parse_event_name(self, name):  # ← Business logic in GUI!
        # ...

# After: Moved to appropriate class
class NamingPattern:
    def parse_event_name(self, name):  # ← Logic in core module
        # ...

class FmodGUI:
    def on_analyze(self):
        # Call core module
        result = self.pattern.parse_event_name(name)
```

**Benefits**: Separation of concerns, testability, DIP

---

#### Strategy 7: Consolidate Duplicate Code
**When**: Same code appears 3+ times

**Pattern**:
```python
# Before: Duplicated in 3 files
# File1:
def normalize(s):
    return s.lower().replace('_', '').replace('-', '')

# File2:
def normalize(s):
    return s.lower().replace('_', '').replace('-', '')

# File3:
def normalize(s):
    return s.lower().replace('_', '').replace('-', '')

# After: Consolidated in utils
# utils.py:
def normalize_string(s: str) -> str:
    """Normalize string for comparison"""
    return s.lower().replace('_', '').replace('-', '')

# All files import from utils:
from fmod_importer.utils import normalize_string
```

**Benefits**: DRY, SSOT, easier maintenance

---

#### Strategy 8: Replace Conditional with Polymorphism
**When**: Long if/elif chains (>5 conditions)

**Pattern**:
```python
# Before: Long conditional
def process(item_type, data):
    if item_type == 'event':
        # 20 lines of event processing
    elif item_type == 'bank':
        # 20 lines of bank processing
    elif item_type == 'bus':
        # 20 lines of bus processing
    elif item_type == 'folder':
        # 20 lines of folder processing
    # ... more conditions

# After: Polymorphism or dict dispatch
PROCESSORS = {
    'event': EventProcessor(),
    'bank': BankProcessor(),
    'bus': BusProcessor(),
    'folder': FolderProcessor(),
}

def process(item_type, data):
    processor = PROCESSORS.get(item_type)
    if not processor:
        raise ValueError(f"Unknown type: {item_type}")
    return processor.process(data)
```

**Benefits**: Extensibility (OCP), readability, maintainability

---

**Checklist**:
- [ ] Refactoring strategy selected
- [ ] Appropriate pattern chosen
- [ ] Benefits clear

---

### Step 4: Implementation by Milestones

#### Milestone 1: Preparation

**Actions**:
1. **Create new structure in parallel** (without deleting old):
   ```python
   # Create new module/class ALONGSIDE existing code
   # Example: Extracting XML handler from project.py

   # Step 1: Create new file
   # fmod_importer/xml_handler.py
   class XMLHandler:
       """New extracted XML handling logic"""
       @staticmethod
       def parse_workspace(path):
           # Copy XML parsing logic from project.py
           pass

       @staticmethod
       def save_xml(element, path):
           # Copy XML saving logic from project.py
           pass
   ```

2. **Implement new structure with complete docstrings**:
   - All new functions/classes fully documented
   - Type hints on all parameters
   - Examples in docstrings

3. **Test new structure in isolation** (if possible):
   ```python
   # Manual testing in REPL
   from fmod_importer.xml_handler import XMLHandler
   handler = XMLHandler()
   result = handler.parse_workspace("test.fspro")
   ```

**Checklist M1**:
- [ ] New structure created (files/classes)
- [ ] Logic copied and adapted
- [ ] Complete docstrings
- [ ] Type hints added
- [ ] Tested in isolation if possible
- [ ] Old code INTACT (not yet deleted)

---

#### Milestone 2: Migration

**Actions**:
1. **Update references to use new structure**:
   ```python
   # project.py - before
   class FMODProject:
       def load(self):
           # Old: Direct XML parsing
           tree = ET.parse(self.workspace_path)
           # ... 50 lines of XML parsing

   # project.py - after
   from fmod_importer.xml_handler import XMLHandler

   class FMODProject:
       def __init__(self):
           self.xml_handler = XMLHandler()

       def load(self):
           # New: Delegate to XML handler
           tree = self.xml_handler.parse_workspace(self.workspace_path)
   ```

2. **Keep old code temporarily with deprecation warnings** (if breaking change):
   ```python
   # Old API kept temporarily
   def old_method(self):
       import warnings
       warnings.warn(
           "old_method is deprecated, use new_method instead",
           DeprecationWarning,
           stacklevel=2
       )
       return self.new_method()
   ```

3. **Test each migration step**:
   - Test after each file migration
   - Verify behavior unchanged
   - Check for regressions

**Checklist M2**:
- [ ] References updated to new structure
- [ ] Old code kept temporarily if necessary
- [ ] Each migration tested
- [ ] No regressions detected
- [ ] External behavior unchanged

---

#### Milestone 3: Cleanup

**Actions**:
1. **Remove old code once migration complete**:
   ```python
   # Remove old methods/classes that are no longer used
   # Remove deprecation warnings if all usages migrated
   ```

2. **Update all imports**:
   ```python
   # Update __init__.py exports
   # fmod_importer/__init__.py
   from .project import FMODProject
   from .xml_handler import XMLHandler  # New export
   from .cache import CacheManager      # New export
   ```

3. **Clean up unused imports**:
   ```bash
   # Remove unused imports from refactored files
   # Check with grep that nothing breaks
   ```

4. **Verify final behavior**:
   - Test all workflows end-to-end
   - Verify no regressions
   - Check error handling still works

**Checklist M3**:
- [ ] Old code removed
- [ ] Imports updated
- [ ] Unused imports cleaned up
- [ ] Final behavior verified
- [ ] End-to-end tests passed

---

### Step 5: Quality Checks

**Before committing, verify**:

#### Improved Metrics
```bash
# Check new line counts
wc -l fmod_importer/*.py fmod_importer/gui/*.py

# Compare to before:
# project.py: 1075 → 420 lines ✅
# xml_handler.py: 0 → 350 lines (new)
# cache.py: 0 → 240 lines (new)
```

- [ ] **Line counts** reduced or better distributed
- [ ] **Complexity** reduced (less nesting, shorter functions)
- [ ] **Duplication** eliminated

#### Behavior Unchanged
```
CRITICAL: Behavior must be identical before/after refactoring
```

- [ ] **Manual tests** identical to pre-refactoring behavior
- [ ] **No regressions** in existing functionality
- [ ] **Error handling** preserved
- [ ] **Edge cases** still handled correctly

#### SOLID Improved
- [ ] **SRP**: Each class/module has clear single responsibility
- [ ] **OCP**: Code more extensible
- [ ] **LSP**: Logical hierarchies
- [ ] **ISP**: Focused interfaces
- [ ] **DIP**: Dependencies towards abstractions

#### Documentation
- [ ] **Complete docstrings** on new code
- [ ] **Inline comments** for non-obvious logic
- [ ] **Module docstrings** explain purpose

**Quality Checklist**:
- [ ] Metrics improved (line counts, complexity)
- [ ] Behavior strictly identical
- [ ] SOLID principles improved
- [ ] Complete documentation

---

### Step 6: Commits by Milestone

**Strategy**: Commits by milestone for clear tracking

```bash
# Milestone 1: Preparation
git add fmod_importer/xml_handler.py fmod_importer/cache.py
git commit -m "refactor: Extract XML handler and cache manager modules

Created new focused modules for XML operations and cache management.
Extracted from project.py to improve Single Responsibility Principle.

- xml_handler.py: 350 lines (XML parsing, saving)
- cache.py: 240 lines (Cache loading, management)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Milestone 2: Migration
git add fmod_importer/project.py
git commit -m "refactor: Update project.py to use extracted modules

FMODProject now delegates XML and cache operations to
specialized modules instead of handling directly.

- project.py: 1075 → 420 lines
- Maintains identical external behavior
- Improves modularity and testability

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Milestone 3: Cleanup
git add fmod_importer/__init__.py fmod_importer/project.py
git commit -m "refactor: Finalize module extraction and cleanup

- Updated package exports for new modules
- Removed old XML/cache code from project.py
- Cleaned up unused imports

All tests passing, no behavior changes.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Format** (see `_protocol-rules.md`):
```
refactor: Brief description of refactoring

Detailed explanation:
- What was refactored
- Why (what problem it solves)
- How (what strategy used)
- Impact (metrics before/after)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Version Bumping**:
- Refactoring generally = **NO version bump**
- EXCEPT if major architectural change = **Minor bump**
- Breaking change = **Major bump** (avoid with backward compatibility)

---

### Step 7: Technical Documentation

**Actions**:

1. **Create/Update ARCHITECTURE.md** (if major change):
   ```markdown
   # FMOD Importer Architecture

   ## Recent Refactoring (v0.2.0)

   ### Project Module Split (2024-12-20)

   **Motivation**: project.py exceeded 1075 lines, violating 800-line threshold

   **Approach**: Extract Module strategy

   **Result**:
   - project.py: 1075 → 420 lines (Core orchestration)
   - xml_handler.py: 350 lines (XML operations)
   - cache.py: 240 lines (Cache management)

   **Benefits**:
   - Improved Single Responsibility Principle
   - Better testability (modules can be tested independently)
   - Easier to maintain and extend
   ```

2. **Update CHANGELOG.md** (if significant refactoring):
   ```markdown
   ## [Unreleased]
   ### Changed
   - Refactored project module into focused sub-modules (XML, cache)
   - Improved modularity and maintainability
   - No behavior changes
   ```

3. **Document design decisions** (for major refactorings):
   ```markdown
   # docs/ADR/001-split-project-module.md

   # ADR 001: Split Project Module

   ## Status
   Accepted

   ## Context
   project.py grew to 1075 lines, exceeding 800-line threshold.
   Mixed responsibilities: core logic, XML handling, caching.

   ## Decision
   Split into three focused modules using Extract Module pattern.

   ## Consequences
   Positive:
   - Improved SRP
   - Better testability
   - Easier navigation

   Negative:
   - More files to manage
   - Slightly more complex imports

   ## Alternatives Considered
   - Keep as-is with better organization
   - Extract only XML handling
   ```

**Documentation Checklist**:
- [ ] ARCHITECTURE.md created/updated if major change
- [ ] CHANGELOG.md updated if significant refactoring
- [ ] ADR (Architecture Decision Record) created if important decision
- [ ] README.md updated if user-facing impact

---

## Complete Examples

### Example 1: Extract Module (project.py → split)

**Problem**: project.py = 1075 lines (exceeds 800)

**Analysis**:
- Mixed responsibilities: Core FMODProject + XML parsing + Cache management
- Dependents: All GUI mixins import FMODProject
- Risk: Medium (public API must remain compatible)

**Strategy**: Extract Module

**Implementation**:

**M1 - Preparation**:
```python
# Create fmod_importer/xml_handler.py
"""
XML Handler Module

Handles FMOD Studio XML file parsing and manipulation.
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path

class XMLHandler:
    """Handles XML operations for FMOD project files"""

    @staticmethod
    def parse_workspace(workspace_path: Path) -> ET.Element:
        """
        Parse FMOD workspace XML file.

        Args:
            workspace_path: Path to workspace XML

        Returns:
            Root XML element

        Raises:
            FileNotFoundError: If workspace file doesn't exist
            ET.ParseError: If XML is malformed
        """
        if not workspace_path.exists():
            raise FileNotFoundError(f"Workspace not found: {workspace_path}")

        tree = ET.parse(workspace_path)
        return tree.getroot()

    @staticmethod
    def save_xml(element: ET.Element, output_path: Path) -> None:
        """
        Save XML element to file with pretty formatting.

        Args:
            element: XML element to save
            output_path: Path to output file
        """
        # Pretty print XML
        xml_str = minidom.parseString(
            ET.tostring(element)
        ).toprettyxml(indent="  ")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)

# Create fmod_importer/cache.py
"""
Cache Module

Handles FMOD project cache loading and management.
"""
import json
from pathlib import Path
from typing import Optional, Dict

class CacheManager:
    """Handles FMOD project cache operations"""

    def __init__(self, cache_path: Path):
        """
        Initialize cache manager.

        Args:
            cache_path: Path to cache JSON file
        """
        self.cache_path = cache_path
        self._cache_data = None

    def load(self) -> Optional[Dict]:
        """
        Load cache from JSON file.

        Returns:
            Cache data dictionary if exists, None otherwise
        """
        if not self.cache_path.exists():
            return None

        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                self._cache_data = json.load(f)
            return self._cache_data
        except (json.JSONDecodeError, IOError):
            return None

    def save(self, data: Dict) -> None:
        """
        Save data to cache.

        Args:
            data: Dictionary to cache
        """
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        self._cache_data = data
```

**Commit M1**:
```bash
git add fmod_importer/xml_handler.py fmod_importer/cache.py
git commit -m "refactor: Extract XML handler and cache manager modules"
```

**M2 - Migration**:
```python
# Update fmod_importer/project.py
from .xml_handler import XMLHandler
from .cache import CacheManager

class FMODProject:
    """FMOD Studio project representation"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.project_dir = self.project_path.parent

        # Use extracted modules
        self.xml_handler = XMLHandler()
        self.cache_manager = CacheManager(self.cache_path)

        # Load project
        if self.cache_path.exists():
            self._load_from_cache()
        else:
            self._load_from_xml()

    def _load_from_cache(self):
        """Load project from cache"""
        data = self.cache_manager.load()
        if data:
            self._populate_from_cache(data)
        else:
            self._load_from_xml()

    def _load_from_xml(self):
        """Load project from XML files"""
        # Use XML handler
        self.workspace = self.xml_handler.parse_workspace(self.workspace_path)
        # ... rest of loading logic

    def save(self):
        """Save project changes"""
        # Use XML handler
        self.xml_handler.save_xml(self.workspace, self.workspace_path)

    # ... rest of FMODProject methods (now focused on core logic)
```

**Commit M2**:
```bash
git add fmod_importer/project.py
git commit -m "refactor: Update project.py to use extracted modules"
```

**M3 - Cleanup**:
```python
# Update fmod_importer/__init__.py
from .project import FMODProject
from .xml_handler import XMLHandler
from .cache import CacheManager
from .naming import NamingPattern
from .matcher import AudioMatcher

__all__ = ['FMODProject', 'XMLHandler', 'CacheManager',
           'NamingPattern', 'AudioMatcher']

# Remove old XML/cache code from project.py
# (Already done in M2, just verify clean)
```

**Commit M3**:
```bash
git add fmod_importer/__init__.py
git commit -m "refactor: Finalize module extraction and update exports"
```

**Documentation**:
```markdown
# docs/ARCHITECTURE.md
## Module Structure (Updated 2024-12-20)

### Core Modules
- **project.py** (420 lines): Core FMODProject class, orchestrates operations
- **xml_handler.py** (350 lines): XML parsing and manipulation
- **cache.py** (240 lines): Cache loading and management
- **naming.py** (710 lines): Naming pattern parsing
- **matcher.py** (473 lines): Audio file matching

### Design Patterns
- **Delegation Pattern**: FMODProject delegates XML/cache ops to specialized modules
- **Single Responsibility**: Each module has one clear purpose
```

---

### Example 2: Consolidate Duplicate Code

**Problem**: `normalize_string()` duplicated in naming.py and matcher.py

**Analysis**:
```python
# naming.py:245
def normalize_string(s: str) -> str:
    return s.lower().replace('_', '').replace('-', '')

# matcher.py:89
def normalize_string(s: str) -> str:
    return s.lower().replace('_', '').replace('-', '')
```

**Strategy**: Consolidate Duplicate Code

**Implementation**:

**M1 - Create shared utility**:
```python
# Create/update fmod_importer/utils.py
"""
Utility Functions

Shared utility functions used across modules.
"""

def normalize_string(s: str) -> str:
    """
    Normalize string for comparison.

    Removes underscores, hyphens, and converts to lowercase
    for consistent string matching.

    Args:
        s: String to normalize

    Returns:
        Normalized string

    Examples:
        >>> normalize_string("Attack_Heavy")
        "attackheavy"
        >>> normalize_string("Jump-High")
        "jumphigh"
    """
    return s.lower().replace('_', '').replace('-', '')
```

**M2 - Update references**:
```python
# naming.py
from .utils import normalize_string

class NamingPattern:
    def _compare_strings(self, s1, s2):
        # Use shared utility
        return normalize_string(s1) == normalize_string(s2)

# matcher.py
from .utils import normalize_string

class AudioMatcher:
    def calculate_similarity(self, str1, str2):
        # Use shared utility
        norm1 = normalize_string(str1)
        norm2 = normalize_string(str2)
        # ... similarity calculation
```

**M3 - Remove duplicates**:
```python
# Remove local normalize_string definitions from naming.py and matcher.py
# (Already done in M2)
```

**Commits**:
```bash
git commit -m "refactor: Extract normalize_string to shared utils module"
git commit -m "refactor: Update naming and matcher to use shared normalize_string"
```

---

## Anti-Patterns to Avoid

### ❌ BAD: Mixing Refactoring with Feature/Bug Fix
```bash
git commit -m "refactor: Split module AND add new feature AND fix bug"
# ← Doing too much!
```

### ✅ GOOD: Separate Refactoring
```bash
git commit -m "refactor: Split project module into focused sub-modules"
# Later, separate commits:
git commit -m "feat: Add export feature"
git commit -m "fix: Handle null values"
```

---

### ❌ BAD: Changing Behavior During Refactoring
```python
# Refactoring + changing logic
def process_data(data):
    # Before: Returns list
    # After: Returns dict ← CHANGED BEHAVIOR!
    return {item['id']: item for item in data}
```

### ✅ GOOD: Identical Behavior
```python
# Refactoring without behavior change
def process_data(data):
    # Still returns list (behavior unchanged)
    # But now delegates to helper functions
    validated = _validate_data(data)
    transformed = _transform_data(validated)
    return transformed
```

---

### ❌ BAD: Deleting Old Code Immediately
```python
# Delete old code before migration complete
# Breaks all dependents!
```

### ✅ GOOD: Gradual Migration
```python
# Keep old code during migration
def old_method(self):
    warnings.warn("Use new_method instead", DeprecationWarning)
    return self.new_method()

# Remove only when all usages migrated
```

---

## Quick Reference

### Complete Checklist

```
Phase 1: Identification
□ Code smell identified
□ Current state measured
□ Success criteria defined
□ Scope determined

Phase 2: Impact Analysis
□ Dependents identified
□ Breaking changes listed
□ Backward compatibility planned
□ Risk level assessed

Phase 3: Strategy Selection
□ Strategy chosen (Extract Function/Class/Module, etc.)
□ Appropriate pattern
□ Clear benefits

Phase 4: Implementation
M1 - Preparation:
  □ New structure created
  □ Logic implemented
  □ Complete docstrings
  □ Tested in isolation
  □ Old code intact

M2 - Migration:
  □ References updated
  □ Old code kept if necessary
  □ Tested step by step
  □ No regressions

M3 - Cleanup:
  □ Old code removed
  □ Imports updated
  □ Behavior verified

Phase 5: Quality Checks
□ Metrics improved
□ Behavior identical (CRITICAL)
□ SOLID improved
□ Complete documentation

Phase 6: Commits
□ Commits per milestone
□ Descriptive messages
□ Correct format

Phase 7: Documentation
□ ARCHITECTURE.md updated if major
□ CHANGELOG.md updated
□ ADR created if important decision
```

### Decision Tree - Which Strategy?

```
Code Smell
    │
    ├─ Function >50 lines
    │  └─ Extract Function
    │
    ├─ Cohesive group of functions/data
    │  └─ Extract Class
    │
    ├─ File >800 lines, multiple responsibilities
    │  └─ Extract Module
    │
    ├─ Large GUI class
    │  └─ Extract Mixin
    │
    ├─ Function >5 parameters
    │  └─ Introduce Parameter Object
    │
    ├─ Method in wrong class
    │  └─ Move Method
    │
    ├─ Code duplicated 3+ times
    │  └─ Consolidate Duplicate Code
    │
    └─ Long if/elif chain (>5)
       └─ Replace Conditional with Polymorphism
```

### Version Bumping for Refactoring

| Change | Version Bump |
|--------|--------------|
| Internal refactoring, no API change | None |
| Significant architectural change | Minor |
| Breaking API change | Major (avoid with compatibility layer) |
