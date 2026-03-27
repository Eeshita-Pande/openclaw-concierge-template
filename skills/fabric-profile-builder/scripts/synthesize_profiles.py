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


DEPTH_RANK = {"identity": 0, "active": 1, "casual": 2, "passive": 3}


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


def deduplicate_signals(signals: list[dict]) -> list[dict]:
    """Deduplicate similar signals: merge evidence counts, keep strongest depth."""
    if not signals:
        return signals

    # Normalize text for comparison
    def normalize(text: str) -> str:
        return text.lower().strip().rstrip(".")

    merged = []
    used = set()

    for i, sig in enumerate(signals):
        if i in used:
            continue

        # Get text field (supports both old "signal" and new "observation" schema)
        text_i = sig.get("observation", sig.get("signal", ""))
        norm_i = normalize(text_i)
        evidence = sig.get("evidence_count", 1)
        depth = sig.get("depth", sig.get("strength", "casual"))

        # Find similar signals
        for j in range(i + 1, len(signals)):
            if j in used:
                continue
            text_j = signals[j].get("observation", signals[j].get("signal", ""))
            norm_j = normalize(text_j)

            # Simple overlap check: if one is a substring of the other,
            # or if they share >60% of words
            words_i = set(norm_i.split())
            words_j = set(norm_j.split())
            if len(words_i) == 0 or len(words_j) == 0:
                continue

            overlap = len(words_i & words_j) / min(len(words_i), len(words_j))
            if overlap > 0.6 or norm_i in norm_j or norm_j in norm_i:
                used.add(j)
                evidence += signals[j].get("evidence_count", 1)
                other_depth = signals[j].get("depth", signals[j].get("strength", "casual"))
                # Keep the stronger depth
                if DEPTH_RANK.get(other_depth, 3) < DEPTH_RANK.get(depth, 3):
                    depth = other_depth
                # Keep the longer/more detailed text
                if len(text_j) > len(text_i):
                    text_i = text_j

        merged.append({
            "observation": text_i,
            "evidence_count": evidence,
            "depth": depth,
            "category": sig.get("category", ""),
        })
        used.add(i)

    # Sort by depth rank (identity first), then by evidence count descending
    merged.sort(key=lambda s: (DEPTH_RANK.get(s["depth"], 3), -s["evidence_count"]))
    return merged


def synthesize_category(client, category: str, signals: list[dict], data_types: list[str]) -> str:
    """Synthesize a factual profile section for one category."""
    # Deduplicate before synthesis
    deduped = deduplicate_signals(signals)

    observation_lines = []
    for s in deduped:
        depth = s.get("depth", "casual")
        evidence = s.get("evidence_count", 1)
        text = s.get("observation", s.get("signal", ""))
        observation_lines.append(f"- [{depth}, {evidence}x] {text}")

    observations_text = "\n".join(observation_lines)
    types_text = ", ".join(data_types)

    prompt = f"""You are writing a factual profile section for a personal AI assistant.
The goal: after reading this, the assistant should KNOW this person's specific tastes,
the names that matter to them, and what they actually do — not vague categories.

Data sources: {types_text}

Here are all observations for the "{category}" category, with depth level and evidence count:

{observations_text}

Write a factual, detailed profile section in markdown. Rules:
- Lead with the strongest signals (identity/active depth with high evidence counts)
- Be SPECIFIC: name real people, places, brands, creators, publications when the data supports it
- State evidence level naturally: "repeatedly searched for" vs "browsed once"
- Omit passive/casual signals unless they form a pattern with 5+ occurrences
- Do NOT speculate or add context not supported by the observations
- Do NOT use filler phrases ("shows a deep interest in", "demonstrates a passion for", "multifaceted")
- If the data is thin, say so in one line — do not pad or stretch
- Format: # {category.title()} heading, ## subheadings for distinct themes, bullet points for specific facts"""

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

    # Combine profiles
    profiles_text = ""
    for cat, content in profiles.items():
        profiles_text += f"\n\n---\n\n### {cat.title()} Profile\n\n{content}"

    prompt = f"""Read all 10 interest profile sections below and synthesize them into a single USER.md.

**Data overview:**
- Total interactions: {total:,}
- Date range: {date_range.get('min', '?')} → {date_range.get('max', '?')}
- Sources: {data_types}

**Interest profiles:**
{profiles_text}

Generate a markdown document with this exact structure:

# About {{Name}}

*Built from {total:,} interactions ({date_range.get('min', '?')} → {date_range.get('max', '?')}) across {data_types}*

## Overview
2-3 sentences: who this person is based on concrete evidence. Profession if detectable, primary domains, geographic context. No adjectives without evidence backing them.

## Deep Engagement
Topics with identity-level or repeated active engagement. Each as a ### subsection with specific names, places, creators, brands. These are the person's defining interests — things they actively seek out, create content about, or return to repeatedly.

## Active Interests
Topics with clear active engagement but less depth or consistency. Specific, not generic. Brief subsections.

## Background
Topics that appear occasionally or passively. One-liners only. Do not pad this section.

## Gaps
What the data doesn't cover. Which categories had no or minimal signal. Which data sources were absent. 2-3 bullet points max.

Rules:
- Cross-source signals (same topic appears in YouTube + Search + Instagram) should be highlighted and ranked higher
- Be specific: name creators, brands, places, publications — not categories
- Do NOT use filler phrases ("multifaceted", "shows a passion for", "demonstrates interest in")
- Do NOT include "Data Sources" or "Personality Indicators" sections
- If a profile section says data is thin, reflect that honestly — do not inflate
- Write a fresh synthesis, not a concatenation of the category profiles
- If the person's name is not detectable, use "User" as the heading"""

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
