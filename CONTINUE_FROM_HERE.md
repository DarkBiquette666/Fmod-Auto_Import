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

### Option 1: Revert to working commit
```bash
git checkout ed044bd -- FmodImporter-Dev/fmod_importer.py
```
This reverts to "Improve fuzzy matching and fix orphan lists layout" commit which was working.

### Option 2: Debug the current code
Look at commit `ed044bd` to see how the original matching worked:
```bash
git show ed044bd:FmodImporter-Dev/fmod_importer.py | grep -A 50 "def analyze_folder"
```

The key is to understand:
1. How `analyze_folder()` matches templates to audio files (this populates the preview tree)
2. How `import_assets()` reads from preview tree and matches to templates

### Important: Two Different Matching Steps
1. **Analyze phase** (`analyze_folder()`): Matches audio files to template events, populates preview tree
2. **Import phase** (`import_assets()`): Reads preview tree, matches to templates for JSON generation

Both need to work correctly.

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
