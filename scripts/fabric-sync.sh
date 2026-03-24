#!/bin/bash
# Daily Fabric sync — fetch last 24h of threads
# Usage: fabric-sync.sh [from_date] [to_date]
# Called by the Fabric Refresh cron job

set -euo pipefail

# Source credentials
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(dirname "$SCRIPT_DIR")"

if [ -f "$WORKSPACE/.env.fabric" ]; then
  source "$WORKSPACE/.env.fabric"
fi

if [ -z "${FABRIC_API_KEY:-}" ] || [ -z "${FABRIC_USER_ID:-}" ]; then
  echo "❌ Missing FABRIC_API_KEY or FABRIC_USER_ID"
  exit 1
fi

FROM_DATE="${1:-$(date -u -d '7 days ago' '+%Y-%m-%dT00:00:00.000Z')}"
TO_DATE="${2:-$(date -u '+%Y-%m-%dT%H:%M:%S.000Z')}"

echo "🔄 Fetching Fabric threads from $FROM_DATE to $TO_DATE..."

ITEMS="[]"
PAGE_TOKEN=""
PAGE=1

while true; do
  PARAMS="from_date=$FROM_DATE&to_date=$TO_DATE&page_size=100"
  [ -n "$PAGE_TOKEN" ] && PARAMS="$PARAMS&page_token=$PAGE_TOKEN"

  RESPONSE=$(curl -sf "https://api.onfabric.io/api/v1/users/$FABRIC_USER_ID/threads?$PARAMS" \
    -H "X-API-Key: $FABRIC_API_KEY" 2>/dev/null) || {
    echo "❌ API request failed on page $PAGE"
    break
  }

  PAGE_ITEMS=$(echo "$RESPONSE" | jq '.items // []')
  COUNT=$(echo "$PAGE_ITEMS" | jq 'length')
  ITEMS=$(echo "$ITEMS $PAGE_ITEMS" | jq -s '.[0] + .[1]')

  echo "  📄 Page $PAGE: $COUNT items"

  PAGE_TOKEN=$(echo "$RESPONSE" | jq -r '.next_page_token // empty')
  HAS_MORE=$(echo "$RESPONSE" | jq -r '.has_more // false')

  [ "$HAS_MORE" = "false" ] || [ -z "$PAGE_TOKEN" ] && break
  PAGE=$((PAGE + 1))
  sleep 0.3
done

TOTAL=$(echo "$ITEMS" | jq 'length')
echo "✅ Total items fetched: $TOTAL"

# Write summary to memory/fabric-latest.md
OUTFILE="$WORKSPACE/memory/fabric-latest.md"

cat > "$OUTFILE" <<EOF
# Fabric Data - Latest 7 Days
**Fetched:** $(date -u '+%Y-%m-%d %H:%M') UTC
**Period:** $(echo "$FROM_DATE" | cut -dT -f1) to $(echo "$TO_DATE" | cut -dT -f1)

## Summary
- **Total items:** $TOTAL
$(echo "$ITEMS" | jq -r '[.[].provider] | group_by(.) | map("- **\(.[0] | ascii_upcase):** \(length)") | .[]')

## Recent Activity

$(echo "$ITEMS" | jq -r '.[:20][] | "- \(.preview // "No preview") [\(.asat // "" | split("T")[0])]"')

## Full JSON Data

$(echo "$ITEMS" | jq '.')
EOF

echo "📝 Written to $OUTFILE"
