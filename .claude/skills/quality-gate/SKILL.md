---
name: quality-gate
description: Run the full review of an application packet and decide whether it may go to the candidate's review queue or must be flagged. Use for "review this application", "is this ready to send?", "run the quality gate", and always before any application is offered for submission.
---

# Quality gate

Nothing reaches the review queue as "ready" unless it clearly passes. When in doubt, flag. A
flagged packet costs the candidate a minute; a bad application costs them a real opportunity.

## Order of passes

Run on `applications/<name>/`, writing each result into `review.md`:

1. `fact-check`
2. `humanize`
3. `fact-check` again, because rewording can change a claim
4. `recruiter-read`, then apply its reordering and cuts
5. `ats-check` on the final text
6. `fact-check` a last time if step 4 or 5 changed wording

Re-read the files from disk before each pass, as if you had not written them. In this repo the
`verifier` agent runs the gate in its own context, separate from the `writer`.

## Bars

| Pass | Bar |
|---|---|
| Fact check | Zero failed claims. No exceptions. |
| Voice | 8 out of 10 or higher. |
| Recruiter read | 7 out of 10 or higher, and no unanswered hesitation about a must-have. |
| ATS | All parsing checks pass; missing keywords are real gaps only. |

- **Ready**: every bar met. Set the job to `ready`.
- **Revise**: a bar missed that reordering, cutting or rewording can fix. Fix and re-run; at most
  two rounds.
- **Flagged**: still failing, or failing for a reason wording cannot fix (a must-have gap, a
  likely knock-out answer, a fact that needs the candidate). Set the job to `flagged`.

## Scorecard (top of review.md)

The verdict and one-line reason; each pass's result; gaps stated plainly; screening answers; what
changed from the base resume; questions for the candidate; content that would help next time.

## When the candidate sends a flagged packet

Their call when the flag is about fit. Set `approved-override`, never `ready`, and record their
words and the date. There is no override for a failed fact check.
