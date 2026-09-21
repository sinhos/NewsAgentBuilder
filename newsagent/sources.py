"""Read-only adapters. Installed commands are used without shell interpolation."""
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit, urljoin

from .net import fetch, safe_url


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.links, self.hidden = [], [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.hidden += 1
        if tag == "a":
            self.links.extend(v for k, v in attrs if k == "href" and v)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain(text):
    parser = TextParser()
    parser.feed(str(text))
    return " ".join(" ".join(parser.parts).split())


def date_iso(value):
    if not value:
        return None
    try:
        if isinstance(value, (int, float)):
            dt = datetime.fromtimestamp(value, timezone.utc)
        else:
            v = str(value).strip()
            if re.fullmatch(r"\d{8}", v):
                dt = datetime.strptime(v, "%Y%m%d")
            else:
                try:
                    dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
                except ValueError:
                    dt = parsedate_to_datetime(v)
        return dt.replace(tzinfo=dt.tzinfo or timezone.utc).astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError, OverflowError):
        return None


def item(source, title, url, text, published=None, access="text", links=None):
    url = safe_url(url)
    text = str(text).strip()
    if not text:
        raise ValueError("Empty source content")
    key = hashlib.sha256((url + "\n" + text).encode()).hexdigest()[:20]
    return {"id": key, "source_id": source["id"], "platform": source["platform"],
            "source_name": source["name"], "title": plain(title)[:300], "url": url,
            "text": text[:20000], "published_at": date_iso(published),
            "date_raw": str(published or ""), "access": access,
            "retrieved_at": datetime.now(timezone.utc).isoformat(), "links": (links or [])[:12]}


def command(args, timeout=75):
    if not shutil.which(args[0]):
        raise ValueError(f"Install {args[0]} to use this connector")
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        # Upstream errors can include personal URLs/tokens. Keep logs out of UI.
        raise ValueError(f"{args[0]} failed; check its connection/login locally (exit {result.returncode})")
    if not result.stdout.strip():
        raise ValueError("Connector returned no content")
    return result.stdout


def rows(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "rows", "items", "posts", "results"):
            if key in data:
                return rows(data[key])
    raise ValueError("Unrecognized connector response; no coverage claimed")


def normalize_social(source, data):
    output = []
    for row in rows(data):
        if not isinstance(row, dict):
            continue
        text = row.get("text") or row.get("body") or row.get("caption") or row.get("raw_text")
        if not isinstance(text, str) or not text.strip():
            continue
        url = row.get("url") or row.get("post_url") or row.get("permalink")
        if not url and row.get("shortcode") and source["platform"] == "instagram":
            url = "https://www.instagram.com/p/" + str(row["shortcode"]) + "/"
        # Some Instagram adapter versions omit permalinks: attribution remains profile-level.
        access = "post text" if url else "caption; profile link only"
        output.append(item(source, text[:140], url or source["url"], text,
                           row.get("created_at") or row.get("posted_at") or row.get("date"), access,
                           re.findall(r'https?://[^\s<>"\]]+', text)))
    if not output:
        raise ValueError("No usable posts returned; connection or empty feed is unverified")
    return output


def collect_social(source):
    p = urlsplit(source["url"])
    handle = p.path.strip("/").split("/")[0].lstrip("@")
    if source["platform"] == "x":
        args = ["opencli", "twitter", "tweets", handle, "--limit", "8", "-f", "json"]
    elif source["platform"] == "instagram":
        args = ["opencli", "instagram", "user", handle, "--limit", "8", "-f", "json"]
    else:
        args = ["opencli", "linkedin", "posts", "--profile-url", source["url"], "--limit", "8", "-f", "json"]
    return normalize_social(source, json.loads(command(args)))


def collect_feed(source):
    body, base = fetch(source["url"])
    declarations = re.sub(r"<!\[CDATA\[.*?\]\]>|<!--.*?-->", "", body, flags=re.S).upper()
    if "<!DOCTYPE" in declarations or "<!ENTITY" in declarations:
        raise ValueError("Unsupported XML declarations")
    root = ET.fromstring(body)
    entries = root.findall(".//item") or root.findall("{http://www.w3.org/2005/Atom}entry")
    output = []
    for entry in entries[:12]:
        fields = {e.tag.split("}")[-1]: e for e in entry}
        def value(key):
            e = fields.get(key)
            return "" if e is None else "".join(e.itertext())
        link = value("link")
        if not link:
            for e in entry:
                if e.tag.split("}")[-1] == "link" and e.get("rel", "alternate") == "alternate":
                    link = e.get("href", "")
                    break
        raw = value("encoded") or value("content") or value("description") or value("summary")
        parser = TextParser()
        parser.feed(raw)
        if link:
            output.append(item(source, value("title"), urljoin(base, link), plain(raw) or value("title"),
                               value("published") or value("pubDate") or value("updated"),
                               "feed text; may be partial", [urljoin(base, u) for u in parser.links]))
    if not output:
        raise ValueError("Feed returned no usable entries")
    return output


def collect_youtube(source):
    raw = command(["yt-dlp", "--ignore-config", "--flat-playlist", "--playlist-end", "6",
                   "--dump-single-json", "--skip-download", "--socket-timeout", "15",
                   "--", source["url"]], timeout=90)
    data = json.loads(raw)
    dated = {}
    channel_id = data.get("channel_id") or data.get("id", "")
    if re.fullmatch(r"UC[A-Za-z0-9_-]{22}", channel_id):
        try:
            feed, _ = fetch("https://www.youtube.com/feeds/videos.xml?channel_id=" + channel_id)
            if "<!ENTITY" not in feed.upper() and "<!DOCTYPE" not in feed.upper():
                root = ET.fromstring(feed)
                for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                    video = entry.findtext("{http://www.youtube.com/xml/schemas/2015}videoId")
                    published = entry.findtext("{http://www.w3.org/2005/Atom}published")
                    dated[video] = published
        except Exception:
            pass  # Metadata remains explicitly undated if the channel feed fails.
    output = []
    for entry in (data.get("entries") or [data])[:6]:
        if not entry:
            continue
        vid = entry.get("id", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
            continue
        url = "https://www.youtube.com/watch?v=" + vid
        output.append(item(source, entry.get("title", "Video"), url,
                           entry.get("description") or entry.get("title", "Video metadata"),
                           entry.get("timestamp") or entry.get("upload_date") or dated.get(vid), "video metadata only"))
    if not output:
        raise ValueError("YouTube returned no usable videos")
    return output


def transcript(url):
    safe_url(url)
    if urlsplit(url).hostname not in ("youtube.com", "www.youtube.com", "youtu.be"):
        raise ValueError("Expected a YouTube URL")
    with tempfile.TemporaryDirectory(prefix="newsagent-transcript-") as temp:
        command(["yt-dlp", "--ignore-config", "--skip-download", "--write-subs", "--write-auto-subs",
                 "--sub-langs", "en.*,en", "--sub-format", "vtt", "--no-playlist",
                 "--socket-timeout", "15", "-o", str(Path(temp) / "video.%(ext)s"), "--", url], 90)
        files = sorted(Path(temp).glob("*.vtt"))
        if not files:
            raise ValueError("Transcript unavailable; do not treat metadata as the video")
        lines, seen, timestamp = [], set(), ""
        for line in files[0].read_text().splitlines():
            if " --> " in line:
                timestamp = line.split(" --> ")[0]
            elif line.strip() and not line.startswith(("WEBVTT", "Kind:", "Language:")) and not line.isdigit():
                clean = plain(html.unescape(line))
                if clean and clean not in seen:
                    lines.append(timestamp + " " + clean)
                    seen.add(clean)
        return "\n".join(lines)[:50000]


def collect(source):
    if source["platform"] in ("x", "linkedin", "instagram"):
        return collect_social(source)
    if source["platform"] == "youtube":
        return collect_youtube(source)
    if source["platform"] == "rss":
        return collect_feed(source)
    body, url = fetch(source["url"])
    parser = TextParser()
    parser.feed(body)
    return [item(source, source["name"], url, plain(body), access="web page; date unknown",
                 links=[urljoin(url, link) for link in parser.links])]
