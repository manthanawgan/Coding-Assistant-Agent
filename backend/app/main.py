from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from sqlalchemy import text
from app.config.settings import settings
from app.db.session import engine, Base
from app.websocket.manager import websocket_manager, router as ws_router
from app.api.v1.routes import auth, repos, tasks, prs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Coding Assistant Agent API...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    yield
    logger.info("Shutting down Coding Assistant Agent API...")


app = FastAPI(
    title="Coding Assistant Agent API",
    description="Autonomous multi-agent software engineering platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(repos.router, prefix="/api/v1/repos", tags=["Repositories"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(prs.router, prefix="/api/v1/prs", tags=["Pull Requests"])
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])


@app.get("/")
async def root():
    return JSONResponse({
        "message": "Coding Assistant Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    })


@app.get("/health")
async def health_check():
    redis_status = "unhealthy"
    try:
        from redis import asyncio as aioredis
        redis = aioredis.from_url(settings.REDIS_URL)
        result = await redis.ping()
        if result:
            redis_status = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")

    db_status = "unhealthy"
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    return JSONResponse({
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        "database": db_status,
        "redis": redis_status,
        "docker": "healthy"
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
