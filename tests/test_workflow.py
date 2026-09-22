import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import socket
import re
import time
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from newsagent.core import Store, write_json, validate_config
from newsagent.editorial import validate_issue
from newsagent.net import safe_url, public_addresses
from newsagent.server import make_server
from newsagent.sources import item, normalize_social, collect_feed, collect_social, needs_browser_bridge


def fixture(store):
    timestamp = datetime.now(timezone.utc).isoformat()
    source = {"id": "release", "name": "Example release", "platform": "web"}
    evidence = item(source, "A release", "https://example.org/release", "The new release adds a local test runner for evaluating generated code.", timestamp, "retrieved page")
    packet = {"id": "packet", "profile": store.config()["profile"], "collected_at": timestamp,
              "window_start": timestamp, "items": [evidence], "coverage": [], "selection_note": "Test sample"}
    issue = {"title": "Test briefing", "overview": "One useful development.", "stories": [{
        "event_key": "local-runner", "title": "Local evaluation becomes available", "importance": "understand", "topic": "engineering",
        "what_changed": "The release adds a local test runner.", "why_it_matters": "Testing generated code fits your engineering interests.",
        "limitations": "We have not benchmarked it.", "next_step": "Try a public example.", "durability": "Evaluation is a transferable skill.",
        "evidence": [{"source_id": evidence["id"], "claim": "A local runner is available.", "quote": "The new release adds a local test runner"}],
        "watch_source_id": "", "watch_reason": ""}], "low_priority": []}
    write_json(store.home / "packet.json", packet)
    return packet, issue


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.store.init()
        self.packet, self.issue = fixture(self.store)

    def tearDown(self):
        self.temp.cleanup()

    def test_rejects_invented_citation_and_quote(self):
        for key, bad in (("source_id", "invented"), ("quote", "This quote was never in the article")):
            altered = copy.deepcopy(self.issue)
            altered["stories"][0]["evidence"][0][key] = bad
            with self.assertRaises(ValueError):
                validate_issue(altered, self.packet)

    def test_unknown_date_or_video_metadata_cannot_be_main_story(self):
        for field, value in (("published_at", None), ("access", "video metadata only")):
            packet = copy.deepcopy(self.packet)
            packet["items"][0][field] = value
            with self.assertRaises(ValueError):
                validate_issue(self.issue, packet)
            issue = copy.deepcopy(self.issue)
            issue["stories"][0]["importance"] = "watch"
            self.assertGreater(validate_issue(issue, packet), 0)

    def test_publish_snapshot_survives_new_collection(self):
        saved = self.store.publish(self.issue)
        write_json(self.store.home / "packet.json", {**self.packet, "items": []})
        restored = self.store.history()[0]
        self.assertEqual(saved["evidence"], restored["evidence"])
        self.assertEqual(restored["evidence"][0]["text"], self.packet["items"][0]["text"])

    def test_failed_review_cannot_replace_valid_issue(self):
        good = self.store.publish(self.issue)
        broken = copy.deepcopy(self.issue)
        broken["stories"][0]["evidence"][0]["quote"] = "A completely invented quote instead"
        with patch("newsagent.models.generate", side_effect=[self.issue, broken, broken]) as model:
            with self.assertRaises(ValueError):
                self.store.generate()
            self.assertEqual(model.call_count, 3)
        self.assertEqual(self.store.history()[0]["id"], good["id"])

    def test_budget_and_repeated_event_rejected(self):
        altered = copy.deepcopy(self.issue)
        altered["stories"] *= 2
        with self.assertRaises(ValueError):
            validate_issue(altered, self.packet)
        altered = copy.deepcopy(self.issue)
        altered["overview"] = "word " * 3100
        with self.assertRaises(ValueError):
            validate_issue(altered, self.packet)

    def test_concise_fields_cannot_hide_long_prose_within_total_budget(self):
        for field, limit in {"title": 12, "what_changed": 45, "why_it_matters": 45,
                             "next_step": 25, "limitations": 40, "durability": 40}.items():
            draft = copy.deepcopy(self.issue)
            draft["stories"][0][field] = "word " * (limit + 1)
            with self.assertRaisesRegex(ValueError, "concise limit"):
                validate_issue(draft, self.packet)
        self.assertGreater(validate_issue(self.issue, self.packet), 0)

    def test_collect_filters_old_and_future_and_exposes_failures(self):
        cfg = self.store.config()
        cfg["sources"] = [{"id": "a", "name": "A", "url": "https://example.org/feed", "platform": "rss", "enabled": True},
                          {"id": "b", "name": "B", "url": "https://example.net/feed", "platform": "rss", "enabled": True}]
        self.store.save_config(cfg)
        recent = self.packet["items"][0]
        old = {**recent, "id": "old", "published_at": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()}
        future = {**recent, "id": "future", "published_at": (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()}
        with patch("newsagent.sources.collect", side_effect=[[recent, old, future], ValueError("Login needed")]):
            result = self.store.collect(1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["coverage"][1]["status"], "unavailable")

    def test_lock_releases_and_stale_packet_cannot_generate(self):
        with self.store.lock():
            with self.assertRaises(ValueError):
                with self.store.lock():
                    pass
        with self.store.lock():
            pass
        self.packet["collected_at"] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        write_json(self.store.home / "packet.json", self.packet)
        with patch("newsagent.models.generate") as generate:
            with self.assertRaises(ValueError):
                self.store.generate()
            generate.assert_not_called()

    def test_feedback_requires_real_issue_and_enters_next_prompt(self):
        with self.assertRaises(ValueError):
            self.store.add_feedback("missing", "local-runner", "useful")
        issue = self.store.publish(self.issue)
        self.store.add_feedback(issue["id"], "local-runner", "not-relevant")
        with patch("newsagent.models.generate", return_value=self.issue) as generate:
            self.store.generate()
        self.assertIn('not-relevant', generate.call_args_list[0].args[0])

    def test_enrichment_is_bounded_and_failed_video_stays_metadata(self):
        packet = copy.deepcopy(self.packet)
        base = packet["items"][0]
        packet["items"] = [dict(base, id=f"video-{i}", platform="youtube", access="video metadata only") for i in range(3)]
        packet["items"] += [dict(base, id=f"feed-{i}", platform="rss", access="feed text") for i in range(5)]
        with patch("newsagent.sources.transcript", side_effect=ValueError("No captions")) as transcripts, \
                patch("newsagent.sources.fetch", return_value=("Long source content. " * 20, "https://example.org/release")) as pages:
            result = self.store.enrich(packet, lambda text: None)
        self.assertEqual(transcripts.call_count, 2)
        self.assertEqual(pages.call_count, 4)
        self.assertIn("metadata only", result["items"][0]["access"])
        self.assertIn("unavailable", result["items"][0]["access"])
        self.assertEqual(result["items"][2]["access"], "video metadata only")
        self.assertIn("Retrieved content", result["items"][3]["text"])


class ConnectorTests(unittest.TestCase):
    def test_private_addresses_credentials_and_dns_rebinding_targets_rejected(self):
        for url in ("file:///etc/passwd", "http://127.0.0.1", "https://user:secret@example.com", "http://169.254.169.254/", "http://[::1]/"):
            with self.assertRaises(ValueError):
                safe_url(url)
        with patch("socket.getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 443))]):
            with self.assertRaises(ValueError):
                public_addresses("example.org", 443)

    def test_instagram_caption_without_permalink_remains_limited(self):
        source = {"id": "ig", "name": "Example", "platform": "instagram", "url": "https://www.instagram.com/example/"}
        result = normalize_social(source, [{"caption": "A caption containing a claim", "date": "2026-09-20"}])
        self.assertEqual(result[0]["url"], source["url"])
        self.assertIn("profile link only", result[0]["access"])
        with self.assertRaises(ValueError):
            normalize_social(source, {"success": True})
        with self.assertRaises(ValueError):
            normalize_social(source, [])

    def test_linkedin_company_route_keeps_page_evidence_undated(self):
        source = {"id": "a16z", "name": "a16z", "platform": "linkedin", "url": "https://www.linkedin.com/company/a16z/", "enabled": True}
        config = json.loads((Path(__file__).resolve().parents[1] / "config/starter.json").read_text())
        config["sources"] = [source]
        validate_config(config)
        self.assertFalse(needs_browser_bridge(source))
        payload = {"sections": {"posts": "A company post with content and claims. " * 10}}
        for data in (payload, {"content": [{"type": "text", "text": json.dumps(payload)}]}):
            with patch("newsagent.sources.command", return_value=json.dumps(data)) as command:
                result = collect_social(source)
            self.assertEqual(command.call_args.args[0][2], "linkedin.get_company_posts")
            self.assertIsNone(result[0]["published_at"])
            self.assertIn("individual dates", result[0]["access"])
        with patch("newsagent.sources.command", return_value=json.dumps({"sections": {"about": "Not posts"}})):
            with self.assertRaises(ValueError):
                collect_social(source)
        source["url"] = "https://www.linkedin.com/school/y-combinator/"
        validate_config(config)
        with patch("newsagent.sources.command") as command:
            with self.assertRaisesRegex(ValueError, "school pages"):
                collect_social(source)
            command.assert_not_called()

    def test_atom_dates_and_rss_partial_content(self):
        source = {"id": "feed", "name": "Example", "platform": "rss", "url": "https://example.org/feed"}
        atom = '<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Update</title><link href="/post"/><updated>2026-09-20T10:00:00Z</updated><content>Actual content</content></entry></feed>'
        with patch("newsagent.sources.fetch", return_value=(atom, source["url"])):
            result = collect_feed(source)
        self.assertEqual(result[0]["url"], "https://example.org/post")
        self.assertEqual(result[0]["published_at"], "2026-09-20T10:00:00+00:00")
        self.assertIn("partial", result[0]["access"])


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.store.init()
        self.server = make_server(self.store, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def test_host_csrf_and_static_file_boundary(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.base + "/api/state", headers={"Host": "attacker.example"}))
        self.assertEqual(error.exception.code, 403)
        error.exception.close()
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.base + "/api/run", data=b'{}', headers={"Content-Type": "application/json"}))
        self.assertEqual(error.exception.code, 403)
        error.exception.close()
        with self.assertRaises(HTTPError) as error:
            urlopen(self.base + "/.local/config.json")
        self.assertEqual(error.exception.code, 404)
        error.exception.close()
        with urlopen(self.base) as response:
            self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])
            self.assertNotIn("__SESSION_TOKEN__", response.read().decode())

    def test_website_generation_saves_reviewed_issue(self):
        _, draft = fixture(self.store)
        reviewed = copy.deepcopy(draft)
        reviewed["title"] = "Reviewed edition"
        with urlopen(self.base) as response:
            token = re.search(r'name="newsagent-session" content="([^"]+)"', response.read().decode())[1]
        request = Request(self.base + "/api/run", data=json.dumps({"action": "generate", "days": 1}).encode(),
                          headers={"Content-Type": "application/json", "X-Newsagent-Token": token, "Origin": self.base})
        with patch("newsagent.models.generate", side_effect=[draft, reviewed]):
            with urlopen(request) as response:
                self.assertTrue(json.load(response)["ok"])
            for _ in range(50):
                with urlopen(self.base + "/api/state") as response:
                    state = json.load(response)
                if not state["job"]["running"]:
                    break
                time.sleep(.02)
        self.assertFalse(state["job"]["running"])
        self.assertEqual(state["job"]["error"], "")
        self.assertEqual(state["issues"][0]["content"]["title"], "Reviewed edition")

    def test_setup_check_validates_draft_without_saving_or_generating(self):
        with urlopen(self.base) as response:
            token = re.search(r'name="newsagent-session" content="([^"]+)"', response.read().decode())[1]
        original = self.store.config()
        draft = copy.deepcopy(original)
        draft['profile']['description'] = 'A different person'
        request = Request(self.base + '/api/check', data=json.dumps(draft).encode(),
                          headers={'Content-Type':'application/json', 'X-Newsagent-Token':token})
        with patch('newsagent.models.generate') as model:
            with urlopen(request) as response:
                self.assertTrue(json.load(response)['checks'])
            model.assert_not_called()
        self.assertEqual(self.store.config(), original)

        draft['provider']['backend'] = 'invalid'
        request.data = json.dumps(draft).encode()
        with self.assertRaises(HTTPError) as error:
            urlopen(request)
        self.assertEqual(error.exception.code, 400)
        error.exception.close()
        self.assertEqual(self.store.config(), original)

    def test_configuration_download_contains_only_settings(self):
        fixture(self.store)
        with urlopen(self.base + '/api/export') as response:
            self.assertIn('attachment;', response.headers['Content-Disposition'])
            self.assertEqual(json.load(response), self.store.config())


if __name__ == "__main__":
    unittest.main()
