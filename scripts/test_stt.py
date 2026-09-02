"""Standalone STT sanity-check: record ~15s from mic, transcribe via Deepgram.

Usage:
    set DEEPGRAM_API_KEY=your_key_here
    python scripts/test_stt.py

Test phrase (Hindi-English code-switched):
    "Sir aapka EMI ₹12,500 tha, 5 tarikh ko due hai"

NOTE on model config:
    We use model="nova-3" with language="multi". This is the correct
    Deepgram setting for Hindi-English code-switching (Hinglish).
    Nova-3 multilingual handles intra-sentential mixing natively.
    Do NOT use language="hi" or language="en" alone — those mono-lingual
    modes will butcher the other language's segments.
"""

from __future__ import annotations

import io
import sys
import time
import wave

import sounddevice as sd  # pip install sounddevice

# Add project root to path so we can import emi_agent
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402
load_dotenv()

from emi_agent.stt import transcribe_audio  # noqa: E402

SAMPLE_RATE = 16000  # 16 kHz — standard for speech
CHANNELS = 1
DURATION_SECONDS = 15


def record_to_wav(duration: int = DURATION_SECONDS) -> bytes:
    """Record from default mic and return WAV bytes."""
    # Countdown so there's no ambiguity about when to speak
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    print("\a🎙️  Recording — speak now!")
    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
    )
    sd.wait()
    print(f"✅ Recording done ({duration}s captured).")

    # Pack into WAV in-memory
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    return buf.getvalue()


def main() -> None:
    wav_bytes = record_to_wav()
    print(f"Audio size: {len(wav_bytes)} bytes")
    print("Sending to Deepgram...")
    transcript = transcribe_audio(wav_bytes)
    print(f"\nTranscript: {transcript!r}")


if __name__ == "__main__":
    main()
