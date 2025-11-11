# Project Architecture

This document describes the architecture and design decisions for the Argentine Financial Data ETL system.

## 📐 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                             │
├─────────────────────────────────────────────────────────────┤
│  • Argentina Datos API (UVA)                               │
│  • Ambito.com API (USD Official, MEP, Blue, Crypto)        │
│  • BCRA (CER - future)                                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    ETL LAYER                                │
├─────────────────────────────────────────────────────────────┤
│  fetch_uva.py        →  Fetch + Transform UVA data        │
│  fetch_usd_data.py   →  Fetch + Transform USD data        │
│  populate_usd_uva.py →  Orchestrate ETL process           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  DATABASE LAYER                             │
├─────────────────────────────────────────────────────────────┤
│  db_manager.py       →  Connection + Operations            │
│  DoltDBManager       →  query(), insert_fx_rate(), etc.    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   DOLT DATABASE                             │
├─────────────────────────────────────────────────────────────┤
│  Table: fx_rate                                            │
│  ├─ DATE (date)           - Primary Key                    │
│  ├─ pair (varchar)        - Primary Key                    │
│  ├─ kind (varchar)        - Primary Key                    │
│  └─ rate (decimal)        - Exchange rate value            │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Design Principles

### 1. **Single Responsibility**
Each module has one clear purpose:
- `fetch_*.py` → Fetch and transform data from external APIs
- `db_manager.py` → Database operations only
- `populate_*.py` → Orchestration only

### 2. **Standardized Data Format**
All fetch functions return the same structure:
```python
[
    {'date': 'YYYY-MM-DD', 'rate': float},
    {'date': 'YYYY-MM-DD', 'rate': float},
    ...
]
```

### 3. **Separation of Concerns**
- **Data Fetching** (utils/) → Independent, reusable modules
- **Data Transformation** (in fetch modules) → Done at source
- **Data Loading** (populate scripts) → Simple orchestration

### 4. **Normalized Database Schema**

Instead of this (BAD):
```sql
CREATE TABLE prices (
    DATE date,
    uva decimal,
    dolar_oficial decimal,
    dolar_blue decimal,
    ...  -- Adding metrics requires ALTER TABLE
);
```

We use this (GOOD):
```sql
CREATE TABLE fx_rate (
    DATE date,
    kind varchar,    -- UVA, USD_OFICIAL, USD_BLUE, etc.
    pair varchar,    -- UVA_ARS, USD_ARS, USDB_ARS, etc.
    rate decimal,
    PRIMARY KEY (DATE, pair, kind)
);
```

**Benefits:**
- ✅ Adding new metrics = just insert new rows
- ✅ Easy queries across metrics
- ✅ No schema changes needed
- ✅ Efficient storage

## 📊 Data Model

### Currency Pairs

| Pair | Description |
|------|-------------|
| `USD_ARS` | Official Dollar in Argentine Pesos |
| `USDM_ARS` | MEP Dollar in Argentine Pesos |
| `USDB_ARS` | Blue Dollar in Argentine Pesos |
| `USDC_ARS` | Crypto Dollar in Argentine Pesos |
| `UVA_ARS` | UVA Index in Argentine Pesos |

### Data Types (kind)

| Kind | Description | Pair | Records |
|------|-------------|------|---------|
| `USD_OFICIAL` | Official Dollar | `USD_ARS` | ~5,800 |
| `USD_MEP` | MEP Dollar | `USDM_ARS` | ~5,800 |
| `USD_BLUE` | Blue Dollar | `USDB_ARS` | ~6,000 |
| `USD_CRIPTO` | Crypto Dollar | `USDC_ARS` | ~5,800 |
| `UVA` | UVA Index | `UVA_ARS` | ~3,500 |

## 🔄 ETL Workflow

### JavaScript ETL Pattern (Original)
```javascript
async function runSymbol(symbol, dataJson, db_pool) {
    const pull_res = await queryPromise(db_pool, `call dolt_pull(...)`)
    const insert_res = await Promise.allSettled(
        dataJson.map(arr => queryPromise(db_pool, `insert ignore...`))
    )
    const add_res = await queryPromise(db_pool, `call dolt_add(...)`)
    const commit_res = await queryPromise(db_pool, `call dolt_commit(...)`)
    const push_res = await queryPromise(db_pool, `call dolt_push(...)`)
}
```

### Python ETL Pattern (Our Implementation)
```python
def run_kind(kind, data_rows, db, pair):
    # pull_res = db.dolt_pull()
    
    for dp in filtered_data:
        result = db.insert_fx_rate(
            date=dp['date'],
            kind=kind,
            pair=pair,
            rate=dp['rate']
        )
    
    # add_res = db.dolt_add('fx_rate')
    # commit_res = db.dolt_commit(message)
    # push_res = db.dolt_push()
```

## 🛠️ Technical Stack

- **Python**: 3.12+
- **Database**: Dolt (MySQL-compatible + version control)
- **Connection**: PyMySQL (Unix socket for local, TCP for remote)
- **Data Processing**: Pandas
- **HTTP Requests**: requests library

## 🔐 Connection Methods

### Unix Socket (Local - Default)
```python
pymysql.connect(unix_socket='/tmp/mysql.sock', ...)
```
- ✅ Faster
- ✅ No authentication issues
- ✅ Used when Dolt server is on same machine

### TCP (Remote - Fallback)
```python
pymysql.connect(host='localhost', port=3306, ...)
```
- ✅ Works for remote connections
- ⚠️ May require authentication setup

## 📝 Code Quality Standards

### All Code is in English
- Comments
- Docstrings
- Variable names
- Error messages
- Documentation

### Function Documentation
Every function includes:
- Purpose description
- Args with types and descriptions
- Returns with format specification
- Usage examples

### Error Handling
- Comprehensive try/except blocks
- Clear error messages
- Graceful degradation
- Connection cleanup in finally blocks

## 🚀 Future Enhancements

### Potential Additions:
1. **Derived Metrics**: UVA_BLUE, UVA_MEP (UVA in different dollars)
2. **CER Data**: Full historical CER from BCRA
3. **Dolt Operations**: Uncomment pull/push for version control
4. **Scheduling**: Run ETL daily via cron/systemd
5. **Metrics Table**: Metadata about each kind/pair
6. **Data Validation**: Check for anomalies before insert
7. **Logging**: Structured logging to files

## 📊 Query Examples

### Compare UVA vs Blue Dollar
```sql
SELECT 
    uva.DATE,
    uva.rate as uva_rate,
    blue.rate as blue_rate,
    (uva.rate / blue.rate) as uva_in_blue_dollars
FROM fx_rate uva
JOIN fx_rate blue ON uva.DATE = blue.DATE
WHERE uva.kind = 'UVA' 
  AND blue.kind = 'USD_BLUE'
  AND uva.DATE >= '2024-01-01'
ORDER BY uva.DATE DESC;
```

### All Metrics for a Date
```sql
SELECT * FROM fx_rate 
WHERE DATE = '2025-11-05'
ORDER BY kind;
```

### Latest Value for Each Metric
```sql
SELECT kind, pair, MAX(DATE) as latest_date, 
       (SELECT rate FROM fx_rate f2 
        WHERE f2.kind = f1.kind AND f2.DATE = MAX(f1.DATE)) as latest_rate
FROM fx_rate f1
GROUP BY kind, pair;
```

---

**Last Updated**: 2025-11-10  
**Version**: 1.0  
**Status**: Production Ready ✅


