"""
Shared utilities for ETL scripts

To run scripts, use:
    python -m etl.utils.fetch_usd_data
    
Or import as module:
    from etl.utils.fetch_usd_data import fetch_ambito_dolar
    from etl.utils import try_fetch, parse_number, DoltDBManager
"""

from .utils import (
    try_fetch, 
    parse_number, 
    BROWSER_HEADERS, 
    parse_ambito_response,
    fetch_all_data_paginated,
    transform_fx_data_to_wide
)
from .db_manager import DoltDBManager

__all__ = [
    'try_fetch', 
    'parse_number', 
    'BROWSER_HEADERS', 
    'parse_ambito_response',
    'fetch_all_data_paginated',
    'transform_fx_data_to_wide',
    'DoltDBManager'
]
