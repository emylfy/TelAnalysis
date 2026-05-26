"""Media / voice / links breakdown for Telegram exports.

Pure functions over message lists; no UI."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from urllib.parse import urlparse

import jmespath


@dataclass
class MediaStats:
    by_kind: dict[str, int] = field(default_factory=dict)
    voice_total_seconds: int = 0
    voice_count: int = 0
    top_domains: list[tuple[str, int]] = field(default_factory=list)
    total_links: int = 0


_KIND_LABELS = {
    "text": "Text",
    "photo": "Photo",
    "video_file": "Video",
    "video_message": "Video msg (round)",
    "voice_message": "Voice",
    "audio_file": "Audio",
    "sticker": "Sticker",
    "animation": "Animation/GIF",
    "file": "File",
    "location": "Location",
    "contact": "Contact",
    "poll": "Poll",
    "service": "Service",
    "other": "Other",
}


def kind_label(kind: str) -> str:
    return _KIND_LABELS.get(kind, kind)


def _classify(m: dict) -> str:
    if not isinstance(m, dict):
        return "other"
    if m.get("type") == "service":
        return "service"
    media_type = m.get("media_type")
    if media_type:
        return str(media_type)
    if "photo" in m:
        return "photo"
    if "poll" in m:
        return "poll"
    if "location_information" in m:
        return "location"
    if "contact_information" in m:
        return "contact"
    if "file" in m:
        return "file"
    text = m.get("text")
    if text or m.get("text_entities"):
        return "text"
    return "other"


def _extract_domain(url: str) -> str | None:
    if not url:
        return None
    try:
        # urlparse needs a scheme; if missing, prepend http:// to parse netloc
        if "://" not in url:
            url = "http://" + url
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return _normalize_host(netloc) if netloc else None
    except Exception:
        return None


# Hosts that point to the same brand under different DNS labels — without
# this, "youtu.be" and "youtube.com" appear as separate entries and the
# Top Domains chart undercounts both.
_HOST_ALIASES: dict[str, str] = {
    # YouTube
    "youtu.be": "youtube.com",
    "m.youtube.com": "youtube.com",
    "music.youtube.com": "youtube.com",
    # Twitter / X
    "x.com": "twitter.com",
    "mobile.twitter.com": "twitter.com",
    "t.co": "twitter.com",
    "vxtwitter.com": "twitter.com",
    "fxtwitter.com": "twitter.com",
    # Telegram
    "t.me": "telegram.org",
    "telegram.me": "telegram.org",
    # GitHub
    "raw.githubusercontent.com": "github.com",
    "gist.github.com": "github.com",
    # Reddit
    "old.reddit.com": "reddit.com",
    "redd.it": "reddit.com",
    # Instagram
    "instagr.am": "instagram.com",
    # Spotify
    "open.spotify.com": "spotify.com",
    # Other common shorteners → keep as-is (the brand IS the short form)
}


def _normalize_host(netloc: str) -> str:
    return _HOST_ALIASES.get(netloc, netloc)


def analyze(messages: list[dict]) -> MediaStats:
    by_kind: Counter = Counter()
    voice_seconds = 0
    voice_count = 0
    domains: Counter = Counter()
    total_links = 0

    for m in messages:
        if not isinstance(m, dict):
            continue
        kind = _classify(m)
        by_kind[kind] += 1

        if kind == "voice_message":
            dur = m.get("duration_seconds")
            try:
                voice_seconds += int(dur or 0)
                voice_count += 1
            except (ValueError, TypeError):
                pass

        ents = jmespath.search("text_entities[*]", m) or []
        for e in ents:
            if not isinstance(e, dict):
                continue
            t = e.get("type")
            if t in ("link", "text_link"):
                url = e.get("href") or e.get("text") or ""
                if url:
                    total_links += 1
                    d = _extract_domain(url)
                    if d:
                        domains[d] += 1

    return MediaStats(
        by_kind=dict(by_kind),
        voice_total_seconds=voice_seconds,
        voice_count=voice_count,
        top_domains=domains.most_common(30),
        total_links=total_links,
    )


def humanize_duration(seconds: int) -> str:
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    s = seconds % 60
    if minutes < 60:
        return f"{minutes}m {s}s"
    hours = minutes // 60
    m = minutes % 60
    if hours < 24:
        return f"{hours}h {m}m"
    days = hours // 24
    h = hours % 24
    return f"{days}d {h}h"
