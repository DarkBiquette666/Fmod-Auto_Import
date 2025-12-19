# Skill: /fmod-feature

Implémente une nouvelle fonctionnalité pour le FMOD Importer en suivant les principes SOLID, DRY, KISS et l'architecture mixin du projet.

## Objectif

Créer des fonctionnalités robustes, bien documentées et maintenables avec des commits structurés par milestone.

## Quand Utiliser Ce Skill

- ✅ L'utilisateur demande une nouvelle fonctionnalité
- ✅ Ajout de features user-facing ou internes
- ✅ Extension des capacités existantes
- ❌ Pas pour les bugs (utiliser `/fmod-debug`)
- ❌ Pas pour restructuration (utiliser `/fmod-refactor`)

## Workflow

### Étape 1: Analyse des Requirements

**Actions**:
1. Lire et comprendre complètement la demande utilisateur
2. Identifier les modules affectés:
   - GUI seulement?
   - Core logic seulement?
   - GUI + Core?
   - Nouveau module nécessaire?
3. Rechercher features similaires existantes pour réutiliser patterns
4. Vérifier si des dépendances externes sont nécessaires (éviter si possible - stdlib only!)
5. Poser questions de clarification si requirements ambigus

**Checklist**:
- [ ] Requirements clairs et complets
- [ ] Modules affectés identifiés
- [ ] Patterns existants recherchés
- [ ] Pas de nouvelles dépendances externes (ou justifiées)

**Questions à Poser** (via AskUserQuestion si nécessaire):
- Comment cette feature s'intègre-t-elle au workflow existant?
- Y a-t-il des cas d'usage edge cases spécifiques?
- Quelle est la priorité (MVP vs feature complète)?
- Comment tester cette feature manuellement?

---

### Étape 2: Planification Architecture

**Actions**:
1. **Déterminer le placement**:
   - Nouveau mixin? → Si nouvelle responsabilité GUI distincte
   - Étendre mixin existant? → Si extension responsabilité existante
   - Nouveau module core? → Si nouvelle logique métier
   - Étendre module core existant? → Si extension logique existante

2. **Vérifier line counts des fichiers cibles**:
   ```bash
   # Check current line count
   wc -l fmod_importer/gui/[target_mixin].py
   ```
   - Si >700 lignes → Planifier extraction AVANT d'ajouter feature
   - Si >800 lignes → BLOCKER: Refactorer d'abord avec `/fmod-refactor`

3. **Identifier composants réutilisables à créer**:
   - Widgets réutilisables
   - Fonctions utilitaires
   - Classes/patterns partagés

4. **Designer les interfaces** (signatures fonctions, APIs classes):
   ```python
   # Example interface design
   class NewFeatureMixin:
       def feature_method(self, param1: Type1, param2: Type2) -> ReturnType:
           """Brief description"""
           pass
   ```

5. **Vérifier compliance SOLID**:
   - **SRP**: Feature a-t-elle une responsabilité unique et bien définie?
   - **OCP**: Peut-on étendre code existant sans le modifier?
   - **LSP**: Les nouveaux mixins sont-ils composables?
   - **ISP**: L'interface est-elle focalisée (pas god class)?
   - **DIP**: Dépend-on d'abstractions, pas d'implémentations?

**Checklist**:
- [ ] Placement déterminé (mixin/module)
- [ ] Line counts vérifiés (< 800 lignes après ajout)
- [ ] Composants réutilisables identifiés
- [ ] Interfaces designées avec type hints
- [ ] SOLID compliance vérifiée

**Décision Tree - Placement**:
```
Feature Description
    │
    ├─ Logique métier pure (XML, parsing, matching)
    │  └─ Ajouter/étendre module core (project.py, naming.py, matcher.py)
    │
    ├─ Interface utilisateur (widgets, dialogs)
    │  └─ Ajouter/étendre GUI mixin
    │     │
    │     ├─ Extension de responsabilité existante
    │     │  └─ Étendre mixin existant (ex: WidgetsMixin pour nouveau widget)
    │     │
    │     └─ Nouvelle responsabilité distincte
    │        └─ Créer nouveau mixin
    │
    └─ Les deux (logique + UI)
       └─ Commencer par core, puis GUI
```

---

### Étape 3: Implémentation par Milestones

#### Milestone 1: Core Logic (sans GUI)

**Actions**:
1. Implémenter logique métier dans module core approprié
2. Écrire docstrings complètes (suivre standard `_protocol-rules.md`)
3. Ajouter type hints pour tous paramètres et returns
4. Implémenter error handling approprié
5. Tester manuellement dans Python REPL si possible

**Exemple**:
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
- [ ] Logique core implémentée
- [ ] Docstrings complètes avec Args/Returns/Raises/Examples
- [ ] Type hints sur tous paramètres
- [ ] Error handling présent
- [ ] Testé manuellement si possible

#### Milestone 2: Intégration GUI

**Actions**:
1. Créer/étendre mixin approprié
2. Connecter logique core aux événements GUI
3. Ajouter placeholder management si nécessaire
4. Suivre patterns widgets existants (voir `widgets.py`)
5. Implémenter error handling avec messagebox user-friendly
6. Tester interaction end-to-end

**Exemple**:
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
- [ ] Mixin créé/étendu
- [ ] Core logic connecté à GUI events
- [ ] Error handling avec messagebox user-friendly
- [ ] Patterns existants suivis
- [ ] Testé end-to-end

#### Milestone 3: Documentation Complète

**Actions**:
1. **README.md**: Ajouter feature documentation
   - Section "Description": Mentionner nouvelle feature
   - Section "Usage": Instructions utilisation
   - Section "Troubleshooting": Erreurs potentielles

2. **CHANGELOG.md**: Ajouter entrée sous "Added"
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

4. **Docstrings**: Vérifier toutes les nouvelles fonctions/classes ont docstrings complètes

5. **Inline comments**: Ajouter uniquement pour logique non-évidente

**Template README.md Addition**:
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
- [ ] CHANGELOG.md updated sous "Added"
- [ ] VERSION bumped (minor pour feat)
- [ ] Toutes docstrings complètes
- [ ] Inline comments uniquement si nécessaire

---

### Étape 4: Quality Checks

**Avant de committer, vérifier**:

#### Architecture
- [ ] **SOLID compliance**:
  - [ ] SRP: Une responsabilité par classe/fonction
  - [ ] OCP: Extension par composition
  - [ ] DIP: Pas de dépendances concrètes GUI↔Core

- [ ] **Séparation des responsabilités**:
  - [ ] Logique métier dans core modules
  - [ ] Interface dans GUI mixins
  - [ ] Pas de code GUI dans core
  - [ ] Pas de logique métier complexe dans GUI

#### Code Quality
- [ ] **DRY**: Pas de duplication code
  - Si code similaire existe, extraire fonction réutilisable
  - Vérifier duplication entre nouveaux et anciens modules

- [ ] **Line Counts**:
  ```bash
  wc -l fmod_importer/gui/*.py fmod_importer/*.py
  ```
  - [ ] Aucun fichier >800 lignes
  - [ ] Si approche 750, suggérer refactoring futur

- [ ] **Error Handling**:
  - [ ] try/except autour d'opérations risquées
  - [ ] Messages d'erreur user-friendly (messagebox)
  - [ ] Pas de bare except clauses

- [ ] **Type Hints**:
  - [ ] Tous paramètres et returns typés
  - [ ] Import typing si nécessaire

- [ ] **Naming**:
  - [ ] Noms clairs et descriptifs
  - [ ] Follow Python conventions (snake_case)
  - [ ] Pas d'abréviations obscures

#### Documentation
- [ ] **Docstrings**:
  - [ ] Toutes fonctions/classes publiques documentées
  - [ ] Format standard (Args, Returns, Raises, Examples)
  - [ ] Expliquent WHY, pas juste WHAT

- [ ] **README.md**:
  - [ ] Feature mentionnée dans Description
  - [ ] Instructions usage ajoutées
  - [ ] Troubleshooting mis à jour

- [ ] **CHANGELOG.md**:
  - [ ] Entrée sous "Added" pour nouvelle version
  - [ ] Description claire de la feature

- [ ] **VERSION**:
  - [ ] Bumped correctement (feat = minor bump)

#### Testing Manuel
- [ ] Feature fonctionne end-to-end
- [ ] Edge cases testés
- [ ] Error handling vérifié (provoquer erreurs)
- [ ] Pas de regressions sur features existantes

---

### Étape 5: Commits par Milestone

**Stratégie**: Commits groupés par milestone (config utilisateur)

#### Option 1: Commits Séparés par Milestone
```bash
# Milestone 1: Core
git add fmod_importer/project.py
git commit -m "feat(core): Add event filtering by bank name (v0.2.0)

Implements filter_events_by_bank() method to filter events
belonging to a specific bank. Includes comprehensive error
handling and validation.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Milestone 2: GUI
git add fmod_importer/gui/widgets.py
git commit -m "feat(gui): Add bank filter widget to UI

Adds dropdown filter to allow users to filter events by bank.
Integrates with core filtering logic from project module.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Milestone 3: Documentation
git add README.md CHANGELOG.md fmod_importer/__init__.py
git commit -m "docs: Document bank filtering feature

Updates README with usage instructions, adds CHANGELOG entry,
and bumps version to 0.2.0.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

#### Option 2: Commit Unique (pour features simples)
```bash
git add fmod_importer/project.py fmod_importer/gui/widgets.py README.md CHANGELOG.md fmod_importer/__init__.py
git commit -m "feat: Add bank filtering feature (v0.2.0)

Implements event filtering by bank name:
- Core filtering logic in project module
- GUI dropdown filter widget
- Full documentation and troubleshooting

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

**Règle de Choix**:
- 3 commits si milestones bien distinctes et feature complexe
- 1 commit si feature simple et cohérente

**Format commit** (voir `_protocol-rules.md`):
```
feat(scope): Brief description (vX.Y.Z)

Detailed explanation:
- What was added
- Why it was added
- How it works

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

### Étape 6: Post-Implémentation

**Actions proactives**:

1. **Vérifier seuils** et suggérer si nécessaire:
   ```bash
   wc -l fmod_importer/gui/*.py | sort -rn | head -5
   ```

   Si fichiers approchent seuils, suggérer:
   ```
   [INFO] widgets.py approaching 750 lines

   État actuel:
   - widgets.py: 745 lines

   Amélioration suggérée:
   - Consider planning refactoring before hitting 800-line threshold
   - Possible extraction: widget factory functions to separate module

   Bénéfice:
   - Maintient modularité
   - Prevent future violations

   Effort estimé: Low
   Skill à utiliser: /fmod-refactor
   ```

2. **Identifier améliorations connexes** (optionnel):
   - Features similaires qui pourraient bénéficier du même pattern
   - Code existant qui pourrait être refactoré avec nouveau pattern
   - Documentation qui pourrait être améliorée

3. **Noter technical debt** (si créé):
   - TODOs pour améliorations futures
   - Limitations connues
   - Optimisations potentielles

**Checklist Post-Implementation**:
- [ ] Seuils ligne vérifiés, suggestions faites si approchent limites
- [ ] Améliorations connexes identifiées
- [ ] Technical debt documenté si applicable

---

## Triggers Automatiques

### Pendant Planification

#### Fichier Approche 800 Lignes
```
[RECOMMEND] Threshold: Target file approaching 800-line limit

État actuel:
- [filename].py: [current] lines
- Adding [feature] will add ~[estimated] lines

Amélioration suggérée:
- Refactor [filename].py BEFORE adding new feature
- Use /refactor to split into smaller modules

Bénéfice:
- Maintain modularity
- Prevent exceeding 800-line threshold
- Easier to add feature after refactoring

Effort estimé: Medium
Skill à utiliser: /fmod-refactor
```

### Pendant Implémentation

#### Duplication Détectée
```
[SUGGEST] Pattern: Similar code found in existing module

État actuel:
- New code similar to [existing_module.py:line_range]

Amélioration suggérée:
- Extract common logic to shared utility function
- Location: fmod_importer/gui/utils.py or fmod_importer/utils.py

Bénéfice:
- DRY principle
- Single source of truth
- Easier maintenance

Effort estimé: Low
```

#### GUI Code dans Core Module
```
[VIOLATION] Architecture: GUI code in core module

État actuel:
- [core_module.py] imports tkinter or uses GUI components

Amélioration suggérée:
- Move GUI logic to appropriate mixin
- Core module should be GUI-agnostic
- Pass data to GUI layer, don't create widgets in core

Bénéfice:
- Respect Dependency Inversion Principle
- Testability
- Separation of concerns

Effort estimé: Low
Skill à utiliser: /fmod-refactor
```

---

## Exemples Complets

### Exemple 1: Simple Feature (1 Milestone)

**Demande**: "Add a 'Clear All' button to reset all fields"

**Exécution**:

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

### Exemple 2: Complex Feature (3 Milestones)

**Demande**: "Add ability to export import results to JSON file"

**Exécution**:

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

## Anti-Patterns à Éviter

### ❌ BAD: Tout dans un Seul Commit
```bash
# Commits 1000 lines of changes without structure
git commit -m "Add feature"
```

### ✅ GOOD: Commits Structurés par Milestone
```bash
git commit -m "feat(core): Add core logic (v0.2.0)"
git commit -m "feat(gui): Add UI components"
git commit -m "docs: Document new feature"
```

---

### ❌ BAD: Pas de Documentation
```python
def filter_events(self, bank_id):
    # No docstring
    return [e for e in self.events if e['bank'] == bank_id]
```

### ✅ GOOD: Documentation Complète
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

### ❌ BAD: GUI Logic dans Core Module
```python
# project.py
import tkinter as tk
from tkinter import messagebox

def create_event(self):
    messagebox.showinfo("Success", "Event created")  # GUI in core!
```

### ✅ GOOD: Séparation Core/GUI
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

### ❌ BAD: Pas de Error Handling
```python
def load_file(self, path):
    with open(path) as f:  # What if file doesn't exist?
        return f.read()
```

### ✅ GOOD: Error Handling Approprié
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

## Référence Rapide

### Checklist Complète

```
Phase 1: Analysis
□ Requirements compris
□ Modules affectés identifiés
□ Patterns existants recherchés
□ Questions posées si ambigu

Phase 2: Planning
□ Placement déterminé
□ Line counts vérifiés (<800)
□ Composants réutilisables identifiés
□ Interfaces designées
□ SOLID compliance vérifiée

Phase 3: Implementation
M1 - Core Logic:
  □ Logique implémentée
  □ Docstrings complètes
  □ Type hints
  □ Error handling
  □ Testé manuellement

M2 - GUI Integration:
  □ Mixin créé/étendu
  □ Core connecté à GUI
  □ Error handling user-friendly
  □ Patterns suivis
  □ Testé end-to-end

M3 - Documentation:
  □ README.md updated
  □ CHANGELOG.md updated
  □ VERSION bumped
  □ Docstrings complètes

Phase 4: Quality Checks
□ SOLID compliance
□ DRY (no duplication)
□ Line counts <800
□ Error handling
□ Type hints
□ Naming clear
□ Documentation complète
□ Testing manuel

Phase 5: Commits
□ Commits par milestone ou unique
□ Format Conventional Commits
□ Messages descriptifs
□ Version bump incluse

Phase 6: Post-Implementation
□ Seuils vérifiés
□ Suggestions faites si nécessaire
□ Améliorations connexes notées
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
