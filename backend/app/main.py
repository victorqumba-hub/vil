"""Victor Institutional Logic — FastAPI application entry point."""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import init_db

# ── Routers ──────────────────────────────────────────────────────────────────
from app.api.auth import router as auth_router
from app.api.signals import router as signals_router
from app.api.portfolio import router as portfolio_router
from app.api.market import router as market_router
from app.api.reports import router as reports_router
from app.api.nonessentials import router as extras_router
from app.ws.websocket import router as ws_router
from app.api.pipeline import router as pipeline_router
from app.api.broker import router as broker_router
from app.api.broker_integration import router as broker_integration_router
from app.api.admin import router as admin_router
from app.api.regime_attribution import router as regime_attribution_router
from app.api.intelligence import router as intelligence_router

from app.services.orchestrator import run_pipeline
from app.services.pipeline_monitor import monitor
from app.ws.websocket import manager as ws_manager
from app.services.lifecycle import lifecycle_manager
from app.services.SignalLifecycleService import lifecycle_service
from app.db.database import async_session
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    from app.db.seed import seed
    try:
        await seed()
    except Exception as e:
        print(f"Seed failed or already seeded: {e}")
    
    # Start periodic pipeline ingestion (every 2 minutes)
    async def periodic_pipeline_run():
        while True:
            try:
                # 1. Start Scan (OANDA Ingestion)
                # Orchestrator handles its own persistence, ML augmentation, and ws broadcasting
                print("[Main] Starting periodic OANDA ingestion cycle...")
                signals = await run_pipeline() 
                
                # 2. Lifecycle Updates (Transactional block)
                async with async_session() as db:
                    print("[Main] Running lifecycle manager updates...")
                    # update_lifecycles handles SUCCEEDED/FAILED/DROPPED/EXPIRED transitions
                    lifecycle_updates = await lifecycle_manager.update_lifecycles(db)
                    await db.commit()

                    # 3. Broadcast lifecycle updates (status changes)
                    if lifecycle_updates:
                        print(f"[Main] Broadcasting {len(lifecycle_updates)} lifecycle updates...")
                        for update in lifecycle_updates:
                            await ws_manager.broadcast("signals", {
                                "eventType": "SIGNAL_UPDATE",
                                "signalId": str(update["id"]),
                                "status": update["new_status"].value if hasattr(update["new_status"], "value") else update["new_status"],
                                "timestamp": update["timestamp"]
                            })

                # 4. Broadcast latest system status
                await ws_manager.broadcast("signals", {
                    "type": "pipeline_status",
                    "data": monitor.get_status().model_dump()
                })
            except Exception as e:
                print(f"[Main] Error in periodic pipeline: {e}")
                monitor.update_status(
                    status="error", 
                    last_error=str(e), 
                    message="System error in pipeline loop",
                    last_failure_time=datetime.utcnow().isoformat()
                )
                await ws_manager.broadcast("signals", {
                    "type": "pipeline_status",
                    "data": monitor.get_status().model_dump()
                })
            await asyncio.sleep(60)  # 60 seconds (1 minute)

    task = asyncio.create_task(periodic_pipeline_run())
    lifecycle_task = asyncio.create_task(lifecycle_service.start_monitoring())
    
    yield
    task.cancel()
    lifecycle_task.cancel()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include routers ─────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(signals_router)
app.include_router(portfolio_router)
app.include_router(market_router)
app.include_router(reports_router)
app.include_router(extras_router)
app.include_router(ws_router)
app.include_router(pipeline_router)
app.include_router(broker_router)
app.include_router(broker_integration_router)
app.include_router(admin_router)
app.include_router(regime_attribution_router)
app.include_router(intelligence_router)


@app.get("/test-login")
async def test_login_route():
    return {"message": "Test login route works"}


# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/db-check", tags=["system"])
async def db_check():
    """Diagnostic: test database connectivity."""
    from sqlalchemy import text
    from app.db.database import get_engine_url
    url = get_engine_url()
    # Mask password in URL for safety
    safe_url = url.split("@")[-1] if "@" in url else url
    try:
        async with async_session() as session:
            result = await session.execute(text("SELECT 1"))
            val = result.scalar()
            return {"db_status": "connected", "result": val, "engine_host": safe_url}
    except Exception as e:
        return {"db_status": "error", "error": str(e), "engine_host": safe_url}


@app.get("/", tags=["system"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "docs": "/docs",
        "health": "/health",
    }
