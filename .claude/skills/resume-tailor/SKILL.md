---
name: resume-tailor
description: Write a resume tailored to one job posting, using only facts from the candidate's fact bank. Use for "tailor my resume for this job", "prep the queued applications", or after job-score queues a posting.
---

# Resume tailoring

Tailoring means choosing, ordering and wording true facts so the reader sees the match quickly. It
never means adding a fact. A resume the candidate cannot defend line by line in an interview is
worse than a weaker one.

## Steps

1. Read `profile/fact-bank.yaml`, the latest file in `drafts/` (the approved base wording), and the
   posting with `python3 scripts/jobs.py show <key>`, including the gaps in its notes.
2. List the posting's requirements and its exact terms. Mark each evidenced, light exposure, or gap.
3. Create `applications/<company>-<role>/` and write `resume.md` there.
4. Write `match.md`: the requirement list, which bullet answers each, and the gaps left open.
5. If any sentence is new or reworded beyond order, cuts, the posting's exact terms and the skills
   section, list it in `review.md` for the candidate's sign-off.
6. Hand the folder to `quality-gate` (in this repo, the `verifier` agent runs it separately, so the
   review is independent of the drafting).

## What may change per posting

- Order of bullets, which bullets appear, emphasis within a bullet.
- The posting's exact word where it names the same thing the candidate did. Never swap in the
  posting's tool for a similar one the candidate used.
- The skills section: `evidenced` and `stated_no_project` skills may be listed; a `light_exposure`
  skill only as "exposure to X". Bullets use `evidenced` skills only.

## What never changes

Titles, employers, dates, numbers and their qualifiers ("about", "estimated"), team size, the
candidate's own role, client anonymity, and anything that depends on an unresolved `open:` item.

## Gaps

A requirement with no evidence stays unmet on the page. Do not hint at it. Record it in `match.md`.
If a must-have is a gap, say so before spending more effort.

## Format

Name, one contact line, then `## Experience`, `## Project` (optional), `## Education`, `## Skills`.
Company line `**Company** | Location`, title line `**Title** · Mon YYYY – Mon YYYY`. One page: at
most 620 words. No street address.
