from pathlib import Path
from dotenv import load_dotenv
import os
import mysql.connector
from mysql.connector import Error
import datetime as dt
import re
from typing import List, Dict, Any

load_dotenv(Path(__file__).with_name(".env"), override=False)

def _get_conn():
    """Create an authenticated connection using env vars (no secrets in code)."""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB", "admissions"),
    )

def _json_safe_rows(rows: list[dict]) -> list[dict]:
    """Convert datetime objects to ISO strings for JSON serialization."""
    out = []
    for r in rows:
        out.append({
            k: (v.isoformat() if isinstance(v, (dt.date, dt.datetime)) else v)
            for k, v in r.items()
        })
    return out

def _sanitize_query(query: str) -> str:
    """Basic query sanitization - remove dangerous SQL keywords."""
    dangerous_keywords = [
        'drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update',
        'grant', 'revoke', 'exec', 'execute', 'xp_', 'sp_', 'union', '--', ';'
    ]
    
    query_lower = query.lower()
    for keyword in dangerous_keywords:
        if keyword in query_lower:
            raise ValueError(f"Dangerous SQL keyword '{keyword}' detected in query")
    
    return query.strip()

def get_database_schema() -> dict:
    """
    Retrieve the database schema including tables, columns, and relationships.
    This helps the agent understand the database structure for dynamic query generation.
    """
    try:
        conn = _get_conn()
        cur = conn.cursor(dictionary=True)
        
        # Get tables and their columns
        schema_query = """
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_KEY,
            COLUMN_COMMENT
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME, ORDINAL_POSITION
        """
        
        cur.execute(schema_query, (os.getenv("MYSQL_DB", "admissions"),))
        schema_rows = cur.fetchall()
        
        # Get foreign key relationships
        fk_query = """
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL
        """
        
        cur.execute(fk_query, (os.getenv("MYSQL_DB", "admissions"),))
        fk_rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        # Organize schema by tables
        tables = {}
        for row in schema_rows:
            table_name = row['TABLE_NAME']
            if table_name not in tables:
                tables[table_name] = {'columns': [], 'foreign_keys': []}
            
            tables[table_name]['columns'].append({
                'name': row['COLUMN_NAME'],
                'type': row['DATA_TYPE'],
                'nullable': row['IS_NULLABLE'] == 'YES',
                'key': row['COLUMN_KEY'],
                'comment': row['COLUMN_COMMENT']
            })
        
        # Add foreign key information
        for fk in fk_rows:
            table_name = fk['TABLE_NAME']
            if table_name in tables:
                tables[table_name]['foreign_keys'].append({
                    'column': fk['COLUMN_NAME'],
                    'references_table': fk['REFERENCED_TABLE_NAME'],
                    'references_column': fk['REFERENCED_COLUMN_NAME']
                })
        
        return {"status": "ok", "schema": tables}
        
    except Error as e:
        return {"status": "error", "message": f"MySQL error: {str(e)}"}

def execute_dynamic_query(user_query: str, natural_language_description: str) -> dict:
    """
    Execute a dynamically generated MySQL query based on user input.
    This replaces the hardcoded query functions with flexible SQL generation.
    
    Args:
        user_query: The SQL query to execute (should be SELECT only)
        natural_language_description: Human description of what the query does
    """
    if not user_query or not user_query.strip():
        return {"status": "error", "message": "Query is required"}
    
    try:
        # Sanitize the query
        sanitized_query = _sanitize_query(user_query)
        
        # Ensure it's a SELECT query only
        if not sanitized_query.lower().strip().startswith('select'):
            return {"status": "error", "message": "Only SELECT queries are allowed"}
        
        # Limit results to prevent overwhelming responses
        if 'limit' not in sanitized_query.lower():
            sanitized_query += " LIMIT 50"
        
        conn = _get_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute(sanitized_query)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return {
            "status": "ok", 
            "results": _json_safe_rows(rows),
            "query_description": natural_language_description,
            "rows_returned": len(rows)
        }
        
    except ValueError as ve:
        return {"status": "error", "message": f"Query validation error: {str(ve)}"}
    except Error as e:
        return {"status": "error", "message": f"MySQL error: {str(e)}"}
