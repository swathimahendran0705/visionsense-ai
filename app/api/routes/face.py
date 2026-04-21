"""
/api/v1/recognise-face  –  DeepFace recognition against known-faces DB.
"""

import time
import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.models import FaceRequest, FaceResponse
from app.services.face_service import recognise_faces
from app.utils.image_utils import decode_base64_image

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/recognise-face",
    response_model=FaceResponse,
    summary="Identify faces in image against the known-faces database.",
)
async def recognise_face(payload: FaceRequest):
    """
    **Pipeline:**
    1. Decode Base64 image  
    2. Run DeepFace.find() against `known_faces/` directory  
    3. Return matches with confidence scores

    **Setup:**  
    Create `known_faces/<PersonName>/` directories and add reference photos.
    """
    t0 = time.perf_counter()

    try:
        image = decode_base64_image(payload.image_base64)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Image decode failed: {exc}",
        )

    try:
        matches = await recognise_faces(image)
    except Exception as exc:
        logger.exception("DeepFace recognition error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Face recognition failed: {exc}",
        )

    elapsed_ms = (time.perf_counter() - t0) * 1000
    logger.info("recognise-face completed in %.1f ms", elapsed_ms)

    # Count faces in the frame vs matched
    faces_detected = max(len(matches), 1)  # DeepFace groups results per face
    unrecognised = max(0, faces_detected - len(matches))

    return FaceResponse(
        faces_detected=faces_detected,
        matches=matches,
        unrecognised_faces=unrecognised,
        processing_time_ms=round(elapsed_ms, 2),
    )