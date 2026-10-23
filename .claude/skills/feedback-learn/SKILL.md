---
name: feedback-learn
description: Record the candidate's corrections, preferences and application outcomes so later drafts and job choices improve. Use when the candidate edits a draft, says "I'd never say that", "stop suggesting X", "I want more roles like Y", or reports an interview, rejection or offer.
---

# Learning from feedback

The system is only tailored if what the candidate says changes what it does next time. Put each
piece of feedback where the skill that needs it will read it.

| Feedback | Where it goes |
|---|---|
| A wording edit, or "that doesn't sound like me" | `profile/voice.md`: date, before, after, and the pattern in one line |
| A new or corrected fact | `profile-intake` |
| Roles, companies, locations, pay, things to avoid | `profile/preferences.yaml` |
| A company to add or drop | `data/watchlist.csv` |
| A title or location that keeps matching wrongly | `config/discovery.json` |
| A score they disagree with | `profile/scoring-notes.md` |
| An outcome | `application-tracker`, plus a line in `profile/scoring-notes.md` if it says something about fit |

## Rules

- Record what they said, with the date. Mark any generalization as yours.
- One comment is a data point, not a rule. Ask before turning a single edit into a standing rule,
  unless they said "always" or "never".
- Exclusions and truthfulness rules cannot be loosened by inference; only a direct statement does.
- After five or more outcomes, look for a pattern and tell the candidate how sure you are. Do not
  change behavior on a pattern they have not seen.
- When the same gap shows up across several postings, tell the candidate once, with the postings
  it cost them.
