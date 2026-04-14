"""Project and block data model — mirrors lib/nodepad-format.ts."""

from __future__ import annotations

import json
import os
import random
import string
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


NODEPAD_FILE_VERSION = 1


def _gen_id() -> str:
    """Generate a short random ID matching nodepad's Math.random().toString(36).substring(2,10)."""
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=8))


@dataclass
class SubTask:
    id: str
    text: str
    is_done: bool = False
    timestamp: float = 0

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "text": self.text, "isDone": self.is_done, "timestamp": self.timestamp}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SubTask:
        return cls(id=d["id"], text=d["text"], is_done=d.get("isDone", False), timestamp=d.get("timestamp", 0))


@dataclass
class Source:
    url: str
    title: str = ""
    site_name: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"url": self.url, "title": self.title, "siteName": self.site_name}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Source:
        return cls(url=d["url"], title=d.get("title", ""), site_name=d.get("siteName", ""))


@dataclass
class TextBlock:
    id: str
    text: str
    timestamp: float
    content_type: str = "general"
    category: str | None = None
    annotation: str | None = None
    confidence: float | None = None
    sources: list[Source] = field(default_factory=list)
    influenced_by: list[str] = field(default_factory=list)
    is_unrelated: bool = False
    is_pinned: bool = False
    sub_tasks: list[SubTask] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "text": self.text,
            "timestamp": self.timestamp,
            "contentType": self.content_type,
        }
        if self.category is not None:
            d["category"] = self.category
        if self.annotation is not None:
            d["annotation"] = self.annotation
        if self.confidence is not None:
            d["confidence"] = self.confidence
        if self.sources:
            d["sources"] = [s.to_dict() for s in self.sources]
        if self.influenced_by:
            d["influencedBy"] = self.influenced_by
        if self.is_unrelated:
            d["isUnrelated"] = True
        if self.is_pinned:
            d["isPinned"] = True
        if self.sub_tasks:
            d["subTasks"] = [t.to_dict() for t in self.sub_tasks]
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TextBlock:
        return cls(
            id=d["id"],
            text=d["text"],
            timestamp=d.get("timestamp", time.time() * 1000),
            content_type=d.get("contentType", "general"),
            category=d.get("category"),
            annotation=d.get("annotation"),
            confidence=d.get("confidence"),
            sources=[Source.from_dict(s) for s in d.get("sources", [])],
            influenced_by=d.get("influencedBy", []),
            is_unrelated=d.get("isUnrelated", False),
            is_pinned=d.get("isPinned", False),
            sub_tasks=[SubTask.from_dict(t) for t in d.get("subTasks", [])],
        )

    def summary(self) -> str:
        """One-line summary for list views."""
        prefix = "\U0001f4cc " if self.is_pinned else ""
        conf = f" [{self.confidence}%]" if self.confidence is not None else ""
        cat = f" ({self.category})" if self.category else ""
        text_preview = self.text[:60] + ("..." if len(self.text) > 60 else "")
        return f"{prefix}[{self.content_type}]{cat}{conf} {text_preview}"


@dataclass
class GhostNote:
    id: str
    text: str
    category: str
    is_generating: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "text": self.text, "category": self.category, "isGenerating": False}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> GhostNote:
        return cls(id=d["id"], text=d["text"], category=d.get("category", "thesis"), is_generating=False)


@dataclass
class Project:
    id: str
    name: str
    blocks: list[TextBlock] = field(default_factory=list)
    collapsed_ids: list[str] = field(default_factory=list)
    ghost_notes: list[GhostNote] = field(default_factory=list)
    last_ghost_texts: list[str] = field(default_factory=list)
    last_ghost_block_count: int | None = None
    last_ghost_timestamp: float | None = None

    @classmethod
    def create(cls, name: str) -> Project:
        return cls(id=_gen_id(), name=name)

    def add_block(self, text: str, content_type: str = "general") -> TextBlock:
        block = TextBlock(
            id=_gen_id(),
            text=text,
            timestamp=time.time() * 1000,
            content_type=content_type,
        )
        self.blocks.append(block)
        return block

    def get_block(self, block_id: str) -> TextBlock | None:
        return next((b for b in self.blocks if b.id == block_id), None)

    def delete_block(self, block_id: str) -> bool:
        before = len(self.blocks)
        self.blocks = [b for b in self.blocks if b.id != block_id]
        return len(self.blocks) < before

    def stats(self) -> dict[str, Any]:
        from collections import Counter
        type_counts = Counter(b.content_type for b in self.blocks)
        enriched = sum(1 for b in self.blocks if b.annotation)
        pinned = sum(1 for b in self.blocks if b.is_pinned)
        return {
            "name": self.name,
            "id": self.id,
            "total_blocks": len(self.blocks),
            "enriched": enriched,
            "pinned": pinned,
            "ghost_notes": len(self.ghost_notes),
            "type_counts": dict(type_counts),
        }

    def to_nodepad(self) -> dict[str, Any]:
        """Serialise to .nodepad file format."""
        return {
            "version": NODEPAD_FILE_VERSION,
            "exportedAt": int(time.time() * 1000),
            "project": {
                "id": self.id,
                "name": self.name,
                "blocks": [b.to_dict() for b in self.blocks],
                "collapsedIds": self.collapsed_ids,
                "ghostNotes": [g.to_dict() for g in self.ghost_notes],
                "lastGhostTexts": self.last_ghost_texts or None,
                "lastGhostBlockCount": self.last_ghost_block_count,
                "lastGhostTimestamp": self.last_ghost_timestamp,
            },
        }

    def save(self, path: str | Path) -> None:
        """Save project as a .nodepad file."""
        data = self.to_nodepad()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def from_nodepad(cls, data: dict[str, Any]) -> Project:
        """Parse a .nodepad file dict into a Project."""
        if not isinstance(data, dict) or "project" not in data:
            raise ValueError("Not a valid .nodepad file — missing project key.")
        src = data["project"]
        if not isinstance(src.get("blocks"), list):
            raise ValueError("Not a valid .nodepad file — missing project.blocks array.")
        return cls(
            id=src.get("id", _gen_id()),
            name=src.get("name", "Imported Project"),
            blocks=[TextBlock.from_dict(b) for b in src["blocks"]],
            collapsed_ids=src.get("collapsedIds", []),
            ghost_notes=[GhostNote.from_dict(g) for g in src.get("ghostNotes", [])],
            last_ghost_texts=src.get("lastGhostTexts", []),
            last_ghost_block_count=src.get("lastGhostBlockCount"),
            last_ghost_timestamp=src.get("lastGhostTimestamp"),
        )

    @classmethod
    def load(cls, path: str | Path) -> Project:
        """Load a project from a .nodepad file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_nodepad(data)
