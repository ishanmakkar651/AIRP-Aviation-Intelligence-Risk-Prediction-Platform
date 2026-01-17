# VS Code Configuration Files

This directory contains recommended VS Code/Cursor IDE configurations for the AIRP platform.

## Setup

To use these configurations:

### Option 1: Automatic (During Setup)

The setup scripts will automatically copy these files:

```bash
# Windows
setup.bat

# Mac/Linux
./setup.sh
```

### Option 2: Manual Copy

```bash
# Copy the entire directory
cp -r .vscode.example .vscode

# Or copy individual files
cp .vscode.example/launch.json .vscode/
cp .vscode.example/settings.json .vscode/
cp .vscode.example/extensions.json .vscode/
```

## Files Included

### launch.json
Debug configurations for:
- 🎨 Dashboard
- 📊 Feature Engineering
- 🤖 Train Models
- 📡 Data Collection
- 🗄️ Database Setup
- ✅ Validate Optimizations
- 📄 Current File

### settings.json
- Python interpreter path (.venv)
- Linting configuration (flake8)
- Formatting (black)
- File exclusions
- Terminal environment

### extensions.json
Recommended extensions:
- Python
- Pylance
- Black Formatter
- SQLTools
- PostgreSQL Driver
- Auto Docstring
- Git tools

## Usage

After copying, press F5 in VS Code to see debug options, or use the Run and Debug panel (Ctrl+Shift+D).

## Customization

Feel free to modify these files to match your preferences. They won't be tracked by git (they're in .gitignore).
