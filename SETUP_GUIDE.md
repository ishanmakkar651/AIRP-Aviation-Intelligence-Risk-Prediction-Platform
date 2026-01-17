# 🚀 Complete Setup Guide for AIRP Platform

**Aviation Intelligence & Risk Prediction Platform**  
Complete step-by-step guide for running in VS Code or Cursor

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [Database Setup](#database-setup)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [VS Code / Cursor Setup](#vs-code--cursor-setup)
7. [Troubleshooting](#troubleshooting)
8. [Performance Optimizations](#performance-optimizations)

---

## 🎯 Prerequisites

### Required Software

1. **Python 3.8 or higher**
   - Download: https://www.python.org/downloads/
   - Verify: `python --version` or `python3 --version`

2. **PostgreSQL 13 or higher**
   - **Windows**: Download from https://www.postgresql.org/download/windows/
   - **Mac**: `brew install postgresql@15`
   - **Linux**: `sudo apt install postgresql postgresql-contrib`
   - Verify: `psql --version`

3. **Git**
   - Download: https://git-scm.com/downloads
   - Verify: `git --version`

4. **VS Code or Cursor**
   - VS Code: https://code.visualstudio.com/
   - Cursor: https://cursor.sh/

### Disk Space Requirements
- **Minimum**: 2GB free space
- **Recommended**: 5GB free space (for data and models)

---

## 📥 Installation Steps

### Step 1: Clone the Repository

```bash
# Using HTTPS
git clone https://github.com/ishanmakkar651/AIRP-Aviation-Intelligence-Risk-Prediction-Platform.git

# Navigate to project directory
cd AIRP-Aviation-Intelligence-Risk-Prediction-Platform
```

### Step 2: Create Virtual Environment

**Windows (CMD/PowerShell):**
```bash
# Create virtual environment
python -m venv .venv

# Activate (PowerShell)
.venv\Scripts\Activate.ps1

# Activate (CMD)
.venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
# Create virtual environment
python3 -m venv .venv

# Activate
source .venv/bin/activate
```

**✅ Verify Activation:**  
Your terminal should show `(.venv)` at the beginning of the prompt.

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

**Expected time:** 2-5 minutes depending on internet speed.

---

## 🗄️ Database Setup

### Step 1: Start PostgreSQL

**Windows:**
```bash
# PostgreSQL should start automatically as a service
# Check status in Services app (services.msc)
```

**Mac:**
```bash
brew services start postgresql@15
```

**Linux:**
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Auto-start on boot
```

### Step 2: Create Database and User

```bash
# Connect to PostgreSQL
psql -U postgres

# In the PostgreSQL prompt, run:
CREATE DATABASE aviation_db;
CREATE USER airp_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE aviation_db TO airp_user;
\q
```

### Step 3: Test Connection

```bash
psql -U airp_user -d aviation_db -h localhost
# If successful, you'll see the PostgreSQL prompt
# Type \q to exit
```

---

## ⚙️ Configuration

### Step 1: Copy Example Config

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

### Step 2: Edit config.yaml

Open `config.yaml` in your editor and update:

```yaml
database:
  host: 127.0.0.1
  port: 5432  # or 5434 if that's your PostgreSQL port
  name: aviation_db
  user: airp_user
  password: your_secure_password  # Use the password you created
```

**Important:** Keep the rest of the configuration as-is for now.

### Step 3: Initialize Database Schema

```bash
python 2_database/db_setup.py
```

**Expected Output:**
```
INFO - Database connection established
INFO - Database schema executed successfully
✅ Database initialized successfully
```

---

## 🚀 Running the Application

### Quick Start (Recommended Order)

#### 1️⃣ Load Airport Data (One-time setup)

```bash
python 1_data_ingestion/airport_loader.py
```

**What it does:** Loads airport reference data  
**Time:** ~30 seconds  
**Output:** Airport data in database

#### 2️⃣ Collect Flight Data (Initial data)

```bash
python 1_data_ingestion/opensky_collector.py
```

**What it does:** Fetches live flight data from OpenSky Network  
**Time:** ~2-3 minutes (collects data for 10 minutes)  
**Output:** Flight states in database  
**Note:** Press Ctrl+C after a few collections to stop

#### 3️⃣ Generate Features (If you have data)

```bash
python 3_feature_engineering/run_pipeline.py
```

**What it does:** Extracts ML features from flight data  
**Time:** 1-5 minutes (depends on data volume)  
**Output:** 
- `data/trajectory_features.csv`
- `data/fuel_efficiency_features.csv`
- `data/operational_features.csv`

#### 4️⃣ Train ML Models (If you have features)

```bash
python 4_models/train_all_models.py
```

**What it does:** Trains 3 ML models (risk, fuel, performance)  
**Time:** 2-10 minutes  
**Output:** Model files in `4_models/*/` directories

#### 5️⃣ Launch Dashboard 🎨

```bash
streamlit run 6_dashboard/app.py
```

**What it does:** Starts interactive web dashboard  
**Access:** Opens automatically at http://localhost:8501  
**Features:**
- 📊 Executive Overview
- 🔍 Flight Search
- 🤖 AI Assistant
- 🔧 Predictive Maintenance
- 📡 Real-time Monitoring

**Stop:** Press Ctrl+C in terminal

---

## 💻 VS Code / Cursor Setup

### Recommended Extensions

Install these extensions for the best experience:

1. **Python** (ms-python.python)
   - Syntax highlighting, IntelliSense, debugging

2. **Pylance** (ms-python.vscode-pylance)
   - Fast Python language server

3. **SQLTools** (mtxr.sqltools)
   - Database management in VS Code

4. **SQLTools PostgreSQL** (mtxr.sqltools-driver-pg)
   - PostgreSQL driver for SQLTools

5. **autoDocstring** (njpwerner.autodocstring)
   - Auto-generate Python docstrings

### VS Code Configuration

#### 1. Open Project in VS Code

```bash
# From project directory
code .
```

#### 2. Select Python Interpreter

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type "Python: Select Interpreter"
3. Choose the one that shows `.venv` (your virtual environment)

#### 3. Configure Launch Settings

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Dashboard",
            "type": "python",
            "request": "launch",
            "module": "streamlit",
            "args": [
                "run",
                "${workspaceFolder}/6_dashboard/app.py"
            ],
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": true
        }
    ]
}
```

#### 4. Recommended Settings

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".venv": false
    }
}
```

### Cursor IDE Setup

Cursor uses the same configuration as VS Code!  
Follow the same steps above.

**Bonus:** Use Cursor's AI features:
- Press `Ctrl+K` to ask AI about code
- Highlight code and press `Ctrl+L` for AI chat
- Use AI to help debug issues

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Failed

**Error:** `could not connect to server: Connection refused`

**Solutions:**
- Check if PostgreSQL is running: `pg_isready`
- Verify port in config.yaml matches your PostgreSQL port
- Windows: Check Services app for PostgreSQL service
- Mac/Linux: `sudo systemctl status postgresql`

#### 2. Module Not Found Errors

**Error:** `ModuleNotFoundError: No module named 'pandas'`

**Solutions:**
```bash
# Ensure virtual environment is activated
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 3. Port Already in Use (8501)

**Error:** `Address already in use`

**Solutions:**
```bash
# Windows: Find and kill process
netstat -ano | findstr :8501
taskkill /PID <process_id> /F

# Mac/Linux: Find and kill process
lsof -ti:8501 | xargs kill -9

# Or use a different port
streamlit run 6_dashboard/app.py --server.port 8502
```

#### 4. No Data in Dashboard

**Cause:** Haven't collected flight data yet

**Solution:**
```bash
# Collect some data first
python 1_data_ingestion/opensky_collector.py
# Wait for 2-3 collections, then Ctrl+C

# Generate features
python 3_feature_engineering/run_pipeline.py

# Train models
python 4_models/train_all_models.py

# Now launch dashboard
streamlit run 6_dashboard/app.py
```

#### 5. OpenSky API Rate Limit

**Error:** `429 Too Many Requests`

**Solution:**
- Free tier: 1 request per 10 seconds
- Wait 10+ seconds between collections
- Check `config.yaml` → `apis.opensky.rate_limit_seconds: 10`

#### 6. Virtual Environment Issues

**Problem:** Commands not found or wrong Python version

**Solutions:**
```bash
# Delete and recreate virtual environment
# Windows
rmdir /s .venv
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate

# Reinstall
pip install -r requirements.txt
```

---

## ⚡ Performance Optimizations

### Already Implemented ✅

This platform includes performance optimizations:

- ✅ **Database Indexes**: 10-100x faster queries
- ✅ **Connection Pooling**: Prevents connection exhaustion
- ✅ **Vectorized Calculations**: 5-20x speedup
- ✅ **Batch Operations**: 100x faster inserts
- ✅ **Memory Optimization**: 50% reduced memory usage

See `PERFORMANCE_IMPROVEMENTS.md` for details.

### System Requirements

**Minimum:**
- CPU: Dual-core 2GHz
- RAM: 4GB
- Disk: 2GB free

**Recommended:**
- CPU: Quad-core 2.5GHz+
- RAM: 8GB+
- Disk: 5GB free (SSD preferred)

### Optimizing for Large Datasets

If working with 100K+ flights:

1. **Enable Connection Pooling:**
```python
from 2_database.db_setup import DatabaseManager
db = DatabaseManager()
db.init_pool(minconn=2, maxconn=20)
```

2. **Use Chunked CSV Reading:**
```python
# In your custom scripts
df = pd.read_csv('large_file.csv', chunksize=10000)
```

3. **Limit Snapshot Retention:**
```python
# In 8_realtime_monitoring/realtime_streamer.py
streamer = RealTimeFlightStreamer(max_snapshots=50)
```

---

## 📖 Additional Resources

### Documentation
- **README.md** - Project overview
- **PERFORMANCE_IMPROVEMENTS.md** - Performance details
- **PHASE3_QUICKSTART.md** - ML models guide

### API Documentation
- OpenSky Network: https://opensky-network.org/apidoc/
- Streamlit: https://docs.streamlit.io/

### Getting Help
- Create an issue: https://github.com/ishanmakkar651/AIRP-Aviation-Intelligence-Risk-Prediction-Platform/issues
- Review documentation in the repo

---

## 🎯 Quick Command Reference

```bash
# Activate virtual environment
.venv\Scripts\activate           # Windows
source .venv/bin/activate        # Mac/Linux

# Collect data
python 1_data_ingestion/opensky_collector.py

# Generate features
python 3_feature_engineering/run_pipeline.py

# Train models
python 4_models/train_all_models.py

# Launch dashboard
streamlit run 6_dashboard/app.py

# Validate optimizations
python validate_optimizations.py

# Real-time monitoring
python 8_realtime_monitoring/start_continuous.py
```

---

## ✅ Verification Checklist

Before considering setup complete, verify:

- [ ] PostgreSQL running and accessible
- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip list`)
- [ ] Database initialized (tables created)
- [ ] Airport data loaded
- [ ] Config.yaml updated with credentials
- [ ] At least one data collection completed
- [ ] Features generated (CSV files in `data/`)
- [ ] Models trained (PKL files in `4_models/`)
- [ ] Dashboard launches at http://localhost:8501
- [ ] Can see data in dashboard pages

---

## 🎉 Success!

If you've completed all steps, you now have a fully functional Aviation Intelligence & Risk Prediction Platform!

**Next Steps:**
1. Explore the dashboard pages
2. Try the AI Assistant
3. Set up continuous monitoring
4. Customize for your region (update `config.yaml`)

**Happy Flying! ✈️**

---

*Last Updated: 2026-01-17*  
*Platform Version: 2.0 (Performance Optimized)*
