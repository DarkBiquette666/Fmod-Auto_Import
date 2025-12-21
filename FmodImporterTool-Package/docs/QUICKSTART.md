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

## With a Template (recommended)

If you already have events to copy:

1. Select a **Template Folder** (source folder)
2. Select a different **Event Folder** (destination)
3. Add your new audio files
4. **Analyze** → tool matches automatically
5. **Import** → events are copied with your new media

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
-  Test first on a small project
- Always backup your FMOD project before importing
- Use "Settings" to save your favorite folders
- Wait for the progress dialog to complete (don't close it manually)

---

**For more details:** See [../README.md](../README.md)
