# Skill: /fmod-debug

Diagnostique et corrige les bugs de manière structurée tout en maintenant la qualité du code et en prévenant les régressions.

## Objectif

Résoudre les bugs efficacement avec des fixes ciblés, bien documentés et testés.

## Quand Utiliser Ce Skill

- ✅ L'utilisateur signale un bug ou une erreur
- ✅ Comportement inattendu observé
- ✅ Crash ou exception détectée
- ❌ Pas pour nouvelle feature (utiliser `/fmod-feature`)
- ❌ Pas pour amélioration code (utiliser `/fmod-refactor`)

## Workflow

### Étape 1: Analyse du Bug Report

**Actions**:
1. **Lire le bug report complètement**:
   - Description du problème
   - Étapes de reproduction (si fournies)
   - Message d'erreur (si applicable)
   - Comportement attendu vs observé

2. **Reproduire le bug** (si étapes disponibles):
   ```python
   # Try to reproduce in similar conditions
   # Note exact error message and stack trace
   ```

3. **Identifier symptômes vs root cause**:
   - **Symptôme**: Ce que l'utilisateur voit (ex: crash, message erreur)
   - **Root cause**: La vraie raison du problème (ex: validation manquante, null pointer)

4. **Déterminer modules affectés**:
   - GUI only?
   - Core logic only?
   - Both?
   - External dependency?

5. **Vérifier si régression**:
   ```bash
   git log -p --all -S "relevant_code_pattern"
   # Check recent commits that might have introduced bug
   ```

**Checklist**:
- [ ] Bug report lu et compris
- [ ] Bug reproduit (si possible)
- [ ] Symptômes identifiés
- [ ] Modules affectés déterminés
- [ ] Historique git vérifié pour regressions

**Questions à Poser** (si information manquante):
- Quelles sont les étapes exactes pour reproduire?
- Quel est le message d'erreur complet (avec stack trace)?
- Cela fonctionnait-il auparavant?
- Dans quelles conditions le bug apparaît-il?

---

### Étape 2: Investigation Root Cause

**Actions**:

1. **Rechercher code pertinent avec Grep**:
   ```bash
   # Search for error message
   grep -r "error message text" fmod_importer/

   # Search for function/class mentioned in stack trace
   grep -r "function_name" fmod_importer/

   # Search for relevant operations
   grep -r "load_project\|parse_xml" fmod_importer/
   ```

2. **Lire modules affectés complètement**:
   - Ne pas se fier uniquement à la ligne d'erreur
   - Comprendre le contexte complet
   - Tracer le flux d'exécution

3. **Tracer le chemin d'exécution**:
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

4. **Identifier l'assumption cassée ou l'erreur logique**:
   - Validation manquante?
   - Null pointer non géré?
   - Type mismatch?
   - Race condition?
   - Edge case non prévu?

5. **Vérifier pour edge cases non gérés**:
   - Empty inputs
   - Null/None values
   - File doesn't exist
   - Invalid format
   - Boundary conditions

6. **Reviewer commits récents**:
   ```bash
   git log --oneline --all -20
   git show <commit-hash>  # Review suspicious commits
   ```

**Checklist**:
- [ ] Code pertinent trouvé et lu
- [ ] Chemin d'exécution tracé
- [ ] Assumption cassée identifiée
- [ ] Edge cases vérifiés
- [ ] Commits récents reviewés

**Techniques d'Investigation**:

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

### Étape 3: Planification du Fix

**Actions**:

1. **Déterminer type de fix**:

   **Fix Minimal** (préféré):
   - Adresse uniquement le bug spécifique
   - Changements minimaux
   - Facile à reviewer et tester
   - Réduit risque de régression

   **Fix Comprehensive**:
   - Adresse bug + problèmes reliés
   - Peut nécessiter refactoring
   - Utilisé si fix minimal crée technical debt
   - Nécessite plus de testing

2. **Évaluer si refactoring nécessaire**:
   - Fix minimal possible? → Faire fix minimal
   - Architecture problématique révélée? → Noter pour `/fmod-refactor` futur
   - Fix impossible sans refactoring? → Utiliser `/fmod-refactor` d'abord

3. **Identifier effets secondaires potentiels**:
   - Quels autres code paths utilisent cette fonction?
   - Y a-t-il des dépendances sur le comportement actuel?
   - Le fix pourrait-il casser autre chose?

4. **Planifier defensive programming**:
   - Quelle validation ajouter?
   - Quel error handling manque?
   - Quels edge cases protéger?

5. **Considérer si fix révèle problème architectural**:
   - Pattern récurrent de bugs similaires?
   - Design flaw sous-jacent?
   - → Noter pour discussion/refactoring futur

**Checklist**:
- [ ] Type de fix déterminé (minimal vs comprehensive)
- [ ] Besoin de refactoring évalué
- [ ] Effets secondaires identifiés
- [ ] Defensive programming planifié
- [ ] Problèmes architecturaux notés

**Decision Tree - Type de Fix**:
```
Bug Analysis
    │
    ├─ Simple logic error, localized
    │  └─ Fix minimal (change 1-5 lines)
    │
    ├─ Missing validation/error handling
    │  └─ Fix minimal (add defensive checks)
    │
    ├─ Edge case non géré
    │  └─ Fix minimal (add edge case handling)
    │
    ├─ Design flaw mineur
    │  └─ Fix minimal now, note for refactoring later
    │
    └─ Design flaw majeur
       └─ Use /fmod-refactor, then apply fix
```

---

### Étape 4: Implémentation

**Actions**:

1. **Appliquer fix minimal et ciblé**:
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

2. **Ajouter error handling si manquant**:
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

3. **Ajouter defensive checks pour edge cases**:
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

4. **Mettre à jour docstrings si comportement change**:
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

5. **Ajouter inline comments expliquant fix** (si non-évident):
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
- [ ] Fix appliqué (minimal et ciblé)
- [ ] Error handling ajouté si manquant
- [ ] Defensive checks pour edge cases
- [ ] Docstrings mis à jour si comportement change
- [ ] Inline comments ajoutés si fix non-évident

**Patterns de Fix Communs**:

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

### Étape 5: Vérification

**Actions**:

1. **Tester scénario bug original**:
   - Reproduire les étapes exactes qui causaient le bug
   - Vérifier que l'erreur ne se produit plus
   - Vérifier que le comportement est correct

2. **Tester edge cases**:
   - Empty inputs
   - Null/None values
   - Boundary conditions
   - Invalid inputs
   - Large datasets

3. **Vérifier pas de regressions**:
   - Tester fonctionnalités reliées
   - Vérifier les cas d'usage principaux
   - Tester workflows complets

4. **Vérifier messages d'erreur user-friendly**:
   - Messages clairs et compréhensibles?
   - Instructions pour résoudre?
   - Pas de stack traces exposés à l'utilisateur?

5. **Valider pas de violation principes SOLID**:
   - Fix maintient Single Responsibility?
   - Pas de couplage ajouté?
   - Pas de duplication introduite?

**Checklist**:
- [ ] Scénario bug original testé et résolu
- [ ] Edge cases testés
- [ ] Pas de regressions détectées
- [ ] Messages d'erreur user-friendly vérifiés
- [ ] Principes SOLID maintenus

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

### Étape 6: Documentation Updates

**Actions**:

1. **Mettre à jour docstrings** (si comportement fonction a changé):
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

2. **Ajouter à CHANGELOG.md** sous "Fixed":
   ```markdown
   ## [Unreleased]
   ### Fixed
   - Fix crash when importing manually matched orphan events without template
   - Add validation for empty project paths with user-friendly error messages
   ```

3. **Ajouter à README troubleshooting** (si bug user-facing):
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

4. **Mettre à jour VERSION** (patch bump pour fix):
   ```python
   # fmod_importer/__init__.py
   VERSION = "0.1.9"  # Was "0.1.8"
   ```

**Checklist**:
- [ ] Docstrings mis à jour si comportement changé
- [ ] CHANGELOG.md updated sous "Fixed"
- [ ] README troubleshooting ajouté si user-facing
- [ ] VERSION bumped (patch pour fix)

---

### Étape 7: Commit

**Stratégie**: Commit unique pour bugs simples, multiple commits si fix complexe

#### Commit Simple (préféré)
```bash
git add fmod_importer/gui/import_workflow.py
git commit -m "fix: Handle missing matched_template field for orphan events (v0.1.9)

Previously, importing manually matched orphan events would cause
KeyError because they don't have matched_template field. Added
defensive check using .get() with fallback to basic event creation.

Fixes #42

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git add CHANGELOG.md fmod_importer/__init__.py
git commit -m "docs: Update changelog for orphan event fix

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

#### Commit Multiple (si fix + tests + docs complexes)
```bash
# Fix principal
git commit -m "fix: Add validation for empty project paths (v0.1.9)"

# Tests (si infrastructure de tests existe)
git commit -m "test: Add test cases for empty path handling"

# Documentation
git commit -m "docs: Document empty path validation in troubleshooting"
```

**Format** (voir `_protocol-rules.md`):
```
fix: Brief description of what was fixed (vX.Y.Z)

Detailed explanation:
- What was the bug
- What caused it
- How it was fixed
- Why this approach was chosen

Fixes #issue_number (if applicable)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Commit Prefixes Spéciaux**:
- `fix: CRITICAL -` pour bugs sévères (data loss, security, crashes)
- `fix: HOTFIX -` pour fixes urgents en production
- `fix!:` pour breaking changes dans fix (rare)

---

## Principes Clés

### 1. Fix Minimal et Ciblé
- Ne pas mélanger fix avec refactoring
- Adresser uniquement le bug spécifique
- Pas de "scope creep" (ajouter features non reliées)
- Si refactoring nécessaire, faire séparément avec `/fmod-refactor`

### 2. Pas de Nouvelles Technical Debt
- Fix ne doit pas introduire duplication code
- Maintenir standards de qualité
- Ajouter defensive programming approprié
- Pas de quick hacks qui causent problèmes futurs

### 3. Documentation Complète
- Expliquer pourquoi bug existait
- Documenter comment fix résout le problème
- Ajouter à troubleshooting si user-facing
- Mettre à jour docstrings si contrat change

### 4. Prévention des Régressions
- Tester scénarios multiples, pas juste le bug
- Vérifier fonctionnalités reliées
- Penser aux edge cases
- Si possible, ajouter tests automatisés (futur)

---

## Architectural Enforcement

### Si Bug Révèle Problème Architectural

**Noter pour refactoring futur**:
```
[INFO] Architectural issue identified

Context:
- Bug caused by [architectural issue]
- Pattern appears in [other locations]

Suggested improvement:
- Refactor to use [better pattern]
- Extract common logic to [module]

Bénéfice:
- Prevent similar bugs
- Improve maintainability

Effort estimé: Medium
Skill à utiliser: /fmod-refactor

Action: Fix bug now with minimal change, plan refactoring separately
```

### Ne Pas Mélanger Fix et Refactoring

```
❌ BAD: Fix bug + refactor architecture in same commit
git commit -m "fix: Handle null values AND refactor entire module"

✅ GOOD: Fix bug, then refactor separately
git commit -m "fix: Add null check for bank_id parameter (v0.1.9)"
# Later, separate effort:
git commit -m "refactor: Extract validation logic to shared module"
```

---

## Exemples Complets

### Exemple 1: Crash avec Null Pointer

**Bug Report**:
"Application crashes when clicking 'Analyze' without loading a project first"

**Workflow**:

1. **Analysis**:
   - Error: `AttributeError: 'NoneType' object has no attribute 'events'`
   - Reproduire: Ouvrir app, cliquer Analyze sans charger projet
   - Symptom: Crash
   - Root cause: Pas de validation que projet est chargé

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
   - Fix minimal: Add check for self.project
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
   Shows user-friendly warning message with instructions.

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   ```

---

### Exemple 2: Logic Error avec Edge Case

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
   - Fix minimal: Use regex to handle any iterator pattern
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
   numeric (_01-_99+) or letter (_A-_Z) iterator suffix.

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   ```

---

### Exemple 3: Regression from Recent Change

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
   - Fix minimal: Check by ID, not name (names can collide)
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

   Fixes #45

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   ```

---

## Anti-Patterns à Éviter

### ❌ BAD: Fix Sans Comprendre Root Cause
```python
# Symptom: Function returns None sometimes
# "Fix": Just add if statement everywhere
if result is not None:  # Band-aid, doesn't fix root cause!
    use_result(result)
```

### ✅ GOOD: Comprendre et Fix Root Cause
```python
# Investigation révèle: fonction return None si fichier manquant
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

## Référence Rapide

### Checklist Complète

```
Phase 1: Analysis
□ Bug report lu et compris
□ Bug reproduit si possible
□ Symptômes identifiés
□ Modules affectés déterminés
□ Git history vérifié

Phase 2: Investigation
□ Code pertinent trouvé (Grep)
□ Modules affectés lus complètement
□ Chemin d'exécution tracé
□ Root cause identifiée
□ Edge cases vérifiés

Phase 3: Planning
□ Type de fix déterminé (minimal vs comprehensive)
□ Refactoring necessity évaluée
□ Effets secondaires identifiés
□ Defensive programming planifié
□ Problèmes architecturaux notés

Phase 4: Implementation
□ Fix appliqué (minimal et ciblé)
□ Error handling ajouté
□ Defensive checks ajoutés
□ Docstrings updated
□ Inline comments si nécessaire

Phase 5: Verification
□ Bug original résolu
□ Edge cases testés
□ Pas de regressions
□ Error messages user-friendly
□ SOLID principles maintenus

Phase 6: Documentation
□ Docstrings updated si comportement change
□ CHANGELOG.md updated ("Fixed")
□ README troubleshooting si user-facing
□ VERSION bumped (patch)

Phase 7: Commit
□ Commit format correct (fix:)
□ Message descriptif
□ Version bump incluse
□ Références issue si applicable
```

### Type de Bugs Communs

| Type | Root Cause | Fix Pattern |
|------|------------|-------------|
| Null Pointer | Validation manquante | Add defensive check |
| Key Error | Dict access sans .get() | Use .get() with default |
| Type Error | Type mismatch | Add type validation |
| Index Error | Boundary condition | Add boundary check |
| File Not Found | Path validation manquante | Add file existence check |
| Permission Error | Permission handling manquant | Add try/except with user message |
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

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```
