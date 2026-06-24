"""Russian (and English-friendly) sentiment via seara/rubert-tiny2-russian-sentiment.

Provides a `compound` score in [-1, +1] like VADER for compatibility:
    compound = P(positive) - P(negative)

The model is ~50MB, ~29M params, downloads on first use to the HuggingFace cache.
Inference is batched and runs on MPS / CUDA when available, else CPU.

This module is OPTIONAL. If `transformers` and `torch` are not installed, all
public functions return safe defaults (zeros / False) without raising. To
enable, run:
    pip install -r requirements-sentiment.txt
"""

from __future__ import annotations

import os
import re
from functools import lru_cache

# Default model is Russian-first. Override with the TLA_SENTIMENT_MODEL env var
# to score other languages — any HuggingFace
# sequence-classification model whose labels include "positive"/"negative" works,
# e.g. "cardiffnlp/twitter-xlm-roberta-base-sentiment" (multilingual) or
# "distilbert-base-uncased-finetuned-sst-2-english" (English). Set it before
# starting the server; the model is loaded once per process.
_DEFAULT_MODEL = "seara/rubert-tiny2-russian-sentiment"


def model_name() -> str:
    """Active sentiment model id (env override or the Russian default)."""
    return os.environ.get("TLA_SENTIMENT_MODEL", "").strip() or _DEFAULT_MODEL


_MAX_LEN = 128
_DEFAULT_BATCH = 32

INSTALL_HINT = (
    "pip install -r requirements-sentiment.txt   "
    "# adds ~1GB (torch + transformers) plus a 50MB model on first use"
)

# Common sarcasm/irony markers in messenger text (RU + EN).
# These don't *always* mean sarcasm — they shift probability. We use them to
# attenuate (halve) sentiment magnitude, never to flip the sign.
SARCASM_MARKERS = frozenset(
    [
        "🙃",  # upside-down face — classic irony marker
        "🤡",  # clown — dismissal / sarcasm
        "🙄",  # rolling eyes — overt sarcasm
        "😏",  # smirk — innuendo, sarcastic edge
        "🤓",  # nerd — mockery
        "🫠",  # melting — overwhelmed / "this is fine"
        "💀",  # skull — "dying" (ironic emphasis)
        "✨",  # sparkles — sarcastic emphasis when bracketing words
    ]
)

# English convention: "...statement /s" tag for sarcasm.
_S_SUFFIX_RE = re.compile(r"(?:^|\s)/s\b", re.IGNORECASE)


def has_sarcasm_marker(text: str) -> bool:
    """Heuristic: text contains a known sarcasm-/irony-marking emoji or /s tag."""
    if not isinstance(text, str) or not text:
        return False
    for m in SARCASM_MARKERS:
        if m in text:
            return True
    if _S_SUFFIX_RE.search(text):
        return True
    return False


def attenuate_sarcasm(text: str, score: float) -> tuple[float, bool]:
    """Apply the sarcasm-emoji heuristic.

    Returns (adjusted_score, was_marked). Halves the score magnitude if a
    sarcasm marker is present — never flips the sign (too aggressive given
    how often these emojis are used non-sarcastically, e.g. 💀 to mean
    "dying of laughter").
    """
    if not has_sarcasm_marker(text):
        return score, False
    if abs(score) < 0.1:
        # Already neutral; just flag it.
        return score, True
    return score * 0.5, True


def is_available() -> bool:
    """True if the optional sentiment dependencies (transformers + torch)
    can be imported. Cheap — caches via importlib internals."""
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401

        return True
    except Exception:
        return False


@lru_cache(maxsize=1)
def _load():
    """Lazy load tokenizer + model + device. Cached for the process lifetime."""
    if not is_available():
        raise RuntimeError("Sentiment dependencies not installed. " + INSTALL_HINT)
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    name = model_name()
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModelForSequenceClassification.from_pretrained(name)
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    model = model.to(device).eval()

    # Resolve the positive/negative class indices by label name. Different models
    # spell them differently ("positive", "POSITIVE", "LABEL_2"), so match on a
    # "pos"/"neg" substring rather than an exact key — keeps custom models working.
    id2label = model.config.id2label  # e.g. {0: neutral, 1: positive, 2: negative}

    def _find(substr: str) -> int | None:
        for idx, lbl in id2label.items():
            if substr in str(lbl).lower():
                return int(idx)
        return None

    pos_idx = _find("pos")
    neg_idx = _find("neg")
    if pos_idx is None or neg_idx is None:
        raise RuntimeError(
            f"Sentiment model {name!r} has labels {id2label} with no recognisable "
            "positive/negative classes. Set TLA_SENTIMENT_MODEL to a model whose "
            "labels include 'positive' and 'negative'."
        )
    return tok, model, torch, device, pos_idx, neg_idx


def score_batch(texts: list[str], batch_size: int = _DEFAULT_BATCH) -> list[float]:
    """Score a list of texts. Returns compound scores in [-1, +1].
    If the optional dependencies aren't installed, returns a list of zeros
    of the same length — callers are expected to check is_available() first
    if they need to differentiate "neutral" from "not scored"."""
    if not texts:
        return []
    if not is_available():
        return [0.0] * len(texts)
    tok, model, torch, device, pos_idx, neg_idx = _load()

    # Sanitise: replace empty strings with a single space so the tokenizer
    # doesn't choke.
    cleaned = [t if (isinstance(t, str) and t.strip()) else " " for t in texts]

    out: list[float] = []
    with torch.no_grad():
        for i in range(0, len(cleaned), batch_size):
            batch = cleaned[i : i + batch_size]
            enc = tok(
                batch,
                padding=True,
                truncation=True,
                max_length=_MAX_LEN,
                return_tensors="pt",
            ).to(device)
            logits = model(**enc).logits
            probs = torch.softmax(logits, dim=-1)
            # compound = P(positive) - P(negative)
            comp = (probs[:, pos_idx] - probs[:, neg_idx]).cpu().tolist()
            # Replace neutral-only entries with 0.0 floor (already covered, but
            # also ensure the original empty texts come out as 0.0 not random
            # tokenizer artefact).
            for orig, c in zip(batch, comp):
                if orig == " ":
                    out.append(0.0)
                else:
                    out.append(float(c))
    return out
