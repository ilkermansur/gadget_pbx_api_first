-- ######################################################
-- GADGET-PBX ULTIMATE PBX + CALL CENTER SCHEMA
-- ######################################################

-- ======================================================
-- 1. PJSIP CORE TABLES
-- ======================================================

CREATE TABLE ps_endpoints (
    id VARCHAR(40) PRIMARY KEY,
    transport VARCHAR(40),
    aors VARCHAR(200),
    auth VARCHAR(40),
    context VARCHAR(40),
    disallow VARCHAR(200) DEFAULT 'all',
    allow VARCHAR(200) DEFAULT 'opus,ulaw,alaw,h264,vp8',
    direct_media VARCHAR(10) DEFAULT 'no',
    rewrite_contact VARCHAR(10) DEFAULT 'yes',
    rtp_symmetric VARCHAR(10) DEFAULT 'yes',
    force_rport VARCHAR(10) DEFAULT 'yes',
    ice_support VARCHAR(10) DEFAULT 'no',
    moh_suggest VARCHAR(40) DEFAULT 'default',
    allow_transfer VARCHAR(10) DEFAULT 'yes',
    mailboxes VARCHAR(80),
    named_call_group VARCHAR(80),
    named_pickup_group VARCHAR(80),
    dnd_enabled BOOLEAN DEFAULT false,
    -- Expanded v1.0 Universal Fields
    outbound_auth VARCHAR(40),
    outbound_proxy VARCHAR(255),
    aggregate_mwi VARCHAR(10),
    mwi_from_user VARCHAR(80),
    device_state_busy_at INTEGER,
    t38_udptl VARCHAR(10),
    t38_udptl_ec VARCHAR(10),
    t38_udptl_maxdatagram INTEGER,
    dtmf_mode VARCHAR(15),
    call_group VARCHAR(80),
    pickup_group VARCHAR(80),
    language VARCHAR(40),
    rtp_timeout INTEGER,
    rtp_timeout_hold INTEGER,
    from_user VARCHAR(80),
    from_domain VARCHAR(80),
    mwifromuser VARCHAR(80),
    tos_audio VARCHAR(10),
    cos_audio INTEGER,
    tos_video VARCHAR(10),
    cos_video INTEGER,
    timers VARCHAR(10),
    timers_min_se INTEGER,
    timers_sess_expires INTEGER,
    identify_by VARCHAR(80),
    -- v1.1 Advanced Codec Management
    codec_ulaw BOOLEAN DEFAULT true,
    codec_alaw BOOLEAN DEFAULT true,
    codec_g729 BOOLEAN DEFAULT false,
    codec_h264 BOOLEAN DEFAULT true,
    codec_opus BOOLEAN DEFAULT false,
    codec_vp8 BOOLEAN DEFAULT false,
    codec_priority VARCHAR(255) DEFAULT 'h264,ulaw,alaw'
);

CREATE TABLE ps_auths (
    id VARCHAR(40) PRIMARY KEY,
    auth_type VARCHAR(10) DEFAULT 'userpass',
    password VARCHAR(80),
    username VARCHAR(80),
    realm VARCHAR(40),
    nonce_lifetime INTEGER,
    md5_creds VARCHAR(80)
);

CREATE TABLE ps_aors (
    id VARCHAR(40) PRIMARY KEY,
    contact VARCHAR(255),
    default_expiration INTEGER,
    mailboxes VARCHAR(80),
    max_contacts INTEGER DEFAULT 5,
    minimum_expiration INTEGER,
    remove_existing VARCHAR(10) DEFAULT 'yes',
    qualify_frequency INTEGER,
    authenticate_qualify VARCHAR(10),
    maximum_expiration INTEGER,
    outbound_proxy VARCHAR(255),
    support_path VARCHAR(10),
    qualify_timeout DOUBLE PRECISION,
    voicemail_extension VARCHAR(40)
);

CREATE TABLE ps_contacts (
    id VARCHAR(255) PRIMARY KEY,
    uri VARCHAR(255),
    expiration_time INTEGER,
    qualify_frequency INTEGER,
    qualify_timeout DOUBLE PRECISION,
    outbound_proxy VARCHAR(255),
    path TEXT,
    user_agent VARCHAR(255),
    reg_server VARCHAR(255),
    via_addr VARCHAR(40),
    via_port INTEGER,
    call_id VARCHAR(255),
    endpoint VARCHAR(40),
    prune_on_boot VARCHAR(10),
    qualify_2xx_only VARCHAR(10) DEFAULT 'no',
    outbound_auth VARCHAR(40),
    authenticate_qualify VARCHAR(10) DEFAULT 'no'
);

CREATE TABLE ps_registrations (
    id VARCHAR(40) PRIMARY KEY,
    transport VARCHAR(40),
    outbound_auth VARCHAR(40),
    server_uri VARCHAR(200),
    client_uri VARCHAR(200),
    retry_interval INTEGER DEFAULT 60,
    max_retries INTEGER DEFAULT 10,
    expiration INTEGER DEFAULT 3600,
    line VARCHAR(10) DEFAULT 'yes',
    endpoint VARCHAR(40)
);

CREATE TABLE ps_identifies (
    id VARCHAR(40) PRIMARY KEY,
    endpoint VARCHAR(40),
    match VARCHAR(80)
);

CREATE TABLE ps_domain_aliases (
    id VARCHAR(40) PRIMARY KEY,
    domain VARCHAR(80)
);

-- ======================================================
-- 2. DIALPLAN (REALTIME EXTENSIONS)
-- ======================================================

CREATE TABLE extensions (
    id BIGSERIAL PRIMARY KEY,
    context VARCHAR(40) NOT NULL,
    exten VARCHAR(40) NOT NULL,
    priority INTEGER NOT NULL DEFAULT 1,
    app VARCHAR(40) NOT NULL,
    appdata VARCHAR(256),
    UNIQUE (context, exten, priority)
);

-- ======================================================
-- 3. QUEUES & CALL CENTER
-- ======================================================

CREATE TABLE queues (
    name VARCHAR(128) PRIMARY KEY,
    musiconhold VARCHAR(128),
    announce VARCHAR(128),
    context VARCHAR(128),
    timeout INTEGER,
    ringinuse VARCHAR(10) DEFAULT 'no',
    setinterfacevar VARCHAR(10) DEFAULT 'yes',
    queue_holdtimeinfo VARCHAR(10) DEFAULT 'yes',
    strategy VARCHAR(20) DEFAULT 'ringall',
    joinempty VARCHAR(20) DEFAULT 'yes',
    leavewhenempty VARCHAR(20) DEFAULT 'no',
    reposition_on_fail VARCHAR(10) DEFAULT 'no',
    -- Advanced Asterisk 20 Queue Fields
    announce_frequency INTEGER,
    announce_to_first_user VARCHAR(10),
    min_announce_frequency INTEGER,
    announce_round_seconds INTEGER,
    announce_holdtime VARCHAR(10),
    announce_position VARCHAR(10),
    announce_position_limit INTEGER,
    periodic_announce VARCHAR(128),
    periodic_announce_frequency INTEGER,
    relative_periodic_announce VARCHAR(10),
    random_periodic_announce VARCHAR(10),
    retry INTEGER,
    wrapuptime INTEGER,
    penaltymemberslimit INTEGER,
    autofill VARCHAR(10),
    monitor_type VARCHAR(128),
    monitor_format VARCHAR(128),
    servicelevel INTEGER,
    queue_thankyou VARCHAR(128),
    queue_lessthan VARCHAR(128),
    queue_reporthold VARCHAR(128),
    queue_periodicannounce VARCHAR(128),
    announce_exit_context VARCHAR(128),
    memberdelay INTEGER,
    weight INTEGER,
    timeoutrestart VARCHAR(10),
    defaultrule VARCHAR(128),
    timeoutpriority VARCHAR(128)
);

CREATE TABLE queue_members (
    queue_name VARCHAR(128) NOT NULL,
    interface VARCHAR(128) NOT NULL,
    uniqueid VARCHAR(128) PRIMARY KEY,
    membername VARCHAR(128),
    state_interface VARCHAR(128),
    penalty INTEGER DEFAULT 0,
    paused INTEGER DEFAULT 0,
    -- Advanced Asterisk 20 Member Fields
    wrapuptime INTEGER,
    reason_paused VARCHAR(80),
    ringinuse VARCHAR(10) DEFAULT 'no',
    UNIQUE (queue_name, interface)
);

-- CALL CENTER ANALYTICS (QUEUE LOGS)
CREATE TABLE queue_log (
    id BIGSERIAL PRIMARY KEY,
    time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    callid VARCHAR(80) NOT NULL,
    queuename VARCHAR(128) NOT NULL,
    agent VARCHAR(80) NOT NULL,
    event VARCHAR(32) NOT NULL,
    data1 VARCHAR(128),
    data2 VARCHAR(128),
    data3 VARCHAR(128),
    data4 VARCHAR(128),
    data5 VARCHAR(128)
);

-- ======================================================
-- 4. CDR & CEL (DETAILED REPORTING)
-- ======================================================

-- CDR (Summary level reports)
CREATE TABLE cdr (
    accountcode VARCHAR(20),
    src VARCHAR(80),
    dst VARCHAR(80),
    dcontext VARCHAR(80),
    clid VARCHAR(80),
    channel VARCHAR(80),
    dstchannel VARCHAR(80),
    lastapp VARCHAR(80),
    lastdata VARCHAR(80),
    start TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    answer TIMESTAMP WITHOUT TIME ZONE,
    "end" TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    duration INTEGER,
    billsec INTEGER,
    disposition VARCHAR(45),
    amaflags INTEGER,
    uniqueid VARCHAR(150),
    userfield VARCHAR(255),
    sequence INTEGER
);

-- CEL (Event level reports - Detailed timeline)
CREATE TABLE cel (
    id BIGSERIAL PRIMARY KEY,
    eventtype VARCHAR(30) NOT NULL,
    eventtime TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    cid_name VARCHAR(80),
    cid_num VARCHAR(80),
    cid_ani VARCHAR(80),
    cid_rdnis VARCHAR(80),
    cid_dnid VARCHAR(80),
    exten VARCHAR(80),
    context VARCHAR(80),
    channame VARCHAR(80),
    appname VARCHAR(80),
    appdata VARCHAR(256),
    amaflags INTEGER,
    accountcode VARCHAR(20),
    uniqueid VARCHAR(150) NOT NULL,
    linkedid VARCHAR(150),
    peer VARCHAR(80),
    userdeftype VARCHAR(255),
    extra VARCHAR(512)
);

-- ======================================================
-- 5. VOICEMAIL
-- ======================================================

CREATE TABLE voicemail (
    uniqueid SERIAL PRIMARY KEY,
    context VARCHAR(80) NOT NULL,
    mailbox VARCHAR(80) NOT NULL,
    password VARCHAR(80) NOT NULL,
    fullname VARCHAR(80),
    email VARCHAR(80),
    pager VARCHAR(80),
    tz VARCHAR(10),
    attach VARCHAR(10),
    sayduration VARCHAR(10),
    saydurationm INTEGER,
    sendvoicemail VARCHAR(10),
    review VARCHAR(10),
    tempgreetwarn VARCHAR(10),
    operator VARCHAR(10),
    envelope VARCHAR(10),
    saycid VARCHAR(10),
    volgain FLOAT,
    deletevoicemail VARCHAR(10),
    nextaftercmd VARCHAR(10),
    forcename VARCHAR(10),
    forcegreetings VARCHAR(10),
    hidefromdir VARCHAR(10)
);

-- ======================================================
-- INITIAL SEED DATA
-- ======================================================

INSERT INTO extensions (context, exten, priority, app, appdata) 
VALUES ('from-internal', '1000', 1, 'Answer', '');
INSERT INTO extensions (context, exten, priority, app, appdata) 
VALUES ('from-internal', '1000', 2, 'Playback', 'hello-world');
INSERT INTO extensions (context, exten, priority, app, appdata) 
VALUES ('from-internal', '1000', 3, 'Hangup', '');

INSERT INTO ps_aors (id, max_contacts) VALUES ('1001', 5);
INSERT INTO ps_auths (id, username, password) VALUES ('1001', '1001', '1001pass');
INSERT INTO ps_endpoints (id, transport, aors, auth, context, moh_suggest, allow_transfer, dnd_enabled) 
VALUES ('1001', 'transport-udp', '1001', '1001', 'from-internal', 'default', 'yes', false);
