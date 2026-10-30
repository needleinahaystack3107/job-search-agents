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
4. Sort each requirement into hard or soft (below), then score out of 100 with the rubric.
5. Save with `python3 scripts/jobs.py mark <key> --status <status> --score <n> --verdict "<one line>" --notes "<details>" --with-siblings`.
6. Show a ranked table: company, title, location, score, main reason, gaps. List excluded
   postings separately with the reason.

## Hard stops (status `excluded`, score 0)

- The employer or the role is on the candidate's exclusion list in `preferences.yaml`.
- The posting or form says it will not sponsor, when the candidate needs sponsorship.
- No listed location is in the candidate's target list.
- The stated top of the pay range is below the candidate's floor for that location.

Ambiguous wording ("must be authorized to work") is not a stop. Score it and flag it.

## Hard and soft requirements

Posted requirements are not all equally strict. A **soft** requirement is noted as a risk; a
**hard** one is a gap. Neither ever lets a resume claim something the fact bank does not hold.

A requirement is **soft** only when the form has no knock-out question on it, the posting does
not mark it "must have", "minimum" or "required" with a number, and it is one of these:

1. **Years, small gap.** Five years or fewer asked, and the candidate's evidenced years in the
   named field fall short by one and a half years or less. Count years from fact-bank role dates
   in that field; other work counts only when the posting says "or a related field", and only
   for the work the fact bank records. Never relabel a role's field to close a gap.
2. **Interchangeable tool.** The candidate has an evidenced tool of the same kind (one BI tool
   for another, one warehouse or orchestrator for another). The missing tool never goes on the
   page, except exactly as the fact bank allows.
3. **Domain as a nice-to-have**, not the core of the duties.
4. **Scale within the evidence**: "large-scale" with no number above what the fact bank records.
5. **Degree field "or related"**, when the candidate has the level asked in a plausibly related
   field.

Everything else in a requirements list is **hard**: larger years gaps, the role's main
programming language, architectural skills (streaming, backend or distributed services, model
training, frontend), licenses, certifications, clearances and work authorization.

## Rubric

| Points | What to judge |
|---|---|
| 40 | **Evidence match.** Share of required skills and duties with a matching `evidenced` entry in the fact bank. A soft gap costs at most 3 points. |
| 15 | **Level.** Years and seniority asked against the candidate's. A soft years gap costs nothing here. |
| 15 | **Domain.** Overlap with the candidate's domains. |
| 15 | **Sponsorship outlook** (if relevant). Explicit support scores full; silence scores less. |
| 10 | **Pay.** Range clears the floor comfortably; no range scores half. |
| 5 | **Role tier.** Core roles score full; stretch roles zero. |

Stretch roles are queued only when every hard must-have has fact-bank evidence.

## Status

- 75 and over with no hard gap in the required qualifications: `queued` (goes to tailoring).
  A hard gap in the duties costs points but does not block queueing; one in the required
  qualifications makes it a maybe. 60 to 74: `scored` (a maybe; the candidate decides).
  Under 60: `skipped`.

## Notes to record

Gaps, each marked hard or soft (never to be covered up later; soft ones go in the verdict as "risk: ..."), screening risks, posting age, one recommendation per company
when two postings from one employer score well, and what you could not tell from the posting.
