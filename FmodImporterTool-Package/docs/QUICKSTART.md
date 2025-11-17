# 🚀 Quick Start Guide - FMOD Importer Tool

## Setup in 2 Steps

### 1. Verify Python
Open a terminal and type:
```bash
python --version
```
If error → Install Python from https://www.python.org/downloads/

**Note:** Python 3.8+ already includes all required libraries (tkinter, xml, json, etc.)

### 2. Launch
**Windows:** Double-click on `launch.bat`
**macOS/Linux:** `./launch.sh`

**Or directly:**
```bash
python fmod_importer.py
```

---

## First Import in 5 Minutes

### 1️⃣ Load your FMOD project
- Click "Browse..." → Select your `.fspro`
- Click "Load"

### 2️⃣ Select your audio files
- Click "Browse..." (Media Files)
- Choose the folder with your .wav/.mp3 files

### 3️⃣ Configure destination
- **Event Folder:** Click "Select..." → Choose where to create events
- **Bank:** Click "Select..." → Choose a bank
- **Bus:** Click "Select..." → Choose a bus

### 4️⃣ Analyze
- Click "Analyze"
- Check the match list

### 5️⃣ Import
- Click "Import"
- Wait for completion
- Open FMOD Studio and save (Ctrl+S)

**That's it!** 🎉

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

**"tkinter not found" (Linux)**
→ `sudo apt-get install python3-tk`

**Changes don't appear in FMOD**
→ Open FMOD Studio and save the project (Ctrl+S)

---

## Tips

✅ Name your files consistently for better matching
✅ Test first on a small project
✅ Always backup your FMOD project before importing
✅ Use "Settings" to save your favorite folders

---

📖 **For more details:** See [../README.md](../README.md)
