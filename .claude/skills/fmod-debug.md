# Skill: /fmod-debug

Diagnose and fix bugs in a structured manner while maintaining code quality and preventing regressions.

## Objective

Resolve bugs efficiently with targeted, well-documented, and tested fixes.

## When to Use This Skill

- ✅ User reports a bug or error
- ✅ Unexpected behavior observed
- ✅ Crash or exception detected
- ❌ Not for new features (use `/fmod-feature`)
- ❌ Not for code improvement (use `/fmod-refactor`)

## Workflow

### Step 1: Bug Report Analysis

**Actions**:
1. **Read the bug report completely**:
   - Problem description
   - Reproduction steps (if provided)
   - Error message (if applicable)
   - Expected vs observed behavior

2. **Reproduce the bug** (if steps available):
   ```python
   # Try to reproduce in similar conditions
   # Note exact error message and stack trace
   ```

3. **Identify symptoms vs root cause**:
   - **Symptom**: What the user sees (ex: crash, error message)
   - **Root cause**: The real reason for the problem (ex: missing validation, null pointer)

4. **Determine affected modules**:
   - GUI only?
   - Core logic only?
   - Both?
   - External dependency?

5. **Check for regression**:
   ```bash
   git log -p --all -S "relevant_code_pattern"
   # Check recent commits that might have introduced bug
   ```

**Checklist**:
- [ ] Bug report read and understood
- [ ] Bug reproduced (if possible)
- [ ] Symptoms identified
- [ ] Affected modules determined
- [ ] Git history checked for regressions

**Questions to Ask** (if information missing):
- What are the exact steps to reproduce?
- What is the complete error message (with stack trace)?
- Did this work before?
- Under what conditions does the bug appear?

---

### Step 2: Root Cause Investigation

**Actions**:

1. **Search relevant code with Grep**:
   ```bash
   # Search for error message
   grep -r "error message text" fmod_importer/

   # Search for function/class mentioned in stack trace
   grep -r "function_name" fmod_importer/

   # Search for relevant operations
   grep -r "load_project\|parse_xml" fmod_importer/
   ```

2. **Read affected modules completely**:
   - Don't rely solely on the error line
   - Understand the complete context
   - Trace execution flow

3. **Trace execution path**:
   ```
   User action
      ↓
   GUI event handler (gui/main.py)
      ↓
   Mixin method (gui/analysis.py)
      ↓
   Core logic (project.py)
      ↓
   ERROR occurs here ←
   ```

4. **Identify broken assumption or logic error**:
   - Missing validation?
   - Unhandled null pointer?
   - Type mismatch?
   - Race condition?
   - Unforeseen edge case?

5. **Check for unhandled edge cases**:
   - Empty inputs
   - Null/None values
   - File doesn't exist
   - Invalid format
   - Boundary conditions

6. **Review recent commits**:
   ```bash
   git log --oneline --all -20
   git show <commit-hash>  # Review suspicious commits
   ```

**Checklist**:
- [ ] Relevant code found and read
- [ ] Execution path traced
- [ ] Broken assumption identified
- [ ] Edge cases verified
- [ ] Recent commits reviewed

**Investigation Techniques**:

#### Technique 1: Stack Trace Analysis
```python
# Read stack trace from bottom to top:
File "gui/import_workflow.py", line 156, in import_events
    template_id = event['matched_template']  # ← KeyError here
                      ↑
          Check: does event always have 'matched_template'?
```

#### Technique 2: Data Flow Tracing
```python
# Trace where problematic data comes from:
event = {...}                    # Where is event created?
event['matched_template'] = ...  # Is this always set?
# OR
event = manually_matched_event   # Different source without matched_template!
```

#### Technique 3: Assumption Validation
```python
# Identify assumptions in code:
def process_event(event):
    # ASSUMPTION: event always has 'matched_template' key
    template_id = event['matched_template']  # ← Assumption might be wrong!

# Validate assumption:
# Q: Where are events created?
# Q: Do all code paths set 'matched_template'?
# A: No! Manually matched orphan events don't have it.
```

---

### Step 3: Fix Planning

**Actions**:

1. **Determine fix type**:

   **Minimal Fix** (preferred):
   - Addresses only the specific bug
   - Minimal changes
   - Easy to review and test
   - Reduces regression risk

   **Comprehensive Fix**:
   - Addresses bug + related problems
   - May require refactoring
   - Used if minimal fix creates technical debt
   - Requires more testing

2. **Evaluate if refactoring needed**:
   - Minimal fix possible? → Do minimal fix
   - Problematic architecture revealed? → Note for future `/fmod-refactor`
   - Fix impossible without refactoring? → Use `/fmod-refactor` first

3. **Identify potential side effects**:
   - What other code paths use this function?
   - Are there dependencies on current behavior?
   - Could the fix break something else?

4. **Plan defensive programming**:
   - What validation to add?
   - What error handling is missing?
   - What edge cases to protect?

5. **Consider if fix reveals architectural problem**:
   - Recurring pattern of similar bugs?
   - Underlying design flaw?
   - → Note for discussion/future refactoring

**Checklist**:
- [ ] Fix type determined (minimal vs comprehensive)
- [ ] Need for refactoring evaluated
- [ ] Side effects identified
- [ ] Defensive programming planned
- [ ] Architectural problems noted

**Decision Tree - Fix Type**:
```
Bug Analysis
    │
    ├─ Simple logic error, localized
    │  └─ Minimal fix (change 1-5 lines)
    │
    ├─ Missing validation/error handling
    │  └─ Minimal fix (add defensive checks)
    │
    ├─ Unhandled edge case
    │  └─ Minimal fix (add edge case handling)
    │
    ├─ Minor design flaw
    │  └─ Minimal fix now, note for refactoring later
    │
    └─ Major design flaw
       └─ Use /fmod-refactor, then apply fix
```

---

### Step 4: Implementation

**Actions**:

1. **Apply minimal and targeted fix**:
   ```python
   # BEFORE (buggy):
   def import_events(self):
       for event in self.events:
           template_id = event['matched_template']  # KeyError if missing
           # ...

   # AFTER (fixed):
   def import_events(self):
       for event in self.events:
           template_id = event.get('matched_template')  # Returns None if missing
           if template_id:
               # Copy from template
           else:
               # Create basic event (handles orphans)
           # ...
   ```

2. **Add error handling if missing**:
   ```python
   # Add try/except for risky operations
   try:
       data = self.load_file(path)
   except FileNotFoundError:
       messagebox.showerror(
           "File Not Found",
           f"Could not find file: {path}\n"
           "Please check the path and try again."
       )
       return None
   ```

3. **Add defensive checks for edge cases**:
   ```python
   def filter_events(self, bank_id: str) -> List[Dict]:
       # Defensive checks
       if not bank_id:
           raise ValueError("bank_id cannot be empty")

       if bank_id not in self.banks:
           raise ValueError(f"Bank {bank_id} not found")

       # Safe to proceed
       return [e for e in self.events.values() if e.get('output_bank') == bank_id]
   ```

4. **Update docstrings if behavior changes**:
   ```python
   def process_event(self, event: Dict) -> None:
       """
       Process event for import.

       Now handles both template-based and orphan events.  # ← Updated

       Args:
           event: Event dictionary (may or may not have 'matched_template')  # ← Clarified

       Raises:
           ValueError: If event is invalid
       """
   ```

5. **Add inline comments explaining fix** (if not obvious):
   ```python
   # Fix for issue #42: Handle orphan events without matched_template
   template_id = event.get('matched_template')
   if template_id:
       # Template-based event
       self._copy_from_template(event, template_id)
   else:
       # Orphan event (manually matched)
       self._create_basic_event(event)
   ```

**Checklist**:
- [ ] Fix applied (minimal and targeted)
- [ ] Error handling added if missing
- [ ] Defensive checks for edge cases
- [ ] Docstrings updated if behavior changes
- [ ] Inline comments added if fix not obvious

**Common Fix Patterns**:

#### Pattern 1: Null/None Check
```python
# Before
value = data['key']

# After
value = data.get('key')  # Returns None if missing
if value:
    # Use value
```

#### Pattern 2: Validation Before Use
```python
# Before
result = process(input_data)

# After
if not input_data:
    raise ValueError("input_data cannot be empty")

result = process(input_data)
```

#### Pattern 3: Graceful Fallback
```python
# Before
data = load_from_cache()  # Might fail

# After
try:
    data = load_from_cache()
except (FileNotFoundError, IOError):
    # Fallback to fresh load
    data = load_from_source()
```

---

### Step 5: Verification

**Actions**:

1. **Test original bug scenario**:
   - Reproduce exact steps that caused the bug
   - Verify error no longer occurs
   - Verify behavior is correct

2. **Test edge cases**:
   - Empty inputs
   - Null/None values
   - Boundary conditions
   - Invalid inputs
   - Large datasets

3. **Check for no regressions**:
   - Test related functionality
   - Verify main use cases
   - Test complete workflows

4. **Verify user-friendly error messages**:
   - Messages clear and understandable?
   - Instructions for resolution?
   - No stack traces exposed to user?

5. **Validate no SOLID principle violations**:
   - Fix maintains Single Responsibility?
   - No coupling added?
   - No duplication introduced?

**Checklist**:
- [ ] Original bug scenario tested and resolved
- [ ] Edge cases tested
- [ ] No regressions detected
- [ ] User-friendly error messages verified
- [ ] SOLID principles maintained

**Test Scenarios Template**:
```python
# Test 1: Original bug scenario
# Steps: [original reproduction steps]
# Expected: [should work without error]
# Result: ✅ PASS

# Test 2: Edge case - empty input
# Steps: [test with empty input]
# Expected: [graceful error or handled]
# Result: ✅ PASS

# Test 3: Edge case - null value
# Steps: [test with null value]
# Expected: [graceful error or handled]
# Result: ✅ PASS

# Test 4: Regression check - normal workflow
# Steps: [normal usage scenario]
# Expected: [works as before]
# Result: ✅ PASS
```

---

### Step 6: Documentation Updates

**Actions**:

1. **Update docstrings** (if function behavior changed):
   ```python
   def load_project(self, path: str) -> bool:
       """
       Load FMOD project from path.

       Now includes validation for empty paths and provides
       user-friendly error messages.  # ← Document change

       Args:
           path: Path to .fspro file

       Returns:
           True if successful, False otherwise

       Raises:
           ValueError: If path is empty or invalid  # ← New exception
           FileNotFoundError: If project file doesn't exist
       """
   ```

2. **Add to CHANGELOG.md** under "Fixed":
   ```markdown
   ## [Unreleased]
   ### Fixed
   - Fix crash when importing manually matched orphan events without template
   - Add validation for empty project paths with user-friendly error messages
   ```

3. **Add to README troubleshooting** (if user-facing bug):
   ```markdown
   ### Import Fails with KeyError

   **Symptom**:
   - Error message: "KeyError: 'matched_template'"
   - Occurs when importing orphan events

   **Cause**:
   - Orphan events that were manually matched don't have template information

   **Solution**:
   - Fixed in v0.1.9
   - Update to latest version
   - Orphan events now handled correctly
   ```

4. **Update VERSION** (patch bump for fix):
   ```python
   # fmod_importer/__init__.py
   VERSION = "0.1.9"  # Was "0.1.8"
   ```

**Checklist**:
- [ ] Docstrings updated if behavior changed
- [ ] CHANGELOG.md updated under "Fixed"
- [ ] README troubleshooting added if user-facing
- [ ] VERSION bumped (patch for fix)

---

### Step 7: Commit

**Strategy**: Single commit for simple bugs, multiple commits if complex fix

#### Simple Commit (preferred)
```bash
git add fmod_importer/gui/import_workflow.py
git commit -m "fix: Handle missing matched_template field for orphan events (v0.1.9)

Previously, importing manually matched orphan events would cause
KeyError because they don't have matched_template field. Added
defensive check using .get() with fallback to basic event creation.

Fixes #42"

git add CHANGELOG.md fmod_importer/__init__.py
git commit -m "docs: Update changelog for orphan event fix"
```

#### Multiple Commits (if complex fix + tests + docs)
```bash
# Main fix
git commit -m "fix: Add validation for empty project paths (v0.1.9)"

# Tests (if test infrastructure exists)
git commit -m "test: Add test cases for empty path handling"

# Documentation
git commit -m "docs: Document empty path validation in troubleshooting"
```

**Format** (see `_protocol-rules.md`):
```
fix: Brief description of what was fixed (vX.Y.Z)

Detailed explanation:
- What was the bug
- What caused it
- How it was fixed
- Why this approach was chosen

Fixes #issue_number (if applicable)
```

**Special Commit Prefixes**:
- `fix: CRITICAL -` for severe bugs (data loss, security, crashes)
- `fix: HOTFIX -` for urgent production fixes
- `fix!:` for breaking changes in fix (rare)

---

## Key Principles

### 1. Minimal and Targeted Fix
- Don't mix fix with refactoring
- Address only the specific bug
- No "scope creep" (adding unrelated features)
- If refactoring needed, do separately with `/fmod-refactor`

### 2. No New Technical Debt
- Fix should not introduce code duplication
- Maintain quality standards
- Add appropriate defensive programming
- No quick hacks that cause future problems

### 3. Complete Documentation
- Explain why bug existed
- Document how fix resolves the problem
- Add to troubleshooting if user-facing
- Update docstrings if contract changes

### 4. Regression Prevention
- Test multiple scenarios, not just the bug
- Verify related functionality
- Think about edge cases
- If possible, add automated tests (future)

---

## Architectural Enforcement

### If Bug Reveals Architectural Problem

**Note for future refactoring**:
```
[INFO] Architectural issue identified

Context:
- Bug caused by [architectural issue]
- Pattern appears in [other locations]

Suggested improvement:
- Refactor to use [better pattern]
- Extract common logic to [module]

Benefit:
- Prevent similar bugs
- Improve maintainability

Estimated effort: Medium
Skill to use: /fmod-refactor

Action: Fix bug now with minimal change, plan refactoring separately
```

### Don't Mix Fix and Refactoring

```
❌ BAD: Fix bug + refactor architecture in same commit
git commit -m "fix: Handle null values AND refactor entire module"

✅ GOOD: Fix bug, then refactor separately
git commit -m "fix: Add null check for bank_id parameter (v0.1.9)"
# Later, separate effort:
git commit -m "refactor: Extract validation logic to shared module"
```

---

## Complete Examples

### Example 1: Null Pointer Crash

**Bug Report**:
"Application crashes when clicking 'Analyze' without loading a project first"

**Workflow**:

1. **Analysis**:
   - Error: `AttributeError: 'NoneType' object has no attribute 'events'`
   - Reproduce: Open app, click Analyze without loading project
   - Symptom: Crash
   - Root cause: No validation that project is loaded

2. **Investigation**:
   ```python
   # gui/analysis.py, line 87
   def analyze_media(self):
       events = self.project.events  # ← self.project is None!
   ```

   ```bash
   grep -r "def analyze_media" fmod_importer/
   # Found: gui/analysis.py:87
   ```

3. **Planning**:
   - Minimal fix: Add check for self.project
   - Type: Defensive programming
   - Impact: None (just adds validation)

4. **Implementation**:
   ```python
   # gui/analysis.py
   def analyze_media(self):
       """Analyze media files and match to templates"""

       # Defensive check added
       if not self.project:
           messagebox.showwarning(
               "No Project Loaded",
               "Please load an FMOD project before analyzing media files.\n\n"
               "Use 'Browse Project' to select your .fspro file."
           )
           return

       # Original code continues...
       events = self.project.events
   ```

5. **Verification**:
   - ✅ Test: Click Analyze without project → Shows warning, no crash
   - ✅ Test: Load project then Analyze → Works normally
   - ✅ Test: Other workflows → No regression

6. **Documentation**:
   ```markdown
   # CHANGELOG.md
   ## [0.1.9] - 2024-12-20
   ### Fixed
   - Prevent crash when analyzing media without loading project first
   ```

   ```markdown
   # README.md Troubleshooting
   ### Analyze Button Does Nothing

   **Solution**:
   - Load an FMOD project first using 'Browse Project'
   - You should see the project path in the Project field
   ```

7. **Commit**:
   ```bash
   git commit -m "fix: Prevent crash when analyzing without project loaded (v0.1.9)

   Added defensive check for project existence before accessing project data.
   Shows user-friendly warning message with instructions."
   ```

---

### Example 2: Logic Error with Edge Case

**Bug Report**:
"Events with trailing numbers (_01, _02) not matching correctly"

**Workflow**:

1. **Analysis**:
   - Expected: "Attack_Heavy_01" should match "Attack_Heavy" template
   - Observed: No match found
   - Root cause: Iterator stripping logic not working

2. **Investigation**:
   ```python
   # naming.py, line 245
   def strip_iterator(self, name: str) -> str:
       """Strip trailing iterator like _01, _02"""
       # Current logic only handles 2-digit iterators
       if name.endswith(('_01', '_02', '_03', ..., '_99')):  # Incomplete!
           return name[:-3]
       return name
   ```

   Issue: Hard-coded list doesn't cover all cases

3. **Planning**:
   - Minimal fix: Use regex to handle any iterator pattern
   - Type: Logic correction
   - Impact: Improves matching for all numbered files

4. **Implementation**:
   ```python
   # naming.py
   import re

   def strip_iterator(self, name: str) -> str:
       """
       Strip trailing iterator like _01, _02, _A, _B.

       Now uses regex to handle any numeric or letter iterator.

       Args:
           name: Asset or event name

       Returns:
           Name with iterator stripped

       Examples:
           >>> strip_iterator("Attack_Heavy_01")
           "Attack_Heavy"
           >>> strip_iterator("Jump_A")
           "Jump"
           >>> strip_iterator("NoIterator")
           "NoIterator"
       """
       # Match _## (digits) or _A (single letter) at end
       pattern = r'_(?:\d+|[A-Z])$'
       return re.sub(pattern, '', name)
   ```

5. **Verification**:
   - ✅ Test: "Attack_Heavy_01" → "Attack_Heavy"
   - ✅ Test: "Attack_Heavy_99" → "Attack_Heavy"
   - ✅ Test: "Attack_Heavy_A" → "Attack_Heavy"
   - ✅ Test: "NoIterator" → "NoIterator" (unchanged)
   - ✅ Test: Matching workflow with numbered files → Works

6. **Documentation**:
   ```markdown
   # CHANGELOG.md
   ## [0.1.9] - 2024-12-20
   ### Fixed
   - Fix event matching for files with trailing iterators (_01, _02, etc.)
   - Iterator stripping now handles any numeric or letter suffix
   ```

7. **Commit**:
   ```bash
   git commit -m "fix: Improve iterator stripping for numbered files (v0.1.9)

   Replaced hard-coded list with regex pattern to handle any
   numeric (_01-_99+) or letter (_A-_Z) iterator suffix."
   ```

---

### Example 3: Regression from Recent Change

**Bug Report**:
"After update to v0.1.8, import creates duplicate events"

**Workflow**:

1. **Analysis**:
   - Regression: Worked in v0.1.7, broken in v0.1.8
   - Symptom: Duplicate events created
   - Need to check recent commits

2. **Investigation**:
   ```bash
   # Check commits between v0.1.7 and v0.1.8
   git log v0.1.7..v0.1.8 --oneline

   # Found suspicious commit:
   d00974a fix: Improve template duplication robustness
   ```

   ```bash
   git show d00974a
   # Shows changes to template copying logic
   ```

   ```python
   # The problematic change:
   def copy_event_from_template(self, template_id, new_name):
       # New code added:
       if new_name not in self.events:  # ← Bug: checks by name, not ID
           # Copy event
           # But events with same name but different IDs get duplicated!
   ```

3. **Planning**:
   - Minimal fix: Check by ID, not name (names can collide)
   - Type: Logic correction in recent change
   - Impact: Fixes duplication issue

4. **Implementation**:
   ```python
   def copy_event_from_template(self, template_id: str, new_name: str) -> Dict:
       """
       Copy event from template with new name.

       Fixed: Now checks for existing event by ID to prevent duplicates,
       not just by name which can collide.

       Args:
           template_id: GUID of template event
           new_name: Name for new event

       Returns:
           Created event dictionary
       """
       # Generate new event ID
       new_id = str(uuid.uuid4())

       # Fix: Check by ID, not name
       if new_id in self.events:
           # Extremely rare, but regenerate if collision
           new_id = str(uuid.uuid4())

       # Copy template
       template = self.events[template_id]
       new_event = copy.deepcopy(template)
       new_event['id'] = new_id
       new_event['name'] = new_name

       self.events[new_id] = new_event
       return new_event
   ```

5. **Verification**:
   - ✅ Test: Import with same names → No duplicates
   - ✅ Test: Import workflow v0.1.7 scenario → Works
   - ✅ Test: Multiple imports → Correct behavior

6. **Documentation**:
   ```markdown
   # CHANGELOG.md
   ## [0.1.9] - 2024-12-20
   ### Fixed
   - Fix duplicate event creation when importing with similar names
   - Regression from v0.1.8 template duplication fix
   ```

7. **Commit**:
   ```bash
   git commit -m "fix: Prevent duplicate events in template copying (v0.1.9)

   Regression introduced in v0.1.8: checked for duplicates by name
   instead of ID, causing events with same name but different IDs
   to be duplicated. Now correctly checks by unique ID.

   Fixes #45"
   ```

---

## Anti-Patterns to Avoid

### ❌ BAD: Fix Without Understanding Root Cause
```python
# Symptom: Function returns None sometimes
# "Fix": Just add if statement everywhere
if result is not None:  # Band-aid, doesn't fix root cause!
    use_result(result)
```

### ✅ GOOD: Understand and Fix Root Cause
```python
# Investigation reveals: function returns None if file missing
# Fix: Proper error handling at source
def load_data(path):
    if not Path(path).exists():
        raise FileNotFoundError(f"File not found: {path}")
    # ... load and return data (never None)
```

---

### ❌ BAD: Bare Except
```python
try:
    risky_operation()
except:  # Catches EVERYTHING, even KeyboardInterrupt!
    pass
```

### ✅ GOOD: Specific Exception
```python
try:
    risky_operation()
except (ValueError, IOError) as e:  # Specific exceptions only
    logger.error(f"Operation failed: {e}")
    messagebox.showerror("Error", f"Operation failed: {e}")
```

---

### ❌ BAD: Mixing Fix with Feature/Refactoring
```python
git commit -m "fix: null check AND add new feature AND refactor module"
# ← Doing too much at once!
```

### ✅ GOOD: Focused Fix Only
```python
git commit -m "fix: Add null check for project parameter (v0.1.9)"
# Separate commits for features and refactoring
```

---

### ❌ BAD: Technical Error Messages to Users
```python
messagebox.showerror(
    "Error",
    f"AttributeError: 'NoneType' object has no attribute 'events' at line 87"
)
# ← User doesn't understand this!
```

### ✅ GOOD: User-Friendly Messages
```python
messagebox.showerror(
    "No Project Loaded",
    "Please load an FMOD project before analyzing media files.\n\n"
    "Use the 'Browse Project' button to select your .fspro file."
)
# ← Clear, actionable guidance
```

---

## Quick Reference

### Complete Checklist

```
Phase 1: Analysis
□ Bug report read and understood
□ Bug reproduced if possible
□ Symptoms identified
□ Affected modules determined
□ Git history checked

Phase 2: Investigation
□ Relevant code found (Grep)
□ Affected modules read completely
□ Execution path traced
□ Root cause identified
□ Edge cases checked

Phase 3: Planning
□ Fix type determined (minimal vs comprehensive)
□ Refactoring necessity evaluated
□ Side effects identified
□ Defensive programming planned
□ Architectural problems noted

Phase 4: Implementation
□ Fix applied (minimal and targeted)
□ Error handling added
□ Defensive checks added
□ Docstrings updated
□ Inline comments if necessary

Phase 5: Verification
□ Original bug resolved
□ Edge cases tested
□ No regressions
□ User-friendly error messages
□ SOLID principles maintained

Phase 6: Documentation
□ Docstrings updated if behavior changes
□ CHANGELOG.md updated ("Fixed")
□ README troubleshooting if user-facing
□ VERSION bumped (patch)

Phase 7: Commit
□ Correct commit format (fix:)
□ Descriptive message
□ Version bump included
□ Issue references if applicable
```

### Common Bug Types

| Type | Root Cause | Fix Pattern |
|------|------------|-------------|
| Null Pointer | Missing validation | Add defensive check |
| Key Error | Dict access without .get() | Use .get() with default |
| Type Error | Type mismatch | Add type validation |
| Index Error | Boundary condition | Add boundary check |
| File Not Found | Missing path validation | Add file existence check |
| Permission Error | Missing permission handling | Add try/except with user message |
| Logic Error | Wrong algorithm | Correct logic/algorithm |
| Regression | Recent change broke existing | Review recent commits, fix introduced bug |

### Commit Message Template

```
fix: [Brief description] (v0.1.X)

[Detailed explanation]:
- What was the bug
- What caused it
- How the fix works
- Edge cases handled

[Optional]:
Fixes #[issue_number]
```
