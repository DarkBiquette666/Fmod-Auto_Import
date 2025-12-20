# Version Bump Skill

**Trigger**: Automatically after validated `feat` or `fix` commits, or manually via `/version-bump`

**Purpose**: Automate version bump process according to Semantic Versioning by analyzing commits and updating all necessary files.

---

## Workflow

### Phase 1: Commit Analysis

1. **Check Git status**
   ```bash
   git status
   ```
   - Ensure no uncommitted modifications exist
   - If modifications exist, warn the user

2. **Retrieve current version**
   - Read `FmodImporter-Dev/fmod_importer/__init__.py`
   - Parse the line `VERSION = "X.Y.Z"`
   - Store: `current_version`

3. **Analyze commits since last version**
   ```bash
   git log v{current_version}..HEAD --oneline
   ```
   - If current version has no tag, use last available tag
   - Parse each commit to detect type:
     - `feat` → MINOR bump required
     - `fix` → PATCH bump required
     - `BREAKING CHANGE` → MAJOR bump required

4. **Determine bump type**
   - Priority: MAJOR > MINOR > PATCH
   - If no feat/fix/breaking commits, ask user for confirmation
   - Calculate `new_version` based on Semantic Versioning rules

### Phase 2: User Validation

5. **Present version bump plan**
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

6. **Wait for user confirmation**
   - If declined, stop the process
   - If accepted, continue

### Phase 3: File Updates

7. **Update VERSION in code**
   - File: `FmodImporter-Dev/fmod_importer/__init__.py`
   - Replace: `VERSION = "{current_version}"` → `VERSION = "{new_version}"`
   - Use Edit tool to preserve exact formatting

8. **Update CHANGELOG.md**
   - Read current file
   - Identify `## [Unreleased]` section
   - Operations:
     a. Rename `[Unreleased]` → `[{new_version}] - {YYYY-MM-DD}`
     b. Add new empty `[Unreleased]` section at top

   **New section template**:
   ```markdown
   ## [Unreleased]

   ### Added

   ### Changed

   ### Fixed

   ## [{new_version}] - {date}

   {existing content from [Unreleased]}
   ```

9. **Verify CHANGELOG contains commits**
   - Ensure feat/fix commits are documented under [new_version]
   - If missing, warn the user
   - Reminder: Commits should already be in CHANGELOG per protocol

### Phase 4: Git Operations

10. **Stage modifications**
    ```bash
    git add FmodImporter-Dev/fmod_importer/__init__.py CHANGELOG.md
    ```

11. **Create version bump commit**
    ```bash
    git commit -m "$(cat <<'EOF'
    chore(release): Bump version to {new_version}

    This release includes:
    - {count_feat} new features
    - {count_fix} bug fixes

    See CHANGELOG.md for full details.
    EOF
    )"
    ```

12. **Create Git tag**
    ```bash
    git tag -a v{new_version} -m "Release version {new_version}"
    ```

13. **Display summary**
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

This skill is **automatically triggered** in the following cases:

### Trigger 1: After validated feat/fix commit
- Detected by protocol after commit creation
- If last commit is type `feat` or `fix`
- AND there hasn't already been a bump for this commit
- THEN: Automatically propose version bump

### Trigger 2: Before push to remote
- Git pre-push hook could verify
- If unversioned feat/fix commits exist
- Propose bump before push

### Trigger 3: Manual via command
```
/version-bump
```

---

## Error Handling

### Error: Working directory not clean
```
❌ Cannot perform version bump with uncommitted changes.
Please commit or stash your changes first.
```

### Error: No commits since last version
```
⚠️  No new commits found since v{current_version}.
Nothing to bump. Create feat/fix commits first.
```

### Error: CHANGELOG not updated
```
⚠️  Warning: CHANGELOG.md may not reflect recent commits.
Found commits that are not documented:
- feat(gui): Add bank filter

Please update CHANGELOG.md before version bump.
Continue anyway? [y/N]
```

### Error: Tag already exists
```
❌ Tag v{new_version} already exists.
Please use a different version or delete the existing tag.
```

---

## Configuration

### Semantic Versioning Rules

**MAJOR (X.0.0)** - Breaking Changes
- Commit body/footer contains `BREAKING CHANGE:`
- API incompatible changes
- Architectural rewrites

**MINOR (0.X.0)** - New Features (Backward Compatible)
- Commits of type `feat`
- New user-facing functionality
- Significant refactoring (non-breaking)

**PATCH (0.0.X)** - Bug Fixes
- Commits of type `fix`
- Performance improvements
- Documentation fixes (optional)

### Version Format
- Format: `MAJOR.MINOR.PATCH`
- Examples: `0.1.8`, `1.0.0`, `2.3.1`
- Git tag prefix: `v` (e.g., `v0.1.9`)

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

## Integration with Protocol

### In _protocol-rules.md

Add the following rule in the "After Commit" section:

```markdown
## Post-Commit Version Check

After each `feat` or `fix` type commit:

1. **Check if version bump necessary**
   - Analyze unversioned commits since last tag
   - If at least 1 feat/fix commit exists

2. **Automatically propose version bump**
   ```
   📦 New feature/fix detected!

   Would you like to bump the version now?

   Current: v0.1.8
   Proposed: v0.2.0 (MINOR - new feature)

   Run version bump now? [Y/n]
   ```

3. **If accepted**: Execute `/version-bump` skill
4. **If declined**: Add note in TODO for later bump
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

- **SSOT**: `fmod_importer/__init__.py` is the single source of truth for VERSION
- **Idempotence**: Re-running skill with same version should not cause errors
- **Atomic**: All modifications must be in a single commit
- **Reversible**: User can always `git reset HEAD~1` to undo
- **Tag safety**: Never force an existing tag, ask for confirmation
