---
name: job-discover
description: Find new job postings from the company watchlist, or add a posting or company the candidate mentions. Use for "find me new jobs", "check for new postings", "add this company to my watchlist", or when the candidate pastes a job link.
---

# Job discovery

Postings come from two places only: the public job-board endpoints of companies in
`data/watchlist.csv`, and links the candidate gives you. Do not scrape LinkedIn, Indeed or any
site that needs a login or prohibits automation, and do not search job aggregators with a browser.

## Find new postings

1. Run `python3 scripts/jobs.py discover`. It polls each company once, with a pause between them.
   Run it at most twice a day.
2. Report companies polled, any that failed, and how many new core and stretch matches there are.
   A board that fails twice in a row has probably moved; say so rather than guessing a new address.
3. Run `python3 scripts/jobs.py prefilter` (dry run), check the reasons, then `prefilter --apply`.
   Then `python3 scripts/jobs.py shortlist --limit 30` and hand the result to `job-score`. The
   shortlist is a keyword pre-rank only, not a recommendation.

## Add a company

1. Check the exclusions in `profile/preferences.yaml` first.
2. Find which system its careers page uses and the board name in the URL
   (`boards.greenhouse.io/<slug>`, `jobs.lever.co/<slug>`, `jobs.ashbyhq.com/<slug>`).
3. Confirm with `python3 scripts/jobs.py probe <ats> <slug>`, then append a row to
   `data/watchlist.csv`.
4. Companies on other systems cannot be polled; suggest the candidate paste links instead.

## Add a pasted link

1. If the link is to LinkedIn or another aggregator, do not open it with automation. Ask for the
   company and title, or find the posting on the employer's own careers site.
2. Pipe one JSON object to `python3 scripts/jobs.py add` with `company`, `title`, `url`,
   `location`, `description` and, if stated, `comp`. Hand the new key to `job-score`.

Title and location patterns are in `config/discovery.json`. Change them only when the candidate
asks for a different role or location scope.
