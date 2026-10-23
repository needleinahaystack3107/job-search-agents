---
name: job-score
description: Read job postings in full and score how well each fits the candidate, applying their strict exclusions and work-authorization needs. Use after job-discover, or for "score these jobs", "is this role a good fit?", "rank my shortlist", "why was this job skipped?".
---

# Job scoring

Decide which postings deserve one of the candidate's few applications a day. A wrong "yes" costs
them a tailored application and a visible rejection; be strict.

## Steps

1. Read `profile/preferences.yaml` and `profile/fact-bank.yaml`.
2. Take the keys from `python3 scripts/jobs.py shortlist --limit 30` (or the keys you were given),
   after `prefilter --apply`. For each, run `python3 scripts/jobs.py show <key>` and read the whole
   description. Then read the application form's questions before scoring. Greenhouse:
   `https://boards-api.greenhouse.io/v1/boards/<board>/jobs/<id>?questions=true`. Ashby and Lever:
   open the application page and read it; type nothing. Note every knock-out question
   (sponsorship, work permit, years, degree, location).
3. Apply the hard stops. Any one ends scoring for that posting.
4. Otherwise score out of 100 with the rubric.
5. Save with `python3 scripts/jobs.py mark <key> --status <status> --score <n> --verdict "<one line>" --notes "<details>" --with-siblings`.
6. Show a ranked table: company, title, location, score, main reason, gaps. List excluded
   postings separately with the reason.

## Hard stops (status `excluded`, score 0)

- The employer or the role is on the candidate's exclusion list in `preferences.yaml`.
- The posting or form says it will not sponsor, when the candidate needs sponsorship.
- No listed location is in the candidate's target list.
- The stated top of the pay range is below the candidate's floor for that location.

Ambiguous wording ("must be authorized to work") is not a stop. Score it and flag it.

## Rubric

| Points | What to judge |
|---|---|
| 40 | **Evidence match.** Share of required skills and duties with a matching `evidenced` entry in the fact bank. |
| 15 | **Level.** Years and seniority asked against the candidate's. |
| 15 | **Domain.** Overlap with the candidate's domains. |
| 15 | **Sponsorship outlook** (if relevant). Explicit support scores full; silence scores less. |
| 10 | **Pay.** Range clears the floor comfortably; no range scores half. |
| 5 | **Role tier.** Core roles score full; stretch roles zero. |

Stretch roles are queued only when every must-have has fact-bank evidence.

## Status

- 75 and over: `queued` (goes to tailoring). 60 to 74: `scored` (a maybe; the candidate decides).
  Under 60: `skipped`.

## Notes to record

Gaps (never to be covered up later), screening risks, posting age, one recommendation per company
when two postings from one employer score well, and what you could not tell from the posting.
