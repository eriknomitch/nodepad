"""Unit tests for cli-anything-nodepad core modules."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from cli_anything.nodepad.core.content_types import ALL_CONTENT_TYPES, CONTENT_TYPE_META, TYPE_ORDER
from cli_anything.nodepad.core.detect import detect_content_type
from cli_anything.nodepad.core.project import Project, TextBlock, GhostNote, SubTask, Source
from cli_anything.nodepad.core.export import export_to_markdown
from cli_anything.nodepad.utils.config import load_config, save_config, CONFIG_FILE
from cli_anything.nodepad.utils.output import set_json_mode, is_json_mode


# ── Content Type Detection ────────────────────────────────────────────────────

class TestDetectContentType:
    def test_quote(self):
        assert detect_content_type('"To be or not to be"') == "quote"
        assert detect_content_type("\u201cHello world\u201d") == "quote"

    def test_task(self):
        assert detect_content_type("[ ] Buy groceries") == "task"
        assert detect_content_type("[x] Done thing") == "task"
        assert detect_content_type("TODO fix the bug") == "task"
        assert detect_content_type("Buy milk and eggs") == "task"

    def test_question(self):
        assert detect_content_type("What is the meaning of life?") == "question"
        assert detect_content_type("?unclear") == "question"

    def test_definition(self):
        assert detect_content_type("Entropy is defined as the measure of disorder") == "definition"
        assert detect_content_type("Photosynthesis refers to the process of converting light") == "definition"

    def test_comparison(self):
        assert detect_content_type("React vs Vue for frontend development") == "comparison"
        assert detect_content_type("The difference between TCP and UDP") == "comparison"

    def test_reference(self):
        assert detect_content_type("https://example.com/article") == "reference"

    def test_idea(self):
        # "What if...?" ends with ? so matches question first — matches the TS behavior
        assert detect_content_type("What if we used a graph database instead") == "idea"
        assert detect_content_type("Imagine a world without passwords") == "idea"

    def test_reflection(self):
        assert detect_content_type("Looking back, the decision was clearly premature") == "reflection"
        assert detect_content_type("I remember when we first started this project") == "reflection"

    def test_opinion(self):
        assert detect_content_type("I think TypeScript is better than JavaScript") == "opinion"
        assert detect_content_type("IMO the architecture needs a complete overhaul") == "opinion"

    def test_entity(self):
        assert detect_content_type("Albert Einstein") == "entity"
        assert detect_content_type("Quantum Computing") == "entity"

    def test_claim(self):
        assert detect_content_type("The earth revolves around the sun") == "claim"

    def test_narrative(self):
        long_text = " ".join(["word"] * 30)
        assert detect_content_type(long_text) == "narrative"

    def test_general_fallback(self):
        # Edge case: 1-3 words with period -> falls through entity check
        assert detect_content_type("Ok.") in ALL_CONTENT_TYPES


# ── Project Model ─────────────────────────────────────────────────────────────

class TestProject:
    def test_create(self):
        p = Project.create("Test Research")
        assert p.name == "Test Research"
        assert len(p.id) == 8
        assert p.blocks == []

    def test_add_block(self):
        p = Project.create("Test")
        b = p.add_block("Hello world", "claim")
        assert len(p.blocks) == 1
        assert b.text == "Hello world"
        assert b.content_type == "claim"
        assert b.id is not None

    def test_get_block(self):
        p = Project.create("Test")
        b = p.add_block("Note 1")
        found = p.get_block(b.id)
        assert found is b
        assert p.get_block("nonexistent") is None

    def test_delete_block(self):
        p = Project.create("Test")
        b = p.add_block("To delete")
        assert p.delete_block(b.id) is True
        assert len(p.blocks) == 0
        assert p.delete_block("nope") is False

    def test_stats(self):
        p = Project.create("Stats Test")
        p.add_block("Question?", "question")
        p.add_block("A claim", "claim")
        b = p.add_block("Pinned", "entity")
        b.is_pinned = True
        b.annotation = "Enriched"
        stats = p.stats()
        assert stats["total_blocks"] == 3
        assert stats["pinned"] == 1
        assert stats["enriched"] == 1
        assert stats["type_counts"]["question"] == 1

    def test_save_load_roundtrip(self):
        p = Project.create("Roundtrip")
        b = p.add_block("Test note", "claim")
        b.annotation = "AI says this"
        b.confidence = 85
        b.category = "science"
        b.is_pinned = True

        gn = GhostNote(id="g1", text="A synthesis", category="bridge")
        p.ghost_notes.append(gn)

        with tempfile.NamedTemporaryFile(suffix=".nodepad", delete=False, mode="w") as f:
            path = f.name
        try:
            p.save(path)
            loaded = Project.load(path)
            assert loaded.name == "Roundtrip"
            assert len(loaded.blocks) == 1
            assert loaded.blocks[0].text == "Test note"
            assert loaded.blocks[0].annotation == "AI says this"
            assert loaded.blocks[0].confidence == 85
            assert loaded.blocks[0].is_pinned is True
            assert len(loaded.ghost_notes) == 1
            assert loaded.ghost_notes[0].text == "A synthesis"
        finally:
            os.unlink(path)


# ── TextBlock Serialisation ───────────────────────────────────────────────────

class TestTextBlock:
    def test_to_dict_from_dict(self):
        b = TextBlock(
            id="abc123",
            text="Hello",
            timestamp=1700000000000,
            content_type="claim",
            category="science",
            annotation="Interesting",
            confidence=75,
            sources=[Source(url="https://example.com", title="Example", site_name="example.com")],
            influenced_by=["xyz789"],
            is_pinned=True,
            sub_tasks=[SubTask(id="s1", text="Do thing", is_done=False, timestamp=1700000000000)],
        )
        d = b.to_dict()
        assert d["id"] == "abc123"
        assert d["contentType"] == "claim"
        assert d["isPinned"] is True
        assert len(d["sources"]) == 1
        assert d["sources"][0]["url"] == "https://example.com"

        restored = TextBlock.from_dict(d)
        assert restored.id == "abc123"
        assert restored.content_type == "claim"
        assert restored.is_pinned is True
        assert len(restored.sources) == 1

    def test_summary(self):
        b = TextBlock(id="x", text="A short note", timestamp=0, content_type="claim")
        s = b.summary()
        assert "[claim]" in s
        assert "A short note" in s

    def test_optional_fields_omitted(self):
        b = TextBlock(id="x", text="Minimal", timestamp=0)
        d = b.to_dict()
        assert "category" not in d
        assert "annotation" not in d
        assert "confidence" not in d
        assert "sources" not in d
        assert "isPinned" not in d


# ── GhostNote ────────────────────────────────────────────────────────────────

class TestGhostNote:
    def test_roundtrip(self):
        g = GhostNote(id="g1", text="A thesis", category="bridge")
        d = g.to_dict()
        assert d["isGenerating"] is False
        restored = GhostNote.from_dict(d)
        assert restored.text == "A thesis"
        assert restored.category == "bridge"


# ── Export ────────────────────────────────────────────────────────────────────

class TestExport:
    def test_empty_project(self):
        p = Project.create("Empty")
        md = export_to_markdown(p)
        assert "No nodes yet" in md

    def test_markdown_structure(self):
        p = Project.create("Research")
        p.add_block("What is consciousness?", "question")
        b = p.add_block("The brain processes information", "claim")
        b.category = "neuroscience"
        b.confidence = 80
        b.annotation = "Well-established in cognitive science"
        p.add_block("Buy lab equipment", "task")

        md = export_to_markdown(p)
        assert "---" in md  # YAML front matter
        assert "Research" in md
        assert "## Overview" in md
        assert "## Contents" in md
        assert "Question" in md
        assert "Claim" in md
        assert "Task" in md
        assert "neuroscience" in md

    def test_claims_table(self):
        p = Project.create("Claims")
        b = p.add_block("Earth is round", "claim")
        b.category = "geography"
        b.confidence = 99
        b.annotation = "Scientific consensus"
        md = export_to_markdown(p)
        assert "| Claim |" in md
        assert "Earth is round" in md

    def test_pinned_section(self):
        p = Project.create("Pinned")
        b = p.add_block("Important note", "entity")
        b.is_pinned = True
        md = export_to_markdown(p)
        assert "Pinned" in md


# ── Config ────────────────────────────────────────────────────────────────────

class TestConfig:
    def test_load_defaults(self):
        cfg = load_config()
        assert "provider" in cfg
        assert "model_id" in cfg

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("NODEPAD_API_KEY", "test-key-123")
        monkeypatch.setenv("NODEPAD_PROVIDER", "openai")
        cfg = load_config()
        assert cfg["api_key"] == "test-key-123"
        assert cfg["provider"] == "openai"


# ── Output ────────────────────────────────────────────────────────────────────

class TestOutput:
    def test_json_mode_toggle(self):
        set_json_mode(True)
        assert is_json_mode() is True
        set_json_mode(False)
        assert is_json_mode() is False


# ── .nodepad Format ───────────────────────────────────────────────────────────

class TestNodepadFormat:
    def test_to_nodepad_structure(self):
        p = Project.create("Format Test")
        p.add_block("Note 1", "claim")
        data = p.to_nodepad()
        assert data["version"] == 1
        assert "exportedAt" in data
        assert data["project"]["name"] == "Format Test"
        assert len(data["project"]["blocks"]) == 1

    def test_from_nodepad_invalid(self):
        with pytest.raises(ValueError, match="missing project key"):
            Project.from_nodepad({"foo": "bar"})

    def test_from_nodepad_missing_blocks(self):
        with pytest.raises(ValueError, match="missing project.blocks"):
            Project.from_nodepad({"project": {"name": "Bad"}})

    def test_full_roundtrip_json(self):
        p = Project.create("JSON RT")
        b = p.add_block("Deep thought", "idea")
        b.category = "philosophy"
        b.annotation = "Profound"
        data = p.to_nodepad()
        raw = json.dumps(data)
        restored = Project.from_nodepad(json.loads(raw))
        assert restored.blocks[0].text == "Deep thought"
        assert restored.blocks[0].category == "philosophy"
