# Conner POS - Compilation Guide

## Overview

This compilation system allows you to generate a Windows executable (`Conner POS.exe`) that includes both the Flask backend and the compiled Angular frontend. The resulting executable is a desktop application that can be installed on any Windows computer and serve as a POS server for multiple clients on the local network.

## Prerequisites

### Required Software

1. **Python 3.12+**
   - Download from: https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

2. **Node.js 18+**
   - Download from: https://nodejs.org/
   - Includes npm automatically

3. **Angular CLI**
   ```bash
   npm install -g @angular/cli
   ```

4. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Verify Requirements

Before compiling, run the verification script:

```bash
python check_requirements.py
```

This script will verify that all necessary tools are installed and configured correctly.

## Configuration

### 1. Create Configuration File

Copy the example file and adjust as needed:

```bash
copy .compile.env.example .compile.env
```

### 2. Configure Variables (Optional)

Edit `.compile.env` to customize the compilation:

```env
# Project paths
FRONTEND_PATH=../conner-front-1.2
BACKEND_PATH=.

# Backend IP (optional, auto-detected)
# BACKEND_IP=192.168.1.100
BACKEND_PORT=5000

# Compilation configuration
ANGULAR_BUILD_CONFIG=production
PYINSTALLER_OPTIONS=--onedir --windowed

# Executable name
EXE_NAME=Conner POS
```

## Compilation Process

### Option 1: Full Compilation (Recommended)

Run the master script that orchestrates the entire process:

```bash
python compile_all.py
```

This script will automatically execute:
1. Prerequisites verification
2. Angular frontend compilation
3. Backend preparation
4. Executable generation with PyInstaller

**Estimated time:** 6-13 minutes

### Option 2: Step-by-Step Compilation

If you prefer to execute each step manually:

#### Step 1: Compile Frontend
```bash
python compile_frontend.py
```

This script:
- Automatically detects the server's LAN IP
- Updates `environment.ts` with the detected IP
- Executes `ng build --configuration production`
- Copies compiled files to `templates/` and `static/`

#### Step 2: Prepare Backend
```bash
python prepare_backend.py
```

This script:
- Verifies directory structure
- Validates that frontend files are present
- Verifies Python dependencies

#### Step 3: Generate Executable
```bash
python build_exe.py
```

This script:
- Generates the PyInstaller `.spec` file
- Compiles the executable with all dependencies
- Creates the installer structure

## Compilation Result

After a successful compilation, you will find:

```
conner-back-1.2/
├── dist/
│   ├── Conner POS/              # Executable and dependencies
│   │   ├── Conner POS.exe       # Main executable
│   │   └── _internal/           # Dependencies
│   └── Conner POS_Installer/    # Installation package
│       ├── Conner POS/          # Executable folder
│       ├── install.bat          # Installation script
│       ├── uninstall.bat        # Uninstallation script
│       └── README.txt           # User instructions
```

## Executable Installation

### For End Users

1. Navigate to `dist/Conner POS_Installer/`
2. Run `install.bat` as Administrator
3. Follow the on-screen instructions
4. The shortcut will be created on the desktop

### Test Without Installation

To test the executable without installing:

1. Navigate to `dist/Conner POS/`
2. Run `Conner POS.exe`
3. Open browser at `http://localhost:5000/dashboard`

## System Features

### Automatic IP Detection

The system automatically detects the server's LAN IP during compilation. This allows:
- The frontend to automatically configure to connect to the backend
- Clients on the local network to access the system using the server's IP

### Database on First Startup

The SQLite database is automatically created on the executable's first startup:
- No need to include a pre-configured database
- The system creates all necessary tables
- Data is stored in `db/conner.db`

### Integrated Static Files

The compiled frontend is fully integrated into the executable:
- All HTML, CSS and JavaScript files are included
- Images and assets are packaged correctly
- No additional external files required

## Troubleshooting

### Error: Angular CLI not found

**Problem:** The system cannot find the `ng` command

**Solution:**
```bash
npm install -g @angular/cli
```

### Error: PyInstaller not found

**Problem:** The system cannot find PyInstaller

**Solution:**
```bash
pip install pyinstaller
```

### Error: Cannot detect LAN IP

**Problem:** The script cannot automatically detect the IP

**Solution:**
1. Edit `.compile.env`
2. Uncomment and set `BACKEND_IP` manually:
   ```env
   BACKEND_IP=192.168.1.100
   ```

### Error: Static files not loading

**Problem:** The frontend doesn't load correctly in the browser

**Solution:**
1. Verify that `compile_frontend.py` executed correctly
2. Verify that `templates/` and `static/browser/` folders exist
3. Review logs in `compilation.log`

### Error: Executable doesn't start

**Problem:** The executable closes immediately or doesn't respond

**Solution:**
1. Run from CMD to see error messages:
   ```bash
   cd "dist\Conner POS"
   "Conner POS.exe"
   ```
2. Verify that port 5000 is not in use
3. Review the `.env` file in the executable folder

## Logs and Debugging

### Compilation Log File

All compilation steps are logged in:
```
compilation.log
```

This file contains:
- Detailed information for each step
- Error messages if something fails
- Execution times for each phase

### Executable Logs

When the executable is running, it generates logs in:
```
app-back.log
```

## Customization

### Change Executable Name

Edit `.compile.env`:
```env
EXE_NAME=My Custom POS
```

### Add an Icon

1. Create or obtain a `.ico` file
2. Place it in the backend folder
3. Edit `.compile.env`:
   ```env
   ICON_PATH=my_icon.ico
   ```

### Modify PyInstaller Options

Edit `.compile.env`:
```env
# For single-file executable (slower to start)
PYINSTALLER_OPTIONS=--onefile --windowed

# For executable with console (useful for debugging)
PYINSTALLER_OPTIONS=--onedir --console
```

## Best Practices

### Before Compiling

1. ✅ Test backend and frontend in development mode
2. ✅ Verify that all tests pass
3. ✅ Update version in corresponding files
4. ✅ Review and update `.env` file if necessary

### During Compilation

1. ✅ Do not interrupt the compilation process
2. ✅ Review logs if something fails
3. ✅ Ensure sufficient disk space (minimum 2 GB)

### After Compiling

1. ✅ Test the executable before distributing
2. ✅ Verify that all endpoints work
3. ✅ Test access from other computers on the network
4. ✅ Create a backup of the installer

## Distribution

### Prepare for Distribution

1. Compress the `Conner POS_Installer/` folder into a ZIP file
2. Include the `README.txt` file with instructions
3. Document system requirements

### System Requirements for End Users

- Windows 10 or higher
- 4 GB RAM minimum
- 500 MB disk space
- Local network connection (for access from multiple computers)

## Updates

### To Update the System

1. Make changes to the source code
2. Run `python compile_all.py` again
3. Distribute the new installer

### Data Migration

The database is maintained in the installation folder:
```
C:\Program Files\Conner POS\db\conner.db
```

To migrate data:
1. Backup `conner.db`
2. Install the new version
3. Replace `conner.db` with the backup

## Support and Documentation

### Complete Documentation

For more information about Conner POS:
- [Complete Documentation](https://docs.google.com/document/d/14uFWKk8CKpCPhdW8aYYKkdY7IRwmmGYA2K6tv9guP_Q/edit)
- [Compilation Plan](COMPILATION_PLAN.md)
- [Agents Guide](../AGENTS.md)

### Reference Files

- `check_requirements.py` - Requirements verification
- `compile_frontend.py` - Frontend compilation
- `prepare_backend.py` - Backend preparation
- `build_exe.py` - Executable generation
- `compile_all.py` - Master compilation script

## License and Credits

**Conner POS** - Point of Sale System for Micro-enterprises

Author: [@adriandDev](https://www.github.com/adritruji6051)

---

**Last updated:** June 19, 2026