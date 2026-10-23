---
name: profile-intake
description: Add to or correct the fact bank and preferences by interviewing the candidate. Use when the candidate shares new work experience, a project, a metric, a promotion, a skill, a new resume file, or a change in what jobs they want.
---

# Profile intake

`profile/fact-bank.yaml` is the only source resumes and cover letters may draw from. Its value
comes from being strictly true, so this skill records what the candidate said and nothing more.

1. Read `profile/fact-bank.yaml`, `profile/preferences.yaml`, and any new files in `inputs/resume/`.
2. Work out what is new or changed. Match it to an existing entry by `id`, or create one.
3. Record each fact with its `status` (`resume`, `stated`, `repo`) and the date. Keep the
   candidate's own numbers and qualifiers.
4. For anything a resume bullet would need but they did not say, add an `open:` item: their own
   part versus the team's, team size, tools, scale, how a result was measured, dates.
5. Ask about open items, at most seven per round, most blocking first, numbered.
6. When an answer is ambiguous, record your reading, label it as your interpretation, and ask.

## Rules

- Never infer a fact. A tool implied by another tool is a question, not an entry.
- Skills sit in one of four lists: `evidenced` (named real work), `stated_no_project`,
  `light_exposure`, `listed_on_resume_without_evidence_yet`. Move a skill only on what was said.
- Future events are recorded as expected and are not usable until confirmed.
- Clients stay anonymous: store descriptions such as "a large retailer", never names.
- Changes to exclusions, locations, pay floors or work authorization go in `preferences.yaml`,
  and only the candidate can loosen them.
