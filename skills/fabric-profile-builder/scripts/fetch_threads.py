#!/usr/bin/env python3
"""Phase 1: Fetch all threads from Fabric API."""

import argparse
import json
import os
import sys
import time
import requests

API_BASE = "https://api.onfabric.io/api/v1"


def get_credentials():
    user_id = os.environ.get("FABRIC_USER_ID")
    api_key = os.environ.get("FABRIC_API_KEY")
    if not user_id or not api_key:
        print("ERROR: FABRIC_USER_ID and FABRIC_API_KEY env vars required", file=sys.stderr)
        sys.exit(1)
    return user_id, api_key


def discover_types(user_id: str, headers: dict) -> list[str]:
    """Probe API for available interaction types."""
    url = f"{API_BASE}/users/{user_id}/threads"
    params = {"page_size": 1, "interaction_type": "__probe__"}
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code == 422 or resp.status_code == 400:
        data = resp.json()
        return data.get("allowed_interaction_types", [])
    # If probe doesn't error, the API may not support it — try without filter
    return []


def check_type_has_data(user_id: str, headers: dict, itype: str) -> bool:
    """Check if an interaction type has any data."""
    url = f"{API_BASE}/users/{user_id}/threads"
    params = {"page_size": 1, "interaction_type": itype}
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code == 200:
        data = resp.json()
        return len(data.get("items", [])) > 0
    return False


def fetch_all_threads(user_id: str, headers: dict, from_date: str = None, to_date: str = None) -> list[dict]:
    """Fetch all threads with pagination."""
    url = f"{API_BASE}/users/{user_id}/threads"
    all_threads = []
    page_token = None
    page_num = 0

    while True:
        params = {"page_size": 100}
        if page_token:
            params["page_token"] = page_token
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date

        for attempt in range(3):
            try:
                resp = requests.get(url, headers=headers, params=params, timeout=30)
                resp.raise_for_status()
                break
            except (requests.RequestException, requests.HTTPError) as e:
                if attempt == 2:
                    print(f"  ERROR: Failed after 3 retries on page {page_num}: {e}", file=sys.stderr)
                    return all_threads
                wait = 2 ** (attempt + 1)
                print(f"  Retry {attempt + 1}/3 in {wait}s: {e}", file=sys.stderr)
                time.sleep(wait)

        data = resp.json()
        items = data.get("items", [])
        all_threads.extend(items)
        page_num += 1

        print(f"  Page {page_num}: {len(items)} items (total: {len(all_threads)})")

        if not data.get("has_more", False) or not data.get("next_page_token"):
            break

        page_token = data["next_page_token"]
        time.sleep(0.2)

    return all_threads


def main():
    parser = argparse.ArgumentParser(description="Fetch all Fabric API threads")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--from-date", help="Start date (YYYY-MM-DD or ISO 8601)")
    parser.add_argument("--to-date", help="End date (YYYY-MM-DD or ISO 8601)")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    user_id, api_key = get_credentials()
    headers = {"X-Api-Key": api_key, "Accept": "application/json"}

    # Discover available types
    print("Discovering available interaction types...")
    types = discover_types(user_id, headers)
    if types:
        print(f"  Available types: {', '.join(types)}")
        # Check which have data
        active_types = []
        for t in types:
            has_data = check_type_has_data(user_id, headers, t)
            status = "✓ has data" if has_data else "✗ empty"
            print(f"    {t}: {status}")
            if has_data:
                active_types.append(t)
            time.sleep(0.2)
        print(f"  Active types: {', '.join(active_types)}")
    else:
        print("  Could not discover types via probe, fetching all...")

    # Fetch all threads
    print("\nFetching all threads...")
    threads = fetch_all_threads(user_id, headers, args.from_date, args.to_date)
    print(f"\nTotal threads fetched: {len(threads)}")

    # Stats
    type_counts = {}
    for t in threads:
        itype = t.get("interaction_type", "unknown")
        type_counts[itype] = type_counts.get(itype, 0) + 1

    print("\nBreakdown by type:")
    for itype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {itype}: {count}")

    # Date range
    dates = [t.get("asat", "")[:10] for t in threads if t.get("asat")]
    if dates:
        print(f"\nDate range: {min(dates)} → {max(dates)}")

    # Save
    output_path = os.path.join(args.output_dir, "raw_threads.json")
    with open(output_path, "w") as f:
        json.dump(threads, f, indent=2)
    print(f"\nSaved to {output_path} ({os.path.getsize(output_path) / 1024 / 1024:.1f} MB)")

    # Save metadata
    meta = {
        "total_threads": len(threads),
        "type_counts": type_counts,
        "date_range": {"min": min(dates) if dates else None, "max": max(dates) if dates else None},
        "active_types": list(type_counts.keys()),
        "fetch_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    meta_path = os.path.join(args.output_dir, "fetch_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)


if __name__ == "__main__":
    main()
