# cli-anything-nodepad

CLI harness for [nodepad](https://nodepad.space) — a spatial AI-augmented research tool.

Manage projects, add and enrich notes, generate synthesis insights, and export to Markdown or `.nodepad` format — all from the terminal. Designed for AI agent consumption with `--json` output mode.

## Installation

```bash
cd agent-harness
pip install -e .
```

Verify installation:

```bash
which cli-anything-nodepad
cli-anything-nodepad --help
```

## Quick Start

```bash
# Configure your AI provider
cli-anything-nodepad config set --provider openrouter --api-key sk-or-v1-...

# Create a project
cli-anything-nodepad project create "My Research"

# Add notes (auto-detects content type)
cli-anything-nodepad -p my-research.nodepad block add "What is consciousness?"
cli-anything-nodepad -p my-research.nodepad block add "The brain processes information in parallel"
cli-anything-nodepad -p my-research.nodepad block add "TODO read Dennett's Consciousness Explained"

# Enrich all blocks with AI annotations
cli-anything-nodepad -p my-research.nodepad enrich all

# Generate synthesis insights
cli-anything-nodepad -p my-research.nodepad ghost generate

# Export to markdown
cli-anything-nodepad -p my-research.nodepad export markdown -o research.md
```

## REPL Mode

Run without a subcommand to enter interactive mode:

```bash
cli-anything-nodepad -p my-research.nodepad
```

```
nodepad> block add "Quantum entanglement challenges locality"
nodepad> block list
nodepad> enrich all
nodepad> ghost generate
nodepad> export markdown
nodepad> quit
```

## JSON Mode

Add `--json` for machine-readable output:

```bash
cli-anything-nodepad --json -p project.nodepad block list
cli-anything-nodepad --json info types
```

## Commands

| Command | Description |
|---------|-------------|
| `project create <name>` | Create a new project |
| `project open <file>` | Open a .nodepad file |
| `project info` | Show project statistics |
| `project list [dir]` | List .nodepad files |
| `block add <text>` | Add a note (auto-detects type) |
| `block list [--type X]` | List blocks |
| `block show <id>` | Show block details |
| `block edit <id> <text>` | Edit block text |
| `block delete <id>` | Delete a block |
| `block pin <id>` | Toggle pin state |
| `enrich block <id>` | AI-enrich a single block |
| `enrich all` | Enrich all unenriched blocks |
| `ghost generate [-n N]` | Generate synthesis notes |
| `ghost list` | List ghost notes |
| `ghost claim <id>` | Promote ghost to block |
| `export markdown [-o file]` | Export as Markdown |
| `export nodepad [-o file]` | Export as .nodepad JSON |
| `config show` | Show current config |
| `config set` | Update config settings |
| `info types` | List all content types |
| `info connections` | Show block connections |
| `info detect <text>` | Detect content type |

## Configuration

Config is stored in `~/.nodepad/config.json`. Environment variables override file settings:

| Env Variable | Description |
|-------------|-------------|
| `NODEPAD_API_KEY` | API key for the provider |
| `NODEPAD_PROVIDER` | `openrouter`, `openai`, or `zai` |
| `NODEPAD_MODEL` | Model ID to use |
| `NODEPAD_BASE_URL` | Custom API base URL |

## Content Types

nodepad classifies notes into 14 types: entity, claim, question, task, idea, reference, quote, definition, opinion, reflection, narrative, comparison, thesis, general.

## Requirements

- Python 3.11+
- click
- An API key from OpenRouter, OpenAI, or Z.ai (for AI features)
