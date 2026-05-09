"""
Face Recognition Service using Groq Vision.
Compares input image against known_faces database using LLaMA vision model.
No TensorFlow, No ONNX required!
"""

import asyncio
import base64
import logging
import os
from pathlib import Path
from typing import List

import numpy as np
from PIL import Image
import io

from groq import Groq
from app.core.config import settings
from app.schemas.models import FaceMatch

logger = logging.getLogger(__name__)

KNOWN_FACES_DIR = Path(settings.KNOWN_FACES_DIR)
_groq_client = Groq(api_key=settings.GROQ_API_KEY)


def _numpy_to_base64(image: np.ndarray) -> str:
    """Convert numpy array to base64 string."""
    pil_img = Image.fromarray(image)
    buffer = io.BytesIO()
    pil_img.save(buffer, format="JPEG", quality=80)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _photo_to_base64(photo_path: Path) -> str:
    """Convert photo file to base64 string."""
    with open(photo_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _get_known_faces() -> dict:
    """Get all known faces from directory."""
    known = {}
    if not KNOWN_FACES_DIR.exists():
        logger.warning("known_faces directory not found!")
        return known

    for person_dir in KNOWN_FACES_DIR.iterdir():
        if not person_dir.is_dir():
            continue
        photos = []
        for ext in ["*.jpg", "*.jpeg", "*.png"]:
            photos.extend(person_dir.glob(ext))
        if photos:
            known[person_dir.name] = photos
            logger.info("Found %d photos for '%s'", len(photos), person_dir.name)

    return known


async def recognise_faces(image: np.ndarray) -> List[FaceMatch]:
    """
    Async wrapper for face recognition using Groq Vision.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run_recognition, image)


def _run_recognition(image: np.ndarray) -> List[FaceMatch]:
    try:
        known_faces = _get_known_faces()

        if not known_faces:
            logger.warning("No known faces found!")
            return []

        input_base64 = _numpy_to_base64(image)
        matches = []

        for person_name, photos in known_faces.items():
            # Use first photo as reference
            ref_photo = photos[0]
            ref_base64 = _photo_to_base64(ref_photo)

            prompt = f"""You are a face recognition system.
Compare these two images:
- Image 1: Reference photo of {person_name}
- Image 2: Input photo to identify

Answer ONLY with one of these:
- "MATCH" if the same person appears in both images
- "NO_MATCH" if different people

Just say MATCH or NO_MATCH, nothing else."""

            response = _groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Reference photo of {person_name}:"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{ref_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": "Input photo to identify:"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{input_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                max_tokens=10,
            )

            result = response.choices[0].message.content.strip().upper()
            logger.info("Groq Vision result for %s: %s", person_name, result)

            if "MATCH" in result and "NO_MATCH" not in result:
                matches.append(
                    FaceMatch(
                        identity=person_name,
                        confidence=0.85,
                        distance=0.15,
                        bbox=[0, 0, 100, 100],
                    )
                )
                logger.info("✅ Matched: %s", person_name)

        return matches

    except Exception as exc:
        logger.error("Face recognition failed: %s", exc)
        return []