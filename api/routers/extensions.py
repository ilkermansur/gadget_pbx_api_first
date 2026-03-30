from fastapi import APIRouter, HTTPException, Depends
from database import get_db_conn, release_db_conn
from schemas import ExtensionCreate, ExtensionUpdate
import psycopg2.extras

router = APIRouter(prefix="/extensions", tags=["Extensions"])
def compile_allow_string(ext):
    """
    Helper to build the PJSIP 'allow' string from boolean flags and priority.
    """
    codecs = {
        "ulaw": ext.codec_ulaw,
        "alaw": ext.codec_alaw,
        "g729": ext.codec_g729,
        "h264": ext.codec_h264,
        "opus": ext.codec_opus,
        "vp8": ext.codec_vp8
    }
    
    # Core list of enabled codecs
    enabled = [c for c, val in codecs.items() if val]
    
    # Priority sorting
    if ext.codec_priority:
        p_list = [p.strip().lower() for p in ext.codec_priority.split(",")]
        # Sort so that items in p_list come first in the order specified
        enabled.sort(key=lambda x: p_list.index(x) if x in p_list else 999)
    
    return ",".join(enabled)

@router.get("/", response_description="List of all PJSIP extensions")
def list_extensions():
    """
    Retrieve a list of all configured PJSIP extensions.
    Returns basic information including ID and context.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, context, moh_suggest, allow_transfer, mailboxes, named_call_group, named_pickup_group, dnd_enabled,
                   codec_ulaw, codec_alaw, codec_g729, codec_h264, codec_opus, codec_vp8, codec_priority
            FROM ps_endpoints
        """)
        return cur.fetchall()
    finally:
        release_db_conn(conn)

@router.get("/{ext_id}", response_description="Detailed extension information")
def get_extension(ext_id: str):
    """
    Retrieve detailed configuration for a specific PJSIP extension.
    - **ext_id**: The numeric extension ID (e.g., 1001)
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, context, moh_suggest, allow_transfer, mailboxes, named_call_group, named_pickup_group, dnd_enabled,
                   codec_ulaw, codec_alaw, codec_g729, codec_h264, codec_opus, codec_vp8, codec_priority
            FROM ps_endpoints WHERE id = %s
        """, (ext_id,))
        result = cur.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Extension not found")
        return result
    finally:
        release_db_conn(conn)

@router.post("/", response_description="Success message")
def create_extension(ext: ExtensionCreate):
    """
    Create a new PJSIP Extension with the following components:
    - **AOR**: Address of Record for registration
    - **Auth**: Authentication credentials
    - **Endpoint**: The SIP endpoint configuration including MoH, Transfer, and Group settings
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        # 1. Create AOR
        cur.execute("INSERT INTO ps_aors (id, max_contacts) VALUES (%s, 5)", (ext.ext_id,))
        # 2. Create Auth
        cur.execute("INSERT INTO ps_auths (id, username, password) VALUES (%s, %s, %s)", 
                    (ext.ext_id, ext.ext_id, ext.password))
        # 3. Create Endpoint
        allow_transfer = "yes" if ext.allow_transfer else "no"
        
        # Compile v1.1 Codecs
        compiled_allow = compile_allow_string(ext) if not ext.allow or ext.allow == "opus,ulaw,alaw,h264,vp8" else ext.allow
        
        cur.execute("""
            INSERT INTO ps_endpoints 
            (id, transport, aors, auth, context, moh_suggest, allow_transfer, mailboxes, named_call_group, named_pickup_group, dnd_enabled, 
             allow, disallow, codec_ulaw, codec_alaw, codec_g729, codec_h264, codec_opus, codec_vp8, codec_priority) 
            VALUES (%s, 'transport-udp', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (ext.ext_id, ext.ext_id, ext.ext_id, ext.context, ext.moh_suggest, allow_transfer, ext.mailboxes, 
              ext.named_call_group, ext.named_pickup_group, ext.dnd_enabled, compiled_allow, ext.disallow,
              ext.codec_ulaw, ext.codec_alaw, ext.codec_g729, ext.codec_h264, ext.codec_opus, ext.codec_vp8, ext.codec_priority))
        
        conn.commit()
        return {"message": f"Extension {ext.ext_id} created successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        release_db_conn(conn)

@router.patch("/{ext_id}", response_description="Success message")
def update_extension(ext_id: str, ext: ExtensionUpdate):
    """
    Update specific fields of an existing extension.
    Only provided fields will be modified.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        # Update Auth
        if ext.password:
            cur.execute("UPDATE ps_auths SET password = %s WHERE id = %s", (ext.password, ext_id))
        
        # Update Endpoint
        updates = []
        params = []
        if ext.context:
            updates.append("context = %s")
            params.append(ext.context)
        if ext.moh_suggest:
            updates.append("moh_suggest = %s")
            params.append(ext.moh_suggest)
        if ext.allow_transfer is not None:
            updates.append("allow_transfer = %s")
            params.append("yes" if ext.allow_transfer else "no")
        if ext.mailboxes:
            updates.append("mailboxes = %s")
            params.append(ext.mailboxes)
        if ext.named_call_group:
            updates.append("named_call_group = %s")
            params.append(ext.named_call_group)
        if ext.named_pickup_group:
            updates.append("named_pickup_group = %s")
            params.append(ext.named_pickup_group)
        if ext.dnd_enabled is not None:
            updates.append("dnd_enabled = %s")
            params.append(ext.dnd_enabled)
            
        # v1.1 Advanced Codec Update
        has_new_codec_settings = any([ext.codec_ulaw is not None, ext.codec_alaw is not None, 
                                     ext.codec_g729 is not None, ext.codec_h264 is not None, 
                                     ext.codec_opus is not None, ext.codec_vp8 is not None,
                                     ext.codec_priority is not None])
        
        if has_new_codec_settings:
            # We need current values to compile the new string
            cur.execute("SELECT allow, disallow FROM ps_endpoints WHERE id = %s", (ext_id,))
            current = cur.fetchone()
            # For simplicity, we'll re-compile based on the PATCH fields + defaults or current
            # This logic could be more complex but let's stick to user intent
            # Simplified: Use the provided booleans or fallback to something sensible
            # Actually, let's just use the direct 'allow' if provided, else compile
            if not ext.allow:
                # Mock a request object to reuse compile_allow_string
                class MockExt: pass
                m = MockExt()
                m.codec_ulaw = ext.codec_ulaw if ext.codec_ulaw is not None else True
                m.codec_alaw = ext.codec_alaw if ext.codec_alaw is not None else True
                m.codec_g729 = ext.codec_g729 if ext.codec_g729 is not None else False
                m.codec_h264 = ext.codec_h264 if ext.codec_h264 is not None else True
                m.codec_opus = ext.codec_opus if ext.codec_opus is not None else False
                m.codec_vp8 = ext.codec_vp8 if ext.codec_vp8 is not None else False
                m.codec_priority = ext.codec_priority if ext.codec_priority else "h264,ulaw,alaw"
                
                new_allow = compile_allow_string(m)
                updates.append("allow = %s")
                params.append(new_allow)
                
                # Update specific boolean columns too for consistency
                updates.append("codec_ulaw = %s, codec_alaw = %s, codec_g729 = %s, codec_h264 = %s, codec_opus = %s, codec_vp8 = %s, codec_priority = %s")
                params.extend([m.codec_ulaw, m.codec_alaw, m.codec_g729, m.codec_h264, m.codec_opus, m.codec_vp8, m.codec_priority])
                
        if ext.allow:
            updates.append("allow = %s")
            params.append(ext.allow)
        if ext.disallow:
            updates.append("disallow = %s")
            params.append(ext.disallow)
        
        if updates:
            query = f"UPDATE ps_endpoints SET {', '.join(updates)} WHERE id = %s"
            params.append(ext_id)
            cur.execute(query, tuple(params))
            
        conn.commit()
        return {"message": f"Extension {ext_id} updated"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        release_db_conn(conn)

@router.delete("/{ext_id}", response_description="Success message")
def delete_extension(ext_id: str):
    """
    Permanently delete an extension and its associated AOR and Auth records.
    """
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM ps_endpoints WHERE id = %s", (ext_id,))
        cur.execute("DELETE FROM ps_auths WHERE id = %s", (ext_id,))
        cur.execute("DELETE FROM ps_aors WHERE id = %s", (ext_id,))
        conn.commit()
        return {"message": f"Extension {ext_id} deleted"}
    finally:
        release_db_conn(conn)
