# OpenClaw Concierge Template

A template for setting up a personal AI concierge powered by [OpenClaw](https://docs.openclaw.ai). Point Claude at this repo and it will set up the full system for you.

**For Claude: read `CLAUDE.md` for setup instructions.**

## What You Get

| Feature | What it does | Schedule |
|---------|-------------|----------|
| **Journal** | One sharp observation + question based on your recent activity | 10pm daily |
| **Discovery** | 1-2 curated finds (restaurants, articles, fashion, travel) | 6pm daily |
| **Restaurant Booking** | Automated OpenTable reservations via browser automation | Weekly check (Sunday noon) + on demand |
| **Fabric Sync** | Pulls your Google searches, Instagram, YouTube into memory | 9am daily |
| **Memory Diff** | Analyzes Fabric data and proposes targeted memory updates | 10:05am daily |
| **Memory Review** | Reviews session logs and curates long-term memory | 10am daily |
| **Memory Ingest** | Keeps semantic memory index current | Every 30min |

Outputs can optionally be delivered to organized Telegram group topics.

## Prerequisites

1. **OpenClaw** installed and running ([docs.openclaw.ai](https://docs.openclaw.ai))
2. **Fabric credentials** in `~/.openclaw/workspace/.env.fabric` ([developer.onfabric.io](https://developer.onfabric.io))
3. **Telegram bot** connected to OpenClaw (optional — for message delivery)

---

## Setup

### Step 1: Fabric Credentials

Create an account at [developer.onfabric.io](https://developer.onfabric.io), connect data sources (Google, Instagram), then save your credentials on the machine:

```bash
nano ~/.openclaw/workspace/.env.fabric
```

Add:
```
FABRIC_API_KEY=your_fabric_api_key
FABRIC_USER_ID=your_fabric_user_id
OPENAI_API_KEY=your_openai_api_key
```

Then: `chmod 600 ~/.openclaw/workspace/.env.fabric`

### Step 2: Run Bootstrap

```bash
git clone <REPO_URL>
cd openclaw-concierge-template
./bootstrap.sh
```

Timezone is auto-detected. Override with `--timezone "America/New_York"` if needed.
Add `--telegram-group-id`, `--topic-*` flags if using Telegram delivery.

This will:
1. Copy template files into your OpenClaw workspace
2. Install all skills (journal, discovery, fabric, memory-review, fabric-memory-diff, opentable-booking, etc.)
3. Pull your Fabric data and generate memory stubs
4. Set up Chrome + Xvfb for browser automation
5. Create 7 cron jobs (fabric-refresh, memory-review, fabric-daily-diff, memory-ingest, discovery, journal, weekly-booking-check)
6. Write a post-setup checklist

### Step 3: Review USER.md

Run the profile builder to generate a comprehensive user profile, then review it:
```bash
cd ~/.openclaw/workspace
source .env.fabric
python3 skills/fabric-profile-builder/scripts/run_pipeline.py \
  --output-dir /tmp/fabric-profile \
  --extraction-provider openai --extraction-model gpt-4o-mini \
  --synthesis-provider openai --synthesis-model gpt-4o
```

Review `USER.md` — this file drives everything (discoveries, journal questions, booking preferences).

### Step 4: Post-Setup

1. Restart the gateway: `systemctl --user restart openclaw-gateway.service`
2. Verify crons: `openclaw cron list`
3. Log into OpenTable via browser if you want restaurant booking (see `setup-checklist.md`)

Your agent is live. Tonight you'll get your first discoveries at 6pm and journal reflection at 10pm. Weekly booking checks run every Sunday at noon.

---

## Folder Structure

After setup, your workspace looks like:

```
workspace/
├── SOUL.md              # Agent personality
├── IDENTITY.md          # Agent name + emoji
├── USER.md              # Your profile (auto-generated from Fabric)
├── AGENTS.md            # Workspace rules
├── MEMORY.md            # Long-term curated memory
├── HEARTBEAT.md         # Periodic health checks
├── TOOLS.md             # Local tool notes
│
├── skills/
│   ├── journal/         # Evening reflection skill
│   ├── discovery/       # Curated finds skill
│   ├── fabric/          # Fabric API integration
│   ├── fabric-profile-builder/  # Full interest profile builder
│   ├── fabric-memory-diff/  # Intelligent Fabric diff + proposals
│   ├── memory-review/       # Daily memory review + curation
│   └── opentable-booking/   # OpenTable browser automation
│
├── memory/
│   ├── user/            # Your ground truth (from Fabric)
│   │   ├── interests.md
│   │   ├── restaurants.md
│   │   ├── fashion.md
│   │   ├── travel.md
│   │   ├── relationships.md
│   │   └── work.md
│   ├── agent/           # Agent's autonomous work
│   │   ├── discoveries/
│   │   └── bookings/
│   ├── shared/
│   │   ├── daily/       # Session logs
│   │   └── diffs/       # Memory update proposals (24h veto window)
│   │       └── applied/ # Archive of applied proposals
│   ├── topics/          # Dedup files
│   └── instagram/       # Monthly Instagram logs
│
└── scripts/
    ├── fabric-sync.sh
    └── check-regressions.py
```

---

## Customization

### Agent Personality
Edit `SOUL.md` — this is your agent's voice. The default is warm, direct, and slightly witty. Make it yours.

### Discovery Types
Edit `skills/discovery/SKILL.md` Step 4 — change the discovery categories to match your interests (e.g., swap "luxury fashion" for "indie music" or "architecture").

### Journal Tone
Edit `skills/journal/SKILL.md` — adjust examples, signals to look for, closing line.

### Cron Schedules
All schedules are in your local timezone. Adjust via OpenClaw cron commands or the TUI.

---

## Skills

Installed automatically by the bootstrap:

| Skill | Source | Description |
|-------|--------|-------------|
| `journal` | Bundled | Nightly journal reflection |
| `discovery` | Bundled | Curated finds curation |
| `fabric` | Bundled | Fabric API integration |
| `fabric-profile-builder` | Bundled | Build interest profiles from Fabric data |
| `fabric-memory-diff` | Bundled | Analyze Fabric data and propose memory updates |
| `memory-review` | Bundled | Review session logs and curate long-term memory |
| `opentable-booking` | Bundled | OpenTable browser automation |

## License

MIT
