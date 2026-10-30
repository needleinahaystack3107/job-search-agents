# AGENTS.md

Instructions for any coding agent working in this repo (OpenAI Codex, Claude Code, or another
agent that reads `AGENTS.md`). Claude Code reads `CLAUDE.md`; the rules there are the same rules
and apply to you too. Read `CLAUDE.md` before your first task.

## What this repo is

A job-search system run by an agent on behalf of one candidate. It finds postings on public
employer job boards, scores them, tailors a resume from a fact bank, checks the result against
fixed quality bars, and fills application forms for the candidate to submit. The candidate
approves every submission.

The workflow lives in plain Markdown instruction files ("skills") plus standard-library Python
scripts. Nothing is tied to one agent product except the optional trace hooks.

## Rules that never bend

1. **Every claim traces to `profile/fact-bank.yaml`.** Never invent, infer or inflate a fact,
   number, title, date or skill. A gap is a question for the candidate, not a new bullet.
2. **Never submit.** Fill forms and stop. The candidate presses Submit.
3. **Never enter passwords, create accounts, or attempt a CAPTCHA.** Hand over to the candidate.
4. **Legal and demographic answers** (work authorization, sponsorship, EEO) come only from
   `profile/preferences.yaml`. Never guess. Answer sponsorship truthfully even when it ends the
   application, and say so.
5. **Consents and agreements** (privacy notices, arbitration, certifications) are asked every time.
6. **Exclusions in `profile/preferences.yaml` are strict.** Only the candidate loosens them.
7. **No scraping of sites that forbid it** (LinkedIn, Indeed and similar). Only public employer
   job-board APIs (Greenhouse, Lever, Ashby) through `scripts/jobs.py`, one request per company
   per run. No stealth, no detection evasion.
8. **Discreet.** Nothing public. Never write former clients' names to any file.
9. **Flag, don't send.** A packet below any quality bar goes to the candidate as flagged, with
   the reason. It is sent only if the candidate decides so (status `approved-override`).
10. **Never commit personal data.** `profile/`, `data/`, `applications/`, `drafts/`, `inputs/`
    and `reports/` are git-ignored. Keep them that way.

## How skills work

Each skill is a folder in `.claude/skills/<name>/` with a `SKILL.md`. The front matter
`description` says when to use it; the body is the procedure. When a request matches a
skill's description, open that `SKILL.md` and follow it step by step. Do not improvise a
shortcut around a skill; the quality gate in particular is never skipped.

The index of all skills, in pipeline order, is [.claude/skills/README.md](.claude/skills/README.md).
The command-line tools are documented in [scripts/README.md](scripts/README.md).

## The daily pipeline

```
job-discover -> job-score -> resume-tailor -> quality-gate -> review queue -> apply-assist -> application-tracker
                                              (fact-check, humanize,          (after the candidate
                                               recruiter-read, ats-check)      approves by name)
```

Start from `.claude/skills/job-search-run/SKILL.md`, which runs the whole day.

## Roles (Discoverer, Scorer, Writer, Verifier, Filler)

The pipeline is split into roles so job descriptions and drafts do not crowd one context, and
so the reviewer is not the author. Role prompts are in `.claude/agents/*.md`; the mapping is in
`config/agents.json`.

| Role | Skills | Rule |
|---|---|---|
| HQ (main session) | job-search-run, apply-assist, application-tracker, feedback-learn, profile-intake | The only role that talks to the candidate |
| Discoverer | job-discover | Reads no job descriptions; returns counts and scoring batches |
| Scorer | job-score | One per batch, in parallel; returns a ranked table only |
| Writer | resume-tailor, cover-letter | Uses only the fact bank |
| Verifier | quality-gate and its four passes | Never checks a packet it wrote |
| Filler | apply-assist | One per approved form, in parallel, in its own browser tab; never submits |

**In Claude Code** these are sub-agents, started automatically.

**In Codex or another agent without sub-agents**, run each role as its own session so the
Verifier still reads the packet fresh. For example:

```bash
codex exec "Act as the Discoverer in .claude/agents/discoverer.md. Run job-discover and return the scoring batches."
```

```bash
codex exec "Act as a Scorer in .claude/agents/scorer.md. Run job-score on these keys: <KEY>, <KEY>."
```

```bash
codex exec "Act as the Writer in .claude/agents/writer.md. Tailor applications/<folder> for job key <KEY>."
```

```bash
codex exec "Act as the Verifier in .claude/agents/verifier.md. Run quality-gate on applications/<folder>."
```

Then, in an interactive session, present the review queue and wait for approvals. If you must
run everything in one session, do the Verifier step only after re-reading the packet from disk,
and say in `review.md` that the check was not independent.

## Tracing and the monitor

- Each skill logs `start`, `end` and `handoff` with `python3 scripts/trace.py` (the exact calls
  are in each skill). This works from any agent.
- `scripts/hook_trace.py` adds per-tool-call tracing through Claude Code hooks. Other agents
  skip it; the monitor still works from the skill-level trace.
- `python3 scripts/monitor.py` serves the dashboard on http://127.0.0.1:8765 (local only).

## Filling forms

`apply-assist` needs a browser the agent can drive. If none is available, stop after the
review queue: the candidate applies by hand with the files in `applications/<folder>/`
(`resume.md`, the built `.docx`, and `answers.md` with every form answer and its source).

## Setup

See [README.md](README.md#setup). In short: copy `examples/profile` to `profile/` and replace it
with real facts, copy `examples/watchlist.csv` to `data/watchlist.csv`, edit
`config/discovery.json`. Python 3.9+, standard library only.

## Checking your work

There is no build step. Before finishing a change to a script, run it with `--help` and on the
demo data (`python3 scripts/demo_data.py`, then the command you changed). Before finishing any
application packet, the quality gate must have run and written its verdict in `review.md`.
