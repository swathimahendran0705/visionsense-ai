"""
VisionSense AI – centralised configuration.
All secrets come from environment variables / .env file.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Gemini ────────────────────────────────────────────────────────────
   # ── Groq ──────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = "YOUR_GROQ_API_KEY"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"   # or "llama3-8b-8192" for even faster
    # ── YOLO ─────────────────────────────────────────────────────────────
    YOLO_MODEL_PATH: str = "yolov10n.pt"          # nano for speed; swap for yolov10s/m
    YOLO_CONFIDENCE: float = 0.25
    YOLO_DEVICE: str = "cpu"                       # "0" for GPU

    # ── DeepFace ─────────────────────────────────────────────────────────
    KNOWN_FACES_DIR: str = "known_faces"           # folder with sub-dirs per person
    DEEPFACE_MODEL: str = "VGG-Face"               # Facenet512 | ArcFace | VGG-Face
    DEEPFACE_DETECTOR: str = "retinaface"
    DEEPFACE_DISTANCE_METRIC: str = "cosine"
    FACE_MATCH_THRESHOLD: float = 0.40

    # ── API ───────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = ["*"]
    MAX_IMAGE_SIZE_MB: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()