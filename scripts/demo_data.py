"""Fill data/ with fictional demo data so the monitor can be tried without a real search.

  python3 scripts/demo_data.py            write demo jobs, application log and trace (refuses if data exists)
  python3 scripts/demo_data.py --force    overwrite existing data/ files

Writes data/jobs.db, data/application-log.csv, data/trace.jsonl and data/trace-run.txt. Every
company, title and event is made up. The trace ends at the current time, so the monitor shows a
run in progress: Scout has handed off, Writer is drafting, Verifier is checking. Standard library only.
"""
import argparse, csv, datetime, json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jobs  # noqa: E402

ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
LOG = os.path.join(DATA, "application-log.csv")
TRACE = os.path.join(DATA, "trace.jsonl")
RUN = os.path.join(DATA, "trace-run.txt")

COMPANIES = ["Northwind Data", "Contoso Health", "Fabrikam Robotics", "Tailspin Freight", "Wingtip Labs",
             "Adventure Works", "Litware Energy", "Proseware Finance", "Woodgrove Retail", "Lamna Media"]
TITLES = ["Data Engineer", "Senior Data Engineer", "Analytics Engineer", "ML Platform Engineer",
          "Machine Learning Engineer", "Data Platform Engineer", "Backend Engineer, Data"]
LOCATIONS = ["Remote (US)", "New York, NY", "Chicago, IL", "Seattle, WA", "Austin, TX"]


def iso(t):
    return t.isoformat(timespec="seconds")


def make_jobs(rng, now):
    if os.path.exists(jobs.DB):
        os.remove(jobs.DB)
    con = jobs.db()
    keys = []
    for i in range(60):
        company = COMPANIES[i % len(COMPANIES)]
        slug = company.lower().replace(" ", "")
        key = f"greenhouse:{slug}:{1000 + i}"
        title = rng.choice(TITLES)
        status = rng.choices(["new", "scored", "queued", "excluded", "flagged", "applied", "closed"],
                             [20, 18, 4, 8, 3, 5, 2])[0]
        score = None if status == "new" else (0 if status == "excluded" else rng.randint(45, 92))
        verdict = {"excluded": "hard stop: outside target locations", "flagged": "gate flagged: one must-have not in fact bank"}.get(status, "")
        con.execute(
            """INSERT INTO jobs (key, company, ats, title, location, url, posted, tier, description, comp,
               first_seen, last_seen, status, score, verdict, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (key, company, "greenhouse", title, rng.choice(LOCATIONS), f"https://example.com/jobs/{1000 + i}",
             (now - datetime.timedelta(days=rng.randint(0, 20))).date().isoformat(), rng.choice(["core", "stretch"]),
             "Fictional demo posting.", "$130,000 - $170,000", iso(now), iso(now), status, score, verdict, ""))
        keys.append((key, company, title, status))
    con.commit()
    con.close()
    return keys


def make_log(rng, today):
    rows, n = [], 0
    for back in range(27, -1, -1):
        day = today - datetime.timedelta(days=back)
        # Ramp from about one a day toward the target of three.
        per_day = rng.choices([0, 1, 2, 3, 4], [3, 4, 3, 2 + (27 - back) // 6, 1])[0]
        for _ in range(per_day):
            n += 1
            company, title = rng.choice(COMPANIES), rng.choice(TITLES)
            key = f"demo-{n:03d}"
            gate = "gate verdict ready" if rng.random() > 0.15 else "gate verdict was flagged, candidate chose to send"
            rows.append({"date": day.isoformat(), "key": key, "company": company, "title": title,
                         "event": "submitted", "detail": f"applications/{key}/resume.docx; {gate}"})
            if back > 7 and rng.random() < 0.35:
                out = rng.choices(["rejected", "interview", "offer"], [6, 3, 0.3])[0]
                when = day + datetime.timedelta(days=rng.randint(3, 7))
                rows.append({"date": when.isoformat(), "key": key, "company": company, "title": title,
                             "event": out, "detail": "demo outcome"})
    rows.sort(key=lambda r: r["date"])
    with open(LOG, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["date", "key", "company", "title", "event", "detail"])
        w.writeheader()
        w.writerows(rows)
    return len(rows)


class Trace:
    def __init__(self, run, t0):
        self.run, self.t, self.events, self.n = run, t0, [], 0

    def step(self, seconds):
        self.t += datetime.timedelta(seconds=seconds)

    def add(self, **ev):
        ev.setdefault("ts", iso(self.t))
        ev.setdefault("run", self.run)
        self.events.append({k: v for k, v in ev.items() if v not in (None, {}, "")})

    def tool(self, agent, tool, kind, label, secs=4, close=True):
        self.n += 1
        tid = f"demo_tool_{self.n:04d}"
        self.add(event="tool", phase="pre", tool=tool, kind=kind, label=label, agent=agent, id=tid)
        self.step(secs)
        if close:
            self.add(event="tool", phase="post", tool=tool, kind=kind, label=label, agent=agent, id=tid)
        self.step(1)


def make_trace(rng, now):
    run = "demo-run-01"
    tr = Trace(run, now - datetime.timedelta(minutes=9))
    tr.add(event="run", note="demo run")
    tr.add(event="start", skill="job-search-run")
    tr.tool("main", "Skill", "skill", "job-search-run", 2)

    # Scout: discover and score.
    tr.tool("main", "Agent", "agent", "scout: discover and score today's postings", 2)
    tr.add(event="agent_start", agent="scout", agent_id="demo-scout")
    tr.add(event="start", skill="job-discover")
    tr.tool("scout", "Bash", "shell", "Poll watchlist job boards", 25)
    tr.add(event="end", skill="job-discover", q={"polled": 10, "new": 14, "failed": 0})
    tr.add(event="start", skill="job-score")
    tr.tool("scout", "Bash", "shell", "List unscored postings", 3)
    for _ in range(4):
        tr.tool("scout", "Bash", "shell", "Show one posting", 6)
        tr.tool("scout", "Bash", "shell", "Save score and verdict", 2)
    tr.add(event="end", skill="job-score", q={"scored": 14, "queued": 2, "maybes": 3, "skipped": 9})
    tr.add(event="handoff", skill="job-score", to="resume-tailor", job="greenhouse:wingtiplabs:1004", q={"score": 86})
    tr.add(event="handoff", skill="job-score", to="resume-tailor", job="greenhouse:northwinddata:1000", q={"score": 81})
    tr.step(2)
    tr.add(event="agent_stop", agent="scout", agent_id="demo-scout")

    # Writer and Verifier: first packet complete.
    job = "greenhouse:wingtiplabs:1004"
    tr.tool("main", "Agent", "agent", "writer: tailor resume for queued posting", 2)
    tr.add(event="agent_start", agent="writer", agent_id="demo-writer-1")
    tr.add(event="start", skill="resume-tailor", job=job)
    tr.tool("writer", "Read", "file", "fact-bank.yaml", 2)
    tr.tool("writer", "Read", "file", "voice.md", 1)
    tr.tool("writer", "Write", "file", "resume.md", 20)
    tr.add(event="end", skill="resume-tailor", job=job, q={"words": 480, "new_lines": 2, "gaps": 1})
    tr.add(event="handoff", skill="resume-tailor", to="quality-gate", job=job, q={"new_lines": 2, "gaps": 1})
    tr.add(event="agent_stop", agent="writer", agent_id="demo-writer-1")

    tr.tool("main", "Agent", "agent", "verifier: run quality gate", 2)
    tr.add(event="agent_start", agent="verifier", agent_id="demo-verifier-1")
    tr.add(event="start", skill="quality-gate", job=job)
    for skill, q in (("fact-check", {"checked": 18, "failed": 0, "failed_first_pass": 1}),
                     ("humanize", {"voice": 8}),
                     ("recruiter-read", {"recruiter": 8}),
                     ("ats-check", {"terms_present": 11, "terms_total": 12, "parse_ok": 1})):
        tr.add(event="start", skill=skill, job=job)
        tr.tool("verifier", "Read", "file", "resume.md", 3)
        if skill == "ats-check":
            tr.tool("verifier", "Bash", "shell", "Build resume DOCX and check parse", 8)
        tr.add(event="end", skill=skill, job=job, q=q)
    tr.add(event="end", skill="quality-gate", job=job, q={"verdict": "ready"})
    tr.add(event="handoff", skill="quality-gate", to="apply-assist", job=job,
           q={"verdict": "ready", "failed": 0, "voice": 8, "recruiter": 8})
    tr.add(event="agent_stop", agent="verifier", agent_id="demo-verifier-1")

    # Second packet: Writer still drafting, so the map shows it live.
    job2 = "greenhouse:northwinddata:1000"
    tr.tool("main", "Agent", "agent", "writer: tailor resume for queued posting", 2, close=False)
    tr.add(event="agent_start", agent="writer", agent_id="demo-writer-2")
    tr.add(event="start", skill="resume-tailor", job=job2)
    tr.tool("writer", "Read", "file", "fact-bank.yaml", 2)
    tr.tool("writer", "Write", "file", "resume.md", 3, close=False)

    with open(TRACE, "w") as f:
        for ev in tr.events:
            f.write(json.dumps(ev) + "\n")
    with open(RUN, "w") as f:
        f.write(run)
    return len(tr.events)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)
    existing = [p for p in (jobs.DB, LOG, TRACE) if os.path.exists(p)]
    if existing and not a.force:
        sys.exit(f"data/ already has files ({', '.join(os.path.basename(str(p)) for p in existing)}). "
                 "Use --force to overwrite them with demo data.")
    rng = random.Random(a.seed)
    now = datetime.datetime.now(datetime.timezone.utc)
    n_jobs = len(make_jobs(rng, now))
    n_log = make_log(rng, datetime.date.today())
    n_tr = make_trace(rng, now)
    print(json.dumps({"jobs": n_jobs, "log_rows": n_log, "trace_events": n_tr}))


if __name__ == "__main__":
    main()
