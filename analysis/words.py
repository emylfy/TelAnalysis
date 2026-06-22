"""Per-user word + sentiment + contact extraction.
Pure functions: take messages, return structured results."""

from __future__ import annotations

import math as _math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import jmespath
import phonenumbers
from validate_email import validate_email

from . import nltk_analyse
from . import sentiment as _sentiment_mod
from .utils import DEDUP_MIN_CHARS, display_name, is_bot_name

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
    total_tokens: int = 0
    unique_tokens: int = 0
    # Token list kept around so we can compute length-insensitive lexical
    # diversity (MTLD). Filled by analyse() — empty for legacy callers.
    _tokens: list[str] = field(default_factory=list, repr=False)

    @property
    def ttr(self) -> float:
        """Naive type-token ratio. Length-sensitive — prefer .mtld for
        cross-user comparison."""
        return self.unique_tokens / self.total_tokens if self.total_tokens else 0.0

    @property
    def mtld(self) -> float:
        """Measure of Textual Lexical Diversity — bidirectional MTLD.
        Reports the average run length until TTR drops to 0.72 (factor).
        Higher = more diverse. Length-insensitive (unlike raw TTR).
        Returns 0.0 when there isn't enough data."""
        return _mtld_bidirectional(self._tokens)


@dataclass
class WordsResult:
    users: dict[str, UserStats]
    emails: list[str]
    phones: list[str]
    chat_top_words: list[tuple[str, int]]
    chat_avg_sentiment: float
    sentiment_available: bool = False
    # (date_iso, score, user_id) for every scored fragment with a date.
    # Used to build sentiment-over-time charts without re-running the model.
    dated_scores: list[tuple[str, float, str]] = field(default_factory=list)
    # Number of fragments where a sarcasm-marker emoji caused score attenuation.
    sarcasm_marked: int = 0


def _score_all(texts: list[str]) -> list[float]:
    """Batch-score texts via rubert-tiny2. Falls back to zeros on failure."""
    if not texts:
        return []
    try:
        return _sentiment_mod.score_batch(texts)
    except Exception as ex:
        # If transformers / model load fails, don't kill analysis.
        print(f"[words] sentiment failed, returning zeros: {ex}")
        return [0.0] * len(texts)


# MTLD — Measure of Textual Lexical Diversity (McCarthy & Jarvis 2010).
# Sweep tokens; whenever running TTR drops to `threshold`, increment a
# "factor count" and reset. Result = total_tokens / factor_count.
# A partial trailing factor is interpolated. Bidirectional = avg(forward,
# reverse) — smooths out start-of-text artifacts. Threshold 0.72 is the
# standard from the literature.

_MTLD_THRESHOLD = 0.72


def _mtld_one_direction(tokens: list[str]) -> float:
    if len(tokens) < 50:
        return 0.0
    factors = 0
    types: set[str] = set()
    n = 0
    for tok in tokens:
        types.add(tok)
        n += 1
        ttr = len(types) / n
        if ttr <= _MTLD_THRESHOLD:
            factors += 1
            types = set()
            n = 0
    # Trailing partial factor — linear interpolation toward the threshold.
    if n > 0:
        ttr = len(types) / n
        partial = (1 - ttr) / (1 - _MTLD_THRESHOLD) if ttr < 1 else 0.0
        factors += partial
    if factors == 0:
        return 0.0
    return len(tokens) / factors


def _mtld_bidirectional(tokens: list[str]) -> float:
    if len(tokens) < 50:
        return 0.0
    fwd = _mtld_one_direction(tokens)
    rev = _mtld_one_direction(list(reversed(tokens)))
    if fwd == 0.0 and rev == 0.0:
        return 0.0
    if fwd == 0.0:
        return rev
    if rev == 0.0:
        return fwd
    return (fwd + rev) / 2


# Log-odds-ratio with Dirichlet prior (Monroe et al. 2008, simplified).
# Quantifies which words are CHARACTERISTIC of one user vs another, rather
# than just frequent. "блять" common in both → filtered out; "ага" only used
# by one → surfaces.


def distinguishing_words(
    tokens_a: list[str],
    tokens_b: list[str],
    top_n: int = 15,
    alpha: float = 0.01,
    min_count: int = 3,
) -> tuple[list[tuple[str, float, int]], list[tuple[str, float, int]]]:
    """Return (a_distinctive, b_distinctive) — each is [(word, log_odds, count), ...].

    Positive log-odds means the word is more characteristic of `a` than `b`.
    `min_count` filters rare hapax noise — word must appear ≥min_count times
    in the user's own tokens to qualify."""
    if not tokens_a or not tokens_b:
        return [], []

    from collections import Counter as _C

    ca = _C(tokens_a)
    cb = _C(tokens_b)
    Na = sum(ca.values())
    Nb = sum(cb.values())
    vocab = set(ca) | set(cb)
    V = len(vocab)
    aV = alpha * V

    rows: list[tuple[str, float, int]] = []  # (word, log_odds, max_count)
    for w in vocab:
        a_c = ca.get(w, 0)
        b_c = cb.get(w, 0)
        if a_c < min_count and b_c < min_count:
            continue
        # smoothed proportions
        pa = (a_c + alpha) / (Na + aV)
        pb = (b_c + alpha) / (Nb + aV)
        if pa <= 0 or pb <= 0:
            continue
        lo = _math.log(pa / pb)
        rows.append((w, lo, max(a_c, b_c)))

    a_dist = sorted([r for r in rows if r[1] > 0], key=lambda r: -r[1])[:top_n]
    b_dist = sorted([r for r in rows if r[1] < 0], key=lambda r: r[1])[:top_n]
    # Flip sign on b side so callers see positive numbers in both columns.
    b_dist = [(w, -lo, c) for (w, lo, c) in b_dist]
    return a_dist, b_dist


def _extract_contacts(text: str) -> tuple[list[str], list[str]]:
    emails: list[str] = []
    for e in re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text):
        if validate_email(e, verify=False):
            emails.append(e)
    phones: list[str] = []
    for p in re.findall(r"\+?[0-9]{1,3}?[-. (]?[0-9]{1,4}[-. )]?[0-9]{1,4}[-. ]?[0-9]{1,9}", text):
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
    # Use mutable lists internally so we can fill in sentiment scores after
    # batched inference. Convert to tuples at the end.
    user_msgs: dict[str, list[list]] = defaultdict(list)
    user_names: dict[str, str] = {}
    seen_long: dict[str, set[str]] = defaultdict(set)
    emails: list[str] = []
    phones: list[str] = []

    # Pass 1: walk messages, accumulate placeholder records, track which need scoring.
    to_score: list[tuple[str, int]] = []  # (uid, slot_index)
    score_inputs: list[str] = []
    score_dates: list[str | None] = []  # message date for each entry in score_inputs

    for m in messages:
        if not isinstance(m, dict):
            continue
        uid = m.get("from_id")
        if not uid:
            uid = m.get("actor_id")
            if uid is None:
                continue
            uid = str(uid).replace(" ", "")
            if uid not in user_names:
                user_names[uid] = display_name(m.get("actor"), uid)
            action = m.get("action")
            if action:
                tex = m.get("text") or ""
                action_text = _action_map.get(action, action)
                if action in ("invite_members", "remove_members"):
                    members = m.get("members") or []
                    members_str = ",".join(str(x) for x in members if x)
                    user_msgs[uid].append([f"{action_text} - {members_str}", 0.0])
                else:
                    user_msgs[uid].append([f"{action_text} {tex}", 0.0])
                continue

        uid = str(uid).replace(" ", "")
        if is_bot_name(m.get("from")):
            continue  # keep bot reposts (welcome/rules) out of vocabulary stats
        if uid not in user_names:
            user_names[uid] = display_name(m.get("from"), uid)

        frags = _extract_text(m)
        joined = " ".join(sorted(f for f in frags if f))
        if len(joined) >= DEDUP_MIN_CHARS:
            if joined in seen_long[uid]:
                continue  # same long block already counted (rules/spam repost)
            seen_long[uid].add(joined)

        m_date = m.get("date") if isinstance(m.get("date"), str) else None
        for fragment in frags:
            if not fragment:
                continue
            slot = len(user_msgs[uid])
            user_msgs[uid].append([fragment, 0.0])  # placeholder score
            to_score.append((uid, slot))
            score_inputs.append(fragment)
            score_dates.append(m_date)
            ex_emails, ex_phones = _extract_contacts(fragment)
            emails.extend(ex_emails)
            phones.extend(ex_phones)

    # Pass 2: batch-score all fragments at once (much faster than per-call).
    sentiment_available = _sentiment_mod.is_available()
    dated_scores: list[tuple[str, float, str]] = []
    sarcasm_marked = 0
    if sentiment_available:
        raw_scores = _score_all(score_inputs)
        adjusted: list[float] = []
        for (uid, slot), text, raw, date_str in zip(
            to_score, score_inputs, raw_scores, score_dates
        ):
            s, marked = _sentiment_mod.attenuate_sarcasm(text, float(raw))
            if marked:
                sarcasm_marked += 1
            user_msgs[uid][slot][1] = s
            adjusted.append(s)
            if date_str:
                dated_scores.append((date_str, s, uid))

    # Per-user aggregates. Sentiment is averaged WEIGHTED by token count so
    # one-word "ага" doesn't equal a paragraph. Falls back to plain mean for
    # very short fragments (avoids div-by-zero).
    users: dict[str, UserStats] = {}
    all_tokens: list[str] = []
    weighted_chat_num = 0.0
    weighted_chat_den = 0.0
    for uid, msgs in user_msgs.items():
        msgs_t = [tuple(r) for r in msgs]
        weighted_num = 0.0
        weighted_den = 0.0
        for txt, s in msgs_t:
            if not isinstance(s, float):
                continue
            w = max(len(txt.split()), 1)
            weighted_num += s * w
            weighted_den += w
        avg = weighted_num / weighted_den if weighted_den else 0.0
        weighted_chat_num += weighted_num
        weighted_chat_den += weighted_den
        try:
            top, tokens = nltk_analyse.analyse(msgs_t, most_com)
        except Exception:
            top, tokens = [], []
        all_tokens.extend(tokens)
        users[uid] = UserStats(
            user_id=uid,
            name=user_names.get(uid) or display_name(None, uid),
            messages=msgs_t,
            avg_sentiment=avg,
            top_words=list(top),
            total_tokens=len(tokens),
            unique_tokens=len(set(tokens)),
            _tokens=list(tokens),
        )

    # Chat-wide aggregates: weighted-average sentiment so long messages
    # carry more weight than one-word reactions.
    try:
        chat_top, _ = nltk_analyse.analyse_all(all_tokens, most_com)
    except Exception:
        chat_top = []
    chat_top_pairs = list(chat_top)
    chat_avg = weighted_chat_num / weighted_chat_den if weighted_chat_den else 0.0

    return WordsResult(
        users=users,
        emails=sorted(set(emails)),
        phones=sorted(set(phones)),
        chat_top_words=chat_top_pairs,
        chat_avg_sentiment=chat_avg,
        sentiment_available=sentiment_available,
        dated_scores=dated_scores,
        sarcasm_marked=sarcasm_marked,
    )


def sentiment_period_series(
    dated_scores: list[tuple[str, float, str]],
    granularity: str = "week",
    per_user: bool = False,
) -> list[dict]:
    """Group scored fragments into time buckets, return [(period, avg, count[, user])].

    `dated_scores`: list of (iso_date, score, user_id) from WordsResult.
    Granularity: 'day' | 'week' | 'month'. Default week.
    Set per_user=True for an extra "user_id" key (caller resolves the name).
    """
    buckets: dict = defaultdict(list)
    for date_iso, score, uid in dated_scores:
        try:
            d = datetime.fromisoformat(date_iso)
        except ValueError:
            continue
        period = _period_key(d, granularity)
        key = (uid, period) if per_user else period
        buckets[key].append(score)

    rows: list[dict] = []
    if per_user:
        for (uid, period), vs in sorted(buckets.items(), key=lambda kv: kv[0][1]):
            rows.append(
                {
                    "user_id": uid,
                    "period": period,
                    "avg": sum(vs) / len(vs),
                    "count": len(vs),
                }
            )
    else:
        for period, vs in sorted(buckets.items()):
            rows.append(
                {
                    "period": period,
                    "avg": sum(vs) / len(vs),
                    "count": len(vs),
                }
            )
    return rows


def sentiment_by_hour(
    dated_scores: list[tuple[str, float, str]],
) -> list[dict]:
    """Average sentiment per hour-of-day (0..23). Surfaces "morning gloomy /
    evening upbeat" patterns the weekly series flattens out.
    """
    buckets: dict[int, list[float]] = defaultdict(list)
    for date_iso, score, _uid in dated_scores:
        try:
            d = datetime.fromisoformat(date_iso)
        except ValueError:
            continue
        buckets[d.hour].append(score)
    return [
        {"hour": h, "avg": sum(buckets[h]) / len(buckets[h]), "count": len(buckets[h])}
        for h in range(24)
        if h in buckets
    ]


def sentiment_by_weekday(
    dated_scores: list[tuple[str, float, str]],
) -> list[dict]:
    """Average sentiment per day-of-week (0=Mon ... 6=Sun). Captures
    Monday-vs-Friday energy patterns hidden in the weekly average."""
    buckets: dict[int, list[float]] = defaultdict(list)
    for date_iso, score, _uid in dated_scores:
        try:
            d = datetime.fromisoformat(date_iso)
        except ValueError:
            continue
        buckets[d.weekday()].append(score)
    return [
        {"weekday": w, "avg": sum(buckets[w]) / len(buckets[w]), "count": len(buckets[w])}
        for w in range(7)
        if w in buckets
    ]


def _period_key(d: datetime, granularity: str) -> str:
    if granularity == "day":
        return d.strftime("%Y-%m-%d")
    if granularity == "month":
        return d.strftime("%Y-%m-01")
    # default: ISO week, Monday-anchored
    start = d - timedelta(days=d.weekday())
    return start.strftime("%Y-%m-%d")
