# Skill: /fmod-feature

Implement a new feature for the FMOD Importer following SOLID, DRY, KISS principles and the project's mixin architecture.

## Objective

Create robust, well-documented and maintainable features with structured commits by milestone.

## When to Use This Skill

- ✅ User requests a new feature
- ✅ Adding user-facing or internal features
- ✅ Extending existing capabilities
- ❌ Not for bugs (use `/fmod-debug`)
- ❌ Not for restructuring (use `/fmod-refactor`)

## Workflow

### Step 1: Requirements Analysis

**Actions**:
1. Read and fully understand the user request
2. Identify affected modules:
   - GUI only?
   - Core logic only?
   - GUI + Core?
   - New module needed?
3. Search for similar existing features to reuse patterns
4. Check if external dependencies are needed (avoid if possible - stdlib only!)
5. Ask clarification questions if requirements are ambiguous

**Checklist**:
- [ ] Requirements clear and complete
- [ ] Affected modules identified
- [ ] Existing patterns researched
- [ ] No new external dependencies (or justified)

**Questions to Ask** (via AskUserQuestion if needed):
- How does this feature integrate with the existing workflow?
- Are there specific edge cases?
- What's the priority (MVP vs complete feature)?
- How to test this feature manually?

---

### Step 2: Architecture Planning

**Actions**:
1. **Determine placement**:
   - New mixin? → If new distinct GUI responsibility
   - Extend existing mixin? → If extending existing responsibility
   - New core module? → If new business logic
   - Extend existing core module? → If extending existing logic

2. **Check line counts of target files**:
   ```bash
   # Check current line count
   wc -l fmod_importer/gui/[target_mixin].py
   ```
   - If >700 lines → Plan extraction BEFORE adding feature
   - If >800 lines → BLOCKER: Refactor first with `/fmod-refactor`

3. **Identify reusable components to create**:
   - Reusable widgets
   - Utility functions
   - Shared classes/patterns

4. **Design interfaces** (function signatures, class APIs):
   ```python
   # Example interface design
   class NewFeatureMixin:
       def feature_method(self, param1: Type1, param2: Type2) -> ReturnType:
           """Brief description"""
           pass
   ```

5. **Verify SOLID compliance**:
   - **SRP**: Does the feature have a single, well-defined responsibility?
   - **OCP**: Can we extend existing code without modifying it?
   - **LSP**: Are the new mixins composable?
   - **ISP**: Is the interface focused (not a god class)?
   - **DIP**: Do we depend on abstractions, not implementations?

**Checklist**:
- [ ] Placement determined (mixin/module)
- [ ] Line counts verified (< 800 lines after addition)
- [ ] Reusable components identified
- [ ] Interfaces designed with type hints
- [ ] SOLID compliance verified

**Decision Tree - Placement**:
```
Feature Description
    │
    ├─ Pure business logic (XML, parsing, matching)
    │  └─ Add/extend core module (project.py, naming.py, matcher.py)
    │
    ├─ User interface (widgets, dialogs)
    │  └─ Add/extend GUI mixin
    │     │
    │     ├─ Extension of existing responsibility
    │     │  └─ Extend existing mixin (ex: WidgetsMixin for new widget)
    │     │
    │     └─ New distinct responsibility
    │        └─ Create new mixin
    │
    └─ Both (logic + UI)
       └─ Start with core, then GUI
```

---

### Step 3: Implementation by Milestones

#### Milestone 1: Core Logic (no GUI)

**Actions**:
1. Implement business logic in appropriate core module
2. Write complete docstrings (follow standard `_protocol-rules.md`)
3. Add type hints for all parameters and returns
4. Implement appropriate error handling
5. Test manually in Python REPL if possible

**Example**:
```python
# fmod_importer/project.py
def filter_events_by_bank(self, bank_id: str) -> List[Dict]:
    """
    Filter events belonging to a specific bank.

    Args:
        bank_id: GUID of the bank to filter by

    Returns:
        List of event dictionaries belonging to the bank

    Raises:
        ValueError: If bank_id is invalid or bank doesn't exist

    Examples:
        >>> project.filter_events_by_bank("{guid-123}")
        [{'id': '{event-1}', 'name': 'Event1'}, ...]
    """
    if not bank_id:
        raise ValueError("bank_id cannot be empty")

    if bank_id not in self.banks:
        raise ValueError(f"Bank {bank_id} not found in project")

    events = []
    for event in self.events.values():
        if event.get('output_bank') == bank_id:
            events.append(event)

    return events
```

**Checklist M1**:
- [ ] Core logic implemented
- [ ] Complete docstrings with Args/Returns/Raises/Examples
- [ ] Type hints on all parameters
- [ ] Error handling present
- [ ] Manually tested if possible

#### Milestone 2: GUI Integration

**Actions**:
1. Create/extend appropriate mixin
2. Connect core logic to GUI events
3. Add placeholder management if necessary
4. Follow existing widget patterns (see `widgets.py`)
5. Implement error handling with user-friendly messagebox
6. Test end-to-end interaction

**Example**:
```python
# fmod_importer/gui/widgets.py (WidgetsMixin)
def _create_bank_filter(self, parent):
    """
    Create bank filter dropdown widget.

    Allows user to filter events by selected bank.

    Args:
        parent: Parent tkinter widget
    """
    frame = ttk.LabelFrame(parent, text="Filter by Bank", padding=10)

    # Bank selection dropdown
    self.bank_filter_var = tk.StringVar()
    bank_dropdown = ttk.Combobox(
        frame,
        textvariable=self.bank_filter_var,
        state="readonly",
        width=30
    )

    # Populate with available banks
    if self.project:
        bank_names = [
            bank['name'] for bank in self.project.banks.values()
        ]
        bank_dropdown['values'] = ['All Banks'] + bank_names

    bank_dropdown.current(0)  # Select "All Banks" by default
    bank_dropdown.grid(row=0, column=0, padx=5, pady=5)

    # Apply filter button
    apply_btn = ttk.Button(
        frame,
        text="Apply Filter",
        command=self._apply_bank_filter
    )
    apply_btn.grid(row=0, column=1, padx=5, pady=5)

    return frame

def _apply_bank_filter(self):
    """Apply bank filter to event tree"""
    if not self.project:
        messagebox.showwarning(
            "No Project",
            "Please load a project first"
        )
        return

    selected_bank = self.bank_filter_var.get()

    try:
        if selected_bank == 'All Banks':
            # Show all events
            self._populate_event_tree(self.project.events.values())
        else:
            # Find bank by name
            bank = next(
                b for b in self.project.banks.values()
                if b['name'] == selected_bank
            )

            # Filter events
            filtered = self.project.filter_events_by_bank(bank['id'])
            self._populate_event_tree(filtered)

    except Exception as e:
        messagebox.showerror(
            "Filter Failed",
            f"Failed to apply bank filter:\n{str(e)}"
        )
```

**Checklist M2**:
- [ ] Mixin created/extended
- [ ] Core logic connected to GUI events
- [ ] Error handling with user-friendly messagebox
- [ ] Existing patterns followed
- [ ] Tested end-to-end

#### Milestone 3: Complete Documentation

**Actions**:
1. **README.md**: Add feature documentation
   - "Description" section: Mention new feature
   - "Usage" section: Usage instructions
   - "Troubleshooting" section: Potential errors

2. **CHANGELOG.md**: Add entry under "Added"
   ```markdown
   ## [Unreleased]
   ### Added
   - Event filtering by bank name in UI
   ```

3. **VERSION**: Bump minor version
   ```python
   # fmod_importer/__init__.py
   VERSION = "0.2.0"  # Was "0.1.8"
   ```

4. **Docstrings**: Verify all new functions/classes have complete docstrings

5. **Inline comments**: Add only for non-obvious logic

**README.md Addition Template**:
```markdown
### Bank Filtering

Filter events by bank to focus on specific audio banks during workflow.

**How to use**:
1. Load your FMOD project
2. In the filter section, select a bank from the dropdown
3. Click "Apply Filter" to show only events in that bank
4. Select "All Banks" to remove filter

**Example**:
Select "SFX_Bank" to see only sound effect events assigned to that bank.

**Troubleshooting**:
- **Filter button disabled**: Load a project first
- **Bank list empty**: Project has no banks defined
```

**Checklist M3**:
- [ ] README.md updated (Description, Usage, Troubleshooting)
- [ ] CHANGELOG.md updated under "Added"
- [ ] VERSION bumped (minor for feat)
- [ ] All docstrings complete
- [ ] Inline comments only if necessary

---

### Step 4: Quality Checks

**Before committing, verify**:

#### Architecture
- [ ] **SOLID compliance**:
  - [ ] SRP: One responsibility per class/function
  - [ ] OCP: Extension through composition
  - [ ] DIP: No concrete GUI↔Core dependencies

- [ ] **Separation of responsibilities**:
  - [ ] Business logic in core modules
  - [ ] Interface in GUI mixins
  - [ ] No GUI code in core
  - [ ] No complex business logic in GUI

#### Code Quality
- [ ] **DRY**: No code duplication
  - If similar code exists, extract reusable function
  - Check duplication between new and old modules

- [ ] **Line Counts**:
  ```bash
  wc -l fmod_importer/gui/*.py fmod_importer/*.py
  ```
  - [ ] No file >800 lines
  - [ ] If approaching 750, suggest future refactoring

- [ ] **Error Handling**:
  - [ ] try/except around risky operations
  - [ ] User-friendly error messages (messagebox)
  - [ ] No bare except clauses

- [ ] **Type Hints**:
  - [ ] All parameters and returns typed
  - [ ] Import typing if necessary

- [ ] **Naming**:
  - [ ] Clear and descriptive names
  - [ ] Follow Python conventions (snake_case)
  - [ ] No obscure abbreviations

#### Documentation
- [ ] **Docstrings**:
  - [ ] All public functions/classes documented
  - [ ] Standard format (Args, Returns, Raises, Examples)
  - [ ] Explain WHY, not just WHAT

- [ ] **README.md**:
  - [ ] Feature mentioned in Description
  - [ ] Usage instructions added
  - [ ] Troubleshooting updated

- [ ] **CHANGELOG.md**:
  - [ ] Entry under "Added" for new version
  - [ ] Clear feature description

- [ ] **VERSION**:
  - [ ] Bumped correctly (feat = minor bump)

#### Manual Testing
- [ ] Feature works end-to-end
- [ ] Edge cases tested
- [ ] Error handling verified (trigger errors)
- [ ] No regressions on existing features

---

### Step 5: Commits by Milestone

**Strategy**: Commits grouped by milestone (user configuration)

#### Option 1: Separate Commits per Milestone
```bash
# Milestone 1: Core
git add fmod_importer/project.py
git commit -m "feat(core): Add event filtering by bank name (v0.2.0)

Implements filter_events_by_bank() method to filter events
belonging to a specific bank. Includes comprehensive error
handling and validation."

# Milestone 2: GUI
git add fmod_importer/gui/widgets.py
git commit -m "feat(gui): Add bank filter widget to UI

Adds dropdown filter to allow users to filter events by bank.
Integrates with core filtering logic from project module."

# Milestone 3: Documentation
git add README.md CHANGELOG.md fmod_importer/__init__.py
git commit -m "docs: Document bank filtering feature

Updates README with usage instructions, adds CHANGELOG entry,
and bumps version to 0.2.0."
```

#### Option 2: Single Commit (for simple features)
```bash
git add fmod_importer/project.py fmod_importer/gui/widgets.py README.md CHANGELOG.md fmod_importer/__init__.py
git commit -m "feat: Add bank filtering feature (v0.2.0)

Implements event filtering by bank name:
- Core filtering logic in project module
- GUI dropdown filter widget
- Full documentation and troubleshooting"
```

**Choice Rule**:
- 3 commits if milestones are distinct and feature is complex
- 1 commit if feature is simple and coherent

**Commit format** (see `_protocol-rules.md`):
```
feat(scope): Brief description (vX.Y.Z)

Detailed explanation:
- What was added
- Why it was added
- How it works
```

---

### Step 6: Post-Implementation

**Proactive actions**:

1. **Check thresholds** and suggest if necessary:
   ```bash
   wc -l fmod_importer/gui/*.py | sort -rn | head -5
   ```

   If files approach thresholds, suggest:
   ```
   [INFO] widgets.py approaching 750 lines

   Current state:
   - widgets.py: 745 lines

   Suggested improvement:
   - Consider planning refactoring before hitting 800-line threshold
   - Possible extraction: widget factory functions to separate module

   Benefit:
   - Maintains modularity
   - Prevent future violations

   Estimated effort: Low
   Skill to use: /fmod-refactor
   ```

2. **Identify related improvements** (optional):
   - Similar features that could benefit from the same pattern
   - Existing code that could be refactored with new pattern
   - Documentation that could be improved

3. **Note technical debt** (if created):
   - TODOs for future improvements
   - Known limitations
   - Potential optimizations

**Post-Implementation Checklist**:
- [ ] Line thresholds checked, suggestions made if approaching limits
- [ ] Related improvements identified
- [ ] Technical debt documented if applicable

---

## Automatic Triggers

### During Planning

#### File Approaching 800 Lines
```
[RECOMMEND] Threshold: Target file approaching 800-line limit

Current state:
- [filename].py: [current] lines
- Adding [feature] will add ~[estimated] lines

Suggested improvement:
- Refactor [filename].py BEFORE adding new feature
- Use /refactor to split into smaller modules

Benefit:
- Maintain modularity
- Prevent exceeding 800-line threshold
- Easier to add feature after refactoring

Estimated effort: Medium
Skill to use: /fmod-refactor
```

### During Implementation

#### Duplication Detected
```
[SUGGEST] Pattern: Similar code found in existing module

Current state:
- New code similar to [existing_module.py:line_range]

Suggested improvement:
- Extract common logic to shared utility function
- Location: fmod_importer/gui/utils.py or fmod_importer/utils.py

Benefit:
- DRY principle
- Single source of truth
- Easier maintenance

Estimated effort: Low
```

#### GUI Code in Core Module
```
[VIOLATION] Architecture: GUI code in core module

Current state:
- [core_module.py] imports tkinter or uses GUI components

Suggested improvement:
- Move GUI logic to appropriate mixin
- Core module should be GUI-agnostic
- Pass data to GUI layer, don't create widgets in core

Benefit:
- Respect Dependency Inversion Principle
- Testability
- Separation of concerns

Estimated effort: Low
Skill to use: /fmod-refactor
```

---

## Complete Examples

### Example 1: Simple Feature (1 Milestone)

**Request**: "Add a 'Clear All' button to reset all fields"

**Execution**:

1. **Analysis**:
   - GUI-only feature
   - Extends WidgetsMixin
   - Simple: just reset form fields

2. **Planning**:
   - Placement: WidgetsMixin (extends existing)
   - widgets.py: 709 lines → ~720 after (OK)
   - No core logic needed

3. **Implementation**:
   ```python
   # widgets.py
   def _create_clear_button(self, parent):
       """Create clear all button"""
       btn = ttk.Button(
           parent,
           text="Clear All",
           command=self._clear_all_fields
       )
       return btn

   def _clear_all_fields(self):
       """Reset all input fields to default state"""
       self.project_path_var.set("")
       self.media_dir_var.set("")
       self.prefix_var.set("")
       self.feature_var.set("")
       # ... reset other fields
       messagebox.showinfo("Cleared", "All fields reset")
   ```

4. **Documentation**:
   - README: Add to "UI Controls" section
   - CHANGELOG: "Added Clear All button to reset form"
   - VERSION: 0.1.8 → 0.1.9 (minor bump)

5. **Commit**:
   ```bash
   git commit -m "feat(gui): Add Clear All button to reset form (v0.1.9)"
   ```

### Example 2: Complex Feature (3 Milestones)

**Request**: "Add ability to export import results to JSON file"

**Execution**:

1. **Analysis**:
   - Core + GUI feature
   - Core: Export logic (JSON serialization)
   - GUI: Export button, file dialog
   - Pattern exists: Settings save/load

2. **Planning**:
   - Core: Add export_results() to FMODProject
   - GUI: Add export button to ImportMixin
   - project.py: 1075 lines → Suggest refactor first (>800)
   - Alternative: Add to separate export.py module

3. **Implementation M1 (Core)**:
   ```python
   # fmod_importer/export.py (NEW MODULE)
   """Export functionality for import results"""
   import json
   from pathlib import Path
   from typing import Dict

   def export_results_to_json(results: Dict, output_path: str) -> None:
       """
       Export import results to JSON file.

       Args:
           results: Import results dictionary
           output_path: Path to output JSON file

       Raises:
           IOError: If file cannot be written
           ValueError: If results is empty

       Examples:
           >>> export_results_to_json({'events': [...]}, 'results.json')
       """
       if not results:
           raise ValueError("Results cannot be empty")

       output_file = Path(output_path)

       try:
           with open(output_file, 'w', encoding='utf-8') as f:
               json.dump(results, f, indent=2)
       except IOError as e:
           raise IOError(f"Failed to write to {output_path}: {e}")
   ```

   **Commit M1**:
   ```bash
   git commit -m "feat(core): Add JSON export functionality (v0.2.0)"
   ```

4. **Implementation M2 (GUI)**:
   ```python
   # import_workflow.py (ImportMixin)
   def _create_export_button(self, parent):
       """Create export results button"""
       btn = ttk.Button(
           parent,
           text="Export Results",
           command=self._export_results
       )
       return btn

   def _export_results(self):
       """Export import results to JSON file"""
       from tkinter import filedialog
       from fmod_importer.export import export_results_to_json

       if not hasattr(self, 'import_results') or not self.import_results:
           messagebox.showwarning(
               "No Results",
               "No import results available to export.\n"
               "Run import first."
           )
           return

       filename = filedialog.asksaveasfilename(
           title="Export Results",
           defaultextension=".json",
           filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
       )

       if filename:
           try:
               export_results_to_json(self.import_results, filename)
               messagebox.showinfo(
                   "Success",
                   f"Results exported successfully to:\n{filename}"
               )
           except Exception as e:
               messagebox.showerror(
                   "Export Failed",
                   f"Failed to export results:\n{str(e)}"
               )
   ```

   **Commit M2**:
   ```bash
   git commit -m "feat(gui): Add export results button to import workflow"
   ```

5. **Implementation M3 (Docs)**:
   - README: Add "Exporting Results" section
   - CHANGELOG: Add under "Added"
   - VERSION: 0.1.8 → 0.2.0

   **Commit M3**:
   ```bash
   git commit -m "docs: Document JSON export feature"
   ```

6. **Post-Implementation**:
   ```
   [INFO] Created new export module

   Good architectural decision:
   - Avoided adding to project.py (already >1000 lines)
   - Created focused export.py module
   - Maintains SRP

   Future consideration:
   - Could add other export formats (CSV, XML) to same module
   ```

---

## Anti-Patterns to Avoid

### ❌ BAD: Everything in One Commit
```bash
# Commits 1000 lines of changes without structure
git commit -m "Add feature"
```

### ✅ GOOD: Structured Commits by Milestone
```bash
git commit -m "feat(core): Add core logic (v0.2.0)"
git commit -m "feat(gui): Add UI components"
git commit -m "docs: Document new feature"
```

---

### ❌ BAD: No Documentation
```python
def filter_events(self, bank_id):
    # No docstring
    return [e for e in self.events if e['bank'] == bank_id]
```

### ✅ GOOD: Complete Documentation
```python
def filter_events_by_bank(self, bank_id: str) -> List[Dict]:
    """
    Filter events belonging to specific bank.

    Args:
        bank_id: GUID of bank

    Returns:
        List of event dictionaries

    Raises:
        ValueError: If bank_id invalid
    """
    if not bank_id:
        raise ValueError("bank_id cannot be empty")

    return [e for e in self.events.values() if e.get('output_bank') == bank_id]
```

---

### ❌ BAD: GUI Logic in Core Module
```python
# project.py
import tkinter as tk
from tkinter import messagebox

def create_event(self):
    messagebox.showinfo("Success", "Event created")  # GUI in core!
```

### ✅ GOOD: Core/GUI Separation
```python
# project.py (core)
def create_event(self, name: str) -> Dict:
    """Create event, return result"""
    # Pure logic, no GUI
    event = {'id': generate_id(), 'name': name}
    self.events[event['id']] = event
    return event

# gui/dialogs.py
def create_event_dialog(self):
    """GUI for creating event"""
    name = self.name_entry.get()
    try:
        event = self.project.create_event(name)  # Call core
        messagebox.showinfo("Success", f"Created {event['name']}")  # GUI here
    except Exception as e:
        messagebox.showerror("Error", str(e))
```

---

### ❌ BAD: No Error Handling
```python
def load_file(self, path):
    with open(path) as f:  # What if file doesn't exist?
        return f.read()
```

### ✅ GOOD: Appropriate Error Handling
```python
def load_file(self, path: str) -> str:
    """Load file with proper error handling"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {path}")
    except PermissionError:
        raise PermissionError(f"Cannot read file: {path}")
    except Exception as e:
        raise IOError(f"Error reading file {path}: {e}")
```

---

## Quick Reference

### Complete Checklist

```
Phase 1: Analysis
□ Requirements understood
□ Affected modules identified
□ Existing patterns researched
□ Questions asked if ambiguous

Phase 2: Planning
□ Placement determined
□ Line counts verified (<800)
□ Reusable components identified
□ Interfaces designed
□ SOLID compliance verified

Phase 3: Implementation
M1 - Core Logic:
  □ Logic implemented
  □ Complete docstrings
  □ Type hints
  □ Error handling
  □ Manually tested

M2 - GUI Integration:
  □ Mixin created/extended
  □ Core connected to GUI
  □ User-friendly error handling
  □ Patterns followed
  □ Tested end-to-end

M3 - Documentation:
  □ README.md updated
  □ CHANGELOG.md updated
  □ VERSION bumped
  □ Docstrings complete

Phase 4: Quality Checks
□ SOLID compliance
□ DRY (no duplication)
□ Line counts <800
□ Error handling
□ Type hints
□ Clear naming
□ Complete documentation
□ Manual testing

Phase 5: Commits
□ Commits per milestone or single
□ Conventional Commits format
□ Descriptive messages
□ Version bump included

Phase 6: Post-Implementation
□ Thresholds verified
□ Suggestions made if necessary
□ Related improvements noted
```

### Decision Trees

**Core vs GUI?**
```
Feature involves...
├─ Data processing, XML, parsing, matching → Core
├─ Widgets, dialogs, user interaction → GUI
└─ Both → Core first, then GUI
```

**New Mixin vs Extend Existing?**
```
Responsibility is...
├─ Extension of existing mixin responsibility → Extend
└─ New distinct responsibility → New mixin
```

**1 Commit vs 3 Commits?**
```
Feature is...
├─ Simple, cohesive (<50 lines total) → 1 commit
└─ Complex, distinct milestones → 3 commits
```
