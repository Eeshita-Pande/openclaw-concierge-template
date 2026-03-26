#!/usr/bin/env python3
"""Phase 3+4: Synthesize interest profiles and generate USER.md.

Uses a reasoning-capable model for narrative synthesis. Provider and model
are configurable via env vars or CLI args.
"""

import argparse
import json
import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_client import create_client

DEFAULT_PROVIDER = os.environ.get("PROFILE_SYNTHESIS_PROVIDER", "anthropic")
DEFAULT_MODEL = os.environ.get("PROFILE_SYNTHESIS_MODEL", "claude-haiku-4-5")

CATEGORIES = [
    "relationships", "work", "travel", "food", "activities",
    "sport", "health", "entertainment", "shopping", "values",
]


def load_all_signals(intermediate_dir: str) -> dict[str, list[dict]]:
    """Load all signals from batch files and group by category."""
    by_category = {c: [] for c in CATEGORIES}

    batch_files = sorted(glob.glob(os.path.join(intermediate_dir, "batch_*.json")))
    for bf in batch_files:
        with open(bf) as f:
            data = json.load(f)
        for signal in data.get("signals", []):
            cat = signal.get("category", "").lower()
            if cat in by_category:
                by_category[cat].append(signal)

    return by_category


def synthesize_category(client, category: str, signals: list[dict], data_types: list[str]) -> str:
    """Synthesize a narrative profile for one category."""
    signal_lines = []
    for s in signals:
        strength = s.get("strength", "medium")
        text = s.get("signal", "")
        signal_lines.append(f"- [{strength}] {text}")

    signals_text = "\n".join(signal_lines)
    types_text = ", ".join(data_types)

    prompt = f"""You are building an interest profile for a person based on their digital activity.
The data comes from these sources: {types_text}.

Here are all the extracted interest signals for the "{category}" category:

{signals_text}

Write a rich, narrative interest profile in markdown. Include:
- Key themes and patterns observed
- Specific creators, channels, brands, or places they engage with
- How strong each interest appears (casual vs deep engagement)
- Cross-reference signals from different data sources when they reinforce each other
- Any evolution over time if visible from the signals
- Do NOT speculate beyond what the data shows
- Do NOT make up information not present in the signals

Format as a readable markdown document starting with a # heading, using ## subheadings for major themes, and bullet points for specific details."""

    try:
        return client.complete(prompt, max_tokens=4096, temperature=0.3)
    except Exception as e:
        return f"# {category.title()}\n\nError generating profile: {e}"


def generate_user_md(client, profiles: dict[str, str], meta: dict) -> str:
    """Generate the final USER.md from all profiles."""
    total = meta.get("total_threads", "unknown")
    date_range = meta.get("date_range", {})
    type_counts = meta.get("type_counts", {})
    data_types = ", ".join(type_counts.keys())

    # Build data sources summary
    sources_lines = []
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        sources_lines.append(f"- **{t}**: {count:,} interactions")
    sources_text = "\n".join(sources_lines)

    # Combine profiles
    profiles_text = ""
    for cat, content in profiles.items():
        profiles_text += f"\n\n---\n\n### {cat.title()} Profile\n\n{content}"

    prompt = f"""Read all 10 interest profile sections below and synthesize them into a single cohesive USER.md.

**Data overview:**
- Total interactions: {total:,}
- Date range: {date_range.get('min', '?')} → {date_range.get('max', '?')}
- Data sources:
{sources_text}

**Interest profiles:**
{profiles_text}

Generate a markdown document with this structure:

# User Profile

*Generated from {total:,} interactions across {data_types} ({date_range.get('min', '?')} → {date_range.get('max', '?')})*

## Data Sources
Summary of available data.

## At a Glance
One paragraph summarizing who this person appears to be.

## Core Interests (Deep engagement)
### Interest 1
### Interest 2
...

## Secondary Interests (Medium engagement)
...

## Lighter Interests (Casual engagement)
...

## Personality Indicators
Bullet points inferring personality traits from content patterns.

## Data Limitations
Honest caveats about what the data can and cannot tell us.

Rules:
- Rank interests by signal count and engagement strength
- Cross-source signals (same interest in YouTube + Search + Instagram) rank higher
- Write a fresh, cohesive overview — not a concatenation
- Be specific (mention creators, brands, places by name)
- Note which categories had minimal signal and which sources were absent"""

    try:
        return client.complete(prompt, max_tokens=8192, temperature=0.3)
    except Exception as e:
        return f"# User Profile\n\nError generating profile: {e}"


def main():
    parser = argparse.ArgumentParser(description="Synthesize interest profiles and USER.md")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER, help=f"LLM provider (default: {DEFAULT_PROVIDER})")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    intermediate_dir = os.path.join(args.output_dir, "intermediate")
    interests_dir = os.path.join(args.output_dir, "interests")
    os.makedirs(interests_dir, exist_ok=True)

    if not os.path.isdir(intermediate_dir):
        print(f"ERROR: {intermediate_dir} not found. Run extract_signals.py first.", file=sys.stderr)
        sys.exit(1)

    # Load metadata
    meta_path = os.path.join(args.output_dir, "fetch_meta.json")
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
    data_types = meta.get("active_types", [])

    # Load signals
    print("Loading signals from batches...")
    by_category = load_all_signals(intermediate_dir)
    for cat, sigs in by_category.items():
        print(f"  {cat}: {len(sigs)} signals")

    # Phase 3: Synthesize profiles
    print(f"\nUsing provider={args.provider}, model={args.model}")
    client = create_client(args.provider, args.model)
    profiles = {}

    print("\nPhase 3: Synthesizing interest profiles...")
    for cat in CATEGORIES:
        signals = by_category[cat]
        out_path = os.path.join(interests_dir, f"{cat}.md")

        if not signals:
            content = f"# {cat.title()}\n\nNo significant signals found for this category in the available data."
            print(f"  {cat}: no signals, writing minimal file")
        else:
            print(f"  {cat}: synthesizing from {len(signals)} signals...", end=" ")
            content = synthesize_category(client, cat, signals, data_types)
            print("done")
            import time as _time
            _time.sleep(1)

        profiles[cat] = content
        with open(out_path, "w") as f:
            f.write(content + "\n")

    print(f"\nProfiles written to {interests_dir}/")

    # Phase 4: Generate USER.md
    print("\nPhase 4: Generating USER.md...")
    user_md = generate_user_md(client, profiles, meta)
    user_path = os.path.join(args.output_dir, "USER.md")
    with open(user_path, "w") as f:
        f.write(user_md + "\n")
    print(f"USER.md written to {user_path}")

    print("\nPipeline complete!")


if __name__ == "__main__":
    main()
