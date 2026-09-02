"""Standalone TTS sanity-check: synthesize English and Hindi strings via Rime.

Usage:
    set RIME_API_KEY=your_key_here
    python scripts/test_tts.py
"""

from __future__ import annotations

import os
import sys

# Add project root to path so we can import emi_agent
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402
load_dotenv()

from emi_agent.templates import reminder_message
from emi_agent.tts import synthesize_speech  # noqa: E402


def main() -> None:
    # Test 1: Hand-verbalized English
    en_verbalized = "Your EMI of twelve thousand five hundred rupees is due on 15th September."
    print(f"Synthesizing English (verbalized) -> test_en_verbalized.wav...")
    synthesize_speech(text=en_verbalized, lang="en", output_path="test_en_verbalized.wav")

    # Test 2: Actual template output (contains raw numerals and currency symbols)
    en_template = reminder_message(12500.00, "2026-09-15", "4521")
    print(f"Synthesizing English (template)   -> test_en_template.wav...")
    print(f"  String: {en_template.encode('ascii', 'backslashreplace').decode('ascii')}")
    synthesize_speech(text=en_template, lang="en", output_path="test_en_template.wav")

    # Test 3: Pure Hindi script
    hi_pure = "आपकी बारह हज़ार पांच सौ रुपये की EMI पंद्रह सितम्बर को देय है।"
    print(f"\nSynthesizing Hindi (pure)         -> test_hi_pure.wav...")
    synthesize_speech(text=hi_pure, lang="hi", output_path="test_hi_pure.wav")

    # Test 4: Code-switched Hinglish with spoken currency format
    from emi_agent.templates import to_spoken_currency_hindi
    formatted_amt = to_spoken_currency_hindi(12500.00)
    hi_mixed = f"Sir aapka EMI {formatted_amt} tha, 5 tarikh ko due hai"
    print(f"Synthesizing Hindi (mixed)        -> test_hi_mixed.wav...")
    print(f"  String: {hi_mixed.encode('ascii', 'backslashreplace').decode('ascii')}")
    synthesize_speech(text=hi_mixed, lang="hi", output_path="test_hi_mixed.wav")
    
    print("\nAll 4 TTS files generated successfully.")


if __name__ == "__main__":
    main()
