# Weather App - Update System Documentation

## Overview
The Weather application includes a complete auto-update system that allows users to update the application with one click from within the app itself.

## Components

### 1. **UpdateManager Class** (in Weather.py)
The `UpdateManager` class handles all update-related functionality:
- Checking for new versions on GitHub
- Downloading updates
- Launching the updater executable
- Version comparison

### 2. **updater.exe** (C++ Executable)
Located in `/Updater/updater.exe`, this is a standalone C++ program that:
- Closes the main Weather application
- Downloads the new version
- Replaces the old executable
- Restarts the application
- Handles file locking and cleanup

### 3. **GUI Integration**
The main Weather.py GUI includes:
- **"🔄 Check Updates" button** in the header
- **Automatic update check** on startup (silent, background)
- **Update notification** if new version is available
- **Progress dialog** during update installation

---

## How It Works

### Update Check Flow

```
[App Startup]
    ↓
[Background thread checks GitHub API]
    ↓
[If update available] → Update button changes to "⬇️ Update Available"
    ↓
[User clicks button]
    ↓
[Show dialog with release notes]
    ↓
[User confirms] → Download & Install
```

### Update Installation Flow

```
[User confirms update]
    ↓
[Download updater.exe if needed]
    ↓
[Launch updater.exe with arguments]
    ↓
[Weather.exe closes]
    ↓
[updater.exe waits for process to close]
    ↓
[updater.exe downloads new Weather.exe]
    ↓
[updater.exe replaces old file]
    ↓
[updater.exe restarts Weather.exe]
    ↓
[updater.exe exits]
```

---

## File Structure

```
Weather/
├── Weather.exe              # Main application
├── Weather.py               # Source code with UpdateManager
├── file_handler.py          # File utilities
├── Updater/
│   ├── updater.exe          # Compiled updater (included in build)
│   ├── updater_final.cpp    # Updater source code
│   ├── compile_updater.bat  # Compile script for updater
│   └── test_update.bat      # Test script for updater
├── Weather.spec             # PyInstaller spec (includes updater)
├── compiler.bat             # Main build script
└── requirements.txt         # Python dependencies
```

---

## Building the Application

### Building Weather.exe (with updater included)

```bash
# Option 1: Use the menu
compiler.bat
# Then select: 1. ONEDIR

# Option 2: Direct PyInstaller
pyinstaller --clean Weather.spec
```

The `Weather.spec` file automatically includes:
- `updater/updater.exe` → copied to `updater/` folder in dist
- All necessary DLLs (SSL, Python, etc.)
- Icon file if present

**Output:** `dist/Weather/Weather.exe` with `dist/Weather/updater/updater.exe` included

---

## Compiling the Updater

If you need to recompile the updater:

```bash
cd Updater
compile_updater.bat
```

**Requirements:**
- MinGW-w64 or MSYS2 with g++
- Windows API libraries

**Output:** `Updater/updater.exe`

---

## Update System Configuration

### In Weather.py:

```python
# Version and repository
VERSION = "1.0.0"
GITHUB_REPO = "Rog294super/Weather-App"

# UpdateManager initialization
self.update_manager = UpdateManager(VERSION, GITHUB_REPO)
```

### GitHub Release Requirements:

For the update system to work, GitHub releases must include:
1. **Tag format:** `v1.0.0` (or any version string)
2. **Required assets:**
   - `Weather.exe` - Main executable
   - `updater.exe` (optional, will be downloaded if missing)
3. **Release notes** in the body (displayed to users)

---

## Weather.spec Configuration

Key sections that include the updater:

```python
a = Analysis(
    ['Weather.py'],
    pathex=[],
    binaries=binaries,
    datas=[item for item in [
        # This line includes the updater
        ('updater\\updater.exe', 'updater') if os.path.exists('updater\\updater.exe') else None,
        ('Weather_icon.ico', '.') if os.path.exists('Weather_icon.ico') else None,
    ] if item is not None],
    # ... rest of config
)
```

**Important:** The path is `updater\\updater.exe` (lowercase) but the actual folder is `Updater` (capital). This needs to be verified before building.

---

## Testing the Update System

### 1. Test Update Manually

```bash
cd Updater
test_update.bat "https://github.com/Rog294super/Weather-App/releases/download/v1.0.0/Weather.exe"
```

### 2. Test Full Flow

1. Build the application:
   ```bash
   compiler.bat
   # Choose option 1
   ```

2. Run the built executable:
   ```bash
   dist\Weather\Weather.exe
   ```

3. Create a test release on GitHub with a higher version number

4. Click "🔄 Check Updates" in the application

5. Confirm the update when prompted

---

## Common Issues & Solutions

### Issue 1: "updater.exe not found"
**Cause:** The updater wasn't included in the build
**Solution:** 
- Check that `Updater/updater.exe` exists
- Verify the path in `Weather.spec` matches actual folder name
- Rebuild with `compiler.bat`

### Issue 2: Path mismatch in Weather.spec
**Current code:**
```python
('updater\\updater.exe', 'updater')  # lowercase 'updater'
```
**Actual folder:**
```
Updater/updater.exe  # capital 'U'
```
**Solution:** Either:
- Rename `Updater` folder to `updater` (lowercase), OR
- Update Weather.spec to use `('Updater\\updater.exe', 'updater')`

### Issue 3: Update check fails silently
**Cause:** Network error, GitHub API rate limit, or invalid repo name
**Solution:** 
- Check internet connection
- Verify `GITHUB_REPO` constant in Weather.py
- Check logs in `weather_debug.log`

### Issue 4: Application doesn't restart after update
**Cause:** Updater might not be finding the executable path correctly
**Solution:** 
- Check updater logs
- Verify the updater delay script is working
- Manual restart may be required

---

## Version Comparison

Currently using **simple string comparison**:

```python
if latest_version > self.current_version:
    # Update available
```

**Limitations:**
- "1.10.0" < "1.9.0" (incorrect)
- "2.0.0" < "10.0.0" (correct by chance)

**Recommended:** Implement proper semantic versioning:

```python
from packaging import version

if version.parse(latest_version) > version.parse(self.current_version):
    # Update available
```

Add to requirements.txt: `packaging>=21.0`

---

## Security Considerations

1. **HTTPS only:** All downloads use HTTPS
2. **GitHub releases:** Official release mechanism
3. **Signature verification:** NOT currently implemented
4. **User confirmation:** Required before any update

**Recommended improvement:** Add checksum verification

---

## Future Enhancements

1. **Automatic updates:** Option to auto-update without user prompt
2. **Update schedule:** Check for updates daily/weekly
3. **Rollback feature:** Ability to revert to previous version
4. **Delta updates:** Download only changed files (reduce bandwidth)
5. **Checksum verification:** Verify downloaded file integrity
6. **Silent mode:** Update in background without UI
7. **Beta channel:** Allow users to opt into beta releases

---

## Updater.exe Arguments

The updater accepts two command-line arguments:

```bash
updater.exe <download_url> <target_path>
```

**Example:**
```bash
updater.exe "https://github.com/user/repo/releases/download/v1.0.0/Weather.exe" "C:\Program Files\Weather\Weather.exe"
```

**Process:**
1. Waits 3 seconds for parent process to exit
2. Terminates Weather.exe if still running
3. Downloads new version to temp location
4. Backs up old Weather.exe
5. Moves new version into place
6. Creates delayed start script
7. Exits (delayed script starts Weather.exe after 3 seconds)

---

## Debugging

### Enable detailed logging:

```python
# In Weather.py
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('weather_debug.log'),
        logging.StreamHandler()
    ]
)
```

### Check logs:
- Main app: `weather_debug.log`
- Updater: Console output (redirect to file if needed)

---

## Distribution Checklist

Before releasing a new version:

- [ ] Update `VERSION` constant in Weather.py
- [ ] Update version.txt (for PyInstaller)
- [ ] Build with `compiler.bat`
- [ ] Test the executable manually
- [ ] Test update mechanism with dummy release
- [ ] Create GitHub release with tag `vX.X.X`
- [ ] Upload `Weather.exe` as asset
- [ ] Upload `updater.exe` as asset (optional)
- [ ] Add release notes
- [ ] Test download and update from previous version

---

## Summary

✅ **What's Working:**
- Update checking from GitHub API
- Version comparison
- Download and installation via updater.exe
- GUI integration with update button
- Progress dialogs
- Automatic restart after update

✅ **What's Included in Build:**
- updater.exe is bundled via Weather.spec
- All necessary DLLs and dependencies

⚠️ **Potential Issue:**
- Path mismatch: `updater\\updater.exe` in spec vs `Updater/updater.exe` folder
- **Fix:** Rename folder to lowercase `updater` or update spec file

🔧 **Recommended Improvements:**
- Implement semantic versioning comparison
- Add checksum verification
- Better error handling and user feedback
- Consider delta updates for larger files
