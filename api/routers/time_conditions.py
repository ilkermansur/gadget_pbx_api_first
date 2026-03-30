from fastapi import APIRouter, HTTPException
from database import get_db_conn, release_db_conn
from schemas import TimeConditionCreate, TimeConditionUpdate
import psycopg2.extras

router = APIRouter(prefix="/time-conditions", tags=["Time Conditions"])

@router.get("/", response_description="List of all time-based rules")
def list_time_conditions():
    """
    Retrieve all configured office hours / time conditions.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM time_conditions")
        return cur.fetchall()
    finally:
        release_db_conn(conn)

@router.post("/", response_description="Success message")
def create_time_condition(tc: TimeConditionCreate):
    """
    Create a new time condition rule (e.g., Office Hours).
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO time_conditions (name, start_time, end_time, weekdays, match_context, mismatch_context) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (tc.name, tc.start_time, tc.end_time, tc.weekdays, tc.match_context, tc.mismatch_context))
        conn.commit()
        return {"message": f"Time condition '{tc.name}' created"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        release_db_conn(conn)

@router.delete("/{tc_id}", response_description="Success message")
def delete_time_condition(tc_id: int):
    """
    Remove a time condition rule.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM time_conditions WHERE id = %s", (tc_id,))
        conn.commit()
        return {"message": f"Time condition {tc_id} deleted"}
    finally:
        release_db_conn(conn)
