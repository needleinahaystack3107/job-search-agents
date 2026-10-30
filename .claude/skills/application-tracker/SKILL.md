---
name: application-tracker
description: Record and report the state of the candidate's job applications and their outcomes. Use for "what have I applied to?", "show my review queue", "I got a rejection from X", "X wants an interview", "how is my search going?", and after any application is submitted.
---

# Application tracker

Two records: the status of each job in `data/jobs.db` (through `scripts/jobs.py`), and a dated
event log in `data/application-log.csv` with columns `date,key,company,title,event,detail`.

## Statuses

`new` → `scored` / `skipped` / `excluded` → `queued` → `ready`, `needs-you` or `flagged` (or
`approved-override`) → `submitted` → `rejected`, `interview`, `offer` or `no-response`. `closed`
means the posting was taken down before an application.

## Record an event

1. Find the job with `python3 scripts/jobs.py list` and match company and title.
2. `python3 scripts/jobs.py mark <key> --status <status>`.
3. Append a line to `data/application-log.csv`. For a submission, put the resume file path and the
   gate verdict ("gate verdict ready" or "gate verdict was flagged") in `detail`; the KPI script
   reads that phrase.
4. Hand rejections, interviews and offers to `feedback-learn`.

## Report

Review queue (`needs-you` first with its question, then `ready` and `flagged`, each with its verdict and `review.md`), counts by status,
submissions this week, and response rate. Under about 20 submissions, a response rate is noise;
say so.
