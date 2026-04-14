"""End-to-end tests for cli-anything-nodepad."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from cli_anything.nodepad.core.project import Project, TextBlock
from cli_anything.nodepad.core.detect import detect_content_type
from cli_anything.nodepad.core.export import export_to_markdown


# ── Full Workflow E2E ─────────────────────────────────────────────────────────

class TestFullWorkflow:
    """Test a complete research session workflow without AI calls."""

    def test_create_populate_export(self, tmp_path):
        """Create project, add blocks, detect types, export markdown and .nodepad."""
        # Create project
        project = Project.create("E2E Research")

        # Add diverse notes
        notes = [
            "Albert Einstein",
            "E=mc^2 describes mass-energy equivalence",
            "What is dark matter composed of?",
            "TODO review the quantum mechanics paper",
            "What if gravity is an emergent phenomenon",
            "https://arxiv.org/abs/2301.00001",
            '"The only source of knowledge is experience" - Einstein',
            "Entropy is defined as the measure of disorder in a system",
            "I think quantum computing will revolutionize cryptography",
            "Looking back, the Copenhagen interpretation seems incomplete",
        ]

        for note in notes:
            ct = detect_content_type(note)
            project.add_block(note, ct)

        assert len(project.blocks) == 10

        # Verify type detection
        types = [b.content_type for b in project.blocks]
        assert "entity" in types
        assert "claim" in types
        assert "question" in types
        assert "task" in types
        assert "idea" in types
        assert "reference" in types
        assert "quote" in types
        assert "definition" in types
        assert "opinion" in types
        assert "reflection" in types

        # Export markdown
        md = export_to_markdown(project)
        assert "E2E Research" in md
        assert "10 nodes" in md
        assert "## Overview" in md

        md_path = tmp_path / "export.md"
        md_path.write_text(md, encoding="utf-8")
        assert md_path.exists()
        assert md_path.stat().st_size > 100

        # Export .nodepad
        np_path = tmp_path / "research.nodepad"
        project.save(str(np_path))
        assert np_path.exists()

        # Verify .nodepad structure
        with open(np_path) as f:
            data = json.load(f)
        assert data["version"] == 1
        assert len(data["project"]["blocks"]) == 10

    def test_import_export_roundtrip(self, tmp_path):
        """Save a project, reload it, verify all data survives."""
        project = Project.create("Roundtrip Test")

        b1 = project.add_block("A claim about the world", "claim")
        b1.category = "geography"
        b1.annotation = "Interesting perspective"
        b1.confidence = 72

        b2 = project.add_block("Follow-up question?", "question")
        b2.influenced_by = [b1.id]

        b3 = project.add_block("Pinned note", "entity")
        b3.is_pinned = True

        path = tmp_path / "roundtrip.nodepad"
        project.save(str(path))

        loaded = Project.load(str(path))
        assert loaded.name == "Roundtrip Test"
        assert len(loaded.blocks) == 3

        lb1 = loaded.get_block(b1.id)
        assert lb1 is not None
        assert lb1.category == "geography"
        assert lb1.annotation == "Interesting perspective"
        assert lb1.confidence == 72

        lb2 = loaded.get_block(b2.id)
        assert lb2 is not None
        assert lb2.influenced_by == [b1.id]

        lb3 = loaded.get_block(b3.id)
        assert lb3 is not None
        assert lb3.is_pinned is True

    def test_project_stats_accuracy(self):
        """Verify stats reflect actual project state."""
        p = Project.create("Stats")
        for i in range(5):
            b = p.add_block(f"Claim number {i}", "claim")
            b.annotation = f"Annotation {i}"
            b.category = "test"
        for i in range(3):
            p.add_block(f"Question {i}?", "question")

        b = p.add_block("Pinned entity", "entity")
        b.is_pinned = True

        stats = p.stats()
        assert stats["total_blocks"] == 9
        assert stats["enriched"] == 5
        assert stats["pinned"] == 1
        assert stats["type_counts"]["claim"] == 5
        assert stats["type_counts"]["question"] == 3
        assert stats["type_counts"]["entity"] == 1


# ── CLI Subprocess Tests ──────────────────────────────────────────────────────

class TestCLISubprocess:
    """Test the installed CLI via subprocess."""

    @staticmethod
    def _resolve_cli(name: str) -> list[str]:
        """Resolve CLI command — use installed binary if available, else python -m."""
        if os.environ.get("CLI_ANYTHING_FORCE_INSTALLED"):
            return [name]
        result = subprocess.run(["which", name], capture_output=True, text=True)
        if result.returncode == 0:
            return [name]
        return [sys.executable, "-m", "cli_anything.nodepad"]

    def test_help(self):
        cmd = self._resolve_cli("cli-anything-nodepad")
        result = subprocess.run(cmd + ["--help"], capture_output=True, text=True, timeout=30)
        assert result.returncode == 0
        assert "nodepad CLI" in result.stdout

    def test_info_types(self):
        cmd = self._resolve_cli("cli-anything-nodepad")
        result = subprocess.run(cmd + ["info", "types"], capture_output=True, text=True, timeout=30)
        assert result.returncode == 0
        assert "Entity" in result.stdout
        assert "Claim" in result.stdout

    def test_info_types_json(self):
        cmd = self._resolve_cli("cli-anything-nodepad")
        result = subprocess.run(cmd + ["--json", "info", "types"], capture_output=True, text=True, timeout=30)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "entity" in data
        assert "claim" in data

    def test_info_detect(self):
        cmd = self._resolve_cli("cli-anything-nodepad")
        result = subprocess.run(
            cmd + ["info", "detect", "What is the meaning of life?"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "Question" in result.stdout or "question" in result.stdout

    def test_project_create_and_list(self, tmp_path):
        cmd = self._resolve_cli("cli-anything-nodepad")

        # Create
        out_file = str(tmp_path / "test.nodepad")
        result = subprocess.run(
            cmd + ["project", "create", "CLI Test", "--output", out_file],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert Path(out_file).exists()

        # List
        result = subprocess.run(
            cmd + ["project", "list", str(tmp_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "CLI Test" in result.stdout

    def test_block_add_and_list(self, tmp_path):
        cmd = self._resolve_cli("cli-anything-nodepad")
        out_file = str(tmp_path / "blocks.nodepad")

        # Create project
        subprocess.run(
            cmd + ["project", "create", "Block Test", "--output", out_file],
            capture_output=True, text=True, timeout=30,
        )

        # Add block
        result = subprocess.run(
            cmd + ["-p", out_file, "block", "add", "Testing CLI blocks"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0

        # List blocks
        result = subprocess.run(
            cmd + ["-p", out_file, "block", "list"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "Testing CLI blocks" in result.stdout

    def test_export_markdown(self, tmp_path):
        cmd = self._resolve_cli("cli-anything-nodepad")
        np_file = str(tmp_path / "export.nodepad")
        md_file = str(tmp_path / "export.md")

        # Create and populate
        subprocess.run(cmd + ["project", "create", "Export Test", "--output", np_file],
                       capture_output=True, text=True, timeout=30)
        subprocess.run(cmd + ["-p", np_file, "block", "add", "A test claim"],
                       capture_output=True, text=True, timeout=30)

        # Export markdown
        result = subprocess.run(
            cmd + ["-p", np_file, "export", "markdown", "--output", md_file],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert Path(md_file).exists()
        content = Path(md_file).read_text()
        assert "Export Test" in content

    def test_config_show(self):
        cmd = self._resolve_cli("cli-anything-nodepad")
        result = subprocess.run(cmd + ["config", "show"], capture_output=True, text=True, timeout=30)
        assert result.returncode == 0
        assert "Provider" in result.stdout
