"""
Image utility helpers for VisionSense AI.
"""

import base64
import io
import logging

import numpy as np
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_BYTES = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024


def decode_base64_image(b64_string: str) -> np.ndarray:
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]

    raw = base64.b64decode(b64_string)

    if len(raw) > MAX_BYTES:
        raise ValueError(
            f"Image size {len(raw) / 1024 / 1024:.1f} MB exceeds "
            f"limit of {settings.MAX_IMAGE_SIZE_MB} MB."
        )

    pil_image = Image.open(io.BytesIO(raw)).convert("RGB")
    return np.array(pil_image)


def numpy_to_pil(array: np.ndarray) -> Image.Image:
    return Image.fromarray(array)