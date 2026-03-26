---
name: memory-review
version: 1.0.0
description: "Review daily session logs and propose updates to MEMORY.md. Distills raw session notes into curated long-term memory — significant events, decisions, and life updates only."
metadata:
  openclaw:
    emoji: "📝"
---

# Memory Review

Review recent daily session logs and propose targeted updates to `MEMORY.md` (long-term curated memory). Think of this as reviewing a journal and updating your mental model.

> **Why this exists:** Daily session logs capture everything — decisions, tool outputs, debugging sessions, casual conversations. MEMORY.md should only contain the distilled essence: life updates, significant decisions, status changes, and lessons learned.

## When to Use

- Daily cron job (runs every morning)
- Manual trigger after a particularly eventful day/week

## Prerequisites

- Daily session logs exist in `memory/shared/daily/`
- `MEMORY.md` exists at workspace root

## Workflow

### Step 1: Read Context

1. `MEMORY.md` — current long-term state
2. `memory/shared/daily/` — read the last 2-3 days of session logs
3. `USER.md` — user profile for context on what matters

### Step 2: Identify Significant Updates

Look for these types of changes worth proposing:

**INCLUDE:**
- Life milestones (new job, move, relationship change, visa status)
- Strategic decisions that affect ongoing behavior
- New ongoing projects or initiatives
- Status changes to tracked items (e.g., a project shipped, a trip completed)
- Critical system constraints or lessons learned
- Changes to user preferences or communication style

**EXCLUDE:**
- Implementation details (debugging steps, config changes, code fixes)
- Transient technical work (already in daily logs)
- Stats/metrics that change frequently (track in dedicated files instead)
- Items already documented in skill files, HEARTBEAT.md, or TOOLS.md
- Duplicate information already in MEMORY.md

### Step 3: Write Proposal

Create `memory/shared/diffs/YYYY-MM-DD-proposed.md`:

```markdown
# Memory Diff Proposal — {date}

## MEMORY.md Updates

### {UPDATE/ADD/REMOVE}: {section name}

**Proposed {addition/change/removal}:**

```markdown
{exact markdown to add/change}
```

**Reason:** {why this belongs in MEMORY.md — what makes it significant enough for long-term memory}

**Why MEMORY.md:** {why this is a system-level constraint, not just a daily note}

---

## No Other Updates Proposed

**Filtered out:**
- {item}: {reason — transient, already documented, too granular}

**Quality check:** {assessment of what was reviewed and why items were filtered}
```

### Step 4: Send Summary

If Telegram is configured, send a brief summary to the Memory topic:
- Whether any proposals were generated
- One-line description of each proposal
- "Full analysis: `memory/shared/diffs/YYYY-MM-DD-proposed.md`"
- "Awaiting approval (24h veto window)" or "Clean slate — no updates proposed"

### Step 5: Auto-Approve Check

Check `memory/shared/diffs/` for `*-proposed.md` files older than 24h:
- If found and not vetoed, apply the changes to MEMORY.md
- Move the proposal to `memory/shared/diffs/applied/`

## Quality Bar

- **Ruthlessly filter.** MEMORY.md is curated wisdom, not a changelog.
- A "no updates" day is normal and expected — most days don't produce MEMORY.md-worthy events.
- Ask: "Would future-me need this to make a decision?" If no, don't propose it.
- Prefer updating existing sections over adding new ones.
- One significant, well-reasoned proposal is better than five marginal ones.

## Output Files

- `memory/shared/diffs/YYYY-MM-DD-proposed.md` — the proposal
- `memory/shared/diffs/applied/` — archive of applied proposals
- Updates to `MEMORY.md` (only after approval/auto-approve)
