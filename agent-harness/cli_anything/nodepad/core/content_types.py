"""Content type definitions — mirrors lib/content-types.ts."""

from typing import Literal

ContentType = Literal[
    "entity", "claim", "question", "task", "idea", "reference", "quote",
    "definition", "opinion", "reflection", "narrative", "comparison",
    "thesis", "general",
]

ALL_CONTENT_TYPES: list[str] = [
    "entity", "claim", "question", "task", "idea", "reference", "quote",
    "definition", "opinion", "reflection", "narrative", "comparison",
    "thesis", "general",
]

CONTENT_TYPE_META: dict[str, dict[str, str]] = {
    "entity":     {"label": "Entity",     "emoji": "\U0001f310", "description": "People, places, and named concepts"},
    "claim":      {"label": "Claim",      "emoji": "\u26a1",     "description": "Assertions with confidence scores"},
    "question":   {"label": "Question",   "emoji": "\u2753",     "description": "Open threads and unknowns"},
    "task":       {"label": "Task",       "emoji": "\u2705",     "description": "Action items"},
    "idea":       {"label": "Idea",       "emoji": "\U0001f4a1", "description": "Raw concepts and hunches"},
    "reference":  {"label": "Reference",  "emoji": "\U0001f517", "description": "Sources and links"},
    "quote":      {"label": "Quote",      "emoji": "\U0001f4ac", "description": "Direct quotations"},
    "definition": {"label": "Definition", "emoji": "\U0001f4d6", "description": "Terminology and explanations"},
    "opinion":    {"label": "Opinion",    "emoji": "\U0001f5e3\ufe0f", "description": "Subjective takes"},
    "reflection": {"label": "Reflection", "emoji": "\U0001fa9e", "description": "Personal observations"},
    "narrative":  {"label": "Narrative",  "emoji": "\U0001f4dc", "description": "Extended accounts"},
    "comparison": {"label": "Comparison", "emoji": "\u2696\ufe0f", "description": "Contrasts and parallels"},
    "thesis":     {"label": "Thesis",     "emoji": "\U0001f52c", "description": "Synthesised conclusions"},
    "general":    {"label": "Note",       "emoji": "\U0001f4dd", "description": "Miscellaneous notes"},
}

# Research-logical ordering for export
TYPE_ORDER: list[str] = [
    "thesis", "claim", "question", "idea", "task", "entity", "definition",
    "reference", "quote", "opinion", "reflection", "narrative", "comparison", "general",
]
