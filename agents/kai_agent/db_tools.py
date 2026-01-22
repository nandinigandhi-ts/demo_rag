from pathlib import Path
from dotenv import load_dotenv
import os
import mysql.connector
from mysql.connector import Error
import datetime as dt

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
    out = []
    for r in rows:
        out.append({
            k: (v.isoformat() if isinstance(v, (dt.date, dt.datetime)) else v)
            for k, v in r.items()
        })
    return out

def get_program_overview(program_name: str) -> dict:
    """
    Return structured info for a program.
    This is a SAFE tool: parameterized query, limited fields, no raw SQL input.
    """
    if not program_name or not program_name.strip():
        return {"status": "error", "message": "program_name is required"}

    q = """
        SELECT program_id, name, mode, duration_weeks, fee_usd, eligibility
        FROM programs
        WHERE name LIKE %s
        LIMIT 3
    """
    try:
        conn = _get_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute(q, (f"%{program_name.strip()}%",))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return {"status": "ok", "results": _json_safe_rows(rows)}
    
    except Error as e:
        return {"status": "error", "message": f"MySQL error: {str(e)}"}

def list_intakes(program_name: str) -> dict:
    """
    List upcoming intakes for a given program name (safe, parameterized).
    """
    if not program_name or not program_name.strip():
        return {"status": "error", "message": "program_name is required"}

    q = """
        SELECT p.name AS program_name, i.intake_name, i.start_date, i.application_deadline, i.seats, i.timezone
        FROM intakes i
        JOIN programs p ON p.program_id = i.program_id
        WHERE p.name LIKE %s
        ORDER BY i.start_date ASC
        LIMIT 10
    """
    try:
        conn = _get_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute(q, (f"%{program_name.strip()}%",))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return {"status": "ok", "results": _json_safe_rows(rows)}
    except Error as e:
        return {"status": "error", "message": f"MySQL error: {str(e)}"}
