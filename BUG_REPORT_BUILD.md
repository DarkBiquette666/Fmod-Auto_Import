# BUG REPORT: Import Events Not Created in Build Version

**Date:** 2026-01-05
**Version:** 0.8.2
**Status:** UNRESOLVED
**Severity:** CRITICAL

---

## Executive Summary

The FMOD Importer tool works perfectly in development mode (Python script) but fails to create events in the build version (.exe created with PyInstaller). The tool reports "Import Complete! Imported: 7" but no events appear in FMOD Studio.

**Key Evidence:**
- ✅ Dev version (Python): Events created successfully
- ❌ Build version (.exe): No events created (despite success message)
- Audio files are copied but marked as "unimported" in FMOD
- No Python errors occur during import

---

## Problem Description

### Symptoms

1. **Import appears successful:**
   - Progress dialog shows "Import Complete!"
   - Message shows "Imported: 7, Failed: 0"
   - No Python errors or exceptions

2. **But nothing is actually imported:**
   - No events created in FMOD Studio project
   - Audio assets copied to Assets folder but marked as "unimported"
   - Event folder remains empty

3. **Dev vs Build difference:**
   - Same FMOD project
   - Same audio files
   - Same configuration
   - **Dev Python script:** Works perfectly
   - **Build .exe:** Fails silently

### Evidence

User provided screenshots showing:
- Analysis phase works correctly (7 matches found)
- Import completes with "Imported: 7"
- Result file path mismatch warning
- Debug messages showing files processed
- But FMOD Studio shows no events

---

## Environment

### Working Environment (Dev)
- **Launch:** `python fmod_importer.py` via `launch.bat`
- **Script location:** `D:\Git\Fmod Scripts\FmodImporter-Dev\Script\_Internal\FmodImportFromJson.js`
- **Result:** ✅ Events created successfully

### Broken Environment (Build)
- **Launch:** `FmodImporter.exe` (PyInstaller build)
- **Script location:** `C:\Users\...\AppData\Local\Temp\_MEI...\Script\_Internal\FmodImportFromJson.js`
- **Result:** ❌ No events created

### System Info
- **OS:** Windows 11
- **FMOD Studio:** Version installed at standard path
- **Python:** 3.12.10
- **PyInstaller:** 6.16.0

---

## Code Architecture

### Import Process Flow

1. **Python side** (`import_workflow.py`):
   - Creates JSON file with import data
   - Generates wrapper JavaScript file
   - Launches FMOD Studio with wrapper script: `fmodstudiocl.exe -scriptFile wrapper.js`
   - Waits for result file
   - Reports success/failure

2. **JavaScript side** (`FmodImportFromJson.js`):
   - Reads JSON import data
   - Creates events in FMOD project
   - Assigns banks, buses, asset folders
   - Adds audio files to events
   - Writes result JSON

### Current Implementation (Lines 414-431 of import_workflow.py)

```python
# Read the main import script content (Python can access _MEIPASS, FMOD Studio cannot)
with open(script_path, 'r', encoding='utf-8') as f:
    import_script_content = f.read()

# Embed the script content directly in the wrapper
# This works around PyInstaller's temp folder being inaccessible to external processes
wrapper_script_content = f"""
// Temporary wrapper script - auto-generated
// Embeds the import script content directly (PyInstaller workaround)

// Set global variables expected by the import script
var FMOD_IMPORTER_JSON_PATH = "{str(json_path).replace(chr(92), '/')}";
var resultPath = "{str(result_path).replace(chr(92), '/')}";

// === EMBEDDED IMPORT SCRIPT START ===
{import_script_content}
// === EMBEDDED IMPORT SCRIPT END ===
"""
```

**Why this approach:**
- PyInstaller's `sys._MEIPASS` temp folder is private to Python process
- External processes (FMOD Studio) cannot read files from it
- Solution: Python reads script and embeds it directly in wrapper
- Eliminates need for FMOD to access temp folder

---

## Previous Fixes Applied (All unsuccessful)

### Fix #1: Script Not Included in Build
- **Problem:** `FmodImportFromJson.js` missing from PyInstaller bundle
- **Fix:** Added to `datas` in `.spec` file
- **Result:** Script included, but events still not created

### Fix #2: Python Variable Scope Error
- **Problem:** `UnboundLocalError: cannot access local variable 'result_path'`
- **Fix:** Added `nonlocal result_path` at line 402
- **Result:** Fixed Python error, but events still not created

### Fix #3: Missing Import
- **Problem:** `name 'time' is not defined`
- **Fix:** Added `import time` at line 11
- **Result:** Fixed Python error, but events still not created

### Fix #4: PyInstaller Temp Folder Access
- **Problem:** FMOD Studio can't access `_MEIPASS` folder
- **Fix:** Embedded JavaScript content directly in wrapper
- **Result:** Should work, but events STILL not created

---

## Critical Files

### 1. `FmodImporter-Dev/fmod_importer/gui/import_workflow.py`
**Lines 400-650:** Import execution logic
- Line 402: `nonlocal result_path` declaration
- Lines 414-431: JavaScript embedding (latest fix)
- Lines 440-455: Wrapper script writing
- Lines 470-490: FMOD Studio execution
- Lines 550-600: Result file reading and parsing

### 2. `FmodImporter-Dev/Script/_Internal/FmodImportFromJson.js`
**Entire file (~300 lines):** FMOD Studio import logic
- Reads JSON data
- Creates events
- Assigns banks/buses
- Adds audio files
- Writes result

### 3. `FmodImporter-Dev/FmodImporter.spec`
**PyInstaller configuration:**
- Line 11: Script included in datas
- Line 46: `console=False` (no console window)
- Line 52: Icon configuration

---

## Debugging Evidence

### Dev Version Logs (Working)

```
[Scripting] DEBUG: Writing JSON to: C:/Users/ANTHON~1/AppData/Local/Temp/fmod_import_result_1449495698ba4834862160a540df33f6.json
DEBUG: Processing audio file: C:/Git/Supercell/rogue-assets/source/audio/Rogue/Assets/Characters/MechafloraEvent/WalkingFabricator/Mechaflora_Event_WalkingFabricator_Death_01.wav
DEBUG: Audio obtained successfully!
DEBUG: Processing audio file: C:/Git/Supercell/rogue-assets/source/audio/Rogue/Assets/Characters/MechafloraEvent/WalkingFabricator/Mechaflora_Event_WalkingFabricator_Death_02.wav
DEBUG: Audio obtained successfully!
[... continues for all 7 files ...]
```

**Result:** Events created in FMOD Studio

### Build Version Behavior (Broken)

- Same project
- Same files
- Shows "Imported: 7"
- But no events in FMOD
- No JavaScript errors visible
- Result file shows "path mismatch" warning

---

## Hypotheses

### Hypothesis #1: FMOD Studio Silently Failing (MOST LIKELY)
**Evidence:**
- No console output from FMOD Studio
- Can't see JavaScript errors
- Script may be failing silently

**How to test:**
1. Enable FMOD Studio console output
2. Capture stdout/stderr from subprocess
3. Add JavaScript logging to file

**Implementation:**
```python
# In import_workflow.py, modify FMOD Studio execution:
result = subprocess.run(
    [fmod_exe, "-scriptFile", wrapper_path],
    capture_output=True,  # Capture stdout/stderr
    text=True,
    timeout=300
)
print(f"FMOD stdout: {result.stdout}")
print(f"FMOD stderr: {result.stderr}")
```

### Hypothesis #2: Wrapper Script Not Accessible
**Evidence:**
- Wrapper written to temp folder
- May have permission issues in build

**How to test:**
1. Write wrapper to accessible location (not temp folder)
2. Try user's Documents folder or project folder

**Implementation:**
```python
# Write wrapper to project folder instead of temp
wrapper_path = Path(self.project.project_dir) / "temp_import_wrapper.js"
```

### Hypothesis #3: JSON Path Encoding Issue
**Evidence:**
- Result shows "path mismatch detected"
- Windows backslashes vs forward slashes
- May confuse JavaScript

**How to test:**
1. Verify JSON file paths are correctly formatted
2. Check if JSON is readable by FMOD
3. Add validation before FMOD execution

### Hypothesis #4: JavaScript Scope Issue
**Evidence:**
- Script expects global variables
- Embedding may affect scope

**How to test:**
1. Add console.log() statements in JavaScript
2. Log to file instead of console
3. Verify variables are accessible

**Implementation in FmodImportFromJson.js:**
```javascript
// At the very start of embedded script:
var logFile = "C:/Temp/fmod_debug.log";
function debugLog(msg) {
    var file = new File(logFile);
    file.open(File.WriteOnly | File.Append);
    file.writeLine(new Date().toISOString() + ": " + msg);
    file.close();
}

debugLog("Script started");
debugLog("JSON path: " + FMOD_IMPORTER_JSON_PATH);
debugLog("Result path: " + resultPath);
```

### Hypothesis #5: FMOD Project Locked
**Evidence:**
- Tool says to close FMOD Studio before running
- But maybe project files are still locked?

**How to test:**
1. Verify no FMOD Studio processes running
2. Check file permissions on project files
3. Try with a fresh FMOD project

---

## Recommended Next Steps

### Priority 1: Add JavaScript Logging (CRITICAL)

Modify `FmodImportFromJson.js` to write debug logs to a file:

```javascript
// Add at the very beginning of the script:
var DEBUG_LOG_PATH = "C:/Temp/fmod_importer_debug.log";

function debugLog(message) {
    try {
        var file = new File(DEBUG_LOG_PATH);
        file.open(File.WriteOnly | File.Append);
        file.writeLine("[" + new Date().toISOString() + "] " + message);
        file.close();
    } catch(e) {
        // Can't do much if logging fails
    }
}

// Log everything:
debugLog("=== SCRIPT STARTED ===");
debugLog("FMOD_IMPORTER_JSON_PATH: " + FMOD_IMPORTER_JSON_PATH);
debugLog("resultPath: " + resultPath);

// Then log before every major operation:
debugLog("Reading JSON file...");
debugLog("Creating event: " + eventName);
debugLog("Adding audio file: " + audioPath);
debugLog("ERROR: " + error.message);
```

**This will tell us:**
- Does the script even run?
- Where does it fail?
- What errors occur?

### Priority 2: Capture FMOD Studio Output

Modify `import_workflow.py` to capture console output:

```python
# Around line 470-490:
result = subprocess.run(
    [fmod_exe, "-scriptFile", str(wrapper_path)],
    capture_output=True,
    text=True,
    timeout=300,
    cwd=str(self.project.project_dir)  # Run from project folder
)

# Log the output:
if result.stdout:
    print(f"FMOD stdout:\n{result.stdout}")
if result.stderr:
    print(f"FMOD stderr:\n{result.stderr}")
```

### Priority 3: Write Wrapper to Accessible Location

Instead of temp folder, use project folder:

```python
# Around line 440:
wrapper_path = Path(self.project.project_dir) / f"temp_import_wrapper_{uuid.uuid4().hex[:8]}.js"
# Make sure to delete it after execution
```

### Priority 4: Validate JSON Before Execution

Add validation to ensure JSON is correct:

```python
# Before launching FMOD, validate the JSON:
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(f"JSON validation: {len(data.get('events', []))} events")
    for event in data['events'][:3]:  # Print first 3
        print(f"  Event: {event.get('name')}")
```

---

## Test Instructions

### To Reproduce Bug

1. **Setup:**
   ```bash
   cd "d:\Git\Fmod Scripts\FmodImporter-Dev"
   ```

2. **Build .exe:**
   ```bash
   pyinstaller FmodImporter.spec --clean --noconfirm
   ```

3. **Copy to package:**
   ```bash
   copy /Y dist\FmodImporter.exe ..\FmodImporterTool-Package\
   ```

4. **Test:**
   - Close FMOD Studio
   - Run `..\FmodImporterTool-Package\FmodImporter.exe`
   - Load project, select files, analyze, import
   - Result: "Imported: 7" but no events

5. **Verify:**
   - Open FMOD Studio
   - Check event folder → Empty
   - Check assets → Marked as "unimported"

### To Test Fix

1. Apply suggested changes
2. Rebuild .exe
3. Run import
4. Check debug log at `C:/Temp/fmod_importer_debug.log`
5. Check FMOD Studio console output
6. Verify events are created

---

## Key Differences: Dev vs Build

| Aspect | Dev (Working) | Build (Broken) |
|--------|---------------|----------------|
| **Script location** | `D:\Git\...\FmodImportFromJson.js` | `C:\Users\...\Temp\_MEI...\Script\...` |
| **Script access** | Direct file on disk | Embedded in wrapper |
| **Console** | Visible in CMD window | Hidden (console=False) |
| **Temp folder** | Project temp folder | PyInstaller _MEIPASS |
| **Debugging** | Easy (print statements) | Impossible (no console) |
| **FMOD errors** | Visible in console | Lost/invisible |

---

## Related Files to Examine

1. **import_workflow.py** - Main import execution
2. **FmodImportFromJson.js** - JavaScript import logic
3. **FmodImporter.spec** - PyInstaller configuration
4. **project.py** - FMOD project handling
5. **fmod_studio.py** - FMOD Studio executable handling

---

## Questions to Answer

1. **Is the JavaScript script even executing?**
   - Add logging to find out

2. **Are there JavaScript errors?**
   - Capture FMOD Studio output

3. **Is the JSON data correct?**
   - Validate before execution

4. **Can FMOD Studio write the result file?**
   - Check file permissions

5. **Is the wrapper script accessible to FMOD?**
   - Try different location

---

## Success Criteria

The fix is successful when:
1. ✅ Build .exe shows "Import Complete! Imported: 7"
2. ✅ FMOD Studio has 7 new events created
3. ✅ Audio files are assigned to events (not marked "unimported")
4. ✅ Banks, buses, and folders are correctly assigned
5. ✅ No errors or warnings during import

---

## Contact & Collaboration

This report is intended for another AI to continue debugging. The original developer has exhausted their debugging attempts and needs fresh perspective.

**Repository:** https://github.com/DarkBiquette666/Fmod-Auto_Import
**Branch:** master
**Latest commit:** `9e8671b` - "fix(build): Embed JavaScript content to fix PyInstaller temp folder access issue"

**Key insight for next developer:** The problem is NOT on the Python side (no errors occur). The problem is on the JavaScript/FMOD Studio side (script fails silently). Need to add logging to JavaScript to see what's happening.

---

**Last Updated:** 2026-01-05
**Status:** Ready for handoff to another AI
