from fastapi import APIRouter, HTTPException
from database import get_db_conn, release_db_conn
from schemas import HuntGroupCreate, HuntGroupUpdate
import psycopg2.extras

router = APIRouter(prefix="/hunt-groups", tags=["Hunt Pilots"])

@router.get("/", response_description="List of all hunt groups")
def list_hunt_groups():
    """
    Retrieve all configured Hunt Pilots (Ring Groups).
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM hunt_groups")
        return cur.fetchall()
    finally:
        release_db_conn(conn)

@router.post("/", response_description="Success message")
def create_hunt_group(hg: HuntGroupCreate):
    """
    Create a new Hunt Pilot with a specific ringing strategy and members.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO hunt_groups (name, strategy, members) 
            VALUES (%s, %s, %s)
        """, (hg.name, hg.strategy, hg.members))
        conn.commit()
        return {"message": f"Hunt group '{hg.name}' created"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        release_db_conn(conn)

@router.patch("/{hg_id}", response_description="Success message")
def update_hunt_group(hg_id: int, hg: HuntGroupUpdate):
    """
    Modify an existing Hunt Pilot's strategy or member list.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        updates = []
        params = []
        if hg.strategy:
            updates.append("strategy = %s")
            params.append(hg.strategy)
        if hg.members:
            updates.append("members = %s")
            params.append(hg.members)
        
        if updates:
            query = f"UPDATE hunt_groups SET {', '.join(updates)} WHERE id = %s"
            params.append(hg_id)
            cur.execute(query, tuple(params))
            conn.commit()
            return {"message": f"Hunt group {hg_id} updated"}
        return {"message": "No changes provided"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        release_db_conn(conn)

@router.delete("/{hg_id}", response_description="Success message")
def delete_hunt_group(hg_id: int):
    """
    Delete a Hunt Pilot.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM hunt_groups WHERE id = %s", (hg_id,))
        conn.commit()
        return {"message": f"Hunt group {hg_id} deleted"}
    finally:
        release_db_conn(conn)
