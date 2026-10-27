# Scripts

Python 3.9+, standard library only. Run from the repo root. Every script reads and writes under
`data/`, `applications/` or `reports/` on your machine; nothing is sent anywhere except the
public job-board requests in `jobs.py discover` and `probe`.

## jobs.py: the job store

`data/jobs.db` (SQLite) holds every posting, its score, verdict and status.

```bash
python3 scripts/jobs.py probe greenhouse <board-slug>
```
Check that a company's public board exists (`greenhouse`, `lever` or `ashby`) before adding it
to `data/watchlist.csv`.

```bash
python3 scripts/jobs.py discover
```
Poll every company in the watchlist: one request per company, with a pause between them.

```bash
python3 scripts/jobs.py prefilter
```
Dry run: list unscored postings that hit a plain-text hard stop (no sponsorship, client-facing
title, pay below the floor), using the patterns in `config/discovery.json`. Add `--apply` to mark
them `excluded`.

```bash
python3 scripts/jobs.py shortlist --limit 30
```
Best unscored postings by keyword pre-rank and freshness, at most two per company.

```bash
python3 scripts/jobs.py list --status queued
```
One JSON line per job, without descriptions. `show KEY` prints one full record.

```bash
python3 scripts/jobs.py mark KEY --status flagged --notes "degree must-have"
```
Also takes `--score`, `--verdict` and `--with-siblings`. `add` reads one JSON object on stdin for
a posting the candidate pasted.

## resume_doc.py: the resume file

```bash
python3 scripts/resume_doc.py build applications/<folder>/resume.md
```
Writes `Last_First_Resume_<MonYYYY>.docx` beside it: single column, no tables or text boxes.

```bash
python3 scripts/resume_doc.py check applications/<folder>/<file>.docx --keywords "dbt,Airflow"
```
Reads the DOCX back as a parser would, reports the word count against the one-page limit, and
which keywords were found.

## trace.py: the run log

```bash
python3 scripts/trace.py run "daily run"
```
Starts a run. Skills then log `start <skill>`, `end <skill> --q key=value ...` and
`handoff <from> <to> --q ...` (see each `SKILL.md`). Writes `data/trace.jsonl`.

## hook_trace.py: per-tool tracing (Claude Code only)

Wired as hooks by `.claude/settings.example.json`. Logs safe labels only (a command's
description, a file's base name, a host), never contents. Other agents can ignore it.

## monitor.py, monitor.html, kpi.py: the dashboard

```bash
python3 scripts/monitor.py
```
Serves http://127.0.0.1:8765 (local only; `MONITOR_PORT` changes the port). Shows the agent map
with live handoffs, tool calls per agent, and KPIs. `python3 scripts/kpi.py` prints the same
numbers as JSON.

## weekly_report.py

```bash
python3 scripts/weekly_report.py
```
Writes `reports/weekly-<date>.md`: applications per day against the target in
`config/agents.json`, with the quality guards beside it.

## demo_data.py

```bash
python3 scripts/demo_data.py
```
Fills `data/` with fictional companies and events so the monitor can be tried before a real
search. Refuses to overwrite existing data unless given `--force`.
