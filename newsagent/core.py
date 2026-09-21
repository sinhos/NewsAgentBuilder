import contextlib
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import tempfile
import uuid

from . import models, sources
from .editorial import prompt, validate_issue
from .net import safe_url

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HOME = ROOT / ".local"
PLATFORMS = {"rss", "web", "youtube", "x", "instagram", "linkedin"}


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".write-")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def validate_config(config):
    if not isinstance(config, dict) or set(config) != {"profile", "sources", "provider"}:
        raise ValueError("Settings need profile, sources, and provider")
    profile = config["profile"]
    if not isinstance(profile, dict) or set(profile) != {"description", "interests", "avoid", "reading_minutes", "language"}:
        raise ValueError("Invalid profile fields")
    for field in ("description", "interests", "avoid", "language"):
        if not isinstance(profile[field], str) or len(profile[field]) > 6000:
            raise ValueError("Profile fields must be text under 6,000 characters")
    if type(profile["reading_minutes"]) is not int or not 3 <= profile["reading_minutes"] <= 20:
        raise ValueError("Reading budget must be 3–20 minutes")
    if not isinstance(config["sources"], list) or len(config["sources"]) > 30:
        raise ValueError("Use at most 30 sources for this personal version")
    ids = set()
    for source in config["sources"]:
        if not isinstance(source, dict) or set(source) != {"id", "name", "platform", "url", "enabled"}:
            raise ValueError("Invalid source fields")
        if not re.fullmatch(r"[a-z0-9-]{1,60}", source["id"]) or source["id"] in ids:
            raise ValueError("Source IDs must be unique lowercase names")
        ids.add(source["id"])
        if source["platform"] not in PLATFORMS or type(source["enabled"]) is not bool:
            raise ValueError("Invalid platform or enabled setting")
        if not isinstance(source["name"], str) or not 1 <= len(source["name"]) <= 150:
            raise ValueError("Source name must be 1–150 characters")
        source["url"] = safe_url(source["url"])
        from urllib.parse import urlsplit
        u = urlsplit(source["url"])
        allowed = {"youtube": {"www.youtube.com", "youtube.com", "youtu.be"},
                   "x": {"x.com", "www.x.com", "twitter.com", "www.twitter.com"},
                   "instagram": {"instagram.com", "www.instagram.com"},
                   "linkedin": {"linkedin.com", "www.linkedin.com"}}
        if source["platform"] in allowed and u.hostname not in allowed[source["platform"]]:
            raise ValueError("Source URL does not match its platform")
        if source["platform"] in ("x", "instagram") and not re.fullmatch(r"/[A-Za-z0-9_.]+/?", u.path):
            raise ValueError("Use an account URL, not an individual post")
        if source["platform"] == "linkedin" and not re.fullmatch(r"/in/[A-Za-z0-9_-]+/?", u.path):
            raise ValueError("This connector needs a LinkedIn /in/ profile URL")
    provider = config["provider"]
    if not isinstance(provider, dict) or set(provider) != {"backend", "model", "base_url", "key_env"}:
        raise ValueError("Invalid provider fields")
    if provider["backend"] not in ("codex", "ollama", "compatible"):
        raise ValueError("Unknown provider")
    if any(not isinstance(v, str) or len(v) > 300 for v in provider.values()):
        raise ValueError("Provider settings must be short text; keep keys in environment variables")
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", provider["key_env"]):
        raise ValueError("key_env must name an environment variable, not contain a secret")
    return config


class Store:
    def __init__(self, home=DEFAULT_HOME):
        self.home = Path(home).resolve()
        self.home.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.config_path = self.home / "config.json"
        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS issues (id TEXT PRIMARY KEY, created TEXT, payload TEXT);
                CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY, issue_id TEXT, event_key TEXT, verdict TEXT, created TEXT);
            """)
        (self.home / "history.sqlite3").chmod(0o600)

    @contextlib.contextmanager
    def db(self):
        connection = sqlite3.connect(self.home / "history.sqlite3", timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def init(self):
        if not self.config_path.exists():
            write_json(self.config_path, json.loads((ROOT / "config/starter.json").read_text()))

    def config(self):
        if not self.config_path.exists():
            raise ValueError("Run python3 -m newsagent init first")
        return validate_config(json.loads(self.config_path.read_text()))

    def save_config(self, config):
        with self.lock():
            write_json(self.config_path, validate_config(config))

    @contextlib.contextmanager
    def lock(self):
        # OS lock releases after interruption/crash; the file itself is harmless.
        import fcntl
        with (self.home / "run.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError("A collection or generation is already running") from exc
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def packet(self):
        path = self.home / "packet.json"
        if not path.exists():
            raise ValueError("Collect sources first")
        return json.loads(path.read_text())

    def is_running(self):
        try:
            with self.lock():
                return False
        except ValueError:
            return True

    def history(self):
        with self.db() as db:
            return [json.loads(row[0]) for row in db.execute("SELECT payload FROM issues ORDER BY created DESC LIMIT 30")]

    def previous(self):
        return [{"date": issue["created_at"], "stories": [
            {"event_key": s["event_key"], "title": s["title"], "what_changed": s["what_changed"]}
            for s in issue["content"]["stories"]]} for issue in self.history()[:7]]

    def feedback(self):
        with self.db() as db:
            return [{"event_key": r[0], "verdict": r[1]} for r in db.execute(
                "SELECT event_key, verdict FROM feedback ORDER BY id DESC LIMIT 30")]

    def add_feedback(self, issue_id, event_key, verdict):
        if verdict not in ("useful", "not-relevant", "already-knew", "unsupported", "go-deeper"):
            raise ValueError("Unknown feedback")
        with self.db() as db:
            row = db.execute("SELECT payload FROM issues WHERE id=?", (issue_id,)).fetchone()
            if not row or event_key not in [s["event_key"] for s in json.loads(row[0])["content"]["stories"]]:
                raise ValueError("Unknown story")
            db.execute("INSERT INTO feedback(issue_id,event_key,verdict,created) VALUES(?,?,?,?)",
                       (issue_id, event_key, verdict, now()))

    def collect(self, days=1, progress=lambda text: None):
        if not 1 <= days <= 14:
            raise ValueError("Lookback must be 1–14 days")
        with self.lock():
            config = self.config()
            start = datetime.now(timezone.utc) - timedelta(days=days)
            packet = {"id": uuid.uuid4().hex, "collected_at": now(), "window_start": start.isoformat(),
                      "profile": config["profile"], "items": [], "coverage": [], "selection_note": "At most 8 items per source, 40 overall; a bounded sample, not exhaustive monitoring."}
            bridge = False
            if any(s["enabled"] and s["platform"] in ("x", "linkedin", "instagram") for s in config["sources"]):
                progress("Checking browser connection")
                if shutil.which("opencli"):
                    try:
                        check = subprocess.run(["opencli", "doctor"], capture_output=True, text=True, timeout=20)
                        bridge = "[OK] Extension" in check.stdout and "[OK] Connectivity" in check.stdout
                    except subprocess.TimeoutExpired:
                        pass
            groups = []
            for source in config["sources"]:
                coverage = {"name": source["name"], "platform": source["platform"], "source_id": source["id"],
                            "url": source["url"], "status": "disabled", "detail": "Disabled in settings", "fetched": 0}
                if source["enabled"]:
                    progress("Reading " + source["name"])
                    try:
                        if source["platform"] in ("x", "linkedin", "instagram") and not bridge:
                            raise ValueError("OpenCLI browser extension is not connected. Connect your browser and sign in to this platform.")
                        fetched = sources.collect(source)
                        recent = [i for i in fetched if not i["published_at"] or
                                  start <= datetime.fromisoformat(i["published_at"]) <= datetime.now(timezone.utc)]
                        groups.append(recent[:8])
                        coverage.update(status="checked", fetched=len(fetched), detail=f"{len(recent)} in the lookback or undated; recent bounded sample only")
                    except Exception as exc:
                        detail = str(exc) if isinstance(exc, ValueError) else type(exc).__name__ + "; retry or check the connector locally"
                        coverage.update(status="unavailable", detail=detail)
                packet["coverage"].append(coverage)
            # Round robin prevents a prolific feed from filling the entire evidence budget.
            seen = set()
            for index in range(8):
                for group in groups:
                    if index < len(group) and group[index]["id"] not in seen and len(packet["items"]) < 40:
                        entry = group[index].copy()
                        entry["text"] = entry["text"][:5000]
                        packet["items"].append(entry)
                        seen.add(entry["id"])
            write_json(self.home / "packet.json", packet)
            write_json(self.home / "packets" / (packet["id"] + ".json"), packet)
            return packet

    def import_item(self, entry):
        with self.lock():
            packet = self.packet()
            required = {"title", "url", "text", "published_at", "platform", "access"}
            if not isinstance(entry, dict) or set(entry) != required or not all(isinstance(v, str) for v in entry.values()):
                raise ValueError("Import needs title, url, text, published_at, platform and access strings")
            if entry["platform"] not in PLATFORMS or len(entry["text"]) > 50000:
                raise ValueError("Invalid imported content")
            source = {"id": "manual", "name": "Explicitly imported evidence", "platform": entry["platform"]}
            normalized = sources.item(source, entry["title"], entry["url"], entry["text"], entry["published_at"], entry["access"])
            if len(packet["items"]) >= 60:
                raise ValueError("Evidence limit reached; start a new collection")
            packet["items"] = [i for i in packet["items"] if i["id"] != normalized["id"]] + [normalized]
            write_json(self.home / "packet.json", packet)
            return normalized

    def evidence(self, url, title, published="", youtube=False):
        if youtube:
            text, final = sources.transcript(url), url
        else:
            raw, final = sources.fetch(url)
            text = sources.plain(raw)
        return self.import_item({"title": title, "url": final, "text": text[:20000], "published_at": published,
                                 "platform": "youtube" if youtube else "web", "access": "transcript" if youtube else "retrieved page"})

    def enrich(self, packet, progress):
        """Small, explicit budget: two recent video transcripts and four short pages."""
        videos = pages = 0
        for entry in packet["items"]:
            video = entry["access"] == "video metadata only"
            page = entry["platform"] == "rss" and len(entry["text"]) < 600
            if video and (videos >= 2 or not entry["published_at"]):
                continue
            if page and pages >= 4:
                continue
            if not video and not page:
                continue
            videos += int(video)
            pages += int(page)
            progress("Reading supporting content: " + entry["title"][:70])
            try:
                if video:
                    full = sources.transcript(entry["url"])
                    access = "YouTube captions; visuals not inspected"
                else:
                    raw, _ = sources.fetch(entry["url"])
                    full = sources.plain(raw)
                    access = "page text; navigation may be included"
                if len(full) < 100:
                    raise ValueError("No substantive text retrieved")
                # Preserve original feed text so its known date/context is not lost.
                entry["text"] = (entry["text"] + "\n\nRetrieved content:\n" + full)[:12000]
                entry["access"] = access
            except Exception:
                entry["access"] += "; deeper retrieval unavailable"
        write_json(self.home / "packet.json", packet)
        write_json(self.home / "packets" / (packet["id"] + ".json"), packet)
        return packet

    def publish(self, content, reviewed_by="Codex conversation", packet=None, provider=None):
        packet = packet or self.packet()
        minutes = validate_issue(content, packet)
        identity = uuid.uuid4().hex
        envelope = {"id": identity, "created_at": now(), "packet_id": packet["id"],
                    "window_start": packet["window_start"], "collected_at": packet["collected_at"],
                    "reading_minutes": minutes, "content": content, "evidence": packet["items"],
                    "coverage": packet["coverage"], "selection_note": packet["selection_note"],
                    "reviewed_by": reviewed_by, "provider": provider or {"backend": "conversation", "model": "current Codex model"},
                    "verification": "Citation existence and exact excerpts checked in code. Claim support reviewed by a model, not independently certified."}
        with self.db() as db:
            db.execute("INSERT INTO issues VALUES(?,?,?)", (identity, envelope["created_at"], json.dumps(envelope)))
        write_json(self.home / "issues" / (identity + ".json"), envelope)
        return envelope

    def generate(self, progress=lambda text: None):
        with self.lock():
            packet = self.packet()
            packet["profile"] = self.config()["profile"]
            if datetime.now(timezone.utc) - datetime.fromisoformat(packet["collected_at"]) > timedelta(hours=36):
                raise ValueError("Evidence is over 36 hours old. Collect again before generating a daily briefing.")
            if not packet["items"]:
                raise ValueError("No evidence collected. Connect a source or import content first.")
            if sum(len(i["text"]) for i in packet["items"]) > 220000:
                raise ValueError("Evidence exceeds this version's input budget. Collect a smaller window or remove large imports.")
            packet = self.enrich(packet, progress)
            provider = self.config()["provider"]
            prior = {"issues": self.previous(), "feedback": self.feedback()}
            progress("Writing your briefing (this can take several minutes)")
            draft = models.generate(prompt(packet, prior), provider)
            progress("Reviewing claims, relevance and repetition")
            reviewed = models.generate(prompt(packet, prior, draft), provider)
            progress("Checking citations and reading time")
            try:
                validate_issue(reviewed, packet)
            except ValueError as exc:
                progress("Repairing an output validation error (one attempt)")
                repair = prompt(packet, prior, reviewed) + "\nVALIDATION ERROR TO FIX: " + str(exc)
                reviewed = models.generate(repair, provider)
            return self.publish(reviewed, "second pass by the same model", packet, provider)
