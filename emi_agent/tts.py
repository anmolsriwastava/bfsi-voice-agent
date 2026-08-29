"""Text-to-speech via Rime's REST API.

Standalone module — not wired into the state machine yet.
"""

from __future__ import annotations

import os

import requests


def synthesize_speech(text: str, lang: str = "en", output_path: str = "output.wav") -> None:
    """Synthesize speech using Rime's REST API and save to a WAV file.

    Args:
        text: The text to synthesize.
        lang: Language code ("en" or "hi"). Defaults to "en".
        output_path: Path to save the resulting WAV file.

    Raises:
        RuntimeError: If RIME_API_KEY env var is not set, or API request fails.
    """
    api_key = os.environ.get("RIME_API_KEY")
    if not api_key:
        raise RuntimeError(
            "RIME_API_KEY environment variable is not set. "
            "See .env.example for setup."
        )

    # Defaults based on Rime's Coda catalog
    # "astra" is confirmed English-capable
    # "nadi" is one of only two confirmed Hindi-capable Coda voices
    speaker = "nadi" if lang == "hi" else "astra"

    url = "https://users.rime.ai/v1/rime-tts"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "audio/wav",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "speaker": speaker,
        "modelId": "coda",
        "lang": lang,
    }

    response = requests.post(url, headers=headers, json=payload, stream=True)
    
    if not response.ok:
        raise RuntimeError(f"Rime API error: {response.status_code} - {response.text}")

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
