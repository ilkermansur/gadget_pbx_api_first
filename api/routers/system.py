from fastapi import APIRouter, HTTPException
from database import get_db_conn, release_db_conn
import psycopg2.extras

router = APIRouter(prefix="/status", tags=["System"])

@router.get("/")
def get_system_status():
    status = {"database": "offline", "version": "1.0.0"}
    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        status["database"] = "online"
    except Exception as e:
        status["database"] = f"error: {str(e)}"
    finally:
        if conn:
            release_db_conn(conn)
    
    return status
