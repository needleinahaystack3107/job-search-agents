---
name: job-search-run
description: Run the candidate's job search for the day - find new postings, score them, prepare the best applications and present the review queue. Use for "run my job search", "do today's job search", "find me new jobs and prep the best one", "what should I apply to today?".
---

# Daily job search run

The whole pipeline in order. Each step is its own skill; follow that skill when you reach it.
Read `CLAUDE.md` first for the standing rules.

0. **Open the monitor and start a trace run.** Run `python3 scripts/trace.py run "<short name>"`,
   then open the monitor (`python3 scripts/monitor.py`, or the `monitor` entry in
   `.claude/launch.json`). Log your own steps with `scripts/trace.py`; the agents log theirs, and
   the hooks log every tool call.

**Agents.** Discovery and scoring go to the `scout` agent. Tailoring goes to the `writer` agent,
one per posting. The quality gate goes to the `verifier` agent, one per packet, after its writer
is done. Spawn them with the Agent tool so job descriptions and drafts stay out of the main
session's context. Everything that talks to the candidate (questions, forms, the tracker) stays in
the main session; relay the agents' questions.

1. **Check usage.** Report plan usage. If it is high, say so and ask before continuing.
2. **Tracker first.** With `application-tracker`, show what is `ready`, `flagged` or `queued`, and
   how many applications went out today.
3. **Discover** with `job-discover` (scout), unless it already ran today.
4. **Pre-filter, then score** with `job-score` (scout): `python3 scripts/jobs.py prefilter`, check
   the reasons, then `--apply`; score at most 30 postings per run, newest first.
5. **Pick** the highest-scoring `queued` postings, one per company at a time.
6. **Tailor** each with `resume-tailor` (writer), then `quality-gate` (verifier).
7. **Present the review queue**: verdict, score, gaps, screening answers, links to `resume.md` and
   `review.md`. List flagged packets separately with the reason.
8. **Stop.** Ask which packets the candidate approves. Only then does `apply-assist` begin.
9. **Batch the manual parts.** Before filling anything, read every approved form and ask all the
   questions that need the candidate at once. Then fill each approved form and hand over once for
   file attachments, bot checks and Submit.

Never skip the quality gate to save time, and never start a form without approval for that
specific application.
