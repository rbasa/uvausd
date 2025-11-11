#!/usr/bin/env python3
"""
Script to validate fx_rate data quality
Detects anomalies like:
- Long periods with no variation (flat/linear data)
- Missing data gaps
- Duplicate consecutive values
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from utils.db_manager import DoltDBManager
import pandas as pd

def validate_pair_data(pair_name, df, threshold_days=30, max_flat_pct=0.90):
    """
    Validates data quality for a specific pair
    
    Args:
        pair_name: Name of the pair (e.g., 'USDB_ARS')
        df: DataFrame with columns: DATE, rate
        threshold_days: Minimum days to consider as a "period"
        max_flat_pct: Maximum percentage of flat values allowed
    
    Returns:
        dict with validation results
    """
    issues = []
    
    if len(df) == 0:
        return {'pair': pair_name, 'status': 'ERROR', 'issues': ['No data found']}
    
    # Sort by date
    df = df.sort_values('DATE').reset_index(drop=True)
    
    # Calculate differences
    df['diff'] = df['rate'].diff()
    df['is_flat'] = df['diff'] == 0
    
    # 1. Check for long flat periods
    flat_count = df['is_flat'].sum()
    flat_pct = flat_count / len(df) * 100
    
    if flat_pct > max_flat_pct * 100:
        issues.append(f"Too many flat values: {flat_pct:.1f}% ({flat_count}/{len(df)})")
    
    # 2. Find consecutive flat periods
    df['flat_group'] = (df['is_flat'] != df['is_flat'].shift()).cumsum()
    flat_groups = df[df['is_flat']].groupby('flat_group').size()
    
    if len(flat_groups) > 0:
        max_consecutive = flat_groups.max()
        if max_consecutive >= threshold_days:
            issues.append(f"Long flat period detected: {max_consecutive} consecutive days")
            
            # Find the period
            worst_group = flat_groups.idxmax()
            flat_period = df[df['flat_group'] == worst_group]
            start = flat_period['DATE'].min()
            end = flat_period['DATE'].max()
            issues.append(f"  Period: {start} to {end}")
    
    # 3. Check for data gaps (missing dates)
    date_range = pd.date_range(start=df['DATE'].min(), end=df['DATE'].max(), freq='D')
    missing_dates = len(date_range) - len(df)
    
    if missing_dates > len(df) * 0.1:  # More than 10% missing
        issues.append(f"Many missing dates: {missing_dates} gaps")
    
    # 4. Check variance in recent data (last 90 days)
    recent = df[df['DATE'] >= df['DATE'].max() - pd.Timedelta(days=90)]
    if len(recent) > 0:
        recent_std = recent['rate'].std()
        if recent_std < 1.0:  # Very low variance
            issues.append(f"Low variance in recent data (std={recent_std:.2f})")
    
    status = 'ERROR' if len(issues) > 0 else 'OK'
    
    return {
        'pair': pair_name,
        'status': status,
        'records': len(df),
        'date_range': f"{df['DATE'].min()} to {df['DATE'].max()}",
        'flat_pct': f"{flat_pct:.1f}%",
        'issues': issues
    }


def validate_all_pairs():
    """
    Validates all currency pairs in the database
    """
    print("\n" + "🔍" * 35)
    print("   FX DATA QUALITY VALIDATION")
    print("🔍" * 35 + "\n")
    
    # Connect to database
    if not os.getenv('DOLT_DB'):
        os.environ['DOLT_DB'] = 'mysql://root:@localhost:3306/macroeconomia'
    
    db = DoltDBManager()
    db.connect()
    
    # Get all pairs
    pairs_query = """
    SELECT DISTINCT pair 
    FROM fx_rate 
    ORDER BY pair
    """
    
    pairs = db.query(pairs_query)
    print(f"📊 Found {len(pairs)} currency pairs to validate\n")
    
    all_results = []
    
    for pair_row in pairs:
        pair = pair_row['pair']
        
        # Get mid-point data (average of bid/ask)
        data_query = f"""
        SELECT 
            DATE,
            AVG(rate) as rate
        FROM fx_rate
        WHERE pair = '{pair}'
          AND kind IN ('bid', 'ask')
        GROUP BY DATE
        ORDER BY DATE
        """
        
        try:
            data = db.query(data_query)
            if not data:
                print(f"⚠️  {pair}: No data")
                continue
            
            df = pd.DataFrame(data)
            df['DATE'] = pd.to_datetime(df['DATE'])
            
            # Validate
            result = validate_pair_data(pair, df)
            all_results.append(result)
            
            # Print result
            status_icon = "✅" if result['status'] == 'OK' else "❌"
            print(f"{status_icon} {pair}")
            print(f"   Records: {result['records']}")
            print(f"   Range: {result['date_range']}")
            print(f"   Flat values: {result['flat_pct']}")
            
            if result['issues']:
                for issue in result['issues']:
                    print(f"   ⚠️  {issue}")
            print()
            
        except Exception as e:
            print(f"❌ {pair}: Error - {e}\n")
    
    db.disconnect()
    
    # Summary
    print("=" * 70)
    print("📊 VALIDATION SUMMARY")
    print("=" * 70)
    
    total = len(all_results)
    errors = sum(1 for r in all_results if r['status'] == 'ERROR')
    ok = total - errors
    
    print(f"Total pairs validated: {total}")
    print(f"✅ OK: {ok}")
    print(f"❌ With issues: {errors}")
    
    if errors > 0:
        print("\n⚠️  Pairs with issues:")
        for r in all_results:
            if r['status'] == 'ERROR':
                print(f"   - {r['pair']}")
        print("\nRecommendation: Run fix script for problematic pairs")
        return 1
    else:
        print("\n✅ All pairs look good!")
        return 0


if __name__ == "__main__":
    try:
        exit_code = validate_all_pairs()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

