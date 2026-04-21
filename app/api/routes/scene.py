"""
/api/v1/describe-scene  –  YOLO detection + Gemini bilingual description.
"""

import time
import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.models import SceneRequest, SceneResponse
from app.services.yolo_service import detect_objects
from app.services.groq_service import generate_scene_description
from app.utils.image_utils import decode_base64_image

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/describe-scene",
    response_model=SceneResponse,
    summary="Detect objects and generate a bilingual scene description.",
)
async def describe_scene(payload: SceneRequest):
    """
    **Pipeline:**
    1. Decode Base64 image  
    2. Run YOLOv10 object detection  
    3. Call Gemini 1.5 Flash concurrently for English & Tamil descriptions  
    4. Return structured response
    """
    t0 = time.perf_counter()

    # 1. Decode image
    try:
        image = decode_base64_image(payload.image_base64)
    except (ValueError, Exception) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Image decode failed: {exc}",
        )

    # 2. YOLO detection
    try:
        objects = await detect_objects(image)
    except Exception as exc:
        logger.exception("YOLO inference error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Object detection failed: {exc}",
        )

    # 3. Gemini bilingual description (runs both langs concurrently)
    english, tamil = await generate_scene_description(objects, payload.language)

    elapsed_ms = (time.perf_counter() - t0) * 1000
    logger.info("describe-scene completed in %.1f ms", elapsed_ms)

    return SceneResponse(
        detected_objects=objects,
        description_english=english,
        description_tamil=tamil,
        object_count=len(objects),
        processing_time_ms=round(elapsed_ms, 2),
    )