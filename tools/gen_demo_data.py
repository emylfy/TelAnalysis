"""Generate synthetic Telegram exports (English) for README screenshots.

Writes two files:
  demo/group_demo.json     — 7-person indie gamedev studio chat, ~2 years
  demo/personal_demo.json  — 2-person 1-on-1 (long-distance friends), ~1.5 years

Design goals (so the dashboard charts look alive, not robotic):
  * Distinct per-user profiles — active hours, message length, emoji rate and
    topic vocabulary all differ, so the per-user radar / heatmaps look varied.
  * Affinity-based replies — people mostly reply to their cluster (the two devs
    talk to each other, artist <-> writer, etc.), so the network graph forms
    real Louvain communities instead of one mush.
  * Variable message length — most messages are short, some run several
    sentences, and a few personas write 300+ char essays, giving a realistic
    length distribution, a visible "essayist" persona and "longest monologues".
  * Per-persona emphasis — ALL-CAPS shouts and "!" exclamations vary by person
    (Maya/Noah shout, Ethan/Ivan rarely), so those speaking-style axes light up.
  * Media variety — stickers, voice, round video, GIFs, audio, files, polls,
    locations and shared contacts, weighted per chat, so the media breakdown
    shows the full range the loader recognises (not just 2-3 types).
  * Topically coherent messages — each message draws all its sentences from one
    category, so previews and n-gram phrases read sensibly.
  * The 1-on-1 vocabulary is curated against the sentiment model
    (seara/rubert-tiny2-russian-sentiment) so the relationship arc — happy ->
    drift -> silence -> rebuild — comes out clean even on English text.

No real conversations are referenced. All content is sampled from vocab pools
seeded with a fixed RNG so output is deterministic.

Usage:
    python3 tools/gen_demo_data.py
"""

from __future__ import annotations

import math
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# json is imported lazily in main(); keep module import-light for tooling.

OUT_DIR = Path(__file__).resolve().parents[1] / "demo"

# Shared vocab pools

GREETINGS = [
    "hey",
    "hi",
    "morning",
    "yo",
    "heya",
    "hello",
    "good morning",
    "gm",
    "evening",
    "hey all",
    "hey team",
    "sup",
    "oh hi",
    "howdy",
]

ACKS = [
    "ok",
    "okay",
    "got it",
    "sure",
    "yep",
    "right",
    "noted",
    "sounds good",
    "alright",
    "makes sense",
    "cool",
    "k",
    "gotcha",
    "will do",
    "on it",
    "fair enough",
    "understood",
    "roger that",
]

AGREES = [
    "agreed",
    "totally",
    "exactly",
    "100%",
    "this",
    "big +1",
    "well said",
    "couldn't agree more",
    "for sure",
    "yeah exactly",
    "true",
    "facts",
    "spot on",
    "good point",
    "same here",
]

DISAGREES = [
    "not sure about that",
    "hmm i disagree",
    "i don't think so",
    "that's debatable",
    "not convinced",
    "eh maybe not",
    "i'd push back on that",
    "not so sure",
    "let's reconsider",
]

QUESTIONS = [
    "what do you think?",
    "does this look ok?",
    "is this fine?",
    "can we ship this?",
    "will we make friday?",
    "is this critical?",
    "can we talk later today?",
    "who's free at 5?",
    "where do i find that?",
    "is this a bug or a feature?",
    "how's the build?",
    "when's the release?",
    "are you on the call?",
    "why this approach?",
    "is this urgent?",
    "how do we fix this?",
    "is this in prod yet?",
    "did the tests pass?",
    "are you in the office today?",
    "did you push it?",
    "can we merge?",
    "is this a blocker?",
    "can you review my PR?",
    "should we punt this to tomorrow?",
    "thoughts?",
    "any blockers?",
    "what's the status?",
]

MEMES = [
    "this is fine",
    "that's a feature not a bug",
    "i'm crying",
    "i can't with this",
    "literally me",
    "i need a weekend",
    "out of coffee again",
    "can someone please sleep",
    "we've been here before",
    "not again",
    "starting over from scratch",
    "lol",
    "lmao",
    "peak",
    "goated",
    "absolute cinema",
    "no thoughts just vibes",
    "real",
    "based",
    "i'm dead",
    "huge",
    "let's gooo",
    "ship it",
]

COMPLAINTS = [
    "so tired",
    "swamped today",
    "i'm burning out",
    "can't keep up",
    "too many tasks",
    "need a break",
    "my brain is fried",
    "how is it monday again",
    "reworking this again",
    "this is an endless loop",
    "running on fumes",
    "the deadline is eating me alive",
]

POSITIVE = [
    "finally!",
    "that came out great",
    "you all rock",
    "so proud of us",
    "this is awesome",
    "this looks incredible",
    "respect",
    "nice work everyone",
    "huge milestone",
    "love this team",
    "best team ever",
    "you're all amazing",
    "we shipped it",
    "incredible work",
    "that's a wrap",
]

ANNOUNCEMENT_PREFIXES = [
    "ok so",
    "heads up",
    "team,",
    "everyone,",
    "quick update:",
    "reminder:",
    "frontend update:",
    "fyi",
]

PLANNING = [
    "standup in 10",
    "let's sync at 3",
    "call in an hour",
    "let's discuss this monday",
    "pushing this to next sprint",
    "demo build is due thursday",
    "retro on friday",
    "i'll set up a call",
    "let's timebox this to an hour",
    "roadmap review is tomorrow",
    "let's lock scope for the milestone",
    "sprint planning at 11",
    "i'll write up the agenda",
    "let's not block the release on this",
    "let's circle back after the release",
    "moving this to the backlog for now",
]

ENGINE = [
    "pushed the fix to main",
    "rebased on dev again",
    "rewrote the shader",
    "fixed the memory leak",
    "profiler showed a bottleneck in the renderer",
    "fps dropped on the new level",
    "optimized the draw calls",
    "cleaned up the asset pipeline",
    "cut load times in half",
    "the build compiles on mac now",
    "the windows build is broken again",
    "got it running on steam deck",
    "fixed the frame pacing",
    "reduced the memory footprint",
    "the lighting pass is way faster now",
    "shipping the nightly build",
    "cache invalidation was the bug",
    "fixed the crash on startup",
]

GAMEPLAY = [
    "tuned the enemy AI",
    "the hitboxes feel better now",
    "reworked the dash mechanic",
    "fixed the double-jump bug",
    "loot tables are more balanced now",
    "bosses hit harder this patch",
    "added controller remapping",
    "the parry window felt too tight",
    "the new encounter is in",
    "fixed the save corruption bug",
    "weapon switching was broken",
    "patrol paths are smoother now",
    "added the checkpoint system",
    "the difficulty curve feels right now",
    "respawn logic is fixed",
    "combat feels way snappier",
]

ART = [
    "icons are done",
    "new character sprites are in",
    "repainted the main menu",
    "the tileset is ready",
    "the new particle effects look great",
    "redrew the HUD",
    "the boss concept is finished",
    "the color palette is locked",
    "animations are smoother now",
    "added the idle animation",
    "exported the new props",
    "the key art is coming together",
    "recorded a gif of the intro",
    "the lighting mood is perfect now",
]

NARRATIVE = [
    "finished the act two dialogue",
    "reworked the opening scene",
    "the lore doc is updated",
    "wrote the new quest text",
    "the ending hits harder now",
    "trimmed the cutscene",
    "added barks for the npcs",
    "the codex entries are in",
    "localization is in for the dialogue",
    "i think the pacing is better now",
    "gave the villain a real motive",
    "the journal text reads cleaner now",
]

COMMUNITY = [
    "wishlist numbers are climbing",
    "the discord is buzzing today",
    "posted the new devlog",
    "scheduled the newsletter",
    "the press kit is updated",
    "a streamer just picked us up",
    "review embargo lifts friday",
    "planning the next dev stream",
    "the trailer is live",
    "our steam page got featured",
    "the community is hyped for the patch",
    "drafting the patch notes",
    "replied to the top bug reports",
]

BIZ = [
    "closed the publisher call",
    "the contract is signed",
    "budget is approved for q3",
    "platform cert is in progress",
    "the localization vendor is booked",
    "we hit the funding milestone",
    "a porting deal is on the table",
    "the festival accepted our build",
    "the investor update is sent",
    "payment cleared for the contractors",
    "the storefront deal is confirmed",
]

LINKS = [
    "https://github.com/demo-studio/engine",
    "https://store.steampowered.com/app/000000/",
    "https://www.gamedeveloper.com/design",
    "https://www.reddit.com/r/gamedev/",
    "https://itch.io/games/featured",
    "https://www.youtube.com/watch?v=demo",
    "https://demostudio.example/devlog/42",
]

# Planted contact info so the email/phone extractor has something to show.
# Addresses use the reserved .example TLD; phones use the fictional 555-01xx
# block (validates as a well-formed US number, never assigned to anyone real).
CONTACT_DROPS = [
    "ping me at ethan@demostudio.example",
    "the new build server is at 10.0.0.42",
    "email the press kit to press@demostudio.example",
    "call me at +1 415 555 0148",
    "my work email is sofia@demostudio.example",
    "reach the publisher at deals@example-publisher.example",
    "support inbox is help@demostudio.example",
    "text me at +1 628 555 0199",
    "my direct line is +1 206 555 0112",
    "studio reception is +1 312 555 0177",
    "for press inquiries email hello@demostudio.example",
    "ivan's cell is +1 646 555 0185",
]

FORWARD_SOURCES = [
    "Indie Game Dev News",
    "Game Programming Patterns",
    "Pixel Art Daily",
    "Unity Blog",
    "Godot Engine",
    "Unreal Engine",
    "Steam Updates",
    "GDC Vault",
]

# Short, excited lines that get UPPERCASED into shouts (drives ALL-CAPS %).
SHOUTS = [
    "let's gooo",
    "ship it",
    "we did it",
    "it works",
    "best day ever",
    "huge news",
    "look at this",
    "it's happening",
    "we shipped it",
    "the build is live",
    "go go go",
    "yesss",
    "incredible news",
    "we made it",
    "finally green",
]

POLL_QUESTIONS = [
    "which boss design do we ship?",
    "release friday or monday?",
    "lunch spot for the offsite?",
    "next platform: switch or playstation?",
    "keep the old tutorial or rewrite it?",
    "which key art for the store page?",
    "crunch saturday or push the date?",
    "what should we name the demo build?",
]
POLL_OPTIONS = ["option a", "option b", "option c", "let's discuss", "no strong opinion", "either works"]

FILE_NAMES = [
    "design_doc_v7.pdf",
    "build_0.9.4_win.zip",
    "patch_notes_draft.docx",
    "level_layout.fbx",
    "soundtrack_master.wav",
    "press_kit.zip",
    "milestone_report.pdf",
    "localization_strings.csv",
]
AUDIO_TRACKS = [
    ("Demo Studio OST", "main theme"),
    ("Demo Studio OST", "boss battle"),
    ("Demo Studio OST", "credits"),
    ("reference track", "for the trailer"),
]
LOCATIONS = ["the studio", "the offsite venue", "the conference hall", "the cafe downstairs"]

EMOJI_HEAVY = [
    "🔥", "💀", "😂", "😅", "🤔", "😩", "👍", "👌", "🥲", "🤡",
    "✨", "🚀", "🎮", "🎨", "🎵", "📦", "✅", "❌", "⚡", "💪",
    "🙏", "❤️", "😎", "🤯", "🥺", "👀", "😴", "🍕", "☕", "🎉",
]

STICKER_EMOJIS = [
    "🐱", "🐶", "🦊", "🐸", "🐙", "🦝", "🦄", "🐼", "🐧", "🦋",
    "💀", "🔥", "✨", "💯", "🎉", "🙃", "😎", "🤡", "🤖", "👾",
]

# 1-on-1 vocabulary — curated against the sentiment model so the arc reads.
# AFFECTION/GOOD score strongly positive, LOW strongly negative, NEUTRAL ~0.

PERSONAL_AFFECTION = [
    "you're the best",
    "you make me so happy",
    "i love you so much",
    "i love you",
    "love you to bits",
    "talking to you makes me happy",
    "glad you're in my life",
    "i appreciate you so much",
    "i feel so close to you",
    "you light up my day",
    "i adore you",
    "i'm so grateful for you",
    "you make my day better",
    "you mean everything to me",
    "you're my favorite person",
]

PERSONAL_GOOD = [
    "what a beautiful day",
    "today was amazing",
    "i feel great today",
    "i feel amazing",
    "such a lovely evening",
    "best day in ages",
    "i'm so happy right now",
    "everything is wonderful",
    "life is good right now",
    "i feel so alive",
    "i had such a great time",
    "i'm really happy lately",
    "i'm in such a good mood",
    "i'm feeling fantastic",
]

PERSONAL_NEUTRAL = [
    "doing some laundry",
    "just the usual",
    "about to head out",
    "watching some tv",
    "went to the store",
    "just got home",
    "just chilling",
    "it's an ordinary day",
]

PERSONAL_LOW = [
    "everything is falling apart",
    "i'm so down lately",
    "i'm barely holding on",
    "i can't stop crying",
    "this week broke me",
    "i'm so tired of everything",
    "i'm completely drained",
    "i feel empty inside",
    "i'm so overwhelmed and sad",
    "i'm so stressed and unhappy",
    "i'm exhausted and sad",
    "i'm miserable today",
]

PERSONAL_DAILY = [
    "made pasta tonight",
    "went to yoga",
    "bought a cozy new blanket",
    "went for a run this morning",
    "watched a movie last night",
    "took a long walk in the park",
    "got coffee with a coworker",
    "signed up for a class",
    "repainted my room",
    "adopted a kitten from the shelter",
    "visited my parents this weekend",
    "went to a concert",
    "finally booked a flight",
    "tried a new mushroom pasta recipe",
    "started a new book",
    "planted some herbs on the balcony",
]

PERSONAL_QUESTIONS = [
    "how are you?",
    "how was your day?",
    "what are you up to tonight?",
    "any plans this weekend?",
    "how's work?",
    "how's the family?",
    "how are you feeling?",
    "did you sleep ok?",
    "have you eaten?",
    "when do we get to meet up?",
    "when are you visiting?",
    "when can we call?",
    "did you watch that show?",
    "read anything good lately?",
    "how's the weather over there?",
    "miss me?",
]

PERSONAL_GREETINGS = [
    "hey",
    "hi",
    "good morning",
    "morning",
    "hey you",
    "heyy",
    "goodnight",
    "night night",
]

PERSONAL_CONTACTS = [
    "call me at +1 312 555 0173",
    "my new email is mira@example.com",
    "text me when you land at +1 917 555 0162",
    "my mom's number is +1 503 555 0144",
    "my new work email is mira.k@example.com",
    "reach me at +1 718 555 0156",
]

PERSONAL_SHOUTS = [
    "i miss you so much",
    "best day ever",
    "i can't wait to see you",
    "i'm so happy",
    "guess what",
    "i love you",
    "call me right now",
]
PERSONAL_LOCATIONS = ["the airport", "downtown", "the train station", "the cafe we love"]
PERSONAL_AUDIO = [
    ("a song that reminds me of you", ""),
    ("our song", ""),
    ("my new favorite track", ""),
]

# Pool registry — categories are referenced by name from persona mixes.

POOLS: dict[str, list[str]] = {
    "GREETINGS": GREETINGS,
    "ACKS": ACKS,
    "AGREES": AGREES,
    "DISAGREES": DISAGREES,
    "QUESTIONS": QUESTIONS,
    "MEMES": MEMES,
    "COMPLAINTS": COMPLAINTS,
    "POSITIVE": POSITIVE,
    "PLANNING": PLANNING,
    "ENGINE": ENGINE,
    "GAMEPLAY": GAMEPLAY,
    "ART": ART,
    "NARRATIVE": NARRATIVE,
    "COMMUNITY": COMMUNITY,
    "BIZ": BIZ,
    "LINKS": LINKS,
    # personal
    "P_AFFECTION": PERSONAL_AFFECTION,
    "P_GOOD": PERSONAL_GOOD,
    "P_NEUTRAL": PERSONAL_NEUTRAL,
    "P_LOW": PERSONAL_LOW,
    "P_DAILY": PERSONAL_DAILY,
    "P_QUESTIONS": PERSONAL_QUESTIONS,
    "P_GREETINGS": PERSONAL_GREETINGS,
}

# Categories whose phrases are inherently short — never stack into monologues.
_SHORT_CATS = {"ACKS", "AGREES", "DISAGREES", "GREETINGS", "MEMES", "LINKS", "P_GREETINGS"}

# What a reply most often is: a short reaction to the parent message.
REPLY_MIX = [("ACKS", 3.0), ("AGREES", 2.0), ("DISAGREES", 1.0), ("MEMES", 1.5), ("QUESTIONS", 1.0)]

# Group chat config — 7 distinct personas

# Each persona: id, name, weight (activity share), hour_center, hour_spread,
# emoji rate, len weights for [1,2,3,4] sentences, reply rate, announce flag,
# and a weighted content mix. Affinity (who they reply to) is GROUP_AFFINITY.
GROUP_USERS = [
    {
        "id": "user1001", "name": "Ethan", "weight": 0.20,
        "hour_center": 13, "hour_spread": 4.0, "emoji": 0.08,
        "len": [0.45, 0.30, 0.18, 0.07], "reply_rate": 0.34, "announce": True,
        "caps_rate": 0.004, "excl_rate": 0.08, "long_rate": 0.025, "essay_cat": "PLANNING",
        "mix": [("PLANNING", 3), ("QUESTIONS", 2.5), ("ENGINE", 1), ("AGREES", 2), ("ACKS", 1.5), ("POSITIVE", 1)],
    },
    {
        "id": "user1002", "name": "Maya", "weight": 0.15,
        "hour_center": 16, "hour_spread": 4.0, "emoji": 0.55,
        "len": [0.70, 0.22, 0.07, 0.01], "reply_rate": 0.30, "announce": False,
        "caps_rate": 0.06, "excl_rate": 0.35, "long_rate": 0.0, "essay_cat": None,
        "mix": [("ART", 3), ("MEMES", 2.5), ("POSITIVE", 2), ("ACKS", 1.5), ("GREETINGS", 1)],
    },
    {
        "id": "user1003", "name": "Kai", "weight": 0.17,
        "hour_center": 19, "hour_spread": 4.5, "emoji": 0.06,
        "len": [0.40, 0.32, 0.20, 0.08], "reply_rate": 0.42, "announce": False,
        "caps_rate": 0.012, "excl_rate": 0.06, "long_rate": 0.05, "essay_cat": "ENGINE",
        "mix": [("ENGINE", 4), ("QUESTIONS", 1.5), ("COMPLAINTS", 1.2), ("LINKS", 1), ("AGREES", 1.2)],
    },
    {
        "id": "user1004", "name": "Noah", "weight": 0.13,
        "hour_center": 23, "hour_spread": 3.5, "emoji": 0.11,
        "len": [0.48, 0.30, 0.16, 0.06], "reply_rate": 0.40, "announce": False,
        "caps_rate": 0.05, "excl_rate": 0.22, "long_rate": 0.02, "essay_cat": "GAMEPLAY",
        "mix": [("GAMEPLAY", 4), ("MEMES", 2), ("QUESTIONS", 1.5), ("COMPLAINTS", 1.2)],
    },
    {
        "id": "user1005", "name": "Liam", "weight": 0.10,
        "hour_center": 9, "hour_spread": 3.5, "emoji": 0.12,
        "len": [0.32, 0.30, 0.24, 0.14], "reply_rate": 0.30, "announce": False,
        "caps_rate": 0.01, "excl_rate": 0.10, "long_rate": 0.07, "essay_cat": "NARRATIVE",
        "mix": [("NARRATIVE", 4), ("POSITIVE", 1.5), ("QUESTIONS", 1.5), ("ACKS", 1)],
    },
    {
        "id": "user1006", "name": "Sofia", "weight": 0.15,
        "hour_center": 14, "hour_spread": 6.0, "emoji": 0.35,
        "len": [0.50, 0.30, 0.15, 0.05], "reply_rate": 0.33, "announce": True,
        "caps_rate": 0.03, "excl_rate": 0.30, "long_rate": 0.01, "essay_cat": "COMMUNITY",
        "mix": [("COMMUNITY", 3.5), ("LINKS", 1.5), ("POSITIVE", 2), ("QUESTIONS", 1.5), ("PLANNING", 1)],
    },
    {
        "id": "user1007", "name": "Ivan", "weight": 0.10,
        "hour_center": 20, "hour_spread": 4.0, "emoji": 0.05,
        "len": [0.62, 0.26, 0.10, 0.02], "reply_rate": 0.25, "announce": False,
        "caps_rate": 0.003, "excl_rate": 0.04, "long_rate": 0.0, "essay_cat": None,
        "mix": [("BIZ", 3), ("PLANNING", 1.5), ("QUESTIONS", 1.5), ("ACKS", 2), ("AGREES", 1.5)],
    },
]

# Reply affinity by speaker index -> {target index: weight}. Unlisted targets
# get a small base weight. This is what gives the network graph its clusters:
#   {Kai, Noah} engineering, {Maya, Liam} creative, Ethan/Sofia bridges.
GROUP_AFFINITY = {
    0: {1: 1.0, 2: 2.0, 3: 1.0, 4: 1.0, 5: 2.0, 6: 1.5},  # Ethan — broad
    1: {4: 3.0, 5: 2.0, 0: 1.5, 2: 0.5, 3: 0.5, 6: 0.3},  # Maya -> Liam, Sofia
    2: {3: 3.5, 0: 2.0, 5: 0.7, 6: 0.5, 1: 0.5, 4: 0.4},  # Kai -> Noah, Ethan
    3: {2: 3.5, 0: 1.5, 5: 0.6, 1: 0.5, 4: 0.4, 6: 0.3},  # Noah -> Kai, Ethan
    4: {1: 3.0, 5: 2.0, 0: 1.2, 2: 0.4, 3: 0.4, 6: 0.4},  # Liam -> Maya, Sofia
    5: {0: 2.0, 6: 2.0, 1: 1.5, 4: 1.5, 2: 1.0, 3: 1.0},  # Sofia — bridge
    6: {0: 3.0, 5: 2.5, 2: 0.6, 1: 0.4, 3: 0.4, 4: 0.4},  # Ivan -> Ethan, Sofia
}

GROUP_START = date(2024, 1, 15)
GROUP_END = date(2026, 5, 1)
GROUP_NAME = "Demo Studio · team"
GROUP_TYPE = "private_supergroup"

# 1-on-1 config

PERSONAL_ME_ID = "user2001"
PERSONAL_ME_NAME = "You"
PERSONAL_OTHER_ID = "user2002"
PERSONAL_OTHER_NAME = "Mira"

PERSONAL_START = date(2024, 10, 1)
PERSONAL_END = date(2026, 5, 1)
PERSONAL_NAME = "Demo Friend"
PERSONAL_TYPE = "personal_chat"

# Generation helpers


def _hour_weight(hour: int, center: float, spread: float) -> float:
    """Gaussian over the clock, wrapping at midnight so night owls aren't clipped."""
    diff = min(abs(hour - center), 24 - abs(hour - center))
    return math.exp(-(diff**2) / (2 * spread**2))


def _day_weight(d: date) -> float:
    """Weekdays slightly busier; summer dip, mild December dip."""
    base = 1.0 if d.weekday() < 5 else 0.65
    seasonal = 0.7 if d.month in (7, 8) else (0.85 if d.month == 12 else 1.0)
    return base * seasonal


def _weighted(rng: random.Random, choices: list[tuple]):
    items = [c[0] for c in choices]
    weights = [c[1] for c in choices]
    return rng.choices(items, weights=weights, k=1)[0]


def _len_count(rng: random.Random, weights: list[float]) -> int:
    return rng.choices([1, 2, 3, 4], weights=weights, k=1)[0]


def _maybe_emoji(rng: random.Random, prob: float) -> str:
    if rng.random() < prob:
        n = rng.choices([1, 2, 3], weights=[0.7, 0.22, 0.08])[0]
        return " " + "".join(rng.choice(EMOJI_HEAVY) for _ in range(n))
    return ""


def _join_frags(frags: list[str]) -> str:
    """Join sentence fragments, avoiding doubled punctuation after . ? or !"""
    out = frags[0]
    for frag in frags[1:]:
        out += (" " if out[-1] in ".?!" else ". ") + frag
    return out


def _compose(rng: random.Random, category: str, n_sentences: int) -> str:
    """Build a message from one category. Short categories never stack."""
    if category in _SHORT_CATS:
        n_sentences = 1
    pool = POOLS[category]
    if n_sentences == 1:
        return rng.choice(pool)
    return _join_frags(rng.sample(pool, min(n_sentences, len(pool))))


def _emphasize(rng: random.Random, text: str, excl_rate: float) -> str:
    """Occasionally turn a statement into an exclamation (drives exclamation %)."""
    if text and text[-1] not in "?!" and rng.random() < excl_rate:
        return text.rstrip(".") + "!"
    return text


def _poll(rng: random.Random) -> dict:
    opts = rng.sample(POLL_OPTIONS, 3)
    voters = [rng.randint(0, 4) for _ in opts]
    return {
        "question": rng.choice(POLL_QUESTIONS),
        "closed": True,
        "total_voters": sum(voters),
        "answers": [{"text": o, "voters": v, "chosen": False} for o, v in zip(opts, voters)],
    }


def _pick_reply_target(rng: random.Random, speaker_idx: int, recent_by_idx: dict[int, list[int]]):
    """Choose a parent message id, favouring the speaker's affinity cluster."""
    affin = GROUP_AFFINITY[speaker_idx]
    cands = [(i, ids) for i, ids in recent_by_idx.items() if i != speaker_idx and ids]
    if not cands:
        return None
    weights = [affin.get(i, 0.4) for i, _ in cands]
    target_idx = rng.choices([c[0] for c in cands], weights=weights, k=1)[0]
    return rng.choice(recent_by_idx[target_idx][-8:])


def _ts(d: date, hour: int, rng: random.Random) -> datetime:
    return datetime(d.year, d.month, d.day, hour, rng.randint(0, 59), rng.randint(0, 59))


def _base_message(msg_id: int, ts: datetime, name: str, uid: str, text: str) -> dict:
    return {
        "id": msg_id,
        "type": "message",
        "date": ts.strftime("%Y-%m-%dT%H:%M:%S"),
        # noqa: UP017 — timezone.utc kept for clarity; offset makes unixtime match the local date string
        "date_unixtime": str(int(ts.replace(tzinfo=timezone.utc).timestamp() - 3 * 3600)),  # noqa: UP017
        "from": name,
        "from_id": uid,
        "text": text,
        "text_entities": [{"type": "plain", "text": text}] if text else [],
    }


def _spike(d: date, group: bool) -> float:
    """Multiplier for special burst-activity days."""
    spikes = (
        [
            (date(2024, 6, 7), 3.0),    # demo launch
            (date(2024, 8, 21), 2.6),   # gamescom
            (date(2024, 11, 22), 4.0),  # early access release
            (date(2025, 3, 14), 2.0),   # patch 1.1
            (date(2025, 5, 9), 1.8),    # studio birthday
            (date(2025, 9, 12), 3.2),   # 1.0 release
            (date(2026, 2, 14), 2.4),   # dlc reveal
        ]
        if group
        else [
            (date(2024, 12, 31), 2.5),  # new year
            (date(2025, 2, 14), 2.2),   # valentine's
            (date(2025, 7, 4), 2.0),    # mira's birthday
            (date(2025, 10, 18), 0.2),  # drift week
            (date(2025, 11, 1), 0.15),  # silence
            (date(2025, 12, 25), 2.6),  # reconcile
        ]
    )
    for sd, mult in spikes:
        delta = abs((d - sd).days)
        if delta <= 2:
            return 1 + (mult - 1) * (1 - delta / 3)
    return 1.0


def _drift_dip(d: date, group: bool) -> float:
    """Sustained low/high activity windows (vacations, crunch, a rough patch)."""
    if group:
        if date(2024, 7, 15) <= d <= date(2024, 8, 5):  # summer vacation
            return 0.25
        if date(2025, 8, 20) <= d <= date(2025, 9, 12):  # 1.0 crunch
            return 1.7
        return 1.0
    if date(2025, 10, 5) <= d <= date(2025, 10, 25):  # cooling off
        return 0.4
    if date(2025, 10, 26) <= d <= date(2025, 11, 24):  # near-silence
        return 0.08
    return 1.0


def _personal_phase(d: date) -> str:
    if d < date(2025, 9, 25):
        return "happy"
    if d < date(2025, 11, 25):
        return "drift"
    return "rebuild"


def _personal_mix(speaker_me: bool, phase: str) -> list[tuple]:
    """Weighted content categories for the 1-on-1, shaped by mood phase.

    'You' leans on questions and daily life; 'Mira' leans warmer and longer.
    The mood phase drives the affect that the sentiment model picks up.
    """
    if phase == "happy":
        mix = [("P_AFFECTION", 3.0), ("P_GOOD", 2.5), ("P_DAILY", 2.5),
               ("P_QUESTIONS", 2.0), ("P_GREETINGS", 1.2), ("ACKS", 1.0)]
    elif phase == "drift":
        mix = [("P_LOW", 3.0), ("P_NEUTRAL", 2.5), ("P_DAILY", 1.5),
               ("ACKS", 2.0), ("P_QUESTIONS", 1.2), ("P_AFFECTION", 0.4)]
    else:  # rebuild
        mix = [("P_NEUTRAL", 2.0), ("P_GOOD", 1.8), ("P_DAILY", 2.0),
               ("P_AFFECTION", 1.5), ("P_QUESTIONS", 1.5), ("P_GREETINGS", 1.0)]

    # tilt per speaker
    bump = {}
    if speaker_me:
        bump = {"P_QUESTIONS": 1.8, "ACKS": 1.5, "P_AFFECTION": 0.7}
    else:
        bump = {"P_AFFECTION": 1.6, "P_DAILY": 1.4, "P_GOOD": 1.3, "P_LOW": 1.3}
    return [(cat, w * bump.get(cat, 1.0)) for cat, w in mix]


# Generators


def gen_group_messages() -> list[dict]:
    rng = random.Random(42)
    messages: list[dict] = []
    msg_id = 1
    total_days = (GROUP_END - GROUP_START).days
    recent_by_idx: dict[int, list[int]] = {i: [] for i in range(len(GROUP_USERS))}

    target_per_day_avg = 95
    user_weights = [u["weight"] for u in GROUP_USERS]

    for day_offset in range(total_days):
        d = GROUP_START + timedelta(days=day_offset)
        load = _day_weight(d) * _spike(d, True) * _drift_dip(d, True)
        n_today = int(target_per_day_avg * load * rng.uniform(0.7, 1.3))

        for _ in range(n_today):
            uidx = rng.choices(range(len(GROUP_USERS)), weights=user_weights, k=1)[0]
            u = GROUP_USERS[uidx]
            hour_w = [_hour_weight(h, u["hour_center"], u["hour_spread"]) for h in range(24)]
            hour = rng.choices(range(24), weights=hour_w, k=1)[0]
            ts = _ts(d, hour, rng)

            is_reply = bool(recent_by_idx) and rng.random() < u["reply_rate"]
            reply_id = _pick_reply_target(rng, uidx, recent_by_idx) if is_reply else None

            if rng.random() < u["caps_rate"]:
                # ALL-CAPS shout — short and clearly uppercase
                text = rng.choice(SHOUTS).upper() + "!"
            elif u["essay_cat"] and rng.random() < u["long_rate"]:
                # long-form write-up — fills the 300+ length bucket / "essayist"
                pool = POOLS[u["essay_cat"]]
                text = _join_frags(rng.sample(pool, min(len(pool), rng.randint(8, 12))))
            elif is_reply and reply_id is not None and rng.random() < 0.6:
                # a reply is usually a short reaction
                text = _compose(rng, _weighted(rng, REPLY_MIX), 1)
            else:
                category = _weighted(rng, u["mix"])
                text = _compose(rng, category, _len_count(rng, u["len"]))
                if u["announce"] and category in ("PLANNING", "COMMUNITY") and rng.random() < 0.3:
                    text = rng.choice(ANNOUNCEMENT_PREFIXES) + " " + text
                text = _emphasize(rng, text, u["excl_rate"])

            text += _maybe_emoji(rng, u["emoji"])

            msg = _base_message(msg_id, ts, u["name"], u["id"], text)
            if reply_id is not None:
                msg["reply_to_message_id"] = reply_id

            r = rng.random()
            if r < 0.001:  # rare planted contact info for the extractor demo
                drop = rng.choice(CONTACT_DROPS)
                msg.update(text=drop, text_entities=[{"type": "plain", "text": drop}])
            elif r < 0.031:  # 3% sticker
                msg.update(media_type="sticker", sticker_emoji=rng.choice(STICKER_EMOJIS), text="", text_entities=[])
            elif r < 0.056:  # 2.5% voice
                msg.update(media_type="voice_message", duration_seconds=rng.randint(5, 220), text="", text_entities=[])
            elif r < 0.076:  # 2% animation / GIF
                msg.update(media_type="animation", text="", text_entities=[])
            elif r < 0.088:  # 1.2% photo
                msg["media_type"] = "photo"
                if rng.random() < 0.4:
                    msg["caption"] = rng.choice(POOLS["ART"])
            elif r < 0.092:  # 0.4% poll
                msg.update(media_type="poll", poll=_poll(rng), text="", text_entities=[])
            elif r < 0.098:  # 0.6% file
                msg.update(media_type="file", file_name=rng.choice(FILE_NAMES), text="", text_entities=[])
            elif r < 0.102:  # 0.4% audio file
                performer, title = rng.choice(AUDIO_TRACKS)
                msg.update(media_type="audio_file", performer=performer, title=title, text="", text_entities=[])
            elif r < 0.106:  # 0.4% round video message
                msg.update(media_type="video_message", duration_seconds=rng.randint(5, 90), text="", text_entities=[])
            elif r < 0.1075:  # 0.15% location
                msg.update(media_type="location", text="", text_entities=[],
                           location_information={"latitude": round(rng.uniform(40, 60), 5), "longitude": round(rng.uniform(-5, 30), 5)})
                if rng.random() < 0.5:
                    msg["caption"] = rng.choice(LOCATIONS)
            elif r < 0.109:  # 0.15% shared contact
                msg.update(media_type="contact", text="", text_entities=[],
                           contact_information={"first_name": rng.choice(["Alex", "Sam", "Jordan", "Riley"]),
                                                "phone_number": f"+1 415 555 0{rng.randint(100, 199)}"})
            elif r < 0.119:  # 1% forward
                msg["forwarded_from"] = rng.choice(FORWARD_SOURCES)

            messages.append(msg)
            bucket = recent_by_idx[uidx]
            bucket.append(msg_id)
            if len(bucket) > 12:
                del bucket[:-12]
            msg_id += 1

    return messages


def gen_personal_messages() -> list[dict]:
    rng = random.Random(123)
    messages: list[dict] = []
    msg_id = 1
    total_days = (PERSONAL_END - PERSONAL_START).days
    recent_me: list[int] = []
    recent_other: list[int] = []

    target_per_day_avg = 38

    for day_offset in range(total_days):
        d = PERSONAL_START + timedelta(days=day_offset)
        load = _day_weight(d) * _spike(d, False) * _drift_dip(d, False)
        n_today = int(target_per_day_avg * load * rng.uniform(0.6, 1.4))
        phase = _personal_phase(d)

        for _ in range(n_today):
            # Mira replies a touch more during the drift phase
            is_me = rng.random() < (0.6 if phase == "drift" else 0.5)
            uid, uname = (PERSONAL_ME_ID, PERSONAL_ME_NAME) if is_me else (PERSONAL_OTHER_ID, PERSONAL_OTHER_NAME)

            hour = rng.choices(range(24), weights=[_hour_weight(h, 13 if is_me else 21, 4.5) for h in range(24)], k=1)[0]
            ts = _ts(d, hour, rng)

            # emphasis rates shift with mood: warm & loud when happy, flat in drift.
            # 'You' shouts/exclaims less than Mira.
            happy = phase == "happy"
            mood_mult = 1.0 if happy else (0.1 if phase == "drift" else 0.5)
            caps_rate = (0.012 if is_me else 0.045) * mood_mult
            excl_rate = (0.12 if is_me else 0.28) * (1.0 if happy else 0.2 if phase == "drift" else 0.6)
            long_rate = 0.0 if (is_me or phase == "drift") else 0.025

            if rng.random() < caps_rate:
                text = rng.choice(PERSONAL_SHOUTS).upper() + "!"
            elif long_rate and rng.random() < long_rate:
                # Mira's occasional heartfelt paragraph (stays positive for the arc)
                pool = (PERSONAL_GOOD + PERSONAL_AFFECTION) if happy else (PERSONAL_AFFECTION + PERSONAL_NEUTRAL)
                text = _join_frags(rng.sample(pool, min(len(pool), rng.randint(10, 14))))
            else:
                # 'You' writes shorter; Mira a bit longer
                len_w = [0.62, 0.26, 0.10, 0.02] if is_me else [0.45, 0.32, 0.17, 0.06]
                category = _weighted(rng, _personal_mix(is_me, phase))
                text = _emphasize(rng, _compose(rng, category, _len_count(rng, len_w)), excl_rate)

            emoji_rate = (0.30 if happy else 0.10 if phase == "drift" else 0.20)
            text += _maybe_emoji(rng, emoji_rate)

            msg = _base_message(msg_id, ts, uname, uid, text)

            target = recent_other if is_me else recent_me
            if target and rng.random() < 0.20:
                msg["reply_to_message_id"] = rng.choice(target[-10:])

            r = rng.random()
            if r < 0.0008:  # rare planted contact info
                drop = rng.choice(PERSONAL_CONTACTS)
                msg.update(text=drop, text_entities=[{"type": "plain", "text": drop}])
            elif r < 0.0458:  # 4.5% sticker
                msg.update(media_type="sticker", sticker_emoji=rng.choice(STICKER_EMOJIS), text="", text_entities=[])
            elif r < 0.0908:  # 4.5% voice (long-distance friends call a lot)
                msg.update(media_type="voice_message", duration_seconds=rng.randint(10, 420), text="", text_entities=[])
            elif r < 0.1158:  # 2.5% round video message
                msg.update(media_type="video_message", duration_seconds=rng.randint(5, 120), text="", text_entities=[])
            elif r < 0.1358:  # 2% animation / GIF
                msg.update(media_type="animation", text="", text_entities=[])
            elif r < 0.1538:  # 1.8% photo
                msg["media_type"] = "photo"
                if rng.random() < 0.5:
                    msg["caption"] = rng.choice(POOLS["P_DAILY"])
            elif r < 0.1618:  # 0.8% audio (songs they share)
                performer, title = rng.choice(PERSONAL_AUDIO)
                msg.update(media_type="audio_file", performer=performer, title=title, text="", text_entities=[])
            elif r < 0.1658:  # 0.4% location
                msg.update(media_type="location", text="", text_entities=[],
                           location_information={"latitude": round(rng.uniform(40, 60), 5), "longitude": round(rng.uniform(-5, 30), 5)})
                if rng.random() < 0.5:
                    msg["caption"] = rng.choice(PERSONAL_LOCATIONS)
            elif r < 0.1688:  # 0.3% file
                msg.update(media_type="file", file_name=rng.choice(["photos.zip", "recipe.pdf", "playlist.m3u", "tickets.pdf"]),
                           text="", text_entities=[])
            elif r < 0.1708:  # 0.2% shared contact
                msg.update(media_type="contact", text="", text_entities=[],
                           contact_information={"first_name": rng.choice(["Mom", "Sam", "Jess", "Leo"]),
                                                "phone_number": f"+1 312 555 0{rng.randint(100, 199)}"})

            messages.append(msg)
            (recent_me if is_me else recent_other).append(msg_id)
            for lst in (recent_me, recent_other):
                if len(lst) > 30:
                    del lst[:-30]
            msg_id += 1

    return messages


def main() -> None:
    import json

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    group_msgs = gen_group_messages()
    group_export = {"name": GROUP_NAME, "type": GROUP_TYPE, "id": 7771001, "messages": group_msgs}
    group_path = OUT_DIR / "group_demo.json"
    group_path.write_text(json.dumps(group_export, ensure_ascii=False), encoding="utf-8")
    print(f"  group    : {len(group_msgs):,} msgs → {group_path}")

    personal_msgs = gen_personal_messages()
    personal_export = {"name": PERSONAL_NAME, "type": PERSONAL_TYPE, "id": 7772001, "messages": personal_msgs}
    personal_path = OUT_DIR / "personal_demo.json"
    personal_path.write_text(json.dumps(personal_export, ensure_ascii=False), encoding="utf-8")
    print(f"  personal : {len(personal_msgs):,} msgs → {personal_path}")


if __name__ == "__main__":
    main()
