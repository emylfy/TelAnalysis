"""Generate synthetic Telegram exports for README screenshots.

Writes two files:
  demo/group_pixelfox.json  — 7-person indie gamedev studio chat, ~2 years
  demo/personal_anya.json   — 2-person 1-on-1 (long-distance friends), ~1.5 years

No real conversations are referenced. All content is sampled from vocab pools
seeded with a fixed RNG so output is deterministic.

Usage:
    python3 tools/gen_demo_data.py
"""

from __future__ import annotations

import json
import math
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[1] / "demo"

# Vocab pools

GREETINGS = [
    "прив",
    "хай",
    "здаров",
    "доброе утро",
    "утро",
    "вечер",
    "хелло",
    "йо",
    "ну привет",
    "приветик",
    "доброе",
    "хей",
]

ACKS = [
    "ок",
    "окей",
    "ага",
    "угу",
    "понял",
    "ясно",
    "принял",
    "хорошо",
    "ок понял",
    "ну ладно",
    "лан",
    "поняла",
    "хорошо принято",
    "ясн",
    "пнл",
]

AGREES = [
    "согласен",
    "плюсую",
    "+",
    "++",
    "точно",
    "именно",
    "верно",
    "да-да",
    "ну да",
    "так и есть",
    "это факт",
    "истина",
    "база",
    "вайбово",
]

DISAGREES = [
    "не согласен",
    "не уверен",
    "хм спорно",
    "вряд ли",
    "ну не знаю",
    "сомневаюсь",
    "не факт",
    "ну такое",
    "странно",
]

QUESTIONS = [
    "а как ты думаешь?",
    "что скажешь?",
    "это норм?",
    "так пойдёт?",
    "успеем к пятнице?",
    "это критично?",
    "можно сегодня обсудить?",
    "кто доступен в 17?",
    "где взять?",
    "это баг или фича?",
    "что с билдом?",
    "когда релиз?",
    "ты на созвоне?",
    "почему такое решение?",
    "это срочно?",
    "ща у всех так?",
    "как чинить?",
    "это уже в проде?",
    "тесты прошли?",
    "ты в офисе сегодня?",
    "пушнул?",
    "смержим?",
    "это блокер?",
    "ревью посмотришь?",
    "до завтра отложим?",
]

DEV_TALK = [
    "пушнул фикс в main",
    "ребейзнулся на dev",
    "тесты упали локально",
    "ща поправлю",
    "коммит готов",
    "PR открыл",
    "просто конфликты в мердже",
    "ща ревью гляну",
    "запушил две правки",
    "залил билд в стиму",
    "профайлер показал ботлнек в рендере",
    "FPS просел на новой локации",
    "поправил утечку памяти",
    "переписал шейдер",
    "новый ассет завёз",
    "анимации добавил",
    "озвучку обновил",
    "локализацию докинул",
    "балансник поправил",
    "враги стали жирнее",
    "лут адекватнее теперь",
    "интерфейс перерисовал",
    "иконки готовы",
    "превью гифкой записал",
    "сборка под мак собралась",
    "виндовый билд кривой",
    "линукс тестируем",
    "стимдек запустился",
    "контроллер настроил",
    "клавиша смены оружия не работала",
    "звук переэкспортнул",
    "музыка зацикливается криво",
    "ambient починил",
]

GAMEDEV_NOUNS = [
    "спрайт",
    "коллизия",
    "хитбокс",
    "тайлсет",
    "шейдер",
    "партикл",
    "пайплайн",
    "ассет",
    "проп",
    "локация",
    "уровень",
    "босс",
    "энкаунтер",
    "лут",
    "крафт",
    "квест",
    "диалог",
    "катсцена",
    "анимация",
    "rig",
    "UI",
    "HUD",
    "меню",
    "пауза",
    "сейв",
    "ачивка",
    "трофей",
    "балансик",
    "враг",
    "моб",
    "AI",
    "патрулирование",
    "тригер",
    "хитскан",
    "хитрейт",
    "DPS",
    "контроллер",
    "инпут",
    "ремэп",
]

MEMES = [
    "это пять",
    "это уже не баг это фича",
    "я плакал",
    "ору с этого",
    "буквально я",
    "мне нужны выходные",
    "кофе закончился",
    "кому-нибудь нужно поспать",
    "мы это уже обсуждали кстати",
    "опять?",
    "снова всё с нуля",
    "лол",
    "не плачь",
    "крутяк",
    "огонь",
    "топ",
    "это база",
    "база-база",
    "проиграл",
    "вайбы",
    "стонкс",
    "ну сильно",
    "сильно",
    "ничосе",
    "ого",
]

COMPLAINTS = [
    "устал",
    "запарка",
    "горю",
    "не успеваю",
    "слишком много задач",
    "надо отдохнуть",
    "башка квадратная",
    "ну сколько можно",
    "опять переделывать",
    "это бесконечный круг",
    "мозг отказывает",
    "что-то ничего не понятно",
]

POSITIVE = [
    "ура",
    "наконец-то",
    "красиво вышло",
    "вы топ",
    "горжусь нами",
    "это круто",
    "это супер",
    "респект",
    "молодцы",
    "🔥",
    "великолепно",
    "лучше не бывает",
    "обнял всех",
    "люблю эту команду",
    "лучшая команда",
    "вы лучшие",
]

NEGATIVE_BUT_OK = [
    "опять что-то сломалось",
    "продакшн упал",
    "юзеры жалуются",
    "багов накопилось",
    "это серьёзно",
    "нужна срочная встреча",
    "deadline горит",
]

ANNOUNCEMENT_PREFIXES = [
    "короче,",
    "так,",
    "ребят,",
    "слушайте,",
    "внимание,",
    "напоминаю,",
    "обновление по фронту:",
]

PLANS_AND_TIMES = [
    "созвон в 15:00 по мск",
    "встреча завтра в 11",
    "созвон через час",
    "обсудим в понедельник",
    "давайте на следующей неделе",
    "к концу спринта точно",
    "на ревью в четверг",
    "после релиза вернёмся",
]

EMOJI_HEAVY = [
    "🔥",
    "💀",
    "😂",
    "😅",
    "🤔",
    "😩",
    "👍",
    "👌",
    "🥲",
    "🤡",
    "💩",
    "✨",
    "🚀",
    "🎮",
    "🎨",
    "🎵",
    "📦",
    "✅",
    "❌",
    "⚡",
    "💪",
    "🙏",
    "❤️",
    "😎",
    "🤯",
    "🥺",
    "👀",
    "😴",
    "🍕",
    "☕",
]

STICKER_EMOJIS = [
    "🐱",
    "🐶",
    "🦊",
    "🐸",
    "🐙",
    "🦝",
    "🦄",
    "🐼",
    "🐧",
    "🦋",
    "💀",
    "🔥",
    "✨",
    "💯",
    "🎉",
    "🙃",
    "😎",
    "🤡",
    "🤖",
    "👾",
]

LINKS = [
    "https://github.com/pixelfox/engine",
    "https://store.steampowered.com/app/0000/",
    "https://www.gamedev.net/articles/",
    "https://www.reddit.com/r/gamedev/",
    "https://twitter.com/i/status/12345",
    "https://www.youtube.com/watch?v=demo",
    "https://itch.io/games/featured",
]

# Group chat config

GROUP_USERS = [
    # (user_id, display_name, weight, hour_skew, personality)
    ("user1001", "Артём", 0.22, 0, "lead"),  # most active, baseline schedule
    ("user1002", "Маша", 0.16, +1, "artist"),  # slightly later
    ("user1003", "Костя", 0.18, +2, "dev"),  # late afternoon dev
    ("user1004", "Лена", 0.13, -1, "writer"),  # earlier morning
    ("user1005", "Денис", 0.11, +3, "sound"),  # evening
    ("user1006", "Юля", 0.12, 0, "comm"),  # ranges
    ("user1007", "Игорь", 0.08, +5, "bizdev"),  # late evening
]

GROUP_START = date(2024, 1, 15)
GROUP_END = date(2026, 5, 1)
GROUP_NAME = "Pixelfox Studio · core team"
GROUP_TYPE = "private_supergroup"

# 1-on-1 config

PERSONAL_ME_ID = "user2001"
PERSONAL_ME_NAME = "ты"
PERSONAL_OTHER_ID = "user2002"
PERSONAL_OTHER_NAME = "Аня"

PERSONAL_START = date(2024, 10, 1)
PERSONAL_END = date(2026, 5, 1)
PERSONAL_NAME = "Аня"
PERSONAL_TYPE = "personal_chat"

# 1-on-1 vocabulary (warmer/personal, less devspeak)

PERSONAL_AFFECTION = [
    "скучаю",
    "обнимаю",
    "люблю",
    "❤️",
    "ты лучшая",
    "ты лучший друг",
    "так рада тебе",
    "приятно слышать",
    "спасибо тебе",
    "береги себя",
    "сладких снов",
    "доброй ночи",
]

PERSONAL_DAILY = [
    "поела борщ сегодня",
    "ходила на йогу",
    "купила новый плед",
    "вышла на пробежку утром",
    "посмотрела фильм вчера",
    "погуляла по парку",
    "сходила в кафе с коллегой",
    "решила записаться на курсы",
    "сделала ремонт в комнате",
    "взяла котёнка из приюта",
    "съездила к родителям на выходные",
    "была на концерте",
    "купила билет на самолёт",
    "тестирую новый рецепт паста с грибами",
]

PERSONAL_MOOD_GOOD = [
    "настроение огонь",
    "день прошёл супер",
    "я в полном восторге",
    "так классно сегодня",
    "чувствую себя живой",
]

PERSONAL_MOOD_OK = ["вроде норм", "ну обычно", "так себе", "никак", "ровно", "ни плохо ни хорошо"]

PERSONAL_MOOD_LOW = [
    "устала очень",
    "грустно сегодня",
    "что-то не очень",
    "не выспалась",
    "болит голова",
    "тяжёлая неделя",
    "ничего не успеваю",
    "выгорела на работе",
]

PERSONAL_QUESTIONS = [
    "как ты?",
    "как день прошёл?",
    "что вечером делаешь?",
    "выходные планируешь?",
    "как работа?",
    "как семья?",
    "ты как себя чувствуешь?",
    "выспалась?",
    "ела сегодня?",
    "когда увидимся?",
    "когда приедешь?",
    "когда созвонимся?",
    "посмотрел сериал тот?",
    "читала что-нибудь?",
    "погода у вас как?",
]

# Generation helpers


def _hour_weight(hour: int, skew: int) -> float:
    """Bell-ish curve centered around 11-21, with skew shifting peak."""
    center = 15 + skew * 0.3
    spread = 4.5
    return math.exp(-((hour - center) ** 2) / (2 * spread**2))


def _day_weight(d: date) -> float:
    """Weekday > weekend slightly. Seasonal dip in summer for both chats."""
    wd = d.weekday()
    base = 1.0 if wd < 5 else 0.65
    month = d.month
    seasonal = 0.7 if month in (7, 8) else (0.85 if month == 12 else 1.0)
    return base * seasonal


def _pick(rng: random.Random, items: list, weights: list[float] | None = None):
    if weights is None:
        return rng.choice(items)
    return rng.choices(items, weights=weights, k=1)[0]


def _maybe_emoji(rng: random.Random, prob: float = 0.18) -> str:
    if rng.random() < prob:
        n = rng.choices([1, 2, 3], weights=[0.7, 0.22, 0.08])[0]
        return " " + "".join(rng.choice(EMOJI_HEAVY) for _ in range(n))
    return ""


def _group_message_text(rng: random.Random, user_personality: str, msg_idx: int) -> str:
    """Sample a group-chat message based on user personality."""
    roll = rng.random()
    if user_personality == "lead":
        if roll < 0.25:
            return _pick(rng, ANNOUNCEMENT_PREFIXES) + " " + _pick(rng, DEV_TALK)
        if roll < 0.45:
            return _pick(rng, QUESTIONS)
        if roll < 0.65:
            return _pick(rng, DEV_TALK)
        if roll < 0.78:
            return _pick(rng, AGREES)
        if roll < 0.88:
            return _pick(rng, PLANS_AND_TIMES)
        return _pick(rng, ACKS)
    if user_personality == "artist":
        if roll < 0.35:
            return rng.choice(MEMES) + _maybe_emoji(rng, 0.5)
        if roll < 0.55:
            return rng.choice(POSITIVE) + _maybe_emoji(rng, 0.4)
        if roll < 0.7:
            return rng.choice(DEV_TALK)
        if roll < 0.85:
            return rng.choice(ACKS) + _maybe_emoji(rng, 0.3)
        return rng.choice(GREETINGS)
    if user_personality == "dev":
        if roll < 0.4:
            return rng.choice(DEV_TALK)
        if roll < 0.6:
            return rng.choice(MEMES)
        if roll < 0.72:
            return rng.choice(COMPLAINTS)
        if roll < 0.82:
            return rng.choice(QUESTIONS)
        if roll < 0.92:
            return rng.choice(LINKS)
        return rng.choice(AGREES)
    if user_personality == "writer":
        if roll < 0.3:
            return "я подумала, что " + rng.choice(DEV_TALK)
        if roll < 0.5:
            return rng.choice(POSITIVE)
        if roll < 0.7:
            return rng.choice(QUESTIONS)
        return rng.choice(ACKS)
    if user_personality == "sound":
        if roll < 0.3:
            return rng.choice(ACKS)
        if roll < 0.5:
            return rng.choice(POSITIVE) + _maybe_emoji(rng, 0.5)
        return rng.choice(DEV_TALK)
    if user_personality == "comm":
        if roll < 0.25:
            return rng.choice(LINKS)
        if roll < 0.5:
            return rng.choice(ANNOUNCEMENT_PREFIXES) + " " + rng.choice(PLANS_AND_TIMES)
        if roll < 0.7:
            return rng.choice(POSITIVE)
        return rng.choice(QUESTIONS)
    # bizdev
    if roll < 0.4:
        return rng.choice(ACKS)
    if roll < 0.6:
        return rng.choice(PLANS_AND_TIMES)
    if roll < 0.8:
        return rng.choice(QUESTIONS)
    return rng.choice(AGREES)


def _personal_message_text(rng: random.Random, mood_phase: str) -> str:
    """1-on-1 message sampling. `mood_phase` shifts the affect distribution."""
    roll = rng.random()
    if mood_phase == "happy":
        if roll < 0.20:
            return rng.choice(PERSONAL_AFFECTION)
        if roll < 0.40:
            return rng.choice(PERSONAL_MOOD_GOOD)
        if roll < 0.55:
            return rng.choice(PERSONAL_DAILY)
        if roll < 0.7:
            return rng.choice(PERSONAL_QUESTIONS)
        if roll < 0.85:
            return rng.choice(GREETINGS)
        return rng.choice(ACKS)
    if mood_phase == "drift":
        if roll < 0.08:
            return rng.choice(PERSONAL_AFFECTION)
        if roll < 0.35:
            return rng.choice(PERSONAL_MOOD_LOW)
        if roll < 0.55:
            return rng.choice(PERSONAL_MOOD_OK)
        if roll < 0.7:
            return rng.choice(PERSONAL_DAILY)
        if roll < 0.85:
            return rng.choice(ACKS)
        return rng.choice(PERSONAL_QUESTIONS)
    if mood_phase == "rebuild":
        if roll < 0.15:
            return rng.choice(PERSONAL_AFFECTION)
        if roll < 0.35:
            return rng.choice(PERSONAL_MOOD_OK)
        if roll < 0.55:
            return rng.choice(PERSONAL_MOOD_GOOD)
        if roll < 0.75:
            return rng.choice(PERSONAL_DAILY)
        return rng.choice(PERSONAL_QUESTIONS)
    # neutral
    if roll < 0.3:
        return rng.choice(PERSONAL_DAILY)
    if roll < 0.55:
        return rng.choice(PERSONAL_QUESTIONS)
    if roll < 0.75:
        return rng.choice(ACKS)
    return rng.choice(GREETINGS)


def _spike(d: date, group: bool) -> float:
    """Multiplier for special burst-activity days."""
    spikes = (
        [
            (date(2024, 6, 7), 3.0, "demo launch"),
            (date(2024, 8, 21), 2.6, "gamescom"),
            (date(2024, 11, 22), 4.0, "early access release"),
            (date(2025, 3, 14), 2.0, "patch 1.1"),
            (date(2025, 5, 9), 1.8, "studio bday"),
            (date(2025, 9, 12), 3.2, "1.0 release"),
            (date(2026, 2, 14), 2.4, "valentines / dlc"),
        ]
        if group
        else [
            (date(2024, 12, 31), 2.5, "new year"),
            (date(2025, 3, 8), 2.3, "march 8"),
            (date(2025, 7, 4), 2.0, "anya birthday"),
            (date(2025, 10, 18), 0.2, "drift week"),
            (date(2025, 11, 1), 0.15, "silence"),
            (date(2025, 12, 25), 2.6, "reconcile"),
        ]
    )
    for sd, mult, _ in spikes:
        delta = abs((d - sd).days)
        if delta <= 2:
            return 1 + (mult - 1) * (1 - delta / 3)
    return 1.0


def _drift_dip(d: date, group: bool) -> float:
    """Periods of low activity (vacations / arguments)."""
    if group:
        # team summer vacation 2024-07-15 → 2024-08-05
        if date(2024, 7, 15) <= d <= date(2024, 8, 5):
            return 0.25
        # crunch — opposite, super high (handled by spike)
        if date(2025, 8, 20) <= d <= date(2025, 9, 12):
            return 1.7
        return 1.0
    # personal: drift period before silence
    if date(2025, 10, 5) <= d <= date(2025, 10, 25):
        return 0.4
    if date(2025, 10, 26) <= d <= date(2025, 11, 24):
        return 0.08
    return 1.0


def _personal_phase(d: date) -> str:
    if d < date(2025, 9, 25):
        return "happy"
    if d < date(2025, 11, 25):
        return "drift"
    return "rebuild"


def gen_group_messages():
    rng = random.Random(42)
    messages = []
    msg_id = 1
    total_days = (GROUP_END - GROUP_START).days
    recent_ids: list[int] = []  # for reply targets

    target_per_day_avg = 95

    user_names = [u[1] for u in GROUP_USERS]
    user_ids = [u[0] for u in GROUP_USERS]
    user_weights = [u[2] for u in GROUP_USERS]

    for day_offset in range(total_days):
        d = GROUP_START + timedelta(days=day_offset)
        dw = _day_weight(d)
        spike = _spike(d, group=True)
        dip = _drift_dip(d, group=True)
        n_today = int(target_per_day_avg * dw * spike * dip * rng.uniform(0.7, 1.3))
        for _ in range(n_today):
            # pick user
            uidx = rng.choices(range(len(GROUP_USERS)), weights=user_weights, k=1)[0]
            uid, uname, _, hskew, persona = GROUP_USERS[uidx]
            # pick hour weighted by personality
            hour_w = [_hour_weight(h, hskew) for h in range(24)]
            hour = rng.choices(range(24), weights=hour_w, k=1)[0]
            minute = rng.randint(0, 59)
            second = rng.randint(0, 59)
            ts = datetime(d.year, d.month, d.day, hour, minute, second)

            text = _group_message_text(rng, persona, msg_id)
            # add emoji tail sometimes
            text += _maybe_emoji(rng, 0.22)

            msg = {
                "id": msg_id,
                "type": "message",
                "date": ts.strftime("%Y-%m-%dT%H:%M:%S"),
                "date_unixtime": str(int(ts.replace(tzinfo=timezone.utc).timestamp() - 3 * 3600)),
                "from": uname,
                "from_id": uid,
                "text": text,
                "text_entities": [{"type": "plain", "text": text}],
            }

            # 30% reply rate, only target recent messages
            if recent_ids and rng.random() < 0.32:
                # pick from last 25
                pool = recent_ids[-25:]
                msg["reply_to_message_id"] = rng.choice(pool)

            # 3% sticker
            r = rng.random()
            if r < 0.03:
                msg["media_type"] = "sticker"
                msg["sticker_emoji"] = rng.choice(STICKER_EMOJIS)
                msg["text"] = ""
                msg["text_entities"] = []
            elif r < 0.06:  # 3% voice
                msg["media_type"] = "voice_message"
                msg["duration_seconds"] = rng.randint(5, 220)
                msg["text"] = ""
                msg["text_entities"] = []
            elif r < 0.065:  # 0.5% photo
                msg["media_type"] = "photo"
                if rng.random() < 0.4:
                    msg["caption"] = rng.choice(DEV_TALK)
            elif r < 0.075:  # 1% forward
                msg["forwarded_from"] = rng.choice(
                    [
                        "Indie Game Dev News",
                        "Game Programming Patterns",
                        "Pixel Art Daily",
                        "Unity Russia",
                        "Godot Engine",
                        "@unrealengine",
                        "Steam Updates",
                    ]
                )

            messages.append(msg)
            recent_ids.append(msg_id)
            if len(recent_ids) > 100:
                recent_ids = recent_ids[-100:]
            msg_id += 1

    return messages


def gen_personal_messages():
    rng = random.Random(123)
    messages = []
    msg_id = 1
    total_days = (PERSONAL_END - PERSONAL_START).days
    recent_ids: list[int] = []

    target_per_day_avg = 38

    for day_offset in range(total_days):
        d = PERSONAL_START + timedelta(days=day_offset)
        dw = _day_weight(d)
        spike = _spike(d, group=False)
        dip = _drift_dip(d, group=False)
        n_today = int(target_per_day_avg * dw * spike * dip * rng.uniform(0.6, 1.4))
        phase = _personal_phase(d)
        for _ in range(n_today):
            # 50/50 with slight skew towards Anya replying more in drift phase
            if phase == "drift":
                is_me = rng.random() < 0.6
            else:
                is_me = rng.random() < 0.5

            uid = PERSONAL_ME_ID if is_me else PERSONAL_OTHER_ID
            uname = PERSONAL_ME_NAME if is_me else PERSONAL_OTHER_NAME
            hskew = 0 if is_me else +2
            hour_w = [_hour_weight(h, hskew) for h in range(24)]
            hour = rng.choices(range(24), weights=hour_w, k=1)[0]
            minute = rng.randint(0, 59)
            second = rng.randint(0, 59)
            ts = datetime(d.year, d.month, d.day, hour, minute, second)

            text = _personal_message_text(rng, phase)
            text += _maybe_emoji(rng, 0.30 if phase == "happy" else 0.12)

            msg = {
                "id": msg_id,
                "type": "message",
                "date": ts.strftime("%Y-%m-%dT%H:%M:%S"),
                "date_unixtime": str(int(ts.replace(tzinfo=timezone.utc).timestamp() - 3 * 3600)),
                "from": uname,
                "from_id": uid,
                "text": text,
                "text_entities": [{"type": "plain", "text": text}],
            }

            if recent_ids and rng.random() < 0.18:
                msg["reply_to_message_id"] = rng.choice(recent_ids[-15:])

            r = rng.random()
            if r < 0.05:  # 5% sticker (higher than group)
                msg["media_type"] = "sticker"
                msg["sticker_emoji"] = rng.choice(STICKER_EMOJIS)
                msg["text"] = ""
                msg["text_entities"] = []
            elif r < 0.10:  # 5% voice (long-distance friends → more voice)
                msg["media_type"] = "voice_message"
                msg["duration_seconds"] = rng.randint(10, 420)
                msg["text"] = ""
                msg["text_entities"] = []
            elif r < 0.12:  # 2% photo
                msg["media_type"] = "photo"
                if rng.random() < 0.5:
                    msg["caption"] = rng.choice(PERSONAL_DAILY)

            messages.append(msg)
            recent_ids.append(msg_id)
            if len(recent_ids) > 60:
                recent_ids = recent_ids[-60:]
            msg_id += 1

    return messages


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    group_msgs = gen_group_messages()
    group_export = {
        "name": GROUP_NAME,
        "type": GROUP_TYPE,
        "id": 7771001,
        "messages": group_msgs,
    }
    group_path = OUT_DIR / "group_pixelfox.json"
    group_path.write_text(json.dumps(group_export, ensure_ascii=False), encoding="utf-8")
    print(f"  group : {len(group_msgs):,} msgs → {group_path}")

    personal_msgs = gen_personal_messages()
    personal_export = {
        "name": PERSONAL_NAME,
        "type": PERSONAL_TYPE,
        "id": 7772001,
        "messages": personal_msgs,
    }
    personal_path = OUT_DIR / "personal_anya.json"
    personal_path.write_text(json.dumps(personal_export, ensure_ascii=False), encoding="utf-8")
    print(f"  personal : {len(personal_msgs):,} msgs → {personal_path}")


if __name__ == "__main__":
    main()
