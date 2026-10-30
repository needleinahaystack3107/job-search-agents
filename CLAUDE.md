# Job search system (template)

A set of Claude Code skills and agents that finds jobs for the candidate, prepares tailored
applications, reviews them against a quality bar, and fills application forms for the candidate's
approval. The candidate must be able to trust it before using it, so correctness and restraint
matter more than volume.

Edit this file for your own search: the rules below are the defaults the skills assume.

## Standing requirements

1. **Tailored.** Everything draws on the candidate's real profile in `profile/`.
2. **Truthful.** Resume and cover-letter content is factually accurate and never fabricated.
   Every claim traces to `profile/fact-bank.yaml`.
3. **Sounds human.** Writing is simple and in the candidate's voice (`profile/voice.md`).
4. **Self-ranking.** The system scores its own output on truthfulness, voice and ATS fit.
5. **Flag, don't apply.** If a packet does not clearly meet the bar, flag it. Never submit
   something borderline.
6. **No bans.** Do not scrape or automate sites that prohibit it (for example LinkedIn, Indeed).
   Read only public employer job-board endpoints, at low volume. No stealth or detection evasion.
7. **Strong for ATS.** Clean parsing, the posting's exact terms, consistent screening answers.
8. **Learns.** Corrections and feedback are recorded and change later output.
9. **Step by step.** Ask when a decision is the candidate's to make.

## Human review points

- The candidate approves every submission through the review queue. Nothing is submitted without
  their say.
- The candidate logs in and creates accounts themselves. Never enter passwords or create accounts.
- A CAPTCHA or bot check means stop and hand over.
- Legal and demographic answers (work authorization, sponsorship, EEO) come only from
  `profile/preferences.yaml`. Never guess one.
- Exclusions in `profile/preferences.yaml` are strict. Only the candidate can loosen them.
- The search is discreet: nothing public, nothing that could reach a current employer.
- Client names from past work are never written to any file; describe them generically.

## Agents and monitoring

- Project agents in `.claude/agents/`: `discoverer` (job-discover, pre-filter, batching), `scorer`
  (job-score, one per batch, in parallel), `writer`
  (resume-tailor, cover-letter), `verifier` (quality-gate and its four passes), `filler`
  (apply-assist, one per approved form, in parallel, each in its own browser tab). The main session
  (HQ) keeps everything that talks to the candidate: it asks every form question up front,
  starts the fillers, and hands over once. Grouping is in `config/agents.json`.
- Hooks (copy `.claude/settings.example.json` to `.claude/settings.local.json`) run
  `scripts/hook_trace.py` on every tool call and sub-agent start/stop. They log safe labels only
  (descriptions, file names, hosts), never form values or message contents.
- Every skill logs its own start/end/handoff to `data/trace.jsonl` with `scripts/trace.py`.
- The monitor (`scripts/monitor.py`, launch config `monitor`) shows the agent graph live.
- Top KPI: applications per day (target in `config/agents.json`), with ranking quality as a guard
  (no fact failures, no lower gate bars). `scripts/weekly_report.py` writes `reports/weekly-<date>.md`.

## Layout

- `profile/fact-bank.yaml` - the only source of claims. `profile/preferences.yaml` - what the
  candidate wants. `profile/voice.md` - how they write.
- `inputs/` - resume and writing samples. `applications/` - one folder per packet.
- `data/watchlist.csv` - companies polled. `data/jobs.db` - postings, scores and statuses.
- `config/discovery.json` - title, location and keyword filters.
- `scripts/jobs.py` - job store (run with `--help`). `.claude/skills/` - the skills.

All of `profile/`, `inputs/`, `applications/`, `drafts/`, `data/` and `reports/` are git-ignored.

## Order of the skills

`job-search-run` runs the whole day: `job-discover` -> `job-score` -> `resume-tailor` ->
`quality-gate` (which runs `fact-check`, `humanize`, `recruiter-read`, `ats-check`) -> review
queue -> `apply-assist` after approval -> `application-tracker`. `cover-letter` is used only when
a form has a field for it. `profile-intake` and `feedback-learn` update the profile at any time.
