# Quick Start Guide - FMOD Importer Tool

## Setup in 1 Step

### Simply double-click `FmodImporter.exe`

**That's it!** This is a standalone Windows executable - **no Python installation required!**

**Note:** The first launch may take a few seconds as the executable extracts its dependencies.

---

## First Import in 5 Minutes

### Step 0: Ensure FMOD Studio is closed
**IMPORTANT:** Close FMOD Studio completely before using this tool!

### Step 1: Load your FMOD project
- Click "Browse..." → Select your `.fspro`
- Click "Load"
- **Tip:** Save this path in Settings to auto-load it next time!

### Step 2: Select your audio files
- Click "Browse..." (Media Files)
- Choose the folder with your .wav/.mp3 files

### Step 3: Configure destination
- **Event Folder:** Click "Select..." → Choose where to create events
- **Bank:** Click "Select..." → Choose a bank
- **Bus:** Click "Select..." → Choose a bus

### Step 4: Analyze
- Click "Analyze"
- Check the match list

### Step 5: Import
- Click "Import"
- **A progress dialog will appear** - wait for completion (1-5 minutes)
- Open FMOD Studio and save (Ctrl+S)

**That's it!**

---

## Import Modes (New in v0.10.0)

### Match Template Mode (Default)

If you have existing events to copy:

1. Keep **"Match Template"** selected
2. Select a **Template Folder** (source folder)
3. Select a different **Event Folder** (destination)
4. Add your new audio files
5. **Analyze** → tool matches automatically
6. **Import** → events are copied with your new media

### Generate from Pattern Mode

If you want to create events from file names:

1. Select **"Generate from Pattern"** mode
2. Template Folder will be hidden (not needed)
3. Enter **Asset Name Pattern** (e.g., `$prefix_$feature_$action`)
4. Leave **Event Name Pattern** empty to use same pattern, or customize
5. **Analyze** → tool parses file names
6. **Import** → events are created based on patterns

---

## Common Issues

**"Please select a destination folder"**
→ Open the "Event Folder" dropdown and select a folder

**"Could not find FMOD Studio executable"**
→ Use the "Browse..." button next to FMOD Studio Executable to locate your FMOD installation

**"FMOD version mismatch detected"**
→ Update FMOD Studio or project to match versions (shown in main UI)

**"Tool doesn't launch"**
→ Ensure Windows 10 or later (64-bit). First launch may take longer.

**Changes don't appear in FMOD**
→ Open FMOD Studio and save the project (Ctrl+S)

---

## Tips

- Name your files consistently for better matching
- Test first on a small project
- Always backup your FMOD project before importing
- Wait for the progress dialog to complete (don't close it manually)

**💡 Save Time - Configure Default Settings:**
- Click **"Settings"** button (bottom of window) after your first setup
- Save your project path and FMOD executable as defaults
- Next time you launch the tool, everything will be pre-filled automatically!
- Especially useful if you always work on the same project

---

**For more details:** See [../README.md](../README.md)
