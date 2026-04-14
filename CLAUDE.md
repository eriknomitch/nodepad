# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is nodepad

A spatial AI-augmented research tool built with Next.js. Users add notes to a spatial canvas; AI classifies them into 14 content types, adds annotations, infers connections, and generates synthesis insights. All data lives in the browser (localStorage). No accounts or servers — API keys are stored client-side and sent directly to providers.

## Commands

```bash
pnpm install          # Install dependencies
pnpm dev              # Start dev server (localhost:3000)
pnpm build            # Production build (outputs to .next/)
pnpm start            # Run production server
pnpm lint             # ESLint (Next.js defaults)
```

Note: `next.config.mjs` sets `ignoreBuildErrors: true` for TypeScript — the build will succeed even with type errors.

## Architecture

**Single-page client app** — `app/page.tsx` is the main entry point (`"use client"`). The only server-side route is `app/api/fetch-url/route.ts` (URL metadata fetching with SSRF protection and rate limiting).

### State & Persistence
- All state via React hooks (`useState`, `useRef`). No external state library.
- Data persisted to `localStorage` (`nodepad-projects`, `nodepad-backup`).
- Undo system: ref-based ring buffer, max 20 snapshots per project.

### Three Views
1. **Tiling** (`tiling-area.tsx`) — BSP tree layout, 7 notes/page, IntersectionObserver for page tracking
2. **Kanban** (`kanban-area.tsx`) — Notes grouped by content type columns
3. **Graph** (`graph-area.tsx`) — D3 force simulation, node size proportional to edge degree, central synthesis node

### AI Pipeline
- **Enrichment** (`lib/ai-enrich.ts`): Detects script/language → builds prompt with note history → POSTs to provider → parses structured JSON response. Retries on rate limit.
- **Synthesis** (`lib/ai-ghost.ts`): Generates emergent insights from full canvas context. De-duplicated via `lastGhostTexts`.
- **Providers** (`lib/ai-settings.ts`): OpenRouter (default), OpenAI, Z.ai. Each has configurable base URL, model ID, web grounding support. Keys stored in localStorage per provider.

### Core Data Types
- **TextBlock**: id, text, timestamp, contentType, annotation, confidence, sources[], influencedBy[], subTasks[], isPinned
- **Project**: Collection of blocks + UI state (collapsedIds, ghostNotes[], lastGhostTexts)
- **ContentType**: 14 types defined in `lib/content-types.ts` — entity, claim, question, task, idea, reference, quote, definition, opinion, reflection, narrative, comparison, general, thesis

### Content Type Detection
Heuristic-based in `lib/detect-content-type.ts`: patterns for quotes, tasks (checkboxes/TODO), questions, definitions, comparisons, URLs, reflections, opinions, entities, claims, narratives. Falls back to "general".

### Export
- **Markdown** (`lib/export.ts`): Grouped by type, YAML front matter, TOC
- **.nodepad** (`lib/nodepad-format.ts`): Versioned JSON format (version 1) with full fidelity

### Security
- SSRF protection in `api/fetch-url/route.ts` (blocks private IPs, metadata hostnames, localhost)
- Origin check middleware in `proxy.ts`
- Sliding-window rate limiting (30 URL fetches/min per IP)
- CSP headers in `next.config.mjs` — allowlist for AI provider APIs + Umami + YouTube

## Tech Stack

- **Next.js 16** / React 19 / TypeScript 5.7 (strict)
- **Tailwind CSS v4** with OKLCh color tokens in `globals.css`
- **shadcn/ui** primitives (Radix-based) in `components/ui/`
- **D3.js** for graph visualization
- **Framer Motion** for animations
- Path alias: `@/*` maps to project root

## Key Conventions

- Components are `"use client"` functional components in `components/`
- shadcn config in `components.json` (Tailwind CSS vars, Lucide icons)
- No test suite — manual QA via dev server
- CSS custom properties for content type colors: `--type-*` vars in `globals.css`
