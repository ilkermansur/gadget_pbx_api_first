from fastapi import APIRouter, HTTPException
from database import get_db_conn, release_db_conn
from schemas import VoicemailCreate, VoicemailUpdate
import psycopg2.extras

router = APIRouter(prefix="/voicemail", tags=["Voicemail"])

@router.get("/", response_description="List of all voicemail boxes")
def list_voicemails():
    """
    Retrieve a list of all configured voicemail boxes.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT uniqueid, context, mailbox, fullname, email FROM voicemail")
        return cur.fetchall()
    finally:
        release_db_conn(conn)

@router.get("/{mailbox}", response_description="Detailed voicemail box information")
def get_voicemail(mailbox: str, context: str = "default"):
    """
    Retrieve detailed configuration for a specific voicemail box.
    - **mailbox**: The mailbox number
    - **context**: The voicemail context (default: 'default')
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM voicemail WHERE mailbox = %s AND context = %s", (mailbox, context))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Voicemail box not found")
        return result
    finally:
        release_db_conn(conn)

@router.post("/", response_description="Success message")
def create_voicemail(vm: VoicemailCreate):
    """
    Create a new voicemail box entry.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO voicemail (mailbox, context, password, fullname, email) 
            VALUES (%s, %s, %s, %s, %s)
        """, (vm.mailbox, vm.context, vm.password, vm.fullname, vm.email))
        conn.commit()
        return {"message": f"Voicemail box {vm.mailbox} created successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        release_db_conn(conn)

@router.patch("/{mailbox}", response_description="Success message")
def update_voicemail(mailbox: str, vm: VoicemailUpdate, context: str = "default"):
    """
    Update specific fields of an existing voicemail box.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        updates = []
        params = []
        if vm.password:
            updates.append("password = %s")
            params.append(vm.password)
        if vm.fullname:
            updates.append("fullname = %s")
            params.append(vm.fullname)
        if vm.email:
            updates.append("email = %s")
            params.append(vm.email)
        
        if updates:
            query = f"UPDATE voicemail SET {', '.join(updates)} WHERE mailbox = %s AND context = %s"
            params.extend([mailbox, context])
            cur.execute(query, tuple(params))
            conn.commit()
            return {"message": f"Voicemail box {mailbox} updated"}
        return {"message": "No changes provided"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        release_db_conn(conn)

@router.delete("/{mailbox}", response_description="Success message")
def delete_voicemail(mailbox: str, context: str = "default"):
    """
    Permanently delete a voicemail box.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM voicemail WHERE mailbox = %s AND context = %s", (mailbox, context))
        conn.commit()
        return {"message": f"Voicemail box {mailbox} deleted"}
    finally:
        release_db_conn(conn)
