# FMOD Importer - Development Protocol

This project follows strict architecture and code quality principles. **Apply these rules automatically** for all code modifications.

## Architecture Principles (ALWAYS Enforce)

- **SOLID**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **DRY**: Extract repeated code at 3rd occurrence → create reusable component
- **KISS**: Prefer simple solutions over complex ones
- **SSOT**: Single Source of Truth (one VERSION location, centralized config)
- **Modularity**: 800-line threshold per file

## Automatic Checks (PROACTIVE - After ANY Code Modification)

After modifying code, **immediately check**:

1. **Line Count**: Use `wc -l` or count during Read
   - **[CRITICAL]**: >1000 lines → MUST refactor immediately
   - **[RECOMMEND]**: >900 lines → Strong suggestion to refactor
   - **[SUGGEST]**: >800 lines → Propose extraction
   - **[INFO]**: >750 lines → Alert approaching threshold

2. **Code Duplication**: Search for repeated patterns
   - 3+ occurrences → Extract to shared function/module
   - Flag location and suggest consolidation

3. **SOLID Violations**: Check Single Responsibility
   - Mixed concerns in one class/file → Suggest extraction
   - Example: project.py has XML parsing + cache + core logic

4. **Documentation**: Update automatically
   - Docstrings for new/modified functions
   - README.md for new features
   - CHANGELOG.md for all changes
   - docs/ARCHITECTURE.md for architectural changes

## Skills Decision Tree (Use Automatically)

When user requests work, **read and apply the appropriate skill**:

- **Bug fix / Error / Debug** → Read `.claude/skills/fmod-debug.md`
- **New feature / Add functionality** → Read `.claude/skills/fmod-feature.md`
- **Refactor / Code quality** → Read `.claude/skills/fmod-refactor.md`
- **Code review / Quality check** → Read `.claude/skills/fmod-review.md`

Global rules are in `.claude/skills/_protocol-rules.md`.

## Commit Strategy

- **Format**: `type(scope): subject` (conventional commits)
- **Types**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
- **Strategy**: Group by milestone (M1: core, M2: GUI, M3: docs)
- **Version**: Bump version for feat/fix (semantic versioning)

## Critical Files to Monitor

Current file sizes (updated 2024-12-20):
- ⚠️ **project.py**: 1075 lines - **CRITICAL** (cache disabled, consider removal)
- ⚠️ **widgets.py**: 724 lines - 90% of threshold
- ⚠️ **naming.py**: 710 lines - 89% of threshold

## Proactive Suggestions Format

Use severity levels in suggestions:

```
[SEVERITY] Issue Type: Description

Current state:
- Metric or measurement

Suggested improvement:
- Specific recommendation

Benefit:
- Impact on code quality

Effort: Low/Medium/High
Skill to use: /fmod-[skill-name]
```

## Important Notes

- **Zero external dependencies** - stdlib only
- **Mixin architecture** - 8 GUI mixins, keep separation clean
- **Lazy loading** - Properties loaded on first access
- **Test before commit** - Ensure tool still works after changes
- **English-only** - All code, comments, and commits in English

---

**Remember**: Be proactive. Check thresholds and suggest improvements without waiting to be asked.
