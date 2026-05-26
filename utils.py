import json
import re
import string

import emoji
import jmespath

spec_chars = string.punctuation + '\n\xa0«»\t—…"<>?!.,;:꧁@#$%^&*()_+=№%༺༺\\༺/༺•'


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


DEFAULT_CONF = {
    "select_type_stem": "Off",
    "most_com": 30,
    "most_com_channel": 100,
}


def read_conf(option):
    try:
        with open("config.json") as f:
            data = json.load(f)
        return jmespath.search(option, data)
    except (FileNotFoundError, json.JSONDecodeError):
        write_conf(DEFAULT_CONF)
        return DEFAULT_CONF.get(option)


def write_conf(dct: dict) -> None:
    with open("config.json", "w") as fw:
        json.dump(dct, fw)


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
