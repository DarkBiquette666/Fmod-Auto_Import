# Moco Auto Import - Automatic Audio Asset Importer for FMOD Studio

**Version:** 1.0
**Author:** Moco
**Description:** Python GUI tool for intelligently importing audio assets into FMOD Studio projects

---

## 📋 Description

Moco Auto Import is a GUI tool that facilitates intelligent audio file importation into FMOD Studio projects. It allows you to:

- ✅ Automatically create FMOD events from audio files
- ✅ Detect and import from existing template folders
- ✅ Intelligently match audio files with events
- ✅ Automatically organize events in specific folders
- ✅ Auto-assign banks, buses, and asset folders
- ✅ Intuitive interface with visual feedback

---

## 🔧 Requirements

### Required Software

1. **Python 3.8 or higher**
   - Download from: https://www.python.org/downloads/
   - ⚠️ During installation, check "Add Python to PATH"

2. **FMOD Studio**
   - Version 2.0 or higher recommended
   - Works with FMOD Studio projects (.fspro)

### Verify Python Installation

Open a terminal/command prompt and type:
```bash
python --version
```

You should see something like: `Python 3.12.0`

---

## 📦 Installation

### Simple - No Installation Required!

1. **Extract the package**
   - Unzip the `MocoAutoImport-Package` folder to your desired location
   - Example: `C:\Tools\MocoAutoImport-Package`

2. **Verify Python**
   - Python 3.8+ must be installed
   - All required libraries (tkinter, xml, json) are already included in Python!

3. **That's it!** The tool is ready to use.

---

## 🚀 Usage

### Launching the Application

**Windows:**
```bash
launch.bat
```

OR double-click on `launch.bat`

**macOS/Linux:**
```bash
chmod +x launch.sh
./launch.sh
```

**Command line (all platforms):**
```bash
python moco_auto_import.py
```

---

## 📖 User Guide

### 1️⃣ Initial Setup

1. **Load an FMOD Project**
   - Click "Browse..." next to "FMOD Project"
   - Select your `.fspro` file
   - Click "Load" to load the project

2. **Select Media Folder**
   - Click "Browse..." next to "Media Files Directory"
   - Select the folder containing your audio files (.wav, .mp3, etc.)

### 2️⃣ Configuration

**Required fields:**

- **Event Folder (Destination)**: FMOD folder where events will be created
- **Bank**: FMOD bank to assign to events
- **Bus**: Mixing bus for events

**Optional fields:**

- **Template Folder**: Existing template folder to copy from
- **Prefix**: Prefix to add to event names (e.g., "Cat")
- **Character Name**: Character name (e.g., "Infiltrator")
- **Asset Folder**: Audio asset folder

### 3️⃣ Recommended Workflow

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

### 4️⃣ Icon Interpretation

In the import event list:

- **✓** (green): Perfect match found
- **~** (orange): Approximate match (medium confidence)
- **?** (red): No match found
- **+** (blue): Auto-created event (no template)

### 5️⃣ Match Management

**Orphan Media Files** (files without event):
- Double-click to manually assign to an event

**Orphan Events** (events without media):
- Double-click to manually assign an audio file

### 6️⃣ Finalization

1. Verify all matches
2. Click **"Import"**
3. Wait for import completion (progress bar shown)
4. **Important:** Open FMOD Studio and save the project

---

## ⚙️ Advanced Settings

Access via the **"Settings"** button at the bottom of the interface.

### Match Thresholds

- **Perfect Match Threshold**: Minimum score for perfect match (default: 90)
- **Good Match Threshold**: Minimum score for acceptable match (default: 70)

### Default Values

You can save your favorite selections:
- Default Template Folder
- Default Destination Folder
- Default Bank
- Default Bus
- Default Asset Folder

These values will be pre-filled on next launch.

---

## 🎯 Common Use Cases

### Case 1: Create variations of an existing character

**Scenario:** You have a "Cat Melee" template and want to create "Cat Ranged"

1. **Prefix:** `Cat`
2. **Character Name:** `Ranged`
3. **Template Folder:** Select "Cat Melee" folder
4. **Destination Folder:** Select/create "Cat Ranged"
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

## 🐛 Troubleshooting

### "Please select a destination folder"

**Cause:** Destination folder not selected
**Solution:** Click "Select..." next to "Event Folder" and choose a folder

### "Please select a bank"

**Cause:** No bank selected
**Solution:** Click "Select..." next to "Bank" and choose a bank

### Import does nothing / no changes in FMOD

**Cause:** Changes not saved yet
**Solution:**
1. Open FMOD Studio
2. **File > Save Project** (Ctrl+S)
3. Changes will appear

### "Failed to load project"

**Possible causes:**
- .fspro file is corrupted
- Metadata folder doesn't exist
- Insufficient permissions

**Solution:** Verify the project opens correctly in FMOD Studio

### Tkinter not available (Linux)

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-tkinter
```

### Audio files not detected

**Check:**
- Files have extension .wav, .mp3, .ogg, .flac, etc.
- Folder path is correct
- You have read permissions

---

## 📁 Package Structure

```
MocoAutoImport-Package/
├── moco_auto_import.py    # Main Python script
├── README.md              # Main documentation (this file)
├── launch.bat             # Windows launcher
├── launch.sh              # macOS/Linux launcher
└── docs/                  # Documentation folder
    ├── QUICKSTART.md      # Quick start guide
    ├── INDEX.md           # Package overview
    ├── LICENSE.txt        # MIT License and disclaimer
    ├── VERSION.txt        # Version information
    └── requirements.txt   # Python dependencies list
```

---

## 💡 Tips and Best Practices

### ✅ Do

- **Always backup** your FMOD project before using the tool
- **Verify matches** before importing
- **Use consistent file names** for better automatic matching
- **Test with a small set** of files first

### ❌ Avoid

- **Don't** import into an open FMOD project (close FMOD Studio first)
- **Don't** interrupt import in progress
- **Don't** modify FMOD project while tool is running
- **Don't** use special characters in file names

### 🔍 Recommended File Naming

For optimal matching, name your files like this:

```
Prefix_CharacterName_Action_Variation.wav
```

**Examples:**
```
Cat_Infiltrator_Attack_01.wav
Cat_Infiltrator_Jump_01.wav
Cat_Infiltrator_Death_01.wav
```

---

## 🔄 Updates

To update the tool:
1. Backup your settings if important
2. Replace `moco_auto_import.py` with the new version
3. Relaunch the application

---

## 📞 Support

In case of problems:
1. Check the "Troubleshooting" section above
2. Verify Python and FMOD are correctly installed
3. Test with a simple FMOD project
4. See [docs/QUICKSTART.md](docs/QUICKSTART.md) for quick reference

---

## 📜 License

This tool is provided "as is" without warranty. Use at your own risk.

**Important:** Always backup your FMOD projects before use!

Full license: [docs/LICENSE.txt](docs/LICENSE.txt)

---

## 🎵 Credits

Developed by **Moco**
For automated audio asset import into FMOD Studio

---

**Version:** 1.0
**Last update:** November 2024
