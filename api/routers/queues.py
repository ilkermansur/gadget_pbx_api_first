from fastapi import APIRouter, HTTPException
from database import get_db_conn, release_db_conn
from schemas import QueueCreate, QueueUpdate, QueueMemberAdd
import psycopg2.extras

router = APIRouter(prefix="/queues", tags=["Queues"])

@router.get("/", response_description="List of all queues")
def list_queues():
    """
    Retrieve a list of all configured call center queues.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM queues")
        return cur.fetchall()
    finally:
        release_db_conn(conn)

@router.post("/", response_description="Success message")
def create_queue(queue: QueueCreate):
    """
    Create a new call center queue.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO queues (name, musiconhold, strategy, timeout, joinempty) 
            VALUES (%s, %s, %s, %s, %s)
        """, (queue.name, queue.musiconhold, queue.strategy, queue.timeout, queue.joinempty))
        conn.commit()
        return {"message": f"Queue {queue.name} created"}
    finally:
        release_db_conn(conn)

@router.delete("/{name}", response_description="Success message")
def delete_queue(name: str):
    """
    Delete a queue and all its members.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM queue_members WHERE queue_name = %s", (name,))
        cur.execute("DELETE FROM queues WHERE name = %s", (name,))
        conn.commit()
        return {"message": f"Queue {name} deleted"}
    finally:
        release_db_conn(conn)

# --- Queue Members ---

@router.get("/{name}/members", response_description="List of queue members")
def list_queue_members(name: str):
    """
    List all agents (members) assigned to a specific queue.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM queue_members WHERE queue_name = %s", (name,))
        return cur.fetchall()
    finally:
        release_db_conn(conn)

@router.post("/{name}/members", response_description="Success message")
def add_queue_member(name: str, member: QueueMemberAdd):
    """
    Add a new agent to a queue.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        uniqueid = f"{name}_{member.interface.replace('/', '_')}"
        cur.execute("""
            INSERT INTO queue_members (queue_name, interface, membername, penalty, uniqueid) 
            VALUES (%s, %s, %s, %s, %s)
        """, (name, member.interface, member.membername, member.penalty, uniqueid))
        conn.commit()
        return {"message": f"Member {member.interface} added to queue {name}"}
    finally:
        release_db_conn(conn)
