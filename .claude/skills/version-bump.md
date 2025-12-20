# Version Bump Skill

**Trigger**: Automatiquement après validation de `feat` ou `fix` commits, ou manuellement via `/version-bump`

**Purpose**: Automatiser le processus de version bump selon Semantic Versioning en analysant les commits et en mettant à jour tous les fichiers nécessaires.

---

## Workflow

### Phase 1: Analyse des Commits

1. **Vérifier l'état Git**
   ```bash
   git status
   ```
   - S'assurer qu'il n'y a pas de modifications non commitées
   - Si des modifications existent, avertir l'utilisateur

2. **Récupérer la version actuelle**
   - Lire `FmodImporter-Dev/fmod_importer/__init__.py`
   - Parser la ligne `VERSION = "X.Y.Z"`
   - Stocker: `current_version`

3. **Analyser les commits depuis la dernière version**
   ```bash
   git log v{current_version}..HEAD --oneline
   ```
   - Si la version actuelle n'a pas de tag, utiliser le dernier tag disponible
   - Parser chaque commit pour détecter le type:
     - `feat` → MINOR bump requis
     - `fix` → PATCH bump requis
     - `BREAKING CHANGE` → MAJOR bump requis

4. **Déterminer le type de bump**
   - Priorité: MAJOR > MINOR > PATCH
   - Si aucun commit feat/fix/breaking, demander confirmation à l'utilisateur
   - Calculer `new_version` basé sur les règles Semantic Versioning

### Phase 2: Validation avec l'Utilisateur

5. **Présenter le plan de version bump**
   ```
   📊 Version Bump Analysis

   Current version: {current_version}
   Proposed version: {new_version}
   Bump type: {MAJOR|MINOR|PATCH}

   Commits since last version:
   - feat(gui): Add bank filter widget
   - fix(import): Resolve path escaping issue

   This will update:
   ✓ fmod_importer/__init__.py (VERSION)
   ✓ CHANGELOG.md (new release section)
   ✓ Git tag (v{new_version})

   Proceed with version bump? [Y/n]
   ```

6. **Attendre confirmation utilisateur**
   - Si refus, arrêter le processus
   - Si acceptation, continuer

### Phase 3: Mise à Jour des Fichiers

7. **Mettre à jour VERSION dans le code**
   - Fichier: `FmodImporter-Dev/fmod_importer/__init__.py`
   - Remplacer: `VERSION = "{current_version}"` → `VERSION = "{new_version}"`
   - Utiliser Edit tool pour préserver la formatting exacte

8. **Mettre à jour CHANGELOG.md**
   - Lire le fichier actuel
   - Identifier la section `## [Unreleased]`
   - Opérations:
     a. Renommer `[Unreleased]` → `[{new_version}] - {YYYY-MM-DD}`
     b. Ajouter une nouvelle section `[Unreleased]` vide en haut

   **Template de nouvelle section**:
   ```markdown
   ## [Unreleased]

   ### Added

   ### Changed

   ### Fixed

   ## [{new_version}] - {date}

   {contenu existant de [Unreleased]}
   ```

9. **Vérifier que CHANGELOG contient les commits**
   - S'assurer que les commits feat/fix sont documentés sous [new_version]
   - Si manquants, avertir l'utilisateur
   - Rappel: Les commits doivent déjà être dans CHANGELOG selon le protocole

### Phase 4: Git Operations

10. **Stager les modifications**
    ```bash
    git add FmodImporter-Dev/fmod_importer/__init__.py CHANGELOG.md
    ```

11. **Créer le commit de version bump**
    ```bash
    git commit -m "$(cat <<'EOF'
    chore(release): Bump version to {new_version}

    This release includes:
    - {count_feat} new features
    - {count_fix} bug fixes

    See CHANGELOG.md for full details.

    🤖 Generated with [Claude Code](https://claude.com/claude-code)

    Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
    EOF
    )"
    ```

12. **Créer le tag Git**
    ```bash
    git tag -a v{new_version} -m "Release version {new_version}"
    ```

13. **Afficher le résumé**
    ```
    ✅ Version bump completed successfully!

    Version: {current_version} → {new_version}
    Commit: {commit_hash}
    Tag: v{new_version}

    Next steps:
    - Review the changes with: git show HEAD
    - Push to remote with: git push && git push --tags
    ```

---

## Automatic Triggering

Ce skill est **automatiquement déclenché** dans les cas suivants:

### Trigger 1: Après un commit feat/fix validé
- Détecté par le protocole après création d'un commit
- Si le dernier commit est de type `feat` ou `fix`
- ET qu'il n'y a pas déjà eu un bump pour ce commit
- ALORS: Proposer automatiquement un version bump

### Trigger 2: Avant un push vers remote
- Hook Git pre-push pourrait vérifier
- Si des commits feat/fix non-versionnés existent
- Proposer un bump avant le push

### Trigger 3: Manuel via commande
```
/version-bump
```

---

## Error Handling

### Erreur: Working directory not clean
```
❌ Cannot perform version bump with uncommitted changes.
Please commit or stash your changes first.
```

### Erreur: No commits since last version
```
⚠️  No new commits found since v{current_version}.
Nothing to bump. Create feat/fix commits first.
```

### Erreur: CHANGELOG not updated
```
⚠️  Warning: CHANGELOG.md may not reflect recent commits.
Found commits that are not documented:
- feat(gui): Add bank filter

Please update CHANGELOG.md before version bump.
Continue anyway? [y/N]
```

### Erreur: Tag already exists
```
❌ Tag v{new_version} already exists.
Please use a different version or delete the existing tag.
```

---

## Configuration

### Semantic Versioning Rules

**MAJOR (X.0.0)** - Breaking Changes
- Commit body/footer contient `BREAKING CHANGE:`
- API incompatible changes
- Architectural rewrites

**MINOR (0.X.0)** - New Features (Backward Compatible)
- Commits de type `feat`
- New user-facing functionality
- Significant refactoring (non-breaking)

**PATCH (0.0.X)** - Bug Fixes
- Commits de type `fix`
- Performance improvements
- Documentation fixes (optionnel)

### Version Format
- Format: `MAJOR.MINOR.PATCH`
- Exemples: `0.1.8`, `1.0.0`, `2.3.1`
- Préfixe tag Git: `v` (ex: `v0.1.9`)

---

## Examples

### Example 1: Patch Bump (Fix)

```
Current commits since v0.1.8:
- fix(import): Resolve path escaping on Windows

Analysis:
✓ 1 fix commit → PATCH bump
✓ No feat commits
✓ No breaking changes

Proposed: 0.1.8 → 0.1.9
```

### Example 2: Minor Bump (Feature)

```
Current commits since v0.1.8:
- feat(gui): Add bank filter widget
- fix(ui): Correct button alignment

Analysis:
✓ 1 feat commit → MINOR bump required
✓ 1 fix commit (included)
✓ No breaking changes

Proposed: 0.1.8 → 0.2.0
```

### Example 3: Major Bump (Breaking)

```
Current commits since v0.2.0:
- feat(api): Redesign matching API

  BREAKING CHANGE: Matcher.match() now returns dict instead of list

Analysis:
✓ BREAKING CHANGE detected → MAJOR bump required
✓ 1 feat commit
✓ Breaking: API signature changed

Proposed: 0.2.0 → 1.0.0
```

---

## Integration avec Protocole

### Dans _protocol-rules.md

Ajouter la règle suivante dans la section "After Commit":

```markdown
## Post-Commit Version Check

Après chaque commit de type `feat` ou `fix`:

1. **Vérifier si version bump nécessaire**
   - Analyser les commits non-versionnés depuis dernier tag
   - Si au moins 1 commit feat/fix existe

2. **Proposer automatiquement le version bump**
   ```
   📦 New feature/fix detected!

   Would you like to bump the version now?

   Current: v0.1.8
   Proposed: v0.2.0 (MINOR - new feature)

   Run version bump now? [Y/n]
   ```

3. **Si accepté**: Exécuter `/version-bump` skill
4. **Si refusé**: Ajouter note dans TODO pour bump ultérieur
```

### Workflow Integration

```
User request
    ↓
Implementation (feat/fix)
    ↓
Tests validation
    ↓
Commit (Conventional Commits)
    ↓
✨ AUTO-TRIGGER: Version bump check
    ↓
    ├─→ [No feat/fix] → Done
    └─→ [feat/fix detected] → Propose version bump
            ↓
            ├─→ [User accepts] → Execute /version-bump
            └─→ [User declines] → Add to TODO
```

---

## Files Modified

| File | Modification | Format |
|------|-------------|--------|
| `fmod_importer/__init__.py` | Update VERSION variable | `VERSION = "X.Y.Z"` |
| `CHANGELOG.md` | Add release section | `## [X.Y.Z] - YYYY-MM-DD` |
| `.git/refs/tags/` | Create version tag | `vX.Y.Z` |

---

## Success Criteria

✅ Version correctly bumped in `__init__.py`
✅ CHANGELOG.md updated with new release section
✅ Git tag created with correct version
✅ Commit message follows Conventional Commits
✅ All changes included in single atomic commit
✅ User informed of next steps (push to remote)

---

## Notes

- **SSOT**: `fmod_importer/__init__.py` est la single source of truth pour VERSION
- **Idempotence**: Réexécuter le skill avec même version ne doit pas causer d'erreurs
- **Atomic**: Toutes les modifications doivent être dans un seul commit
- **Reversible**: Utilisateur peut toujours faire `git reset HEAD~1` pour annuler
- **Tag safety**: Ne jamais forcer un tag existant, demander confirmation
