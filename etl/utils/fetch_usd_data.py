#!/usr/bin/env python3
"""
Script to fetch USD exchange rate data from Ambito.com
Supports: formal (official), mep, informal (blue), cripto (crypto)

To run:
    python -m etl.utils.fetch_usd_data
"""

import pandas as pd
from .utils import try_fetch, BROWSER_HEADERS, parse_ambito_response, parse_number

def fetch_ambito_dolar(kind, start_date, end_date):
    """
    Fetches historical USD exchange rate data from Ambito.com
    
    Args:
        kind: Dollar type - must be exactly one of these values:
              'formal'    = Official Dollar
              'mep'       = MEP Dollar (Electronic Payment Market)
              'informal'  = Blue Dollar
              'cripto'    = Crypto Dollar
        start_date: Start date (format: 'YYYY-MM-DD')
        end_date: End date (format: 'YYYY-MM-DD')
    
    Returns:
        List of dictionaries with format: [{'date': 'YYYY-MM-DD', 'rate': float}, ...]
        Ready to be inserted into fx_rate table
    
    Example:
        >>> data = fetch_ambito_dolar('formal', '2024-01-01', '2024-12-31')
        >>> data = fetch_ambito_dolar('informal', '2024-01-01', '2024-12-31')
    """
    
    start_date = pd.to_datetime(start_date).strftime("%Y-%m-%d")
    end_date = pd.to_datetime(end_date).strftime("%Y-%m-%d")
    base_url = f"https://mercados.ambito.com/dolar/{kind}/historico-general/{start_date}/{end_date}"
    
    print(f"\n{'='*70}")
    print(f"🔍 Fetching {kind.upper()} DOLLAR data")
    print(f"{'='*70}")
    print(f"📅 Period: {start_date} to {end_date}")
    print(f"🌐 URL: {base_url}")
    print(f"{'='*70}\n")
    
    # Fetch data
    resp = try_fetch(base_url, headers=BROWSER_HEADERS)
    
    if isinstance(resp, Exception):
        print(f"❌ Request error: {resp}")
        return []

    if resp.status_code != 200:
        print(f"❌ HTTP Error {resp.status_code}")
        print(f"Response text (first 300 chars):\n{resp.text[:300]}")
        return []
    
    print(f"✅ Response received - Status Code: {resp.status_code}")
    
    # Parse raw JSON response
    raw_data = resp.json()
    parsed = parse_ambito_response(raw_data)
    
    if not parsed:
        print("⚠️  No data found in response")
        return []
    
    # Convert to standardized format for fx_rate table
    # Returns bid and ask rates only (mid can be calculated at query time)
    usd_data = []
    for item in parsed:
        # Convert date DD/MM/YYYY to YYYY-MM-DD
        fecha_dt = pd.to_datetime(item['fecha'], format='%d/%m/%Y')
        fecha_str = fecha_dt.strftime('%Y-%m-%d')
        
        # Parse buy (bid) and sell (ask) rates
        compra = parse_number(item['compra'])  # bid
        venta = parse_number(item['venta'])     # ask
        
        if compra and venta:
            # Add bid rate (compra)
            usd_data.append({
                'date': fecha_str,
                'kind': 'bid',
                'rate': compra
            })
            
            # Add ask rate (venta)
            usd_data.append({
                'date': fecha_str,
                'kind': 'ask',
                'rate': venta
            })
    
    print(f"✅ Processed {len(usd_data)} USD records (bid/ask)")
    return usd_data

if __name__ == "__main__":
    print("\n" + "🇦🇷" * 35)
    print("   USD EXCHANGE RATE FETCH SCRIPT - AMBITO.COM")
    print("🇦🇷" * 35 + "\n")
    
    # Configuration
    kind = "formal"  # Options: 'formal', 'mep', 'informal', 'cripto'
    start = "2024-08-01"
    end = "2024-08-31"
    
    print(f"⚙️  CONFIGURATION:")
    print(f"   Dollar type: {kind.upper()}")
    print(f"   Period: {start} to {end}")
    print("")
    
    # Fetch data
    data = fetch_ambito_dolar(kind, start, end)
    
    if data:
        print(f"\n📊 SAMPLE DATA:")
        print("="*70)
        for item in data[:10]:
            print(f"  {item['date']} | Rate: ${item['rate']:.2f}")
        if len(data) > 10:
            print(f"  ... ({len(data) - 10} more records)")
        print("="*70 + "\n")
