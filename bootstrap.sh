#!/bin/bash
set -euo pipefail

# OpenClaw Starter Template — Bootstrap Script
# Usage: ./bootstrap.sh --agent-name "Luna" --user-name "Sarah" --timezone "America/New_York" ...

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ─── Parse Arguments ──────────────────────────────────────────────

AGENT_NAME=""
USER_NAME=""
TIMEZONE=""
LOCATION=""
FABRIC_API_KEY=""
FABRIC_ACCOUNT_ID=""
FABRIC_USER_ID=""
TELEGRAM_GROUP_ID=""
TOPIC_DISCOVERY=""
TOPIC_JOURNAL=""
TOPIC_BOOKING=""
TOPIC_MEMORY=""
WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"

while [[ $# -gt 0 ]]; do
  case $1 in
    --agent-name) AGENT_NAME="$2"; shift 2 ;;
    --user-name) USER_NAME="$2"; shift 2 ;;
    --timezone) TIMEZONE="$2"; shift 2 ;;
    --location) LOCATION="$2"; shift 2 ;;
    --fabric-api-key) FABRIC_API_KEY="$2"; shift 2 ;;
    --fabric-account-id) FABRIC_ACCOUNT_ID="$2"; shift 2 ;;
    --fabric-user-id) FABRIC_USER_ID="$2"; shift 2 ;;
    --telegram-group-id) TELEGRAM_GROUP_ID="$2"; shift 2 ;;
    --topic-discovery) TOPIC_DISCOVERY="$2"; shift 2 ;;
    --topic-journal) TOPIC_JOURNAL="$2"; shift 2 ;;
    --topic-booking) TOPIC_BOOKING="$2"; shift 2 ;;
    --topic-memory) TOPIC_MEMORY="$2"; shift 2 ;;
    --workspace) WORKSPACE="$2"; shift 2 ;;
    *) echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
  esac
done

# ─── Validate Required Args ──────────────────────────────────────

MISSING=()
[ -z "$AGENT_NAME" ] && MISSING+=("--agent-name")
[ -z "$USER_NAME" ] && MISSING+=("--user-name")
[ -z "$TIMEZONE" ] && MISSING+=("--timezone")
[ -z "$FABRIC_API_KEY" ] && MISSING+=("--fabric-api-key")
[ -z "$FABRIC_USER_ID" ] && MISSING+=("--fabric-user-id")

if [ ${#MISSING[@]} -gt 0 ]; then
  echo -e "${RED}Missing required arguments:${NC}"
  for m in "${MISSING[@]}"; do echo "  $m"; done
  echo ""
  echo "Usage: ./bootstrap.sh \\"
  echo "  --agent-name \"Luna\" \\"
  echo "  --user-name \"Sarah\" \\"
  echo "  --timezone \"America/New_York\" \\"
  echo "  --location \"New York\" \\"
  echo "  --fabric-api-key \"fab_xxx\" \\"
  echo "  --fabric-account-id \"acc_xxx\" \\"
  echo "  --fabric-user-id \"usr_xxx\""
  echo ""
  echo "Optional Telegram flags:"
  echo "  --telegram-group-id \"-100xxxxxxxxxx\" \\"
  echo "  --topic-discovery \"3\" \\"
  echo "  --topic-journal \"5\" \\"
  echo "  --topic-booking \"7\" \\"
  echo "  --topic-memory \"9\""
  exit 1
fi

# Derive slugs (lowercase, hyphens)
USER_SLUG=$(echo "$USER_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
AGENT_SLUG=$(echo "$AGENT_NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
SETUP_DATE=$(date -u '+%Y-%m-%d')
LOCATION="${LOCATION:-$(echo "$TIMEZONE" | sed 's|.*/||' | tr '_' ' ')}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     OpenClaw Starter Template — Bootstrap    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Agent:     ${GREEN}$AGENT_NAME${NC} ($AGENT_SLUG)"
echo -e "  User:      ${GREEN}$USER_NAME${NC} ($USER_SLUG)"
echo -e "  Timezone:  ${GREEN}$TIMEZONE${NC}"
echo -e "  Location:  ${GREEN}$LOCATION${NC}"
echo -e "  Workspace: ${GREEN}$WORKSPACE${NC}"
echo ""

# ─── Step 1: Create Memory Folder Structure ──────────────────────

echo -e "${YELLOW}[1/8] Creating memory folder structure...${NC}"

mkdir -p "$WORKSPACE/memory/$USER_SLUG"
mkdir -p "$WORKSPACE/memory/$AGENT_SLUG/discoveries"
mkdir -p "$WORKSPACE/memory/$AGENT_SLUG/bookings"
mkdir -p "$WORKSPACE/memory/shared/daily"
mkdir -p "$WORKSPACE/memory/shared/diffs"
mkdir -p "$WORKSPACE/memory/shared/diffs/applied"
mkdir -p "$WORKSPACE/memory/topics"
mkdir -p "$WORKSPACE/memory/instagram"
mkdir -p "$WORKSPACE/scripts"

# Create empty fabric-latest.md
touch "$WORKSPACE/memory/fabric-latest.md"

echo -e "  ${GREEN}✓${NC} memory/$USER_SLUG/"
echo -e "  ${GREEN}✓${NC} memory/$AGENT_SLUG/discoveries/"
echo -e "  ${GREEN}✓${NC} memory/$AGENT_SLUG/bookings/"
echo -e "  ${GREEN}✓${NC} memory/shared/daily/"
echo -e "  ${GREEN}✓${NC} memory/shared/diffs/"
echo -e "  ${GREEN}✓${NC} memory/topics/"
echo -e "  ${GREEN}✓${NC} memory/instagram/"
echo -e "  ${GREEN}✓${NC} memory/fabric-latest.md"

# ─── Step 2: Copy & Replace Template Files ───────────────────────

echo ""
echo -e "${YELLOW}[2/8] Copying template files...${NC}"

TEMPLATES=(SOUL.md IDENTITY.md USER.md AGENTS.md MEMORY.md HEARTBEAT.md TOOLS.md)

for tmpl in "${TEMPLATES[@]}"; do
  if [ -f "$SCRIPT_DIR/templates/$tmpl" ]; then
    sed \
      -e "s|{{agent_name}}|$AGENT_NAME|g" \
      -e "s|{{agent_slug}}|$AGENT_SLUG|g" \
      -e "s|{{user_name}}|$USER_NAME|g" \
      -e "s|{{user_slug}}|$USER_SLUG|g" \
      -e "s|{{timezone}}|$TIMEZONE|g" \
      -e "s|{{location}}|$LOCATION|g" \
      -e "s|{{setup_date}}|$SETUP_DATE|g" \
      -e "s|{{telegram_group_id}}|$TELEGRAM_GROUP_ID|g" \
      -e "s|{{topic_discovery}}|$TOPIC_DISCOVERY|g" \
      -e "s|{{topic_journal}}|$TOPIC_JOURNAL|g" \
      -e "s|{{topic_booking}}|$TOPIC_BOOKING|g" \
      -e "s|{{topic_memory}}|$TOPIC_MEMORY|g" \
      "$SCRIPT_DIR/templates/$tmpl" > "$WORKSPACE/$tmpl"
    echo -e "  ${GREEN}✓${NC} $tmpl"
  fi
done

# ─── Step 3: Install Skills ─────────────────────────────────────

echo ""
echo -e "${YELLOW}[3/8] Installing skills...${NC}"

# Copy bundled skills
for skill_dir in "$SCRIPT_DIR/skills"/*/; do
  skill_name=$(basename "$skill_dir")
  mkdir -p "$WORKSPACE/skills/$skill_name"
  cp -r "$skill_dir"* "$WORKSPACE/skills/$skill_name/"
  echo -e "  ${GREEN}✓${NC} skills/$skill_name/"
done

# ─── Step 4: Store Fabric Credentials ───────────────────────────

echo ""
echo -e "${YELLOW}[4/8] Storing Fabric credentials...${NC}"

cat > "$WORKSPACE/.env.fabric" <<EOF
FABRIC_API_KEY=$FABRIC_API_KEY
FABRIC_ACCOUNT_ID=${FABRIC_ACCOUNT_ID:-}
FABRIC_USER_ID=$FABRIC_USER_ID
EOF
chmod 600 "$WORKSPACE/.env.fabric"
echo -e "  ${GREEN}✓${NC} .env.fabric (chmod 600)"

# ─── Step 5: Bootstrap from Fabric Data ─────────────────────────

echo ""
echo -e "${YELLOW}[5/8] Bootstrapping memory from Fabric data...${NC}"

if [ -f "$SCRIPT_DIR/scripts/bootstrap-fabric.py" ]; then
  python3 "$SCRIPT_DIR/scripts/bootstrap-fabric.py" \
    --api-key "$FABRIC_API_KEY" \
    --user-id "$FABRIC_USER_ID" \
    --user-name "$USER_NAME" \
    --user-slug "$USER_SLUG" \
    --workspace "$WORKSPACE" \
    --timezone "$TIMEZONE" \
    --location "$LOCATION" && \
    echo -e "  ${GREEN}✓${NC} Memory files generated from Fabric data" || \
    echo -e "  ${YELLOW}⚠${NC} Fabric bootstrap failed — memory files will be empty stubs"
else
  echo -e "  ${YELLOW}⚠${NC} bootstrap-fabric.py not found — creating empty memory stubs"
  for f in interests.md restaurants.md fashion.md travel.md relationships.md work.md; do
    title=$(echo "$f" | sed 's/.md//' | sed 's/^./\U&/')
    echo "# $title" > "$WORKSPACE/memory/$USER_SLUG/$f"
    echo "" >> "$WORKSPACE/memory/$USER_SLUG/$f"
    echo "(To be populated from Fabric data or manually)" >> "$WORKSPACE/memory/$USER_SLUG/$f"
  done
  # Also create topic dedup files
  for f in food.md lifestyle.md travel.md interests.md; do
    title=$(echo "$f" | sed 's/.md//' | sed 's/^./\U&/')
    echo "# $title" > "$WORKSPACE/memory/topics/$f"
  done
fi

# ─── Step 6: Install Browser (Chrome + Xvfb) ────────────────────

echo ""
echo -e "${YELLOW}[6/8] Setting up browser (Chrome + Xvfb)...${NC}"

# Install Xvfb if not present
if ! command -v Xvfb &>/dev/null; then
  echo -e "  Installing Xvfb..."
  sudo apt-get update -qq >/dev/null 2>&1
  sudo apt-get install -y -qq xvfb >/dev/null 2>&1
  echo -e "  ${GREEN}✓${NC} Xvfb installed"
else
  echo -e "  ${GREEN}✓${NC} Xvfb already installed"
fi

# Install Google Chrome if not present
if ! command -v google-chrome &>/dev/null; then
  echo -e "  Installing Google Chrome..."
  TMPCHROME=$(mktemp /tmp/chrome-XXXXXX.deb)
  curl -sL 'https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb' -o "$TMPCHROME"
  sudo apt-get install -y -qq "$TMPCHROME" >/dev/null 2>&1
  rm -f "$TMPCHROME"
  echo -e "  ${GREEN}✓${NC} Google Chrome installed ($(google-chrome --version 2>/dev/null | head -1))"
else
  echo -e "  ${GREEN}✓${NC} Google Chrome already installed ($(google-chrome --version 2>/dev/null | head -1))"
fi

# Create Xvfb systemd user service
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"

if [ ! -f "$SYSTEMD_USER_DIR/xvfb.service" ]; then
  cat > "$SYSTEMD_USER_DIR/xvfb.service" <<'XVFB_EOF'
[Unit]
Description=Xvfb Virtual Framebuffer

[Service]
ExecStart=/usr/bin/Xvfb :99 -screen 0 1920x1080x24
Restart=always
RestartSec=2

[Install]
WantedBy=default.target
XVFB_EOF
  systemctl --user daemon-reload
  systemctl --user enable --now xvfb.service >/dev/null 2>&1
  echo -e "  ${GREEN}✓${NC} xvfb.service created and started"
else
  # Ensure it's running
  systemctl --user start xvfb.service 2>/dev/null || true
  echo -e "  ${GREEN}✓${NC} xvfb.service already configured"
fi

# Add DISPLAY=:99 to gateway service via drop-in
GATEWAY_DROPIN_DIR="$SYSTEMD_USER_DIR/openclaw-gateway.service.d"
mkdir -p "$GATEWAY_DROPIN_DIR"

if [ ! -f "$GATEWAY_DROPIN_DIR/display.conf" ]; then
  cat > "$GATEWAY_DROPIN_DIR/display.conf" <<'DISPLAY_EOF'
[Unit]
After=xvfb.service
Wants=xvfb.service

[Service]
Environment=DISPLAY=:99
DISPLAY_EOF
  systemctl --user daemon-reload
  echo -e "  ${GREEN}✓${NC} Gateway DISPLAY=:99 drop-in created"
  echo -e "  ${YELLOW}⚠${NC} Restart the gateway to pick up DISPLAY: systemctl --user restart openclaw-gateway.service"
else
  echo -e "  ${GREEN}✓${NC} Gateway DISPLAY drop-in already exists"
fi

# ─── Step 7: Create Cron Jobs ───────────────────────────────────

echo ""
echo -e "${YELLOW}[7/8] Creating cron jobs...${NC}"

# Check if openclaw CLI is available
if command -v openclaw &>/dev/null; then
  OPENCLAW_CMD="openclaw"
elif [ -f "$HOME/.local/share/fnm/node-versions/v24.14.1/installation/bin/openclaw" ]; then
  OPENCLAW_CMD="$HOME/.local/share/fnm/node-versions/v24.14.1/installation/bin/openclaw"
else
  OPENCLAW_CMD=""
fi

if [ -n "$OPENCLAW_CMD" ]; then
  # Wait for gateway to be healthy
  echo -e "  Waiting for gateway..."
  for i in $(seq 1 10); do
    if curl -s http://127.0.0.1:18789/health >/dev/null 2>&1; then
      break
    fi
    sleep 2
  done

  # Build announce flag if Telegram is configured
  ANNOUNCE_FLAG=""
  if [ -n "$TELEGRAM_GROUP_ID" ]; then
    ANNOUNCE_FLAG="--announce"
  fi

  # Evening discovery — 6pm daily
  $OPENCLAW_CMD cron add \
    --name "evening-discovery" \
    --cron "0 18 * * *" \
    --tz "$TIMEZONE" \
    --session isolated \
    --message "Read and follow the discovery skill: skills/discovery/SKILL.md" \
    $ANNOUNCE_FLAG >/dev/null 2>&1 && \
    echo -e "  ${GREEN}✓${NC} evening-discovery (6pm $TIMEZONE)" || \
    echo -e "  ${YELLOW}⚠${NC} evening-discovery — failed (create manually)"

  # Nightly journal — 10pm daily
  $OPENCLAW_CMD cron add \
    --name "nightly-journal" \
    --cron "0 22 * * *" \
    --tz "$TIMEZONE" \
    --session isolated \
    --message "Read and follow the journal skill: skills/journal/SKILL.md" \
    $ANNOUNCE_FLAG >/dev/null 2>&1 && \
    echo -e "  ${GREEN}✓${NC} nightly-journal (10pm $TIMEZONE)" || \
    echo -e "  ${YELLOW}⚠${NC} nightly-journal — failed (create manually)"

  # Fabric data refresh — 9am daily
  $OPENCLAW_CMD cron add \
    --name "fabric-refresh" \
    --cron "0 9 * * *" \
    --tz "$TIMEZONE" \
    --session isolated \
    --message "Fetch fresh data from Fabric API. Read skills/fabric/SKILL.md for API reference. Source credentials from .env.fabric, fetch last 24h of threads, and write summary to memory/fabric-latest.md." >/dev/null 2>&1 && \
    echo -e "  ${GREEN}✓${NC} fabric-refresh (9am $TIMEZONE)" || \
    echo -e "  ${YELLOW}⚠${NC} fabric-refresh — failed (create manually)"

  # Weekly booking check — Sunday noon
  $OPENCLAW_CMD cron add \
    --name "weekly-booking-check" \
    --cron "0 12 * * 0" \
    --tz "$TIMEZONE" \
    --session isolated \
    --message "Check if there are any upcoming dining plans or booking requests. Read skills/opentable-booking/SKILL.md for booking flow." \
    $ANNOUNCE_FLAG >/dev/null 2>&1 && \
    echo -e "  ${GREEN}✓${NC} weekly-booking-check (Sunday noon $TIMEZONE)" || \
    echo -e "  ${YELLOW}⚠${NC} weekly-booking-check — failed (create manually)"

else
  echo -e "  ${YELLOW}⚠${NC} openclaw CLI not found — cron jobs must be created manually"
  echo -e "  ${BLUE}ℹ${NC}  After starting the gateway, run:"
  echo "    openclaw cron add --name evening-discovery --cron '0 18 * * *' --tz '$TIMEZONE' --session isolated --message 'Read and follow the discovery skill: skills/discovery/SKILL.md' --announce"
  echo "    openclaw cron add --name nightly-journal --cron '0 22 * * *' --tz '$TIMEZONE' --session isolated --message 'Read and follow the journal skill: skills/journal/SKILL.md' --announce"
  echo "    openclaw cron add --name fabric-refresh --cron '0 9 * * *' --tz '$TIMEZONE' --session isolated --message 'Fetch fresh Fabric data. Read skills/fabric/SKILL.md. Source .env.fabric, fetch last 24h, write to memory/fabric-latest.md.'"
  echo "    openclaw cron add --name weekly-booking-check --cron '0 12 * * 0' --tz '$TIMEZONE' --session isolated --message 'Check if there are any upcoming dining plans or booking requests. Read skills/opentable-booking/SKILL.md for booking flow.'"
fi

# ─── Step 8: Post-setup Login Reminder ──────────────────────────

echo ""
echo -e "${YELLOW}[8/8] Post-setup checklist...${NC}"

cat > "$WORKSPACE/setup-checklist.md" <<CHECKLIST_EOF
# Post-Bootstrap Checklist

## Browser Login (one-time)

The OpenTable booking skill requires an authenticated browser session.
After the gateway is running with DISPLAY=:99:

1. Start the browser: \`openclaw browser start\`
2. Navigate to OpenTable: \`openclaw browser navigate 'https://www.opentable.co.uk/my/profile'\`
3. Use the email login flow (screenshot + type + click via \`openclaw browser\` commands)
4. Verify login: \`openclaw browser screenshot\`
5. Ensure a payment card is saved in the OpenTable account

The session persists in the \`openclaw\` browser profile — this only needs to be done once.

## Verify Cron Jobs

\`\`\`
openclaw cron list
\`\`\`

Expected:
- evening-discovery (6pm ${TIMEZONE})
- nightly-journal (10pm ${TIMEZONE})
- fabric-refresh (9am ${TIMEZONE})
- weekly-booking-check (Sunday noon ${TIMEZONE})

## Review USER.md

Check that the Fabric bootstrap generated a reasonable profile.
Fill in any missing fields (name, timezone, location).
CHECKLIST_EOF

echo -e "  ${GREEN}✓${NC} setup-checklist.md written"

# ─── Done ────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Setup Complete!                 ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Workspace: ${BLUE}$WORKSPACE${NC}"
echo ""
echo -e "  ${YELLOW}Next steps:${NC}"
echo -e "  1. Restart the gateway: ${BLUE}systemctl --user restart openclaw-gateway.service${NC}"
echo -e "  2. Start the browser: ${BLUE}openclaw browser start${NC}"
echo -e "  3. Log into OpenTable (see ${BLUE}setup-checklist.md${NC})"
echo -e "  4. Review ${BLUE}$WORKSPACE/USER.md${NC}"
echo -e "  5. Edit ${BLUE}$WORKSPACE/SOUL.md${NC} — give your agent personality"
echo -e "  6. Tonight: first discoveries at 6pm, first journal at 10pm"
echo ""
