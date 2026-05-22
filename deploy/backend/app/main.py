import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import agent, agent_chat, alerts, auth, configs, credentials, dashboard, devices, ipam, links, monitor, phase5, syslog_viewer, tasks, vlans
from .services.scheduler import init_scheduler


def create_app() -> FastAPI:
    app = FastAPI(title="NetOps API", version="1.0.0")

    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Public routes
    app.include_router(agent.router)
    app.include_router(agent_chat.router)
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

    # Protected routes
    app.include_router(credentials.router, prefix="/api/credentials", tags=["credentials"])
    app.include_router(devices.router, prefix="/api/devices", tags=["devices"])
    app.include_router(configs.router, prefix="/api/configs", tags=["configs"])
    app.include_router(monitor.router, prefix="/api/monitor", tags=["monitor"])
    app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
    app.include_router(ipam.router)
    app.include_router(links.router)
    app.include_router(vlans.router)
    app.include_router(alerts.router)
    app.include_router(syslog_viewer.router)
    app.include_router(phase5.router)
    app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])

    @app.on_event("startup")
    def on_start() -> None:
        init_db()
        try:
            init_scheduler()
        except Exception:
            pass
        try:
            from .services.syslog_server import syslog_server
            import asyncio
            asyncio.ensure_future(syslog_server.start())
        except Exception:
            pass

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
