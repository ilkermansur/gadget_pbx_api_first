from fastapi import APIRouter, HTTPException
from database import get_db_conn, release_db_conn
from schemas import TrunkCreate, TrunkUpdate
import psycopg2.extras

router = APIRouter(prefix="/trunks", tags=["Trunks"])

@router.get("/", response_description="List of all SIP trunks")
def list_trunks():
    """
    Retrieve a list of all configured SIP trunks (outbound registrations).
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, server_uri, client_uri FROM ps_registrations")
        return cur.fetchall()
    finally:
        release_db_conn(conn)

@router.get("/{trunk_id}", response_description="Detailed trunk information")
def get_trunk(trunk_id: str):
    """
    Retrieve detailed configuration for a specific SIP trunk.
    - **trunk_id**: The unique ID assigned to the trunk
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, server_uri, client_uri FROM ps_registrations WHERE id = %s", (trunk_id,))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Trunk not found")
        return result
    finally:
        release_db_conn(conn)

@router.post("/", response_description="Success message")
def create_trunk(trunk: TrunkCreate):
    """
    Register a new SIP Trunk with an external provider.
    - **trunk_id**: Unique identifier for this trunk
    - **host**: The SIP server address
    - **username/password**: Credentials for registration
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        # Create registration record
        cur.execute("INSERT INTO ps_registrations (id, transport, server_uri, client_uri) VALUES (%s, 'transport-udp', %s, %s)", 
                    (trunk.trunk_id, f"sip:{trunk.host}", f"sip:{trunk.username}@{trunk.host}"))
        conn.commit()
        return {"message": f"Trunk {trunk.trunk_id} created"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        release_db_conn(conn)

@router.patch("/{trunk_id}", response_description="Success message")
def update_trunk(trunk_id: str, trunk: TrunkUpdate):
    """
    Update registration details for an existing trunk.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        if trunk.host:
            cur.execute("UPDATE ps_registrations SET server_uri = %s WHERE id = %s", (f"sip:{trunk.host}", trunk_id))
        if trunk.username and trunk.host:
            cur.execute("UPDATE ps_registrations SET client_uri = %s WHERE id = %s", (f"sip:{trunk.username}@{trunk.host}", trunk_id))
        conn.commit()
        return {"message": f"Trunk {trunk_id} updated"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        release_db_conn(conn)

@router.delete("/{trunk_id}", response_description="Success message")
def delete_trunk(trunk_id: str):
    """
    Remove a trunk registration.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM ps_registrations WHERE id = %s", (trunk_id,))
        conn.commit()
        return {"message": f"Trunk {trunk_id} deleted"}
    finally:
        release_db_conn(conn)
