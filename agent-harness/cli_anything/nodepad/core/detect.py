"""Heuristic content type detection — mirrors lib/detect-content-type.ts."""

import re


URL_REGEX = re.compile(r"https?://\S+", re.IGNORECASE)


def detect_content_type(text: str) -> str:
    """Detect the content type of a note using heuristic rules."""
    trimmed = text.strip()
    lower = trimmed.lower()

    # Quote: starts with quotation marks
    if re.match(r'^["\'\u201c\u201d\u2018\u2019\u00ab\u2039]', trimmed):
        return "quote"

    # Task: checkbox syntax, TODO/FIXME, or action verbs
    if re.match(r"^\[[\sx]?\]", trimmed, re.IGNORECASE) or re.match(
        r"^(todo|fixme|hack|buy|call|send|finish|complete|remind|need to)\b",
        trimmed,
        re.IGNORECASE,
    ):
        return "task"

    # Question: starts with ? or ends with ? within first sentence
    if trimmed.startswith("?") or re.match(r"^[^.!]{3,}\?", trimmed):
        return "question"

    # Definition: "is defined as", "means", "refers to"
    if re.search(r"\b(is defined as|means|refers to|is the)\b", lower):
        return "definition"

    # Comparison: "vs", "compared to", "versus", etc.
    if re.search(
        r"\b(vs\.?|versus|compared to|on the other hand|differs from|difference between)\b",
        lower,
    ):
        return "comparison"

    # Reference: contains a URL
    if URL_REGEX.search(trimmed):
        return "reference"

    # Idea: starts with "what if", "could we", "imagine", "how about"
    if re.match(r"^(what if|could we|imagine|how about|maybe we)\b", trimmed, re.IGNORECASE):
        return "idea"

    # Reflection: reflective patterns
    if re.search(
        r"\b(i remember|looking back|in retrospect|upon reflection|thinking about it)\b",
        lower,
    ):
        return "reflection"

    # Opinion: opinion markers
    if re.search(r"\b(i think|i feel|i believe|imo|imho|in my opinion|personally)\b", lower):
        return "opinion"

    # Entity: short, no verb-like structure
    word_count = len(trimmed.split())
    if word_count <= 3 and "." not in trimmed and "!" not in trimmed:
        return "entity"

    # Claim: assertive statements (4-25 words)
    if 4 <= word_count <= 25 and not trimmed.endswith("?"):
        return "claim"

    # Narrative: longer text blocks
    if word_count > 25:
        return "narrative"

    return "general"
