from fastapi import APIRouter
from database import get_db_conn, release_db_conn
from schemas import DashboardSummary, ServiceStatus
import psycopg2.extras
import socket
import time

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

def check_port(host: str, port: int, timeout: int = 2):
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except:
        return False

@router.get("/services", response_model=list[ServiceStatus])
def get_service_status():
    """
    Check the connectivity of core services (Database and Asterisk).
    """
    results = []
    
    # Check Database
    start = time.time()
    db_online = "offline"
    latency = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        release_db_conn(conn)
        db_online = "online"
        latency = round((time.time() - start) * 1000, 2)
    except:
        db_online = "offline"
    
    results.append(ServiceStatus(name="Database", status=db_online, latency_ms=latency))
    
    # Check Asterisk (via internal network bridge)
    # SIP is usually UDP, but Asterisk often has a TCP/HTTP port for ARI/AMI.
    # We will check common ports: 5060 (SIP), 8088 (ARI), 5038 (AMI)
    asterisk_status = "offline"
    for port in [5060, 8088, 5038]:
        if check_port("asterisk", port, timeout=1):
            asterisk_status = "online"
            break
            
    results.append(ServiceStatus(name="Asterisk", status=asterisk_status))
    
    return results

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary():
    """
    Retrieve aggregated statistics for the dashboard UI.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # 1. Extensions Stats
        cur.execute("SELECT count(*) as total FROM ps_endpoints")
        total_ext = cur.fetchone()['total']
        
        cur.execute("SELECT count(distinct id) as online FROM ps_contacts")
        online_ext = cur.fetchone()['online']
        
        # 2. Trunks Stats
        cur.execute("SELECT count(*) as total FROM ps_registrations")
        total_trunks = cur.fetchone()['total']
        
        # 3. Device Types (Heuristic)
        cur.execute("SELECT user_agent FROM ps_contacts")
        agents = cur.fetchall()
        physical = 0
        soft = 0
        for row in agents:
            ua = (row['user_agent'] or "").lower()
            if any(x in ua for x in ["yealink", "cisco", "grandstream", "polycom", "snom"]):
                physical += 1
            else:
                soft += 1
                
        # 4. Active Calls (Placeholder as real-time SIP requires ARI/AMI)
        # For now, we return 0 or a very basic check from current channels if we had ARI
        active_calls = 0 
        
        import os
        load = os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0.0

        return DashboardSummary(
            extensions_total=total_ext,
            extensions_online=online_ext,
            extensions_offline=total_ext - online_ext,
            trunks_total=total_trunks,
            trunks_online=0, # Need ARI to verify outbound registration status
            active_calls=active_calls,
            physical_phones=physical,
            softphones=soft,
            system_load=load
        )
    finally:
        release_db_conn(conn)
