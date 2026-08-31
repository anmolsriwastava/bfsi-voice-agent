"""Interactive demo runner for the EMI voice agent.

Run with: python main.py

Creates a sample call context and loops the state machine,
recording mic audio, transcribing it, and playing TTS replies.
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
import time
import wave

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv

load_dotenv()

from emi_agent.intent import classify_identity, classify_intent, compute_reschedule_date
from emi_agent.logger import dump_log
from emi_agent.models import CallContext, CallState
from emi_agent.state_machine import run_step
from emi_agent.stt import transcribe_audio
from emi_agent.tts import synthesize_speech

SAMPLE_RATE = 16000
CHANNELS = 1
RECORD_SECONDS = 5  # Fixed short duration for snappier conversation


def record_to_wav(duration: int = RECORD_SECONDS) -> bytes:
    print(f"\n\a🎙️  Listening ({duration}s)... speak now!")
    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
    )
    sd.wait()
    
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    return buf.getvalue()


def play_wav(filepath: str) -> None:
    with wave.open(filepath, "rb") as wf:
        samplerate = wf.getframerate()
        channels = wf.getnchannels()
        audio_data = wf.readframes(wf.getnframes())
        
    audio_np = np.frombuffer(audio_data, dtype=np.int16)
    if channels > 1:
        audio_np = audio_np.reshape(-1, channels)
        
    sd.play(audio_np, samplerate=samplerate)
    sd.wait()


def is_hindi(text: str) -> bool:
    """Detect if text contains Devanagari characters or common Hinglish words."""
    if not text:
        return False
        
    if re.search(r'[\u0900-\u097F]', text):
        return True
    
    hinglish_keywords = {"rupaye", "tha", "hai", "tarikh", "aapka", "sir"}
    words = set(text.lower().replace(",", "").replace(".", "").split())
    if words.intersection(hinglish_keywords):
        return True
        
    return False


def speak_reply(reply_text: str) -> None:
    print(f"\nAgent: {reply_text}")
    lang = "hi" if is_hindi(reply_text) else "en"
    output_wav = "agent_reply.wav"
    
    print("  (Synthesizing speech...)")
    synthesize_speech(reply_text, lang=lang, output_path=output_wav)
    print("  (Playing...)")
    play_wav(output_wav)


def main() -> None:
    if not os.environ.get("DEEPGRAM_API_KEY") or not os.environ.get("RIME_API_KEY"):
        print("Error: Missing DEEPGRAM_API_KEY or RIME_API_KEY in .env")
        sys.exit(1)

    ctx = CallContext(
        customer_name="Rahul Sharma",
        emi_amount=12500.00,
        due_date="2026-09-15",
        account_last4="4521",
        classify_identity=classify_identity,
        classify_intent=classify_intent,
        compute_reschedule_date=compute_reschedule_date,
    )

    print("=" * 60)
    print("  EMI Voice Agent \u2014 End-to-End Voice Demo")
    print("=" * 60)
    print("Press Ctrl+C to exit at any time.\n")

    # Opening turn (no user input)
    reply = run_step(ctx)
    if reply:
        speak_reply(reply)

    while ctx.state != CallState.ENDED:
        # States that auto-advance (no user input needed)
        if ctx.state in {CallState.REMINDER_DELIVERY, CallState.CLOSE}:
            reply = run_step(ctx)
            if reply:
                speak_reply(reply)
            continue

        # Get user input (audio)
        try:
            wav_bytes = record_to_wav(RECORD_SECONDS)
        except (KeyboardInterrupt, EOFError):
            print("\n[Call terminated by user]")
            break
            
        print("  (Transcribing...)")
        user_input = transcribe_audio(wav_bytes)
        print(f"You:   {user_input}")
        
        reply = run_step(ctx, user_input=user_input)
        if reply:
            speak_reply(reply)

    # Dump transition log
    print()
    print("=" * 60)
    print("  Transition Log")
    print("=" * 60)
    log = dump_log(ctx)
    print(json.dumps(log, indent=2))


if __name__ == "__main__":
    main()
