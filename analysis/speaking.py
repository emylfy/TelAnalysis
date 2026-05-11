"""Speaking-style metrics per user.

Pure functions. Counts characters/words, message extremes, and tone signals
(questions, exclamations, ALL-CAPS bursts).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

# 4-way time-of-day buckets
_TIME_BUCKETS = [
    ("night", range(0, 6)),  # 00-05
    ("morning", range(6, 12)),  # 06-11
    ("day", range(12, 18)),  # 12-17
    ("evening", range(18, 24)),  # 18-23
]
_HOUR_TO_BUCKET = {h: name for name, hrs in _TIME_BUCKETS for h in hrs}

# Length buckets in characters
_LENGTH_BUCKETS = [
    ("<30", lambda c: c < 30),
    ("30-100", lambda c: 30 <= c < 100),
    ("100-300", lambda c: 100 <= c < 300),
    ("300+", lambda c: c >= 300),
]


def _parse(s) -> datetime | None:
    if not isinstance(s, str):
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


@dataclass
class SpeakingStyle:
    user_id: str
    name: str
    msg_count: int
    avg_chars: float
    avg_words: float
    median_chars: int
    longest_text: str
    longest_chars: int
    question_ratio: float  # share of msgs with '?'
    exclamation_ratio: float  # share of msgs with '!'
    caps_ratio: float  # share of msgs that are mostly uppercase
    time_of_day: dict[str, int] = field(default_factory=dict)  # bucket -> count
    length_buckets: dict[str, int] = field(default_factory=dict)  # bucket -> count
    # First-message-of-day distribution as minutes-from-midnight (0..1439).
    # Per-day earliest message — separates "writes first thing in the morning"
    # from "active in the afternoon", which time_of_day buckets blur together.
    first_msg_minutes: list[int] = field(default_factory=list)
    # Replies (msg with reply_to_message_id) vs new sends. Reply-thread users
    # vs flat-style users have very different conversation rhythms — surfacing
    # this separates "always quotes back" from "drops one-liners".
    reply_count: int = 0  # share = reply_count / msg_count

    @property
    def first_msg_median(self) -> int | None:
        """Median minutes-from-midnight across all active days. None if no data."""
        if not self.first_msg_minutes:
            return None
        s = sorted(self.first_msg_minutes)
        return s[len(s) // 2]

    @property
    def reply_ratio(self) -> float:
        """Share of this user's messages that quote-reply to another message."""
        return self.reply_count / self.msg_count if self.msg_count else 0.0

    @property
    def first_msg_median_hhmm(self) -> str:
        m = self.first_msg_median
        if m is None:
            return "—"
        return f"{m // 60:02d}:{m % 60:02d}"

    @property
    def persona(self) -> str:
        """Single-word persona based on dominant time bucket."""
        if not self.time_of_day:
            return "?"
        dominant = max(self.time_of_day.items(), key=lambda kv: kv[1])[0]
        return {
            "night": "🌙 night owl",
            "morning": "🌅 early bird",
            "day": "☀️ daytime",
            "evening": "🌆 evening",
        }.get(dominant, dominant)

    @property
    def length_persona(self) -> str:
        """How long their messages typically are."""
        if not self.length_buckets:
            return "?"
        dominant = max(self.length_buckets.items(), key=lambda kv: kv[1])[0]
        return {
            "<30": "📝 one-liner",
            "30-100": "💬 short",
            "100-300": "📄 elaborate",
            "300+": "📜 essayist",
        }.get(dominant, dominant)


def _msg_text(m: dict) -> str:
    """Combine text + caption + text_entities into one string per message."""
    parts: list[str] = []
    t = m.get("text")
    if isinstance(t, str):
        parts.append(t)
    elif isinstance(t, list):
        for item in t:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                v = item.get("text")
                if isinstance(v, str):
                    parts.append(v)
    c = m.get("caption")
    if isinstance(c, str):
        parts.append(c)
    return " ".join(parts).strip()


def _is_caps(text: str) -> bool:
    """Heuristic: message is 'shouting' if it has ≥5 letters and >60% uppercase."""
    letters = [c for c in text if c.isalpha()]
    if len(letters) < 5:
        return False
    uppers = sum(1 for c in letters if c.isupper())
    return uppers / len(letters) > 0.6


def analyze(messages: list[dict]) -> dict[str, SpeakingStyle]:
    """Return {user_id: SpeakingStyle}. Skips users with no text messages."""
    user_texts: dict[str, list[str]] = defaultdict(list)
    user_names: dict[str, str] = {}
    user_hours: dict[str, list[int]] = defaultdict(list)
    # Per-day earliest message timestamp (minutes-from-midnight) per user.
    # Walk in chronological order; first message on each calendar date wins.
    user_first_per_day: dict[str, dict[str, int]] = defaultdict(dict)
    user_replies: dict[str, int] = defaultdict(int)

    for m in messages:
        if not isinstance(m, dict):
            continue
        uid = m.get("from_id")
        if not uid:
            continue
        uid = str(uid).replace(" ", "")
        user_names.setdefault(uid, m.get("from") or uid)
        text = _msg_text(m)
        if not text:
            continue
        user_texts[uid].append(text)
        if m.get("reply_to_message_id") is not None:
            user_replies[uid] += 1
        d = _parse(m.get("date"))
        if d is not None:
            user_hours[uid].append(d.hour)
            day_key = d.strftime("%Y-%m-%d")
            mins = d.hour * 60 + d.minute
            existing = user_first_per_day[uid].get(day_key)
            if existing is None or mins < existing:
                user_first_per_day[uid][day_key] = mins

    out: dict[str, SpeakingStyle] = {}
    for uid, texts in user_texts.items():
        n = len(texts)
        if n == 0:
            continue
        chars = [len(t) for t in texts]
        words = [len(t.split()) for t in texts]
        sorted_chars = sorted(chars)
        median_c = sorted_chars[n // 2]
        longest_idx = max(range(n), key=lambda i: chars[i])
        questions = sum(1 for t in texts if "?" in t)
        excl = sum(1 for t in texts if "!" in t)
        caps = sum(1 for t in texts if _is_caps(t))

        # Time-of-day distribution
        time_of_day = {name: 0 for name, _ in _TIME_BUCKETS}
        for h in user_hours.get(uid, []):
            bucket = _HOUR_TO_BUCKET.get(h)
            if bucket:
                time_of_day[bucket] += 1

        # Length-bucket distribution
        length_buckets = {name: 0 for name, _ in _LENGTH_BUCKETS}
        for c in chars:
            for name, pred in _LENGTH_BUCKETS:
                if pred(c):
                    length_buckets[name] += 1
                    break

        out[uid] = SpeakingStyle(
            user_id=uid,
            name=user_names.get(uid, uid),
            msg_count=n,
            avg_chars=sum(chars) / n,
            avg_words=sum(words) / n,
            median_chars=median_c,
            longest_text=texts[longest_idx],
            longest_chars=chars[longest_idx],
            question_ratio=questions / n,
            exclamation_ratio=excl / n,
            caps_ratio=caps / n,
            time_of_day=time_of_day,
            length_buckets=length_buckets,
            first_msg_minutes=list(user_first_per_day.get(uid, {}).values()),
            reply_count=user_replies.get(uid, 0),
        )
    return out
