---
name: fabric
version: 1.0.0
description: Fetch user threads and assets from Fabric API. Google searches, Instagram posts, YouTube activity, and media. Powers the memory system with real context.
---

# Fabric API Skill

Fetch personalized threads and assets from Fabric's context API. Used by daily cron jobs to keep memory files fresh.

## Setup

1. Create an account at [developer.onfabric.io](https://developer.onfabric.io)
2. Follow the [Quick Start guide](https://developer.onfabric.io/quick-start) to:
   - Create an application
   - Connect data sources (Google Chrome, Instagram, etc.)
   - Get your user's consent via the consent flow
3. From the developer dashboard, note:
   - **API Key** — your application's API key
   - **User ID** — the consented user's ID
   - **Account ID** — your developer account ID (optional for basic calls)

4. Store credentials as OpenClaw environment variables:
   ```
   FABRIC_API_KEY=your_api_key
   FABRIC_USER_ID=your_user_id
   FABRIC_ACCOUNT_ID=your_account_id
   ```

---

## API Basics

**Base URL:** `https://api.onfabric.io/api/v1`

**Authentication:** `X-API-Key` header (NOT Bearer token)

---

## Endpoints

### Get Threads

```bash
curl -s "https://api.onfabric.io/api/v1/users/{user_id}/threads" \
  -H "X-API-Key: {api_key}"
```

**Query Parameters:**
- `user_id` (required) — from `$FABRIC_USER_ID`
- `from_date` (optional) — ISO 8601, e.g., `2026-02-17T13:02:14.660Z`
- `to_date` (optional) — ISO 8601
- `page_size` (optional) — results per page (default 10, max 100)
- `page_token` (optional) — for pagination

**Response:**
```json
{
  "items": [
    {
      "id": "thread-uuid",
      "provider": "google|instagram",
      "interaction_type": "google_search|view",
      "preview": "Human-readable preview text",
      "payload": { },
      "is_asset": false,
      "asat": "2026-02-18T12:00:00.000000Z"
    }
  ],
  "next_page_token": "...",
  "has_more": true
}
```

### Get Thread Asset

If a thread has `"is_asset": true`, fetch its media:

```bash
curl -s "https://api.onfabric.io/api/v1/users/{user_id}/threads/{thread_id}/asset" \
  -H "X-API-Key: {api_key}"
```

Returns media URL for download.

---

## Daily Sync (Last 24 Hours)

```bash
FROM_DATE=$(date -u -d '1 day ago' '+%Y-%m-%dT00:00:00.000Z')
TO_DATE=$(date -u '+%Y-%m-%dT00:00:00.000Z')

PAGE_TOKEN=""
while true; do
  if [ -z "$PAGE_TOKEN" ]; then
    RESPONSE=$(curl -s "https://api.onfabric.io/api/v1/users/$FABRIC_USER_ID/threads?from_date=$FROM_DATE&to_date=$TO_DATE&page_size=100" \
      -H "X-API-Key: $FABRIC_API_KEY")
  else
    sleep 0.5
    RESPONSE=$(curl -s "https://api.onfabric.io/api/v1/users/$FABRIC_USER_ID/threads?from_date=$FROM_DATE&to_date=$TO_DATE&page_size=100&page_token=$PAGE_TOKEN" \
      -H "X-API-Key: $FABRIC_API_KEY")
  fi

  # Process items...
  PAGE_TOKEN=$(echo "$RESPONSE" | jq -r '.next_page_token // empty')
  HAS_MORE=$(echo "$RESPONSE" | jq -r '.has_more // false')
  [ "$HAS_MORE" = "false" ] || [ -z "$PAGE_TOKEN" ] && break
done
```

---

## Output

### memory/fabric-latest.md

Summary of last 7 days of activity:

```markdown
# Fabric Data - Latest 7 Days
**Fetched:** 2026-03-24 09:00 UTC
**Period:** 2026-03-17 to 2026-03-24

## Summary
- **Total items:** 10
- **Google searches:** 8
- **Instagram posts/stories:** 2

## Recent Activity

### Google Searches (2026-03-23)
- Topic research (8:04-8:16 AM)
  - Searched: "topic"
  - Related articles read

### YouTube (2026-03-22)
- Followed channel X
- Watched: "Video Title"
```

---

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| 401 | Wrong API key or header format | Check `FABRIC_API_KEY`, use `X-API-Key` not Bearer |
| 404 | Wrong endpoint or IDs | Verify `/api/v1/` in URL, check user_id |
| 429 | Rate limited | Add `sleep 0.5` between requests |
| Empty response | All pages fetched | Check `has_more: false` |
