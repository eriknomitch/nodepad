# NODEPAD — Agent Harness SOP

## Software Overview

**Nodepad** is a spatial AI-augmented research tool built with Next.js. Users add notes to a canvas; AI classifies them into 14 content types, adds annotations, infers connections, and generates synthesis insights. All data lives in the browser (localStorage). No accounts or backend servers — API keys are stored client-side and sent directly to AI providers.

**Website:** https://nodepad.space

## Architecture

Nodepad is a single-page client application. The "backend" is a set of AI provider APIs (OpenRouter, OpenAI, Z.ai) accessed via OpenAI-compatible chat completion endpoints. The only server-side route is `/api/fetch-url` for CORS-bypassed URL metadata fetching.

### Data Model

- **TextBlock**: A note with id, text, timestamp, contentType (14 types), category, annotation, confidence, sources, influencedBy connections, subTasks, isPinned
- **Project**: Collection of blocks + ghostNotes (synthesis) + UI state
- **GhostNote**: AI-generated synthesis insight (15-25 word thesis + category)
- **ContentType**: entity, claim, question, task, idea, reference, quote, definition, opinion, reflection, narrative, comparison, thesis, general

### File Formats

- **.nodepad**: Versioned JSON format (version 1) — full project fidelity including blocks, ghost notes, connections, sub-tasks
- **Markdown export**: YAML front matter, TOC, type-grouped sections, claims table, task checklists

### AI Pipeline

1. **Enrichment** (`ai-enrich.ts`): Detects language/script → builds prompt with note context → POSTs to provider → parses structured JSON response (contentType, category, annotation, confidence, connections, sources)
2. **Synthesis** (`ai-ghost.ts`): Generates emergent insights from canvas context. Cross-category bridge detection, 15-25 word thesis constraint, deduplication via previous syntheses.
3. **Providers**: OpenRouter (default), OpenAI, Z.ai. Each with configurable base URL, model ID, web grounding support.

## CLI Command Groups

| Group | Description |
|-------|-------------|
| `project` | Create, list, show, delete, rename projects |
| `block` | Add, list, show, edit, delete, pin/unpin blocks |
| `enrich` | Run AI enrichment on blocks |
| `ghost` | Generate synthesis insights |
| `export` | Export to markdown or .nodepad format |
| `config` | Manage AI provider settings |
| `info` | Introspect project data (stats, types, connections) |

## Real Software Integration

The "real software" for nodepad is the AI provider APIs. The CLI:
1. Reads/writes .nodepad project files directly (JSON manipulation)
2. Calls the same OpenAI-compatible APIs for enrichment and synthesis
3. Generates markdown export using the same formatting rules
4. Manages config via `~/.nodepad/config.json` (replaces localStorage)

## Key Implementation Notes

- Content type detection is heuristic-based — port directly from TypeScript
- AI enrichment uses OpenAI chat completions API with structured JSON output
- Ghost synthesis uses lighter models with json_object response format
- .nodepad format is JSON with version field for future migration
- Config stored in `~/.nodepad/config.json` instead of browser localStorage
- Projects stored as individual .nodepad files in working directory or `~/.nodepad/projects/`
