from fastapi import FastAPI
from routers import extensions, trunks, dialplan, reports, system, voicemail, queues, monitoring, blacklist, time_conditions, dashboard, hunt_groups

app = FastAPI(title="GadgetPBX Management API", version="1.0.0")

# Include Modular Routers
app.include_router(extensions.router)
app.include_router(trunks.router)
app.include_router(dialplan.router)
app.include_router(reports.router)
app.include_router(system.router)
app.include_router(voicemail.router)
app.include_router(queues.router)
app.include_router(monitoring.router)
app.include_router(blacklist.router)
app.include_router(time_conditions.router)
app.include_router(dashboard.router)
app.include_router(hunt_groups.router)

@app.get("/")
def root():
    return {"message": "Welcome to GadgetPBX Management API", "status": "online"}
