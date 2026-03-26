# Fabric API Thread Schemas

## Common Thread Structure

```json
{
  "id": "uuid",
  "provider": "google|instagram",
  "interaction_type": "google_youtube|google_search|instagram_stories|...",
  "preview": "Human-readable summary",
  "payload": { ... },
  "version": "1.0.7",
  "asat": "2026-03-24T19:50:27.983000",
  "is_asset": false,
  "asset_description": null
}
```

## Interaction Types

| Type | Provider | Content | Has Media |
|------|----------|---------|-----------|
| `google_youtube` | Google | YouTube video views/likes | No |
| `google_search` | Google | Search queries + clicked results | No |
| `google_discover` | Google | Discover feed interactions | No |
| `google_image_search` | Google | Image search queries | No |
| `google_video_search` | Google | Video search queries | No |
| `google_shopping` | Google | Shopping searches + product views | No |
| `google_lens` | Google | Google Lens lookups | No |
| `instagram_stories` | Instagram | Stories posted by user | Yes |
| `instagram_posts` | Instagram | Posts shared by user | Yes |

## Payload by Type

### google_youtube
```json
{
  "type": "View|Like",
  "object": {
    "url": "https://www.youtube.com/watch?v=...",
    "name": "Video title",
    "type": "Video",
    "attributedTo": { "url": "...", "name": "Creator Name", "type": "Profile" }
  },
  "fibreKind": "View|Reaction",
  "published": "2026-03-24T19:50:27.983000Z"
}
```

### google_search
```json
{
  "type": "Search",
  "object": { "url": "https://www.google.com/search?q=...", "name": "query text", "type": "SearchQuery" },
  "fibreKind": "Search",
  "published": "2026-03-24T12:00:00.000000Z"
}
```

### instagram_stories / instagram_posts
```json
{
  "type": "Create",
  "object": { "url": "https://www.instagram.com/p/...", "name": "Caption text", "type": "Image|Video" },
  "fibreKind": "Create",
  "published": "2026-01-15T10:30:00.000000Z"
}
```
- `is_asset` = true, `asset_description` may contain AI-generated visual description
- Media via `GET /users/{user_id}/threads/{thread_id}/asset`

### google_shopping / google_discover / google_image_search / google_lens / google_video_search
Same structure as `google_search` with `object.name` containing query/item name.

## Signal Value by Source

| Data Type | Best For | Weaker For |
|-----------|----------|------------|
| YouTube | Entertainment, values, work, hobbies | Relationships, shopping |
| Google Search | Shopping, health, travel, immediate needs | Long-term values |
| Google Shopping | Shopping, brands | Everything else |
| Instagram Stories | Relationships, travel, food, lifestyle | Work, deep interests |
| Instagram Posts | Identity, travel, relationships | Work, health |
| Google Discover | News, values, passive consumption | Active interests |
