---
name: fabric-profile-builder
description: Build a comprehensive interest profile from Fabric API thread data. Downloads all user threads (Google searches, YouTube, Instagram, shopping, etc.), extracts interest signals using LLM batch analysis, and synthesizes 10 topic-specific profiles plus a high-level USER.md summary. Use when asked to build, rebuild, or update a user interest profile from Fabric data, or to analyze someone's digital activity patterns.
---

# Fabric Profile Builder

Build a user interest profile from Fabric API thread history. 4-phase pipeline: fetch → extract → synthesize → summarize.

## Prerequisites

- `FABRIC_USER_ID` and `FABRIC_API_KEY` env vars set
- Python 3.10+ with `requests` package
- At least one LLM provider SDK installed (`anthropic`, `openai`, or both)
- Corresponding API key set in env (e.g., `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`)

## Model Selection Strategy

The pipeline uses two model tiers. The agent should pick models based on what's available:

**Phase 2 (Extraction) — use a fast, cheap model:**
- Processes hundreds of batches, each a structured JSON extraction task
- Latency and cost matter more than reasoning depth
- Good choices: `claude-haiku-4-5`, `gpt-4o-mini`, `llama-3.1-8b`, any fast model
- Provider: whatever is cheapest/fastest available

**Phase 3+4 (Synthesis) — use a reasoning-capable model:**
- Only ~11 calls total (10 categories + 1 summary)
- Needs to write coherent narrative, cross-reference signals, rank interests
- Good choices: `claude-sonnet-4-6`, `claude-opus-4-6`, `gpt-4o`, `gpt-4.5`
- Provider: whatever has the best reasoning model available

**If only one model is available** (e.g., only Haiku): use it for everything — the pipeline still produces good results. The extraction prompts are structured enough that even small models handle them well.

## Quick Start

Run the full pipeline, specifying models:

```bash
cd <skill_dir>

python3 scripts/run_pipeline.py \
  --output-dir <output_dir> \
  --extraction-provider anthropic --extraction-model claude-haiku-4-5 \
  --synthesis-provider anthropic --synthesis-model claude-sonnet-4-6
```

> `<skill_dir>` is the directory containing this SKILL.md. `<output_dir>` is wherever you want the output written.

Or run phases individually (useful for resuming):

```bash
# Phase 1: Fetch all threads (no LLM needed)
python3 scripts/fetch_threads.py --output-dir OUTPUT_DIR

# Phase 2: Extract interest signals
python3 scripts/extract_signals.py --output-dir OUTPUT_DIR \
  --provider anthropic --model claude-haiku-4-5

# Phase 3+4: Synthesize profiles + USER.md
python3 scripts/synthesize_profiles.py --output-dir OUTPUT_DIR \
  --provider anthropic --model claude-sonnet-4-6
```

## Supported Providers

| Provider | Env Var | SDK | Notes |
|----------|---------|-----|-------|
| `anthropic` | `ANTHROPIC_API_KEY` | `anthropic` | Also auto-reads OpenClaw auth-profiles.json |
| `openai` | `OPENAI_API_KEY` | `openai` | Works with Azure or any compatible API |
| `openrouter` | `OPENROUTER_API_KEY` | `openai` | Routes to any model via openrouter.ai |

For Anthropic OAuth tokens (sk-ant-oat*), you may need to set `ANTHROPIC_BETA=oauth-2025-04-20` for access to larger models.

## Phases

### Phase 1: Fetch Threads
- Probes API for available interaction types
- Downloads all threads with pagination (page_size=100, 0.2s sleep)
- Saves to `OUTPUT_DIR/raw_threads.json`
- Retries failed requests 3x with exponential backoff
- No LLM needed

### Phase 2: Extract Interest Signals
- Compacts threads (type-specific: title/query/description extraction)
- Batches 100 threads per LLM call
- Extracts signals across 10 categories: relationships, work, travel, food, activities, sport, health, entertainment, shopping, values
- Checkpoints each batch to `OUTPUT_DIR/intermediate/batch_NNN.json`
- Resumable — skips already-completed batches

### Phase 3: Synthesize Interest Profiles
- Groups all signals by category
- One LLM call per category for narrative synthesis
- Writes to `OUTPUT_DIR/interests/{category}.md`

### Phase 4: Generate USER.md
- Reads all 10 profiles
- Produces a ranked, cross-referenced summary
- Writes to `OUTPUT_DIR/USER.md`

## Output Structure

```
OUTPUT_DIR/
├── raw_threads.json          # All threads
├── fetch_meta.json           # Thread counts, date range, active types
├── intermediate/             # Per-batch extraction results
│   ├── batch_000.json
│   └── ...
├── interests/                # 10 category profiles
│   ├── relationships.md
│   ├── work.md
│   ├── travel.md
│   ├── food.md
│   ├── activities.md
│   ├── sport.md
│   ├── health.md
│   ├── entertainment.md
│   ├── shopping.md
│   └── values.md
├── USER.md                   # High-level summary
└── .checkpoint.json          # Resumability state
```

## Configuration via Env Vars

All settings can also be passed as CLI args (which take precedence):

| Var | Default | Description |
|-----|---------|-------------|
| `FABRIC_USER_ID` | (required) | Fabric user UUID |
| `FABRIC_API_KEY` | (required) | Fabric API key |
| `PROFILE_EXTRACTION_PROVIDER` | `anthropic` | Provider for Phase 2 |
| `PROFILE_EXTRACTION_MODEL` | `claude-haiku-4-5` | Model for Phase 2 |
| `PROFILE_SYNTHESIS_PROVIDER` | `anthropic` | Provider for Phase 3+4 |
| `PROFILE_SYNTHESIS_MODEL` | `claude-haiku-4-5` | Model for Phase 3+4 |
| `ANTHROPIC_BETA` | (none) | Beta flags for Anthropic OAuth tokens |

## After Running

Review the output and copy relevant files to memory:

```bash
# Copy interest profiles to wherever user context lives
cp OUTPUT_DIR/interests/*.md /path/to/user/memory/

# Review USER.md and merge into existing user profile
# Don't blindly overwrite — review and integrate
```

## Error Handling

| Scenario | Action |
|---|---|
| API returns 401 | Check API key |
| Pagination failure | Retries 3x with backoff, saves partial results |
| Thread with no content | Skipped automatically |
| LLM returns invalid JSON | Retries once, skips batch on failure |
| LLM rate limit (429) | Backs off and retries |
| Partial run interrupted | Resume from checkpoint (skips completed batches) |

## Payload Schemas

See `references/api_schemas.md` for detailed thread payload structures per interaction type.
