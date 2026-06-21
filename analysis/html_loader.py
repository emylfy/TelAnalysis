"""Telegram Desktop HTML-export loader.

Parses `messages*.html` from a Telegram Desktop *HTML* export into the same
normalised dict shape that `loader.load_json` produces for JSON exports, so the
rest of the pipeline consumes it unchanged. JSON remains the recommended source;
HTML is lossier and the gaps below are why:

  * `from_id` does not exist in HTML — synthesised as `html:<name>`, so identity
    is only as stable as the display name (breaks on renames / namesakes). This
    degrades the Network and Per-User tabs for groups; the UI warns on load.
  * chat `type` is not encoded in HTML — left as "?" (pipeline shows all tabs).
  * `text_entities` formatting is flattened to plain text.
  * media is detected coarsely from CSS classes; only voice duration is recovered,
    and link-preview thumbnails inflate the photo count slightly.

Uses only the stdlib (re / html.unescape) — no bs4/lxml dependency. Tested for
parity against the matching JSON export (text + timestamps match exactly).
"""

from __future__ import annotations

import glob
import html as _html
import os
import re
from datetime import datetime

# Marker placed on the returned dict so callers (UI) can warn about HTML's
# reduced fidelity. JSON exports never carry it.
SOURCE_HTML = "html"

# block splitting

# Each message is a `<div class="message ..." id="messageN">`. The head regex
# both locates block starts and pulls out the class + id.
_MSG_HEAD_RE = re.compile(r'<div class="message ([^"]*)"\s+id="message(-?\d+)"')

# date lives in title="DD.MM.YYYY HH:MM:SS UTC+HH:MM"
_DATE_RE = re.compile(
    r'<div class="pull_right date details" title="'
    r'(\d{2})\.(\d{2})\.(\d{4}) (\d{2}):(\d{2}):(\d{2}) UTC([+-]\d{2}):(\d{2})"'
)
_FROM_RE = re.compile(r'<div class="from_name">\s*(.*?)\s*</div>', re.S)
_TEXT_RE = re.compile(r'<div class="text">(.*?)</div>', re.S)
# service messages ("X created", "pinned this message") and day dividers both
# live in `body details`; the divider filter below separates them.
_BODY_DETAILS_RE = re.compile(r'<div class="body details">\s*(.*?)\s*</div>', re.S)
_REPLY_RE = re.compile(r'go_to_message(-?\d+)')
_FWD_FROM_RE = re.compile(
    r'<div class="forwarded body">\s*<div class="from_name">\s*(.*?)(?:<span|</div>)',
    re.S,
)
_VOICE_DUR_RE = re.compile(r'media_voice_message.*?status details">\s*(\d{2}):(\d{2})', re.S)

# A `message service` block is a real service message *or* a day divider
# ("14 December 2021"). Day dividers parse as a bare date → we drop those.
_DATE_DIVIDER_RE = re.compile(r"^\d{1,2}\s+\w+\s+\d{4}$")


def _flatten_html(fragment: str) -> str:
    """Turn an inline-HTML text fragment into plain text."""
    fragment = re.sub(r"<br\s*/?>", "\n", fragment)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    return _html.unescape(fragment).strip()


def _media_type(block: str) -> str | None:
    if "media_voice_message" in block:
        return "voice_message"
    if "photo_wrap" in block or "media_photo" in block:
        return "photo"
    if "video_file" in block or "media_video" in block:
        return "video_file"
    if "sticker" in block:
        return "sticker"
    if "media_file" in block or "media_document" in block:
        return "file"
    return None


def _msg_file_order(p: str) -> int:
    """Sort key for messages.html, messages2.html, …, messages10.html.

    Plain alphabetical sort would put messages10 before messages2; Telegram
    numbers continuation files, so sort by that number (no number == 0).
    """
    m = re.search(r"messages(\d*)\.html$", os.path.basename(p))
    return int(m.group(1)) if m and m.group(1) else 0


def parse_html_export(path: str) -> dict:
    """Parse a Telegram Desktop HTML export dir (or a messages.html file).

    Returns a dict shaped like a single-chat JSON export: name/type/id/messages,
    plus a `_source` marker so the UI can flag HTML's reduced fidelity.
    """
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "messages*.html")), key=_msg_file_order)
    else:
        files = [path]
    if not files:
        raise FileNotFoundError(f"no messages*.html found at {path}")

    name = "Chat"
    messages: list[dict] = []
    last_sender = None  # carry-forward for "joined" continuation blocks

    for fp in files:
        with open(fp, encoding="utf-8", errors="replace") as f:
            raw = f.read()

        # chat name from the page header (first file only carries it reliably)
        if name == "Chat":
            hm = re.search(r'<div class="text bold">\s*(.*?)\s*</div>', raw, re.S)
            if hm:
                name = _flatten_html(hm.group(1)) or "Chat"

        # split into per-message blocks at each message head
        heads = list(_MSG_HEAD_RE.finditer(raw))
        bounds = [m.start() for m in heads] + [len(raw)]
        for i, head in enumerate(heads):
            block = raw[bounds[i] : bounds[i + 1]]
            classes, mid = head.group(1), int(head.group(2))
            is_service = "service" in classes

            # text divs (covers normal + forwarded body text)
            texts = [_flatten_html(t) for t in _TEXT_RE.findall(block)]
            texts = [t for t in texts if t]
            text = "\n".join(texts)

            if is_service:
                bd = _BODY_DETAILS_RE.search(block)
                stext = _flatten_html(bd.group(1)) if bd else text
                if not stext or _DATE_DIVIDER_RE.match(stext):
                    continue  # day divider, not a real message
                messages.append({"id": mid, "type": "service", "text": stext, "action": ""})
                continue

            # sender: present unless this is a joined continuation block
            fm = _FROM_RE.search(block)
            sender = _flatten_html(fm.group(1)) if fm else last_sender
            if sender:
                last_sender = sender

            # date → ISO + unixtime (offset-aware)
            date_iso = None
            date_unix = None
            dm = _DATE_RE.search(block)
            if dm:
                dd, mm, yyyy, hh, mi, ss, oh, om = dm.groups()
                tz = f"{oh}:{om}"
                dt = datetime.fromisoformat(f"{yyyy}-{mm}-{dd}T{hh}:{mi}:{ss}{tz}")
                date_iso = dt.strftime("%Y-%m-%dT%H:%M:%S")
                date_unix = str(int(dt.timestamp()))

            msg: dict = {
                "id": mid,
                "type": "message",
                "from": sender,
                # synthetic, name-derived identity — the big JSON→HTML compromise
                "from_id": f"html:{sender}" if sender else None,
                "text": text,
            }
            if date_iso:
                msg["date"] = date_iso
                msg["date_unixtime"] = date_unix
            rm = _REPLY_RE.search(block)
            if rm:
                msg["reply_to_message_id"] = int(rm.group(1))
            if "forwarded body" in block:
                fw = _FWD_FROM_RE.search(block)
                msg["forwarded_from"] = _flatten_html(fw.group(1)) if fw else "unknown"
            mt = _media_type(block)
            if mt:
                msg["media_type"] = mt
                if mt == "voice_message":
                    vm = _VOICE_DUR_RE.search(block)
                    if vm:
                        msg["duration_seconds"] = int(vm.group(1)) * 60 + int(vm.group(2))
            messages.append(msg)

    return {"name": name, "type": "?", "id": None, "messages": messages, "_source": SOURCE_HTML}
