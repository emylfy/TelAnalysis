import re
import string
import emoji
import os
import subprocess
import platform
import json
import jmespath

spec_chars = string.punctuation + '\n\xa0«»\t—…"<>?!.,;:꧁@#$%^&*()_+=№%༺༺\༺/༺•'


# Full-export support
def is_full_export(data):
    return (
        isinstance(data, dict)
        and isinstance(data.get("chats"), dict)
        and isinstance(data["chats"].get("list"), list)
    )


def sanitize_chat_filename(name, chat_id):
    base = name if name else "saved_messages"
    base = re.sub(r"[^\w\-]+", "_", base, flags=re.UNICODE)
    base = base.strip("_")[:60] or "chat"
    return f"{base}_{chat_id}"


def build_chat_options(data):
    opts = []
    for chat in data["chats"]["list"]:
        cid = chat.get("id")
        name = chat.get("name") or "Saved Messages"
        ctype = chat.get("type", "?")
        msg_count = len(chat.get("messages") or [])
        label = f"{name} [{ctype}] ({msg_count} msgs)"
        opts.append({"label": label, "value": str(cid)})
    return opts


def find_chat_by_id(data, chat_id):
    for chat in data["chats"]["list"]:
        if str(chat.get("id")) == str(chat_id):
            return chat
    return None


def write_chat_as_single(chat, asset_dir="asset"):
    cid = chat.get("id")
    name = chat.get("name")
    safe = sanitize_chat_filename(name, cid)
    payload = {
        "name": name or "Saved Messages",
        "type": chat.get("type"),
        "id": cid,
        "messages": chat.get("messages") or [],
    }
    os.makedirs(asset_dir, exist_ok=True)
    path = os.path.join(asset_dir, f"{safe}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    return path


##config telanalysis
def read_conf(option):
    try:
        with open("config.json", "r") as read_conf:
            read_conf = json.load(read_conf)
            select_type_stem = jmespath.search(f"{option}", read_conf)
        return select_type_stem
    except:
        write_conf(
            '{"select_type_stem": "Off", "most_com": 30, "most_com_channel":100}'
        )


def write_conf(dct):
    with open("config.json", "w") as fw:
        json.dump(dct, fw)


def clear_console():
    system = platform.system()
    if system == "Windows":
        subprocess.run("cls", shell=True)
    elif system == "Darwin" or system == "Linux":
        subprocess.run("clear", shell=True)


def open_url():
    system = platform.system()
    if system == "Windows":
        subprocess.run(f"start http://127.0.0.1:9993", shell=True)
    elif system == "Darwin" or system == "Linux":
        subprocess.run("open http://127.0.0.1:9993", shell=True)


def remove_chars_from_text(text, char=None):
    if char is None:
        char = spec_chars

    pattern = f"[{re.escape(char)}]"
    text = re.sub(pattern, " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def remove_emojis(data):
    """Strip Unicode emoji codepoints from text.
    Preserves all non-emoji content: ASCII, cyrillic, punctuation, digits.
    Whitespace is collapsed."""
    if data is None:
        return ""
    if not isinstance(data, str):
        try:
            data = str(data)
        except Exception:
            return ""
    data = emoji.replace_emoji(data, replace="")
    data = re.sub(r"\s+", " ", data).strip()
    return data


def clear_user(user):
    # Убираем спецсимволы, эмодзи и очищаем текст
    user = str(user).replace(" ", "").replace('"', "").replace(".", "").replace("꧁", "")
    user = remove_chars_from_text(user)
    user = remove_emojis(user)

    return user.strip()  # Удаляем пробелы в начале и конце строки
