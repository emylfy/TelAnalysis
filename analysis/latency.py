"""Reply-latency stats. For every reply, computes seconds between original and reply."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ui import i18n


@dataclass
class LatencyStats:
    overall_seconds: list[int]  # all reply latencies, in seconds
    per_user_seconds: dict[str, list[int]]  # responder user_id -> list
    user_names: dict[str, str]
    median_seconds: float
    p90_seconds: float
    # Replies whose delay exceeded `cap_hours` (and were therefore excluded
    # from the histograms / median / p90). Surfaced in UI so users know the
    # numbers above don't include slow replies.
    dropped_over_cap: int = 0
    cap_hours: int = 24
    # Q&A subset — pairs where the original message contains '?'. Replies to
    # questions tend to come faster than generic acknowledgements, so this is
    # a much sharper "responsiveness" metric than the chat-wide median.
    qa_seconds: list[int] = None  # type: ignore[assignment]
    qa_median_seconds: float = 0.0
    qa_p90_seconds: float = 0.0


def _ts(m: dict) -> int | None:
    """Return integer unix timestamp from a Telegram message, or None."""
    if not isinstance(m, dict):
        return None
    raw = m.get("date_unixtime")
    if raw is None:
        return None
    try:
        return int(raw)
    except (ValueError, TypeError):
        return None


def compute(messages: list[dict], cap_hours: int = 24) -> LatencyStats:
    """Build reply-latency stats.

    `cap_hours` clips outliers (e.g. someone replying days later) so the
    distribution stays informative. Set to 24 by default.
    """
    if not messages:
        return LatencyStats(
            overall_seconds=[],
            per_user_seconds={},
            user_names={},
            median_seconds=0.0,
            p90_seconds=0.0,
            dropped_over_cap=0,
            cap_hours=cap_hours,
            qa_seconds=[],
        )

    # id -> (timestamp, has_question, responder_id) — has_question is True
    # if the original message text contains '?'. Used to split Q&A pairs out
    # of the general latency distribution.
    ts_index: dict = {}
    has_q_index: dict = {}
    for m in messages:
        if not isinstance(m, dict):
            continue
        mid = m.get("id")
        if mid is not None:
            ts = _ts(m)
            if ts is not None:
                ts_index[mid] = ts
                # Question detection: cheap check on text/caption.
                txt = m.get("text")
                if isinstance(txt, list):
                    txt = "".join(
                        x
                        if isinstance(x, str)
                        else (x.get("text", "") if isinstance(x, dict) else "")
                        for x in txt
                    )
                if not isinstance(txt, str):
                    txt = ""
                cap = m.get("caption") if isinstance(m.get("caption"), str) else ""
                has_q_index[mid] = "?" in (txt + cap)

    user_names: dict[str, str] = {}
    overall: list[int] = []
    per_user: dict[str, list[int]] = defaultdict(list)
    qa: list[int] = []
    cap_seconds = cap_hours * 3600
    dropped = 0

    for m in messages:
        if not isinstance(m, dict):
            continue
        rid = m.get("reply_to_message_id")
        if rid is None:
            continue
        original_ts = ts_index.get(rid)
        reply_ts = _ts(m)
        if original_ts is None or reply_ts is None:
            continue
        delta = reply_ts - original_ts
        if delta < 0:
            continue
        if delta > cap_seconds:
            dropped += 1
            continue
        responder = str(m.get("from_id") or "")
        if not responder:
            continue
        if responder not in user_names:
            user_names[responder] = m.get("from") or responder
        overall.append(delta)
        per_user[responder].append(delta)
        if has_q_index.get(rid):
            qa.append(delta)

    overall_sorted = sorted(overall)
    median = overall_sorted[len(overall_sorted) // 2] if overall_sorted else 0.0
    p90_idx = int(len(overall_sorted) * 0.9)
    p90 = overall_sorted[p90_idx] if overall_sorted else 0.0

    qa_sorted = sorted(qa)
    qa_median = qa_sorted[len(qa_sorted) // 2] if qa_sorted else 0.0
    qa_p90 = qa_sorted[int(len(qa_sorted) * 0.9)] if qa_sorted else 0.0

    return LatencyStats(
        overall_seconds=overall,
        per_user_seconds=dict(per_user),
        user_names=user_names,
        median_seconds=float(median),
        p90_seconds=float(p90),
        dropped_over_cap=dropped,
        cap_hours=cap_hours,
        qa_seconds=qa,
        qa_median_seconds=float(qa_median),
        qa_p90_seconds=float(qa_p90),
    )


def humanize_seconds(s: float) -> str:
    s = int(s)
    if s < 60:
        return f"{s}{i18n.dur_unit('s')}"
    if s < 3600:
        return f"{s // 60}{i18n.dur_unit('m')} {s % 60}{i18n.dur_unit('s')}"
    return f"{s // 3600}{i18n.dur_unit('h')} {(s % 3600) // 60}{i18n.dur_unit('m')}"
