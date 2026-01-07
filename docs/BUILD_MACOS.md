# Building FMOD Importer for macOS

The FMOD Importer tool is now source-compatible with macOS. However, you cannot build a macOS application (`.app` or Mach-O executable) from Windows. You must build it on a Mac.

## Prerequisites (on macOS)

1.  **Python 3.10+**: Install via [Homebrew](https://brew.sh/) or Python.org.
    ```bash
    brew install python
    ```
2.  **FMOD Studio**: Ensure FMOD Studio is installed in `/Applications/FMOD Studio/`.

## Build Instructions

1.  **Clone the repository** to your Mac.
2.  **Open Terminal** and navigate to `FmodImporter-Dev`.
3.  **Install PyInstaller**:
    ```bash
    pip3 install pyinstaller
    ```
4.  **Run the Build**:
    ```bash
    pyinstaller FmodImporter.spec --clean --noconfirm
    ```
5.  **Locate the App**:
    The built executable will be in `dist/FmodImporter`.

## Troubleshooting macOS Issues

### "App is damaged and can't be opened"
This is a common macOS security feature for unsigned apps.
To fix:
1.  Open Terminal.
2.  Run: `xattr -cr /path/to/dist/FmodImporter`

### Terminal Window
The `.spec` file is configured with `console=False`. However, on macOS, `pyinstaller` generates a Unix executable by default. To create a proper `.app` bundle, you might need to adjust the `.spec` file or use `--windowed` explicitly if it wasn't picked up.

If the generated output is just a binary file `FmodImporter` instead of `FmodImporter.app`:
PyInstaller on macOS typically creates a directory or a binary. For a proper `.app` bundle, ensure your `.spec` file has `app = BUNDLE(...)` section (which requires adjustments).

**Current Spec File Note:** The current `FmodImporter.spec` creates a single-file/folder executable (`EXE`). On macOS, this results in a command-line binary. It will work, but it won't look like a native Mac app icon.

To generate a `.app` bundle, add this to `FmodImporter.spec` (only on Mac):

```python
import platform
if platform.system() == 'Darwin':
    app = BUNDLE(
        exe,
        name='FmodImporter.app',
        icon='Logo/FmodImporterLogo.icns',
        bundle_identifier='com.darkbiquette.fmodimporter'
    )
```
