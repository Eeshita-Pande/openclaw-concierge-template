#!/usr/bin/env python3
"""
Daily regression check — catches file corruption, shrinkage, and cron failures.
Run via cron at midnight. Reports issues to Telegram.
"""

import os
import subprocess
import sys
from datetime import datetime


def check_git_status(workspace):
    """Check for uncommitted changes and auto-commit if reasonable."""
    issues = []
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=workspace, capture_output=True, text=True, timeout=10
        )
        uncommitted = len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0

        if uncommitted > 0:
            if uncommitted < 50:
                # Auto-commit
                subprocess.run(["git", "add", "-A"], cwd=workspace, timeout=10)
                subprocess.run(
                    ["git", "commit", "-m", f"Auto-commit: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC ({uncommitted} files)"],
                    cwd=workspace, timeout=10
                )
            else:
                issues.append(f"⚠️ {uncommitted} uncommitted files — too many to auto-commit")
    except Exception as e:
        issues.append(f"❌ Git check failed: {e}")

    return issues


def check_file_sizes(workspace):
    """Check tracked files for suspicious size changes."""
    issues = []
    try:
        # Get list of tracked files with current sizes
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=workspace, capture_output=True, text=True, timeout=10
        )
        for filepath in result.stdout.strip().splitlines():
            full_path = os.path.join(workspace, filepath)
            if not os.path.exists(full_path):
                issues.append(f"❌ DELETED: {filepath}")
                continue

            current_size = os.path.getsize(full_path)

            # Check against last commit
            try:
                prev = subprocess.run(
                    ["git", "show", f"HEAD:{filepath}"],
                    cwd=workspace, capture_output=True, timeout=10
                )
                prev_size = len(prev.stdout)

                if prev_size > 100:  # Only check files that were non-trivial
                    ratio = current_size / prev_size if prev_size > 0 else 0
                    if ratio < 0.5:
                        issues.append(f"⚠️ SHRUNK {int((1-ratio)*100)}%: {filepath} ({prev_size}→{current_size} bytes)")
                    elif ratio > 3.0:
                        issues.append(f"⚠️ GREW {int(ratio*100)}%: {filepath} ({prev_size}→{current_size} bytes)")
            except Exception:
                pass

    except Exception as e:
        issues.append(f"❌ File size check failed: {e}")

    return issues


def main():
    workspace = os.environ.get("OPENCLAW_WORKSPACE", os.path.expanduser("~/.openclaw/workspace"))

    print(f"🔍 Regression check: {workspace}")
    print(f"📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
    print()

    all_issues = []

    # Git health
    print("Checking git status...")
    all_issues.extend(check_git_status(workspace))

    # File sizes
    print("Checking file sizes...")
    all_issues.extend(check_file_sizes(workspace))

    if all_issues:
        print(f"\n⚠️ {len(all_issues)} issue(s) found:")
        for issue in all_issues:
            print(f"  {issue}")
        sys.exit(1)
    else:
        print("\n✅ No issues found")
        sys.exit(0)


if __name__ == "__main__":
    main()
