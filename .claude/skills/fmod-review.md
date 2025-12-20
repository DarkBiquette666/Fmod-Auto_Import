# Skill: /fmod-review

Complete code review for quality, adherence to principles, and identification of improvement opportunities.

## Objective

Systematically analyze code to identify problems, principle violations, and improvement opportunities.

## When to Use This Skill

- ✅ User requests "review", "check code", "audit", "analyze"
- ✅ Before major release
- ✅ After adding important features
- ✅ Periodically to maintain quality
- ✅ When code quality is uncertain
- ❌ Not for fixing bugs (use `/fmod-debug`)
- ❌ Not for implementing features (use `/fmod-feature`)

## Workflow

### Step 1: Scope Definition

**Actions**:

1. **Determine review scope**:
   - **Single file**: Review a specific file
   - **Module**: Review all files in a module (e.g., gui/)
   - **Entire codebase**: Complete project review
   - **Recent changes**: Review recent commits

2. **Define review depth**:
   - **Quick scan** (5-10 min): Basic metrics, obvious violations
   - **Standard review** (20-30 min): Complete checks, SOLID, documentation
   - **Deep analysis** (1+ hour): Detailed architectural analysis

3. **Identify specific concerns** (if applicable):
   - Security vulnerabilities?
   - Performance issues?
   - Architecture compliance?
   - Documentation gaps?
   - Test coverage?

**Checklist**:
- [ ] Scope defined (file, module, codebase, recent changes)
- [ ] Depth selected (quick, standard, deep)
- [ ] Specific concerns identified

**Scope Examples**:
```bash
# Single file
/review fmod_importer/project.py

# Module
/review fmod_importer/gui/

# Entire codebase
/review

# Recent changes
/review --since="2024-12-01"
```

---

### Step 2: Automated Checks

#### 2.1 Line Count Analysis

**Actions**:
```bash
# Get line counts for all Python files
wc -l fmod_importer/**/*.py | sort -rn

# Identify files exceeding thresholds
wc -l fmod_importer/**/*.py | awk '$1 > 800 {print $0}'
```

**Thresholds** (see `_protocol-rules.md`):
- 750 lines → `[INFO]` Plan refactoring
- 800 lines → `[RECOMMEND]` Refactor now
- 900 lines (mixin) → `[RECOMMEND]` Urgent
- 1000 lines → `[CRITICAL]` Absolute maximum

**Output Template**:
```markdown
### Line Count Analysis

| File | Lines | Status |
|------|-------|--------|
| project.py | 1075 | ❌ EXCEEDS 800 |
| naming.py | 710 | ⚠️ APPROACHING 800 |
| widgets.py | 709 | ⚠️ APPROACHING 800 |
| matcher.py | 473 | ✅ OK |
| dialogs.py | 699 | ✅ OK |

**Recommendations**:
- `[CRITICAL]` project.py: Refactor immediately (1075 lines)
- `[INFO]` naming.py: Plan refactoring before adding more (710 lines)
- `[INFO]` widgets.py: Plan refactoring before adding more (709 lines)
```

---

#### 2.2 Architecture Validation

**Actions**:

1. **Check GUI mixin pattern**:
   ```bash
   # Check FmodImporterGUI inherits from mixins
   grep -n "class FmodImporterGUI" fmod_importer/gui/main.py

   # Should show:
   # class FmodImporterGUI(UtilsMixin, WidgetsMixin, ...)
   ```

2. **Check core/GUI separation**:
   ```bash
   # Core modules should NOT import GUI
   grep -r "import tkinter\|from tkinter" fmod_importer/project.py fmod_importer/naming.py fmod_importer/matcher.py

   # Should be empty (no GUI imports in core)
   ```

3. **Check circular dependencies**:
   ```bash
   # Check for circular imports
   # Manually trace import chains
   grep -r "^from \|^import " fmod_importer/*.py
   ```

**Output Template**:
```markdown
### Architecture Validation

✅ **Mixin Pattern**: Correctly implemented
- FmodImporterGUI composes 8 mixins
- Each mixin < 1000 lines

❌ **Separation of Concerns**:
- VIOLATION: project.py imports tkinter (line 45)
- Recommendation: Remove GUI dependencies from core modules

✅ **No Circular Dependencies**: No cycles detected
```

---

#### 2.3 Code Duplication Detection

**Actions**:

1. **Search for similar functions**:
   ```bash
   # Find duplicate function names
   grep -rh "^    def " fmod_importer/ | sort | uniq -c | sort -rn | awk '$1 > 1'

   # Find similar code blocks (manual inspection)
   # Look for patterns like normalize, validate, parse
   ```

2. **Search for repeated string literals**:
   ```bash
   # Find repeated string literals (potential constants)
   grep -roh '"[^"]\{10,\}"' fmod_importer/ | sort | uniq -c | sort -rn | head -20
   ```

3. **Identify repeated patterns**:
   - Similar try/except blocks
   - Similar validation logic
   - Similar widget creation

**Output Template**:
```markdown
### Code Duplication

❌ **Duplicated Functions**:
- `normalize_string()` appears in:
  - naming.py:245
  - matcher.py:89
- **Recommendation**: Extract to utils.py

❌ **Duplicated String Literals**:
- "File not found:" appears 7 times
- **Recommendation**: Create error message constants

✅ **No major pattern duplication** detected
```

---

### Step 3: SOLID Principles Review

#### 3.1 Single Responsibility Principle (SRP)

**Questions to Ask**:
- Does each class have ONE clear responsibility?
- Do methods do ONE coherent thing?
- Do mixins address ONE aspect of functionality?

**Checks**:
```python
# Example: Check if class has multiple unrelated responsibilities
class FMODProject:
    # ✅ GOOD: All methods relate to project management
    def load_project(self): ...
    def save_project(self): ...
    def get_events(self): ...

    # ❌ BAD: Unrelated responsibility
    def export_to_pdf(self): ...  # ← Export is separate concern!
```

**Output Template**:
```markdown
### SRP Compliance

✅ **FMODProject**: Single responsibility (project management)
✅ **NamingPattern**: Single responsibility (pattern parsing)
⚠️ **WidgetsMixin**: Approaching multi-responsibility (widgets + placeholders + help dialogs)
  - **Suggestion**: Consider extracting help dialogs to separate mixin
```

---

#### 3.2 Open/Closed Principle (OCP)

**Questions to Ask**:
- Are new features added by composition/extension?
- Is modification of existing code avoided?

**Checks**:
```python
# ✅ GOOD: Extension via composition (mixin pattern)
class FmodGUI(ExistingMixin, NewFeatureMixin):  # ← Extended without modifying
    pass

# ❌ BAD: Modifying existing code for new feature
class FmodGUI:
    def existing_method(self):
        # ... original code
        # NEW FEATURE CODE ADDED HERE ← Modification!
```

**Output Template**:
```markdown
### OCP Compliance

✅ **Mixin Architecture**: Excellent OCP compliance
- New features added via new mixins
- Existing mixins rarely modified

⚠️ **Core Modules**: Some modification for features
- Suggestion: Consider plugin/extension architecture for project.py
```

---

#### 3.3 Liskov Substitution Principle (LSP)

**Questions to Ask**:
- Are mixins composable without conflicts?
- Are inheritance hierarchies logical?

**Checks**:
```python
# ✅ GOOD: Mixins can be composed in any order
class FmodGUI(MixinA, MixinB, MixinC):  # Works
class FmodGUI(MixinC, MixinA, MixinB):  # Also works

# ❌ BAD: Order matters (fragile inheritance)
class FmodGUI(MixinA, MixinB):  # Works
class FmodGUI(MixinB, MixinA):  # Breaks!
```

**Output Template**:
```markdown
### LSP Compliance

✅ **Mixin Composability**: All mixins composable without conflicts
✅ **No problematic inheritance** detected
```

---

#### 3.4 Interface Segregation Principle (ISP)

**Questions to Ask**:
- Are there "god classes" with unrelated methods?
- Are interfaces focused?

**Checks**:
```python
# ❌ BAD: God class with unrelated methods
class Utilities:
    def format_xml(self): ...      # XML formatting
    def send_email(self): ...      # Email (unrelated!)
    def calculate_hash(self): ...  # Cryptography (unrelated!)

# ✅ GOOD: Focused interfaces
class XMLFormatter:
    def format_xml(self): ...

class EmailService:
    def send_email(self): ...
```

**Output Template**:
```markdown
### ISP Compliance

✅ **Focused Mixins**: Each mixin has cohesive interface
✅ **No god classes** detected

⚠️ **utils.py**: 378 lines of unrelated utilities
- **Suggestion**: Split into focused modules (xml_utils, string_utils, etc.)
```

---

#### 3.5 Dependency Inversion Principle (DIP)

**Questions to Ask**:
- Does core logic depend on abstractions?
- Does GUI depend on core, not the reverse?

**Checks**:
```bash
# ❌ BAD: Core imports GUI
grep "import tkinter" fmod_importer/project.py
# Should be empty!

# ✅ GOOD: GUI imports core
grep "from fmod_importer.project import FMODProject" fmod_importer/gui/
# Should have results
```

**Output Template**:
```markdown
### DIP Compliance

✅ **Dependency Direction**: GUI → Core (correct)
❌ **Concrete Dependencies**: project.py directly imports XML library
- **Suggestion**: Consider abstraction layer for XML operations
```

---

### Step 4: DRY/KISS/SSOT Analysis

#### 4.1 DRY (Don't Repeat Yourself)

**Checks**:
```bash
# Find duplicate code blocks (manual)
# Look for similar patterns in:
grep -n "def normalize" fmod_importer/*.py
grep -n "def validate" fmod_importer/*.py
grep -n "try:" fmod_importer/gui/*.py | wc -l  # Many try blocks?
```

**Output Template**:
```markdown
### DRY Violations

❌ **Duplicate Logic**:
1. String normalization in naming.py and matcher.py
2. File validation in 5 different files
3. Error message formatting repeated 12 times

**Recommendations**:
- Extract normalize_string() to utils.py
- Create FileValidator class
- Create ErrorFormatter utility
```

---

#### 4.2 KISS (Keep It Simple, Stupid)

**Checks**:
- Overly complex solutions?
- Premature optimization?
- Unclear variable names?

**Examples**:
```python
# ❌ BAD: Overly complex
result = reduce(lambda acc, x: acc + [x] if x not in acc else acc, items, [])

# ✅ GOOD: Simple and clear
result = list(set(items))  # Remove duplicates

# Or even better:
unique_items = list(set(items))  # Clear variable name
```

**Output Template**:
```markdown
### KISS Violations

⚠️ **Complex Implementations**:
- matcher.py:156: Overly complex list comprehension (3 levels nested)
  - Suggestion: Break into multiple steps with clear variable names

✅ **Generally simple** code throughout project
```

---

#### 4.3 SSOT (Single Source of Truth)

**Checks**:
```bash
# Find VERSION definitions
grep -rn "VERSION\s*=" fmod_importer/

# Should be only in __init__.py
```

**Output Template**:
```markdown
### SSOT Violations

✅ **VERSION**: Defined only in __init__.py
✅ **Configuration**: Centralized in settings
❌ **Error Messages**: Duplicated across files
- **Recommendation**: Create error_messages.py constants file
```

---

### Step 5: Documentation Review

#### 5.1 Docstring Completeness

**Checks**:
```bash
# Find functions without docstrings
grep -Pzo "def \w+\([^)]*\):\n(?!\s+\"\"\")" fmod_importer/*.py

# Count functions with vs without docstrings
total_funcs=$(grep -rc "^    def " fmod_importer/ | awk -F: '{sum+=$2} END {print sum}')
documented=$(grep -rc '"""' fmod_importer/ | awk -F: '{sum+=$2} END {print sum}')
```

**Output Template**:
```markdown
### Docstring Completeness

**Coverage**: 87% (145/167 functions documented)

❌ **Missing Docstrings**:
- project.py:234: _internal_helper()
- matcher.py:89: _parse_suffix()
- widgets.py:456: _update_placeholder()

**Quality Issues**:
- ⚠️ naming.py:45: Missing Args section
- ⚠️ project.py:123: Missing Examples section
- ⚠️ matcher.py:200: Missing Raises section

**Recommendations**:
- Add docstrings to all public functions
- Complete Args/Returns/Raises sections
- Add Examples for complex functions
```

---

#### 5.2 README Accuracy

**Checks**:
- Do README features match code reality?
- Are usage instructions current?
- Is troubleshooting comprehensive?

**Manual Review**:
- Test examples from README
- Verify all mentioned features exist
- Check for undocumented features

**Output Template**:
```markdown
### README Accuracy

✅ **Features**: All mentioned features exist and work
⚠️ **Undocumented Features**:
- Bank filtering (added in v0.2.0) not in README
- JSON export (recent) not documented

❌ **Outdated Information**:
- Screenshot shows old UI (pre-v0.1.5)
- Installation instructions mention deprecated dependency

**Recommendations**:
- Add bank filtering to "Features" section
- Add JSON export to "Usage" section
- Update screenshot to current UI
- Remove deprecated dependency from requirements
```

---

#### 5.3 CHANGELOG Maintenance

**Checks**:
```bash
# Check if CHANGELOG exists
ls CHANGELOG.md

# Check format
head -20 CHANGELOG.md

# Check recent versions documented
git tag | tail -5  # Recent tags
grep "\[0.1." CHANGELOG.md  # Versions in changelog
```

**Output Template**:
```markdown
### CHANGELOG Status

❌ **CHANGELOG.md**: Does not exist
- **Recommendation**: Create CHANGELOG.md following Keep a Changelog format

**Suggested Initial Content**:
``markdown
# Changelog

## [Unreleased]

## [0.1.8] - 2024-12-19
### Fixed
- Improve template duplication robustness

[... historical versions based on git log]
``
```

---

### Step 6: Code Quality Metrics

#### 6.1 Complexity Indicators

**Checks**:

1. **Long Functions** (>50 lines):
   ```bash
   # Find long functions (manual or script)
   # Count lines between "def" and next "def" or class end
   ```

2. **Deep Nesting** (>3 levels):
   ```python
   # Look for deeply nested code
   if condition1:
       if condition2:
           if condition3:
               if condition4:  # ← Too deep!
   ```

3. **Many Parameters** (>5):
   ```bash
   # Find functions with many parameters
   grep -rn "def \w\+([^)]\{50,\})" fmod_importer/
   ```

**Output Template**:
```markdown
### Complexity Metrics

❌ **Long Functions**:
- project.py:156: `copy_event_from_template()` (87 lines)
- analysis.py:45: `analyze_media()` (62 lines)
- **Recommendation**: Break into smaller focused functions

⚠️ **Deep Nesting**:
- import_workflow.py:234: 4 levels of nesting
- **Recommendation**: Extract inner logic to helper methods

❌ **Too Many Parameters**:
- project.py:234: `create_event()` has 8 parameters
- **Recommendation**: Use parameter object (EventConfig)
```

---

#### 6.2 Error Handling

**Checks**:
```bash
# Find bare except clauses (bad)
grep -rn "except:" fmod_importer/

# Find try blocks without specific exceptions
grep -A1 "try:" fmod_importer/ | grep -v "except ("
```

**Output Template**:
```markdown
### Error Handling

❌ **Bare Except Clauses**:
- utils.py:89: `except:` (catches ALL exceptions including KeyboardInterrupt)
- **Recommendation**: Catch specific exceptions only

⚠️ **Generic Exception Handling**:
- project.py:156: `except Exception:` (too broad)
- **Recommendation**: Catch FileNotFoundError, IOError, etc. specifically

✅ **User-Friendly Error Messages**: Good messagebox usage throughout GUI

**Missing Error Handling**:
- naming.py:234: File open without try/except
- matcher.py:156: Division without zero check
```

---

#### 6.3 Code Style

**Checks**:
```bash
# Check for common style issues
grep -rn "import \*" fmod_importer/  # Wildcard imports (bad)
grep -rn "#.*TODO" fmod_importer/   # TODO comments
grep -rn "^\s*#" fmod_importer/ | grep -v '"""'  # Commented-out code
```

**Output Template**:
```markdown
### Code Style

✅ **Naming Conventions**: Consistent snake_case
✅ **No wildcard imports**: No `from module import *` found
⚠️ **TODO Comments**: 7 TODO comments found
- Consider creating issues for todos

❌ **Commented-Out Code**:
- widgets.py:234-245: 12 lines of commented code
- **Recommendation**: Remove or document why kept

✅ **Type Hints**: Good coverage on function signatures
```

---

### Step 7: Report Generation

**Report Structure**:

```markdown
# Code Review Report - [Scope]
Date: [YYYY-MM-DD]
Reviewer: Claude Sonnet 4.5

## Executive Summary

- **Scope**: [Files/modules reviewed]
- **Overall Quality**: [Excellent/Good/Fair/Needs Improvement]
- **Critical Issues**: [Count]
- **Recommendations**: [Count]
- **Positive Observations**: [Count]

## Summary Statistics

- Total files reviewed: X
- Total lines of code: Y
- Average file size: Z lines
- Files exceeding 800 lines: N
- Functions lacking docstrings: M
- Code duplication instances: P

## Critical Issues

### 1. [Issue Title]
- **Location**: [file:line]
- **Severity**: CRITICAL
- **Description**: [What's wrong]
- **Impact**: [How it affects code]
- **Recommendation**: [How to fix]
- **Effort**: [Low/Medium/High]
- **Skill to use**: /[skill-name]

## Architecture Feedback

### SOLID Compliance
- **SRP**: [Assessment with examples]
- **OCP**: [Assessment with examples]
- **LSP**: [Assessment with examples]
- **ISP**: [Assessment with examples]
- **DIP**: [Assessment with examples]

### Modularity
[Assessment of module organization]

### Code Organization
[Assessment of file/folder structure]

## Refactoring Opportunities

### 1. [Opportunity Title]
- **Location**: [file or module]
- **Current State**: [Description]
- **Proposed Improvement**: [What to do]
- **Benefit**: [Why it matters]
- **Effort**: [Low/Medium/High]
- **Priority**: [High/Medium/Low]
- **Skill to use**: /refactor

## Documentation Gaps

### 1. [Gap Description]
- **Location**: [file or section]
- **Missing**: [What's missing]
- **Recommendation**: [What to add]
- **Priority**: [High/Medium/Low]

## Code Quality Metrics

### File Sizes
[Table of files >750 lines]

### Duplicate Code Blocks
[List of duplicated code with locations]

### Complex Functions
[List of functions >50 lines or high cyclomatic complexity]

### Error Handling Issues
[List of bare except, missing error handling]

## Recommendations Summary

### High Priority (Do Soon)
1. [Recommendation with skill to use]
2. [Recommendation with skill to use]

### Medium Priority (Plan For)
1. [Recommendation with skill to use]
2. [Recommendation with skill to use]

### Low Priority (Nice to Have)
1. [Recommendation]
2. [Recommendation]

## Positive Observations

- [What's working well]
- [Good practices observed]
- [Architectural strengths]

## Next Steps

1. [Immediate action]
2. [Short-term improvement]
3. [Long-term goal]

---

*Review conducted using FMOD Importer Development Protocol*
*See `_protocol-rules.md` for detailed standards and guidelines*
```

---

### Step 8: Action Items and Prioritization

**Actions**:

1. **Categorize findings by priority**:
   - **CRITICAL**: Must fix (security, data loss, crashes)
   - **HIGH**: Should fix soon (violations, tech debt)
   - **MEDIUM**: Plan to fix (improvements, optimizations)
   - **LOW**: Nice to have (style, minor improvements)

2. **Create action items with recommended skills**:
   ```markdown
   ## Action Items

   ### CRITICAL
   - [ ] Fix security vulnerability in file upload (/debug)
   - [ ] Refactor project.py (1075 lines) (/refactor)

   ### HIGH
   - [ ] Extract duplicate normalize_string() (/refactor)
   - [ ] Add missing error handling in naming.py (/debug)
   - [ ] Create CHANGELOG.md (manual)

   ### MEDIUM
   - [ ] Split widgets.py before adding features (/refactor)
   - [ ] Add docstrings to 22 undocumented functions (manual)

   ### LOW
   - [ ] Update README screenshot (manual)
   - [ ] Remove commented-out code (manual)
   ```

3. **Estimate effort for each item**:
   - **Low**: < 1 hour
   - **Medium**: 1-4 hours
   - **High**: 4+ hours

4. **Recommend execution order**:
   1. Critical issues first
   2. High priority refactorings that unlock features
   3. Documentation gaps
   4. Medium/low priority improvements

**Checklist**:
- [ ] Findings categorized by priority
- [ ] Action items created with skills
- [ ] Effort estimated for each item
- [ ] Execution order recommended

---

## Complete Examples

### Example 1: Single File Review (project.py)

**Request**: `/review fmod_importer/project.py`

**Execution**:

```markdown
# Code Review Report - project.py
Date: 2024-12-20
Reviewer: Claude Sonnet 4.5

## Executive Summary

- **Scope**: fmod_importer/project.py (single file)
- **Overall Quality**: Good (needs refactoring)
- **Critical Issues**: 1
- **High Priority Recommendations**: 2
- **Positive Observations**: 4

## Summary Statistics

- Lines of code: 1075
- Functions: 34
- Classes: 1 (FMODProject)
- Docstring coverage: 94% (32/34 functions)
- Complexity: Medium-High

## Critical Issues

### 1. File Exceeds 800-Line Threshold
- **Location**: project.py (entire file)
- **Severity**: CRITICAL
- **Description**: File is 1075 lines, exceeding 800-line threshold significantly
- **Impact**: Violates modularity principle, difficult to navigate and maintain
- **Recommendation**: Split into focused modules:
  - project.py (core orchestration)
  - xml_handler.py (XML operations)
  - cache.py (caching logic)
- **Effort**: High
- **Skill to use**: /refactor

## Architecture Feedback

### SOLID Compliance
- **SRP**: ⚠️ Mixed responsibilities (project management + XML + caching)
  - Recommendation: Extract XML and cache to separate modules
- **OCP**: ✅ Good extensibility
- **DIP**: ✅ No GUI dependencies (good separation)

### Responsibilities Identified
1. Core project management (events, banks, buses, folders)
2. XML parsing and saving (50+ lines)
3. Cache loading and management (80+ lines)
4. Event manipulation
5. Folder management

**Recommendation**: Responsibility #2 and #3 should be separate modules

## Refactoring Opportunities

### 1. Extract XML Handler Module
- **Current**: XML operations scattered throughout project.py
- **Proposed**: Create xml_handler.py with XMLHandler class
- **Benefit**: SRP, easier testing, reusable
- **Effort**: Medium
- **Priority**: HIGH
- **Skill to use**: /refactor

### 2. Extract Cache Manager Module
- **Current**: Cache logic in FMODProject.__init__ and methods
- **Proposed**: Create cache.py with CacheManager class
- **Benefit**: SRP, clear cache interface
- **Effort**: Low-Medium
- **Priority**: HIGH
- **Skill to use**: /refactor

## Documentation Gaps

### 1. Missing Examples in Complex Methods
- **Methods**: copy_event_from_template(), create_event_folder()
- **Recommendation**: Add usage examples in docstrings
- **Priority**: MEDIUM

## Code Quality Metrics

### Complexity
- **Long Functions**:
  - copy_event_from_template(): 87 lines ❌
  - _load_banks(): 65 lines ⚠️
- **Recommendation**: Extract helper methods

### Error Handling
- ✅ Good try/except coverage
- ✅ User-friendly error messages
- ⚠️ One bare except clause (line 456)

## Recommendations Summary

### High Priority
1. Refactor into 3 modules (project, xml_handler, cache) - /refactor
2. Extract long functions (87 lines) into helpers - /refactor

### Medium Priority
1. Add examples to complex method docstrings - Manual
2. Replace bare except with specific exceptions - /debug

### Low Priority
1. Add type hints to 2 remaining methods - Manual

## Positive Observations

- ✅ Excellent docstring coverage (94%)
- ✅ Good separation from GUI (no tkinter imports)
- ✅ Comprehensive error handling
- ✅ Clear method naming and organization
- ✅ Lazy loading pattern well implemented

## Next Steps

1. **Immediate**: Plan refactoring strategy (Extract Module pattern)
2. **This Week**: Execute refactoring using /refactor skill
3. **Follow-up**: Add examples to complex methods

---

**Overall Assessment**: Solid code quality with one critical issue (file size).
Refactoring will significantly improve maintainability while preserving
excellent documentation and error handling practices.
```

---

### Example 2: Full Codebase Review

**Request**: `/review` (entire codebase)

**Execution** (abbreviated):

```markdown
# Code Review Report - FMOD Importer Codebase
Date: 2024-12-20
Reviewer: Claude Sonnet 4.5

## Executive Summary

- **Scope**: Entire FMOD Importer codebase
- **Overall Quality**: Good (some refactoring needed)
- **Critical Issues**: 1
- **High Priority Recommendations**: 5
- **Medium Priority Recommendations**: 8
- **Lines of Code**: ~8000 (Python only)

## Summary Statistics

- Total files reviewed: 15
- Total lines of code: 8023
- Average file size: 535 lines
- Files exceeding 800 lines: 1 (project.py)
- Files approaching 800 lines: 2 (naming.py, widgets.py)
- Docstring coverage: 89% (overall)
- Code duplication instances: 4

## Critical Issues

### 1. project.py Exceeds Size Threshold
[Same as Example 1]

## Architecture Feedback

### Overall Architecture: Excellent
- ✅ Mixin pattern well-implemented
- ✅ Clear separation core/GUI
- ✅ No circular dependencies
- ✅ Modular design

### SOLID Compliance: Good
- **SRP**: Mostly good, project.py exception
- **OCP**: Excellent (mixin extensibility)
- **LSP**: Good (mixin composability)
- **ISP**: Good (focused interfaces)
- **DIP**: Excellent (GUI → Core dependency direction)

## Refactoring Opportunities

### HIGH PRIORITY

1. **Split project.py** (already covered)

2. **Consolidate normalize_string()**
   - **Locations**: naming.py:245, matcher.py:89
   - **Recommendation**: Extract to utils.py
   - **Effort**: Low
   - **Skill**: /refactor

3. **Extract Help Dialogs from widgets.py**
   - **Current**: widgets.py includes help dialog logic (80 lines)
   - **Recommendation**: Create help_dialogs.py mixin
   - **Benefit**: Keep widgets.py from exceeding 800 lines
   - **Effort**: Low
   - **Skill**: /refactor

### MEDIUM PRIORITY

1. **Create Error Message Constants**
   - **Issue**: Error messages duplicated across 12 files
   - **Recommendation**: Create error_messages.py
   - **Effort**: Medium

2. **Add Type Hints to Legacy Functions**
   - **Coverage**: 85% have type hints
   - **Remaining**: 15 functions without hints
   - **Effort**: Low

## Documentation Gaps

### 1. Missing CHANGELOG.md
- **Impact**: Version history not tracked
- **Recommendation**: Create CHANGELOG.md with historical versions
- **Priority**: HIGH

### 2. Missing ARCHITECTURE.md
- **Impact**: Design decisions not documented
- **Recommendation**: Create docs/ARCHITECTURE.md
- **Priority**: MEDIUM

### 3. Undocumented Features
- Bank filtering (v0.2.0)
- JSON export (recent)
- **Recommendation**: Update README.md

## Code Quality Metrics

### File Sizes (Top 10)
| File | Lines | Status |
|------|-------|--------|
| project.py | 1075 | ❌ EXCEEDS |
| naming.py | 710 | ⚠️ APPROACHING |
| widgets.py | 709 | ⚠️ APPROACHING |
| dialogs.py | 699 | ✅ OK |
| drag_drop.py | 641 | ✅ OK |
| matcher.py | 473 | ✅ OK |
| import_workflow.py | 430 | ✅ OK |
| asset_dialogs.py | 394 | ✅ OK |
| settings.py | 379 | ✅ OK |
| utils.py | 378 | ✅ OK |

### Duplicate Code
1. `normalize_string()` - 2 locations
2. File validation pattern - 5 locations
3. Error message formatting - 12 locations
4. Widget placeholder logic - 3 locations

### Complex Functions (>50 lines)
1. project.py:156 - copy_event_from_template() (87 lines)
2. analysis.py:45 - analyze_media() (62 lines)
3. import_workflow.py:89 - import_events() (58 lines)

## Recommendations Summary

### CRITICAL (Do Immediately)
1. Refactor project.py into 3 modules - /refactor

### HIGH PRIORITY (This Week)
1. Consolidate normalize_string() - /refactor
2. Create CHANGELOG.md - Manual
3. Extract help dialogs from widgets.py - /refactor
4. Add missing docstrings (22 functions) - Manual
5. Update README with recent features - Manual

### MEDIUM PRIORITY (This Month)
1. Create ARCHITECTURE.md - Manual
2. Create error message constants - /refactor
3. Add type hints to remaining functions - Manual
4. Break up long functions (>50 lines) - /refactor
5. Remove commented-out code - Manual

### LOW PRIORITY (When Time Permits)
1. Update README screenshot - Manual
2. Add unit tests (infrastructure needed) - /new-feature
3. Performance profiling - Manual

## Positive Observations

- ✅ **Excellent Architecture**: Mixin pattern well-executed
- ✅ **Zero External Dependencies**: Stdlib only (very portable)
- ✅ **Great Documentation**: 89% docstring coverage
- ✅ **Clean Separation**: Core/GUI boundaries clear
- ✅ **Good Error Handling**: User-friendly messages throughout
- ✅ **Consistent Style**: Python conventions followed
- ✅ **Smart Patterns**: Lazy loading, caching, strategy pattern

## Next Steps

### Week 1
- Refactor project.py using /refactor
- Create CHANGELOG.md
- Update README.md with recent features

### Week 2
- Consolidate duplicate code using /refactor
- Add missing docstrings
- Create ARCHITECTURE.md

### Month 1
- Implement remaining medium priority items
- Consider test infrastructure

---

**Overall Assessment**: High-quality codebase with excellent architecture.
Main issue is project.py size. Once refactored, will be exemplary Python project.

**Estimated Total Refactoring Effort**: 1-2 days for high-priority items
```

---

## Anti-Patterns to Avoid

### ❌ BAD: Review Without Context
```markdown
# Bad review
File too big. Fix it.
```

### ✅ GOOD: Review with Context and Recommendations
```markdown
# Good review
## Issue: File Size
- **File**: project.py (1075 lines)
- **Threshold**: 800 lines
- **Impact**: Violates modularity, hard to maintain
- **Recommendation**: Split into project.py, xml_handler.py, cache.py
- **Effort**: Medium (4-6 hours)
- **Skill**: /refactor
- **Priority**: HIGH
```

---

### ❌ BAD: Vague Suggestions
```markdown
Code could be better.
```

### ✅ GOOD: Specific Actionable Recommendations
```markdown
**Issue**: Duplicate `normalize_string()` function
- **Locations**: naming.py:245, matcher.py:89
- **Action**: Extract to utils.py
- **Benefit**: DRY principle, single source of truth
- **Effort**: Low (30 minutes)
- **Skill**: /refactor
```

---

### ❌ BAD: Only Negative Feedback
```markdown
Everything is wrong. Needs complete rewrite.
```

### ✅ GOOD: Balanced Feedback
```markdown
## Positive Observations
- Excellent docstring coverage (94%)
- Clean separation of concerns
- Good error handling

## Areas for Improvement
- File size exceeds threshold (refactor needed)
- Minor code duplication (easily fixed)
```

---

## Quick Reference

### Complete Checklist

```
Phase 1: Scope Definition
□ Scope defined (file/module/codebase/recent)
□ Depth selected (quick/standard/deep)
□ Specific concerns identified

Phase 2: Automated Checks
□ Line count analysis performed
□ Architecture validation completed
□ Code duplication detected

Phase 3: SOLID Review
□ SRP compliance checked
□ OCP compliance checked
□ LSP compliance checked
□ ISP compliance checked
□ DIP compliance checked

Phase 4: DRY/KISS/SSOT
□ DRY violations identified
□ KISS violations identified
□ SSOT violations identified

Phase 5: Documentation
□ Docstring completeness checked
□ README accuracy verified
□ CHANGELOG status checked

Phase 6: Code Quality
□ Complexity metrics analyzed
□ Error handling reviewed
□ Code style checked

Phase 7: Report Generation
□ Report structured and complete
□ Critical issues highlighted
□ Recommendations specific and actionable
□ Positive observations included

Phase 8: Action Items
□ Findings categorized by priority
□ Skills recommended for each item
□ Effort estimated
□ Execution order suggested
```

### Priority Levels

| Level | Meaning | Timeline |
|-------|---------|----------|
| CRITICAL | Must fix immediately | This week |
| HIGH | Should fix soon | This month |
| MEDIUM | Plan to fix | This quarter |
| LOW | Nice to have | When time permits |

### Review Depth Guide

| Depth | Time | Coverage |
|-------|------|----------|
| Quick Scan | 5-10 min | Metrics, obvious issues |
| Standard Review | 20-30 min | Full checks, SOLID, docs |
| Deep Analysis | 1+ hour | Architecture, patterns, optimization |
