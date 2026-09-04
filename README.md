# EMI Voice Agent

A voice agent that calls a loan customer, confirms their identity, reads out their EMI reminder, and handles their spoken reply. Built for the DataForge hackathon by KGP Data Analytics Society.

The core idea: a text or SMS reminder cannot confirm who picked up the phone, cannot handle someone disputing the charge on the spot, and cannot read out numbers in a way the customer trusts. This only works as a voice product.

## Setup

1. Clone the repo and go into the folder.
2. Create a virtual environment and activate it.
3. Install dependencies:

```
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and fill in your own keys:

```
DEEPGRAM_API_KEY=your_key_here
RIME_API_KEY=your_key_here
```

Get a Deepgram key from console.deepgram.com. Get a Rime key from app.rime.ai/tokens.

5. Run the interactive call:

```
python main.py
```

This uses a default synthetic customer. To test with a different one, change the customer_id passed in main.py, or pass it as an argument if you added CLI support.

## Architecture

```
Microphone (local, 5s window)
   -> Deepgram STT (transcribes what the customer said)
   -> State machine (decides what state the call is in and what to say next)
   -> Rime TTS (turns the agent's reply into speech)
   -> Playback (speaks it out loud)
```

The state machine has four real states: confirm identity, deliver the reminder, handle the customer's response, and close the call. Customer responses branch into will pay, dispute, reschedule, or unclear. Every state change is logged with a timestamp, which is how we track what actually happened in a call.

Customer data (name, EMI amount, due date, account number) comes from a small local fixture file, not a live database. This is synthetic test data, not real customer information.

## Third-party services

**Deepgram** - speech to text.
- Model: `nova-3`
- Language: `multi` (this is what lets it handle Hindi-English code-switching in one pass, instead of needing separate routing)
- Mode: pre-recorded (record locally, send the file, get the transcript back)
- SDK: `deepgram-sdk`, pinned to `~=7.8` because the API changed shape between major versions and an unpinned version can silently break

**Rime** - text to speech.
- Model: `coda`
- Speaker for English: `astra`
- Speaker for Hindi: `nadi` (confirmed from Rime's live voice catalog, not guessed - only 2 of the 253 Coda voices support Hindi, so this had to be checked directly)
- Language: `en` for English replies, `hi` for Hindi and code-switched replies
- Endpoint: `https://users.rime.ai/v1/rime-tts`
- Transport: plain HTTPS POST, JSON body, no streaming
- Audio format returned: wav

Both services are called with the API key read from environment variables. Nothing is hardcoded in the source.

## Known limitations

- Deepgram sometimes mishears customer replies. In one real test call, "I have already paid" came back as "I have already painted." This is a speech-to-text limitation, not something we can fix from the Rime side.
- Our intent classifier is a simple keyword matcher, not an LLM. It has no rule for "already paid" as its own category, so that kind of reply currently falls through to unclear and the call ends with a callback instead of correctly logging it as a dispute. This is a known, open gap.
- Rime reads raw currency formatting (like ₹12,500.00) cleanly in English, but the same raw formatting sounds confused in Hindi or code-switched sentences. We tried converting the amount to a spoken form before sending it to Rime for the Hindi path, which helped, but did not fully fix it. See RIME_EVIDENCE.md for the actual before and after clips.
- We only tested Hindi-English code-switching written in Roman script (Hinglish). We did not test the same sentence written in Devanagari, so we don't know how that version sounds.
- The recording window for the microphone is a fixed 5 seconds. A customer speaking slowly or in a long sentence can get cut off.

## Failure behavior

If the customer's response comes back as unclear (either because they said something unclear, or because the transcript came out garbled), the agent re-prompts once. If it's still unclear on the second try, the call ends gracefully with a message saying the agent will call back, instead of guessing or getting stuck.

## Reproducing our acceptance test

See `RIME_EVIDENCE.md` for the full pronunciation test, including exact steps and the audio files it produces.