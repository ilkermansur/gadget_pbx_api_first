from fastapi import APIRouter
from database import get_db_conn, release_db_conn
import psycopg2.extras

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/cdr")
def get_cdr():
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT src, dst, duration, disposition, start FROM cdr ORDER BY start DESC LIMIT 50")
        return cur.fetchall()
    finally:
        release_db_conn(conn)

@router.get("/queuelog")
def get_queue_log():
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM queue_log ORDER BY time DESC LIMIT 50")
        return cur.fetchall()
    finally:
        release_db_conn(conn)
