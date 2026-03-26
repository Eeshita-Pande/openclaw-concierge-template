#!/usr/bin/env python3
"""Run the full Fabric Profile Builder pipeline (all 4 phases)."""

import argparse
import os
import subprocess
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_phase(name: str, script: str, args: list[str]) -> bool:
    """Run a pipeline phase and return success status."""
    print(f"\n{'=' * 60}")
    print(f"  {name}")
    print(f"{'=' * 60}\n")

    cmd = [sys.executable, os.path.join(SCRIPT_DIR, script)] + args
    result = subprocess.run(cmd, env=os.environ)

    if result.returncode != 0:
        print(f"\nERROR: {name} failed with code {result.returncode}", file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Run full Fabric Profile Builder pipeline")
    parser.add_argument("--output-dir", required=True, help="Output directory for all artifacts")
    parser.add_argument("--from-date", help="Start date filter (YYYY-MM-DD or ISO 8601)")
    parser.add_argument("--to-date", help="End date filter (YYYY-MM-DD or ISO 8601)")
    parser.add_argument("--batch-size", type=int, default=100, help="Threads per extraction batch")
    parser.add_argument("--skip-fetch", action="store_true", help="Skip Phase 1 (reuse existing raw_threads.json)")
    parser.add_argument("--skip-extract", action="store_true", help="Skip Phase 2 (reuse existing batch files)")
    # Model selection — agent picks these based on what's available
    parser.add_argument("--extraction-provider", default="anthropic", help="Provider for extraction (Phase 2)")
    parser.add_argument("--extraction-model", default="claude-haiku-4-5", help="Model for extraction — use a fast/cheap model")
    parser.add_argument("--synthesis-provider", default="anthropic", help="Provider for synthesis (Phase 3+4)")
    parser.add_argument("--synthesis-model", default="claude-haiku-4-5", help="Model for synthesis — use a reasoning-capable model")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    start = time.time()

    # Phase 1: Fetch
    if not args.skip_fetch:
        fetch_args = ["--output-dir", args.output_dir]
        if args.from_date:
            fetch_args += ["--from-date", args.from_date]
        if args.to_date:
            fetch_args += ["--to-date", args.to_date]

        if not run_phase("Phase 1: Fetch Threads", "fetch_threads.py", fetch_args):
            sys.exit(1)
    else:
        print("\nSkipping Phase 1 (--skip-fetch)")

    # Phase 2: Extract
    if not args.skip_extract:
        extract_args = [
            "--output-dir", args.output_dir,
            "--batch-size", str(args.batch_size),
            "--provider", args.extraction_provider,
            "--model", args.extraction_model,
        ]
        if not run_phase("Phase 2: Extract Interest Signals", "extract_signals.py", extract_args):
            sys.exit(1)
    else:
        print("\nSkipping Phase 2 (--skip-extract)")

    # Phase 3+4: Synthesize
    synth_args = [
        "--output-dir", args.output_dir,
        "--provider", args.synthesis_provider,
        "--model", args.synthesis_model,
    ]
    if not run_phase("Phase 3+4: Synthesize Profiles & USER.md", "synthesize_profiles.py", synth_args):
        sys.exit(1)

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"  Pipeline complete in {elapsed / 60:.1f} minutes")
    print(f"  Output: {args.output_dir}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
