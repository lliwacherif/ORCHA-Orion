# app/main.py
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router as v1_router
from app.api.v1.auth import router as auth_router
from app.utils.logging import TraceIdMiddleware, logger
from app.config import settings
from app.tasks.pulse_scheduler import pulse_scheduler_loop, pulse_checker_loop
import redis.asyncio as redis

app = FastAPI(title="ORCHA - Orchestrator")

# Background task handles for pulse scheduler
pulse_scheduler_task = None
pulse_checker_task = None

# CORS - Allow frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TraceIdMiddleware)
app.include_router(v1_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])

from app.api.v1.folders import router as folders_router
app.include_router(folders_router, prefix="/api/v1/folders", tags=["Folders"])

@app.on_event("startup")
async def startup_event():
    global pulse_scheduler_task, pulse_checker_task
    
    try:
        app.state.redis = redis.from_url(settings.REDIS_URL)
        # simple ping to verify connectivity
        await app.state.redis.ping()
        logger.info("redis connected", extra={"trace_id": "startup"})
    except Exception:
        app.state.redis = None
        logger.info("redis not available, continuing without it", extra={"trace_id": "startup"})
    
    # Start pulse scheduler background tasks
    try:
        pulse_scheduler_task = asyncio.create_task(pulse_scheduler_loop())
        logger.info("✅ Pulse scheduler started", extra={"trace_id": "startup"})
        
        pulse_checker_task = asyncio.create_task(pulse_checker_loop())
        logger.info("✅ Pulse checker started", extra={"trace_id": "startup"})
    except Exception as e:
        logger.error(f"Failed to start pulse scheduler: {e}", extra={"trace_id": "startup"})

@app.on_event("shutdown")
async def shutdown_event():
    global pulse_scheduler_task, pulse_checker_task
    
    # Cancel pulse scheduler tasks
    if pulse_scheduler_task:
        pulse_scheduler_task.cancel()
        logger.info("Pulse scheduler stopped", extra={"trace_id": "shutdown"})
    
    if pulse_checker_task:
        pulse_checker_task.cancel()
        logger.info("Pulse checker stopped", extra={"trace_id": "shutdown"})
    
    try:
        if getattr(app.state, "redis", None) is not None:
            await app.state.redis.close()
    except Exception:
        pass
    logger.info("shutdown complete", extra={"trace_id": "shutdown"})
