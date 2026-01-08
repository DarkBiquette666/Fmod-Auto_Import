# FMOD Importer Tool - Automatic Audio Asset Importer for FMOD Studio

**Version:** 0.10.0
**Description:** Standalone Windows/macOS application for intelligently importing audio assets into FMOD Studio projects

---

## CRITICAL WARNING

**ALWAYS CLOSE FMOD STUDIO BEFORE USING THIS TOOL!**

This tool directly manipulates XML files in your FMOD project. Having FMOD Studio open while running this tool can cause:
- Data corruption
- Loss of changes
- Conflicts between the tool and FMOD Studio
- Unpredictable behavior

**Recommended workflow:**
1. **CLOSE** FMOD Studio completely
2. Run FMOD Importer Tool
3. Complete your import
4. **THEN** open FMOD Studio
5. Save your project (Ctrl+S)

---

## Description

FMOD Importer Tool is a GUI tool that facilitates intelligent audio file importation into FMOD Studio projects. It allows you to:

- Automatically create FMOD events from audio files
- Detect and import from existing template folders
- Intelligently match audio files with events
- Automatically organize events in specific folders
- Auto-assign banks, buses, and asset folders
- Intuitive interface with visual feedback

---

## Requirements

### Required Software

**FMOD Studio**
- Version 2.0 or higher recommended
- Works with FMOD Studio projects (.fspro)

---

## Usage

### Launching the Application

**Simply double-click on `FmodImporter.exe`**

**Note:** The first launch may take a few seconds as the executable extracts its dependencies to a temporary folder.

---

## User Guide

### 1. Initial Setup

**IMPORTANT: Close FMOD Studio before proceeding!**

1. **Load an FMOD Project**
   - **Ensure FMOD Studio is closed**
   - Click "Browse..." next to "FMOD Project"
   - Select your `.fspro` file
   - Click "Load" to load the project

2. **Select Media Folder**
   - Click "Browse..." next to "Media Files Directory"
   - Select the folder containing your audio files (.wav, .mp3, etc.)

**Note:** If FMOD Studio is not installed in standard paths (`C:\Program Files\FMOD SoundSystem`), you may need to configure the FMOD executable path in Settings (click "Settings" button at bottom).

**💡 Tip - Save Time with Default Settings:**
Once you've configured your project path and FMOD executable path, you can save them as defaults:
1. Click the **"Settings"** button at the bottom of the window
2. Your current paths will be pre-filled in the settings dialog
3. Click **"Save"** to make them the default values
4. Next time you launch the tool, these paths will be automatically loaded - no need to browse again!

This is especially useful if you:
- Always work on the same FMOD project
- Have FMOD Studio installed in a non-standard location
- Want to skip repetitive setup steps

### 2. Configuration

**Required fields:**

- **Event Folder (Destination)**: FMOD folder where events will be created
- **Bank**: FMOD bank to assign to events
- **Bus**: Mixing bus for events
- **Asset Folder**: Audio asset folder
- **Prefix**: Prefix to add to event names (e.g., "Mechaflora")
- **FeatureName**: Feature or character name (e.g., "Weak_Ranged")

**Optional fields:**

- **Template Folder**: Existing template folder to copy from (only in Match Template mode)

### 3. Import Modes

FMOD Importer offers two import modes, selectable via radio buttons in the Pattern Setup section:

#### **Match Template Mode** (Default)

Use this mode when you have existing FMOD events to use as templates.

**How it works:**
1. You select a **Template Folder** containing existing events
2. The tool matches your audio files to template events using fuzzy matching
3. New events are created based on the template structure

**Pattern order:**
- **Event Pattern** (first): Defines how FMOD events are named
- **Asset Pattern** (second, optional): Override for parsing audio file names differently

**Separator fields:** Visible and usable for fine-tuning pattern matching.

#### **Generate from Pattern Mode** (New in v0.10.0)

Use this mode when you want to create events purely based on file naming patterns, without templates.

**How it works:**
1. Template Folder is hidden (not needed)
2. You define how your audio files are named (Asset Name Pattern)
3. The tool parses file names and creates events accordingly

**Pattern order (INVERTED):**
- **Asset Name Pattern** (first): Defines how your audio files are named (SOURCE)
- **Event Name Pattern** (second, optional): Defines how events should be named (DESTINATION)

**Smart inheritance:** If Event Name Pattern is empty, it inherits from Asset Name Pattern.

**Separator fields:** Hidden (not needed in this mode).

#### **Which mode should I use?**

| Scenario | Recommended Mode |
|----------|-----------------|
| You have template events to copy | Match Template |
| You want fuzzy matching with existing events | Match Template |
| You need separator fields for pattern matching | Match Template |
| You're creating events from scratch | Generate from Pattern |
| Your files are named consistently and you want direct mapping | Generate from Pattern |
| You don't have any template events | Generate from Pattern |

### 4. Recommended Workflow

#### **Option A: Match Template Mode**

1. Select **"Match Template"** mode (default)
2. Select an existing **Template Folder**
3. Configure Event Pattern and optionally Asset Pattern
4. Click **"Analyze"**
5. Tool automatically matches files to template events
6. Verify matches in the list
7. Click **"Import"**

#### **Option B: Generate from Pattern Mode**

1. Select **"Generate from Pattern"** mode
2. Template Folder section will be hidden
3. Configure **Asset Name Pattern** (how your files are named)
4. Optionally configure **Event Name Pattern** (or leave empty to inherit)
5. Click **"Analyze"**
6. Tool creates events based on parsed file names
7. Check the event list
8. Click **"Import"**

### 5. Icon Interpretation

In the import event list:

- **[OK]**: Perfect match found
- **~**: Approximate match (medium confidence)
- **?**: No match found
- **+**: Auto-created event (no template)

### 6. Match Management

**Orphan Media Files** (files without event):
- Right-click to manually assign to an event

**Orphan Events** (events without media):
- Right-click to manually assign an audio file

### 7. Import Progress

When you click **"Import"**:
- A progress dialog will appear showing the import status
- The dialog displays an animated progress bar
- Status messages update as the import progresses:
  - "Preparing to import..." - Initial validation
  - "Copying audio files..." - Files being copied to FMOD Assets folder
  - "Executing FMOD Studio import..." - FMOD Studio processing events
- The main window remains responsive during import (no freeze)
- Import typically takes 1-5 minutes depending on project size
- The progress dialog automatically closes when import completes

**Note:** You can still interact with the main window during import, but avoid starting another import until the current one completes.

### 8. Finalization

1. Verify all matches
2. Click **"Import"**
3. Monitor the progress dialog
4. Wait for the "Import Complete" message
5. **Important:** Now you can open FMOD Studio and save the project (Ctrl+S)
6. **Remember:** The tool directly modifies XML files, so never have FMOD Studio open while importing

---

## Advanced Settings

Access via the **"Settings"** button at the bottom of the interface.

### Default Values - Avoid Repetitive Setup

**Save time by configuring default values that will be automatically loaded each time you launch the tool.**

#### How It Works:
1. Configure your paths and settings in the main interface
2. Click **"Settings"** button (bottom of window)
3. The settings dialog opens with your current values pre-filled
4. Click **"Save"** to store these as defaults
5. **Next launch:** All saved values are automatically loaded!

#### What You Can Save:
- **Default FMOD Project** - Your main `.fspro` file path
- **FMOD Studio Executable** - Path to `fmodstudiocl.exe` or `FMOD Studio.exe`
- **Default Media Directory** - Your audio files folder
- **Default Template Folder** - Commonly used template folder
- **Default Bank** - Your preferred bank
- **Default Destination Folder** - Where you usually create events
- **Default Bus** - Your standard mixing bus
- **Default Event Separator** - Event naming pattern separator (e.g., "_")
- **Default Asset Separator** - Asset naming pattern separator (e.g., "_")

**💡 Pro Tip:** If you always work on the same project, save the project path and FMOD executable once - you'll never need to browse for them again!

---

## Common Use Cases

### Case 1: Create variations of an existing character (Match Template)

**Scenario:** You have a "WeakTemplate" template and want to create "MechafloraWeakRanged"

1. **Import Mode:** Match Template (default)
2. **Prefix:** `Sfx`
3. **FeatureName:** `BlueEyesWhiteDragon`
4. **Template Folder:** Select "WeakTemplate" folder
5. **Destination Folder:** Select/create "BlueEyesWhiteDragon"
6. **Media Files:** Point to new audio files
7. **Analyze** then **Import**

### Case 2: Quick import from file names (Generate from Pattern)

**Scenario:** You have consistently named files like `Sfx_Dragon_Attack.wav`, `Sfx_Dragon_Idle.wav`

1. **Import Mode:** Generate from Pattern
2. **Asset Name Pattern:** `$prefix_$feature_$action`
3. **Event Name Pattern:** Leave empty (will use same pattern)
4. **Destination Folder:** Choose where to create events
5. **Bank, Bus:** Select appropriate values
6. **Media Files:** Point to your files
7. **Analyze** then **Import**

### Case 3: Transform file naming to different event naming (Generate from Pattern)

**Scenario:** Your files are named `sfx_dragon_attack.wav` but you want events named `SfxDragonAttack`

1. **Import Mode:** Generate from Pattern
2. **Asset Name Pattern:** `$prefix_$feature_$action` (with underscore separator in files)
3. **Event Name Pattern:** `$prefix$feature$action` (CamelCase for events)
4. **Destination Folder:** Choose target folder
5. **Analyze** then **Import**

### Case 4: Reorganize existing events (Match Template)

**Scenario:** You want to copy events to a new folder with new media

1. **Import Mode:** Match Template
2. **Template Folder:** Source folder
3. **Destination Folder:** New target folder
4. **Media Files:** New audio files
5. **Analyze** to see matches
6. Adjust manually if needed
7. **Import**

---

## Troubleshooting

### "Could not find FMOD Studio executable"

**Cause:** FMOD Studio not found in standard installation paths
**Solution:**
1. Click "Settings" button at bottom of window
2. Click "Browse..." next to "FMOD Studio Executable"
3. Select `fmodstudiocl.exe` or `FMOD Studio.exe` from your FMOD installation
4. Click "Save"

### "Please specify prefix and feature name"

**Cause:** Prefix or FeatureName fields are empty or contain placeholder text
**Solution:** Fill in both required fields with actual values (not "e.g. Sfx" or "e.g. BlueEyesWhiteDragon")

### "Please select an audio asset folder"

**Cause:** No asset folder selected
**Solution:** Click "Select..." next to "Asset Folder" and choose a folder

### "Please select a destination folder"

**Cause:** Destination folder not selected
**Solution:** Click "Select..." next to "Event Folder" and choose a folder

### "Please select a bank"

**Cause:** No bank selected
**Solution:** Click "Select..." next to "Bank" and choose a bank

### Import does nothing / no changes in FMOD

**Cause:** Changes not saved yet, or FMOD Studio was open during import
**Solution:**
1. **Ensure FMOD Studio was closed during import**
2. If FMOD was open during import, changes may be lost - run import again with FMOD closed
3. Open FMOD Studio
4. **File > Save Project** (Ctrl+S)
5. Changes will appear

### Import progress dialog appears stuck

**Cause:** Import is processing a large project or FMOD Studio is taking longer than expected
**Solution:**
1. **Wait patiently** - Imports can take 1-5 minutes depending on project size
2. Check if FMOD Studio process is running in Task Manager (it should be)
3. If stuck for more than 5 minutes, the import will timeout automatically
4. If timeout occurs, check:
   - FMOD Studio installation is working correctly
   - Project files are not corrupted
   - Sufficient disk space and permissions
5. Try importing again with a smaller batch of events

**Note:** The progress dialog cannot be closed manually - you must wait for the import to complete or timeout. This prevents interrupting the FMOD Studio process mid-import, which could corrupt the project.

### "FMOD version mismatch detected"

**Cause:** Project FMOD version doesn't match installed FMOD Studio executable version

**Solution:**
1. Check the version display in the main interface (shows Project version vs Executable version)
2. Either:
   - Update your FMOD Studio installation to match the project version
   - Upgrade/downgrade the FMOD project to match your executable version
3. The tool will prevent import until versions match to avoid compatibility issues
4. Version detection is automatic when you load a project

### "Failed to load project"

**Possible causes:**
- FMOD Studio is currently open with the project (close it!)
- .fspro file is corrupted
- Metadata folder doesn't exist
- Insufficient permissions
- XML files are locked by FMOD Studio

**Solution:**
1. **Close FMOD Studio completely**
2. Verify the project opens correctly in FMOD Studio
3. Close FMOD Studio again before using the tool

### Audio files not detected

**Check:**
- Files have extension .wav, .mp3, .ogg, .flac, etc.
- Folder path is correct
- You have read permissions

---

## Package Structure

```
FmodImporterTool-Package/
├── FmodImporter.exe       # Standalone Windows executable
├── README.md              # Main documentation (this file)
└── docs/                  # Documentation folder
    ├── QUICKSTART.md      # Quick start guide
    ├── INDEX.md           # Package overview
    ├── LICENSE.txt        # MIT License and disclaimer
    ├── VERSION.txt        # Version information
    └── requirements.txt   # Python dependencies list
```

---

## Tips and Best Practices

### Do

- **Always backup** your FMOD project before using the tool
- **Verify matches** before importing
- **Use consistent file names** for better automatic matching
- **Test with a small set** of files first

### Avoid

- **NEVER** import into an open FMOD project (always close FMOD Studio first!)
- **NEVER** have FMOD Studio open while using this tool (XML file conflicts!)
- **Don't** interrupt import in progress
- **Don't** modify FMOD project files manually while tool is running
- **Don't** use special characters in file names

## Updates

To update the tool:
1. Backup your settings if important
2. Download the new version of `FmodImporter.exe`
3. Replace the old executable with the new one

---

## Support

In case of problems:
1. Check the "Troubleshooting" section above
2. Verify FMOD Studio is correctly installed
3. Test with a simple FMOD project
4. See [docs/QUICKSTART.md](docs/QUICKSTART.md) for quick reference

---

## License

This tool is provided "as is" without warranty. Use at your own risk.

**Important:** Always backup your FMOD projects before use!

Full license: [docs/LICENSE.txt](docs/LICENSE.txt)

---

**Version:** 0.10.0
**Last update:** January 2025
