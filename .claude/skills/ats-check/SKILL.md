---
name: ats-check
description: Build the resume file and check that an applicant tracking system would parse it cleanly and find the posting's key terms. Use for "check this resume for ATS", "build the DOCX", "what keywords am I missing?", and as a pass of quality-gate.
---

# ATS check

Applicant tracking systems parse a resume into fields, and recruiters search those fields by exact
words. The file must parse cleanly, and the posting's terms must appear where they are true.

1. Build: `python3 scripts/resume_doc.py build applications/<name>/resume.md`. The file is named
   `Last_First_Resume_<MonYYYY>.docx` from the resume's first line.
2. List the posting's must-have terms exactly as written, plus common short or long forms.
3. Check: `python3 scripts/resume_doc.py check applications/<name>/<file>.docx --keywords "<terms>"`.
4. Sort every missing keyword into **can add truthfully** (the candidate has evidence and the resume
   uses another word; fix the wording) or **gap** (no evidence; leave it missing). Never add a
   keyword to pass this check.
5. Write the `ATS` section of `review.md`.

## Passes when

Name, email and phone are read from the first two lines; Experience, Education and Skills are
found; every job has a `Mon YYYY – Mon YYYY` range; one page (620 words or fewer); and
`odd_characters`, `hidden_characters`, `file_metadata` and `unexpected_file_parts` are all empty.

The check is a local approximation, not the employer's real system. Report coverage as "X of Y
must-have terms present, Z are real gaps", never as a percentage. List the screening questions the
form will likely ask with the answers from `profile/preferences.yaml`, and say if an honest answer
will likely knock the application out.
