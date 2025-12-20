# FMOD Importer Tool - Automatic Audio Asset Importer for FMOD Studio

**Version:** 0.2.0
**Description:** Standalone Windows application for intelligently importing audio assets into FMOD Studio projects

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

**That's it!** This is a standalone executable - **no Python installation required!**

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

### 2. Configuration

**Required fields:**

- **Event Folder (Destination)**: FMOD folder where events will be created
- **Bank**: FMOD bank to assign to events
- **Bus**: Mixing bus for events
- **Asset Folder**: Audio asset folder
- **Prefix**: Prefix to add to event names (e.g., "Mechaflora")
- **FeatureName**: Feature or character name (e.g., "Weak_Ranged")

**Optional fields:**

- **Template Folder**: Existing template folder to copy from

### 3. Recommended Workflow

#### **Option A: Import from Template**

1. Select an existing **Template Folder**
2. Click **"Analyze"**
3. Tool automatically detects template events
4. Verify matches in the list
5. Click **"Import"**

#### **Option B: Direct Import (no template)**

1. Do NOT select a Template Folder
2. Click **"Analyze"**
3. Tool creates basic events for each audio file
4. Check the event list
5. Click **"Import"**

### 4. Icon Interpretation

In the import event list:

- **✓**: Perfect match found
- **~**: Approximate match (medium confidence)
- **?**: No match found
- **+**: Auto-created event (no template)

### 5. Match Management

**Orphan Media Files** (files without event):
- Right-click to manually assign to an event

**Orphan Events** (events without media):
- Right-click to manually assign an audio file

### 6. Finalization

1. Verify all matches
2. Click **"Import"**
3. Wait for import completion
4. **Important:** Now you can open FMOD Studio and save the project (Ctrl+S)
5. **Remember:** The tool directly modifies XML files, so never have FMOD Studio open while importing

---

## Advanced Settings

Access via the **"Settings"** button at the bottom of the interface.

### Default Values

You can save your favorite selections:
- Default FMOD Project
- FMOD Studio Executable
- Default Media Directory
- Default Template Folder
- Default Bank
- Default Destination Folder
- Default Bus
- Default Event Separator
- Default Asset Separator

These values will be pre-filled on next launch.

---

## Common Use Cases

### Case 1: Create variations of an existing character

**Scenario:** You have a "Weak_Template" template and want to create "Mechaflora Weak Ranged"

1. **Prefix:** `Mechaflora`
2. **FeatureName:** `Weak_Ranged`
3. **Template Folder:** Select "Weak_Template" folder
4. **Destination Folder:** Select/create "Mechaflora Weak Ranged"
5. **Media Files:** Point to new audio files
6. **Analyze** then **Import**

### Case 2: Quick import without template

**Scenario:** You just have audio files to import quickly

1. Do **NOT** select a Template Folder
2. **Destination Folder:** Choose where to create events
3. **Bank, Bus:** Select appropriate values
4. **Media Files:** Point to your files
5. **Analyze** then **Import**

### Case 3: Reorganize existing events

**Scenario:** You want to copy events to a new folder with new media

1. **Template Folder:** Source folder
2. **Destination Folder:** New target folder
3. **Media Files:** New audio files
4. **Analyze** to see matches
5. Adjust manually if needed
6. **Import**

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
**Solution:** Fill in both required fields with actual values (not "e.g. Sfx" or "e.g. BlueEyesDragon")

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

**Version:** 0.2.0
**Last update:** December 2025
