#!/usr/bin/env python3
"""
Database Manager - Handles connections and operations with Dolt

"""

import pymysql
import os
from typing import List, Dict, Any, Optional


class DoltDBManager:
    """Manages operations with Dolt database"""
    
    def __init__(self, connection_string: str = None):
        """
        Initializes the manager with the connection string
        
        Args:
            connection_string: mysql://user:password@host:port/database
                             or None to use DOLT_DB environment variable
        """
        self.connection_string = connection_string or os.getenv('DOLT_DB')
        if not self.connection_string:
            raise ValueError("❌ DOLT_DB not configured. Use: export DOLT_DB='mysql://user:@localhost:3306/macroeconomia'")
        
        self.connection = None
        self._parse_connection_string()
    
    def _parse_connection_string(self):
        """Parses the connection string mysql://user:password@host:port/database"""
        if not self.connection_string.startswith('mysql://'):
            raise ValueError("❌ Connection string must start with 'mysql://'")
        
        # Remove mysql:// prefix
        conn_str = self.connection_string[8:]
        
        # Split user:password@host:port/database
        if '@' in conn_str:
            user_pass, rest = conn_str.split('@', 1)
            if ':' in user_pass:
                self.user, self.password = user_pass.split(':', 1)
            else:
                self.user = user_pass
                self.password = ''
        else:
            raise ValueError("❌ Invalid connection string")
        
        # Split host:port/database
        if '/' in rest:
            host_port, self.database = rest.split('/', 1)
        else:
            raise ValueError("❌ Missing database in connection string")
        
        # Split host:port
        if ':' in host_port:
            self.host, port_str = host_port.split(':', 1)
            self.port = int(port_str)
        else:
            self.host = host_port
            self.port = 3306
    
    def connect(self):
        """Establishes database connection"""
        try:
            # Try Unix socket first (more reliable for local Dolt)
            try:
                self.connection = pymysql.connect(
                    unix_socket='/tmp/mysql.sock',
                    user=self.user,
                    password='',
                    database=self.database,
                    autocommit=False,
                    cursorclass=pymysql.cursors.DictCursor
                )
                print(f"✅ Connected via Unix socket: /tmp/mysql.sock → {self.database}")
            except:
                # Fallback to TCP
                self.connection = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password='',
                    database=self.database,
                    autocommit=False,
                    cursorclass=pymysql.cursors.DictCursor
                )
                print(f"✅ Connected via TCP: {self.host}:{self.port}/{self.database}")
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print(f"   Attempted: {self.host}:{self.port}/{self.database}")
            raise
    
    def disconnect(self):
        """Closes the connection"""
        if self.connection:
            self.connection.close()
            print("✅ Connection closed")
    
    def query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Executes a query - Equivalent to queryPromise in JS
        
        Args:
            sql: SQL query to execute
            params: Query parameters (optional)
        
        Returns:
            List of dictionaries with results
        """
        if not self.connection:
            raise Exception("❌ No connection established. Call connect() first.")
        
        try:
            # pymysql already uses DictCursor by default if configured in connect()
            cursor = self.connection.cursor()
            cursor.execute(sql, params or ())
            
            # Commands that return results
            sql_upper = sql.strip().upper()
            returns_results = (
                sql_upper.startswith('SELECT') or 
                sql_upper.startswith('SHOW') or 
                sql_upper.startswith('DESCRIBE') or
                sql_upper.startswith('DESC') or
                sql_upper.startswith('CALL')
            )
            
            if returns_results:
                result = cursor.fetchall()
            else:
                result = [{"affected_rows": cursor.rowcount}]
                self.connection.commit()
            
            cursor.close()
            return result
            
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            raise
    
    def dolt_pull(self) -> Dict:
        """
        Pull changes from origin/main
        Note: Requires root privileges or SUPER grant
        """
        try:
            result = self.query("CALL dolt_pull('origin', 'main')")
            return result[0] if result else {}
        except Exception as e:
            if 'command denied' in str(e).lower():
                print(f"   ⚠️  Pull skipped: User lacks DOLT_PULL privileges")
                print(f"   💡 Run with root user or grant SUPER privilege")
                return {"status": 0, "message": "skipped - insufficient privileges"}
            raise
    
    def dolt_add(self, table_name: str) -> Dict:
        """Adds table to staging"""
        result = self.query(f"CALL dolt_add('{table_name}')")
        return result[0] if result else {}
    
    def dolt_commit(self, message: str) -> Dict:
        """
        Commits changes
        Returns success even if nothing to commit
        """
        try:
            result = self.query("CALL dolt_commit('-m', %s)", (message,))
            return result[0] if result else {}
        except Exception as e:
            # "nothing to commit" is not an error - it's a valid state
            if 'nothing to commit' in str(e).lower():
                return {"status": 0, "message": "nothing to commit"}
            raise
    
    def dolt_push(self) -> Dict:
        """
        Pushes changes to origin/main
        Note: Requires root privileges or SUPER grant
        """
        try:
            result = self.query("CALL dolt_push('origin', 'main')")
            return result[0] if result else {}
        except Exception as e:
            if 'command denied' in str(e).lower():
                print(f"   ⚠️  Push skipped: User lacks DOLT_PUSH privileges")
                print(f"   💡 Run manually: cd /path/to/db && dolt push origin main")
                return {"status": 0, "message": "skipped - insufficient privileges"}
            raise
    
    def insert_fx_rate(self, date: str, kind: str, pair: str, rate: float) -> Dict:
        """
        Insert into fx_rate with INSERT IGNORE (equivalent to JS)
        
        Args:
            date: Date in format 'YYYY-MM-DD'
            kind: Data type (e.g., 'UVA', 'USD_OFICIAL')
            pair: Currency pair (e.g., 'UVA_ARS', 'USD_ARS')
            rate: Exchange rate value
        
        Returns:
            Dictionary with affected_rows
        """
        result = self.query(
            "INSERT IGNORE INTO fx_rate (DATE, kind, pair, rate) VALUES (%s, %s, %s, %s)",
            (date, kind, pair, rate)
        )
        return result[0] if result else {}


if __name__ == "__main__":
    # Connection test
    import os
    
    # Set default if not configured
    if not os.getenv('DOLT_DB'):
        os.environ['DOLT_DB'] = 'mysql://root:@localhost:3306/macroeconomia'
        print(f"ℹ️  Using default DOLT_DB: {os.environ['DOLT_DB']}\n")
    
    db = DoltDBManager()
    db.connect()
    
    # Test query
    result = db.query("CALL dolt_pull('origin', 'main')")
    print(f"Total records in fx_rate: {result[0]['total']}")
    
    db.disconnect()
