"""Vaani pipeline: turn a spoken note into tasks, deadlines, priorities and reminders.

The heavy lifting is done by Sarvam's chat model; everything here is prompt
construction, robust JSON normalisation and an offline demo fallback so the UI
still works before an API key is added.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote, urlencode

IST = timezone(timedelta(hours=5, minutes=30))

LANGUAGES = {
    "hi-IN": {"name": "Hindi", "native": "हिंदी", "glyph": "अ"},
    "ta-IN": {"name": "Tamil", "native": "தமிழ்", "glyph": "த"},
    "te-IN": {"name": "Telugu", "native": "తెలుగు", "glyph": "త"},
    "ml-IN": {"name": "Malayalam", "native": "മലയാളം", "glyph": "മ"},
    "bn-IN": {"name": "Bengali", "native": "বাংলা", "glyph": "ব"},
    "mr-IN": {"name": "Marathi", "native": "मराठी", "glyph": "म"},
    "kn-IN": {"name": "Kannada", "native": "ಕನ್ನಡ", "glyph": "ಕ"},
    "gu-IN": {"name": "Gujarati", "native": "ગુજરાતી", "glyph": "ગ"},
    "pa-IN": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "glyph": "ਪ"},
    "od-IN": {"name": "Odia", "native": "ଓଡ଼ିଆ", "glyph": "ଓ"},
    "ur-IN": {"name": "Urdu", "native": "اردو", "glyph": "ا"},
    "en-IN": {"name": "English", "native": "English", "glyph": "A"},
}

CATEGORIES = {
    "call",
    "payment",
    "meeting",
    "health",
    "travel",
    "shopping",
    "home",
    "work",
    "other",
}

PRIORITIES = {"high", "medium", "low"}

# Only these destinations can ever be opened from a model response. The model
# returns a type and a query, never a URL; the server builds the link itself.
SEARCH_SERVICES = {
    "youtube": ("YouTube", "https://www.youtube.com/results?search_query={query}"),
    "google": ("Google", "https://www.google.com/search?q={query}"),
    "maps": ("Google Maps", "https://www.google.com/maps/search/?api=1&query={query}"),
    "amazon": ("Amazon", "https://www.amazon.in/s?k={query}"),
    "flipkart": ("Flipkart", "https://www.flipkart.com/search?q={query}"),
}

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def today_ist() -> date:
    return datetime.now(IST).date()


def language_name(code: str) -> str:
    return LANGUAGES.get(code, {}).get("name", "Unknown")


def resolve_target(target: str, detected: str) -> str:
    """Resolve the output language, falling back to the detected language."""
    if not target or target in {"match", "auto"}:
        return detected if detected in LANGUAGES else "hi-IN"
    return target if target in LANGUAGES else "en-IN"


def guess_language(text: str) -> str:
    """Cheap script detection, used for typed text and the offline demo mode."""
    ranges = [
        ("hi-IN", "\u0900", "\u097f"),
        ("bn-IN", "\u0980", "\u09ff"),
        ("pa-IN", "\u0a00", "\u0a7f"),
        ("gu-IN", "\u0a80", "\u0aff"),
        ("od-IN", "\u0b00", "\u0b7f"),
        ("ta-IN", "\u0b80", "\u0bff"),
        ("te-IN", "\u0c00", "\u0c7f"),
        ("kn-IN", "\u0c80", "\u0cff"),
        ("ml-IN", "\u0d00", "\u0d7f"),
        ("ur-IN", "\u0600", "\u06ff"),
    ]
    for code, start, end in ranges:
        if any(start <= ch <= end for ch in text):
            return code
    # Romanised Hindi/Hinglish, e.g. "kal electrician ko call karna hai".
    words = set(re.findall(r"[a-z]+", text.lower()))
    hinglish = {
        "kal", "aaj", "abhi", "parso", "karna", "karo", "karni", "hai", "hain",
        "aur", "nahi", "mujhe", "ko", "se", "tak", "paise", "paisa", "jaldi",
        "baje", "davai", "dawai", "subah", "shaam", "ghar", "doodh", "kapde",
        "lena", "dena", "jana", "yaar", "bhai", "chahiye", "hoga", "karke",
    }
    if len(words & hinglish) >= 2:
        return "hi-IN"
    return "en-IN"


SCHEMA_HINT = """{
  "language_code": "hi-IN",
  "language_name": "Hindi",
  "summary": "<one short line in the target language>",
  "briefing": "<20-35 spoken words in the target language, reading the plan naturally>",
  "command": {
    "type": "search|call|message|email",
    "service": "youtube|google|maps|amazon|flipkart",
    "query": "<what to search, for search only>",
    "phone": "<digits the speaker actually said, call/message only>",
    "text": "<message to send, message only>",
    "to": "<email address the speaker actually said, email only>",
    "subject": "<email subject>",
    "body": "<email body>",
    "label": "<button label in the target language, max 4 words>"
  },
  "tasks": [
    {
      "title": "<verb-first action, max 6 words, target language>",
      "title_en": "<same action in English>",
      "category": "call|payment|meeting|health|travel|shopping|home|work|other",
      "priority": "high|medium|low",
      "due_label": "<short deadline phrase in target language, e.g. आज / सोमवार से पहले / कोई तारीख नहीं>",
      "due_iso": "<YYYY-MM-DD resolved from today, or an empty string>",
      "due_time": "<HH:MM 24-hour, or an empty string>",
      "why": "<max 8 words in target language explaining the priority>",
      "reminder": "<ready-to-send 1-2 sentence reminder in target language, including the deadline>",
      "reminder_en": "<the same reminder in English>",
      "action": {
        "type": "search|call|message|email",
        "service": "youtube|google|maps|amazon|flipkart",
        "query": "<search text>",
        "phone": "<digits>",
        "text": "<message>",
        "to": "<email>",
        "subject": "<subject>",
        "body": "<body>",
        "label": "<button label in target language, max 4 words>"
      }
    }
  ]
}"""


def build_messages(transcript: str, target_code: str, detected_code: str = "") -> list[dict]:
    today = today_ist()
    target = LANGUAGES.get(target_code, LANGUAGES["en-IN"])
    detected = language_name(detected_code) if detected_code in LANGUAGES else "unknown"
    system = f"""You are Vaani, an assistant that turns spoken notes in Indian languages into a clean action plan.

Today is {today.isoformat()} ({today.strftime('%A')}), timezone Asia/Kolkata (IST).
The speaker's language was detected as: {detected}.
Write every user-facing value in {target['name']} ({target_code}).

You understand Hindi, Tamil, Telugu, Malayalam, Bengali, Marathi, Kannada, Gujarati, Punjabi, Odia, Urdu, Assamese and Indian English, including romanised and code-mixed speech such as Hinglish ("kal electrician ko call karna hai").

Return ONE JSON object and nothing else, with exactly this shape:
{SCHEMA_HINT}

Rules:
1. Split the note into 1-6 atomic tasks a person can tick off. Merge duplicates. Skip filler and small talk.
2. priority "high" when there is explicit urgency (aaj, abhi, jaldi, urgent), money/bills, health, safety, or a deadline today/tomorrow. "medium" for a deadline within 7 days. "low" when there is no real deadline.
3. Resolve relative dates against today. "kal" means tomorrow, "parso" means the day after, "Monday tak" means the coming Monday. Put the resolved date in due_iso and a natural phrase in due_label. Never invent a date that was not implied.
4. due_time is only set when a clock time is actually spoken.
5. title must be verb-first and short (max 6 words). Keep target-language script for Indic languages; product names and English loanwords may stay in Latin script.
6. reminder is a message the user could send to a landlord, electrician, colleague or family member. It must sound like the speaker (keep code-mixing if they mixed languages), name the task and the deadline, and never say "this is a reminder from your assistant" or address the user as "you must".
7. briefing is what the assistant would say back out loud: 20-35 words, natural spoken rhythm, covering the tasks in order. No emojis, no markdown.
8. summary is one short scannable line in the target language.
9. Never invent names, amounts or dates. If the note has nothing actionable, return tasks: [] and explain that in summary.
10. If the note is already in {target['name']}, do not translate it into another language.
11. If the speaker asks to do something now — open, search, play, call, message or email — put it in "command" and do not turn it into a task. Example: "YouTube pe AR Rahman ke gaane chalao" → command search youtube, query "AR Rahman songs". Set "command": null when there is no immediate command.
12. Actions are limited to search, call, message and email. Never return a URL, domain, markdown link or HTML. The server builds the link from your type and arguments. The label must be in {target['name']}, max 4 words (e.g. "YouTube खोलें").
13. For call and message, only include a phone number the speaker actually said; never invent one. For email, only set "to" when an address was spoken, otherwise leave it empty. For search, keep the query short and faithful to what was asked.
14. A task may also carry an "action" when opening something is the natural next step, e.g. a bill payment task with an action to search the biller. Leave "action": null otherwise."""
    user = f'Spoken note:\n"""\n{transcript.strip()}\n"""'
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def parse_json_object(text: str) -> dict:
    """Parse a JSON object from a model reply, tolerating fences and prose."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("The model returned an empty response.")
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    try:
        value = json.loads(cleaned)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        value = json.loads(cleaned[start : end + 1])
        if isinstance(value, dict):
            return value
    raise ValueError("Could not parse the model response as JSON.")


def _text(value, fallback: str = "", limit: int = 600) -> str:
    if not isinstance(value, (str, int, float)):
        return fallback
    cleaned = re.sub(r"\s+", " ", str(value)).strip().strip('"').strip()
    return cleaned[:limit] or fallback


def _priority(value, default: str = "medium") -> str:
    value = _text(value).lower()
    mapping = {
        "urgent": "high",
        "critical": "high",
        "asap": "high",
        "important": "high",
        "normal": "medium",
        "moderate": "medium",
        "later": "low",
    }
    value = mapping.get(value, value)
    return value if value in PRIORITIES else default


def _category(value) -> str:
    value = _text(value).lower()
    mapping = {
        "bills": "payment",
        "bill": "payment",
        "money": "payment",
        "finance": "payment",
        "doctor": "health",
        "medicine": "health",
        "medical": "health",
        "phone": "call",
        "invite": "meeting",
        "buy": "shopping",
        "repair": "home",
        "office": "work",
    }
    value = mapping.get(value, value)
    return value if value in CATEGORIES else "other"


def _iso_date(value) -> str:
    value = _text(value, limit=32)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return ""
    try:
        date.fromisoformat(value)
    except ValueError:
        return ""
    return value


def _time(value) -> str:
    value = _text(value, limit=16)
    if not re.fullmatch(r"\d{2}:\d{2}", value):
        return ""
    hours, minutes = value.split(":")
    if int(hours) > 23 or int(minutes) > 59:
        return ""
    return value


def _phone(value) -> str:
    """Normalise what the speaker said into a dialable number, or drop it."""
    digits = re.sub(r"\D", "", _text(value, limit=32))
    if len(digits) == 10 and digits[0] in "6789":
        return "+91" + digits
    if len(digits) == 11 and digits[0] == "0" and digits[1] in "6789":
        return "+91" + digits[1:]
    if len(digits) == 12 and digits.startswith("91") and digits[2] in "6789":
        return "+" + digits
    if 11 <= len(digits) <= 15:
        return "+" + digits
    return ""


def action_view(raw, target_code: str = "en-IN") -> dict | None:
    """Turn a model's action intent into one allow-listed, safe link.

    The model never supplies a URL. It names an action and its arguments; this
    function validates them and builds the destination itself, so a prompt
    injection cannot produce a `javascript:` link or an arbitrary domain.
    """
    if not isinstance(raw, dict):
        return None
    kind = _text(raw.get("type"), "", 20).lower()
    service = _text(raw.get("service"), "", 24).lower()
    detail = ""

    if kind == "search":
        if service not in SEARCH_SERVICES:
            return None
        query = _text(raw.get("query"), "", 200)
        if not query:
            return None
        name, template = SEARCH_SERVICES[service]
        url = template.format(query=quote(query, safe=""))
        default = f"Open {name}" if service in {"youtube", "maps"} else f"Search {name}"
        detail = query
    elif kind == "call":
        phone = _phone(raw.get("phone"))
        if not phone:
            return None
        url = "tel:" + phone
        default = "Call"
        detail = phone
    elif kind == "message":
        channel = _text(raw.get("channel"), "whatsapp", 24).lower()
        if channel != "whatsapp":
            return None
        text = _text(raw.get("text"), "", 900)
        if not text:
            return None
        phone = _phone(raw.get("phone"))
        number = phone.lstrip("+")
        query = urlencode({"text": text})
        url = f"https://wa.me/{number}?{query}" if number else f"https://wa.me/?{query}"
        default = "Open WhatsApp"
        detail = text
    elif kind == "email":
        to = _text(raw.get("to"), "", 200)
        if to and not EMAIL_RE.match(to):
            to = ""
        subject = _text(raw.get("subject"), "", 160)
        body = _text(raw.get("body") or raw.get("text"), "", 900)
        if not (to or subject or body):
            return None
        params = urlencode([(key, value) for key, value in (("subject", subject), ("body", body)) if value])
        url = "mailto:" + quote(to, safe="@") + ("?" + params if params else "")
        default = "Compose email"
        detail = to or subject or body
    else:
        return None

    label = _text(raw.get("label"), "", 60) or default
    view = {"type": kind, "label": label, "url": url, "detail": detail}
    if kind == "search":
        view["service"] = service
    return view


def normalize(payload: dict, transcript: str, target_code: str, detected_code: str = "") -> dict:
    """Make model output safe and complete enough for the UI to render."""
    detected = _text(payload.get("language_code"), detected_code or guess_language(transcript), 16)
    if detected not in LANGUAGES:
        detected = detected_code if detected_code in LANGUAGES else guess_language(transcript)

    raw_tasks = payload.get("tasks")
    if not isinstance(raw_tasks, list):
        raw_tasks = []

    command = action_view(payload.get("command"), target_code)

    tasks: list[dict] = []
    for index, raw in enumerate(raw_tasks[:8]):
        if not isinstance(raw, dict):
            continue
        title = _text(raw.get("title"), "", 120)
        title_en = _text(raw.get("title_en"), "", 160)
        if not title and not title_en:
            continue
        due_iso = _iso_date(raw.get("due_iso"))
        tasks.append(
            {
                "id": f"t{index + 1}",
                "title": title or title_en,
                "title_en": title_en or title,
                "category": _category(raw.get("category")),
                "priority": _priority(raw.get("priority")),
                "due_label": _text(raw.get("due_label"), "", 60),
                "due_iso": due_iso,
                "due_time": _time(raw.get("due_time")),
                "why": _text(raw.get("why"), "", 100),
                "reminder": _text(raw.get("reminder"), "", 480),
                "reminder_en": _text(raw.get("reminder_en"), "", 480),
                "action": action_view(raw.get("action"), target_code),
            }
        )

    summary = _text(payload.get("summary"), "", 240)
    briefing = _text(payload.get("briefing"), "", 500)

    if not summary:
        if command:
            summary = f"{command['label']}: {command['detail']}" if command["detail"] else command["label"]
        else:
            summary = _fallback_summary(tasks, target_code)
    if not briefing:
        if command:
            briefing = f"{command['label']}. {command['detail']}" if command["detail"] else command["label"]
        else:
            briefing = _fallback_briefing(tasks, target_code)

    return {
        "language_code": detected,
        "language_name": language_name(detected),
        "target_language": target_code,
        "target_language_name": language_name(target_code),
        "summary": summary,
        "briefing": briefing,
        "command": command,
        "kind": "command" if command else "plan",
        "tasks": tasks,
    }


def _fallback_summary(tasks: list[dict], target_code: str) -> str:
    if not tasks:
        if target_code == "hi-IN":
            return "इस नोट में कोई साफ़ काम नहीं मिला।"
        return "No clear action found in this note."
    if target_code == "hi-IN":
        return f"{len(tasks)} काम मिले — पहला: {tasks[0]['title']}।"
    return f"{len(tasks)} task{'s' if len(tasks) != 1 else ''} found — first: {tasks[0]['title']}."


def _fallback_briefing(tasks: list[dict], target_code: str) -> str:
    if not tasks:
        return _fallback_summary(tasks, target_code)
    if target_code == "hi-IN":
        lines = [f"आपके {len(tasks)} काम हैं।"]
        for task in tasks:
            when = f", {task['due_label']}" if task["due_label"] else ""
            lines.append(f"{task['title']}{when}।")
        return " ".join(lines)
    lines = [f"You have {len(tasks)} task{'s' if len(tasks) != 1 else ''}."]
    for task in tasks:
        when = f", {task['due_label']}" if task["due_label"] else ""
        lines.append(f"{task['title']}{when}.")
    return " ".join(lines)


# --- Offline demo mode -------------------------------------------------------
# Keeps the product demonstrable before a Sarvam key is configured. The UI marks
# these results clearly, so nobody mistakes them for a live model response.

def _next_monday(today: date) -> date:
    days = (0 - today.weekday()) % 7
    return today + timedelta(days=days or 7)


_COMMAND_HEAD = re.compile(
    r"^(?:please|pls|kripya|search|play|open|kholo|khol|chalao|dikhao)\s+",
    flags=re.IGNORECASE,
)
_COMMAND_TAIL = re.compile(
    r"\b(?:search|dhundo|dhoondo|kholo|khol|open|chalao|chala|play|dikhao|dikha|sunao|karo|kar do)\b.*$",
    flags=re.IGNORECASE,
)


def _clean_query(text: str) -> str:
    text = _text(text, "", 200).strip(" .,!?:;\"'")
    text = _COMMAND_HEAD.sub("", text)
    text = _COMMAND_TAIL.sub("", text).strip(" .,!?:;\"'")
    return text[:200]


def _after_keyword(text: str, keywords: list[str]) -> str:
    for keyword in keywords:
        match = re.search(
            rf"\b{re.escape(keyword)}\b\s*(?:pe|par|on|mein|me|se)?\s*(.+)",
            text,
            flags=re.IGNORECASE,
        )
        if match:
            return match.group(1)
    return ""


def _demo_label(action: dict, target_code: str) -> dict:
    if target_code == "hi-IN":
        key = action.get("service") if action.get("type") == "search" else action.get("type")
        label = {
            "youtube": "YouTube खोलें",
            "google": "Google पर खोजें",
            "maps": "Maps खोलें",
            "amazon": "Amazon पर खोजें",
            "flipkart": "Flipkart पर खोजें",
            "call": "कॉल करें",
            "message": "WhatsApp खोलें",
            "email": "ईमेल लिखें",
        }.get(key)
        if label:
            action["label"] = label
    return action


def demo_command(transcript: str, target_code: str = "en-IN") -> dict | None:
    """Recognise the obvious 'open/search/call' notes without a model.

    Deliberately narrow: it only fires on clear service names and a real phone
    number, so the demo never invents an action the note did not ask for.
    """
    lower = transcript.lower()

    phone = ""
    for match in re.finditer(
        r"(?<!\d)(?:(?:\+?91|0)[\s-]?)?[6-9](?:[\s-]?\d){9}(?!\d)", transcript
    ):
        phone = _phone(match.group(0))
        if phone:
            break

    if "youtube" in lower:
        query = _clean_query(_after_keyword(transcript, ["youtube"]))
        if query:
            return _demo_label({"type": "search", "service": "youtube", "query": query}, target_code)

    if any(word in lower for word in ("maps", "rasta", "raasta", "directions")):
        query = _clean_query(_after_keyword(transcript, ["maps", "rasta", "raasta"]))
        if not query:
            query = _clean_query(
                re.sub(r"\b(?:ka|ki|ke)\s+(?:rasta|raasta).*$", "", transcript, flags=re.IGNORECASE)
            )
        if query:
            return _demo_label({"type": "search", "service": "maps", "query": query}, target_code)

    if "google" in lower:
        query = _clean_query(_after_keyword(transcript, ["google"])) or _clean_query(transcript)
        if query:
            return _demo_label({"type": "search", "service": "google", "query": query}, target_code)

    if phone and re.search(r"\b(?:call|phone|dial)\b|फोन|कॉल", lower):
        return _demo_label({"type": "call", "phone": phone}, target_code)

    return None


def demo_analyze(transcript: str, target_code: str, detected_code: str = "") -> dict:
    detected = detected_code if detected_code in LANGUAGES else guess_language(transcript)
    target = target_code or detected
    if target not in LANGUAGES:
        target = detected
    today = today_ist()

    if "electrician" in transcript.lower() and "rent" in transcript.lower() and detected == "hi-IN":
        monday = _next_monday(today).isoformat()
        hindi = target == "hi-IN"
        tasks = [
            {
                "id": "t1",
                "title": "इलेक्ट्रीशियन को कॉल करें" if hindi else "Call the electrician",
                "title_en": "Call the electrician",
                "category": "call",
                "priority": "high",
                "due_label": "कल" if hindi else "Tomorrow",
                "due_iso": (today + timedelta(days=1)).isoformat(),
                "due_time": "",
                "why": "कल का काम, टालना नहीं" if hindi else "Due tomorrow, don't postpone",
                "reminder": "Kal electrician ko call karna hai — subah 10 baje tak try kar lena."
                if hindi
                else "Please call the electrician tomorrow before 10 am.",
                "reminder_en": "Please call the electrician tomorrow before 10 am.",
            },
            {
                "id": "t2",
                "title": "किराया जमा करें" if hindi else "Pay the rent",
                "title_en": "Pay the rent",
                "category": "payment",
                "priority": "medium",
                "due_label": "सोमवार तक" if hindi else "By Monday",
                "due_iso": monday,
                "due_time": "",
                "why": "पैसे और तारीख, दोनों ज़रूरी" if hindi else "Money with a hard deadline",
                "reminder": "Rent payment Monday tak complete karna hai."
                if hindi
                else "Please complete the rent payment by Monday.",
                "reminder_en": "Please complete the rent payment by Monday.",
            },
        ]
        return normalize(
            {
                "language_code": "hi-IN",
                "summary": "दो ज़रूरी काम: कल इलेक्ट्रीशियन को कॉल, सोमवार से पहले किराया।"
                if hindi
                else "Two tasks: call the electrician tomorrow, pay rent before Monday.",
                "briefing": "आपके दो काम हैं। पहला, कल इलेक्ट्रीशियन को कॉल करें। दूसरा, सोमवार से पहले किराया जमा करें।"
                if hindi
                else "You have two tasks. First, call the electrician tomorrow. Second, pay the rent before Monday.",
                "tasks": tasks,
            },
            transcript,
            target,
            detected,
        )

    # Generic heuristic fallback for any other note.
    command = demo_command(transcript, target)
    if command:
        view = action_view(command, target)
        if view:
            summary = f"{view['label']}: {view['detail']}" if view["detail"] else view["label"]
            briefing = f"{view['label']}. {view['detail']}" if view["detail"] else view["label"]
            return normalize(
                {
                    "language_code": detected,
                    "summary": summary,
                    "briefing": briefing,
                    "command": command,
                },
                transcript,
                target,
                detected,
            )

    parts = [
        part.strip(" ,.-")
        for part in re.split(r"[.;\n]|\s+(?:aur|and|மற்றும்|మరియు|ഒപ്പം)\s+", transcript)
        if part.strip(" ,.-")
    ][:5]

    urgency = ("aaj", "kal", "abhi", "jaldi", "urgent", "today", "tomorrow", "asap",
               "அவசர", "అర్జెంట్", "അടിയന്തിര")
    is_urgent = any(word in transcript.lower() for word in urgency)
    english = target == "en-IN"

    tasks = []
    for index, part in enumerate(parts):
        lower = part.lower()
        if any(word in lower for word in ("pay", "rent", "bill", "किराया", "बिल")):
            category = "payment"
        elif any(word in lower for word in ("doctor", "medicine", "davai", "दवा", "डॉक्टर")):
            category = "health"
        elif any(word in lower for word in ("call", "phone", "कॉल", "फोन")):
            category = "call"
        elif any(word in lower for word in ("buy", "milk", "खरीद", "दूध")):
            category = "shopping"
        else:
            category = "other"
        tasks.append(
            {
                "id": f"t{index + 1}",
                "title": part[:100],
                "title_en": part[:140],
                "category": category,
                "priority": "high" if is_urgent and index == 0 else "medium",
                "due_label": "" ,
                "due_iso": "",
                "due_time": "",
                "why": "Demo mode — add a Sarvam key for real reasoning."
                if english
                else "डेमो मोड — असली विश्लेषण के लिए Sarvam key जोड़ें।",
                "reminder": part if english else part,
                "reminder_en": part,
            }
        )

    return normalize(
        {
            "language_code": detected,
            "summary": ("Demo analysis — add a Sarvam key for live extraction."
                        if english else "डेमो विश्लेषण — लाइव नतीजों के लिए Sarvam key जोड़ें।"),
            "tasks": tasks,
        },
        transcript,
        target,
        detected,
    )
