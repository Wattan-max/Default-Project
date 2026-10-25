# Vaani — voice to action, in your language

Speak a messy note in Hindi, Tamil, Telugu, Malayalam, Bengali, Marathi, Kannada, Gujarati, Punjabi, Odia or Urdu — Vaani turns it into a clean action list with deadlines, priorities and a ready-to-send reminder in your own language.

> **Input:** “Kal electrician ko call karna hai aur Monday tak rent pay karna hai.”
>
> **Output**
> - **Call the electrician** — tomorrow · high priority
> - **Pay the rent** — before Monday · medium priority
> - **Reminder:** “Kal electrician ko call karna hai — subah 10 baje tak try kar lena.”

Built with [Sarvam AI](https://sarvam.ai): **Saaras** (speech-to-text), **Sarvam-105B** (reasoning + structured extraction), **Mayura** (translation) and **Bulbul** (voice playback).

---

## Run it (2 commands, no dependencies)

Requires **Python 3.10+**. There is no `pip install` step — the server uses only the standard library.

```bash
cp .env.example .env      # Windows: copy .env.example .env
# paste your Sarvam key into .env
python server.py
```

Open **http://127.0.0.1:8000**. Use `python server.py --no-open` to skip the browser launch.

No key yet? The app still runs in **clearly-labelled demo mode** for typed notes so you can click through the UI. Add a key in `.env` or with the **API key** button in the top right to unlock live transcription, reasoning, translation and voice.

Get a key at [dashboard.sarvam.ai](https://dashboard.sarvam.ai).

---

## What it actually does

```
 mic / upload ──► POST /speech-to-text (saaras:v4, language_code=unknown)
                    │  transcript + detected language + confidence
                    ▼
              POST /v1/chat/completions (sarvam-105b, JSON mode)
                    │  atomic tasks · resolved dates · urgency · reminder drafts
                    ▼
     ┌──────────────┼─────────────────┐
     ▼              ▼                 ▼
task cards      POST /translate   POST /text-to-speech
(importance,    (mayura:v1,       (bulbul:v2,
 dates, done)    transcript)       briefing + reminders)
```

- **Transcribe** — Sarvam Saaras v4 with auto language detection, including code-mixed Hinglish.
- **Understand** — a carefully constrained prompt returns one JSON object: 1–6 atomic tasks, `due_iso` resolved against today's IST date, a priority, a one-line “why”, and a reminder message in the speaker's tone.
- **Act now** — an “open YouTube and search…” style note becomes a command with one safe, server-built button. No URL ever comes from the model.
- **Translate** — the plan is written directly in the chosen output language; the raw transcript can be translated on demand with Mayura.
- **Speak** — Bulbul reads back the spoken briefing or any individual reminder.
- **Act** — copy a reminder, copy the whole plan, tick tasks off, or export dated tasks to `.ics`.

Everything is server-side: the browser never talks to Sarvam directly, and the API key is never rendered into the page.

### Design choices that matter

- **Dates are resolved, not echoed.** The prompt receives today's date and weekday, so “kal”, “parso” and “Monday tak” become real dates. The UI then shows both the natural phrase and the concrete date.
- **Priority is explained.** Every high-priority task carries a short reason (“due tomorrow”, “money with a hard deadline”), so the list does not feel like a random colour.
- **Reminders are messages, not notifications.** They are written in the first person, in the speaker's language mix, ready to paste into WhatsApp.
- **Graceful failure.** Missing key, blocked mic, unsupported TTS language, oversized file, upstream 429/5xx — all have a visible, human message. Server calls retry once on transient failures.
- **No accounts, no database.** Audio is proxied to Sarvam and discarded; only the last plan is kept in `localStorage` for convenience.

---

## Try these lines

| Language | Say |
| --- | --- |
| Hinglish | `Kal electrician ko call karna hai aur Monday tak rent pay karna hai.` |
| हिंदी | `डॉक्टर से कल सुबह मिलना है और शाम को दवाई लेनी है। बिजली का बिल आज ही जमा करना है।` |
| தமிழ் | `நாளைக்கு காலையில் எலக்ட்ரீஷியனுக்கு கால் செய்ய வேண்டும். திங்கட்கிழமைக்குள் வீட்டு வாடகை கட்ட வேண்டும்.` |
| తెలుగు | `రేపు ఉదయం ఎలక్ట్రిషియన్‌కు కాల్ చేయాలి. సోమవారం లోపు అద్దె కట్టాలి.` |
| മലയാളം | `നാളെ രാവിലെ ഡോക്ടറെ കാണണം. തിങ്കളാഴ്ചയ്ക്ക് മുൻപ് വാടക അടയ്ക്കണം.` |
| বাংলা | `কাল সকালে ইলেকট্রিশিয়ানকে ফোন করতে হবে। সোমবারের মধ্যে বাড়িভাড়া দিতে হবে।` |
| Command | `YouTube pe AR Rahman ke best songs search karo.` |

The chips under the recorder run these instantly.

---

## Commands — one tap, not autopilot

A note that asks you to do something **now** becomes a command instead of a task:

| You say | Button |
| --- | --- |
| “YouTube pe AR Rahman ke best songs search karo” | Open YouTube |
| “Google pe best electrician search karo” | Search Google |
| “Bandra station ka rasta dikhao” | Open Google Maps |
| “Mummy ko 98765 43210 par call karo” | Call |
| “Sharma ji ko WhatsApp pe rent ka message bhejo” | Open WhatsApp |
| “Owner ko email likho ki rent kal de dunga” | Compose email |
| “Electricity bill bharo” | Task + a link to search the biller |

Safety rules baked into the implementation:

- The model returns only `{type, service, query, phone, to, ...}` — **never a URL**. The server builds the link from a small allow-list (`youtube`, `google`, `maps`, `amazon`, `flipkart`).
- Phone numbers and email addresses are used only when the speaker actually said them; otherwise the action is dropped.
- Nothing opens automatically. Every action is a normal link the user taps, with `rel="noopener noreferrer"`.
- No form is submitted, no message is sent and no payment is made. The app opens the place; the user stays in control.

---

## Suggested 3-minute demo

1. **Open on the empty state** and say the one-liner: “People in India don't think in forms. They think out loud, in three languages at once.”
2. **Record the Hinglish line** (or tap the Hinglish chip). While it runs, point at the pipeline: transcribe → understand → prioritise → draft.
3. **Land on the result.** Point out: detected language, the two tasks, “tomorrow” turned into a date, the reason for the high priority.
4. **Play the briefing** with the speaker button — Bulbul answers in the same language.
5. **Play / copy the rent reminder.** “Rent payment Monday se pehle complete karna hai.” That is the output a user actually sends.
6. **Switch the plan language to Tamil**, reprocess, and show the whole plan change language without touching the note.
7. **Tick a task and export the plan** to the calendar. Close on: “Voice in, actions out, in the language people actually speak.”

---

## Project layout

| Path | Purpose |
| --- | --- |
| `server.py` | Stdlib HTTP server, Sarvam client, multipart upload, TTS/translate routes |
| `pipeline.py` | Prompt, JSON parsing/normalisation, date helpers, offline demo fallback |
| `public/index.html` | App shell and recorder |
| `public/app.js` | Recording, API calls, task rendering, TTS, ICS export |
| `public/styles.css` | Theme and layout |
| `.env.example` | Key + optional port/host |

### API surface

| Route | Body | Returns |
| --- | --- | --- |
| `GET /api/health` | — | key status, today's date, language list |
| `POST /api/process` | raw audio **or** UTF-8 text; headers `X-Source`, `X-Target`, `X-Speak-Lang`, `X-Sarvam-Key` | transcript, language, summary, briefing, command, tasks, timings |
| `POST /api/translate` | `{ text, source, target }` | `{ translated_text }` |
| `POST /api/tts` | `{ text, language }` | `audio/wav` |

---

## Checks

```bash
python -m unittest -v    # 14 offline tests, no key needed
python smoke_test.py     # optional: one small paid call per Sarvam endpoint
```

The unit tests cover JSON repair, field normalisation, language detection and the demo fallback. `smoke_test.py` reads the key from `.env` (or takes it as an argument) and checks chat, translate and TTS — plus speech-to-text if you pass an audio file — so you can tell a key or quota problem apart from an app bug before a demo.

---

## Notes and limits

- This is a demo, not a production service: no auth, no persistence, single process, key stored in the browser. Put it behind a real backend before exposing it.
- Audio is capped at 25 MB; recordings auto-stop at 2 minutes.
- Voice playback supports the 11 languages Bulbul supports; Urdu plans can still be read and copied.
- `demo mode` is intentionally obvious: it uses a small canned/heuristic analyser and never pretends to be the model.
- Actions are links, not integrations: they open YouTube, Google, Maps, WhatsApp, the dialer or a mail draft. Nothing is sent, submitted or paid automatically.
- Dates assume **Asia/Kolkata (IST)**, which is the right default for the target users.
- To expose on your LAN for a phone demo: `HOST=0.0.0.0 python server.py`. Note that mobile browsers require HTTPS for microphone access, so use localhost or a tunnel for recording.
