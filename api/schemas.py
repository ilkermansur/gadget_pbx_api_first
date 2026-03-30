from pydantic import BaseModel
from typing import Optional, List

# Extension Schemas
class ExtensionCreate(BaseModel):
    """
    Schema for creating a new PJSIP Extension.
    """
    ext_id: str = "1001" # Extension number / User ID
    password: str = "pass123" # SIP authentication password
    context: str = "from-internal" # Dialplan context for outbound calls
    moh_suggest: Optional[str] = "default" # Default Music on Hold class
    allow_transfer: bool = True # Whether this extension can perform transfers
    mailboxes: Optional[str] = None # Link to voicemail (e.g. 1001@default)
    named_call_group: Optional[str] = None # Call Group for pickup (e.g. 'sales')
    named_pickup_group: Optional[str] = None # Group this extension can pick up from
    dnd_enabled: bool = False # Do Not Disturb status
    allow: Optional[str] = "opus,ulaw,alaw,h264,vp8" # Allowed codecs (Legacy/Direct)
    disallow: Optional[str] = "all" # Disallowed codecs (Legacy/Direct)
    # v1.1 Advanced Codec Flags
    codec_ulaw: bool = True
    codec_alaw: bool = True
    codec_g729: bool = False
    codec_h264: bool = True
    codec_opus: bool = False
    codec_vp8: bool = False
    codec_priority: Optional[str] = "h264,ulaw,alaw" # Priority order

class ExtensionUpdate(BaseModel):
    """
    Schema for updating an existing PJSIP Extension.
    """
    password: Optional[str] = None # New SIP authentication password
    context: Optional[str] = None # New dialplan context
    moh_suggest: Optional[str] = None # New Music on Hold class
    allow_transfer: Optional[bool] = None # Update transfer permission
    mailboxes: Optional[str] = None # Update voicemail link
    named_call_group: Optional[str] = None # Update Call Group
    named_pickup_group: Optional[str] = None # Update Pickup Group
    dnd_enabled: Optional[bool] = None # Update DND status
    allow: Optional[str] = None # Update allowed codecs
    disallow: Optional[str] = None # Update disallowed codecs
    # v1.1 Advanced Codec Flags
    codec_ulaw: Optional[bool] = None
    codec_alaw: Optional[bool] = None
    codec_g729: Optional[bool] = None
    codec_h264: Optional[bool] = None
    codec_opus: Optional[bool] = None
    codec_vp8: Optional[bool] = None
    codec_priority: Optional[str] = None

# Trunk Schemas
class TrunkCreate(BaseModel):
    """
    Schema for creating a new SIP Trunk.
    """
    trunk_id: str = "provider_trunk" # Unique ID for the trunk
    host: str = "sip.provider.com" # SIP provider host/IP
    username: Optional[str] = None # Outbound registration username
    password: Optional[str] = None # Outbound registration password

class TrunkUpdate(BaseModel):
    """
    Schema for updating an existing SIP Trunk.
    """
    host: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

# Dialplan Schemas
class RouteCreate(BaseModel):
    """
    Schema for creating a new Dialplan Route (Extension entry).
    """
    context: str = "from-internal" # Context where this route is active
    exten: str = "100" # Dialed number
    priority: int = 1 # Execution order for this extension/context
    app: str = "Dial" # Asterisk application to execute
    appdata: Optional[str] = "" # Application parameters (e.g. PJSIP/1001)

class RouteUpdate(BaseModel):
    """
    Schema for updating an existing Dialplan Route.
    """
    context: Optional[str] = None
    exten: Optional[str] = None
    priority: Optional[int] = None
    app: Optional[str] = None
    appdata: Optional[str] = None

# Voicemail Schemas
class VoicemailCreate(BaseModel):
    """
    Schema for creating a new Voicemail box.
    """
    mailbox: str = "1001" # Mailbox number
    context: str = "default" # Voicemail context
    password: str = "1234" # Pin code for checking messages
    fullname: Optional[str] = None # Owner's full name
    email: Optional[str] = None # Email address for notifications

class VoicemailUpdate(BaseModel):
    """
    Schema for updating an existing Voicemail box.
    """
    password: Optional[str] = None
    fullname: Optional[str] = None
    email: Optional[str] = None

# Queue Schemas
class QueueCreate(BaseModel):
    """
    Schema for creating a new Call Center Queue.
    """
    name: str = "support" # Unique name for the queue
    musiconhold: Optional[str] = "default" # MoH class for callers in queue
    strategy: str = "ringall" # Ringing strategy (ringall, leastrecent, fewesthits, etc)
    timeout: int = 15 # How long to ring each agent
    joinempty: str = "yes" # Allow callers to join if no agents are online

class QueueUpdate(BaseModel):
    """
    Schema for updating an existing Queue.
    """
    musiconhold: Optional[str] = None
    strategy: Optional[str] = None
    timeout: Optional[int] = None

class QueueMemberAdd(BaseModel):
    """
    Schema for adding a member (agent) to a queue.
    """
    interface: str = "PJSIP/1001" # Technical interface of the agent
    membername: Optional[str] = None # Human-readable name of the agent
    penalty: int = 0 # Priority level (lower = rings first)

# Blacklist Schemas
class BlacklistEntry(BaseModel):
    """
    Schema for blocking a phone number.
    """
    number: str = "5551234567" # The number to block
    note: Optional[str] = "Spam caller" # Reason for blocking

# Time Condition Schemas
class TimeConditionCreate(BaseModel):
    """
    Schema for creating a Time Condition (Office Hours).
    """
    name: str = "Working Hours" # Name of the rule
    start_time: str = "09:00" # Start time (HH:MM)
    end_time: str = "18:00" # End time (HH:MM)
    weekdays: str = "1-5" # Days of week (1=Mon, 5=Fri, e.g. '1-5')
    match_context: str = "from-internal" # Where to send if time matches
    mismatch_context: str = "after-hours" # Where to send if time doesn't match

class TimeConditionUpdate(BaseModel):
    """
    Schema for updating a Time Condition.
    """
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    weekdays: Optional[str] = None
    match_context: Optional[str] = None
    mismatch_context: Optional[str] = None

# Hunt Group (Hunt Pilot) Schemas
class HuntGroupCreate(BaseModel):
    """
    Schema for creating a Hunt Pilot (Ring Group).
    """
    name: str = "sales_hunt" # Unique name for the hunt group
    strategy: str = "simultaneous" # 'simultaneous' or 'linear'
    members: str = "1001,1002" # Comma-separated list of extensions

class HuntGroupUpdate(BaseModel):
    """
    Schema for updating a Hunt Pilot.
    """
    strategy: Optional[str] = None
    members: Optional[str] = None

# Report Schemas
class CDRLog(BaseModel):
    src: str
    dst: str
    duration: int
    disposition: str
    start: str

# Dashboard Schemas
class ServiceStatus(BaseModel):
    """
    Status of a system service (Asterisk, Database, etc.)
    """
    name: str
    status: str # online, offline, degraded
    latency_ms: Optional[float] = None

class DashboardSummary(BaseModel):
    """
    Comprehensive statistics for the PBX Dashboard.
    """
    extensions_total: int
    extensions_online: int
    extensions_offline: int
    trunks_total: int
    trunks_online: int
    active_calls: int # Placeholder or ARI derived
    physical_phones: int # Heuristic based on User-Agent
    softphones: int # Heuristic based on User-Agent
    system_load: float # CPU matching
