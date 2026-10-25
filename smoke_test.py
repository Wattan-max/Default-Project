#!/usr/bin/env python3
"""Quick smoke test for the Sarvam endpoints Vaani uses.

    python smoke_test.py                  # uses SARVAM_API_KEY from .env
    python smoke_test.py sk_xxx           # or pass the key explicitly
    python smoke_test.py sk_xxx note.webm # also test speech-to-text

Makes three small paid API calls (chat, translate, TTS) plus one optional STT
call. Never prints the key.
"""

from __future__ import annotations

import sys

import pipeline
import server


def main() -> int:
    server.load_env()
    key = server.env_key()
    args = [arg for arg in sys.argv[1:]]
    if args and args[0].startswith("sk_"):
        key = args.pop(0)
    audio_path = args[0] if args else ""

    if not key:
        print("No API key found. Add SARVAM_API_KEY to .env or pass it as the first argument.")
        print("The app still runs in demo mode without one.")
        return 1

    try:
        print("1/4  chat (sarvam-105b)…")
        raw = server.chat(
            [
                {"role": "system", "content": "Return only a JSON object."},
                {"role": "user", "content": 'Reply with {"ok": true} and nothing else.'},
            ],
            key,
        )
        parsed = pipeline.parse_json_object(raw)
        print(f"     ok: {parsed}")

        print("2/4  translate (mayura:v1)…")
        translated = server.translate(
            "कल इलेक्ट्रीशियन को कॉल करना है और सोमवार तक किराया देना है।",
            "hi-IN",
            "en-IN",
            key,
        )
        print(f"     ok: {translated['translated_text'][:120]}")

        print("3/4  text-to-speech (bulbul:v2)…")
        audio = server.speak("नमस्ते, आपका प्लान तैयार है।", "hi-IN", key)
        if not audio.startswith(b"RIFF"):
            raise RuntimeError("TTS returned bytes that are not a WAV file.")
        print(f"     ok: {len(audio):,} bytes of WAV")

        if audio_path:
            print(f"4/4  speech-to-text (saaras:v4) — {audio_path}")
            with open(audio_path, "rb") as handle:
                data = handle.read()
            result = server.transcribe(data, audio_path.split("/")[-1], "audio/webm", key, "unknown")
            print(f"     ok: [{result['language_code']}] {result['transcript'][:160]}")
        else:
            print("4/4  speech-to-text skipped (pass an audio file to test it)")

    except server.ApiError as exc:
        print(f"\nFAILED: {exc.message}")
        if exc.hint:
            print(f"HINT:   {exc.hint}")
        return 1
    except Exception as exc:  # noqa: BLE001 - this is a diagnostic script
        print(f"\nFAILED: {exc!r}")
        return 1

    print("\nAll checks passed. Live mode is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
