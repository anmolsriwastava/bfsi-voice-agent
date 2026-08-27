"""Speech-to-text via Deepgram's pre-recorded API (v7 SDK).

Standalone module — not wired into the state machine yet.
"""

from __future__ import annotations

import os

from deepgram import DeepgramClient


def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe audio bytes using Deepgram's pre-recorded API.

    Args:
        audio_bytes: Raw audio data (WAV format recommended).

    Returns:
        Transcript string, or empty string if no speech detected.

    Raises:
        RuntimeError: If DEEPGRAM_API_KEY env var is not set.
    """
    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DEEPGRAM_API_KEY environment variable is not set. "
            "See .env.example for setup."
        )

    client = DeepgramClient(api_key=api_key)

    # NOTE: language="multi" + model="nova-3" is the correct config for
    # Hindi-English code-switching (Hinglish). Nova-3 with language=multi
    # handles intra-sentential mixing natively — no routing or separate
    # language detection needed.
    response = client.listen.v1.media.transcribe_file(
        request=audio_bytes,
        model="nova-3",
        language="multi",
        smart_format=True,
    )

    # ponytail: no retry/backoff — add if flaky in production
    channels = response.results.channels
    if not channels or not channels[0].alternatives:
        return ""
    return channels[0].alternatives[0].transcript

