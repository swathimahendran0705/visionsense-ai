"""
DeepFace face-recognition service.
Matches faces in an input image against a local known-faces database.

known_faces/
├── Amma/
│   ├── photo1.jpg
│   └── photo2.jpg
├── Appa/
│   └── photo1.jpg
└── Ravi/
    └── photo1.jpg
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import List

# ── Force PyTorch backend — avoids TensorFlow 377MB download ────────────────
os.environ["DEEPFACE_HOME"] = "."
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["CUDA_VISIBLE_DEVICES"] = ""  # CPU only

import numpy as np
# from deepface import DeepFace

from app.core.config import settings
from app.schemas.models import FaceMatch

logger = logging.getLogger(__name__)

KNOWN_FACES_DIR = Path(settings.KNOWN_FACES_DIR)


async def recognise_faces(image: np.ndarray) -> List[FaceMatch]:
    """
    Async wrapper: runs DeepFace in a thread executor.
    Returns matched face records.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run_deepface, image)


def _run_deepface(image: np.ndarray) -> List[FaceMatch]:
    if not KNOWN_FACES_DIR.exists():
        logger.warning(
            "known_faces directory '%s' not found. "
            "Create it with sub-folders per person.",
            KNOWN_FACES_DIR,
        )
        return []

    matches: List[FaceMatch] = []

    try:
        results = DeepFace.find(
            img_path=image,
            db_path=str(KNOWN_FACES_DIR),
            model_name=settings.DEEPFACE_MODEL,
            detector_backend=settings.DEEPFACE_DETECTOR,
            distance_metric=settings.DEEPFACE_DISTANCE_METRIC,
            enforce_detection=False,
            silent=True,
        )
    except Exception as exc:
        logger.error("DeepFace.find() failed: %s", exc)
        return []

    for face_df in results:
        # results is a list of DataFrames, one per face detected
        if face_df.empty:
            continue

        best = face_df.iloc[0]  # closest match first
        distance: float = float(best["distance"])

        if distance > settings.FACE_MATCH_THRESHOLD:
            # No confident match for this face
            continue

        # Derive person name from file path: known_faces/<Name>/photo.jpg
        identity_path: str = best["identity"]
        person_name = Path(identity_path).parent.name

        # Facial region bbox from DeepFace ≥ 0.0.93
        region = best.get("source_x", None)
        if region is not None:
            bbox = [
                int(best.get("source_x", 0)),
                int(best.get("source_y", 0)),
                int(best.get("source_w", 0)),
                int(best.get("source_h", 0)),
            ]
        else:
            bbox = [0, 0, 0, 0]

        confidence = max(0.0, 1.0 - distance)

        matches.append(
            FaceMatch(
                identity=person_name,
                confidence=round(confidence, 3),
                distance=round(distance, 4),
                bbox=bbox,
            )
        )

    logger.info(
        "DeepFace matched %d / %d faces.",
        len(matches),
        len(results),
    )
    return matches