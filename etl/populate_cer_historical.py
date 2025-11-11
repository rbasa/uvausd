#!/usr/bin/env python3
"""
Script to populate complete historical CER data from BCRA XLS files
"""

import requests
import pandas as pd
import subprocess
import sys
from datetime import datetime, date
import os
import time
import tempfile
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_cer_file(year):
    """Download CER XLS file from BCRA for a specific year"""
    url = f"https://www.bcra.gob.ar/pdfs/PublicacionesEstadisticas/cer{year}.xls"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    try:
        print(f"Downloading CER data for year {year}...")
        # Disable SSL verification for BCRA
        resp = requests.get(url, headers=headers, timeout=30, verify=False)
        resp.raise_for_status()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.xls', delete=False) as tmp_file:
            tmp_file.write(resp.content)
            tmp_file_path = tmp_file.name
        
        return tmp_file_path
        
    except Exception as e:
        print(f"Error downloading CER data for year {year}: {e}")
        return None

def parse_cer_xls(file_path, year):
    """Parse CER XLS file and extract data"""
    try:
        # Read Excel file
        df = pd.read_excel(file_path, header=None)
        
        # Find the data section (CER data usually starts after some header rows)
        # Look for rows that contain date-like data in column 4 and numeric data in column 5
        data_rows = []
        
        for idx, row in df.iterrows():
            # Check if column 4 contains a date and column 5 contains a numeric value
            if pd.notna(row[4]) and pd.notna(row[5]):
                try:
                    # Column 4 contains date in YYYYMMDD format
                    if isinstance(row[4], int) and len(str(row[4])) == 8:
                        # Convert YYYYMMDD to datetime
                        date_str = str(row[4])
                        fecha = pd.to_datetime(f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}")
                    elif isinstance(row[4], str) and len(row[4]) == 8 and row[4].isdigit():
                        # Convert YYYYMMDD string to datetime
                        fecha = pd.to_datetime(f"{row[4][:4]}-{row[4][4:6]}-{row[4][6:8]}")
                    else:
                        continue
                    
                    # Column 5 contains the CER value
                    if isinstance(row[5], (int, float)):
                        valor = float(row[5])
                    elif isinstance(row[5], str):
                        valor = float(row[5].replace(',', '.'))
                    else:
                        continue
                    
                    if pd.notna(fecha) and not pd.isna(valor):
                        data_rows.append({
                            'fecha': fecha,
                            'valor': valor
                        })
                except (ValueError, TypeError):
                    continue
        
        if not data_rows:
            print(f"No valid data found in CER file for year {year}")
            return None
        
        # Create DataFrame
        result_df = pd.DataFrame(data_rows)
        result_df = result_df.dropna(subset=["fecha", "valor"])
        result_df = result_df.drop_duplicates(subset=["fecha"])
        result_df = result_df.sort_values("fecha").reset_index(drop=True)
        
        print(f"Found {len(result_df)} CER data points for year {year}")
        return result_df
        
    except Exception as e:
        print(f"Error parsing CER file for year {year}: {e}")
        return None
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            os.unlink(file_path)

def insert_cer_data_to_dolt(df):
    """Insert CER data into Dolt database"""
    if df is None or df.empty:
        print("No data to insert")
        return
    
    print(f"Inserting {len(df)} CER data points...")
    
    # Create SQL insert statements
    insert_statements = []
    for _, row in df.iterrows():
        date_str = row['fecha'].strftime('%Y-%m-%d')
        valor = row['valor']
        insert_sql = f"INSERT IGNORE INTO macroeconomia_d (DATE, dato, valor) VALUES ('{date_str}', 'CER', {valor});"
        insert_statements.append(insert_sql)
    
    # Execute in batches
    batch_size = 100
    for i in range(0, len(insert_statements), batch_size):
        batch = insert_statements[i:i+batch_size]
        sql_commands = "\n".join(batch)
        
        try:
            # Write to temporary file
            with open("temp_cer_insert.sql", "w") as f:
                f.write(sql_commands)
            
            # Execute with dolt
            result = subprocess.run(
                ["dolt", "sql", "-f", "temp_cer_insert.sql"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"Successfully inserted batch {i//batch_size + 1}")
            else:
                print(f"Error in batch {i//batch_size + 1}: {result.stderr}")
                
        except Exception as e:
            print(f"Error executing batch {i//batch_size + 1}: {e}")
        finally:
            # Clean up temp file
            if os.path.exists("temp_cer_insert.sql"):
                os.remove("temp_cer_insert.sql")
    
    # Commit changes
    try:
        subprocess.run(["dolt", "add", "macroeconomia_d"], check=True)
        subprocess.run(["dolt", "commit", "-m", f"Add historical CER data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"], check=True)
        print("Changes committed successfully")
    except Exception as e:
        print(f"Error committing changes: {e}")

def main():
    # Get CER data for years 2002 to current year
    current_year = datetime.now().year
    start_year = 2002  # Since convertibilidad exit
    
    print(f"Fetching CER data from {start_year} to {current_year}")
    
    all_data = []
    
    for year in range(start_year, current_year + 1):
        print(f"\nProcessing year {year}...")
        
        # Download XLS file
        file_path = download_cer_file(year)
        if file_path is None:
            print(f"Skipping year {year} - download failed")
            continue
        
        # Parse XLS file
        df = parse_cer_xls(file_path, year)
        if df is not None:
            all_data.append(df)
        
        # Rate limiting
        time.sleep(1)
    
    if all_data:
        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=["fecha"])
        combined_df = combined_df.sort_values("fecha").reset_index(drop=True)
        
        print(f"\nTotal CER data points: {len(combined_df)}")
        print(f"Date range: {combined_df['fecha'].min()} to {combined_df['fecha'].max()}")
        print("Sample data:")
        print(combined_df.head())
        
        # Insert into database
        insert_cer_data_to_dolt(combined_df)
    else:
        print("No CER data found")

if __name__ == "__main__":
    main()

