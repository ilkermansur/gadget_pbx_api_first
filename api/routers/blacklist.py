from fastapi import APIRouter, HTTPException
from database import get_db_conn, release_db_conn
from schemas import BlacklistEntry
import psycopg2.extras

router = APIRouter(prefix="/blacklist", tags=["Blacklist"])

@router.get("/", response_description="List of all blocked numbers")
def list_blacklist():
    """
    Retrieve all phone numbers currently blocked by the system.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM blacklist ORDER BY created_at DESC")
        return cur.fetchall()
    finally:
        release_db_conn(conn)

@router.post("/", response_description="Success message")
def add_to_blacklist(entry: BlacklistEntry):
    """
    Block a new phone number.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO blacklist (number, note) VALUES (%s, %s)", (entry.number, entry.note))
        conn.commit()
        return {"message": f"Number {entry.number} blacklisted"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        release_db_conn(conn)

@router.delete("/{number}", response_description="Success message")
def remove_from_blacklist(number: str):
    """
    Unblock a phone number.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM blacklist WHERE number = %s", (number,))
        conn.commit()
        return {"message": f"Number {number} removed from blacklist"}
    finally:
        release_db_conn(conn)
