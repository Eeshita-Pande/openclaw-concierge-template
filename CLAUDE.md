# OpenClaw Concierge Template

You are setting up a personal AI concierge powered by OpenClaw. This repo is a template — follow these instructions to configure a fully working OpenClaw agent for the user.

## What This Sets Up

A personal AI assistant that:
- Sends a **journal reflection** every night (10pm) based on the user's recent activity
- Curates **1-2 daily discoveries** (6pm) — restaurants, articles, travel, fashion
- Books **restaurants via OpenTable** on demand (browser automation)
- Syncs the user's **Fabric data** (Google searches, Instagram, YouTube) into memory every morning (9am)
- Optionally delivers everything to organized **Telegram group topics**

## Prerequisites

Before running bootstrap, ensure:

1. **OpenClaw is installed and the gateway is running** on the target machine
   - Verify: `systemctl --user status openclaw-gateway.service`
   - The workspace should exist at `~/.openclaw/workspace`
   - The `openclaw` CLI should be available

2. **Python 3** is installed (for Fabric data bootstrapping)
   - Verify: `python3 --version`

3. The target machine is **Linux/amd64** (for Chrome + Xvfb browser automation)

## Setup Flow

### Step 1: Verify Prerequisites

Before running bootstrap, verify:

1. **OpenClaw is running:** `systemctl --user status openclaw-gateway.service`
2. **Fabric credentials exist:** `cat ~/.openclaw/workspace/.env.fabric` should contain `FABRIC_API_KEY` and `FABRIC_USER_ID`

If credentials aren't set up yet, create the file:
```bash
nano ~/.openclaw/workspace/.env.fabric
```

Add these lines:
```
FABRIC_API_KEY=<your_fabric_api_key>
FABRIC_USER_ID=<your_fabric_user_id>
OPENAI_API_KEY=<your_openai_api_key>
```

**How to get Fabric credentials:** Create an account at [developer.onfabric.io](https://developer.onfabric.io), follow the Quick Start to connect data sources (Google, Instagram), then find the API Key and User ID on the dashboard.

### Step 2: Clone This Repo to the Target Machine

Clone this repo to the target machine (replace `<REPO_URL>` with the actual repository URL):

```bash
cd /tmp
git clone <REPO_URL>
cd openclaw-concierge-template
```

### Step 3: Run the Bootstrap Script

```bash
./bootstrap.sh
```

The script auto-detects timezone from the machine. Override with `--timezone "America/New_York"` if needed.
Add `--location "New York"` to set the user's city (otherwise derived from timezone).
Add `--telegram-group-id`, `--topic-discovery`, `--topic-journal`, `--topic-booking`, `--topic-memory` if using Telegram delivery.

The bootstrap script will:
1. Create the memory folder structure in the workspace
2. Copy template files (SOUL.md, IDENTITY.md, USER.md, AGENTS.md, etc.)
3. Install all skills (journal, discovery, fabric, fabric-memory-diff, memory-review, opentable-booking, etc.)
4. Bootstrap memory from Fabric API data (if credentials available)
5. Install Chrome + Xvfb for browser automation
6. Create 7 cron jobs (fabric-refresh, memory-review, fabric-daily-diff, memory-ingest, discovery, journal, weekly-booking-check)
7. Write a post-setup checklist

### Step 4: Restart the Gateway

```bash
systemctl --user restart openclaw-gateway.service
```

This picks up the new DISPLAY=:99 environment variable for browser automation.

### Step 5: Verify Setup

```bash
# Check cron jobs were created
openclaw cron list

# Check the workspace has all files
ls ~/.openclaw/workspace/*.md
ls ~/.openclaw/workspace/skills/
ls ~/.openclaw/workspace/memory/
```

Expected crons:
- `fabric-refresh` — 9am daily
- `memory-review` — 10am daily
- `fabric-daily-diff` — 10:05am daily
- `memory-ingest` — every 30min (silent)
- `evening-discovery` — 6pm daily
- `nightly-journal` — 10pm daily
- `weekly-booking-check` — Sunday noon weekly
- `weekly-profile-refresh` — Sunday 8am weekly

### Step 6: Browser Login for OpenTable (Optional)

If the user wants restaurant booking, they need to log into OpenTable once:

```bash
openclaw browser start
openclaw browser navigate 'https://www.opentable.co.uk/my/profile'
# Then use screenshot + type + click to complete the login flow
openclaw browser screenshot
```

The browser session persists across restarts.

### Step 7: Build User Profile (Recommended)

If Fabric credentials are configured, run the profile builder to create a comprehensive user profile:

```bash
cd ~/.openclaw/workspace
source .env.fabric
python3 skills/fabric-profile-builder/scripts/run_pipeline.py \
  --output-dir /tmp/fabric-profile \
  --extraction-provider openai --extraction-model gpt-4o-mini \
  --synthesis-provider openai --synthesis-model gpt-4o
```

This generates interest profiles across 10 categories and a comprehensive `USER.md`. Copy the generated `USER.md` to the workspace if it looks good.

### Step 8: Review USER.md

Open `~/.openclaw/workspace/USER.md` and review the auto-generated profile with the user. Fix anything that's wrong or missing — this file drives journal questions, discovery curation, and booking preferences.

## Troubleshooting

### Cron jobs failed to create
If the gateway wasn't running during bootstrap, create them manually:
```bash
openclaw cron add --name evening-discovery --cron '0 18 * * *' --tz '<TIMEZONE>' --session isolated --message 'Read and follow the discovery skill: skills/discovery/SKILL.md' --announce --to '<TELEGRAM_CHAT_ID>'
openclaw cron add --name nightly-journal --cron '0 22 * * *' --tz '<TIMEZONE>' --session isolated --message 'Read and follow the journal skill: skills/journal/SKILL.md' --announce --to '<TELEGRAM_CHAT_ID>'
openclaw cron add --name fabric-refresh --cron '0 9 * * *' --tz '<TIMEZONE>' --session isolated --message 'Fetch fresh Fabric data. Read skills/fabric/SKILL.md. Source .env.fabric, fetch last 24h, write to memory/fabric-latest.md.'
openclaw cron add --name weekly-booking-check --cron '0 12 * * 0' --tz '<TIMEZONE>' --session isolated --message 'Check if there are any upcoming dining plans or booking requests. Read skills/opentable-booking/SKILL.md for booking flow.'
openclaw cron add --name memory-review --cron '0 10 * * *' --tz '<TIMEZONE>' --session isolated --message 'Review recent daily session logs and propose MEMORY.md updates. Read and follow skills/memory-review/SKILL.md.'
openclaw cron add --name fabric-daily-diff --cron '5 10 * * *' --tz '<TIMEZONE>' --session isolated --message 'Analyze recent Fabric data and propose memory updates. Read and follow skills/fabric-memory-diff/SKILL.md.'
openclaw cron add --name memory-ingest --every 30m --session isolated --no-deliver --message 'Run openclaw memory index to keep the semantic memory index current.'
openclaw cron add --name weekly-profile-refresh --cron '0 8 * * 0' --tz '<TIMEZONE>' --session isolated --message 'Refresh user profile from recent Fabric data and public sources. Read and follow skills/weekly-profile-refresh/SKILL.md.'
```

### Fabric bootstrap failed
The script creates empty stubs if Fabric data isn't available. You can re-run just the Fabric bootstrap later:
```bash
python3 /tmp/openclaw-concierge-template/scripts/bootstrap-fabric.py \
  --api-key "<KEY>" --user-id "<USER_ID>" \
  --user-name "<NAME>" --user-slug "<slug>" \
  --workspace ~/.openclaw/workspace \
  --timezone "<TZ>" --location "<LOC>"
```

Or use the fabric-profile-builder skill for a more thorough profile:
```bash
cd ~/.openclaw/workspace
python3 skills/fabric-profile-builder/scripts/run_pipeline.py \
  --provider anthropic --extract-model claude-haiku-4-5-20251001 --synth-model claude-sonnet-4-5-20250514
```

### Xvfb or Chrome not installing
The bootstrap assumes Debian/Ubuntu (uses `apt-get`). For other distros, install `xvfb` and `google-chrome-stable` manually, then create the systemd services as described in the bootstrap script (Step 6).

### OpenClaw CLI not found
The bootstrap checks common paths. If `openclaw` is installed elsewhere, add it to PATH or provide the full path. The fnm-installed version is checked at `~/.local/share/fnm/node-versions/*/installation/bin/openclaw`.

## Repo Structure

```
bootstrap.sh                    # Main setup script
templates/                      # Workspace file templates (with {{placeholders}})
skills/                         # Bundled skills
  discovery/SKILL.md            # Daily curated finds
  journal/SKILL.md              # Nightly journal reflection
  fabric/SKILL.md               # Fabric API integration
  fabric-profile-builder/       # Full profile builder pipeline
  fabric-memory-diff/SKILL.md   # Intelligent Fabric diff + proposals
  memory-review/SKILL.md        # Daily memory review + curation
  opentable-booking/SKILL.md    # OpenTable browser automation
  public-profile-enricher/SKILL.md  # Public profile enrichment from web
  weekly-profile-refresh/SKILL.md   # Weekly profile refresh orchestration
scripts/
  bootstrap-fabric.py           # Initial Fabric data fetch
  fabric-sync.sh                # Daily Fabric sync
  check-regressions.py          # File integrity checks
```
