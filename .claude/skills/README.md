# Skills

Each folder holds one `SKILL.md`: front matter with a `name` and a `description` (when to use
it), then the procedure. Claude Code loads these automatically. Any other agent should open the
matching `SKILL.md` and follow it; see [AGENTS.md](../../AGENTS.md).

## In pipeline order

| # | Skill | Role | What it does | Reads | Writes |
|---|---|---|---|---|---|
| 0 | [job-search-run](job-search-run/SKILL.md) | HQ | Runs the whole day, start to review queue | everything below | review queue |
| 1 | [job-discover](job-discover/SKILL.md) | Scout | Polls the watchlist's public job boards; adds a pasted posting | `data/watchlist.csv`, `config/discovery.json` | `data/jobs.db` |
| 2 | [job-score](job-score/SKILL.md) | Scout | Reads postings in full, applies exclusions, scores fit 0-100 | `data/jobs.db`, `profile/` | scores and statuses in `data/jobs.db` |
| 3 | [resume-tailor](resume-tailor/SKILL.md) | Writer | One-page resume for one posting, fact bank only | `profile/`, the posting | `applications/<folder>/resume.md`, `match.md`, `answers.md` |
| 3a | [cover-letter](cover-letter/SKILL.md) | Writer | Cover letter or free-text answer, only when a form asks | `profile/`, the posting | `applications/<folder>/` |
| 4 | [quality-gate](quality-gate/SKILL.md) | Verifier | Runs the four passes below and sets the verdict | the packet | `applications/<folder>/review.md` |
| 4.1 | [fact-check](fact-check/SKILL.md) | Verifier | Every claim traced to the fact bank; 0 failures allowed | packet, `profile/fact-bank.yaml` | `review.md` |
| 4.2 | [humanize](humanize/SKILL.md) | Verifier | Plain, in the candidate's voice; 8/10 or more | packet, `profile/voice.md` | `review.md` |
| 4.3 | [recruiter-read](recruiter-read/SKILL.md) | Verifier | Ten-second skim; 7/10 or more, no unanswered must-have | packet, posting | `review.md` |
| 4.4 | [ats-check](ats-check/SKILL.md) | Verifier | Builds the DOCX, checks parsing and exact posting terms | `resume.md` | `.docx`, `review.md` |
| 5 | [apply-assist](apply-assist/SKILL.md) | HQ | Fills an approved form and stops before Submit | `answers.md`, `profile/` | `answers.md`, trace |
| 6 | [application-tracker](application-tracker/SKILL.md) | HQ | Records submissions and outcomes; shows the queue | `data/` | `data/application-log.csv`, `data/jobs.db` |

Any time:

| Skill | Role | What it does |
|---|---|---|
| [profile-intake](profile-intake/SKILL.md) | HQ | Adds or corrects facts and preferences by asking the candidate |
| [feedback-learn](feedback-learn/SKILL.md) | HQ | Records corrections and outcomes so later output changes |

## Job statuses

`new` -> `scored` / `skipped` / `excluded` -> `queued` -> `ready` or `flagged`
(or `approved-override` when the candidate sends a flagged packet) -> `submitted` ->
`rejected` / `interview` / `offer` / `no-response`. `closed` means the posting came down first.

## Verdicts

- **ready**: every pass met its bar. Goes to the review queue.
- **flagged**: at least one pass missed, or a must-have is unanswered. Goes to the queue with
  the reason; sent only if the candidate decides to (`approved-override`, recorded in `review.md`).

A fact-check failure is never overridden: the claim is fixed or removed first.

## Writing a new skill

Keep the same shape: a `description` that names the plain requests that should trigger it, a
short procedure, the files it reads and writes, the trace calls, and the points where it must
stop for the candidate. Add it to `config/agents.json` under the role that runs it.
