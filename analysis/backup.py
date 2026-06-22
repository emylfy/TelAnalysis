"""Backup management: browse a full Telegram export and prune chats / heavy media.

ISOLATION BOUNDARY. This is the ONLY module under `analysis/` that writes to or
deletes from the user's export — every other analysis module is strictly
read-only. All mutation here is:

- gated behind `can_manage()` (a real on-disk export folder with `chats/`, not an
  uploaded copy of result.json and not an HTML export);
- reversible: delete/slim MOVE data into `<root>/.telanalysis_trash/` rather than
  removing it, recording a manifest so it can be restored. Disk is only actually
  reclaimed by `empty_trash()` — the single hard delete in the whole app;
- path-guarded: every filesystem target goes through `safe_under_root()`, which
  rejects `..` and anything resolving outside the export root (mirrors the guard
  in `api.main.sticker_file`).

A full Telegram export stores media under `chats/chat_XXX/<subdir>/…` but the
result.json chat objects do NOT name their folder — we derive it from the media
paths inside each chat's messages (`chat_folder`). Chats with no media (notably
`left_chats`) have no folder; deleting them only edits result.json.
"""

from __future__ import annotations

import html as htmllib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from analysis import loader

TRASH_DIR = ".telanalysis_trash"

# `chats/chat_009/...` → folder name. Matches the media-path prefix Telegram
# writes into `photo` / `file` / `thumbnail` fields.
_FOLDER_RE = re.compile(r"^chats/(chat_\d+)/")
_MEDIA_KEYS = ("photo", "file", "thumbnail")

# Authoritative chat→folder rows in the HTML export's lists/chats.html:
# <a href="../chats/chat_NNN/messages.html#allow_back"> … <div class="name bold">NAME</div>
_CHATS_HTML_RE = re.compile(
    r'href="\.\./chats/(chat_\d+)/messages\.html[^"]*".*?<div class="name bold">(.*?)</div>',
    re.S,
)


# paths + capability


def export_root(path: str) -> Path:
    """The export folder: parent of result.json, or the folder itself."""
    p = Path(path).resolve()
    return p if p.is_dir() else p.parent


def result_json_path(path: str) -> Path | None:
    """Locate the writable result.json for this export, or None (e.g. an HTML
    export, or a lone uploaded result.json placed elsewhere)."""
    p = Path(path).resolve()
    if p.is_file() and p.suffix.lower() == ".json":
        return p
    if p.is_dir():
        cand = p / "result.json"
        if cand.exists():
            return cand
    return None


def can_manage(path: str) -> bool:
    """Whether destructive management is allowed for this export.

    Requires a real result.json sitting next to a `chats/` folder in a writable
    directory. This excludes HTML exports (no result.json) and browser-uploaded
    copies of result.json (saved alone in the OS temp dir, no `chats/`).
    """
    rj = result_json_path(path)
    if rj is None:
        return False
    root = rj.parent
    return (root / "chats").is_dir() and os.access(root, os.W_OK)


def safe_under_root(root: Path, rel: str) -> Path:
    """Resolve `rel` under `root`, refusing path-escape. Mirrors the guard in
    `api.main.sticker_file`. Raises ValueError on anything unsafe."""
    rel_norm = rel.replace("\\", "/")
    if rel_norm.startswith("/") or ".." in rel_norm.split("/"):
        raise ValueError(f"unsafe path: {rel!r}")
    target = (root / rel_norm).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f"path escapes root: {rel!r}")
    return target


def reveal_folder(path: str, rel: str) -> dict[str, Any]:
    """Open a chat's on-disk folder in the OS file manager (Finder / Explorer /
    file browser). Read-only: it just launches the system browser on a folder
    that already exists inside this export. `rel` is the chat's `folder` field
    (e.g. "chats/chat_009"), validated to stay under the export root."""
    root = export_root(path)
    target = safe_under_root(root, rel)  # raises ValueError on path-escape
    if not target.is_dir():
        raise FileNotFoundError(str(target))
    if sys.platform == "darwin":
        cmd = ["open", str(target)]
    elif os.name == "nt":
        cmd = ["explorer", str(target)]
    else:
        cmd = ["xdg-open", str(target)]
    # fire-and-forget: explorer.exe exits non-zero even on success, and we don't
    # want to block the request on the file manager's lifetime.
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"ok": True, "path": str(target)}


# inspection (read-only)


def chat_folder(messages: list) -> str | None:
    """First `chat_XXX` referenced by a chat's media. NOTE: unreliable on its own
    — forwarded messages reference the *source* chat's folder, so a chat that
    forwards heavily can resolve to someone else's folder. Used only as the
    raw signal for `_media_owner_map`; prefer `folder_map`."""
    for m in messages:
        if not isinstance(m, dict):
            continue
        for key in _MEDIA_KEYS:
            v = m.get(key)
            if isinstance(v, str):
                mm = _FOLDER_RE.match(v.replace("\\", "/"))
                if mm:
                    return mm.group(1)
    return None


def _folder_ref_counts(messages: list) -> Counter:
    """How many media paths in a chat point at each `chat_XXX` folder."""
    c: Counter = Counter()
    for m in messages:
        if not isinstance(m, dict):
            continue
        for key in _MEDIA_KEYS:
            v = m.get(key)
            if isinstance(v, str):
                mm = _FOLDER_RE.match(v.replace("\\", "/"))
                if mm:
                    c[mm.group(1)] += 1
    return c


def _iter_chats(data: dict):
    """Yield (chat_dict, is_left) for every chat in a full export, active first."""
    for key, is_left in (("chats", False), ("left_chats", True)):
        section = data.get(key)
        if isinstance(section, dict):
            for ch in section.get("list", []) or []:
                if isinstance(ch, dict):
                    yield ch, is_left


def _parse_chats_html(root: Path) -> dict[str, list[str]]:
    """Authoritative name → [folders] map from the HTML export's
    lists/chats.html (Telegram writes the real chat↔folder pairing there).
    Returns {} when the file is absent (a JSON-only export)."""
    f = root / "lists" / "chats.html"
    if not f.is_file():
        return {}
    try:
        html = f.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    out: dict[str, list[str]] = {}
    for folder, raw_name in _CHATS_HTML_RE.findall(html):
        name = htmllib.unescape(re.sub(r"\s+", " ", raw_name).strip())
        out.setdefault(name, []).append(folder)
    return out


def _media_owner_map(data: dict) -> dict[str, str]:
    """Fallback chat-id → folder when there's no chats.html. Each folder is
    awarded to the single chat that references it MOST (its real owner), so a
    chat that merely forwards from another never claims that other's folder.
    Chats left without a uniquely-owned folder map to nothing (safe: shown as
    0 B, never deleted)."""
    # (chat_id, folder) → count, then pick the top chat per folder.
    best: dict[str, tuple[int, str]] = {}  # folder → (count, chat_id)
    for ch, _is_left in _iter_chats(data):
        cid = str(ch.get("id"))
        for folder, n in _folder_ref_counts(ch.get("messages") or []).items():
            if folder not in best or n > best[folder][0]:
                best[folder] = (n, cid)
    out: dict[str, str] = {}
    for folder, (_n, cid) in best.items():
        out[cid] = folder  # one folder per owner chat
    return out


def folder_map(root: Path, data: dict) -> dict[str, str]:
    """chat-id → `chat_XXX` folder. Prefers the authoritative lists/chats.html
    pairing (matched by name, positionally disambiguating duplicate names);
    falls back to the media-ownership heuristic for JSON-only exports."""
    html_map = _parse_chats_html(root)
    if html_map:
        # consume folders per name in export order so duplicate names line up
        pools = {name: list(folders) for name, folders in html_map.items()}
        out: dict[str, str] = {}
        for ch, _is_left in _iter_chats(data):
            name = htmllib.unescape((ch.get("name") or "").strip()) or (ch.get("name") or "")
            pool = pools.get(ch.get("name") or "") or pools.get(name)
            if pool:
                out[str(ch.get("id"))] = pool.pop(0)
        if out:
            return out
    return _media_owner_map(data)


def folder_stats(folder: Path) -> dict[str, Any]:
    """Single-pass walk of a chat folder → total bytes, file count, and bytes
    bucketed by top-level subdir (`photos`, `video_files`, …) — the units the
    'slim' action operates on."""
    total = 0
    files = 0
    per: dict[str, int] = {}
    for dirpath, _dirs, filenames in os.walk(folder):
        rel = os.path.relpath(dirpath, folder)
        top = "_root" if rel == "." else rel.split(os.sep)[0]
        for name in filenames:
            try:
                size = os.path.getsize(os.path.join(dirpath, name))
            except OSError:
                continue
            total += size
            files += 1
            per[top] = per.get(top, 0) + size
    return {"bytes": total, "files": files, "media": per}


def dir_size(folder: Path) -> int:
    total = 0
    for dirpath, _dirs, filenames in os.walk(folder):
        for name in filenames:
            try:
                total += os.path.getsize(os.path.join(dirpath, name))
            except OSError:
                continue
    return total


def _date_bounds(messages: list) -> tuple[str | None, str | None]:
    """First/last message date. ISO-8601 strings sort lexicographically, so
    min/max need no datetime parsing."""
    first = last = None
    for m in messages:
        if not isinstance(m, dict):
            continue
        d = m.get("date")
        if not isinstance(d, str) or not d:
            continue
        if first is None or d < first:
            first = d
        if last is None or d > last:
            last = d
    return first, last


def _row(ch: dict, root: Path, is_left: bool, folder_name: str | None) -> dict[str, Any]:
    messages = ch.get("messages") or []
    folder = None
    disk = 0
    files = 0
    media: dict[str, int] = {}
    if folder_name:
        fp = root / "chats" / folder_name
        if fp.is_dir():
            folder = f"chats/{folder_name}"
            stats = folder_stats(fp)
            disk, files, media = stats["bytes"], stats["files"], stats["media"]
    first, last = _date_bounds(messages)
    return {
        "id": str(ch.get("id")),
        "name": ch.get("name") or ("Saved Messages" if not is_left else "?"),
        "type": ch.get("type") or "?",
        "msg_count": len(messages),
        "first_date": first,
        "last_date": last,
        "folder": folder,
        "disk_bytes": disk,
        "file_count": files,
        "media": media,
        "is_left": is_left,
    }


def chat_rows(data: dict, root: Path) -> list[dict[str, Any]]:
    """Per-chat metadata for the manager table: active chats first, then
    `left_chats` (text-only, no folders). Folder attribution is authoritative
    (lists/chats.html) when present, so sizes aren't double-counted."""
    fmap = folder_map(root, data)
    return [
        _row(ch, root, is_left, fmap.get(str(ch.get("id"))))
        for ch, is_left in _iter_chats(data)
    ]


# HTML tails (lists/chats.html + export_results.html)
#
# A full export keeps two HTML artifacts that still name a deleted chat after
# result.json is rewritten: lists/chats.html (one row per chat) and the
# "N Chats" counter on export_results.html. We strip those too so a removed
# chat leaves no trace. All edits are reversible (blocks + counter delta are
# stored in the trash manifest and re-applied by `restore`).

_ENTRY_LIST_OPEN = '<div class="entry_list">'
# A chat row opens with <div class="entry clearfix"> (left/empty, no link) or
# <a class="entry block_link clearfix" href="../chats/chat_NNN/..."> (active).
_ENTRY_OPEN_RE = re.compile(r'<(?:div|a)\b[^>]*class="entry[^"]*clearfix"[^>]*>')
_DIVA_TAG_RE = re.compile(r"</?(?:div|a)\b[^>]*>")
_HREF_FOLDER_RE = re.compile(r'href="\.\./chats/(chat_\d+)/')
_NAME_BOLD_RE = re.compile(r'<div class="name bold">\s*(.*?)\s*</div>', re.S)
# The "Chats" tile counter on export_results.html.
_RESULTS_COUNT_RE = re.compile(
    r'(class="section block_link chats"[^>]*>.*?<div class="counter details">\s*)(\d+)(\s*</div>)',
    re.S,
)


def _entry_blocks(html: str):
    """Yield (start, end, kind, folder, name) for every chat row in chats.html.
    `kind` is 'link' (active, folder from its href) or 'bare' (left/empty). The
    row span is found by balancing <div>/<a> tags from the opener, so nested
    markup (userpic, body) is included and never mis-split."""
    for om in _ENTRY_OPEN_RE.finditer(html):
        start = om.start()
        depth = 0
        end = None
        for tm in _DIVA_TAG_RE.finditer(html, start):
            depth += -1 if tm.group(0).startswith("</") else 1
            if depth == 0:
                end = tm.end()
                break
        if end is None:
            continue
        block = html[start:end]
        fm = _HREF_FOLDER_RE.search(om.group(0))
        folder = fm.group(1) if fm else None
        nm = _NAME_BOLD_RE.search(block)
        name = htmllib.unescape(re.sub(r"\s+", " ", nm.group(1)).strip()) if nm else None
        yield start, end, ("link" if folder else "bare"), folder, name


def _ws_start(html: str, start: int) -> int:
    """Index where the whitespace run preceding `start` begins — removed with the
    block so deletions don't leave blank gaps."""
    i = start
    while i > 0 and html[i - 1] in " \t\r\n":
        i -= 1
    return i


def _container_opens(html: str) -> list[int]:
    """Offsets of each entry_list container opener. A full export emits two — the
    active chats, then the left chats — matching result.json's two sections."""
    return [m.start() for m in re.finditer(re.escape(_ENTRY_LIST_OPEN), html)]


def _remove_entry_blocks(seg: str, folders: set[str], names: Counter) -> tuple[str, list[str]]:
    """Drop matching rows from one container segment. Active rows match by folder
    (exact); left/empty rows match by name via the `names` multiset (so N
    same-named tombstones remove N rows). CONSUMES `names` in place so the same
    multiset can be threaded across containers without double-removing. Returns
    (new_segment, removed_blocks)."""
    cuts: list[tuple[int, int, str]] = []
    for start, end, kind, folder, name in _entry_blocks(seg):
        if kind == "link" and folder in folders:
            cuts.append((_ws_start(seg, start), end, seg[start:end]))
        elif kind == "bare" and name is not None and names.get(name, 0) > 0:
            names[name] -= 1
            cuts.append((_ws_start(seg, start), end, seg[start:end]))
    if not cuts:
        return seg, []
    out: list[str] = []
    removed: list[str] = []
    prev = 0
    for cut, end, raw in cuts:
        out.append(seg[prev:cut])
        removed.append(raw)
        prev = end
    out.append(seg[prev:])
    return "".join(out), removed


def _reinsert_entry_blocks(html: str, records: list[dict]) -> str:
    """Put removed rows back into their origin container (by stored index), just
    after that entry_list opener. Position within a container is cosmetic (rows
    render in document order), so this is robust across delete/restore batches."""
    opens = _container_opens(html)
    if not opens or not records:
        return html
    by_c: dict[int, list[str]] = {}
    for r in records:
        idx = min(int(r.get("c", 0)), len(opens) - 1)
        by_c.setdefault(idx, []).append(r["b"])
    # insert back-to-front so earlier opener offsets stay valid
    for idx in sorted(by_c, reverse=True):
        at = opens[idx] + len(_ENTRY_LIST_OPEN)
        insert = "".join("\n\n     " + b for b in by_c[idx])
        html = html[:at] + insert + html[at:]
    return html


def _adjust_results_count(html: str, delta: int) -> str:
    """Shift the 'Chats' tile counter on export_results.html by `delta`
    (clamped at 0)."""
    def repl(m: re.Match) -> str:
        return f"{m.group(1)}{max(0, int(m.group(2)) + delta)}{m.group(3)}"
    return _RESULTS_COUNT_RE.sub(repl, html, count=1)


def _split_specs(removed: list[dict]) -> tuple[tuple[set, Counter], tuple[set, Counter]]:
    """Partition removal targets into (active, left) → ((folders, names), …),
    keyed off each chat's `is_left`, so each is matched only within its own
    container."""
    af: set[str] = set()
    an: Counter = Counter()
    lf: set[str] = set()
    ln: Counter = Counter()
    for r in removed:
        folder, name, left = r.get("folder"), r.get("name"), r.get("is_left")
        fset, nctr = (lf, ln) if left else (af, an)
        if folder:
            fset.add(folder)
        elif name:
            nctr[name] += 1
    return (af, an), (lf, ln)


def _clean_html_tails(root: Path, removed: list[dict]) -> dict:
    """Strip deleted chats from the HTML tails. `removed` is
    [{name, folder|None, is_left}] per chat. Edits are container-aware: active
    chats match only in the first entry_list, left chats only in the rest. Falls
    back to whole-file matching if the export isn't split as expected. Returns
    manifest data for `restore`; a no-op returning {} on a JSON-only export."""
    info: dict[str, Any] = {}
    (af, an), (lf, ln) = _split_specs(removed)

    chats_html = root / "lists" / "chats.html"
    html = _read_text(chats_html)
    if html is not None:
        opens = _container_opens(html)
        records: list[dict] = []
        if len(opens) >= 2:
            bounds = opens + [len(html)]
            pieces = [html[: opens[0]]]
            for i in range(len(opens)):
                seg = html[bounds[i] : bounds[i + 1]]
                folders, names = (af, an) if i == 0 else (lf, ln)
                new_seg, blocks = _remove_entry_blocks(seg, folders, names)
                pieces.append(new_seg)
                records += [{"c": i, "b": b} for b in blocks]
            new_html = "".join(pieces)
        else:  # unsplit export: one pool, one container
            new_html, blocks = _remove_entry_blocks(html, af | lf, an + ln)
            records = [{"c": 0, "b": b} for b in blocks]
        if records:
            _atomic_write_text(chats_html, new_html)
            info["chats_html_blocks"] = records

    results_html = root / "export_results.html"
    rhtml = _read_text(results_html)
    if rhtml is not None and removed:
        new_rhtml = _adjust_results_count(rhtml, -len(removed))
        if new_rhtml != rhtml:
            _atomic_write_text(results_html, new_rhtml)
            info["results_count_delta"] = len(removed)
    return info


def _restore_html_tails(root: Path, info: dict) -> None:
    """Re-apply the inverse of `_clean_html_tails` from stored manifest data."""
    blocks = info.get("chats_html_blocks")
    if blocks:
        chats_html = root / "lists" / "chats.html"
        html = _read_text(chats_html)
        if html is not None:
            _atomic_write_text(chats_html, _reinsert_entry_blocks(html, blocks))
    delta = info.get("results_count_delta")
    if delta:
        results_html = root / "export_results.html"
        rhtml = _read_text(results_html)
        if rhtml is not None:
            _atomic_write_text(results_html, _adjust_results_count(rhtml, delta))


# trash + manifest


def _trash(root: Path) -> Path:
    return root / TRASH_DIR


def _manifest_path(root: Path) -> Path:
    return _trash(root) / "manifest.json"


def _load_manifest(root: Path) -> dict:
    f = _manifest_path(root)
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {"entries": []}


def _save_manifest(root: Path, man: dict) -> None:
    _trash(root).mkdir(exist_ok=True)
    _atomic_write(_manifest_path(root), man)


def _atomic_write(target: Path, data: Any) -> None:
    """Write JSON via temp + os.replace so a crash can't truncate the file
    (matters for the 40-MB result.json)."""
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, target)


def _atomic_write_text(target: Path, text: str) -> None:
    """Atomic text write (for the HTML tails), same crash-safety as above."""
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, target)


def _read_text(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _new_entry_id() -> str:
    return str(int(time.time() * 1000))


def _move_into_trash(root: Path, entry_id: str, rel: str) -> dict | None:
    """Move `<root>/<rel>` into the trash entry. Returns a {rel, stored} record
    for the manifest, or None if the source is missing."""
    src = safe_under_root(root, rel)
    if not src.exists():
        return None
    bytes_moved = dir_size(src) if src.is_dir() else src.stat().st_size
    dest_dir = _trash(root) / entry_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / Path(rel).name
    shutil.move(str(src), str(dest))
    return {"rel": rel, "stored": f"{TRASH_DIR}/{entry_id}/{dest.name}", "bytes": bytes_moved}


# mutations


def _read_result(root: Path) -> dict:
    rj = root / "result.json"
    return loader.load_json(str(rj))


def delete_chats(path: str, chat_ids: list[str]) -> dict:
    """Move each chat's media folder into the trash and drop its entry from
    result.json. Reversible via `restore`. Returns counts + bytes that will be
    reclaimed when the trash is emptied."""
    root = export_root(path)
    data = _read_result(root)
    fmap = folder_map(root, data)
    wanted = {str(i) for i in chat_ids}
    entry_id = _new_entry_id()

    moved: list[dict] = []
    snapshots: list[dict] = []
    removed_messages = 0
    pending_bytes = 0

    for list_key, is_left in (("chats", False), ("left_chats", True)):
        section = data.get(list_key)
        if not isinstance(section, dict) or not isinstance(section.get("list"), list):
            continue
        keep = []
        for ch in section["list"]:
            if isinstance(ch, dict) and str(ch.get("id")) in wanted:
                messages = ch.get("messages") or []
                removed_messages += len(messages)
                snapshots.append({"chat": ch, "left": is_left})
                folder_name = fmap.get(str(ch.get("id")))
                if folder_name:
                    rec = _move_into_trash(root, entry_id, f"chats/{folder_name}")
                    if rec:
                        moved.append(rec)
                        pending_bytes += rec["bytes"]
            else:
                keep.append(ch)
        section["list"] = keep

    _atomic_write(root / "result.json", data)

    # Strip the deleted chats from the HTML tails too. A chat with a real on-disk
    # folder matches its chats.html row by folder; a tombstone (no folder) matches
    # by name. Reversible via the stored blocks + counter delta.
    # Take the folder from fmap (authoritative chats.html pairing) — NOT from an
    # on-disk check, since the folder has just been moved into the trash above. A
    # chat with a folder owns a linked chats.html row (matched by folder); a
    # tombstone has none (matched by name).
    removed_specs = [
        {"name": s["chat"].get("name"), "folder": fmap.get(str(s["chat"].get("id"))), "is_left": s.get("left")}
        for s in snapshots
    ]
    html_info = _clean_html_tails(root, removed_specs)

    man = _load_manifest(root)
    man["entries"].append(
        {
            "id": entry_id,
            "ts": time.time(),
            "kind": "delete",
            "label": _entry_label(snapshots),
            "chats": snapshots,
            "chat_names": [s["chat"].get("name") or "?" for s in snapshots],
            "moved": moved,
            "html": html_info,
            "bytes": pending_bytes,
        }
    )
    _save_manifest(root, man)

    return {
        "trash_id": entry_id,
        "removed_chats": len(snapshots),
        "removed_messages": removed_messages,
        "bytes": pending_bytes,
    }


def slim_chat(path: str, chat_id: str, media_types: list[str]) -> dict:
    """Move selected media subdirs of one chat into the trash, keeping the
    chat's text and its result.json entry. The JSON's media references become
    dangling — an accepted trade-off for reclaiming space without losing text."""
    root = export_root(path)
    data = _read_result(root)

    target = None
    for ch, _is_left in _iter_chats(data):
        if str(ch.get("id")) == str(chat_id):
            target = ch
            break
    if target is None:
        raise ValueError("chat not found")

    folder_name = folder_map(root, data).get(str(chat_id))
    if not folder_name:
        return {"trash_id": None, "bytes": 0}

    entry_id = _new_entry_id()
    moved: list[dict] = []
    pending_bytes = 0
    # Only real subdirs; '_root' (loose files) and unknown names are ignored.
    for sub in media_types:
        if sub in ("_root", "") or "/" in sub or sub == "..":
            continue
        rec = _move_into_trash(root, entry_id, f"chats/{folder_name}/{sub}")
        if rec:
            moved.append(rec)
            pending_bytes += rec["bytes"]

    if not moved:
        return {"trash_id": None, "bytes": 0}

    name = target.get("name") or "?"
    man = _load_manifest(root)
    man["entries"].append(
        {
            "id": entry_id,
            "ts": time.time(),
            "kind": "slim",
            "label": name,
            "chats": [],
            "chat_names": [name],
            "moved": moved,
            "bytes": pending_bytes,
        }
    )
    _save_manifest(root, man)
    return {"trash_id": entry_id, "bytes": pending_bytes}


def restore(path: str, trash_id: str) -> dict:
    """Undo a trash entry: move folders/media back and re-insert any removed
    chat objects into result.json."""
    root = export_root(path)
    man = _load_manifest(root)
    entry = next((e for e in man["entries"] if e["id"] == trash_id), None)
    if entry is None:
        raise ValueError("trash entry not found")

    for mv in entry.get("moved", []):
        stored = safe_under_root(root, mv["stored"])
        dest = safe_under_root(root, mv["rel"])
        if stored.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(stored), str(dest))

    snapshots = entry.get("chats", [])
    if snapshots:
        data = _read_result(root)
        for snap in snapshots:
            key = "left_chats" if snap.get("left") else "chats"
            section = data.setdefault(key, {})
            section.setdefault("list", []).append(snap["chat"])
        _atomic_write(root / "result.json", data)

    html_info = entry.get("html")
    if html_info:
        _restore_html_tails(root, html_info)

    entry_dir = _trash(root) / trash_id
    if entry_dir.exists():
        shutil.rmtree(entry_dir, ignore_errors=True)
    man["entries"] = [e for e in man["entries"] if e["id"] != trash_id]
    _save_manifest(root, man)
    return {"restored_chats": len(snapshots)}


def empty_trash(path_or_root: str | Path) -> dict:
    """Permanently delete the trash — the only hard removal. Returns reclaimed
    bytes."""
    root = path_or_root if isinstance(path_or_root, Path) else export_root(str(path_or_root))
    td = _trash(root)
    freed = dir_size(td) if td.exists() else 0
    if td.exists():
        shutil.rmtree(td, ignore_errors=True)
    return {"freed_bytes": freed}


def trash_entries(root: Path) -> list[dict]:
    """Manifest entries for the trash panel (newest first)."""
    man = _load_manifest(root)
    out = []
    for e in man.get("entries", []):
        out.append(
            {
                "id": e["id"],
                "ts": e.get("ts", 0),
                "kind": e.get("kind", "delete"),
                "label": e.get("label", "?"),
                "chat_names": e.get("chat_names", []),
                "chat_count": len(e.get("chat_names", [])),
                "bytes": e.get("bytes", 0),
            }
        )
    out.sort(key=lambda x: x["ts"], reverse=True)
    return out


def trash_bytes(root: Path) -> int:
    td = _trash(root)
    return dir_size(td) if td.exists() else 0


def _entry_label(snapshots: list[dict]) -> str:
    names = [s["chat"].get("name") or "?" for s in snapshots]
    if not names:
        return "?"
    if len(names) == 1:
        return names[0]
    return f"{names[0]} +{len(names) - 1}"
