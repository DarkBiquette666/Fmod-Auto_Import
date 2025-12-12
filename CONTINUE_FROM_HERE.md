# Continue From Here - FMOD Importer Debug Session

## Date: 2025-12-12

## Current Problem

The template matching during **Analyze** phase is broken. Events that should match templates are showing as "from scratch" (no template match found).

### Symptoms:
1. When clicking "Analyze", events show `+ EventName` (from scratch) instead of showing template matches
2. When clicking "Import", error "No events ready for import" or "No events matched templates"
3. Even simple events like "Alert" don't match

### Root Cause (suspected):
I modified the template matching logic in `import_assets()` function and broke it. The original matching logic in `analyze_folder()` was working but I may have introduced regressions.

## What Was Changed Today

### Files Modified:
1. `FmodImporter-Dev/fmod_importer.py` - Template matching logic in `import_assets()` function (lines ~4050-4160)
2. `FmodImporter-Dev/Script/_Internal/FmodImportFromJson.js` - Template duplication using UI action, bus routing fix

### Key Changes Made:
1. Changed template suffix extraction from `split("_", 2)` to `split("_")`
2. Added "fuzzy matching" with `normalize_action()` function
3. Changed how event suffix is extracted using `event_prefix`

## How to Fix

**DO NOT REVERT** - The JavaScript fixes (template duplication, bus routing, bank assignment) are working and must be preserved.

### The Problem
The template matching logic in `import_assets()` was broken by changes to suffix extraction. The original working code used a simpler approach.

### Original Working Logic (from commit ed044bd)
```python
# Simple and working:
template_map = {}
for tmpl in template_events:
    parts = tmpl["name"].split("_", 2)
    if len(parts) >= 3:
        expected_name = f"{prefix}_{character}_{parts[2]}"
        template_map[expected_name] = tmpl
```

### Current Broken Logic
The new code with `normalize_action()` and complex suffix extraction broke the matching.

### Fix Strategy
1. **Keep all JavaScript fixes** in `FmodImportFromJson.js` - they work correctly
2. **Fix Python matching** in `import_assets()` (~line 4050-4160):
   - Restore simpler suffix extraction using `split("_", 2)`
   - Use the `character` variable that was already available
   - Add fuzzy matching as an ENHANCEMENT, not a replacement

### Key Variables to Use
- `prefix` - The selected prefix (e.g., "Mechaflora")
- `character` - The normalized feature name (e.g., "Strong_Repair")
- Template names follow: `_Template_{CharacterName}_{Action}`
- Event names follow: `{Prefix}_{Character}_{Action}`

### Two Matching Steps (Both Must Work)
1. **Analyze phase** (`analyze_folder()`): Matches audio files to template events, populates preview tree
2. **Import phase** (`import_assets()`): Reads preview tree, matches to templates for JSON generation

The analyze phase was likely still working. Focus on fixing `import_assets()` first.

## Working Features (confirmed)
- Template duplication via `studio.window.triggerAction(studio.window.actions.Duplicate)`
- Bus routing via `event.mixerInput.output = bus` (not masterTrack.mixerGroup.output)
- Bank assignment via `event.relationships.banks.add(bank)`
- Audio import via `studio.project.importAudioFile()`

## Files to Check

### For Analyze matching:
- `fmod_importer.py` - Look for `analyze_folder()` method
- Check how `AudioMatcher` class works
- Look for where preview tree is populated

### For Import matching:
- `fmod_importer.py` - `import_assets()` method around line 4050+
- The `template_by_base` and `event_by_base` dictionaries
- The `normalize_action()` function

## Debug Output Added
When "No events matched templates" error shows, it displays:
- Template bases (normalized action names from templates)
- Event bases (normalized action names from preview)
- Template names found
- Event names from preview

This helps identify why matching fails.

## Git Status
All changes are uncommitted. To see what changed:
```bash
git diff FmodImporter-Dev/fmod_importer.py
```
