from fastapi import APIRouter
from database import get_db_conn, release_db_conn
import psycopg2.extras

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

@router.get("/peers", response_description="Real-time extension registration status")
def get_peers():
    """
    Detailed list of all extensions and their current registration status.
    Uses 'ps_contacts' to determine if an endpoint is online.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Join ps_endpoints with ps_contacts to see who is online
        query = """
            SELECT 
                e.id as extension,
                e.context,
                CASE WHEN c.id IS NOT NULL THEN 'online' ELSE 'offline' END as status,
                c.user_agent,
                c.uri as ip_address
            FROM ps_endpoints e
            LEFT JOIN ps_contacts c ON c.id LIKE e.id || '%'
        """
        cur.execute(query)
        return cur.fetchall()
    finally:
        release_db_conn(conn)
