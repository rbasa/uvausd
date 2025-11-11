# ETL Scripts

ETL scripts to populate the Dolt database with Argentine financial data.

## 📁 Structure

```
etl/
├── populate_usd_uva.py      # Main ETL script for USD and UVA data
├── populate_cer_historical.py  # CER historical data loader
├── fix_schema.py            # Schema maintenance utility
├── fix_primary_key.py       # Primary key fix utility
└── utils/                   # Shared modules
    ├── __init__.py
    ├── utils.py             # Common utilities (parse_number, try_fetch, etc.)
    ├── db_manager.py        # Database connection manager (DoltDBManager)
    ├── fetch_usd_data.py    # USD data fetcher from Ambito.com
    ├── fetch_uva.py         # UVA data fetcher from Argentina Datos API
    └── README.md
```

## 🚀 Quick Start

### Prerequisites

1. **Start Dolt SQL Server**:
```bash
cd data
dolt sql-server
```

2. **Activate virtual environment**:
```bash
cd /Users/user/uva
source .venv/bin/activate
```

### Run the ETL

```bash
# The script uses default connection if DOLT_DB is not set
python etl/populate_usd_uva.py

# Or set custom connection string
export DOLT_DB='mysql://user:@localhost:3306/macroeconomia'
python etl/populate_usd_uva.py
```

## 📊 What the ETL Does

### 1. **Fetches UVA Data**
- Source: Argentina Datos API
- Returns: `[{'date': 'YYYY-MM-DD', 'rate': float}, ...]`
- ~3,500 records from 2016 to present

### 2. **Fetches USD Data (4 types)**
- Source: Ambito.com API
- Types:
  - `formal` → USD_OFICIAL (Official Dollar)
  - `mep` → USD_MEP (Electronic Payment Market)
  - `informal` → USD_BLUE (Blue/Informal Dollar)
  - `cripto` → USD_CRIPTO (Crypto Dollar)
- Returns: `[{'date': 'YYYY-MM-DD', 'rate': float}, ...]`
- ~6,000 records per type from 2002 to present

### 3. **Inserts into Database**
- Table: `fx_rate`
- Columns: `DATE, kind, pair, rate`
- Uses `INSERT IGNORE` to avoid duplicates
- Excludes today's data (incomplete)

## 🔧 Module Architecture

### Clean Separation of Concerns

```
fetch_uva.py          →  Returns standardized data: [{'date': 'YYYY-MM-DD', 'rate': float}]
fetch_usd_data.py     →  Returns standardized data: [{'date': 'YYYY-MM-DD', 'rate': float}]
db_manager.py         →  Handles all database operations
populate_usd_uva.py   →  Orchestrates: fetch → insert → complete
```

### Data Flow

```
1. fetch_uva_data()
   ↓
   [{'date': '2024-08-26', 'rate': 1565.43}]
   ↓
2. run_kind('UVA', data, db, pair='UVA_ARS')
   ↓
3. db.insert_fx_rate(date='2024-08-26', kind='UVA', pair='UVA_ARS', rate=1565.43)
   ↓
4. INSERT IGNORE INTO fx_rate (DATE, kind, pair, rate) VALUES (...)
```

## 📚 Usage Examples

### Fetch and Display Data

```python
from etl.utils.fetch_uva import fetch_uva_data
from etl.utils.fetch_usd_data import fetch_ambito_dolar

# Fetch UVA
uva = fetch_uva_data()
print(f"UVA records: {len(uva)}")
print(f"Latest: {uva[-1]}")

# Fetch USD Blue
blue = fetch_ambito_dolar('informal', '2024-01-01', '2024-12-31')
print(f"USD Blue records: {len(blue)}")
print(f"Latest: {blue[-1]}")
```

### Direct Database Operations

```python
from etl.utils import DoltDBManager
import os

os.environ['DOLT_DB'] = 'mysql://user:@localhost:3306/macroeconomia'
db = DoltDBManager()
db.connect()

# Query data
uva_recent = db.query("""
    SELECT * FROM fx_rate 
    WHERE kind='UVA' 
    ORDER BY DATE DESC 
    LIMIT 10
""")

# Insert single record
db.insert_fx_rate(
    date='2024-08-26',
    kind='UVA',
    pair='UVA_ARS',
    rate=1565.43
)

db.disconnect()
```

## 🛠️ Maintenance Scripts

### Fix Schema Issues

```bash
python etl/fix_schema.py
```

### Fix Primary Key

```bash
python etl/fix_primary_key.py
```

## 📈 Expected Results

After running `populate_usd_uva.py`:

```
USD_BLUE       | USDB_ARS   |  ~5,900 records | 2002-01-11 → present
USD_CRIPTO     | USDC_ARS   |  ~5,800 records | 2002-04-09 → present
USD_MEP        | USDM_ARS   |  ~5,800 records | 2002-04-09 → present
USD_OFICIAL    | USD_ARS    |  ~5,800 records | 2002-04-09 → present
UVA            | UVA_ARS    |  ~3,500 records | 2016-03-31 → present

TOTAL: ~27,000 records
```

## 🔑 Key Features

- ✅ **Modular design**: Each module has a single responsibility
- ✅ **Standardized output**: All fetch functions return the same format
- ✅ **Clean code**: No redundant conversions in main ETL
- ✅ **Error handling**: Comprehensive error messages
- ✅ **Duplicate prevention**: Uses `INSERT IGNORE`
- ✅ **Progress tracking**: Shows progress every 500 records
- ✅ **Debug mode**: Shows first 3 insertions for verification

## 🐛 Troubleshooting

### Connection Refused

Make sure Dolt SQL server is running:
```bash
cd data
dolt sql-server
```

### Import Errors

Activate the virtual environment:
```bash
source .venv/bin/activate
```

### No Data Inserted

Check that:
1. Table schema is correct (`DECIMAL(15,6)` for rate)
2. Primary key is `(DATE, pair, kind)`
3. Currency pairs exist in `pair` table


