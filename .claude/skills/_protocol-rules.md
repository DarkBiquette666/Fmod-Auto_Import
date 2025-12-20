# FMOD Importer Protocol Rules

This file contains global rules shared by all skills in the FMOD Importer project.

## Architecture Principles

### SOLID

#### Single Responsibility Principle (SRP)
- Each class/function has ONE clear responsibility
- Methods perform ONE coherent task
- Mixins address ONE aspect of GUI functionality

**Verification**:
- Can the class be described in one sentence without "and"?
- Does changing a business requirement affect only one reason to modify this class?

#### Open/Closed Principle (OCP)
- Extend behavior via composition (mixins) not modification
- Use inheritance/patterns to add features without changing existing code

**Verification**:
- Are new features added via new mixins/classes rather than modifying existing ones?

#### Liskov Substitution Principle (LSP)
- Mixins can be composed without breaking FmodImporterGUI
- Subclasses preserve base class contracts

**Verification**:
- Can mixins be added/removed without breaking the GUI?

#### Interface Segregation Principle (ISP)
- Mixins expose only relevant methods
- No "god classes" with unrelated methods

**Verification**:
- Do classes use all methods of the interfaces they implement?

#### Dependency Inversion Principle (DIP)
- Depend on abstractions (NamingPattern, AudioMatcher) not concrete implementations
- Core modules (project, naming, matcher) are independent of GUI

**Verification**:
- Do core modules import GUI modules? (NO!)
- Do dependencies point to abstractions?

### Code Language Standards

**🇬🇧 MANDATORY: All code must be written in English**

This applies to:
- ✅ Variable names: `event_name` not `nom_event`
- ✅ Function names: `create_event()` not `creer_evenement()`
- ✅ Class names: `AudioMatcher` not `CorrespondanceAudio`
- ✅ Comments: `# Parse the XML file` not `# Parser le fichier XML`
- ✅ Docstrings: All documentation in English
- ✅ Error messages shown to developers (technical errors)
- ✅ Log messages

**Exceptions** (French is allowed for):
- ❌ User-facing GUI labels and messages (messagebox, tooltips)
- ❌ User documentation in French (if applicable)

**Rationale**:
- International collaboration and maintenance
- Consistency with Python/programming conventions
- Easier code reviews and debugging
- Better integration with English-based libraries and documentation

**Example**:
```python
# ✅ GOOD - English code with French UI
def create_event_from_selection(audio_files: list[str]) -> Event:
    """
    Create FMOD event from selected audio files.

    Args:
        audio_files: List of paths to audio files

    Returns:
        Created Event object
    """
    if not audio_files:
        # Technical error - English
        raise ValueError("Cannot create event from empty selection")

    event = Event()
    for file in audio_files:
        event.add_audio(file)

    # User message - French OK
    messagebox.showinfo("Succès", "L'événement a été créé avec succès!")
    return event

# ❌ BAD - French in code
def creer_evenement_depuis_selection(fichiers_audio: list[str]) -> Event:
    """
    Crée un événement FMOD depuis les fichiers sélectionnés.
    """
    if not fichiers_audio:
        raise ValueError("Impossible de créer événement depuis sélection vide")
    ...
```

### DRY (Don't Repeat Yourself)
- Extract repeated logic into utility functions
- Create reusable components on the 3rd occurrence of similar code
- Check for duplication between modules

**Triggers**:
- Identical/similar code block appears 3+ times → EXTRACT

### KISS (Keep It Simple, Stupid)
- Prefer simple solutions to clever ones
- Avoid premature optimization
- Clear variable/function names

**Verification**:
- Is the code easy to understand for someone unfamiliar with the project?
- Is there a simpler solution?

### WYSIWYG (What You See Is What You Get)
- Code behavior matches its appearance
- No hidden side effects
- Explicit is better than implicit

**Verification**:
- Do functions do exactly what their name suggests?
- Are there undocumented side effects?

### SSOT (Single Source of Truth)
- VERSION in `__init__.py` only
- Configuration in one place
- Avoid data structure duplication

**Verification**:
- Is data duplicated somewhere?
- Are there multiple sources for the same information?

### Modularity
- Clear module boundaries
- Minimal coupling between modules
- High cohesion within modules

**Target architecture**:
```
fmod_importer/
├── __init__.py           # Exports, VERSION
├── project.py            # Core FMOD project logic
├── naming.py             # Pattern parsing
├── matcher.py            # Audio matching
└── gui/                  # GUI layer (separate)
    ├── __init__.py
    ├── main.py           # Main GUI class
    └── [mixins].py       # GUI mixins
```

---

## Thresholds and Metrics

### Line Count Thresholds

| Threshold | Action | Level |
|-----------|--------|-------|
| 750 lines | Plan refactoring before 800 | `[INFO]` |
| 800 lines | Refactoring recommended | `[RECOMMEND]` |
| 900 lines (mixin) | Split mixin or extract utilities | `[RECOMMEND]` |
| 1000 lines | Absolute maximum for mixins | `[CRITICAL]` |

### Complexity Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Function lines | 40 lines | Split function |
| Function lines | 50 lines | Refactoring required |
| Nesting depth | 3 levels | Extract nested logic |
| Parameter count | 5 parameters | Parameter object or config dict |
| if/elif chain | 5 conditions | Dict dispatch or polymorphism |
| try/except block | 20 lines | Extract into separate function |

---

## Automatic Triggers

### Pattern Triggers

#### Code Duplication
```
[SUGGEST] Pattern: Code duplication detected

Current state:
- [Code block] appears in [N] files

Suggested improvement:
- Extract into reusable function in [appropriate module]

Benefit:
- Single Source of Truth
- Easier to maintain
- Reduces codebase size

Estimated effort: Low
Skill to use: /fmod-refactor
```

#### Similar Structures
```
[SUGGEST] Pattern: Classes with similar structures

Current state:
- [ClassA] and [ClassB] have [N] similar methods

Suggested improvement:
- Create abstract base class or shared mixin

Benefit:
- Reusability
- Consistency
- Easier maintenance

Estimated effort: Medium
Skill to use: /fmod-refactor
```

### Architecture Triggers

#### GUI Code in Core
```
[VIOLATION] Architecture: GUI code in core module

Current state:
- [core_module.py] imports/uses tkinter or GUI components

Suggested improvement:
- Move GUI logic to appropriate mixin
- Keep core modules GUI-agnostic

Benefit:
- Respects Dependency Inversion Principle
- Improved testability
- Separation of responsibilities

Estimated effort: Medium
Skill to use: /fmod-refactor
```

#### Business Logic in GUI
```
[RECOMMEND] Architecture: Business logic in GUI

Current state:
- [gui_mixin.py] contains complex business logic

Suggested improvement:
- Extract to appropriate core module
- GUI calls core module

Benefit:
- Business logic reusability
- Easier to test
- Clear separation of responsibilities

Estimated effort: Medium
Skill to use: /fmod-refactor
```

#### Circular Dependency
```
[CRITICAL] Architecture: Circular dependency detected

Current state:
- [ModuleA] imports [ModuleB] which imports [ModuleA]

Suggested improvement:
- Refactor to eliminate cycle
- Options: Dependency Injection, Event System, Extract Common Module

Benefit:
- Maintainable code
- Avoids subtle bugs
- Clearer architecture

Estimated effort: High
Skill to use: /fmod-refactor
```

---

## Documentation Standards

### Docstrings

#### Standard Format
```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """
    Brief one-line summary (imperative mood).

    Detailed explanation of what the function does, why it exists,
    and how it fits into the larger system. Include edge cases
    and important implementation details.

    Args:
        param1: Description of param1 and valid values
        param2: Description of param2 and valid values

    Returns:
        Description of return value and its type/structure

    Raises:
        ValueError: When param1 is invalid
        IOError: When file operation fails

    Examples:
        >>> function_name(value1, value2)
        expected_result

        >>> function_name(edge_case)
        edge_case_result
    """
```

#### Class Docstrings
```python
class ClassName:
    """
    Brief one-line summary.

    Detailed description of class purpose, responsibilities,
    and how it fits into the larger architecture. Mention
    design patterns used if applicable.

    Attributes:
        attr1: Description of attribute 1
        attr2: Description of attribute 2

    Examples:
        >>> obj = ClassName()
        >>> obj.method()
        result
    """
```

#### Module Docstrings
```python
"""
Module Name

Brief description of module purpose and contents.

This module handles [primary responsibility] for the FMOD Importer.
It provides [key functionality] and is used by [consumers].

Key classes:
    - ClassName1: Brief description
    - ClassName2: Brief description

Dependencies:
    - Module1: For [reason]
    - Module2: For [reason]
"""
```

### README.md Updates

#### When to Update
- ✅ New user-facing feature → Update "Description" and "Usage"
- ✅ New workflow → Add "Recommended Workflow"
- ✅ New possible error → Add "Troubleshooting"
- ✅ UI change → Update descriptions/screenshots
- ✅ Version bump → Update version at bottom

#### Feature Section Template
```markdown
### [Feature Name]

[Description of what the feature does and why it's useful]

**How to use**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Example**:
[Concrete usage example]

**Notes**:
- [Important point 1]
- [Important point 2]
```

#### Troubleshooting Template
```markdown
### [Problem]

**Symptoms**:
- [Symptom 1]
- [Symptom 2]

**Cause**:
[Explanation of the cause]

**Solution**:
1. [Resolution step 1]
2. [Resolution step 2]

**Alternative**:
[Alternative solution if applicable]
```

### CHANGELOG.md

#### Format
Follow [Keep a Changelog](https://keepachangelog.com/):

```markdown
# Changelog

All notable changes to FMOD Importer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [X.Y.Z] - YYYY-MM-DD
### Added
- [New feature description]

### Changed
- [Change to existing functionality]

### Deprecated
- [Soon-to-be removed feature]

### Removed
- [Removed feature]

### Fixed
- [Bug fix description]

### Security
- [Security fix]
```

#### Update Triggers
- `feat` commit → Add under "Added"
- `fix` commit → Add under "Fixed"
- Major `refactor` → Add under "Changed"
- Breaking change → Note under appropriate section + mention BREAKING CHANGE

---

## Commit Conventions

### Format (Conventional Commits)
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Note**: Do NOT include Claude/Anthropic signatures in commits.

### Commit Types

| Type | Description | Version Bump | Example |
|------|-------------|--------------|---------|
| `feat` | New feature | Minor (0.1.0→0.2.0) | `feat(gui): Add bank filter widget` |
| `fix` | Bug fix | Patch (0.1.0→0.1.1) | `fix: Handle empty template folders` |
| `refactor` | Code restructuring | None* | `refactor: Extract XML handler module` |
| `docs` | Documentation only | None | `docs: Update README troubleshooting` |
| `test` | Add/update tests | None | `test: Add matcher unit tests` |
| `chore` | Maintenance | None | `chore: Update build script` |
| `perf` | Performance | Patch if significant | `perf: Optimize event matching` |
| `style` | Formatting | None | `style: Fix PEP8 violations` |

*Refactor = Minor bump if major architectural change

### Scopes (optional)

| Scope | Usage |
|-------|-------|
| `gui` | GUI changes (mixins, widgets) |
| `core` | Core modules (project, naming, matcher) |
| `build` | Build system (PyInstaller, CI/CD) |
| `deps` | Dependencies |

### Subject Rules
- Maximum 72 characters
- Imperative mood (Add, Fix, Refactor, not Added, Fixed, Refactored)
- No final period
- Start with lowercase after type

### Body (optional but recommended for complex changes)
- Explain WHY, not WHAT (the diff shows what)
- Wrap at 72 characters
- Separate subject and body with blank line

### Footer (optional)
- Breaking changes: `BREAKING CHANGE: description`
- Issue references: `Fixes #123` or `Closes #456`

### Examples

#### Simple Feature
```
feat(gui): Add event preview panel
```

#### Bug Fix with Details
```
fix: Prevent crash when loading empty projects

Previously, loading a project with no events would cause
a NullPointerException in the analysis workflow. Added
defensive checks and user-friendly error message.

Fixes #42
```

#### Major Refactoring
```
refactor: Split project.py into focused modules

Project module exceeded 1075 lines, violating 800-line threshold.
Split into:
- project.py: Core project management (420 lines)
- xml_handler.py: XML operations (350 lines)
- cache.py: Caching logic (240 lines)

Improves Single Responsibility Principle and maintainability.
```

#### Breaking Change
```
feat!: Change naming pattern API to accept separator

BREAKING CHANGE: NamingPattern constructor now requires
separator parameter. Update all instantiations:

Before: NamingPattern(pattern_str)
After: NamingPattern(pattern_str, separator='_')

Migration: Add separator='_' to all NamingPattern calls.
```

---

## Version Bumping

### ⚡ Automatic Version Bump System

**Version bump is AUTOMATICALLY triggered after each validated `feat` or `fix` commit.**

When Claude completes a `feat` or `fix` commit, it must **immediately** propose a version bump using the `/version-bump` skill.

### Semantic Versioning (MAJOR.MINOR.PATCH)

#### MAJOR (1.0.0)
- Breaking changes
- Incompatible API changes
- Major architectural modifications
- **Detection**: Commit contains `BREAKING CHANGE:` in body/footer

#### MINOR (0.X.0)
- New features (backward-compatible)
- `feat` commits
- Significant architectural refactoring
- **Detection**: `feat` type commits since last version

#### PATCH (0.0.X)
- Bug fixes
- `fix` commits
- Significant performance improvements
- **Detection**: `fix` type commits since last version

### Automatic Workflow

```
1. User Request
   ↓
2. Implementation (feat/fix)
   ↓
3. Tests & Validation
   ↓
4. Commit created with Conventional Commits format
   ↓
5. ✨ AUTO-TRIGGER: Version Bump Check
   ↓
   If commit = feat OR fix:
   ├─→ Propose version bump immediately
   │   "📦 New feature/fix committed! Bump version now? (v0.1.8 → v0.2.0)"
   │
   └─→ If user accepts: Execute `/version-bump` skill
       If user refuses: Add reminder to TODO
```

### When to Trigger Version Bump

**ALWAYS after** these commits:
- ✅ `feat(scope): ...` → Propose MINOR bump
- ✅ `fix(scope): ...` → Propose PATCH bump
- ✅ Commit with `BREAKING CHANGE:` → Propose MAJOR bump

**NEVER after** these commits:
- ❌ `docs:` → No bump
- ❌ `style:` → No bump
- ❌ `refactor:` (unless major architectural)
- ❌ `test:` → No bump
- ❌ `chore:` → No bump

### Version Bump Process (via `/version-bump` skill)

The `/version-bump` skill automates:

1. **Analyze commits** since last tagged version
   - Parse git log to detect feat/fix/breaking
   - Determine bump type (MAJOR > MINOR > PATCH)

2. **Calculate new version**
   - Read current VERSION from `fmod_importer/__init__.py`
   - Apply Semantic Versioning rule
   - Propose new version to user

3. **Update files**
   - `fmod_importer/__init__.py` → `VERSION = "X.Y.Z"`
   - `CHANGELOG.md` → Rename `[Unreleased]` to `[X.Y.Z]`

4. **Git operations**
   - Create commit: `chore(release): Bump version to X.Y.Z`
   - Create tag: `vX.Y.Z`
   - Display next steps (push to remote)

**See full details**: [version-bump.md](version-bump.md)

### Complete Example

```
User: "Add bank filter widget to GUI"
  ↓
[Claude implements the feature]
  ↓
[Tests & validation]
  ↓
[Commit created]:
  "feat(gui): Add bank filter widget"
  ↓
🤖 Claude detects feat commit and proposes:

  "📦 New feature committed!

   Current version: v0.1.8
   Proposed: v0.2.0 (MINOR bump - new feature)

   Would you like to bump the version now? [Y/n]"

  ↓
[User: Y]
  ↓
🤖 Claude executes /version-bump:
  ✓ Updated fmod_importer/__init__.py: VERSION = "0.2.0"
  ✓ Updated CHANGELOG.md: [0.2.0] - 2024-12-20
  ✓ Created commit: chore(release): Bump version to 0.2.0
  ✓ Created tag: v0.2.0

  "✅ Version bump completed!
   Next: git push && git push --tags"
```

### Affected Files

| File | Modification | Trigger |
|------|-------------|---------|
| `fmod_importer/__init__.py` | `VERSION = "X.Y.Z"` | Automatic via skill |
| `CHANGELOG.md` | `## [X.Y.Z] - YYYY-MM-DD` | Automatic via skill |
| `.git/refs/tags/vX.Y.Z` | Git tag | Automatic via skill |

### Important

- **SSOT**: `fmod_importer/__init__.py` is the single source of truth
- **Atomic**: Version bump = 1 commit + 1 tag
- **Always propose**: Never skip the proposal after feat/fix
- **User decision**: Always ask for confirmation before bump
- **Skill reference**: See `/version-bump` for complete implementation

---

## Quality Checks Checklist

Before each commit, verify:

### Architecture
- [ ] SOLID principles respected
- [ ] No GUI code in core modules
- [ ] No complex business logic in GUI
- [ ] No circular dependencies
- [ ] Mixin pattern maintained for GUI

### Code Quality
- [ ] **English only** - All code, comments, docstrings, and variable names in English
- [ ] No code duplication (DRY)
- [ ] Clear and descriptive names (KISS)
- [ ] No hidden side effects (WYSIWYG)
- [ ] No duplicated data (SSOT)
- [ ] Appropriate error handling

### Metrics
- [ ] No file >800 lines (or refactoring planned)
- [ ] No function >50 lines
- [ ] Nesting depth ≤3 levels
- [ ] Parameter count ≤5

### Documentation
- [ ] Complete docstrings for public code
- [ ] README.md updated if user-facing feature
- [ ] CHANGELOG.md updated
- [ ] VERSION bumped if necessary
- [ ] Inline comments for complex logic only

### Tests (future)
- [ ] Unit tests for core logic
- [ ] Integration tests for workflows
- [ ] All tests pass

---

## Post-Commit Automation

### 🚀 Automatic Actions After Commit

**IMPORTANT**: After each successful commit, Claude must **automatically** perform these checks:

#### 1. Check Commit Type

Analyze the just-created commit:
```bash
git log -1 --pretty=format:"%s"
```

#### 2. Trigger Version Bump if Applicable

**IF the commit starts with:**
- ✅ `feat` → **PROPOSE** version bump (MINOR)
- ✅ `fix` → **PROPOSE** version bump (PATCH)
- ✅ Contains `BREAKING CHANGE` → **PROPOSE** version bump (MAJOR)

**THEN immediately display:**

```
📦 Feature/Fix committed successfully!

Commit: {commit_hash_short} {commit_subject}
Current version: v{current_version}
Proposed bump: v{new_version} ({bump_type})

Would you like to bump the version now? [Y/n]
```

**IF user accepts [Y]:**
- Execute `/version-bump` skill immediately
- Don't wait until end of conversation

**IF user refuses [n]:**
- Add reminder to TODO: "Pending version bump for v{new_version}"
- Continue normally

#### 3. Documentation Reminder

**IF `feat` commit with user-facing feature:**
- Check that README.md has been updated
- If not: Remind "README.md may need updating for this feature"

### Post-Commit Automation Examples

#### Example 1: Fix Commit
```
✅ Commit created: fix(import): Resolve path escaping on Windows

📦 Fix committed successfully!

Commit: a3b4c5d fix(import): Resolve path escaping on Windows
Current version: v0.1.8
Proposed bump: v0.1.9 (PATCH)

Would you like to bump the version now? [Y/n] _
```

#### Example 2: Feature Commit
```
✅ Commit created: feat(gui): Add bank filter widget

📦 Feature committed successfully!

Commit: e7f8g9h feat(gui): Add bank filter widget
Current version: v0.1.8
Proposed bump: v0.2.0 (MINOR - new feature)

Would you like to bump the version now? [Y/n] _
```

#### Example 3: Docs Commit (No Bump)
```
✅ Commit created: docs: Update README troubleshooting

✓ Documentation commit completed.
(No version bump needed for docs-only changes)
```

### Post-Commit Checklist

After **each** `feat` or `fix` commit, verify:

- [ ] Version bump proposal displayed to user
- [ ] User responded (Y or n)
- [ ] If Y: `/version-bump` executed successfully
- [ ] If n: Reminder added to TODO
- [ ] CHANGELOG.md contains entry for this commit
- [ ] README.md updated if necessary

### Exceptions

**DO NOT propose version bump if:**
- Commit type is `docs`, `test`, `style`, `chore`
- Commit is already a version bump (`chore(release): Bump version...`)
- User explicitly requested not to bump
- It's a merge commit

---

## Error Handling Standards

### Principles
- Catch specific exceptions, not generic
- Provide useful error messages to user
- Log technical details for debugging
- Fail gracefully with fallbacks when possible

### Pattern
```python
def risky_operation(path: str) -> Result:
    """
    Perform operation that might fail.

    Args:
        path: Path to file

    Returns:
        Result object

    Raises:
        ValueError: If path is invalid
        IOError: If file cannot be read
    """
    if not path:
        raise ValueError("Path cannot be empty")

    try:
        with open(path, 'r') as f:
            data = f.read()
    except FileNotFoundError:
        # User-friendly message
        messagebox.showerror(
            "File Not Found",
            f"Could not find file: {path}\n\n"
            "Please check the path and try again."
        )
        return None
    except PermissionError:
        messagebox.showerror(
            "Permission Denied",
            f"Cannot read file: {path}\n\n"
            "Please check file permissions."
        )
        return None
    except Exception as e:
        # Catch-all for unexpected errors
        messagebox.showerror(
            "Unexpected Error",
            f"An error occurred while reading file:\n{str(e)}\n\n"
            "Please report this issue if it persists."
        )
        return None

    return process_data(data)
```

### Anti-Patterns to Avoid
```python
# ❌ BAD: Bare except
try:
    risky_operation()
except:
    pass

# ❌ BAD: Generic exception without context
try:
    risky_operation()
except Exception:
    raise Exception("Error")

# ❌ BAD: Silent failure
try:
    risky_operation()
except:
    return None

# ✅ GOOD: Specific exception with context
try:
    risky_operation()
except FileNotFoundError as e:
    logger.error(f"File not found: {path}", exc_info=True)
    show_user_error("File not found", path)
    return None
```

---

## Skill Decision Tree

```
User Request
    │
    ├─ Describes specific bug/error
    │  → Use /fmod-debug
    │
    ├─ Requests new functionality
    │  → Use /fmod-feature
    │
    ├─ Mentions "refactor", "improve code", "clean up", "restructure"
    │  → Use /fmod-refactor
    │
    ├─ Requests "review", "check code", "audit", "analyze"
    │  → Use /fmod-review
    │
    └─ General question or discussion
       → No skill, respond directly
```

### Ambiguous Cases

#### "Fix this code"
- If specific bug described → `/fmod-debug`
- If general quality improvement → `/fmod-refactor`

#### "Add feature X and clean up code Y"
- Separate into two tasks:
  1. `/fmod-feature` for X
  2. `/fmod-refactor` for Y

#### "Why is this code structured this way?"
- Use `/fmod-review` to analyze architecture
- Explain design decisions

---

## Project Architecture Patterns

### Mixin Pattern (GUI)
```python
class FmodImporterGUI(
    UtilsMixin,
    WidgetsMixin,
    DialogsMixin,
    AssetDialogsMixin,
    DragDropMixin,
    AnalysisMixin,
    ImportMixin,
    SettingsMixin
):
    """Main GUI class composed of focused mixins"""
    pass
```

**Benefits**:
- Each mixin <1000 lines
- Clear separation of responsibilities
- Easy to test individually
- Modular and reusable

**Rules**:
- Each mixin = one responsibility
- No dependencies between mixins (as much as possible)
- Methods prefixed if private to mixin (_method_name)

### Builder Pattern (Naming)
```python
pattern = NamingPattern("$prefix_$feature_$action")
event_name = pattern.build(
    prefix="Sfx",
    feature="Attack",
    action="Heavy"
)
# → "Sfx_Attack_Heavy"
```

### Strategy Pattern (Matching)
```python
# Multiple parsing strategies with fallback
def parse_asset(self, asset_name):
    # Try exact match
    result = self._parse_exact(asset_name)
    if result:
        return result

    # Try flexible match
    result = self._parse_flexible(asset_name)
    if result:
        return result

    # Try fuzzy match
    return self._parse_fuzzy(asset_name)
```

### Lazy Loading Pattern (Project)
```python
@property
def banks(self) -> Dict[str, Dict]:
    """Load banks lazily on first access"""
    if self._banks is None:
        self._banks = self._load_banks()
    return self._banks
```

### Caching Pattern (Project)
```python
# Check cache first, fallback to XML
if cache_path.exists():
    data = load_cache(cache_path)
else:
    data = parse_xml(xml_path)
    save_cache(data, cache_path)
```

---

## Suggestion Levels

### [INFO]
Informative suggestion, nice-to-have

**Example**: File approaching 750 lines

### [SUGGEST]
Recommended improvement

**Example**: Code duplicated 3 times

### [RECOMMEND]
Strongly recommended

**Example**: File exceeds 800 lines

### [VIOLATION]
Principle violation, should be fixed

**Example**: GUI code in core module

### [CRITICAL]
Serious problem, must be fixed immediately

**Example**: Circular dependency

---

## Quick References

### Critical Thresholds
- 750 lines: Plan refactoring
- 800 lines: Refactoring recommended
- 900 lines (mixin): Urgent refactoring
- 1000 lines: Absolute maximum

### Commit Types
- `feat`: Feature (minor bump)
- `fix`: Bug fix (patch bump)
- `refactor`: Restructure (no bump)
- `docs`: Documentation (no bump)

### Documentation to Update
- README.md: User-facing features, troubleshooting
- CHANGELOG.md: Each version
- Docstrings: Each public function/class
- ARCHITECTURE.md: Major architectural changes

### Quick SOLID Check
1. SRP: One responsibility per class?
2. OCP: Extension through composition?
3. LSP: Mixins composable?
4. ISP: No god classes?
5. DIP: Depends on abstractions?
