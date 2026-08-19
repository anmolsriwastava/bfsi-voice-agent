# RIME_EVIDENCE.md

## The Claim

Our product is an EMI reminder voice agent for loan customers. It calls a customer, confirms who they are, reads out their loan details, and listens to their reply.

The hard voice problem we are solving is pronunciation and controlled delivery. Loan reminders are full of things that are easy to say wrong: currency amounts, account numbers, dates, and mixed Hindi-English sentences. If the agent reads these badly, the customer will not trust it or understand it, and the whole product fails. So we tested this directly instead of assuming Rime would just handle it.

Our claim is simple: Rime reads raw currency and date formatting correctly when the sentence is in English, but the same raw formatting does not read well once the sentence switches into Hindi or mixes Hindi and English together. We found this, tried to fix it, and are reporting the real result below, including the part that is still not fully fixed.

## Acceptance Test

We used one fixed loan reminder as the test case:

- Account ending in 4521
- EMI amount ₹12,500.00
- Due date 15th September 2026

We rendered this information through Rime in four different ways and listened to each one:

1. **Plain English, hand written out** ("twelve thousand five hundred rupees") - this is the easy version, used only as a baseline.
2. **Real English template output** - the actual text our app generates, with raw formatting: "Your EMI of ₹12,500.00 is due on 15th September 2026."
3. **Pure Hindi** - the same kind of sentence written fully in Hindi script.
4. **Code-switched Hindi-English (Hinglish)** - a natural mixed sentence a real agent might say, written in Roman script: "Sir aapka EMI ₹12,500 tha, 5 tarikh ko due hai."

We listened to each file ourselves and wrote down what we heard, instead of guessing or trusting the API to "just work."

## Procedure

Speaker used: `astra` for English, `nadi` for Hindi (Coda model, confirmed from Rime's live voice catalog, not guessed).

Steps to reproduce:

```
python scripts/test_tts.py
```

This script generates four labeled wav files:
- `test_en_verbalized.wav`
- `test_en_template.wav`
- `test_hi_pure.wav`
- `test_hi_mixed.wav`

Open each file and listen. No special tools needed.

## Result

- Plain English (baseline): clean, no issues.
- Real English template output with raw ₹ symbol and date: also clean. Rime handled the currency symbol and the ordinal date correctly without needing us to spell anything out.
- Pure Hindi: understandable, though the pacing felt a little fast.
- Code-switched Hindi-English with the raw ₹ symbol: this is where it broke. The delivery sounded confused around the currency part. The ₹ symbol was not skipped, but it was not read naturally either, it just sounded off compared to the English-only version.

We then tried a fix: instead of sending the raw ₹12,500 symbol into the Hindi-tagged sentence, we converted it to a spoken form first, something like "12,500 rupaye" with no symbol. We regenerated the mixed Hindi-English clip with this change.

Result after the fix: better than before, but still not fully clean. It is an improvement, not a full solution.

## Limitations

- The ₹ symbol works fine in English-only speech through Rime, but does not fully work in Hindi or code-switched speech, even after converting it to a spoken form. This needs more tuning than we had time for.
- Our speech-to-text step (Deepgram, nova-3, multi language) occasionally misheard customer replies. In one real test run, "I have already paid" was transcribed as "I have already painted." This is a real STT limitation, not something we can fix on the Rime side.

