"""
YOLOv10 object-detection service.
Runs inference in a thread-pool executor to avoid blocking the event loop.
"""

import asyncio
import logging
from typing import List

import numpy as np
from PIL import Image as PILImage

from app.core.config import settings
from app.core.model_loader import ModelLoader
from app.schemas.models import DetectedObject

logger = logging.getLogger(__name__)


async def detect_objects(image: np.ndarray) -> List[DetectedObject]:
    """
    Async wrapper: runs YOLO in a thread executor so the event loop stays free.
    Returns a list of DetectedObject instances.
    """
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, _run_yolo, image)
    return results


def _run_yolo(image: np.ndarray) -> List[DetectedObject]:
    model = ModelLoader.get_yolo()

    # Convert numpy array → PIL Image to bypass numpy conflict
    pil_img = PILImage.fromarray(image)

    predictions = model.predict(
        source=pil_img,
        conf=settings.YOLO_CONFIDENCE,
        device=settings.YOLO_DEVICE,
        verbose=False,
    )

    detected: List[DetectedObject] = []
    seen_labels: set = set()

    for result in predictions:
        for box in result.boxes:
            label: str = result.names[int(box.cls[0])]
            confidence: float = float(box.conf[0])
            bbox: List[float] = box.xyxy[0].tolist()  # [x1, y1, x2, y2]

            detected.append(
                DetectedObject(label=label, confidence=confidence, bbox=bbox)
            )
            seen_labels.add(label)

    logger.info("YOLO detected %d objects: %s", len(detected), list(seen_labels))
    return detected