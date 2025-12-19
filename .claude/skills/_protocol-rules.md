# Règles du Protocole FMOD Importer

Ce fichier contient les règles globales partagées par tous les skills du projet FMOD Importer.

## Principes d'Architecture

### SOLID

#### Single Responsibility Principle (SRP)
- Chaque classe/fonction a UNE responsabilité claire
- Les méthodes effectuent UNE tâche cohérente
- Les mixins addressent UN aspect de la fonctionnalité GUI

**Vérification**:
- La classe peut-elle être décrite en une phrase sans "et" ?
- Le changement d'une exigence métier n'affecte-t-il qu'une seule raison de modifier cette classe ?

#### Open/Closed Principle (OCP)
- Étendre le comportement via composition (mixins) non modification
- Utiliser héritage/patterns pour ajouter features sans changer code existant

**Vérification**:
- Les nouvelles features sont-elles ajoutées via nouveaux mixins/classes plutôt que modifier l'existant ?

#### Liskov Substitution Principle (LSP)
- Les mixins peuvent être composés sans casser FmodImporterGUI
- Les sous-classes préservent les contrats des classes de base

**Vérification**:
- Les mixins peuvent-ils être ajoutés/retirés sans casser le GUI ?

#### Interface Segregation Principle (ISP)
- Les mixins exposent uniquement les méthodes pertinentes
- Pas de "god classes" avec méthodes non-reliées

**Vérification**:
- Les classes utilisent-elles toutes les méthodes des interfaces qu'elles implémentent ?

#### Dependency Inversion Principle (DIP)
- Dépendre d'abstractions (NamingPattern, AudioMatcher) non d'implémentations concrètes
- Les modules core (project, naming, matcher) sont indépendants du GUI

**Vérification**:
- Les modules core importent-ils des modules GUI ? (NON!)
- Les dépendances pointent-elles vers des abstractions ?

### DRY (Don't Repeat Yourself)
- Extraire logique répétée dans fonctions utilitaires
- Créer composants réutilisables à la 3ème occurrence de code similaire
- Vérifier duplication entre modules

**Triggers**:
- Code bloc identique/similaire apparaît 3+ fois → EXTRAIRE

### KISS (Keep It Simple, Stupid)
- Préférer solutions simples aux solutions clever
- Éviter optimisation prématurée
- Noms de variables/fonctions clairs

**Vérification**:
- Le code est-il facile à comprendre pour quelqu'un qui ne connaît pas le projet ?
- Y a-t-il une solution plus simple ?

### WYSIWYG (What You See Is What You Get)
- Le comportement du code correspond à son apparence
- Pas d'effets secondaires cachés
- Explicite vaut mieux qu'implicite

**Vérification**:
- Les fonctions font-elles exactement ce que leur nom suggère ?
- Y a-t-il des effets secondaires non documentés ?

### SSOT (Single Source of Truth)
- VERSION dans `__init__.py` uniquement
- Configuration en un seul endroit
- Éviter duplication structures de données

**Vérification**:
- Les données sont-elles dupliquées quelque part ?
- Y a-t-il plusieurs sources pour la même information ?

### Modularité
- Frontières de modules claires
- Couplage minimal entre modules
- Haute cohésion à l'intérieur des modules

**Architecture cible**:
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

## Seuils et Métriques

### Seuils de Ligne de Code

| Seuil | Action | Niveau |
|-------|--------|--------|
| 750 lignes | Planifier refactoring avant 800 | `[INFO]` |
| 800 lignes | Refactoring recommandé | `[RECOMMEND]` |
| 900 lignes (mixin) | Splitter mixin ou extraire utilities | `[RECOMMEND]` |
| 1000 lignes | Maximum absolu pour mixins | `[CRITICAL]` |

### Seuils de Complexité

| Métrique | Seuil | Action |
|----------|-------|--------|
| Lignes fonction | 40 lignes | Splitter fonction |
| Lignes fonction | 50 lignes | Refactoring requis |
| Profondeur nesting | 3 niveaux | Extraire nested logic |
| Nombre paramètres | 5 paramètres | Parameter object ou config dict |
| Chaîne if/elif | 5 conditions | Dict dispatch ou polymorphisme |
| Bloc try/except | 20 lignes | Extraire dans fonction séparée |

---

## Triggers Automatiques

### Pattern Triggers

#### Duplication de Code
```
[SUGGEST] Pattern: Code dupliqué détecté

État actuel:
- [Bloc de code] apparaît dans [N] fichiers

Amélioration suggérée:
- Extraire dans fonction réutilisable dans [module approprié]

Bénéfice:
- Single Source of Truth
- Plus facile à maintenir
- Réduit taille codebase

Effort estimé: Low
Skill à utiliser: /fmod-refactor
```

#### Structures Similaires
```
[SUGGEST] Pattern: Classes avec structures similaires

État actuel:
- [ClassA] et [ClassB] ont [N] méthodes similaires

Amélioration suggérée:
- Créer abstract base class ou mixin partagé

Bénéfice:
- Réutilisabilité
- Cohérence
- Facilite maintenance

Effort estimé: Medium
Skill à utiliser: /fmod-refactor
```

### Architecture Triggers

#### GUI Code dans Core
```
[VIOLATION] Architecture: Code GUI dans module core

État actuel:
- [core_module.py] importe/utilise tkinter ou GUI components

Amélioration suggérée:
- Déplacer logique GUI vers mixin approprié
- Garder core modules GUI-agnostic

Bénéfice:
- Respect Dependency Inversion Principle
- Testabilité améliorée
- Séparation des responsabilités

Effort estimé: Medium
Skill à utiliser: /fmod-refactor
```

#### Business Logic dans GUI
```
[RECOMMEND] Architecture: Logique métier dans GUI

État actuel:
- [gui_mixin.py] contient logique métier complexe

Amélioration suggérée:
- Extraire vers module core approprié
- GUI appelle module core

Bénéfice:
- Réutilisabilité logique métier
- Plus facile à tester
- Séparation claire des responsabilités

Effort estimé: Medium
Skill à utiliser: /fmod-refactor
```

#### Dépendance Circulaire
```
[CRITICAL] Architecture: Dépendance circulaire détectée

État actuel:
- [ModuleA] importe [ModuleB] qui importe [ModuleA]

Amélioration suggérée:
- Refactorer pour éliminer cycle
- Options: Dependency Injection, Event System, Extract Common Module

Bénéfice:
- Code maintenable
- Évite bugs subtils
- Architecture plus claire

Effort estimé: High
Skill à utiliser: /fmod-refactor
```

---

## Standards de Documentation

### Docstrings

#### Format Standard
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

#### Docstrings de Classe
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

#### Docstrings de Module
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

#### Quand Mettre à Jour
- ✅ Nouvelle feature user-facing → Update "Description" et "Usage"
- ✅ Nouveau workflow → Add "Recommended Workflow"
- ✅ Nouvelle erreur possible → Add "Troubleshooting"
- ✅ Changement UI → Update descriptions/screenshots
- ✅ Version bump → Update version en bas

#### Template Section Feature
```markdown
### [Nom de la Feature]

[Description de ce que fait la feature et pourquoi elle est utile]

**Comment utiliser**:
1. [Étape 1]
2. [Étape 2]
3. [Étape 3]

**Exemple**:
[Exemple concret d'utilisation]

**Notes**:
- [Point important 1]
- [Point important 2]
```

#### Template Troubleshooting
```markdown
### [Problème]

**Symptômes**:
- [Symptôme 1]
- [Symptôme 2]

**Cause**:
[Explication de la cause]

**Solution**:
1. [Étape de résolution 1]
2. [Étape de résolution 2]

**Alternative**:
[Solution alternative si applicable]
```

### CHANGELOG.md

#### Format
Suivre [Keep a Changelog](https://keepachangelog.com/):

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

#### Triggers Update
- `feat` commit → Ajouter sous "Added"
- `fix` commit → Ajouter sous "Fixed"
- `refactor` majeur → Ajouter sous "Changed"
- Breaking change → Note sous section appropriée + mention BREAKING CHANGE

---

## Conventions de Commit

### Format (Conventional Commits)
```
<type>(<scope>): <subject> (<version>)

<body>

<footer>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Types de Commit

| Type | Description | Version Bump | Exemple |
|------|-------------|--------------|---------|
| `feat` | Nouvelle feature | Minor (0.1.0→0.2.0) | `feat(gui): Add bank filter widget` |
| `fix` | Bug fix | Patch (0.1.0→0.1.1) | `fix: Handle empty template folders` |
| `refactor` | Restructuration code | None* | `refactor: Extract XML handler module` |
| `docs` | Documentation seule | None | `docs: Update README troubleshooting` |
| `test` | Ajout/update tests | None | `test: Add matcher unit tests` |
| `chore` | Maintenance | None | `chore: Update build script` |
| `perf` | Performance | Patch si significatif | `perf: Optimize event matching` |
| `style` | Formatting | None | `style: Fix PEP8 violations` |

*Refactor = Minor bump si changement architectural majeur

### Scopes (optionnel)

| Scope | Utilisation |
|-------|-------------|
| `gui` | Changements GUI (mixins, widgets) |
| `core` | Modules core (project, naming, matcher) |
| `build` | Système de build (PyInstaller, CI/CD) |
| `deps` | Dépendances |

### Règles de Subject
- Maximum 72 caractères
- Imperative mood (Add, Fix, Refactor, not Added, Fixed, Refactored)
- Pas de point final
- Commencer par minuscule après le type

### Body (optionnel mais recommandé pour changements complexes)
- Expliquer POURQUOI, pas QUOI (le diff montre le quoi)
- Wrapper à 72 caractères
- Séparer subject et body par ligne blanche

### Footer (optionnel)
- Breaking changes: `BREAKING CHANGE: description`
- Issue references: `Fixes #123` ou `Closes #456`
- Co-authors (toujours inclure Claude)

### Exemples

#### Simple Feature
```
feat(gui): Add event preview panel (v0.2.0)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

#### Bug Fix avec Détails
```
fix: Prevent crash when loading empty projects (v0.1.9)

Previously, loading a project with no events would cause
a NullPointerException in the analysis workflow. Added
defensive checks and user-friendly error message.

Fixes #42

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

#### Refactoring Majeur
```
refactor: Split project.py into focused modules (v0.2.0)

Project module exceeded 1075 lines, violating 800-line threshold.
Split into:
- project.py: Core project management (420 lines)
- xml_handler.py: XML operations (350 lines)
- cache.py: Caching logic (240 lines)

Improves Single Responsibility Principle and maintainability.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

#### Breaking Change
```
feat!: Change naming pattern API to accept separator (v1.0.0)

BREAKING CHANGE: NamingPattern constructor now requires
separator parameter. Update all instantiations:

Before: NamingPattern(pattern_str)
After: NamingPattern(pattern_str, separator='_')

Migration: Add separator='_' to all NamingPattern calls.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

## Version Bumping

### Semantic Versioning (MAJOR.MINOR.PATCH)

#### MAJOR (1.0.0)
- Breaking changes
- Changements API incompatibles
- Modifications architectural majeurs

#### MINOR (0.1.0)
- Nouvelles features (backward-compatible)
- Commits `feat`
- Refactoring architectural significatif

#### PATCH (0.1.1)
- Bug fixes
- Commits `fix`
- Performance improvements significatifs

### Process de Version Bump

1. **Déterminer le type de bump** basé sur commits depuis dernière version
2. **Mettre à jour VERSION** dans `fmod_importer/__init__.py`
3. **Mettre à jour CHANGELOG.md** avec nouvelle section version
4. **Inclure version dans message commit**: `(vX.Y.Z)`

### Exemple
```python
# fmod_importer/__init__.py
VERSION = "0.2.0"  # Was "0.1.8"
```

```markdown
# CHANGELOG.md
## [0.2.0] - 2024-12-20
### Added
- Event filtering by bank name
- JSON export functionality
```

```bash
git commit -m "feat(gui): Add bank filter widget (v0.2.0)"
```

---

## Quality Checks Checklist

Avant chaque commit, vérifier:

### Architecture
- [ ] Principes SOLID respectés
- [ ] Pas de code GUI dans modules core
- [ ] Pas de logique métier complexe dans GUI
- [ ] Pas de dépendances circulaires
- [ ] Mixin pattern maintenu pour GUI

### Code Quality
- [ ] Pas de duplication code (DRY)
- [ ] Noms clairs et descriptifs (KISS)
- [ ] Pas d'effets secondaires cachés (WYSIWYG)
- [ ] Pas de données dupliquées (SSOT)
- [ ] Error handling approprié

### Métriques
- [ ] Aucun fichier >800 lignes (ou refactoring planifié)
- [ ] Aucune fonction >50 lignes
- [ ] Profondeur nesting ≤3 niveaux
- [ ] Nombre paramètres ≤5

### Documentation
- [ ] Docstrings complètes pour code public
- [ ] README.md à jour si feature user-facing
- [ ] CHANGELOG.md à jour
- [ ] VERSION bumped si nécessaire
- [ ] Commentaires inline pour logique complexe uniquement

### Tests (futur)
- [ ] Tests unitaires pour logique core
- [ ] Tests d'intégration pour workflows
- [ ] Tests passent tous

---

## Error Handling Standards

### Principes
- Catcher les exceptions spécifiques, pas génériques
- Fournir messages d'erreur utiles à l'utilisateur
- Logger les détails techniques pour debugging
- Fail gracefully avec fallbacks quand possible

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

### Anti-Patterns à Éviter
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
Requête Utilisateur
    │
    ├─ Décrit un bug/erreur spécifique
    │  → Utiliser /fmod-debug
    │
    ├─ Demande nouvelle fonctionnalité
    │  → Utiliser /fmod-feature
    │
    ├─ Mentionne "refactor", "améliorer code", "clean up", "restructure"
    │  → Utiliser /fmod-refactor
    │
    ├─ Demande "review", "vérifier code", "audit", "analyser"
    │  → Utiliser /fmod-review
    │
    └─ Question générale ou discussion
       → Pas de skill, répondre directement
```

### Cas Ambigus

#### "Fix this code"
- Si bug spécifique décrit → `/fmod-debug`
- Si amélioration qualité générale → `/fmod-refactor`

#### "Add feature X et clean up code Y"
- Séparer en deux tasks:
  1. `/fmod-feature` pour X
  2. `/fmod-refactor` pour Y

#### "Pourquoi ce code est structuré ainsi?"
- Utiliser `/fmod-review` pour analyser architecture
- Expliquer les design decisions

---

## Architecture Patterns du Projet

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

**Bénéfices**:
- Chaque mixin <1000 lignes
- Séparation claire des responsabilités
- Facile à tester individuellement
- Modulaire et réutilisable

**Règles**:
- Chaque mixin = une responsabilité
- Pas de dépendances entre mixins (autant que possible)
- Méthodes prefixées si privées au mixin (_method_name)

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
# Multiple stratégies de parsing avec fallback
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

## Niveau de Suggestions

### [INFO]
Suggestion informative, nice-to-have

**Exemple**: Fichier approche 750 lignes

### [SUGGEST]
Amélioration recommandée

**Exemple**: Code dupliqué 3 fois

### [RECOMMEND]
Fortement recommandé

**Exemple**: Fichier dépasse 800 lignes

### [VIOLATION]
Violation de principe, devrait être corrigé

**Exemple**: Code GUI dans module core

### [CRITICAL]
Problème sérieux, doit être corrigé immédiatement

**Exemple**: Dépendance circulaire

---

## Références Rapides

### Seuils Critiques
- 750 lignes: Planifier refactoring
- 800 lignes: Refactoring recommandé
- 900 lignes (mixin): Refactoring urgent
- 1000 lignes: Maximum absolu

### Types de Commit
- `feat`: Feature (minor bump)
- `fix`: Bug fix (patch bump)
- `refactor`: Restructure (no bump)
- `docs`: Documentation (no bump)

### Documentation à Mettre à Jour
- README.md: Features user-facing, troubleshooting
- CHANGELOG.md: Chaque version
- Docstrings: Chaque fonction/classe publique
- ARCHITECTURE.md: Changements architecturaux majeurs

### Quick SOLID Check
1. SRP: Une responsabilité par classe?
2. OCP: Extension par composition?
3. LSP: Mixins composables?
4. ISP: Pas de god classes?
5. DIP: Dépend d'abstractions?
