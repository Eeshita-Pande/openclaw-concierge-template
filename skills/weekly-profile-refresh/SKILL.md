---
name: weekly-profile-refresh
description: Weekly profile refresh that re-runs the Fabric profile builder on the last 30 days of data, diffs against existing memory profiles, proposes updates, and optionally runs the public profile enricher.
---

# Weekly Profile Refresh

Refresh the user's profile from recent Fabric data and public sources. Run weekly to keep the profile current without manual intervention.

## Step 1: Check Prerequisites

```bash
source ~/.openclaw/workspace/.env.fabric
```

Verify `FABRIC_API_KEY` and `FABRIC_USER_ID` are set. If not, log a warning and stop.

## Step 2: Run Profile Builder (Last 30 Days)

Calculate the date 30 days ago and run the pipeline:

```bash
FROM_DATE=$(date -d '30 days ago' +%Y-%m-%d 2>/dev/null || date -v-30d +%Y-%m-%d)

python3 skills/fabric-profile-builder/scripts/run_pipeline.py \
  --output-dir /tmp/weekly-profile-refresh \
  --from-date "$FROM_DATE" \
  --extraction-provider anthropic --extraction-model claude-haiku-4-5 \
  --synthesis-provider anthropic --synthesis-model claude-sonnet-4-6
```

If the pipeline fails, log the error and continue to Step 4 (public enricher can still run).

## Step 3: Diff Against Existing Profiles

Read the newly generated profiles from `/tmp/weekly-profile-refresh/interests/` and compare against the existing memory files in `memory/{user}/`.

For each category:
1. Read the existing file (e.g., `memory/{user}/interests.md`)
2. Read the new file (e.g., `/tmp/weekly-profile-refresh/interests/entertainment.md`)
3. Identify:
   - **New facts** not in the existing profile
   - **Faded interests** that were strong before but have no recent signal
   - **Intensity changes** — something casual that became active, or vice versa

Present a summary of proposed changes:

```
## Profile Refresh Summary — YYYY-MM-DD

### New observations (last 30 days)
- [category]: [new fact from recent data]
- ...

### Faded interests (no recent signal)
- [category]: [fact that had no activity in the last 30 days]
- ...

### Intensity changes
- [category]: [fact] — was casual, now active (or vice versa)
- ...

### No changes
- [categories with no significant changes]
```

Apply new observations to the memory files. Flag faded interests but do not remove them — they may return.

## Step 4: Public Profile Enricher (If Stale)

Check if `memory/{user}/public-profile.md` exists and when it was last updated:

- If it **doesn't exist** and USER.md has a name/URLs: run `skills/public-profile-enricher/SKILL.md`
- If it **exists but is older than 30 days**: re-run the enricher
- If it **exists and is recent**: skip

## Step 5: Clean Up

```bash
rm -rf /tmp/weekly-profile-refresh
```

## Step 6: Log

Write a brief summary to `memory/{agent}/profile-refresh-log.md` (append):

```
## YYYY-MM-DD
- Fabric data: [X] threads from last 30 days
- New observations: [N]
- Faded interests: [N]
- Public enricher: [ran/skipped/failed]
```
