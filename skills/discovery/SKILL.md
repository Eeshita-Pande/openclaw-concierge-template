---
name: discovery
version: 1.0.0
description: Curate 1-2 thoughtful discoveries for your user based on their Fabric data, interests, and memory. Designed for use with OpenClaw memory system + Fabric API.
---

# Discovery Skill

Find 1–2 things your user would genuinely love. Quality over quantity. If nothing is strong enough, send nothing.

## ⚠️ Critical Rule

**Output ONLY the final message — 1–2 bullet points, nothing else. No preamble, no reasoning, no "I found X items". Do all analysis internally.**

---

## Step 1: Know Them (Read First)

These files define who your user is and what they'd care about:

- `USER.md` — core preferences, location, languages, aesthetic
- Files in `memory/{user}/` — read ALL available files:
  - `interests.md` — intellectual passions, current obsessions
  - `fashion.md` — brands, aesthetic preferences, what's been recommended
  - `travel.md` — places visited, places being planned
  - `work.md` — professional context (for article relevance)
  - `relationships.md` — partner, close friends (for "good for a date night" framing)
  - `restaurants.md` — recent restaurant recommendations
- `memory/instagram/YYYY-MM.md` — current month only (signals mood, aesthetic)

---

## Step 2: Dedup Check (Mandatory)

Read these to know what to avoid recommending:

**Already visited / owned / read:**
- `memory/topics/food.md` — full restaurant history
- `memory/topics/lifestyle.md` — fashion items owned or sent
- `memory/topics/travel.md` — places visited
- `memory/topics/interests.md` — articles/tools already read
- Files in `memory/{user}/` (also read in Step 1)

**Already recommended:**
- `memory/{agent}/discoveries/` — last 7 daily log files

Never recommend anything already in these files.

---

## Step 3: Fresh Context

- `memory/fabric-latest.md` — what they've been searching/watching this week (signals live interests)
- `memory/shared/daily/YYYY-MM-DD.md` — today + yesterday (upcoming plans, stated interests)

---

## Step 4: Find 1–2 Discoveries

**Discovery types (rotate, don't repeat same category two days running):**
- New restaurant (near their location, matching cuisine preferences from USER.md)
- Fashion drop or exhibition (matching their aesthetic from memory files)
- Article relevant to their work or intellectual interests
- Travel experience (specific, immersive, connecting to known interests)
- Product (matching their aesthetic preferences)

**Quality bar:**
- Would they genuinely care about this? Not generic.
- Is it timely? (new opening, just published, limited availability)
- Does it connect to something they're actually interested in right now (check Fabric data)?
- Skip if mediocre. 0 sent > 1 weak sent.

---

## Step 5: Log It

Write to `memory/{agent}/discoveries/YYYY-MM-DD.md` (append if exists):

```
## YYYY-MM-DD Evening Discoveries
- item: <name>
  category: <food|fashion|travel|article|product>
  link: <url>
  rationale: <1–2 lines>
  status: sent
```

If nothing sent: `- item: NONE (no strong discoveries today)` with rationale.

**Also update the relevant topic file** to prevent future duplication:
- Restaurant → append to `memory/topics/food.md`
- Article → append to `memory/topics/interests.md`
- Fashion → append to `memory/topics/lifestyle.md`
- Travel → append to `memory/topics/travel.md`

---

## Output Format

```
• **[Name]** — [one line: what it is + why it's for them]. [link]

• **[Name]** — [one line: what it is + why it's for them]. [link]
```

Witty and concise. If only one strong find, send one. Max two.
