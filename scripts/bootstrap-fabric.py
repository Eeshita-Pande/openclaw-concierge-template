#!/usr/bin/env python3
"""
Bootstrap memory files from Fabric API data.

Pulls all available threads for a user, categorizes them, and generates:
- memory/{user}/interests.md
- memory/{user}/restaurants.md
- memory/{user}/fashion.md
- memory/{user}/travel.md
- memory/{user}/relationships.md
- memory/{user}/work.md
- memory/topics/food.md
- memory/topics/interests.md
- memory/topics/lifestyle.md
- memory/topics/travel.md
- memory/fabric-latest.md (last 7 days summary)
- USER.md (updated with discovered preferences)
"""

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone


def fetch_threads(api_key, user_id, from_date=None, to_date=None, max_pages=50):
    """Fetch all threads from Fabric API, paginating through results."""
    base = f"https://api.onfabric.io/api/v1/users/{user_id}/threads"
    headers = {"X-API-Key": api_key}
    items = []
    page_token = ""
    page = 1

    while page <= max_pages:
        params = {"page_size": "100"}
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        if page_token:
            params["page_token"] = page_token

        url = base + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  ⚠️  API error on page {page}: {e}")
            break

        page_items = data.get("items", [])
        items.extend(page_items)
        print(f"  📄 Page {page}: {len(page_items)} items (total: {len(items)})")

        page_token = data.get("next_page_token") or ""
        has_more = data.get("has_more", False)
        if not has_more or not page_token:
            break

        page += 1
        time.sleep(0.3)

    return items


def categorize_threads(items):
    """Categorize threads into interest areas."""
    categories = defaultdict(list)

    for item in items:
        provider = item.get("provider", "")
        interaction = item.get("interaction_type", "")
        preview = item.get("preview", "")
        payload = item.get("payload", {})
        asat = item.get("asat", "")

        entry = {
            "preview": preview,
            "date": asat[:10] if asat else "",
            "provider": provider,
            "type": interaction,
            "url": payload.get("object", {}).get("url", ""),
        }

        preview_lower = preview.lower()

        # Categorize by content signals
        if provider == "instagram":
            categories["instagram"].append(entry)
        elif any(kw in preview_lower for kw in ["restaurant", "dinner", "lunch", "brunch", "food", "menu", "reservation", "opentable", "booking"]):
            categories["restaurants"].append(entry)
        elif any(kw in preview_lower for kw in ["fashion", "dress", "shoes", "heels", "bag", "designer", "collection", "runway", "style"]):
            categories["fashion"].append(entry)
        elif any(kw in preview_lower for kw in ["flight", "hotel", "airbnb", "travel", "airport", "visa", "passport", "booking.com"]):
            categories["travel"].append(entry)
        elif any(kw in preview_lower for kw in ["linkedin", "startup", "funding", "investor", "product", "saas", "api", "platform"]):
            categories["work"].append(entry)
        else:
            categories["interests"].append(entry)

    return categories


def write_memory_file(path, title, entries, entry_formatter=None):
    """Write a categorized memory file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w") as f:
        f.write(f"# {title}\n\n")
        if not entries:
            f.write("(No data yet — will be populated from Fabric sync)\n")
            return

        f.write(f"*Auto-generated from Fabric data on {datetime.now(timezone.utc).strftime('%Y-%m-%d')}*\n\n")

        if entry_formatter:
            for entry in entries:
                f.write(entry_formatter(entry))
        else:
            for entry in entries:
                date = entry.get("date", "")
                preview = entry.get("preview", "")
                url = entry.get("url", "")
                line = f"- {preview}"
                if date:
                    line += f" [{date}]"
                if url:
                    line += f" ({url})"
                f.write(line + "\n")


def write_user_md(path, user_name, timezone, location, categories):
    """Generate USER.md from categorized Fabric data."""
    with open(path, "w") as f:
        f.write(f"# USER.md - About {user_name}\n\n")
        f.write("## Basics\n")
        f.write(f"- **Name:** {user_name}\n")
        f.write(f"- **Timezone:** {timezone}\n")
        f.write(f"- **Location:** {location}\n\n")

        f.write("## What They Care About\n\n")
        f.write("*Auto-generated from Fabric data. Review and edit!*\n\n")

        f.write("**Professional:**\n")
        if categories["work"]:
            for entry in categories["work"][:5]:
                f.write(f"- {entry['preview'][:100]}\n")
        else:
            f.write("- (edit: add professional context)\n")

        f.write("\n**Intellectual:**\n")
        if categories["interests"]:
            for entry in categories["interests"][:8]:
                f.write(f"- {entry['preview'][:100]}\n")
        else:
            f.write("- (edit: add intellectual interests)\n")

        f.write("\n**Lifestyle:**\n")
        if categories["fashion"]:
            f.write("- Fashion interests detected from browsing history\n")
        if categories["restaurants"]:
            f.write(f"- Restaurant explorer ({len(categories['restaurants'])} food-related searches)\n")
        if categories["travel"]:
            f.write(f"- Travel ({len(categories['travel'])} travel-related searches)\n")
        if not any(categories[k] for k in ["fashion", "restaurants", "travel"]):
            f.write("- (edit: add lifestyle preferences)\n")

        f.write("\n**Communication Style:**\n")
        f.write("- (edit: describe how they like to communicate)\n")

        f.write("\n## Full Context\n")
        f.write("For detailed context, see:\n")
        user_slug = user_name.lower().replace(" ", "-")
        f.write(f"- `memory/{user_slug}/` → Ground truth files\n")
        f.write("- Use `memory_search()` when you need specifics\n")


def write_fabric_latest(path, recent_items):
    """Write the fabric-latest.md summary."""
    now = datetime.now(timezone.utc)

    providers = defaultdict(int)
    for item in recent_items:
        providers[item.get("provider", "unknown")] += 1

    with open(path, "w") as f:
        f.write(f"# Fabric Data - Latest 7 Days\n")
        f.write(f"**Fetched:** {now.strftime('%Y-%m-%d %H:%M')} UTC\n\n")
        f.write(f"## Summary\n")
        f.write(f"- **Total items:** {len(recent_items)}\n")
        for provider, count in sorted(providers.items()):
            f.write(f"- **{provider.title()}:** {count}\n")

        f.write(f"\n## Recent Activity\n\n")
        for item in recent_items[:20]:
            preview = item.get("preview", "")
            date = item.get("asat", "")[:10]
            f.write(f"- {preview} [{date}]\n")


def main():
    parser = argparse.ArgumentParser(description="Bootstrap memory from Fabric API")
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--user-name", required=True)
    parser.add_argument("--user-slug", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--timezone", default="UTC")
    parser.add_argument("--location", default="")
    args = parser.parse_args()

    print(f"  Fetching all Fabric threads for user {args.user_id}...")

    # Fetch last 90 days for initial bootstrap
    now = datetime.now(timezone.utc)
    from_date = (now - timedelta(days=90)).strftime("%Y-%m-%dT00:00:00.000Z")
    to_date = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    all_items = fetch_threads(args.api_key, args.user_id, from_date, to_date)
    print(f"  Total threads fetched: {len(all_items)}")

    if not all_items:
        print("  ⚠️  No threads found — creating empty stubs")
        # Create empty stubs
        for f in ["interests.md", "restaurants.md", "fashion.md", "travel.md", "relationships.md", "work.md"]:
            title = f.replace(".md", "").title()
            write_memory_file(
                os.path.join(args.workspace, "memory", args.user_slug, f),
                title, []
            )
        return

    # Categorize
    categories = categorize_threads(all_items)
    print(f"  Categories: " + ", ".join(f"{k}={len(v)}" for k, v in categories.items()))

    # Write memory/{user}/ files
    user_mem = os.path.join(args.workspace, "memory", args.user_slug)
    write_memory_file(os.path.join(user_mem, "interests.md"), "Interests", categories["interests"])
    write_memory_file(os.path.join(user_mem, "restaurants.md"), "Restaurants & Food", categories["restaurants"])
    write_memory_file(os.path.join(user_mem, "fashion.md"), "Fashion & Style", categories["fashion"])
    write_memory_file(os.path.join(user_mem, "travel.md"), "Travel & Destinations", categories["travel"])
    write_memory_file(os.path.join(user_mem, "relationships.md"), "Relationships", [])  # Can't auto-detect from threads
    write_memory_file(os.path.join(user_mem, "work.md"), "Work & Professional", categories["work"])

    # Write memory/topics/ dedup files
    topics = os.path.join(args.workspace, "memory", "topics")
    write_memory_file(os.path.join(topics, "food.md"), "Restaurants & Food (Dedup)", categories["restaurants"])
    write_memory_file(os.path.join(topics, "interests.md"), "Interests (Dedup)", categories["interests"])
    write_memory_file(os.path.join(topics, "lifestyle.md"), "Lifestyle & Fashion (Dedup)", categories["fashion"])
    write_memory_file(os.path.join(topics, "travel.md"), "Travel (Dedup)", categories["travel"])

    # Write fabric-latest.md (last 7 days)
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    recent = [i for i in all_items if i.get("asat", "") >= seven_days_ago]
    write_fabric_latest(os.path.join(args.workspace, "memory", "fabric-latest.md"), recent)

    # Write/update USER.md
    write_user_md(
        os.path.join(args.workspace, "USER.md"),
        args.user_name, args.timezone, args.location, categories
    )

    print(f"  ✅ Memory files written to {user_mem}/")
    print(f"  ✅ Topic files written to {topics}/")
    print(f"  ✅ USER.md updated")


if __name__ == "__main__":
    main()
