# 🚈 AIRP - Aviation Intelligence & Risk Prediction Platform

A comprehensive Python-based platform for analyzing flight operations, detecting inefficiencies, predicting maintenance needs, and monitoring real-time aviation data. Built with machine learning and advanced analytics for operational excellence.

![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-Active-brightgreen)
![Performance](https://img.shields.io/badge/performance-optimized-success)

---

## 🚀 Quick Start

**New to the project? Start here:**

### Option 1: Automated Setup (Recommended)

**Windows:**
```bash
setup.bat
```

**Mac/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

### Option 2: Launch Dashboard Directly

**Windows:**
```bash
launch_dashboard.bat
```

**Mac/Linux:**
```bash
chmod +x launch_dashboard.sh
./launch_dashboard.sh
```

### 📖 Complete Guide

For detailed setup instructions, troubleshooting, and VS Code/Cursor configuration:  
**[📘 READ THE COMPLETE SETUP GUIDE →](SETUP_GUIDE.md)**

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Module Guide](#module-guide)
- [Models & Analytics](#models--analytics)
- [Dashboard](#dashboard)
- [Configuration](#configuration)
- [Performance](#performance)
- [Usage Examples](#usage-examples)
- [Contributing](#contributing)

---

## 🎯 Project Overview

**AIRP** is an enterprise-grade platform designed to optimize aviation operations through data-driven insights and predictive analytics. The platform processes real-time and historical flight data to:

- **Detect** operational inefficiencies and anomalies
- **Predict** aircraft maintenance needs before failures occur
- **Score** operational risk across flight operations
- **Optimize** fuel efficiency and performance metrics
- **Monitor** real-time flight operations with alerts

The system integrates with multiple data sources (OpenSky Network, aviation APIs) and provides both analytical models and an interactive dashboard for decision-making.

---

## ✨ Features

### 🔍 Core Analytics
- **Flight Data Ingestion**: Automatic collection from multiple APIs (OpenSky, Aviation Edge, AviationStack)
- **Trajectory Analysis**: 1500+ flight path analysis with optimization metrics
- **Feature Engineering**: 50+ operational features extracted per flight
- **Anomaly Detection**: Real-time detection of unusual flight patterns

### 🤖 Machine Learning Models
1. **Operational Risk Scoring** - Isolation Forest ensemble identifying risk factors
2. **Fuel Inefficiency Detection** - Pinpoints wasteful consumption patterns
3. **Performance Classification** - XGBoost classifier predicting efficiency categories

### 🔧 Predictive Maintenance
- AI-powered maintenance prediction system
- Component failure forecasting
- Maintenance scheduling optimization

### 📡 Real-time Monitoring
- Continuous flight data streaming
- Live dashboard updates
- Automated alert system
- Snapshot archiving for historical analysis

### 📊 Interactive Dashboard
- Multi-page Streamlit application
- Flight search and visualization
- AI assistant integration (Claude)
- Predictive maintenance insights
- Real-time monitoring

---

## 🏗️ Architecture

```
AIRP/
├── 1_data_ingestion/          # Phase 1: Data Collection
│   ├── airport_loader.py      # Airport metadata
│   └── opensky_collector.py   # Flight data collection
│
├── 2_database/                # Phase 2: Data Storage
│   ├── db_setup.py            # PostgreSQL initialization
│   └── schema.sql             # Database schema
│
├── 3_feature_engineering/     # Phase 3: Feature Extraction
│   ├── run_pipeline.py        # Main pipeline
│   ├── trajectory_analyzer.py # Flight path analysis
│   ├── fuel_efficiency_calc.py
│   └── operational_features.py
│
├── 4_models/                  # Phase 4: ML Models
│   ├── train_all_models.py    # Train all models
│   ├── risk_scoring/          # Risk prediction
│   ├── fuel_anomaly/          # Fuel anomalies
│   └── performance_classifier/# Performance prediction
│
├── 6_dashboard/               # Interactive Streamlit App
│   ├── app.py                 # Main dashboard
│   └── pages/                 # Multi-page interface
│
├── 7_advanced_analytics/      # Advanced Features
│   └── predictive_maintenance.py
│
├── 8_realtime_monitoring/     # Real-time Operations
│   ├── realtime_streamer.py
│   └── start_continuous.py
│
├── data/                      # Output data & artifacts
├── config.yaml                # Configuration
└── requirements.txt           # Dependencies
```

---

## 🚀 Installation

### Prerequisites
- **Python 3.8+**
- **PostgreSQL 13+** (or compatible)
- **Git**
- 2GB+ disk space

### Step 1: Clone Repository
```bash
git clone (https://github.com/ishanmakkar651/AIRP-Aviation-Intelligence-Risk-Prediction-Platform.git)
cd AIRP
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Database
Edit `config.yaml` with your PostgreSQL credentials:
```yaml
database:
  host: 127.0.0.1
  port: 5432
  name: aviation_db
  user: your_user
  password: your_password
```

### Step 5: Initialize Database
```bash
python 2_database/db_setup.py
```

### Step 6: Collect Initial Data
```bash
python 1_data_ingestion/airport_loader.py
python 1_data_ingestion/opensky_collector.py
```

---

## ⚡ Quick Start

### 1. Feature Engineering (Phase 2)
Transform raw flight data into ML-ready features:
```bash
cd D:\AIRP
.venv\Scripts\activate
python 3_feature_engineering/run_pipeline.py
```
**Expected Output:** 
- `data/trajectory_features.csv` (25+ columns)
- `data/fuel_efficiency_features.csv` (35+ columns)
- `data/operational_features.csv` (50+ columns)

### 2. Train ML Models (Phase 3)
Train all three models simultaneously:
```bash
python 4_models/train_all_models.py
```
**Expected Results:**
- Risk Scoring: ~5% anomalies detected
- Fuel Inefficiency: ~10% detected as inefficient
- Performance Classification: 85-92% accuracy

### 3. Launch Dashboard
```bash
streamlit run 6_dashboard/app.py
```
Access at `http://localhost:8501`

### 4. Start Real-time Monitoring
```bash
python 8_realtime_monitoring/start_continuous.py
```

---

## 📚 Module Guide

### 1️⃣ Data Ingestion (`1_data_ingestion/`)
Collects flight and airport data from multiple sources.

**Key Files:**
- `airport_loader.py` - Loads airport reference data
- `opensky_collector.py` - Fetches live flight data from OpenSky Network

**Configuration:**
```yaml
apis:
  opensky:
    rate_limit_seconds: 10
    active_region: india  # or north_america, europe
```

### 2️⃣ Database (`2_database/`)
PostgreSQL database setup and management.

**Schema Includes:**
- flights, trajectories, anomalies
- airports, aircraft, airlines
- features, predictions, maintenance logs

**Commands:**
```bash
# Initialize database
python 2_database/db_setup.py

# View schema
cat 2_database/schema.sql
```

### 3️⃣ Feature Engineering (`3_feature_engineering/`)
Extracts 50+ features from raw flight data.

**Pipeline Steps:**
1. Trajectory analysis (flight paths, distances)
2. Fuel efficiency calculation
3. Operational feature extraction
4. Statistical aggregation

**Features Extracted:**
- **Trajectory:** Duration, distance, speed profiles
- **Fuel:** Efficiency scores, stability, route optimization
- **Operational:** Temporal, performance, risk indicators

**Run:**
```bash
python 3_feature_engineering/run_pipeline.py
```

### 4️⃣ Machine Learning Models (`4_models/`)

#### Risk Scoring (`risk_scoring/`)
**Algorithm:** Isolation Forest + Ensemble
**Output:** Risk score (0-100), Risk level (LOW/MEDIUM/HIGH/CRITICAL)
```bash
python 4_models/risk_scoring/train_model.py
```

#### Fuel Anomaly Detection (`fuel_anomaly/`)
**Algorithm:** Isolation Forest
**Output:** Anomaly flag, cause detection
```bash
python 4_models/fuel_anomaly/train_model.py
```

#### Performance Classification (`performance_classifier/`)
**Algorithm:** XGBoost Multi-class Classifier
**Output:** Efficiency category (Excellent/Good/Fair/Poor)
```bash
python 4_models/performance_classifier/train_model.py
```

### 5️⃣ Dashboard (`6_dashboard/`)
Interactive Streamlit multi-page application.

**Pages:**
1. **Flight Search** - Query and visualize flights
2. **AI Assistant** - Claude-powered aviation insights
3. **Predictive Maintenance** - Maintenance forecasting
4. **Real-time Monitoring** - Live operation status

**Run:**
```bash
streamlit run 6_dashboard/app.py
```

### 6️⃣ Advanced Analytics (`7_advanced_analytics/`)
Specialized analysis modules.

**Predictive Maintenance:**
- Component failure prediction
- Maintenance scheduling
- Cost-benefit analysis

```bash
python 7_advanced_analytics/predictive_maintenance.py
```

### 7️⃣ Real-time Monitoring (`8_realtime_monitoring/`)
Continuous flight data monitoring and alerts.

**Features:**
- Real-time streaming
- Snapshot archiving
- Summary statistics
- Alert generation

```bash
python 8_realtime_monitoring/start_continuous.py
```

---

## 🤖 Models & Analytics

### Model Performance

Based on 13,395 flight records / 2,970 trajectories:

| Model | Algorithm | Accuracy/Detection | Key Metric |
|-------|-----------|-------------------|-----------|
| Risk Scoring | Isolation Forest | 95% anomaly detection | Risk scores 0-100 |
| Fuel Anomaly | Isolation Forest | 90% detection rate | 10% flagged inefficient |
| Performance Classifier | XGBoost | 85-92% accuracy | 4-class classification |

### Feature Importance

**Top Performance Indicators:**
1. Altitude stability
2. Speed consistency  
3. Route efficiency
4. Climb rates
5. Temporal patterns (hour/day)

### Output Data

All models save:
- `*.pkl` - Trained model files
- `model_info.json` - Metadata (accuracy, training date)
- `scaler.pkl` - Feature normalization
- `visualizations/` - Charts and analysis plots

---

## 📊 Dashboard

### Access Points
```
Main: http://localhost:8501
APIs: Configured in config.yaml
Data: data/ directory
Models: 4_models/ directory
```

### Pages Overview

**1. Flight Search** 🔍
- Search by flight number, route, date
- Visualization of flight paths
- Performance metrics display

**2. AI Assistant** 🤖
- Claude AI integration
- Natural language aviation queries
- Insight generation and recommendations

**3. Predictive Maintenance** 🔧
- Component status predictions
- Maintenance scheduling
- Cost optimization

**4. Real-time Monitoring** 📡
- Live flight data
- Active alerts
- Anomaly detection

---

## ⚙️ Configuration

### Database Setup (`config.yaml`)
```yaml
database:
  host: 127.0.0.1
  port: 5434
  name: aviation_db
  user: airp_user
  password: your_password
```

### API Configuration
```yaml
apis:
  opensky:
    rate_limit_seconds: 10
    active_region: india
  
  aviation_edge:
    api_key: YOUR_KEY
    base_url: https://aviation-edge.com/v2/public
```

### Data Collection
```yaml
collection:
  flight_interval: 10        # minutes
  weather_interval: 30       # minutes
  retention_days: 90
```

---

## 📦 Dependencies

### Core
- pyyaml, python-dotenv
- psycopg2-binary (PostgreSQL)

### Data Processing
- pandas, numpy, requests

### ML & Models
- scikit-learn, xgboost, imbalanced-learn

### Visualization & Dashboard
- streamlit, plotly, matplotlib, seaborn

### LLM Integration
- anthropic (Claude API)

### Testing
- pytest, pytest-cov

See `requirements.txt` for complete list with versions.

---

## 🧪 Testing

Run test suite:
```bash
pytest tests/ -v
pytest tests/ --cov=.

# Specific module test
python 7_advanced_analytics/test_maintenance.py
```

---

## 📈 Usage Examples

### Example 1: Query Risk Scores
```python
import pandas as pd
from 4_models.risk_scoring.train_model import predict_risk

df = pd.read_csv('data/operational_features.csv')
risk_scores = predict_risk(df)
print(risk_scores.describe())
```

### Example 2: Detect Fuel Anomalies
```python
from 4_models.fuel_anomaly.train_model import detect_anomalies

anomalies = detect_anomalies(df)
print(f"Found {len(anomalies)} inefficient flights")
```

### Example 3: Real-time Monitoring
```bash
# Continuous data collection and monitoring
python 8_realtime_monitoring/start_continuous.py

# View latest snapshot
cat data/realtime/latest_snapshot.json
```

---

## 🔄 Workflow

### Recommended Execution Order
1. **Setup** → Install & configure database
2. **Ingest** → Collect flight data (Phase 1)
3. **Engineer** → Extract features (Phase 2)
4. **Train** → Build ML models (Phase 3)
5. **Deploy** → Launch dashboard (Phase 4)
6. **Monitor** → Start real-time streaming (Phase 5)

### Data Flow
```
OpenSky API / Aviation APIs
         ↓
    PostgreSQL Database
         ↓
Feature Engineering Pipeline
         ↓
ML Models Training
         ↓
Predictions & Insights
         ↓
Dashboard & Real-time Alerts
```

---

## 📝 Key Outputs

### Data Files (`data/`)
- `trajectory_features.csv` - Flight path features
- `fuel_efficiency_features.csv` - Fuel metrics
- `operational_features.csv` - All features (ML-ready)
- `risk_scores.csv` - Risk predictions
- `fuel_anomalies.csv` - Anomaly detection results
- `maintenance_predictions.csv` - Maintenance forecasts
- `realtime/` - Streaming snapshots

### Model Files (`4_models/`)
```
4_models/
├── risk_scoring/
│   ├── model_info.json
│   ├── risk_model.pkl
│   └── visualizations/
├── fuel_anomaly/
│   ├── model_info.json
│   ├── fuel_model.pkl
│   └── visualizations/
└── performance_classifier/
    ├── model_info.json
    ├── classifier_model.pkl
    └── feature_importance.csv
```

---

## ⚡ Performance

### Performance Optimizations ✅

This platform includes comprehensive performance optimizations:

- **Database Indexes**: 10-100x faster time-series queries
- **Connection Pooling**: Prevents connection exhaustion
- **Vectorized Calculations**: 5-20x speedup for computations
- **Batch Operations**: 100x faster database inserts
- **Memory Optimization**: 50% reduced memory usage

### Performance Benchmarks

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Time-series query (10K rows) | 5.0s | 0.05s | **100x faster** |
| Trajectory distance calc (1K points) | 2.0s | 0.2s | **10x faster** |
| Risk scoring (1K flights) | 3.0s | 0.15s | **20x faster** |
| Aircraft batch insert (1K aircraft) | 10.0s | 0.1s | **100x faster** |
| Feature engineering memory | 20GB | 10GB | **50% reduction** |

**📊 Full Details:** [PERFORMANCE_IMPROVEMENTS.md](PERFORMANCE_IMPROVEMENTS.md)

---

## 🚨 Troubleshooting

### PostgreSQL Connection Error
```bash
# Check PostgreSQL service
psql -U your_user -h localhost -d aviation_db

# Reset config.yaml with correct credentials
```

### Missing Data Files
```bash
# Re-run feature engineering
python 3_feature_engineering/run_pipeline.py

# Check data directory
ls -la data/
```

### Model Training Issues
```bash
# Verify features exist
python -c "import pandas as pd; pd.read_csv('data/operational_features.csv')"

# Retrain individual model
python 4_models/risk_scoring/train_model.py -v
```

### Dashboard Connection Issues
```bash
# Check port availability
lsof -i :8501  # or: netstat -ano | findstr :8501

# Try alternate port
streamlit run 6_dashboard/app.py --server.port 8502
```

---

## 📚 Documentation

- **[Complete Setup Guide](SETUP_GUIDE.md)** - Detailed instructions for VS Code/Cursor
- **[Performance Improvements](PERFORMANCE_IMPROVEMENTS.md)** - Optimization details
- **[Phase 3 ML Models](PHASE3_QUICKSTART.md)** - ML model documentation
- **[Phase 2 Features](Readme2.md)** - Feature engineering guide
- **[Database Schema](2_database/schema.sql)** - Database structure
- **[Configuration](config.yaml)** - System configuration

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Make changes and add tests
4. Submit pull request

---

## 📄 License

MIT License - See LICENSE file for details

---

## 👥 Author

**Aviation Intelligence & Risk Prediction Platform Team**

---

## 🔗 Resources

- **OpenSky Network:** https://opensky-network.org/
- **Streamlit Docs:** https://streamlit.io/
- **XGBoost Docs:** https://xgboost.readthedocs.io/
- **Anthropic Claude:** https://www.anthropic.com/
- **PostgreSQL Docs:** https://www.postgresql.org/docs/

---

## 📞 Support

For issues, questions, or suggestions:
- Create an issue on GitHub
- Check existing documentation in PHASE3_QUICKSTART.md and Readme2.md
- Review config.yaml for configuration help

---

**Happy Flying! ✈️**

Last Updated: January 3, 2026
