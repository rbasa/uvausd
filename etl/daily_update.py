#!/usr/bin/env python3
"""
Daily ETL Update Script
Fetches latest data and pushes to DoltHub

This script is designed to run in GitHub Actions daily.
It only fetches and updates recent data (last 7 days) to be efficient.

Usage:
    python etl/daily_update.py
    
Environment variables required:
    DOLT_DB: Database connection string (mysql://user:password@host:port/database)
    
Note: DoltHub push uses SSH keys configured via `dolt config` or SSH agent
"""

import os
import sys
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))

from utils.fetch_usd_data import fetch_ambito_dolar
from utils.fetch_uva import fetch_uva_data
from utils.db_manager import DoltDBManager


def update_recent_data(days_back=7):
    """
    Updates data for the last N days
    
    Args:
        days_back: Number of days to update (default: 7)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    print("\n" + "🔄" * 35)
    print("   DAILY DATA UPDATE")
    print("🔄" * 35)
    print(f"\n📅 Updating period: {start_str} to {end_str}")
    print(f"⏰ Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Connect to database
    db = DoltDBManager()
    db.connect()
    
    # Track what was updated
    updated_pairs = []
    
    try:
        # 1. Update UVA data
        print("\n🔵 Fetching UVA data...")
        uva_data = fetch_uva_data()
        
        if uva_data:
            # Filter to only recent dates
            recent_uva = [d for d in uva_data if d['date'] >= start_str]
            print(f"   Found {len(recent_uva)} recent UVA records")
            
            if recent_uva:
                inserted_count = 0
                for item in recent_uva:
                    result = db.insert_fx_rate(
                        date=item['date'],
                        kind=item['kind'],
                        pair='UVA_ARS',
                        rate=item['rate']
                    )
                    if result.get('inserted', False):
                        inserted_count += 1
                
                if inserted_count > 0:
                    updated_pairs.append('UVA_ARS')
                    print(f"   ✅ Updated UVA_ARS: {inserted_count} new records inserted")
                else:
                    print(f"   ℹ️  UVA_ARS: All records already exist (no new data)")
        
        # 2. Update USD data (all types)
        usd_types = [
            ('formal', 'USD_ARS'),      # Official
            ('mep', 'USDM_ARS'),         # MEP
            ('informal', 'USDB_ARS'),    # Blue
            ('cripto', 'USDC_ARS')       # Crypto
        ]
        
        for kind, pair in usd_types:
            print(f"\n🔵 Fetching {pair} data...")
            usd_data = fetch_ambito_dolar(kind, start_str, end_str)
            
            if usd_data:
                inserted_count = 0
                for item in usd_data:
                    result = db.insert_fx_rate(
                        date=item['date'],
                        kind=item['kind'],
                        pair=pair,
                        rate=item['rate']
                    )
                    if result.get('inserted', False):
                        inserted_count += 1
                
                if inserted_count > 0:
                    updated_pairs.append(pair)
                    print(f"   ✅ Updated {pair}: {inserted_count} new records inserted (out of {len(usd_data)} processed)")
                else:
                    print(f"   ℹ️  {pair}: All records already exist (no new data)")
        
        # 3. Summary
        if updated_pairs:
            print("\n💾 New data inserted into database")
            print(f"   Updated pairs: {', '.join(set(updated_pairs))}")
            print("\n💡 Dolt operations (add/commit/push) will be handled by:")
            print("   - GitHub Actions workflow (automatic)")
            print("   - Or manually via Dolt CLI: dolt add → dolt commit → dolt push")
        else:
            print("\nℹ️  No new data to insert (all records already exist)")
            print("   This is normal if the data was already updated recently")
        
        print("\n" + "="*70)
        print("✅ DAILY UPDATE COMPLETED SUCCESSFULLY")
        print("="*70)
        if updated_pairs:
            print(f"\nUpdated pairs: {', '.join(set(updated_pairs))}")
        else:
            print("\nNo new data inserted (database already up to date)")
        print(f"Next run: Tomorrow at the same time")
        print("="*70 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Update failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        db.disconnect()


if __name__ == "__main__":
    # Get days to update from env var or use default (7)
    days = int(os.getenv('UPDATE_DAYS', '7'))
    
    exit_code = update_recent_data(days_back=days)
    sys.exit(exit_code)

