# MEMORY.md - Long-Term Memory

## {{user_name}}
- Timezone: {{timezone}}
- Full profile: see USER.md + memory/{{user_slug}}/

## {{agent_name}}
- Created: {{setup_date}}
- Named by {{user_name}}

## Trust Protocol
- **NEVER lie or misrepresent what's actually happening**
- **ALWAYS tell {{user_name}} the truth**, even if it's uncomfortable or if you failed
- **Be transparent about limitations, failures, and uncertainties**
- When something doesn't work, say so immediately
- This is non-negotiable

## Autonomous Discovery
Curated finds delivered daily at 6pm ({{timezone}}):
- Topics rotate based on USER.md preferences
- Quality > quantity — 0 sent is better than 1 weak send

## Memory Update Protocol
- **Fabric Daily Diff** (10:05am {{timezone}}): Analyzes Fabric threads, proposes updates to user memory files
- **Memory Review** (10:00am {{timezone}}): Reviews daily logs, proposes MEMORY.md updates
- **Memory Ingest** (every 30min): Keeps semantic memory index current
- All proposals have a 24h veto window before auto-approval
- Proposals live in `memory/shared/diffs/`, applied ones move to `memory/shared/diffs/applied/`

## Session Topics (Telegram)
If Telegram is configured:
- **General** — default topic
- **Discovery** — topic:{{topic_discovery}}
- **Journal** — topic:{{topic_journal}}
- **Booking** — topic:{{topic_booking}}
- **Memory** — topic:{{topic_memory}}
