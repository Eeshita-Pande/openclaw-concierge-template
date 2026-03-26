---
name: fabric-memory-diff
version: 1.0.0
description: "Analyze Fabric threads and propose targeted memory updates. Compares new activity against existing user memory, filters transient items, and writes proposals with a 24h veto window."
metadata:
  openclaw:
    emoji: "🧠"
---

# Fabric Memory Diff

Analyze recent Fabric API data and propose targeted updates to user memory files. This skill turns raw activity into meaningful, deduplicated memory proposals.

> **Why this exists:** Raw Fabric data is noisy — most searches are transient utility (weather, directions, quick lookups). This skill separates signal from noise and proposes only genuine interest updates to the right memory files.

## When to Use

- Daily cron job (runs after `fabric-refresh` populates `memory/fabric-latest.md`)
- Manual trigger when catching up on missed days

## Prerequisites

- `memory/fabric-latest.md` must be populated (by the `fabric-refresh` cron)
- User memory files exist in `memory/{user_slug}/` (even if empty stubs)
- `.env.fabric` credentials configured

## Workflow

### Step 1: Read Context

Load these files (DO NOT skip any):
1. `memory/fabric-latest.md` — raw Fabric threads from last 24h
2. `USER.md` — user profile for context
3. `memory/{user_slug}/restaurants.md` — existing restaurant memory
4. `memory/{user_slug}/fashion.md` — existing fashion memory
5. `memory/{user_slug}/travel.md` — existing travel memory
6. `memory/{user_slug}/interests.md` — existing interests memory
7. `memory/{user_slug}/work.md` — existing work memory
8. `memory/{user_slug}/relationships.md` — existing relationship memory

### Step 2: Analyze Each Thread

For each Fabric thread, classify it:

**INCLUDE (propose update):**
- Sustained interest signals (same topic across multiple searches/days)
- New restaurants visited or researched with intent
- Travel planning (flights, hotels, specific destinations)
- Professional tool/competitor research
- Books, articles, or content consumed with depth (multiple related searches)
- Life milestones (immigration, career changes, moves)
- New relationships or significant social events

**EXCLUDE (filter out):**
- Transient utility searches (weather, directions, quick lookups, password resets)
- Single random media consumption (one-off YouTube video, casual browsing)
- Already-documented items (check existing memory files for duplicates)
- News events without sustained personal interest
- Platform/tool troubleshooting (WiFi issues, app settings)

### Step 3: Route to Correct File

Each proposal targets a specific memory file:

| Signal Type | Target File |
|-------------|-------------|
| Restaurant visit/research | `memory/{user_slug}/restaurants.md` |
| Fashion purchase/interest | `memory/{user_slug}/fashion.md` |
| Travel planning/visit | `memory/{user_slug}/travel.md` |
| Books, articles, research | `memory/{user_slug}/interests.md` |
| Career, tools, competitors | `memory/{user_slug}/work.md` |
| People, social events | `memory/{user_slug}/relationships.md` |

### Step 4: Dedup Check

For each proposal, verify it doesn't already exist in the target file:
- Search for the restaurant name, book title, destination, etc.
- If found, skip (log as "already tracked")
- If similar but different (e.g., same restaurant chain, different location), note the distinction

### Step 5: Write Proposal

Create `memory/shared/diffs/fabric-YYYY-MM-DD.md`:

```markdown
# Fabric Daily Diff — {date}
**Generated:** {timestamp} UTC
**Period:** Past 24h (from {from_date})
**Total items analyzed:** {count}

---

## PROPOSAL {n}: {short title}
**Item:** {name/description}
**Type:** {category}
**Context:** {what the user did — search terms, pages visited, time spent}

**Proposal:** Add to **{target_file}** → "{section}"

**Entry:**
```markdown
- **{Name}**: {description with context}. ({date}).
```

**Conflict check:** {result} ✅/⚠️

---

## Filtered Out
- **{item}** ({reason}): {why filtered — transient, duplicate, etc.}

---

## Summary
- **{n} new proposal(s)** ({categories})
- **{m} items filtered** ({reasons})
- **Quality bar:** {assessment}

---

**Veto window:** 24 hours. React ✅ to approve, or reply with edits/vetoes.
```

### Step 6: Send Summary

If Telegram is configured, send a brief summary to the Memory topic:
- Number of proposals
- One-line description of each
- Link to full diff file
- "Awaiting approval (24h veto window)"

### Step 7: Auto-Approve Check

Check `memory/shared/diffs/` for proposals older than 24h that haven't been vetoed:
- If found, apply them to the target memory files
- Move the diff file to `memory/shared/diffs/applied/`
- Log the application

## Quality Bar

- **0 proposals is a valid outcome.** Most days have mostly transient activity.
- Better to miss a signal than to pollute memory with noise.
- When in doubt, filter it out — the data is still in `fabric-latest.md` if needed later.
- Each proposal must include a conflict check against existing memory.

## Output Files

- `memory/shared/diffs/fabric-YYYY-MM-DD.md` — the proposal
- `memory/shared/diffs/applied/` — archive of applied diffs
- Updates to `memory/{user_slug}/*.md` (only after approval/auto-approve)
