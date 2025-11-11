import requests
import pandas as pd
from urllib.parse import urlencode
from datetime import datetime, timedelta


def parse_number(val):
    """Converts Argentine format string to float"""
    if pd.isna(val) or val == "":
        return None
    try:
        # Replace dot (thousands separator) and comma (decimal)
        return float(str(val).replace(".", "").replace(",", "."))
    except:
        return None

def try_fetch(url, headers=None):
    """Attempts HTTP GET request to URL"""
    try:
        resp = requests.get(url, headers=headers or {}, timeout=30)
        return resp
    except Exception as e:
        return e


# Headers to simulate a browser
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Referer": "https://www.ambito.com/"
}

def parse_ambito_response(data):
    """
    Parses Ambito response which comes as list of lists:
    [['Fecha', 'Compra', 'Venta'], ['25/08/2025', '1326,49', '1367,98'], ...]
    
    Returns:
        List of dictionaries with {fecha, compra, venta}
    """
    if not isinstance(data, list) or len(data) < 2:
        return []
    
    # First row is header, rest is data
    rows = []
    for item in data[1:]:  # Skip header
        if isinstance(item, list) and len(item) >= 3:
            fecha_str, compra_str, venta_str = item[0], item[1], item[2]
            rows.append({
                "fecha": fecha_str,
                "compra": compra_str,
                "venta": venta_str
            })
    return rows
# Import data from DoltHub API
# https://www.dolthub.com/repositories/rbasa/macroeconomia

def fetch_dolthub_data(sql_query):
    """
    Fetches data from DoltHub API and returns a pandas DataFrame
    
    Args:
        sql_query: SQL query to execute
        
    Returns:
        pandas DataFrame with the results
    """
    # DoltHub repository configuration
    DOLTHUB_OWNER = "rbasa"
    DOLTHUB_REPO = "macroeconomia"
    DOLTHUB_BRANCH = "main"

    base_url = f"https://www.dolthub.com/api/v1alpha1/{DOLTHUB_OWNER}/{DOLTHUB_REPO}/{DOLTHUB_BRANCH}"
    params = {"q": sql_query}
    url = f"{base_url}?{urlencode(params)}"
    
    response = requests.get(url)
    response.raise_for_status()
    
    data = response.json()
    
    # Convert to DataFrame
    df = pd.DataFrame(data['rows'])
    
    # Convert columns to appropriate types based on schema
    if 'DATE' in df.columns:
        df['DATE'] = pd.to_datetime(df['DATE'])
    
    if 'rate' in df.columns:
        df['rate'] = pd.to_numeric(df['rate'], errors='coerce')
    
    # Convert any other numeric-looking columns
    for col in df.columns:
        if col not in ['DATE', 'pair', 'kind']:
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except:
                pass
    
    return df


def transform_fx_data_to_wide(df_raw):
    """
    Transforms fx_rate data from LONG format (multiple rows per date) 
    to WIDE format (1 row per date with all pairs as columns)
    
    Args:
        df_raw: DataFrame with columns: DATE, pair, kind, rate
                (output from fetch_all_data_paginated or SQL query)
    
    Returns:
        DataFrame with columns: fecha, uva, usd, usdb, usdm, usdc, 
                                uva_usd, uva_usdb, uva_usdm, uva_usdc
    
    Example:
        >>> df_raw = fetch_all_data_paginated(['UVA_ARS', 'USD_ARS', 'USDB_ARS'])
        >>> df = transform_fx_data_to_wide(df_raw)
        >>> print(df.columns)
        ['fecha', 'uva', 'usd', 'usdb', 'uva_usd', 'uva_usdb']
    """
    # ============================================================================
    # Transform df_raw (LONG format) → df (WIDE format)
    # ============================================================================
    # Goal: 1 row per date with columns: fecha, uva, usd, usdb, usdm, usdc, ratios
    # ============================================================================

    
    if len(df_raw) == 0:
        print("⚠️  Empty input data")
        return pd.DataFrame()
    
    print("🔄 Transforming data from LONG to WIDE format...")
    print(f"   Input (df_raw): {len(df_raw):,} rows (multiple per date)")
    
    # Step 1: Extract UVA (already 1 row per date, kind='index')
    df_uva = df_raw[df_raw['pair'] == 'UVA_ARS'][['DATE', 'rate']].copy()
    df_uva = df_uva.rename(columns={'DATE': 'fecha', 'rate': 'uva'})
    
    # Step 2: For USD pairs, calculate mid-point (average of bid/ask)
    usd_pairs = ['USD_ARS', 'USDB_ARS', 'USDM_ARS', 'USDC_ARS']
    df_usd = df_raw[df_raw['pair'].isin(usd_pairs)].copy()
    
    # Calculate mid-point for each pair and date
    df_usd_mid = df_usd.groupby(['DATE', 'pair'])['rate'].mean().reset_index()
    
    # Step 3: Pivot to wide format (each pair becomes a column)
    df_usd_wide = df_usd_mid.pivot(index='DATE', columns='pair', values='rate').reset_index()
    df_usd_wide = df_usd_wide.rename(columns={'DATE': 'fecha'})
    
    # Rename columns to simpler names
    column_mapping = {
        'USD_ARS': 'usd',
        'USDB_ARS': 'usdb',
        'USDM_ARS': 'usdm',
        'USDC_ARS': 'usdc'
    }
    df_usd_wide = df_usd_wide.rename(columns=column_mapping)
    
    # Step 4: Merge UVA + USD data
    df = df_uva.merge(df_usd_wide, on='fecha', how='inner')
    
    # Step 5: Calculate UVA in USD (ratios)
    # Only calculate if the USD column exists
    if 'usd' in df.columns:
        df['uva_usd'] = df['uva'] / df['usd']
    if 'usdb' in df.columns:
        df['uva_usdb'] = df['uva'] / df['usdb']
    if 'usdm' in df.columns:
        df['uva_usdm'] = df['uva'] / df['usdm']
    if 'usdc' in df.columns:
        df['uva_usdc'] = df['uva'] / df['usdc']
    
    # Step 6: Sort by date
    df = df.sort_values('fecha').reset_index(drop=True)
    
    print(f"\n✅ Transformation complete!")
    print(f"   Output: {len(df):,} rows (1 per date)")
    print(f"   Date range: {df['fecha'].min()} to {df['fecha'].max()}")
    print(f"   Columns: {', '.join(df.columns)}")
    
    return df


def fetch_all_data_paginated(pairs, start_date='2016-03-31', end_date=None, chunk_months=12):
    """
    Fetches all data by paginating through date ranges
    
    Args:
        pairs: List of currency pairs to fetch
        start_date: Start date (default: UVA inception date)
        end_date: End date (default: today)
        chunk_months: Number of months per chunk (default: 12)
        
    Returns:
        Complete DataFrame with all data
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    all_chunks = []
    current = start
    
    print(f"📊 Fetching data in chunks from {start_date} to {end_date}...")
    
    while current < end:
        # Calculate chunk end date
        chunk_end = current + pd.DateOffset(months=chunk_months)
        if chunk_end > end:
            chunk_end = end
        
        # Build query for this chunk
        pairs_str = "', '".join(pairs)
        query = f"""
        SELECT DATE, pair, kind, rate
        FROM fx_rate
        WHERE pair IN ('{pairs_str}')
          AND DATE >= '{current.strftime('%Y-%m-%d')}'
          AND DATE < '{chunk_end.strftime('%Y-%m-%d')}'
        ORDER BY DATE ASC, pair ASC
        """
        
        try:
            chunk_df = fetch_dolthub_data(query)
            if len(chunk_df) > 0:
                all_chunks.append(chunk_df)
            else:
                print(f"   ⚠️  {current.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}: No data")
        except Exception as e:
            print(f"   ❌ {current.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}: Error - {e}")
        
        current = chunk_end
    
    if all_chunks:
        result = pd.concat(all_chunks, ignore_index=True)
        print(f"\n✅ Total records fetched: {len(result):,}")
        return result
    else:
        print("\n❌ No data fetched")
        return pd.DataFrame()

