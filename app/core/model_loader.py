"""
ModelLoader – loads heavyweight models once at startup.
Shared across all async workers via module-level singletons.
"""

import asyncio
import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Singletons ──────────────────────────────────────────────────────────────
_yolo_model = None


class ModelLoader:

    @classmethod
    async def initialize(cls):
        """Load all models in the background thread pool to avoid blocking the event loop."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, cls._load_yolo)

    @staticmethod
    def _load_yolo():
        global _yolo_model
        from ultralytics import YOLO
        logger.info("Loading YOLOv10 model …")
        _yolo_model = YOLO(settings.YOLO_MODEL_PATH)
        logger.info("YOLOv10 model loaded ✅")

    @classmethod
    async def cleanup(cls):
        global _yolo_model
        _yolo_model = None

    @classmethod
    def get_yolo(cls):
        if _yolo_model is None:
            raise RuntimeError("YOLO model not initialised. Was lifespan() called?")
        return _yolo_model