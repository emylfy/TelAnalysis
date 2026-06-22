"""Tests for utils: text sanitisation, emoji stripping, filename sanitisation,
config IO."""

from __future__ import annotations

import json
from pathlib import Path

from analysis import utils

# remove_emojis


def test_remove_emojis_strips_emoji_keeps_text():
    assert utils.remove_emojis("hello 👋 world") == "hello world"


def test_remove_emojis_preserves_cyrillic():
    assert utils.remove_emojis("привет 🔥 мир") == "привет мир"


def test_remove_emojis_collapses_whitespace():
    assert utils.remove_emojis("a    b\n\nc") == "a b c"


def test_remove_emojis_handles_none():
    assert utils.remove_emojis(None) == ""


def test_remove_emojis_handles_empty():
    assert utils.remove_emojis("") == ""


def test_remove_emojis_pure_emoji_string():
    assert utils.remove_emojis("🔥🎉👋") == ""


# remove_chars_from_text


def test_remove_chars_from_text_default_strips_punct():
    out = utils.remove_chars_from_text("hello, world!")
    assert "," not in out
    assert "!" not in out
    assert "hello" in out
    assert "world" in out


def test_remove_chars_from_text_custom_chars():
    out = utils.remove_chars_from_text("a-b-c", "-")
    assert out == "a b c"


# sanitize_chat_filename


def test_sanitize_chat_filename_basic():
    assert utils.sanitize_chat_filename("Alice", 123) == "Alice_123"


def test_sanitize_chat_filename_strips_special():
    out = utils.sanitize_chat_filename("Alice & Bob!", 1)
    assert " " not in out
    assert "&" not in out
    assert "!" not in out
    assert out.endswith("_1")


def test_sanitize_chat_filename_falls_back_to_saved_messages():
    out = utils.sanitize_chat_filename(None, 999)
    assert "saved_messages" in out
    assert out.endswith("_999")


def test_sanitize_chat_filename_truncates_long_name():
    long_name = "a" * 200
    out = utils.sanitize_chat_filename(long_name, 1)
    # base capped at 60 + "_<id>"
    assert len(out.rsplit("_", 1)[0]) <= 60


# clear_user


def test_clear_user_strips_spaces_and_emojis():
    assert utils.clear_user("Иван 🔥") == "Иван"


def test_clear_user_handles_int():
    assert utils.clear_user(12345) == "12345"


# read_conf / write_conf


def test_read_conf_falls_back_to_defaults_when_missing(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(utils, "CONFIG_PATH", tmp_path / "config.json")
    val = utils.read_conf("select_type_stem")
    assert val == utils.DEFAULT_CONF["select_type_stem"]
    # write_conf should have created the file
    assert (tmp_path / "config.json").exists()


def test_write_conf_then_read_conf_roundtrip(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(utils, "CONFIG_PATH", tmp_path / "config.json")
    utils.write_conf({"select_type_stem": "On"})
    assert utils.read_conf("select_type_stem") == "On"


def test_read_conf_recovers_from_corrupted_file(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(utils, "CONFIG_PATH", tmp_path / "config.json")
    (tmp_path / "config.json").write_text("not json at all", encoding="utf-8")
    val = utils.read_conf("select_type_stem")
    assert val == utils.DEFAULT_CONF["select_type_stem"]
    # Should have rewritten with defaults
    written = json.loads((tmp_path / "config.json").read_text())
    assert written == utils.DEFAULT_CONF
