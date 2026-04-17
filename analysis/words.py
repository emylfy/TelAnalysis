"""Per-user word + sentiment + contact extraction.
Pure functions: take messages, return structured results."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

import jmespath
import phonenumbers
from validate_email import validate_email
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

import nltk_analyse

_analyzer = SentimentIntensityAnalyzer()

_action_map = {
    "invite_members": "Invite Member",
    "remove_members": "Kicked Members",
    "join_group_by_link": "Joined by Link",
    "pin_message": "Pinned Message",
}


@dataclass
class UserStats:
    user_id: str
    name: str
    messages: list[tuple[str, float]] = field(default_factory=list)
    avg_sentiment: float = 0.0
    top_words: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class WordsResult:
    users: dict[str, UserStats]
    emails: list[str]
    phones: list[str]
    chat_top_words: list[tuple[str, int]]
    chat_avg_sentiment: float


def _sentiment(text: str) -> float:
    try:
        return float(_analyzer.polarity_scores(str(text))["compound"])
    except Exception:
        return 0.0


def _extract_contacts(text: str) -> tuple[list[str], list[str]]:
    emails: list[str] = []
    for e in re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text):
        if validate_email(e, verify=False):
            emails.append(e)
    phones: list[str] = []
    for p in re.findall(
        r"\+?[0-9]{1,3}?[-. (]?[0-9]{1,4}[-. )]?[0-9]{1,4}[-. ]?[0-9]{1,9}", text
    ):
        try:
            parsed = phonenumbers.parse(p, None)
            if phonenumbers.is_valid_number(parsed):
                phones.append(p)
        except Exception:
            pass
    return emails, phones


def _extract_text(message) -> set[str]:
    """Recursively collect text fragments from a message dict."""
    out: set[str] = set()
    if isinstance(message, dict):
        t = message.get("text")
        if isinstance(t, str) and t.strip():
            out.add(t)
        elif isinstance(t, list):
            for item in t:
                if isinstance(item, str):
                    out.add(item)
        c = message.get("caption")
        if isinstance(c, str) and c.strip():
            out.add(c)
        ents = jmespath.search("text_entities[*].text", message)
        if ents:
            for e in ents:
                out.add(e)
        if "forwarded_from" in message:
            out.update(_extract_text(message["forwarded_from"]))
        if "reply_to_message" in message:
            out.update(_extract_text(message["reply_to_message"]))
        for v in message.values():
            if isinstance(v, (list, dict)):
                out.update(_extract_text(v))
    elif isinstance(message, list):
        for item in message:
            out.update(_extract_text(item))
    return out


def analyze(messages: list[dict], most_com: int = 30) -> WordsResult:
    """Process messages → per-user stats + global aggregates."""
    user_msgs: dict[str, list[tuple[str, float]]] = defaultdict(list)
    user_names: dict[str, str] = {}
    emails: list[str] = []
    phones: list[str] = []

    for m in messages:
        if not isinstance(m, dict):
            continue
        uid = m.get("from_id")
        if not uid:
            uid = m.get("actor_id")
            if uid is None:
                continue
            uid = str(uid).replace(" ", "")
            action = m.get("action")
            if action:
                tex = m.get("text") or ""
                action_text = _action_map.get(action, action)
                if action in ("invite_members", "remove_members"):
                    members = m.get("members") or []
                    members_str = ",".join(str(x) for x in members if x)
                    user_msgs[uid].append((f"{action_text} - {members_str}", 0.0))
                else:
                    user_msgs[uid].append((f"{action_text} {tex}", 0.0))
                continue

        uid = str(uid).replace(" ", "")
        if uid not in user_names:
            user_names[uid] = m.get("from") or uid

        for fragment in _extract_text(m):
            if not fragment:
                continue
            score = _sentiment(fragment)
            user_msgs[uid].append((fragment, score))
            ex_emails, ex_phones = _extract_contacts(fragment)
            emails.extend(ex_emails)
            phones.extend(ex_phones)

    # Per-user aggregates
    users: dict[str, UserStats] = {}
    all_tokens: list[str] = []
    for uid, msgs in user_msgs.items():
        sentiments = [s for _, s in msgs if isinstance(s, float)]
        avg = sum(sentiments) / len(sentiments) if sentiments else 0.0
        try:
            top, tokens = nltk_analyse.analyse(msgs, most_com)
        except Exception:
            top, tokens = [], []
        all_tokens.extend(tokens)
        users[uid] = UserStats(
            user_id=uid,
            name=user_names.get(uid, uid),
            messages=msgs,
            avg_sentiment=avg,
            top_words=list(top),
        )

    # Chat-wide aggregates
    try:
        chat_top, _ = nltk_analyse.analyse_all(all_tokens, most_com)
    except Exception:
        chat_top = []
    chat_top_pairs = list(chat_top)
    chat_sentiments = [_sentiment(w) for w, _ in chat_top_pairs]
    chat_avg = sum(chat_sentiments) / len(chat_sentiments) if chat_sentiments else 0.0

    return WordsResult(
        users=users,
        emails=sorted(set(emails)),
        phones=sorted(set(phones)),
        chat_top_words=chat_top_pairs,
        chat_avg_sentiment=chat_avg,
    )
