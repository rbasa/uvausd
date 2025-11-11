# UVA Analysis - Quick Setup Guide

## 🎯 What This Repository Does

Analyzes the **UVA (Unidad de Valor Adquisitivo)** index measured in different USD exchange rates in Argentina.

**Data Sources:**
- UVA: [Argentina Datos API](https://api.argentinadatos.com)
- USD rates: [Ambito.com](https://mercados.ambito.com)
- **Data Storage**: [DoltHub](https://www.dolthub.com/repositories/rbasa/macroeconomia)

## 📊 Repository Structure

```
uva/
├── README.md                    # Main documentation
├── SETUP.md                     # This file - quick start
├── AUTOMATION_SETUP.md          # GitHub Actions setup (optional)
├── DOLTHUB_CREDENTIALS_GUIDE.md # DoltHub credentials (for automation)
│
├── uva_analisis.ipynb           # 📊 Main analysis notebook
├── requirements.txt             # Python dependencies
│
├── etl/                         # ETL Scripts
│   ├── populate_usd_uva.py      # Full historical ETL
│   ├── daily_update.py          # Incremental daily ETL
│   ├── run_etl_and_push.sh      # Wrapper script (ETL + Git)
│   └── utils/                   # Shared utilities
│       ├── fetch_usd_data.py    # Fetch USD rates
│       ├── fetch_uva.py         # Fetch UVA data
│       ├── db_manager.py        # Database manager
│       └── utils.py             # Data transformation
│
├── data/
│   └── tables.sql               # Database schema
│
└── .github/workflows/
    └── daily_etl.yml            # Automated daily updates
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Option A: Use DoltHub Data (Easiest)

Just open the notebook and run it - data loads from DoltHub API automatically:

```bash
jupyter notebook uva_analisis.ipynb
```

### 2. Option B: Run Local ETL

If you want to fetch fresh data or contribute updates:

```bash
# Start Dolt SQL server (in your Dolt database directory)
cd /path/to/macroeconomia
dolt sql-server

# In another terminal, run ETL
cd /path/to/uva
source .venv/bin/activate
python etl/populate_usd_uva.py

# Commit and push changes
dolt add fx_rate
dolt commit -m "Update data"
dolt push origin main
```

## 🤖 Automated Daily Updates (Optional)

To set up automated daily data updates via GitHub Actions:

1. Follow **AUTOMATION_SETUP.md**
2. Generate DoltHub credentials
3. Add secrets to GitHub
4. Push to GitHub - done!

## 📚 Documentation Files

| File | Purpose | When to Read |
|------|---------|--------------|
| `README.md` | Project overview | Start here |
| `SETUP.md` | Quick start guide | First time setup |
| `AUTOMATION_SETUP.md` | GitHub Actions setup | If you want automated updates |
| `DOLTHUB_CREDENTIALS_GUIDE.md` | DoltHub auth | When setting up automation |
| `ARCHITECTURE.md` | Technical deep dive | For contributors |
| `etl/README.md` | ETL scripts docs | When running/modifying ETL |

## ✅ Essential Files for GitHub

**Must commit:**
- ✅ `README.md`
- ✅ `requirements.txt`
- ✅ `uva_analisis.ipynb`
- ✅ `etl/` directory (all scripts)
- ✅ `data/tables.sql`
- ✅ `.github/workflows/daily_etl.yml`
- ✅ `.gitignore`

**Optional (documentation):**
- `SETUP.md` (this file)
- `AUTOMATION_SETUP.md` (if using GitHub Actions)
- `DOLTHUB_CREDENTIALS_GUIDE.md` (if using GitHub Actions)
- `ARCHITECTURE.md` (for technical details)

**Don't commit:**
- ❌ `.venv/` (virtual environment)
- ❌ `__pycache__/` (Python cache)
- ❌ `*.html` (notebook exports)
- ❌ `config.yaml` (may contain secrets)
- ❌ `dolt_db/` (Dolt working directory)

## 🔐 Before Pushing to GitHub

```bash
# 1. Check what will be committed
git status

# 2. Make sure no secrets are included
git diff

# 3. Verify .gitignore is working
git check-ignore -v .venv/ config.yaml

# 4. Push
git add .
git commit -m "Initial commit"
git push
```

## 🌟 That's It!

For most users:
- Just use the notebook with DoltHub data
- No ETL setup needed
- Data updates automatically via GitHub Actions

For contributors:
- Follow AUTOMATION_SETUP.md to set up GitHub Actions
- Run local ETL to test changes

