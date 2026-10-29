#!/usr/bin/env python3
"""Vaani — voice-to-action assistant for Indian languages.

A dependency-free Python server that wires Sarvam's speech-to-text, chat and
text-to-speech APIs into a small, demo-friendly UI.

    python server.py            # http://127.0.0.1:8000
    python server.py --no-open  # don't open a browser

Set SARVAM_API_KEY in .env (or paste a key in the UI). Without a key the app
runs in clearly-labelled demo mode.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import socket
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pipeline

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
API_BASE = os.environ.get("SARVAM_BASE_URL", "https://api.sarvam.ai").rstrip("/")
MAX_BODY = 26 * 1024 * 1024  # 26 MB, a little above Sarvam's audio limit
TTS_LANGUAGES = {"bn-IN", "en-IN", "gu-IN", "hi-IN", "kn-IN", "ml-IN", "mr-IN",
                 "od-IN", "pa-IN", "ta-IN", "te-IN"}

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
    ".webmanifest": "application/manifest+json",
}


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400, hint: str = ""):
        super().__init__(message)
        self.message = message
        self.status = status
        self.hint = hint


class SarvamError(ApiError):
    pass


# --- config ------------------------------------------------------------------

def load_env(path: Path = ROOT / ".env") -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env_key() -> str:
    return os.environ.get("SARVAM_API_KEY", "").strip()


# --- Sarvam client -----------------------------------------------------------

def _call(
    path: str,
    body: bytes,
    content_type: str,
    key: str,
    timeout: int = 120,
    extra_headers: dict[str, str] | None = None,
) -> dict:
    url = API_BASE + path
    headers = {
        "api-subscription-key": key,
        "Content-Type": content_type,
        "Accept": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    last_error: Exception | None = None
    for attempt in range(2):
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(
                request, timeout=timeout, context=ssl.create_default_context()
            ) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            message = raw
            try:
                parsed = json.loads(raw)
                error = parsed.get("error") if isinstance(parsed.get("error"), dict) else {}
                message = error.get("message") or parsed.get("detail") or raw
            except (json.JSONDecodeError, AttributeError):
                pass
            if exc.code == 403:
                raise SarvamError(
                    "Sarvam rejected the API key.",
                    401,
                    "Check the key in Settings, or create a new one at dashboard.sarvam.ai.",
                ) from exc
            if exc.code == 401:
                raise SarvamError(
                    "Sarvam could not authenticate that key.",
                    401,
                    "Check the key in Settings. If it is new, give it a minute and try again.",
                ) from exc
            if exc.code in (429, 500, 502, 503, 504) and attempt == 0:
                last_error = exc
                time.sleep(0.8)
                continue
            raise SarvamError(f"Sarvam error ({exc.code}): {str(message)[:300]}", 502) from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            if attempt == 0:
                last_error = exc
                time.sleep(0.6)
                continue
            reason = getattr(exc, "reason", exc)
            raise SarvamError(f"Could not reach Sarvam: {reason}", 502) from exc
    raise SarvamError(f"Sarvam request failed: {last_error}", 502)


def _multipart(fields: dict[str, str], file_field: tuple[str, str, str, bytes]) -> tuple[bytes, str]:
    boundary = "----vaani" + uuid.uuid4().hex
    parts: list[bytes] = []
    for name, value in fields.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    name, filename, mime, data = file_field
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", filename) or "note.webm"
    parts.append(
        (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; '
            f'filename="{safe_name}"\r\nContent-Type: {mime}\r\n\r\n'
        ).encode()
    )
    parts.append(data)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def transcribe(audio: bytes, filename: str, mime: str, key: str, language: str) -> dict:
    fields = {"model": "saaras:v4", "language_code": language or "unknown"}
    body, content_type = _multipart(fields, ("file", filename, mime, audio))
    data = _call("/speech-to-text", body, content_type, key, timeout=180)
    transcript = (data.get("transcript") or "").strip()
    if not transcript:
        raise ApiError("No speech was detected in that clip. Try again a little closer to the mic.", 422)
    return {
        "transcript": transcript,
        "language_code": data.get("language_code") or "unknown",
        "language_probability": data.get("language_probability"),
    }


def chat(messages: list[dict], key: str) -> str:
    payload = {
        "model": os.environ.get("SARVAM_CHAT_MODEL", "sarvam-105b"),
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 2200,
        # Thinking mode is on by default on sarvam-105b and its tokens count
        # against max_tokens, so a long prompt can come back with empty content
        # and finish_reason "length". Extraction needs a few hundred tokens,
        # not a chain of thought, so reasoning is switched off explicitly.
        "reasoning_effort": None,
        "response_format": {"type": "json_object"},
    }

    def send(body: dict) -> dict:
        return _call(
            "/v1/chat/completions",
            json.dumps(body).encode("utf-8"),
            "application/json",
            key,
            timeout=150,
            # The OpenAI-compatible route documents bearer auth; sending the
            # subscription key both ways keeps it working across deployments.
            extra_headers={"Authorization": f"Bearer {key}"},
        )

    def content_of(data: dict) -> str:
        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise SarvamError("Sarvam returned an unexpected chat response.", 502) from exc
        return (message.get("content") or message.get("reasoning_content") or "").strip()

    def hit_the_ceiling(data: dict) -> bool:
        try:
            return data["choices"][0].get("finish_reason") == "length"
        except (KeyError, IndexError, TypeError):
            return False

    try:
        data = send(payload)
    except SarvamError as exc:
        # Older deployments may not accept JSON mode or the reasoning knob.
        message = exc.message.lower()
        if not any(token in message for token in ("response_format", "reasoning", "json_object")):
            raise
        payload.pop("response_format", None)
        payload.pop("reasoning_effort", None)
        data = send(payload)

    content = content_of(data)
    if not content and hit_the_ceiling(data):
        # Reasoning was ignored and ate the budget: retry with room for both.
        data = send({**payload, "max_tokens": 3600})
        content = content_of(data)

    if not content:
        raise SarvamError(
            "Sarvam returned an empty response. Please retry.",
            502,
            "If this keeps happening, the model may be spending its token "
            "budget on reasoning. Try a shorter note.",
        )
    return content


def _text_chunks(text: str, limit: int = 900) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks, current = [], ""
    for sentence in re.split(r"(?<=[.!?।])\s+", text):
        if len(current) + len(sentence) + 1 > limit and current:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def translate(text: str, source: str, target: str, key: str) -> dict:
    if source not in pipeline.LANGUAGES:
        source = "auto"
    if target not in pipeline.LANGUAGES:
        target = "en-IN"
    pieces = []
    for chunk in _text_chunks(text):
        payload = {
            "input": chunk,
            "source_language_code": source,
            "target_language_code": target,
            "model": "mayura:v1",
            "numerals_format": "international",
        }
        data = _call(
            "/translate",
            json.dumps(payload).encode("utf-8"),
            "application/json",
            key,
            timeout=90,
        )
        pieces.append(data.get("translated_text") or "")
    return {"translated_text": " ".join(piece for piece in pieces if piece).strip()}


TTS_SPEAKERS = {
    "shubh", "aditya", "ritu", "priya", "neha", "rahul", "pooja", "rohan",
    "simran", "kavya", "amit", "dev", "ishita", "shreya", "ratan", "varun",
    "manan", "sumit", "kabir", "aayan", "ashutosh", "advait", "anand",
    "tarun", "sunny", "mani",
}
TTS_DEFAULT_SPEAKER = "priya"


def speak(text: str, language: str, key: str, speaker: str = TTS_DEFAULT_SPEAKER) -> bytes:
    if language not in TTS_LANGUAGES:
        label = pipeline.language_name(language) if language in pipeline.LANGUAGES else language
        raise ApiError(
            f"Voice playback isn't available for {label} yet.",
            422,
            "The reminder text is still ready to copy.",
        )
    if speaker not in TTS_SPEAKERS:
        speaker = TTS_DEFAULT_SPEAKER
    payload = {
        "text": text.strip()[:2400],
        "language_code": language,
        "speaker": speaker,
        "model": "bulbul:v3",
        "pace": 1.0,
        "output_audio_codec": "wav",
    }
    data = _call(
        "/text-to-speech",
        json.dumps(payload).encode("utf-8"),
        "application/json",
        key,
        timeout=90,
    )
    audios = data.get("audios") or []
    if not audios:
        raise SarvamError("Sarvam returned no audio.", 502)
    try:
        return base64.b64decode(audios[0])
    except (ValueError, TypeError) as exc:
        raise SarvamError("Sarvam returned audio in an unexpected format.", 502) from exc


# --- request handlers --------------------------------------------------------

def process_note(body: bytes, headers, key: str) -> dict:
    started = time.perf_counter()
    source = (headers.get("X-Source") or "text").lower()
    target_hint = headers.get("X-Target") or "match"
    speak_lang = headers.get("X-Speak-Lang") or "unknown"
    demo = not key
    timings: dict[str, int] = {}
    probability = None

    if source == "audio":
        if not body:
            raise ApiError("The recording was empty. Please try again.", 400)
        if demo:
            raise ApiError(
                "Live transcription needs a Sarvam API key.",
                400,
                "Add your key in Settings, or use a sample note to explore the demo.",
            )
        mime = (headers.get("Content-Type") or "audio/webm").split(";")[0].strip()
        extension = "mp4" if "mp4" in mime else "webm"
        filename = headers.get("X-Filename") or f"note.{extension}"
        stage = time.perf_counter()
        result = transcribe(body, filename, mime, key, speak_lang)
        timings["transcribe_ms"] = round((time.perf_counter() - stage) * 1000)
        transcript = result["transcript"]
        detected = result["language_code"] if result["language_code"] in pipeline.LANGUAGES else pipeline.guess_language(transcript)
        probability = result.get("language_probability")
    else:
        transcript = body.decode("utf-8", "replace").strip()
        if not transcript:
            raise ApiError("Type or record something first.", 400)
        if len(transcript) > 4000:
            raise ApiError("That note is a bit long — keep it under 4,000 characters.", 400)
        detected = pipeline.guess_language(transcript)

    target = pipeline.resolve_target(target_hint, detected)
    stage = time.perf_counter()

    if demo:
        core = pipeline.demo_analyze(transcript, target, detected)
    else:
        try:
            content = chat(pipeline.build_messages(transcript, target, detected), key)
            core = pipeline.normalize(pipeline.parse_json_object(content), transcript, target, detected)
        except ValueError as exc:
            raise SarvamError(f"Could not structure the plan: {exc}. Please retry.", 502) from exc
        timings["plan_ms"] = round((time.perf_counter() - stage) * 1000)

    timings["total_ms"] = round((time.perf_counter() - started) * 1000)

    return {
        "transcript": transcript,
        "language_code": core["language_code"],
        "language_name": core["language_name"],
        "language_probability": probability,
        "target_language": core["target_language"],
        "target_language_name": core["target_language_name"],
        "summary": core["summary"],
        "briefing": core["briefing"],
        "kind": core["kind"],
        "command": core["command"],
        "tasks": core["tasks"],
        "demo": demo,
        "source": source,
        "timings": timings,
        "notice": (
            "Demo mode: add a Sarvam API key for live transcription and reasoning."
            if demo
            else ""
        ),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "Vaani/1.0"
    protocol_version = "HTTP/1.1"

    # -- helpers
    def _send_bytes(self, status: int, payload: bytes, content_type: str, extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for name, value in (extra or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send_bytes(status, body, "application/json; charset=utf-8")

    def _error(self, exc: ApiError) -> None:
        self._json(exc.status, {"error": exc.message, "hint": exc.hint})

    def _read_body(self) -> bytes:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise ApiError("Invalid Content-Length header.", 400)
        if length > MAX_BODY:
            raise ApiError("That file is too large. Keep audio under 25 MB.", 413)
        return self.rfile.read(length) if length else b""

    def _key(self, supplied: str | None = None) -> str:
        return (supplied or self.headers.get("X-Sarvam-Key") or env_key()).strip()

    def _notice_demo(self) -> None:
        pass

    # -- routes
    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/api/health", "/health"):
            self._json(200, {
                "ok": True,
                "key_configured": bool(env_key()),
                "demo_mode": not bool(env_key()),
                "today": pipeline.today_ist().isoformat(),
                "languages": pipeline.LANGUAGES,
            })
            return
        self._serve_static(path)

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        try:
            if path == "/api/process":
                body = self._read_body()
                key = self._key()
                self._json(200, process_note(body, self.headers, key))
            elif path == "/api/translate":
                body = self._read_body()
                key = self._key()
                if not key:
                    raise ApiError("Add a Sarvam API key to translate.", 400)
                data = json.loads(body.decode("utf-8") or "{}")
                text = str(data.get("text") or "").strip()
                if not text:
                    raise ApiError("Nothing to translate.", 400)
                self._json(200, translate(
                    text,
                    str(data.get("source") or "auto"),
                    str(data.get("target") or "en-IN"),
                    key,
                ))
            elif path == "/api/tts":
                body = self._read_body()
                key = self._key()
                if not key:
                    raise ApiError("Add a Sarvam API key for voice playback.", 400)
                data = json.loads(body.decode("utf-8") or "{}")
                text = str(data.get("text") or "").strip()
                if not text:
                    raise ApiError("Nothing to speak.", 400)
                audio = speak(text, str(data.get("language") or "hi-IN"), key, str(data.get("speaker") or TTS_DEFAULT_SPEAKER))
                self._send_bytes(200, audio, "audio/wav", {"Cache-Control": "no-store"})
            else:
                self._json(404, {"error": "Not found."})
        except ApiError as exc:
            self._error(exc)
        except json.JSONDecodeError:
            self._error(ApiError("Invalid JSON body.", 400))
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as exc:  # last-resort guard so the demo never dead-ends
            print(f"[vaani] unexpected error: {exc!r}", flush=True)
            self._error(ApiError("Something went wrong on the server. Please retry.", 500))

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Allow", "GET, POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _serve_static(self, path: str) -> None:
        rel = "index.html" if path in {"/", "/index.html"} else path.lstrip("/")
        candidate = (PUBLIC / rel).resolve()
        if not candidate.is_relative_to(PUBLIC) or not candidate.is_file():
            self._send_bytes(404, b"Not found", "text/plain; charset=utf-8")
            return
        content_type = MIME.get(candidate.suffix.lower()) or mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self._send_bytes(
            200,
            candidate.read_bytes(),
            content_type,
            {"Cache-Control": "no-cache, must-revalidate"},
        )

    def log_message(self, fmt: str, *args) -> None:
        # Keep the console readable during a live demo.
        print(f"[vaani] {self.address_string()} {fmt % args}", flush=True)

    def handle(self) -> None:
        try:
            super().handle()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass


def _lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def main() -> None:
    load_env()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    url = f"http://127.0.0.1:{port}"
    mode = "LIVE (Sarvam key configured)" if env_key() else "DEMO (no Sarvam key yet)"
    print()
    print("  Vaani — voice to action, in your language")
    print(f"  Mode : {mode}")
    print(f"  Open : {url}")
    if host == "0.0.0.0":
        print(f"  LAN  : http://{_lan_ip()}:{port}  (mic needs https or localhost)")
    print("  Stop : Ctrl+C")
    print()

    if "--no-open" not in sys.argv:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        ThreadingHTTPServer((host, port), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\n  Bye.")


if __name__ == "__main__":
    main()
