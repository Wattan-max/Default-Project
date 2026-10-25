"""Small, dependency-free tests for the extraction pipeline.

Run: python -m unittest -v
"""

import unittest
from datetime import date

import pipeline


class JsonParsingTests(unittest.TestCase):
    def test_plain_json(self):
        self.assertEqual(pipeline.parse_json_object('{"tasks": []}'), {"tasks": []})

    def test_fenced_json(self):
        raw = '```json\n{"summary": "ok", "tasks": []}\n```'
        self.assertEqual(pipeline.parse_json_object(raw)["summary"], "ok")

    def test_json_with_prose(self):
        raw = 'Sure — here is the plan:\n{"tasks": [{"title": "Call"}]}\nLet me know!'
        self.assertEqual(len(pipeline.parse_json_object(raw)["tasks"]), 1)

    def test_invalid_json_raises(self):
        with self.assertRaises(ValueError):
            pipeline.parse_json_object("no json here")
        with self.assertRaises(ValueError):
            pipeline.parse_json_object("")


class NormalisationTests(unittest.TestCase):
    def test_sanitises_bad_fields(self):
        payload = {
            "language_code": "ta-IN",
            "summary": "  plan  ",
            "tasks": [
                {
                    "title": "பால் வாங்கு",
                    "title_en": "Buy milk",
                    "priority": "urgent",
                    "category": "shopping",
                    "due_iso": "2026-02-30",
                    "due_time": "9:5",
                    "reminder": "பால் வாங்க வேண்டும்.",
                    "reminder_en": "Buy milk.",
                },
                {"title": ""},
                "junk",
            ],
        }
        out = pipeline.normalize(payload, "பால் வாங்கு", "ta-IN")
        self.assertEqual(out["language_code"], "ta-IN")
        self.assertEqual(out["summary"], "plan")
        self.assertEqual(len(out["tasks"]), 1)
        task = out["tasks"][0]
        self.assertEqual(task["priority"], "high")  # "urgent" mapped
        self.assertEqual(task["category"], "shopping")
        self.assertEqual(task["due_iso"], "")  # impossible date dropped
        self.assertEqual(task["due_time"], "")  # malformed time dropped
        self.assertEqual(task["id"], "t1")

    def test_unknown_values_fall_back(self):
        out = pipeline.normalize(
            {"language_code": "xx-XX", "tasks": [{"title": "Do it", "priority": "banana", "category": "rocket"}]},
            "Do it",
            "en-IN",
        )
        self.assertIn(out["language_code"], pipeline.LANGUAGES)
        self.assertEqual(out["tasks"][0]["priority"], "medium")
        self.assertEqual(out["tasks"][0]["category"], "other")

    def test_task_cap(self):
        tasks = [{"title": f"Task {i}", "due_iso": "2026-10-26"} for i in range(20)]
        out = pipeline.normalize({"tasks": tasks}, "Task", "en-IN")
        self.assertEqual(len(out["tasks"]), 8)
        self.assertEqual(out["tasks"][-1]["due_iso"], "2026-10-26")

    def test_fallbacks_are_produced(self):
        out = pipeline.normalize({"tasks": [{"title": "Call the plumber"}]}, "Call the plumber", "en-IN")
        self.assertTrue(out["summary"])
        self.assertTrue(out["briefing"])


class LanguageTests(unittest.TestCase):
    def test_script_detection(self):
        self.assertEqual(pipeline.guess_language("नमस्ते, कल मिलते हैं"), "hi-IN")
        self.assertEqual(pipeline.guess_language("நாளைக்கு காலையில் வருவேன்"), "ta-IN")
        self.assertEqual(pipeline.guess_language("రేపు ఉదయం కలుద్దాం"), "te-IN")
        self.assertEqual(pipeline.guess_language("നാളെ രാവിലെ കാണാം"), "ml-IN")

    def test_hinglish_detection(self):
        self.assertEqual(pipeline.guess_language("Kal electrician ko call karna hai"), "hi-IN")
        self.assertEqual(pipeline.guess_language("Mujhe jaldi ghar jana hai"), "hi-IN")

    def test_english_stays_english(self):
        self.assertEqual(pipeline.guess_language("Call the electrician tomorrow"), "en-IN")

    def test_target_resolution(self):
        self.assertEqual(pipeline.resolve_target("match", "ta-IN"), "ta-IN")
        self.assertEqual(pipeline.resolve_target("", "hi-IN"), "hi-IN")
        self.assertEqual(pipeline.resolve_target("en-IN", "ta-IN"), "en-IN")
        self.assertEqual(pipeline.resolve_target("klingon", "ta-IN"), "en-IN")
        self.assertEqual(pipeline.resolve_target("match", "unknown"), "hi-IN")


class DemoModeTests(unittest.TestCase):
    def test_sample_produces_realistic_plan(self):
        transcript = "Kal electrician ko call karna hai aur Monday tak rent pay karna hai."
        out = pipeline.demo_analyze(transcript, "hi-IN", "hi-IN")
        self.assertEqual(len(out["tasks"]), 2)
        self.assertEqual(out["tasks"][0]["priority"], "high")
        self.assertTrue(out["tasks"][0]["reminder"])
        self.assertTrue(out["summary"])
        for task in out["tasks"]:
            if task["due_iso"]:
                date.fromisoformat(task["due_iso"])  # raises if invalid

    def test_heuristic_fallback_never_crashes(self):
        out = pipeline.demo_analyze("Buy milk. Call the plumber.", "en-IN", "en-IN")
        self.assertGreaterEqual(len(out["tasks"]), 1)
        self.assertTrue(out["summary"])


class ActionTests(unittest.TestCase):
    def test_youtube_search_url_is_built_and_encoded(self):
        view = pipeline.action_view(
            {"type": "search", "service": "youtube", "query": "AR Rahman & songs"}, "en-IN"
        )
        self.assertEqual(
            view["url"],
            "https://www.youtube.com/results?search_query=AR%20Rahman%20%26%20songs",
        )
        self.assertEqual(view["label"], "Open YouTube")
        self.assertEqual(view["detail"], "AR Rahman & songs")

    def test_unknown_service_is_rejected(self):
        self.assertIsNone(
            pipeline.action_view({"type": "search", "service": "evil.example", "query": "x"}, "en-IN")
        )
        self.assertIsNone(pipeline.action_view(None, "en-IN"))

    def test_model_supplied_url_is_ignored(self):
        view = pipeline.action_view(
            {
                "type": "search",
                "service": "youtube",
                "query": "lofi",
                "url": "https://evil.example/steal",
            },
            "en-IN",
        )
        self.assertTrue(view["url"].startswith("https://www.youtube.com/"))

    def test_phone_normalisation(self):
        view = pipeline.action_view({"type": "call", "phone": "098765 43210"}, "en-IN")
        self.assertEqual(view["url"], "tel:+919876543210")
        self.assertEqual(view["detail"], "+919876543210")
        self.assertIsNone(pipeline.action_view({"type": "call", "phone": "123"}, "en-IN"))

    def test_whatsapp_with_and_without_number(self):
        with_phone = pipeline.action_view(
            {"type": "message", "phone": "+91 98765 43210", "text": "Rent kal."}, "en-IN"
        )
        self.assertEqual(with_phone["url"], "https://wa.me/919876543210?text=Rent+kal.")
        contact_picker = pipeline.action_view({"type": "message", "text": "Rent kal."}, "en-IN")
        self.assertEqual(contact_picker["url"], "https://wa.me/?text=Rent+kal.")

    def test_email_requires_valid_address(self):
        view = pipeline.action_view(
            {"type": "email", "to": "owner@example.com", "subject": "Rent"}, "en-IN"
        )
        self.assertTrue(view["url"].startswith("mailto:owner@example.com?"))
        bad = pipeline.action_view(
            {"type": "email", "to": "not-an-email", "subject": "Rent"}, "en-IN"
        )
        self.assertTrue(bad["url"].startswith("mailto:?subject=Rent"))

    def test_normalise_attaches_command_and_task_action(self):
        payload = {
            "command": {"type": "search", "service": "youtube", "query": "lofi"},
            "tasks": [
                {
                    "title": "Pay rent",
                    "action": {"type": "search", "service": "maps", "query": "bank"},
                }
            ],
        }
        out = pipeline.normalize(payload, "YouTube lofi", "en-IN")
        self.assertEqual(out["kind"], "command")
        self.assertTrue(out["command"]["url"].startswith("https://www.youtube.com/"))
        self.assertTrue(
            out["tasks"][0]["action"]["url"].startswith("https://www.google.com/maps/")
        )
        self.assertTrue(out["summary"])

    def test_demo_youtube_command(self):
        out = pipeline.demo_analyze(
            "YouTube pe AR Rahman ke best songs search karo.", "en-IN", "en-IN"
        )
        self.assertEqual(out["tasks"], [])
        self.assertEqual(out["kind"], "command")
        self.assertEqual(out["command"]["service"], "youtube")
        self.assertEqual(out["command"]["detail"], "AR Rahman ke best songs")
        self.assertTrue(out["command"]["url"].startswith("https://www.youtube.com/"))

    def test_demo_command_label_in_hindi(self):
        out = pipeline.demo_analyze("YouTube pe lofi songs chalao", "hi-IN", "hi-IN")
        self.assertEqual(out["command"]["label"], "YouTube खोलें")

    def test_demo_call_needs_a_real_number(self):
        out = pipeline.demo_analyze("Mummy ko call karo", "hi-IN", "hi-IN")
        self.assertIsNone(out["command"])
        with_number = pipeline.demo_analyze("Mummy ko 98765 43210 par call karo", "hi-IN", "hi-IN")
        self.assertEqual(with_number["command"]["url"], "tel:+919876543210")


if __name__ == "__main__":
    unittest.main()
