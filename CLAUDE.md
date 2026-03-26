# OpenClaw Concierge Template

You are setting up a personal AI concierge powered by OpenClaw. This repo is a template — follow these instructions to configure a fully working OpenClaw agent for the user.

## What This Sets Up

A personal AI assistant that:
- Sends a **journal reflection** every night (10pm) based on the user's recent activity
- Curates **1-2 daily discoveries** (6pm) — restaurants, articles, travel, fashion
- Books **restaurants via OpenTable** on demand (browser automation)
- Syncs the user's **Fabric data** (Google searches, Instagram, YouTube) into memory every morning (9am)
- Delivers everything to organized **Telegram group topics**

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

### Step 1: Gather Information from the User

Ask the user for the following. Do not proceed until you have all required items.

**Required:**
| Parameter | Description | Example |
|-----------|-------------|---------|
| Agent name | The name the agent goes by | "Luna" |
| User name | The user's first name | "Eeshita" |
| Timezone | IANA timezone | "Europe/London" |
| Fabric API key | From developer.onfabric.io | "fab_..." |
| Fabric User ID | From the Fabric dashboard | "usr_..." |
| Telegram group ID | The group where the agent posts | "-100..." |
| Topic: Discovery | Telegram topic ID for curated finds | "3" |
| Topic: Journal | Telegram topic ID for journal reflections | "5" |
| Topic: Booking | Telegram topic ID for booking confirmations | "7" |
| Topic: Memory | Telegram topic ID for memory/diff updates | "9" |

**Optional:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| Location | User's city | Derived from timezone |
| Fabric Account ID | Only needed for some API calls | "" |
| Workspace path | OpenClaw workspace location | `~/.openclaw/workspace` |

**How to get Telegram topic IDs:** Open the topic in Telegram Web/Desktop. The URL ends with `/{topic_id}`. The group must have Topics/Forum mode enabled (Group Settings > Topics > On). The user needs to create these topics manually: Discovery, Journal, Booking, Memory.

**How to get Fabric credentials:** The user creates an account at [developer.onfabric.io](https://developer.onfabric.io), follows the Quick Start to connect data sources (Google, Instagram), then finds their API Key, Account ID, and User ID on the dashboard.

### Step 2: Clone This Repo to the Target Machine

```bash
cd /tmp
git clone https://github.com/Eeshita-Pande/openclaw-concierge-template.git
cd openclaw-concierge-template
```

### Step 3: Run the Bootstrap Script

```bash
./bootstrap.sh \
  --agent-name "<AGENT_NAME>" \
  --user-name "<USER_NAME>" \
  --timezone "<TIMEZONE>" \
  --fabric-api-key "<FABRIC_API_KEY>" \
  --fabric-user-id "<FABRIC_USER_ID>" \
  --telegram-group-id "<TELEGRAM_GROUP_ID>" \
  --topic-discovery "<TOPIC_DISCOVERY>" \
  --topic-journal "<TOPIC_JOURNAL>" \
  --topic-booking "<TOPIC_BOOKING>" \
  --topic-memory "<TOPIC_MEMORY>"
```

Add `--fabric-account-id`, `--location`, or `--workspace` if the user provided them.

The bootstrap script will:
1. Create the memory folder structure in the workspace
2. Copy and template-replace workspace files (SOUL.md, IDENTITY.md, USER.md, etc.)
3. Install skills (journal, discovery, fabric, fabric-profile-builder, opentable-booking)
4. Store Fabric credentials securely
5. Bootstrap memory from Fabric API data (interests, restaurants, travel, etc.)
6. Install Chrome + Xvfb for browser automation
7. Create cron jobs (discovery at 6pm, journal at 10pm, fabric-refresh at 9am)
8. Write a post-setup checklist

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
- `evening-discovery` — 6pm daily
- `nightly-journal` — 10pm daily
- `fabric-refresh` — 9am daily

### Step 6: Browser Login for OpenTable (Optional)

If the user wants restaurant booking, they need to log into OpenTable once:

```bash
openclaw browser start
openclaw browser navigate 'https://www.opentable.co.uk/my/profile'
# Then use screenshot + type + click to complete the login flow
openclaw browser screenshot
```

The browser session persists across restarts.

### Step 7: Review USER.md

Open `~/.openclaw/workspace/USER.md` and review the auto-generated profile with the user. Fix anything that's wrong or missing — this file drives journal questions, discovery curation, and booking preferences.

## Troubleshooting

### Cron jobs failed to create
If the gateway wasn't running during bootstrap, create them manually:
```bash
openclaw cron add --name evening-discovery --cron '0 18 * * *' --tz '<TIMEZONE>' --session isolated --message 'Read and follow the discovery skill: skills/discovery/SKILL.md' --announce
openclaw cron add --name nightly-journal --cron '0 22 * * *' --tz '<TIMEZONE>' --session isolated --message 'Read and follow the journal skill: skills/journal/SKILL.md' --announce
openclaw cron add --name fabric-refresh --cron '0 9 * * *' --tz '<TIMEZONE>' --session isolated --message 'Fetch fresh Fabric data. Read skills/fabric/SKILL.md. Source .env.fabric, fetch last 24h, write to memory/fabric-latest.md.'
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
scripts/
  bootstrap-fabric.py           # Initial Fabric data fetch
  fabric-sync.sh                # Daily Fabric sync
  check-regressions.py          # File integrity checks
```
