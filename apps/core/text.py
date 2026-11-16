"""Language-aware text normalization shared by FAQ search and chatbot matching."""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

HAUSA_SIGNAL_WORDS = {
    "ake",
    "amsa",
    "bayanai",
    "biya",
    "biyan",
    "bukata",
    "domin",
    "fili",
    "gaggawa",
    "gwamnati",
    "haraji",
    "hanyar",
    "ina",
    "kudin",
    "lafiya",
    "makaranta",
    "manomi",
    "nema",
    "nemi",
    "rajista",
    "samu",
    "takarda",
    "takardar",
    "tallafi",
    "tambaya",
    "tuntubi",
    "yaya",
    "zan",
}

ENGLISH_SIGNAL_WORDS = {
    "apply",
    "business",
    "contact",
    "education",
    "government",
    "health",
    "help",
    "land",
    "pay",
    "permit",
    "register",
    "service",
    "tax",
    "what",
    "where",
}

STOP_WORDS = {
    # English
    "a", "about", "an", "and", "are", "can", "do", "for", "from", "get", "how",
    "i", "in", "is", "it", "me", "my", "of", "on", "please", "the", "to", "want",
    "what", "where", "with",
    # Hausa
    "ce", "da", "dan", "don", "ga", "game", "ina", "ka", "ko", "ma", "mai", "na",
    "ne", "ni", "shi", "su", "ta", "wace", "ya", "yadda", "yaya", "zan",
}

# Canonical forms cover common unaccented spellings and small expression variants.
TOKEN_ALIASES = {
    "kudin": "kudi",
    "kudi": "kudi",
    "daukar": "dauka",
    "maikata": "maaikata",
    "maaikatan": "maaikata",
    "dalibai": "dalibi",
    "manoma": "manomi",
    "filaye": "fili",
    "asibitoci": "asibiti",
    "takardu": "takarda",
    "hukumomi": "hukuma",
}


def normalize_text(value: str) -> str:
    value = (value or "").lower().translate(str.maketrans({"ƙ": "k", "ɗ": "d", "ɓ": "b"}))
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    value = value.replace("’", "").replace("‘", "").replace("'", "")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    tokens = [TOKEN_ALIASES.get(token, token) for token in value.split()]
    return " ".join(tokens)


def tokenize(value: str, *, remove_stop_words: bool = True) -> list[str]:
    tokens = normalize_text(value).split()
    if remove_stop_words:
        tokens = [token for token in tokens if len(token) > 1 and token not in STOP_WORDS]
    return tokens


def detect_language(value: str, fallback: str = "en") -> tuple[str, float]:
    """Return ``(language, confidence)`` using conservative lexical signals."""
    original = (value or "").lower()
    tokens = normalize_text(value).split()
    hausa_score = 3 if re.search(r"[ƙɗɓ]", original) else 0
    english_score = 0
    for token in tokens:
        if token in HAUSA_SIGNAL_WORDS:
            hausa_score += 1
        if token in ENGLISH_SIGNAL_WORDS:
            english_score += 1

    total = hausa_score + english_score
    if not total or hausa_score == english_score:
        return fallback, 0.5
    language = "ha" if hausa_score > english_score else "en"
    confidence = max(hausa_score, english_score) / total
    return language, round(confidence, 3)


def token_overlap(left: str, right: str) -> float:
    left_tokens, right_tokens = set(tokenize(left)), set(tokenize(right))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def join_search_values(values: Iterable[str]) -> str:
    return " ".join(normalize_text(value) for value in values if value)


SENSITIVE_PATTERNS = (
    re.compile(r"\b(?:bvn|nin)\s*(?:is|:|-)?\s*\d{10,12}\b", re.IGNORECASE),
    re.compile(r"\b(?:password|pin)\s*(?:is|:|-)\s*\S+", re.IGNORECASE),
    re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
)


def redact_sensitive_data(value: str) -> tuple[str, bool]:
    """Redact common credentials before a public chat message is persisted."""
    redacted = value
    changed = False
    for pattern in SENSITIVE_PATTERNS:
        redacted, count = pattern.subn("[REDACTED]", redacted)
        changed = changed or bool(count)
    return redacted, changed
