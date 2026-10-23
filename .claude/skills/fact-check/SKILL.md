---
name: fact-check
description: Check every claim in a resume or cover letter against the candidate's fact bank and report anything unsupported, inflated or altered. Use for "fact check this resume", "is anything here made up?", and as the first pass of quality-gate.
---

# Fact check

Nothing sent in the candidate's name may be fabricated. This pass is adversarial: assume the draft
contains an error and look for it.

1. Read `profile/fact-bank.yaml` fresh. Do not rely on memory of it or on drafting notes.
2. Split the document into single claims: each title, employer, date, number, tool, team size,
   outcome and skill.
3. For each claim, find the fact-bank entry that supports it and compare word for word.
4. Write results into the `Fact check` section of `review.md`.

## A claim fails when it is

- **Unsupported**: no entry backs it.
- **Inflated**: a number is larger or rounder, a qualifier dropped ("about 450" became "450+",
  "estimated $100M" became "$100M"), or "contributed to" became "led".
- **Substituted**: a different tool than the one used.
- **Transplanted**: a true fact attached to the wrong project or employer.
- **Not yet true**: a future event, such as a pending promotion.
- **Open**: it depends on an unresolved `open:` item.
- **Overstated skill**: a non-`evidenced` skill in a bullet, or a `light_exposure` skill presented
  as more than exposure.
- **Confidential**: a client is named or identifiable.

## Output

One row per failed claim: the text, the failure type, what the fact bank says, and the fix. Then
counts: checked, passed, failed. Any failure fails the pass. The fix is to remove the claim or ask
the candidate through `profile-intake`, never to reword around a missing fact.
