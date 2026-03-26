# OpenClaw Concierge Template

A template for setting up a personal AI concierge powered by [OpenClaw](https://docs.openclaw.ai). Point Claude at this repo and it will set up the full system for you.

**For Claude: read `CLAUDE.md` for setup instructions.**

## What You Get

| Feature | What it does | Schedule |
|---------|-------------|----------|
| **Journal** | One sharp observation + question based on your recent activity | 10pm daily |
| **Discovery** | 1-2 curated finds (restaurants, articles, fashion, travel) | 6pm daily |
| **Restaurant Booking** | Automated OpenTable reservations via browser automation | On demand |
| **Fabric Sync** | Pulls your Google searches, Instagram, YouTube into memory | 9am daily |

All outputs are delivered to organized Telegram group topics.

## Prerequisites

1. **OpenClaw** installed and running ([docs.openclaw.ai](https://docs.openclaw.ai))
2. **Fabric account** with API credentials ([developer.onfabric.io](https://developer.onfabric.io))
3. **Telegram bot** connected to OpenClaw
4. **Telegram group** with forum/topics enabled (your agent's home base)

---

## Setup

### Step 1: Fabric Credentials

1. Create an account at [developer.onfabric.io](https://developer.onfabric.io)
2. Follow the [Quick Start guide](https://developer.onfabric.io/quick-start) to connect your data sources (Google, Instagram)
3. Note your **API Key**, **Account ID**, and **User ID** from the dashboard

### Step 2: Telegram Group Topics

Create a Telegram group with **Topics enabled** (Group Settings → Topics → On).

Create these 5 topics manually:
- **General** (default topic — no ID needed)
- **Discovery** — curated finds land here
- **Journal** — evening reflections
- **Booking** — restaurant booking confirmations
- **Memory** — Fabric diffs and memory updates

To get each topic ID: open the topic in Telegram Web/Desktop, look at the URL — it ends with `/{topic_id}`.

### Step 3: Run Bootstrap

```bash
git clone https://github.com/Eeshita-Pande/openclaw-concierge-template.git
cd openclaw-concierge-template

./bootstrap.sh \
  --agent-name "Luna" \
  --user-name "Sarah" \
  --timezone "America/New_York" \
  --fabric-api-key "fab_xxx" \
  --fabric-account-id "acc_xxx" \
  --fabric-user-id "usr_xxx" \
  --telegram-group-id "-100xxxxxxxxxx" \
  --topic-discovery "3" \
  --topic-journal "5" \
  --topic-booking "7" \
  --topic-memory "9"
```

This will:
1. Copy template files into your OpenClaw workspace
2. Replace all placeholders with your details
3. Pull your Fabric data and generate memory files + `USER.md`
4. Install skills (journal, discovery, fabric, opentable-booking)
5. Set up Chrome + Xvfb for browser automation
6. Create cron jobs (discovery 6pm, journal 10pm, fabric-refresh 9am)
7. Write a post-setup checklist

### Step 4: Review USER.md

The bootstrap generates `USER.md` from your Fabric data — your interests, places, people, work context. **Review it for 5 minutes** and fix anything that's wrong or missing. This file drives everything — discoveries, journal questions, booking preferences.

### Step 5: Post-Setup

1. Restart the gateway: `systemctl --user restart openclaw-gateway.service`
2. Verify crons: `openclaw cron list`
3. Log into OpenTable via browser if you want restaurant booking (see `setup-checklist.md`)

Your agent is live. Tonight you'll get your first discoveries at 6pm and journal reflection at 10pm.

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
│   └── opentable-booking/  # OpenTable booking (from ClawHub)
│
├── memory/
│   ├── {user}/          # Your ground truth (from Fabric)
│   │   ├── interests.md
│   │   ├── restaurants.md
│   │   ├── fashion.md
│   │   ├── travel.md
│   │   ├── relationships.md
│   │   └── work.md
│   ├── {agent}/         # Agent's autonomous work
│   │   ├── discoveries/
│   │   └── bookings/
│   ├── shared/
│   │   ├── daily/       # Session logs
│   │   └── diffs/       # Fabric update proposals
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
| `opentable-booking` | ClawHub | OpenTable browser automation |

## License

MIT
