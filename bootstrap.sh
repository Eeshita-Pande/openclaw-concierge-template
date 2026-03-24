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
[ -z "$TELEGRAM_GROUP_ID" ] && MISSING+=("--telegram-group-id")
[ -z "$TOPIC_DISCOVERY" ] && MISSING+=("--topic-discovery")
[ -z "$TOPIC_JOURNAL" ] && MISSING+=("--topic-journal")
[ -z "$TOPIC_BOOKING" ] && MISSING+=("--topic-booking")
[ -z "$TOPIC_MEMORY" ] && MISSING+=("--topic-memory")

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
  echo "  --fabric-user-id \"usr_xxx\" \\"
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

echo -e "${YELLOW}[1/6] Creating memory folder structure...${NC}"

mkdir -p "$WORKSPACE/memory/$USER_SLUG"
mkdir -p "$WORKSPACE/memory/$AGENT_SLUG/discoveries"
mkdir -p "$WORKSPACE/memory/$AGENT_SLUG/bookings"
mkdir -p "$WORKSPACE/memory/shared/daily"
mkdir -p "$WORKSPACE/memory/shared/diffs"
mkdir -p "$WORKSPACE/memory/shared/diffs/applied"
mkdir -p "$WORKSPACE/memory/topics"
mkdir -p "$WORKSPACE/memory/instagram"
mkdir -p "$WORKSPACE/scripts"

echo -e "  ${GREEN}✓${NC} memory/$USER_SLUG/"
echo -e "  ${GREEN}✓${NC} memory/$AGENT_SLUG/discoveries/"
echo -e "  ${GREEN}✓${NC} memory/$AGENT_SLUG/bookings/"
echo -e "  ${GREEN}✓${NC} memory/shared/daily/"
echo -e "  ${GREEN}✓${NC} memory/shared/diffs/"
echo -e "  ${GREEN}✓${NC} memory/topics/"
echo -e "  ${GREEN}✓${NC} memory/instagram/"

# ─── Step 2: Copy & Replace Template Files ───────────────────────

echo ""
echo -e "${YELLOW}[2/6] Copying template files...${NC}"

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
echo -e "${YELLOW}[3/6] Installing skills...${NC}"

# Copy bundled skills
for skill_dir in "$SCRIPT_DIR/skills"/*/; do
  skill_name=$(basename "$skill_dir")
  mkdir -p "$WORKSPACE/skills/$skill_name"
  cp -r "$skill_dir"* "$WORKSPACE/skills/$skill_name/"
  echo -e "  ${GREEN}✓${NC} skills/$skill_name/"
done

# Install ClawHub skills if clawhub CLI is available
if command -v clawhub &>/dev/null; then
  echo -e "  Installing from ClawHub..."
  (cd "$WORKSPACE" && clawhub install restaurant-booking-opentable 2>/dev/null) && \
    echo -e "  ${GREEN}✓${NC} restaurant-booking-opentable (ClawHub)" || \
    echo -e "  ${YELLOW}⚠${NC} restaurant-booking-opentable (install failed — install manually later)"
else
  echo -e "  ${YELLOW}⚠${NC} clawhub CLI not found — install restaurant-booking-opentable manually:"
  echo "    npm i -g clawhub && cd $WORKSPACE && clawhub install restaurant-booking-opentable"
fi

# ─── Step 4: Store Fabric Credentials ───────────────────────────

echo ""
echo -e "${YELLOW}[4/6] Storing Fabric credentials...${NC}"

cat > "$WORKSPACE/.env.fabric" <<EOF
FABRIC_API_KEY=$FABRIC_API_KEY
FABRIC_ACCOUNT_ID=${FABRIC_ACCOUNT_ID:-}
FABRIC_USER_ID=$FABRIC_USER_ID
EOF
chmod 600 "$WORKSPACE/.env.fabric"
echo -e "  ${GREEN}✓${NC} .env.fabric (chmod 600)"

# ─── Step 5: Bootstrap from Fabric Data ─────────────────────────

echo ""
echo -e "${YELLOW}[5/6] Bootstrapping memory from Fabric data...${NC}"

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

# ─── Step 6: Create Cron Jobs ───────────────────────────────────

echo ""
echo -e "${YELLOW}[6/6] Creating cron jobs...${NC}"
echo -e "  ${BLUE}ℹ${NC}  Cron jobs are created via OpenClaw — run these commands after starting your gateway:"
echo ""

DELIVERY_DISCOVERY="${TELEGRAM_GROUP_ID}:topic:${TOPIC_DISCOVERY}"
DELIVERY_JOURNAL="${TELEGRAM_GROUP_ID}:topic:${TOPIC_JOURNAL}"
DELIVERY_BOOKING="${TELEGRAM_GROUP_ID}:topic:${TOPIC_BOOKING}"
DELIVERY_MEMORY="${TELEGRAM_GROUP_ID}:topic:${TOPIC_MEMORY}"

cat > "$WORKSPACE/setup-crons.md" <<EOF
# Cron Jobs to Create

Run these in a chat session with your agent, or use the OpenClaw TUI.

## 1. Evening Journal (9pm daily)
Create a cron job:
- **Name:** Evening Journal Reflection
- **Schedule:** \`0 21 * * *\` (${TIMEZONE})
- **Session:** isolated
- **Model:** anthropic/claude-sonnet-4-5
- **Delivery:** announce → telegram → \`${DELIVERY_JOURNAL}\`
- **Payload:**
\`\`\`
Evening journal reflection for ${USER_NAME}. Read \`skills/journal/SKILL.md\` and follow it.

⚠️ OUTPUT RULE: Your entire response must be the final message only — observation + question + closing line. No analysis, no bullet points, no reasoning, no preamble.

Read these files for context:
- memory/shared/daily/YYYY-MM-DD.md (today + past 3 days)
- memory/fabric-latest.md
- memory/${USER_SLUG}/travel.md
- memory/${USER_SLUG}/work.md
- memory/${USER_SLUG}/interests.md
- USER.md

Then output the reflection. Nothing else.
\`\`\`

## 2. Evening Discoveries (7pm daily)
- **Name:** Evening Discoveries
- **Schedule:** \`0 19 * * *\` (${TIMEZONE})
- **Session:** isolated
- **Model:** anthropic/claude-sonnet-4-5
- **Delivery:** announce → telegram → \`${DELIVERY_DISCOVERY}\`
- **Payload:**
\`\`\`
Find 1–2 discoveries for ${USER_NAME}. Read \`skills/discovery/SKILL.md\` and follow it exactly.
Do all context reading and dedup checks as described in the skill, then output the final message only.
\`\`\`

## 3. Fabric Data Refresh (9am daily)
- **Name:** Refresh Fabric Data
- **Schedule:** \`0 9 * * *\` (${TIMEZONE})
- **Session:** isolated
- **Delivery:** none
- **Payload:**
\`\`\`
Fetch fresh data from Fabric API. Read \`skills/fabric/SKILL.md\` for API reference.

Source credentials from .env.fabric, fetch last 24h of threads, and write summary to memory/fabric-latest.md.
Include: total items, provider breakdown, notable searches/activity.
\`\`\`

## 4. Fabric Diff Report (10am daily)
- **Name:** Fabric + Memory Daily Diff
- **Schedule:** \`5 10 * * *\` (${TIMEZONE})
- **Session:** isolated
- **Delivery:** announce → telegram → \`${DELIVERY_MEMORY}\`
- **Payload:**
\`\`\`
Generate a daily diff from Fabric data.

Read memory/fabric-latest.md and compare against memory/${USER_SLUG}/ files.
Route new items to the correct topic file:
- Travel → memory/${USER_SLUG}/travel.md
- Restaurants → memory/${USER_SLUG}/restaurants.md
- Work/Tech → memory/${USER_SLUG}/work.md
- Interests → memory/${USER_SLUG}/interests.md

Write proposed changes to memory/shared/diffs/fabric-YYYY-MM-DD.md.
Auto-approve after 24h if no objection.
\`\`\`

## 5. Weekly Restaurant Booking (Monday 8pm)
- **Name:** Weekly Restaurant Booking
- **Schedule:** \`0 20 * * 1\` (${TIMEZONE})
- **Session:** isolated
- **Model:** anthropic/claude-sonnet-4-5
- **Delivery:** announce → telegram → \`${DELIVERY_BOOKING}\`
- **Payload:**
\`\`\`
Weekly dinner booking. Read \`skills/restaurant-booking-opentable/SKILL.md\` if available.
Book the next unbooked Saturday for party of 2 around 20:30.
Check memory/${USER_SLUG}/restaurants.md for preferences and USER.md for location.
\`\`\`
EOF

echo -e "  ${GREEN}✓${NC} setup-crons.md — cron job definitions written"
echo -e "  ${BLUE}ℹ${NC}  Ask your agent to read setup-crons.md and create the jobs"

# ─── Done ────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Setup Complete! 🎉              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Workspace: ${BLUE}$WORKSPACE${NC}"
echo ""
echo -e "  ${YELLOW}Next steps:${NC}"
echo -e "  1. Review ${BLUE}$WORKSPACE/USER.md${NC} — fix anything the Fabric bootstrap got wrong"
echo -e "  2. Edit ${BLUE}$WORKSPACE/SOUL.md${NC} — give your agent personality"
echo -e "  3. Start OpenClaw: ${BLUE}openclaw gateway start${NC}"
echo -e "  4. Tell your agent: ${BLUE}\"Read setup-crons.md and create all the cron jobs\"${NC}"
echo -e "  5. Tonight: first journal at 9pm, first discoveries at 7pm"
echo ""
