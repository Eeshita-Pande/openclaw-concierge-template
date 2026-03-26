#!/usr/bin/env python3
"""Phase 2: Extract interest signals from threads using an LLM.

Supports multiple providers via a unified interface:
  - anthropic: Uses the anthropic Python SDK (ANTHROPIC_API_KEY)
  - openai: Uses the openai Python SDK (OPENAI_API_KEY) — works for OpenAI, Azure, or any compatible API
  - openrouter: Uses openai SDK pointed at OpenRouter (OPENROUTER_API_KEY)

Set PROFILE_EXTRACTION_PROVIDER and PROFILE_EXTRACTION_MODEL env vars, or pass --provider/--model CLI args.
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_client import create_client

DEFAULT_PROVIDER = os.environ.get("PROFILE_EXTRACTION_PROVIDER", "anthropic")
DEFAULT_MODEL = os.environ.get("PROFILE_EXTRACTION_MODEL", "claude-haiku-4-5")

CATEGORIES = [
    "relationships", "work", "travel", "food", "activities",
    "sport", "health", "entertainment", "shopping", "values",
]

TYPE_DESCRIPTIONS = {
    "google_youtube": "YouTube activity: videos viewed and liked, with titles and creator names",
    "google_search": "Google searches: queries the user typed into Google Search",
    "google_shopping": "Google Shopping: products the user searched for or viewed",
    "google_discover": "Google Discover: articles and content surfaced in the user's feed",
    "google_image_search": "Google Image Search: image queries the user performed",
    "google_video_search": "Google Video Search: video queries the user performed",
    "google_lens": "Google Lens: objects/images the user looked up with their camera",
    "instagram_stories": "Instagram Stories: ephemeral content the user posted (descriptions of images/videos)",
    "instagram_posts": "Instagram Posts: permanent content the user shared (descriptions and captions)",
}


def compact_thread(thread: dict) -> dict | None:
    """Compact a thread to essential fields for LLM processing."""
    payload = thread.get("payload", {})
    obj = payload.get("object", {})
    attributed = obj.get("attributedTo", {})
    itype = thread.get("interaction_type", "")

    compact = {
        "type": itype,
        "date": thread.get("asat", "")[:10],
        "action": payload.get("type", payload.get("fibreKind", "")),
    }

    if "youtube" in itype:
        title = obj.get("name", "")[:200]
        creator = attributed.get("name", "")
        if not title and not creator:
            return None
        compact["title"] = title
        compact["creator"] = creator

    elif any(k in itype for k in ["search", "discover", "lens", "shopping"]):
        query = obj.get("name", "")[:200]
        if not query:
            return None
        compact["query"] = query

    elif "instagram" in itype:
        desc = thread.get("asset_description") or obj.get("name", "") or ""
        desc = desc[:300]
        if not desc:
            return None
        compact["description"] = desc

    else:
        preview = thread.get("preview", "")[:200]
        if not preview:
            return None
        compact["text"] = preview

    return compact


def format_interaction(compact: dict) -> str:
    """Format a compact thread for the LLM prompt."""
    date = compact.get("date", "????-??-??")
    itype = compact.get("type", "")

    if "youtube" in itype:
        action = compact.get("action", "View")
        title = compact.get("title", "")
        creator = compact.get("creator", "")
        suffix = f' by {creator}' if creator else ''
        return f'- [{date}] {action}: "{title}"{suffix}'

    elif any(k in itype for k in ["search", "discover", "lens", "shopping"]):
        label = "Shopping" if "shopping" in itype else "Search"
        if "lens" in itype:
            label = "Lens"
        if "discover" in itype:
            label = "Discover"
        return f'- [{date}] {label}: "{compact.get("query", "")}"'

    elif "instagram" in itype:
        kind = "Story" if "stories" in itype else "Post"
        return f'- [{date}] {kind}: "{compact.get("description", "")}"'

    else:
        return f'- [{date}] {compact.get("action", "")}: "{compact.get("text", "")}"'


def build_extraction_prompt(compacted_batch: list[dict]) -> str:
    """Build the extraction prompt for a batch of threads."""
    # Determine which types are in this batch
    types_in_batch = set(c.get("type", "") for c in compacted_batch)
    type_descs = []
    for t in types_in_batch:
        if t in TYPE_DESCRIPTIONS:
            type_descs.append(f"- {TYPE_DESCRIPTIONS[t]}")
    type_desc_text = "\n".join(type_descs) if type_descs else "- Mixed digital interactions"

    formatted = "\n".join(format_interaction(c) for c in compacted_batch)

    return f"""Analyze these digital interactions and extract interest signals — recurring topics, content patterns, and behavioral indicators. For each signal, note its category and a brief description.

The data includes:
{type_desc_text}

Return ONLY valid JSON:
{{
  "signals": [
    {{"category": "<category>", "signal": "<description>", "strength": "low|medium|high"}}
  ]
}}

Categories: {', '.join(CATEGORIES)}

Rules:
- Only extract clear signals supported by the data
- Group similar items into one signal (not one per interaction)
- Strength: high = repeated/liked/actively created, medium = several occurrences, low = one-off
- If a batch has no clear signals for a category, skip it
- Keep signals concise (1 sentence each)

Interactions:
{formatted}"""


def extract_batch(client, batch: list[dict], batch_idx: int) -> dict:
    """Send one batch to the LLM for extraction."""
    prompt = build_extraction_prompt(batch)

    for attempt in range(2):
        try:
            text = client.complete(prompt, max_tokens=2048, temperature=0.1)

            # Try to parse JSON — handle markdown code blocks
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                text = text.rsplit("```", 1)[0]
            text = text.strip()

            result = json.loads(text)
            return result

        except json.JSONDecodeError as e:
            if attempt < 1:
                print(f"    JSON parse error on batch {batch_idx}, retrying: {e}", file=sys.stderr)
                time.sleep(1)
            else:
                print(f"    SKIP batch {batch_idx}: invalid JSON after retries", file=sys.stderr)
                return {"signals": [], "error": str(e)}

        except Exception as e:
            print(f"    SKIP batch {batch_idx}: {e}", file=sys.stderr)
            return {"signals": [], "error": str(e)}

    return {"signals": []}


def main():
    parser = argparse.ArgumentParser(description="Extract interest signals from threads")
    parser.add_argument("--output-dir", required=True, help="Output directory (must contain raw_threads.json)")
    parser.add_argument("--batch-size", type=int, default=100, help="Threads per LLM batch")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER, help=f"LLM provider (default: {DEFAULT_PROVIDER})")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    raw_path = os.path.join(args.output_dir, "raw_threads.json")
    if not os.path.exists(raw_path):
        print(f"ERROR: {raw_path} not found. Run fetch_threads.py first.", file=sys.stderr)
        sys.exit(1)

    intermediate_dir = os.path.join(args.output_dir, "intermediate")
    os.makedirs(intermediate_dir, exist_ok=True)

    # Load checkpoint
    checkpoint_path = os.path.join(args.output_dir, ".checkpoint.json")
    checkpoint = {}
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path) as f:
            checkpoint = json.load(f)
    completed_batches = set(checkpoint.get("completed_batches", []))

    # Load and compact threads
    print("Loading threads...")
    with open(raw_path) as f:
        threads = json.load(f)
    print(f"  Loaded {len(threads)} threads")

    print("Compacting threads...")
    compacted = []
    skipped = 0
    for t in threads:
        c = compact_thread(t)
        if c:
            compacted.append(c)
        else:
            skipped += 1
    print(f"  Compacted: {len(compacted)}, skipped (no content): {skipped}")

    # Batch
    batches = []
    for i in range(0, len(compacted), args.batch_size):
        batches.append(compacted[i:i + args.batch_size])
    print(f"  {len(batches)} batches of ~{args.batch_size}")

    # Process
    print(f"Using provider={args.provider}, model={args.model}")
    client = create_client(args.provider, args.model)
    total_signals = 0
    new_batches = 0

    for idx, batch in enumerate(batches):
        batch_file = os.path.join(intermediate_dir, f"batch_{idx:03d}.json")

        if idx in completed_batches:
            # Load existing result for counting
            if os.path.exists(batch_file):
                with open(batch_file) as f:
                    existing = json.load(f)
                total_signals += len(existing.get("signals", []))
            print(f"  Batch {idx:03d}/{len(batches) - 1}: skipped (already done)")
            continue

        print(f"  Batch {idx:03d}/{len(batches) - 1}: processing {len(batch)} threads...", end=" ")
        result = extract_batch(client, batch, idx)
        signals = result.get("signals", [])
        total_signals += len(signals)
        new_batches += 1

        print(f"{len(signals)} signals")

        # Save batch result
        with open(batch_file, "w") as f:
            json.dump(result, f, indent=2)

        # Update checkpoint
        completed_batches.add(idx)
        checkpoint["completed_batches"] = sorted(completed_batches)
        checkpoint["last_batch"] = idx
        checkpoint["total_signals"] = total_signals
        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint, f, indent=2)

        # Rate limit: ~1 req/sec
        time.sleep(1)

    print(f"\nDone. {total_signals} total signals from {len(batches)} batches ({new_batches} new).")
    print(f"Results in {intermediate_dir}/")


if __name__ == "__main__":
    main()
