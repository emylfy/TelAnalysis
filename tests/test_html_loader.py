"""Tests for analysis.html_loader and the loader.load_export dispatcher.

The HTML fixture mirrors the real Telegram Desktop export structure: a page
header, a day-divider service block, a real service message, a normal message
with inline formatting, a "joined" continuation (no from_name), a reply, a
forwarded message, and a voice message.
"""

from __future__ import annotations

import json
from pathlib import Path

from analysis import html_loader, loader

FIXTURE = """<!DOCTYPE html>
<html><body>
 <div class="page_header"><div class="content">
  <div class="text bold">
Team Chat
  </div>
 </div></div>
 <div class="history">

  <div class="message service" id="message-1">
   <div class="body details">
14 December 2021
   </div>
  </div>

  <div class="message service" id="message1">
   <div class="body details">
Group &laquo;Team Chat&raquo; created
   </div>
  </div>

  <div class="message default clearfix" id="message2">
   <div class="body">
    <div class="pull_right date details" title="14.12.2021 23:43:49 UTC+03:00">23:43</div>
    <div class="from_name">
Alice
    </div>
    <div class="text">
Hello &quot;<strong>world</strong>&quot;<br>second line
    </div>
   </div>
  </div>

  <div class="message default clearfix joined" id="message3">
   <div class="body">
    <div class="pull_right date details" title="14.12.2021 23:44:00 UTC+03:00">23:44</div>
    <div class="text">
still Alice talking
    </div>
   </div>
  </div>

  <div class="message default clearfix" id="message4">
   <div class="body">
    <div class="pull_right date details" title="14.12.2021 23:45:10 UTC+03:00">23:45</div>
    <div class="from_name">
Bob
    </div>
    <div class="reply_to details">
In reply to <a href="#go_to_message2" onclick="return GoToMessage(2)">this message</a>
    </div>
    <div class="text">
replying to Alice
    </div>
   </div>
  </div>

  <div class="message default clearfix" id="message5">
   <div class="body">
    <div class="pull_right date details" title="14.12.2021 23:46:00 UTC+03:00">23:46</div>
    <div class="from_name">
Bob
    </div>
    <div class="forwarded body">
     <div class="from_name">
Carol <span class="date details" title="10.12.2021 09:00:00 UTC+03:00"> 10.12.2021 09:00:00</span>
     </div>
     <div class="text">
forwarded content
     </div>
    </div>
   </div>
  </div>

  <div class="message default clearfix" id="message6">
   <div class="body">
    <div class="pull_right date details" title="14.12.2021 23:47:30 UTC+03:00">23:47</div>
    <div class="from_name">
Alice
    </div>
    <div class="media_wrap clearfix">
     <div class="media clearfix pull_left media_voice_message">
      <div class="body">
       <div class="title bold">Voice message</div>
       <div class="status details">00:41, 164.2 KB</div>
      </div>
     </div>
    </div>
   </div>
  </div>

 </div>
</body></html>
"""


def _write(tmp_path: Path, name: str = "messages.html") -> Path:
    p = tmp_path / name
    p.write_text(FIXTURE, encoding="utf-8")
    return p


def test_parses_header_and_counts(tmp_path: Path):
    data = html_loader.parse_html_export(str(_write(tmp_path)))
    assert data["name"] == "Team Chat"
    assert data["_source"] == "html"
    msgs = data["messages"]
    # day divider dropped; 1 service + 5 real messages
    assert sum(m["type"] == "service" for m in msgs) == 1
    assert sum(m["type"] == "message" for m in msgs) == 5


def test_day_divider_dropped(tmp_path: Path):
    data = html_loader.parse_html_export(str(_write(tmp_path)))
    texts = [m.get("text") for m in data["messages"]]
    assert "14 December 2021" not in texts
    assert any("created" in (t or "") for t in texts)


def test_text_flattened_with_formatting(tmp_path: Path):
    data = html_loader.parse_html_export(str(_write(tmp_path)))
    m2 = next(m for m in data["messages"] if m["id"] == 2)
    assert m2["text"] == 'Hello "world"\nsecond line'


def test_date_reconstructed_offset_aware(tmp_path: Path):
    data = html_loader.parse_html_export(str(_write(tmp_path)))
    m2 = next(m for m in data["messages"] if m["id"] == 2)
    assert m2["date"] == "2021-12-14T23:43:49"
    # 23:43:49 +03:00 == 20:43:49 UTC == 1639514629
    assert m2["date_unixtime"] == "1639514629"


def test_joined_block_carries_sender_forward(tmp_path: Path):
    data = html_loader.parse_html_export(str(_write(tmp_path)))
    m3 = next(m for m in data["messages"] if m["id"] == 3)
    assert m3["from"] == "Alice"
    assert m3["from_id"] == "html:Alice"


def test_synthetic_from_id(tmp_path: Path):
    data = html_loader.parse_html_export(str(_write(tmp_path)))
    bob = next(m for m in data["messages"] if m["id"] == 4)
    assert bob["from_id"] == "html:Bob"


def test_reply_target_parsed(tmp_path: Path):
    data = html_loader.parse_html_export(str(_write(tmp_path)))
    m4 = next(m for m in data["messages"] if m["id"] == 4)
    assert m4["reply_to_message_id"] == 2


def test_forwarded_from_parsed(tmp_path: Path):
    data = html_loader.parse_html_export(str(_write(tmp_path)))
    m5 = next(m for m in data["messages"] if m["id"] == 5)
    assert m5["forwarded_from"] == "Carol"
    assert "forwarded content" in m5["text"]


def test_voice_message_media_and_duration(tmp_path: Path):
    data = html_loader.parse_html_export(str(_write(tmp_path)))
    m6 = next(m for m in data["messages"] if m["id"] == 6)
    assert m6["media_type"] == "voice_message"
    assert m6["duration_seconds"] == 41


def test_multifile_natural_order():
    # messages10 must sort after messages2, not before
    files = ["/x/messages10.html", "/x/messages.html", "/x/messages2.html"]
    assert sorted(files, key=html_loader._msg_file_order) == [
        "/x/messages.html",
        "/x/messages2.html",
        "/x/messages10.html",
    ]


# --- load_export dispatcher -------------------------------------------------


def test_load_export_html_file(tmp_path: Path):
    data = loader.load_export(str(_write(tmp_path)))
    assert data["_source"] == "html"
    assert data["name"] == "Team Chat"


def test_load_export_json_file_has_no_source(tmp_path: Path):
    p = tmp_path / "result.json"
    p.write_text(json.dumps({"name": "X", "type": "personal_chat", "messages": []}), encoding="utf-8")
    data = loader.load_export(str(p))
    assert "_source" not in data
    assert data["name"] == "X"


def test_load_export_dir_prefers_json(tmp_path: Path):
    (tmp_path / "result.json").write_text(
        json.dumps({"name": "FromJSON", "type": "personal_chat", "messages": []}),
        encoding="utf-8",
    )
    _write(tmp_path)  # also drop a messages.html alongside
    data = loader.load_export(str(tmp_path))
    assert data["name"] == "FromJSON"
    assert "_source" not in data


def test_load_export_dir_falls_back_to_html(tmp_path: Path):
    _write(tmp_path)
    data = loader.load_export(str(tmp_path))
    assert data["_source"] == "html"
    assert data["name"] == "Team Chat"


def test_load_export_via_list_chats(tmp_path: Path):
    data = loader.load_export(str(_write(tmp_path)))
    chats = loader.list_chats(data)
    assert len(chats) == 1
    assert chats[0].name == "Team Chat"
    assert len(chats[0].messages) == 6
