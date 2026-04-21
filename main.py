"""
VisionSense AI - Zero-UI Backend for Visually Impaired Users
Production-ready FastAPI microservice
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.routes import scene, face
from app.core.config import settings
from app.core.model_loader import ModelLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle manager."""
    logger.info("🚀 VisionSense AI starting up …")
    await ModelLoader.initialize()
    logger.info("✅ All models loaded and ready.")
    yield
    logger.info("🛑 VisionSense AI shutting down …")
    await ModelLoader.cleanup()


app = FastAPI(
    title="VisionSense AI",
    description="Zero-UI real-time scene understanding for visually impaired users.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middleware ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)

# ── Routers ─────────────────────────────────────────────────────────────────
app.include_router(scene.router, prefix="/api/v1", tags=["Scene Understanding"])
app.include_router(face.router,  prefix="/api/v1", tags=["Face Recognition"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "VisionSense AI", "version": "1.0.0"}