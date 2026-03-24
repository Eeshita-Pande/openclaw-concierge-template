---
name: journal
version: 1.0.0
description: Evening journal reflection. Generates a single sharp observation + one open question based on the user's recent activity. Designed for use with Fabric data + OpenClaw memory system.
---

# Journal Reflection Skill

Generate a nightly check-in. One observation. One question. Nothing else visible.

## ⚠️ Critical Rule

**Output ONLY the final observation + question + closing line. Do all analysis internally. Never let reasoning, patterns, themes, bullet points, or internal notes appear in the output. The user sees only the clean message.**

---

## Context Sources

Read these before writing (paths relative to workspace):

- `memory/shared/daily/YYYY-MM-DD.md` — today + past 3 days (use actual dates)
- `memory/fabric-latest.md` — recent searches, YouTube, Instagram activity
- `USER.md` — current life context, preferences
- Files in `memory/{user}/` — travel, work, interests, relationships (check what exists)

---

## Output Format

Two parts, clearly separated by a blank line:

1. **Observation** — 1–2 sentences. Specific, named, no hedging. References something real from their recent activity.
2. **Question** — One open question that follows naturally. Curious, not probing.

Close with: `Reply in Journal topic if you want to think out loud. 🐾`

**Total length: under 80 words.**

---

## Good Examples

```
You searched "iran" on Sunday morning and read five articles in 12 minutes — defence gaps, strike capability, London threat assessment.

What pulled you there? News headline, conversation, or just woke up with it on your mind?

Reply in Journal topic if you want to think out loud. 🐾
```

```
You've been researching Orchha — Amar Mahal, Bundelkhand Riverside, Diwali 2026 timing.

What's drawing you there?

Reply in Journal topic if you want to think out loud. 🐾
```

```
You've been deep in data privacy infrastructure — MyTerms, GliaNet, consent frameworks — while reading about AI futures.

Is this work's next chapter, or something pulling you personally?

Reply in Journal topic if you want to think out loud. 🐾
```

```
ILR approved, citizenship application in — two milestones in the same week.

What's it like watching those pieces fall into place?

Reply in Journal topic if you want to think out loud. 🐾
```

---

## Bad Examples (never do these)

❌ **Internal thinking leaked:**
```
Based on recent context I'm seeing:

Recent theme: Iran conflict research spike...
Deviation from norm: This wasn't gradual interest...
Pattern: Sharp pivot from AI/tech...

---

You searched "iran"...
```

❌ **Generic check-in (no specific context):**
```
Hey love 💛 How was your Monday? What felt good? What drained you? What's one intention for tomorrow?
```

❌ **Laundry list of questions:**
```
How did today feel? What stood out? Who did you connect with? What's sitting with you?
```

❌ **Hedged observation:**
```
It looks like you might have been interested in geopolitics recently, possibly related to Iran...
```

---

## What Signals to Look For

Scan context for deviations, intensity, or transitions:

- **Urgent news/search spike** — multiple articles on the same topic in a short window
- **Travel research** — flight searches, hotel names, specific destinations
- **New trip planning** — dates, heritage properties, historical sites
- **Life milestones** — immigration, citizenship, work changes, relationships
- **Intense work sprint** — late-night sessions, repeated tool/product research
- **Sustained new interest** — same topic across multiple days
- **Unusual quiet** — less activity than normal (intentional rest or avoidance?)

---

## Tone

- Close friend checking in — not therapist, not project manager
- Warm and curious, not probing or intense
- Specific beats generic every time
- If nothing stands out, pick the most interesting thing and ask about it simply
