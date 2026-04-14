"""nodepad CLI — Click-based CLI with REPL mode for the nodepad spatial research tool."""

from __future__ import annotations

import cmd
import json
import os
import shlex
import sys
import time
from pathlib import Path
from typing import Any

import click

from cli_anything.nodepad.core.project import Project, TextBlock, GhostNote
from cli_anything.nodepad.core.detect import detect_content_type
from cli_anything.nodepad.core.content_types import ALL_CONTENT_TYPES, CONTENT_TYPE_META, TYPE_ORDER
from cli_anything.nodepad.core.export import export_to_markdown
from cli_anything.nodepad.core.enrich import enrich_block
from cli_anything.nodepad.core.ghost import generate_ghost
from cli_anything.nodepad.utils.config import (
    load_config, save_config, load_ai_config, ensure_config_dir, CONFIG_FILE,
)
from cli_anything.nodepad.utils.output import set_json_mode, is_json_mode, output, error, success


# ── State ─────────────────────────────────────────────────────────────────────

_current_project: Project | None = None
_project_path: str | None = None


def _ensure_project() -> Project:
    if _current_project is None:
        error("No project loaded. Use 'project open <file>' or 'project create <name>' first.")
    return _current_project


def _save_project() -> None:
    if _current_project and _project_path:
        _current_project.save(_project_path)


# ── CLI Root ──────────────────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.option("--json", "json_mode", is_flag=True, help="Output in JSON format for agent consumption.")
@click.option("--project", "-p", "project_file", type=click.Path(), help="Open a .nodepad project file.")
@click.pass_context
def cli(ctx: click.Context, json_mode: bool, project_file: str | None) -> None:
    """nodepad CLI — spatial AI research tool for the terminal.

    Run without a subcommand to enter REPL mode.
    """
    set_json_mode(json_mode)

    if project_file:
        _open_project(project_file)

    if ctx.invoked_subcommand is None:
        repl = NodepadREPL()
        repl.cmdloop()


# ── Project Commands ──────────────────────────────────────────────────────────

@cli.group()
def project():
    """Manage nodepad projects."""
    pass


@project.command("create")
@click.argument("name")
@click.option("--output", "-o", "out_path", type=click.Path(), help="Output file path (default: <name>.nodepad)")
def project_create(name: str, out_path: str | None) -> None:
    """Create a new empty project."""
    global _current_project, _project_path
    _current_project = Project.create(name)
    _project_path = out_path or f"{name.lower().replace(' ', '-')}.nodepad"
    _save_project()
    success(f"Created project '{name}' -> {_project_path}")


@project.command("open")
@click.argument("file", type=click.Path(exists=True))
def project_open_cmd(file: str) -> None:
    """Open an existing .nodepad project file."""
    _open_project(file)
    proj = _ensure_project()
    output(proj.stats(), human=f"Opened '{proj.name}' ({len(proj.blocks)} blocks)")


def _open_project(path: str) -> None:
    global _current_project, _project_path
    _current_project = Project.load(path)
    _project_path = path


@project.command("info")
def project_info() -> None:
    """Show current project statistics."""
    proj = _ensure_project()
    stats = proj.stats()
    if is_json_mode():
        output(stats)
    else:
        print(f"  Project: {stats['name']}")
        print(f"  ID:      {stats['id']}")
        print(f"  Blocks:  {stats['total_blocks']} ({stats['enriched']} enriched, {stats['pinned']} pinned)")
        print(f"  Ghosts:  {stats['ghost_notes']}")
        if stats["type_counts"]:
            print("  Types:")
            for t in TYPE_ORDER:
                count = stats["type_counts"].get(t, 0)
                if count:
                    meta = CONTENT_TYPE_META.get(t, {})
                    print(f"    {meta.get('emoji', '')} {meta.get('label', t)}: {count}")


@project.command("list")
@click.argument("directory", type=click.Path(exists=True), default=".")
def project_list(directory: str) -> None:
    """List .nodepad files in a directory."""
    files = sorted(Path(directory).glob("*.nodepad"))
    if not files:
        output({"files": []}, human="No .nodepad files found.")
        return
    results = []
    for f in files:
        try:
            p = Project.load(f)
            results.append({"file": str(f), "name": p.name, "blocks": len(p.blocks)})
        except Exception:
            results.append({"file": str(f), "name": "?", "blocks": 0})
    if is_json_mode():
        output(results)
    else:
        for r in results:
            print(f"  {r['file']}: {r['name']} ({r['blocks']} blocks)")


# ── Block Commands ────────────────────────────────────────────────────────────

@cli.group()
def block():
    """Manage blocks (notes) in the current project."""
    pass


@block.command("add")
@click.argument("text")
@click.option("--type", "-t", "content_type", type=click.Choice(ALL_CONTENT_TYPES), help="Force content type.")
@click.option("--enrich/--no-enrich", default=False, help="Run AI enrichment after adding.")
def block_add(text: str, content_type: str | None, enrich: bool) -> None:
    """Add a new block to the project."""
    proj = _ensure_project()
    detected = content_type or detect_content_type(text)
    block = proj.add_block(text, detected)

    if enrich:
        try:
            ctx = [{"text": b.text, "category": b.category or ""} for b in proj.blocks[:-1][-15:]]
            result = enrich_block(text, context=ctx, forced_type=content_type)
            block.content_type = result.get("contentType", block.content_type)
            block.category = result.get("category")
            block.annotation = result.get("annotation")
            block.confidence = result.get("confidence")
            block.is_unrelated = result.get("isUnrelated", False)
            if result.get("sources"):
                from cli_anything.nodepad.core.project import Source
                block.sources = [Source(**s) for s in result["sources"]]
            # Map influencedByIndices to block IDs
            indices = result.get("influencedByIndices", [])
            context_blocks = proj.blocks[:-1][-15:]
            block.influenced_by = [context_blocks[i].id for i in indices if 0 <= i < len(context_blocks)]
        except Exception as e:
            click.echo(f"  Enrichment failed: {e}", err=True)

    _save_project()
    if is_json_mode():
        output(block.to_dict())
    else:
        success(f"Added block {block.id}: [{detected}] {text[:50]}")


@block.command("list")
@click.option("--type", "-t", "content_type", type=click.Choice(ALL_CONTENT_TYPES), help="Filter by type.")
@click.option("--pinned", is_flag=True, help="Show only pinned blocks.")
def block_list(content_type: str | None, pinned: bool) -> None:
    """List all blocks in the project."""
    proj = _ensure_project()
    blocks = proj.blocks
    if content_type:
        blocks = [b for b in blocks if b.content_type == content_type]
    if pinned:
        blocks = [b for b in blocks if b.is_pinned]

    if is_json_mode():
        output([b.to_dict() for b in blocks])
    else:
        if not blocks:
            print("  No blocks found.")
            return
        for b in blocks:
            print(f"  {b.id}: {b.summary()}")


@block.command("show")
@click.argument("block_id")
def block_show(block_id: str) -> None:
    """Show detailed info for a block."""
    proj = _ensure_project()
    b = proj.get_block(block_id)
    if not b:
        error(f"Block '{block_id}' not found.")
    if is_json_mode():
        output(b.to_dict())
    else:
        print(f"  ID:         {b.id}")
        print(f"  Type:       {b.content_type}")
        print(f"  Text:       {b.text}")
        if b.category:
            print(f"  Category:   {b.category}")
        if b.annotation:
            print(f"  Annotation: {b.annotation}")
        if b.confidence is not None:
            print(f"  Confidence: {b.confidence}%")
        if b.is_pinned:
            print(f"  Pinned:     yes")
        if b.sources:
            print(f"  Sources:")
            for s in b.sources:
                print(f"    - {s.title or s.url} ({s.site_name})")
        if b.influenced_by:
            print(f"  Influenced by: {', '.join(b.influenced_by)}")
        if b.sub_tasks:
            print(f"  Sub-tasks:")
            for t in b.sub_tasks:
                check = "x" if t.is_done else " "
                print(f"    [{check}] {t.text}")


@block.command("edit")
@click.argument("block_id")
@click.argument("text")
def block_edit(block_id: str, text: str) -> None:
    """Edit a block's text."""
    proj = _ensure_project()
    b = proj.get_block(block_id)
    if not b:
        error(f"Block '{block_id}' not found.")
    b.text = text
    b.content_type = detect_content_type(text)
    _save_project()
    success(f"Updated block {block_id}")


@block.command("delete")
@click.argument("block_id")
def block_delete(block_id: str) -> None:
    """Delete a block."""
    proj = _ensure_project()
    if proj.delete_block(block_id):
        _save_project()
        success(f"Deleted block {block_id}")
    else:
        error(f"Block '{block_id}' not found.")


@block.command("pin")
@click.argument("block_id")
def block_pin(block_id: str) -> None:
    """Toggle pin state for a block."""
    proj = _ensure_project()
    b = proj.get_block(block_id)
    if not b:
        error(f"Block '{block_id}' not found.")
    b.is_pinned = not b.is_pinned
    _save_project()
    success(f"Block {block_id} {'pinned' if b.is_pinned else 'unpinned'}")


# ── Enrich Commands ───────────────────────────────────────────────────────────

@cli.group()
def enrich():
    """Run AI enrichment on blocks."""
    pass


@enrich.command("block")
@click.argument("block_id")
@click.option("--type", "-t", "forced_type", type=click.Choice(ALL_CONTENT_TYPES), help="Force content type.")
def enrich_single(block_id: str, forced_type: str | None) -> None:
    """Enrich a single block with AI annotation."""
    proj = _ensure_project()
    b = proj.get_block(block_id)
    if not b:
        error(f"Block '{block_id}' not found.")

    ctx = [{"text": bl.text, "category": bl.category or ""} for bl in proj.blocks if bl.id != block_id][-15:]

    try:
        result = enrich_block(b.text, context=ctx, forced_type=forced_type, category=b.category)
    except Exception as e:
        error(f"Enrichment failed: {e}")

    b.content_type = result.get("contentType", b.content_type)
    b.category = result.get("category")
    b.annotation = result.get("annotation")
    b.confidence = result.get("confidence")
    b.is_unrelated = result.get("isUnrelated", False)

    if result.get("sources"):
        from cli_anything.nodepad.core.project import Source
        b.sources = [Source(**s) for s in result["sources"]]

    indices = result.get("influencedByIndices", [])
    context_blocks = [bl for bl in proj.blocks if bl.id != block_id][-15:]
    b.influenced_by = [context_blocks[i].id for i in indices if 0 <= i < len(context_blocks)]

    _save_project()
    if is_json_mode():
        output(result)
    else:
        print(f"  Type:       {b.content_type}")
        print(f"  Category:   {b.category}")
        print(f"  Annotation: {b.annotation}")
        if b.confidence is not None:
            print(f"  Confidence: {b.confidence}%")


@enrich.command("all")
@click.option("--force", is_flag=True, help="Re-enrich already enriched blocks.")
def enrich_all(force: bool) -> None:
    """Enrich all blocks in the project."""
    proj = _ensure_project()
    targets = proj.blocks if force else [b for b in proj.blocks if not b.annotation]
    if not targets:
        success("All blocks already enriched.")
        return

    total = len(targets)
    for i, b in enumerate(targets, 1):
        if not is_json_mode():
            click.echo(f"  [{i}/{total}] Enriching: {b.text[:40]}...")

        ctx = [{"text": bl.text, "category": bl.category or ""} for bl in proj.blocks if bl.id != b.id][-15:]
        try:
            result = enrich_block(b.text, context=ctx)
            b.content_type = result.get("contentType", b.content_type)
            b.category = result.get("category")
            b.annotation = result.get("annotation")
            b.confidence = result.get("confidence")
            b.is_unrelated = result.get("isUnrelated", False)
        except Exception as e:
            if not is_json_mode():
                click.echo(f"    Failed: {e}", err=True)

    _save_project()
    success(f"Enriched {total} blocks.")


# ── Ghost Commands ────────────────────────────────────────────────────────────

@cli.group()
def ghost():
    """Generate synthesis (ghost) notes."""
    pass


@ghost.command("generate")
@click.option("--count", "-n", default=1, help="Number of ghost notes to generate.")
def ghost_generate(count: int) -> None:
    """Generate synthesis insights from the current project."""
    proj = _ensure_project()
    enriched = [b for b in proj.blocks if b.annotation and b.category]
    if len(enriched) < 5:
        error(f"Need at least 5 enriched blocks (have {len(enriched)}). Run 'enrich all' first.")

    categories = list({b.category for b in enriched if b.category})
    if len(categories) < 2:
        error(f"Need at least 2 categories (have {len(categories)}). Add more diverse notes.")

    generated = []
    for i in range(count):
        # Build recency-biased, category-diverse context (max 10)
        ctx = [{"text": b.text, "category": b.category or ""} for b in enriched[-10:]]
        previous = proj.last_ghost_texts or []

        try:
            result = generate_ghost(ctx, previous_syntheses=previous)
        except Exception as e:
            error(f"Ghost generation failed: {e}")

        from cli_anything.nodepad.core.project import GhostNote, _gen_id
        gn = GhostNote(id=_gen_id(), text=result["text"], category=result["category"])
        proj.ghost_notes.append(gn)
        proj.last_ghost_texts = (proj.last_ghost_texts or []) + [result["text"]]
        generated.append(gn)

    _save_project()
    if is_json_mode():
        output([g.to_dict() for g in generated])
    else:
        for g in generated:
            print(f"  [{g.category}] {g.text}")


@ghost.command("list")
def ghost_list() -> None:
    """List all ghost (synthesis) notes."""
    proj = _ensure_project()
    if not proj.ghost_notes:
        output({"ghosts": []}, human="  No ghost notes yet.")
        return
    if is_json_mode():
        output([g.to_dict() for g in proj.ghost_notes])
    else:
        for g in proj.ghost_notes:
            print(f"  {g.id}: [{g.category}] {g.text}")


@ghost.command("claim")
@click.argument("ghost_id")
def ghost_claim(ghost_id: str) -> None:
    """Promote a ghost note to a regular block (thesis type)."""
    proj = _ensure_project()
    gn = next((g for g in proj.ghost_notes if g.id == ghost_id), None)
    if not gn:
        error(f"Ghost note '{ghost_id}' not found.")
    block = proj.add_block(gn.text, "thesis")
    block.category = gn.category
    proj.ghost_notes = [g for g in proj.ghost_notes if g.id != ghost_id]
    _save_project()
    success(f"Claimed ghost as block {block.id}: [{block.content_type}] {block.text[:50]}")


# ── Export Commands ───────────────────────────────────────────────────────────

@cli.group("export")
def export_cmd():
    """Export project data."""
    pass


@export_cmd.command("markdown")
@click.option("--output", "-o", "out_path", type=click.Path(), help="Output file path.")
def export_markdown(out_path: str | None) -> None:
    """Export project as formatted Markdown."""
    proj = _ensure_project()
    md = export_to_markdown(proj)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
        success(f"Exported to {out_path}")
    else:
        print(md)


@export_cmd.command("nodepad")
@click.option("--output", "-o", "out_path", type=click.Path(), help="Output file path.")
def export_nodepad(out_path: str | None) -> None:
    """Export project as .nodepad JSON."""
    proj = _ensure_project()
    data = proj.to_nodepad()
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        success(f"Exported to {out_path}")
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))


# ── Config Commands ───────────────────────────────────────────────────────────

@cli.group()
def config():
    """Manage AI provider configuration."""
    pass


@config.command("show")
def config_show() -> None:
    """Show current configuration."""
    cfg = load_config()
    if is_json_mode():
        safe = {k: ("***" if k == "api_key" and v else v) for k, v in cfg.items()}
        output(safe)
    else:
        print(f"  Provider:     {cfg.get('provider', 'openrouter')}")
        print(f"  Model:        {cfg.get('model_id', 'openai/gpt-4o')}")
        key = cfg.get("api_key", "")
        masked = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else ("(set)" if key else "(not set)")
        print(f"  API Key:      {masked}")
        print(f"  Grounding:    {'on' if cfg.get('web_grounding') else 'off'}")
        print(f"  Config file:  {CONFIG_FILE}")


@config.command("set")
@click.option("--api-key", help="API key for the provider.")
@click.option("--provider", type=click.Choice(["openrouter", "openai", "zai"]), help="AI provider.")
@click.option("--model", "model_id", help="Model ID to use.")
@click.option("--grounding/--no-grounding", default=None, help="Enable/disable web grounding.")
@click.option("--base-url", help="Custom base URL for the provider.")
def config_set(api_key: str | None, provider: str | None, model_id: str | None,
               grounding: bool | None, base_url: str | None) -> None:
    """Update configuration settings."""
    cfg = load_config()
    if api_key is not None:
        cfg["api_key"] = api_key
    if provider is not None:
        cfg["provider"] = provider
    if model_id is not None:
        cfg["model_id"] = model_id
    if grounding is not None:
        cfg["web_grounding"] = grounding
    if base_url is not None:
        cfg["custom_base_url"] = base_url
    save_config(cfg)
    success("Configuration updated.")


# ── Info Commands ─────────────────────────────────────────────────────────────

@cli.group()
def info():
    """Introspect project data."""
    pass


@info.command("types")
def info_types() -> None:
    """List all content types with descriptions."""
    if is_json_mode():
        output(CONTENT_TYPE_META)
    else:
        for t in ALL_CONTENT_TYPES:
            meta = CONTENT_TYPE_META[t]
            print(f"  {meta['emoji']} {meta['label']:12s} {meta['description']}")


@info.command("connections")
def info_connections() -> None:
    """Show block connection graph."""
    proj = _ensure_project()
    edges = []
    for b in proj.blocks:
        for target_id in b.influenced_by:
            target = proj.get_block(target_id)
            if target:
                edges.append({
                    "from": b.id,
                    "from_text": b.text[:40],
                    "to": target.id,
                    "to_text": target.text[:40],
                })
    if is_json_mode():
        output(edges)
    elif not edges:
        print("  No connections found. Enrich blocks to discover connections.")
    else:
        for e in edges:
            print(f"  {e['from']} ({e['from_text']}...)")
            print(f"    -> {e['to']} ({e['to_text']}...)")


@info.command("detect")
@click.argument("text")
def info_detect(text: str) -> None:
    """Detect content type for a text string (without saving)."""
    detected = detect_content_type(text)
    meta = CONTENT_TYPE_META.get(detected, {})
    if is_json_mode():
        output({"contentType": detected, "label": meta.get("label", detected)})
    else:
        print(f"  {meta.get('emoji', '')} {meta.get('label', detected)} ({detected})")


# ── REPL ──────────────────────────────────────────────────────────────────────

class NodepadREPL(cmd.Cmd):
    """Interactive REPL for nodepad CLI."""

    intro = (
        "\n"
        "  nodepad CLI \u2014 spatial AI research tool\n"
        "  Type 'help' for commands, 'quit' to exit.\n"
    )
    prompt = "nodepad> "

    def _dispatch(self, line: str) -> None:
        """Parse a line and dispatch to the Click CLI."""
        try:
            args = shlex.split(line)
        except ValueError as e:
            print(f"  Parse error: {e}")
            return
        if not args:
            return
        try:
            cli.main(args, standalone_mode=False)
        except SystemExit:
            pass
        except click.exceptions.UsageError as e:
            print(f"  Usage error: {e}")
        except Exception as e:
            print(f"  Error: {e}")

    def default(self, line: str) -> None:
        self._dispatch(line)

    def do_quit(self, _: str) -> bool:
        """Exit the REPL."""
        return True

    def do_exit(self, _: str) -> bool:
        """Exit the REPL."""
        return True

    do_EOF = do_quit

    def do_help(self, arg: str) -> None:
        """Show help for commands."""
        if not arg:
            print("\n  Available command groups:")
            print("    project    Manage projects (create, open, info, list)")
            print("    block      Manage blocks (add, list, show, edit, delete, pin)")
            print("    enrich     AI enrichment (block, all)")
            print("    ghost      Synthesis notes (generate, list, claim)")
            print("    export     Export data (markdown, nodepad)")
            print("    config     Settings (show, set)")
            print("    info       Introspect (types, connections, detect)")
            print("    quit       Exit the REPL")
            print("\n  Type '<group> --help' for details on each group.")
            print()
        else:
            self._dispatch(f"{arg} --help")

    def emptyline(self) -> None:
        pass


if __name__ == "__main__":
    cli()
