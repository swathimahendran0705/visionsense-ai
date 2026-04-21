"""
Pydantic schemas for VisionSense AI API.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ── Shared ──────────────────────────────────────────────────────────────────

class DetectedObject(BaseModel):
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: List[float] = Field(..., description="[x1, y1, x2, y2] in pixel coords")


# ── Scene Understanding ─────────────────────────────────────────────────────

class SceneRequest(BaseModel):
    image_base64: str = Field(..., description="Base64-encoded image (JPEG/PNG)")
    language: str = Field(default="both", description="'tamil' | 'english' | 'both'")


class SceneResponse(BaseModel):
    detected_objects: List[DetectedObject]
    description_english: Optional[str] = None
    description_tamil: Optional[str] = None
    object_count: int
    processing_time_ms: float


# ── Face Recognition ────────────────────────────────────────────────────────

class FaceMatch(BaseModel):
    identity: str                          # Name of matched person
    confidence: float = Field(..., ge=0.0, le=1.0)
    distance: float
    bbox: List[int] = Field(..., description="[x, y, w, h]")


class FaceRequest(BaseModel):
    image_base64: str = Field(..., description="Base64-encoded image (JPEG/PNG)")


class FaceResponse(BaseModel):
    faces_detected: int
    matches: List[FaceMatch]
    unrecognised_faces: int
    processing_time_ms: float