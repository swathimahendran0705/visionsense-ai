"""
Groq LLaMA scene-description service.
Ultra-fast inference for bilingual scene descriptions.
"""

import asyncio
import logging
from typing import List, Tuple

from groq import Groq

from app.core.config import settings
from app.schemas.models import DetectedObject

logger = logging.getLogger(__name__)

_groq_client = Groq(api_key=settings.GROQ_API_KEY)

# ── Prompt templates ────────────────────────────────────────────────────────

_ENGLISH_PROMPT = """You are an AI assistant helping visually impaired people understand their surroundings.
Based on the following detected objects: {objects}

Generate a concise, natural, human-friendly scene description (2-3 sentences).
Focus on spatial relationships and anything safety-critical (vehicles, stairs, doors).
Be warm, clear, avoid technical jargon.
Respond ONLY with the scene description."""

_TAMIL_PROMPT = """நீங்கள் பார்வையற்ற நபர்களுக்கு சுற்றுச்சூழலை புரிந்துகொள்ள உதவும் AI உதவியாளர்.
கண்டறியப்பட்ட பொருள்கள்: {objects}

இந்த காட்சியை இயற்கையான தமிழில் 2-3 வாக்கியங்களில் விவரிக்கவும்.
பாதுகாப்பு தொடர்பான விஷயங்களில் கவனம் செலுத்தவும்.
விவரணை மட்டும் எழுதவும்."""


async def generate_scene_description(
    objects: List[DetectedObject],
    language: str = "both",
) -> Tuple[str | None, str | None]:

    if not objects:
        empty_en = "The scene appears to be empty or no objects were detected."
        empty_ta = "காட்சியில் எந்த பொருளும் கண்டறியப்படவில்லை."
        return (
            empty_en if language in ("english", "both") else None,
            empty_ta if language in ("tamil", "both") else None,
        )

    object_list = ", ".join(
        f"{o.label} ({o.confidence:.0%})" for o in objects
    )

    tasks = []
    if language in ("english", "both"):
        tasks.append(_call_groq(_ENGLISH_PROMPT.format(objects=object_list)))
    else:
        tasks.append(asyncio.sleep(0, result=None))

    if language in ("tamil", "both"):
        tasks.append(_call_groq(_TAMIL_PROMPT.format(objects=object_list)))
    else:
        tasks.append(asyncio.sleep(0, result=None))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    english = _safe(results[0]) if language in ("english", "both") else None
    tamil   = _safe(results[1]) if language in ("tamil",   "both") else None

    return english, tamil


async def _call_groq(prompt: str) -> str:
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: _groq_client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        ),
    )
    return response.choices[0].message.content.strip()


def _safe(result) -> str | None:
    if isinstance(result, Exception):
        logger.error("Groq call failed: %s", result)
        return "Description unavailable at this time."
    return result