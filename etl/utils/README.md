# Utils Module

Shared utilities for ETL scripts.

## 📁 Structure

```
utils/
├── __init__.py          # Defines the package (enables imports)
├── utils.py             # Shared functions
├── db_manager.py        # Database connection and operations manager
├── fetch_usd_data.py    # Script to fetch USD data
├── fetch_uva.py         # Script to fetch UVA data
└── README.md            # This file
```

## 🤔 What is `__init__.py`?

It's a special file that tells Python: **"this folder is a Python package"**.

**Without `__init__.py`:**
```python
# ❌ This fails
from etl.utils import try_fetch
```

**With `__init__.py`:**
```python
# ✅ This works
from etl.utils import try_fetch, parse_number, DoltDBManager
from etl.utils.fetch_usd_data import fetch_ambito_dolar
```

## 🚀 How to Use

### Run as module

All scripts in this package use relative imports and must be run as modules:

```bash
cd /Users/user/uva
source .venv/bin/activate

# Run USD data fetcher
python -m etl.utils.fetch_usd_data

# Run UVA data fetcher
python -m etl.utils.fetch_uva
```

### Import in another script

```python
from etl.utils import try_fetch, parse_number, DoltDBManager
from etl.utils.fetch_usd_data import fetch_ambito_dolar
from etl.utils.fetch_uva import fetch_uva_data

# Fetch data (returns standardized format)
uva_data = fetch_uva_data()  # [{'date': 'YYYY-MM-DD', 'rate': float}, ...]
usd_data = fetch_ambito_dolar('formal', '2024-01-01', '2024-12-31')

# Use utilities
response = try_fetch('https://api.example.com/data')
price = parse_number('1.326,49')  # → 1326.49
```

## 📚 Available Functions

### `try_fetch(url, headers=None)`
Wrapper for `requests.get()` with error handling.

```python
from etl.utils import try_fetch

resp = try_fetch('https://api.example.com/data', headers={'User-Agent': 'Bot'})
if isinstance(resp, Exception):
    print(f"Error: {resp}")
else:
    print(f"Status: {resp.status_code}")
```

### `parse_number(val)`
Converts Argentine format strings to float.

```python
from etl.utils import parse_number

parse_number('1.326,49')  # → 1326.49
parse_number('92.020,50') # → 92020.5
parse_number(None)         # → None
```

### `parse_ambito_response(data)`
Parses Ambito API response (list of lists format).

```python
from etl.utils import parse_ambito_response

raw_data = [['Fecha', 'Compra', 'Venta'], ['26/08/2024', '928,31', '987,34']]
parsed = parse_ambito_response(raw_data)
# → [{'fecha': '26/08/2024', 'compra': '928,31', 'venta': '987,34'}]
```

### `DoltDBManager`
Manages database connections and Dolt operations.

```python
from etl.utils import DoltDBManager
import os

os.environ['DOLT_DB'] = 'mysql://user:@localhost:3306/macroeconomia'
db = DoltDBManager()
db.connect()

# Execute queries
result = db.query("SELECT * FROM fx_rate LIMIT 10")

# Dolt operations
db.dolt_pull()
db.dolt_add('fx_rate')
db.dolt_commit('Update fx_rate')
db.dolt_push()

# Insert data
db.insert_fx_rate(date='2024-08-26', kind='UVA', pair='UVA_ARS', rate=1565.43)

db.disconnect()
```

### `fetch_ambito_dolar(kind, start_date, end_date)`
Fetches historical USD data from Ambito.com.

```python
from etl.utils.fetch_usd_data import fetch_ambito_dolar

# Valid types: 'formal', 'mep', 'informal', 'cripto'
data = fetch_ambito_dolar('formal', '2024-08-01', '2024-08-31')
print(data)  # List of lists with format: [['Fecha', 'Compra', 'Venta'], ...]
```

### `fetch_uva_data()`
Fetches UVA historical data from Argentina Datos API.

```python
from etl.utils.fetch_uva import fetch_uva_data

data = fetch_uva_data()
# → [{'fecha': '2016-03-31', 'valor': 14.05}, ...]
```

## ⚡ Quick Summary

- **`__init__.py`** = Makes the folder a Python package
- **`utils.py`** = Shared functions everyone can use
- **`db_manager.py`** = Database connection and operations
- **`fetch_usd_data.py`** = Specific script to fetch USD data
- **`fetch_uva.py`** = Specific script to fetch UVA data
- **Execute**: `python -m etl.utils.fetch_usd_data`
- **Import**: `from etl.utils import try_fetch, parse_number, DoltDBManager`
