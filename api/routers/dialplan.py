from fastapi import APIRouter, HTTPException
from database import get_db_conn, release_db_conn
from schemas import RouteCreate, RouteUpdate
import psycopg2.extras

router = APIRouter(prefix="/dialplan", tags=["Dialplan"])

@router.get("/", response_description="List of all dialplan routes")
def list_routes():
    """
    Retrieve a list of all dialplan routes stored in the database.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, context, exten, priority, app, appdata FROM extensions")
        return cur.fetchall()
    finally:
        release_db_conn(conn)

@router.get("/{route_id}", response_description="Detailed route information")
def get_route(route_id: int):
    """
    Retrieve a specific dialplan route by its database ID.
    - **route_id**: The primary key ID in the extensions table
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, context, exten, priority, app, appdata FROM extensions WHERE id = %s", (route_id,))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Route not found")
        return result
    finally:
        release_db_conn(conn)

@router.post("/", response_description="Success message")
def create_route(route: RouteCreate):
    """
    Create a new dialplan entry.
    - **context**: The logical grouping (e.g., 'from-internal')
    - **exten**: The dialed number or pattern
    - **priority**: Step number in the execution (typically starting at 1)
    - **app**: Asterisk application (e.g., 'Dial', 'Playback')
    - **appdata**: Arguments for the application
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO extensions (context, exten, priority, app, appdata) VALUES (%s, %s, %s, %s, %s)", 
                    (route.context, route.exten, route.priority, route.app, route.appdata))
        conn.commit()
        return {"message": "Route created"}
    finally:
        release_db_conn(conn)

@router.patch("/{route_id}", response_description="Success message")
def update_route(route_id: int, route: RouteUpdate):
    """
    Modify an existing dialplan route.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        updates = []
        params = []
        if route.context:
            updates.append("context = %s")
            params.append(route.context)
        if route.exten:
            updates.append("exten = %s")
            params.append(route.exten)
        if route.priority:
            updates.append("priority = %s")
            params.append(route.priority)
        if route.app:
            updates.append("app = %s")
            params.append(route.app)
        if route.appdata is not None:
            updates.append("appdata = %s")
            params.append(route.appdata)
        
        if updates:
            query = f"UPDATE extensions SET {', '.join(updates)} WHERE id = %s"
            params.append(route_id)
            cur.execute(query, tuple(params))
            conn.commit()
            return {"message": f"Route {route_id} updated"}
        return {"message": "No changes provided"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        release_db_conn(conn)

@router.delete("/{route_id}", response_description="Success message")
def delete_route(route_id: int):
    """
    Remove a dialplan entry from the database.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM extensions WHERE id = %s", (route_id,))
        conn.commit()
        return {"message": f"Route {route_id} deleted"}
    finally:
        release_db_conn(conn)
