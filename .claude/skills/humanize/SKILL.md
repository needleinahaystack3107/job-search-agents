---
name: humanize
description: Make a resume or cover letter read simply and like the candidate wrote it, and flag wording that reads as machine-generated. Use for "make this sound more human", "does this sound like AI?", and as a pass of quality-gate.
---

# Humanize

Plain, specific writing stands out; polish does not. This pass removes polish and keeps substance.
It may cut and reword. It may never add a fact, so `fact-check` runs again after it.

1. Read the candidate's writing samples in `inputs/writing-samples/` and past edits in
   `profile/voice.md`. With no samples, say so and apply only the general rules.
2. Go line by line with the checks below.
3. Write the `Voice` section of `review.md`: what changed, what still reads as generated, a score
   out of 10.

## Simplify

- One idea per sentence. A bullet is: what they did, with what, and what came of it.
- Plain verbs: built, wrote, led, cut, ran, fixed. Not spearheaded, leveraged, orchestrated,
  utilized, championed.
- Cut adjectives that claim quality (scalable, robust, seamless, cutting-edge) and filler
  ("successfully", "in order to", "responsible for", "various").
- Name the thing: "15 data sources", not "diverse data sources".

## Signs of generated text

Identical bullet shapes, lists of exactly three again and again, closing clauses that restate the
benefit in abstract words, two abstract nouns joined by "and", em dashes for drama, stacked tool
names with no account of what was done.

## Score

10 means a colleague would believe the candidate typed it. 7 or below means at least three lines
still read as generated; list them.
