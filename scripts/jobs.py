"""Job store for the job-search skills. Standard library only.

  python3 scripts/jobs.py discover            poll every company in data/watchlist.csv
  python3 scripts/jobs.py probe ATS SLUG      check that a company board exists (ats: greenhouse|lever|ashby)
  python3 scripts/jobs.py prefilter [--apply]  mark unscored postings that hit a plain-text hard stop as excluded (dry run without --apply)
  python3 scripts/jobs.py shortlist [--limit N]  best unscored postings by keyword pre-rank and freshness, max two per company
  python3 scripts/jobs.py list [--status S]   one JSON line per job, without descriptions
  python3 scripts/jobs.py show KEY            full record, with description
  python3 scripts/jobs.py mark KEY [--status S] [--score N] [--verdict V] [--notes TEXT] [--with-siblings]
  python3 scripts/jobs.py add                 add a job the user pasted; reads one JSON object on stdin

Only the public job-board endpoints that employers publish are read: one request per company
per run, with a pause between companies. Nothing here logs in anywhere or submits anything.
"""
import argparse
import csv
import html
import json
import re
import sqlite3
import sys
import time
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "jobs.db"
WATCHLIST = ROOT / "data" / "watchlist.csv"
CONFIG = ROOT / "config" / "discovery.json"
PAUSE_SECONDS = 1.5
USER_AGENT = "personal-job-search/1.0 (single user, low volume)"

ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true",
}
# Statuses a later run may overwrite to "closed" when the posting disappears.
OPEN_STATUSES = ("new", "scored", "queued")


def fetch(ats, slug):
    req = urllib.request.Request(ENDPOINTS[ats].format(slug=slug), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def plain(text):
    """HTML (possibly entity-escaped, as Greenhouse sends it) to readable text."""
    text = html.unescape(text or "")
    text = re.sub(r"<(br|/p|/li|/h\d|/div)[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"<li[^>]*>", "- ", text, flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def normalize(ats, slug, data):
    """Yield one dict per posting, in the same shape for every ATS."""
    if ats == "greenhouse":
        for j in data.get("jobs", []):
            yield {
                "id": str(j["id"]),
                "title": j["title"],
                "location": (j.get("location") or {}).get("name", ""),
                "url": j.get("absolute_url", ""),
                "posted": j.get("first_published") or j.get("updated_at") or "",
                "description": plain(j.get("content")),
                "comp": "",
            }
    elif ats == "lever":
        for j in data:
            cats = j.get("categories") or {}
            places = cats.get("allLocations") or [cats.get("location", "")]
            lists = "\n\n".join(f"{l.get('text', '')}\n{plain(l.get('content'))}" for l in j.get("lists", []))
            posted = j.get("createdAt")
            yield {
                "id": j["id"],
                "title": j["text"],
                "location": "; ".join(p for p in places if p) + (f" ({j['workplaceType']})" if j.get("workplaceType") else ""),
                "url": j.get("hostedUrl", ""),
                "posted": datetime.fromtimestamp(posted / 1000, timezone.utc).isoformat() if posted else "",
                "description": "\n\n".join(x for x in (j.get("descriptionPlain", ""), lists, j.get("additionalPlain", "")) if x).strip(),
                "comp": (j.get("salaryRange") and json.dumps(j["salaryRange"])) or "",
            }
    elif ats == "ashby":
        for j in data.get("jobs", []):
            places = [j.get("location", "")] + [s.get("location", "") for s in j.get("secondaryLocations", [])]
            yield {
                "id": j["id"],
                "title": j["title"],
                "location": "; ".join(p for p in places if p) + (" (Remote)" if j.get("isRemote") else ""),
                "url": j.get("jobUrl", ""),
                "posted": j.get("publishedAt", ""),
                "description": j.get("descriptionPlain") or plain(j.get("descriptionHtml")),
                "comp": (j.get("compensation") or {}).get("compensationTierSummary") or "",
            }


def tier_for(title, location, cfg):
    """'core' or 'stretch' when the title and at least one listed location fit the user's targets, else None."""
    def in_target(place):
        wanted = re.search(cfg["location_include"], place, re.I) or re.search(cfg["location_include_case_sensitive"], place)
        return wanted and not re.search(cfg["location_exclude"], place, re.I)

    if re.search(cfg["title_exclude"], title, re.I) or not any(in_target(p) for p in re.split(r"[;|]", location)):
        return None
    if re.search(cfg["title_core"], title, re.I):
        return "core"
    if re.search(cfg["title_stretch"], title, re.I):
        return "stretch"
    return None


def age_days(posted):
    """Days since the posting went up, or None when the board gave no usable date."""
    try:
        return (datetime.now(timezone.utc).date() - date.fromisoformat((posted or "")[:10])).days
    except ValueError:
        return None


def freshness_bonus(days):
    """Newer postings first: a fresh posting outranks a stale one with a few more keyword hits."""
    if days is None:
        return 0
    return 3 if days <= 14 else 0 if days <= 90 else -3 if days <= 180 else -6


def prescore(row, cfg):
    """Cheap keyword ranking so that only the most promising postings get a full read."""
    text = row["description"].lower()
    hits = [k for k in cfg["skill_keywords"] if k in text]
    years = [int(y) for y in re.findall(r"(\d{1,2})\+\s*years", text) if int(y) < 20]
    asked = max(years) if years else 0  # the largest "N+ years" is usually the headline requirement
    flags = []
    if re.search(cfg["no_sponsorship"], text, re.I):
        flags.append("sponsorship or citizenship wording - read closely")
    if asked >= 7:
        flags.append(f"asks for {asked}+ years")
    level_penalty = 4 if asked >= 5 else 0
    days = age_days(row["posted"])
    return {"prescore": len(hits) + (5 if row["tier"] == "core" else 0) - level_penalty - 10 * len(flags) + freshness_bonus(days),
            "age_days": days, "years_asked": asked, "skill_hits": hits, "flags": flags}


US_PLACE = re.compile(r"(?i:united states|\busa\b|remote - us)|\bUS\b|, ?(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)\b")
# For a candidate who already holds a transferable work visa (config "visa_transfer_ok": true), a posting that
# supports visa transfers is not a stop even when it refuses new sponsorship.
TRANSFER_OK = re.compile(r"(support|accept|consider)\w*\s+(h-?1b\s+|visa\s+)?transfers?", re.I)
CLEARANCE_REQUIRED = re.compile(r"\b(requires?|required|active|obtain|must|eligib\w*|hold)\b", re.I)


def pay_top_usd(row):
    """Top of a stated USD base range, or None. Reads the comp field first, then the description."""
    for text in (row["comp"] or "", row["description"] or ""):
        m = re.search(r"\$\s?(\d[\d,]*(?:\.\d+)?)\s?([kK])?\s*(?:-|–|—|to)\s*\$?\s?(\d[\d,]*(?:\.\d+)?)\s?([kK])?", text)
        if m:
            top = float(m.group(3).replace(",", "")) * (1000 if m.group(4) or m.group(2) else 1)
            if 20000 <= top <= 2000000:  # skip hourly rates and stray numbers
                return int(top)
    return None


def hard_stop(row, cfg):
    """The job-score hard stops that plain text can show for certain. Returns a reason, or None.
    Anything ambiguous returns None and is left for a full read."""
    text, title = row["description"] or "", row["title"]
    m = re.search(cfg["no_sponsorship"], text, re.I) if cfg.get("needs_sponsorship") and cfg.get("no_sponsorship") else None
    if m:
        context = text[max(0, m.start() - 60):m.end() + 40]
        is_clearance = "clearance" in m.group(0).lower()
        transfer_ok = cfg.get("visa_transfer_ok") and TRANSFER_OK.search(text) and not is_clearance
        if not transfer_ok and not (is_clearance and not CLEARANCE_REQUIRED.search(context)):
            return f"sponsorship or clearance wording: \"{context.strip()}\""
    m = re.search(cfg["client_facing_title"], title, re.I) if cfg.get("client_facing_title") else None
    # The title alone is not enough: some teams with these titles build internal product. Require customer-heavy duties too.
    if m and len(re.findall(r"\b(customers?|clients?)\b", text, re.I)) >= 5:
        return f"client-facing title ({m.group(0)}) and customer-facing duties; excluded in config"
    m = re.search(cfg["client_facing_text"], text, re.I) if cfg.get("client_facing_text") else None
    if m:
        return f"client-facing duties: \"{m.group(0)}\"; excluded in config"
    top = pay_top_usd(row)
    if top and cfg.get("us_pay_floor_usd") and top < cfg["us_pay_floor_usd"] and US_PLACE.search(row["location"]) and "£" not in text and "€" not in text:
        return f"top of stated pay range ${top:,} is below the ${cfg['us_pay_floor_usd']:,} US floor"
    return None


def prefilter(args):
    """Mark postings that hit a hard stop as excluded, so full scoring goes to the rest. Dry run unless --apply."""
    cfg = json.loads(CONFIG.read_text())
    con = db()
    rows = con.execute("SELECT * FROM jobs WHERE status = 'new'").fetchall()
    stopped = [(r, reason) for r, reason in ((r, hard_stop(r, cfg)) for r in rows) if reason]
    today = datetime.now(timezone.utc).date().isoformat()
    for r, reason in stopped:
        print(json.dumps({"key": r["key"], "company": r["company"], "title": r["title"], "reason": reason}))
        if args.apply:
            con.execute("UPDATE jobs SET status = 'excluded', score = 0, verdict = ?, notes = ? WHERE key = ?",
                        (f"Pre-filter: {reason}", f"Excluded by the pre-filter on {today}, not read in full. Reverse with mark --status new.", r["key"]))
    con.commit()
    print(json.dumps({"unscored": len(rows), "hard_stops": len(stopped), "left_for_scoring": len(rows) - len(stopped), "applied": args.apply}))


def shortlist(args):
    cfg = json.loads(CONFIG.read_text())
    rows = db().execute("SELECT * FROM jobs WHERE status = 'new'").fetchall()
    ranked = sorted(({**{k: r[k] for k in ("key", "company", "title", "location", "tier", "comp", "posted", "url")}, **prescore(r, cfg)} for r in rows),
                    key=lambda j: -j["prescore"])
    seen, titles, out = {}, set(), []
    for j in ranked:  # one row per company and title (other locations are siblings), two titles per company
        if (j["company"], j["title"]) in titles or seen.get(j["company"], 0) >= 2:
            continue
        titles.add((j["company"], j["title"]))
        seen[j["company"]] = seen.get(j["company"], 0) + 1
        out.append(j)
    for j in out[: args.limit]:
        print(json.dumps(j))


def db():
    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute(
        """CREATE TABLE IF NOT EXISTS jobs (
            key TEXT PRIMARY KEY, company TEXT, ats TEXT, title TEXT, location TEXT, url TEXT,
            posted TEXT, tier TEXT, description TEXT, comp TEXT, first_seen TEXT, last_seen TEXT,
            status TEXT DEFAULT 'new', score INTEGER, verdict TEXT, notes TEXT)"""
    )
    return con


def upsert(con, key, company, ats, job, tier, now):
    """Insert or refresh a posting. Returns True when it is new."""
    is_new = con.execute("SELECT 1 FROM jobs WHERE key = ?", (key,)).fetchone() is None
    con.execute(
        """INSERT INTO jobs (key, company, ats, title, location, url, posted, tier, description, comp, first_seen, last_seen)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(key) DO UPDATE SET title = excluded.title, location = excluded.location, url = excluded.url,
             description = excluded.description, comp = excluded.comp, last_seen = excluded.last_seen""",
        (key, company, ats, job["title"], job["location"], job["url"], job["posted"], tier, job["description"], job["comp"], now, now),
    )
    return is_new


def discover(_args):
    cfg = json.loads(CONFIG.read_text())
    con = db()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    new_jobs, failed = [], []
    with WATCHLIST.open() as f:
        companies = [r for r in csv.DictReader(f) if r["ats"] in ENDPOINTS]
    for i, c in enumerate(companies):
        if i:
            time.sleep(PAUSE_SECONDS)
        try:
            data = fetch(c["ats"], c["slug"])
        except Exception as e:  # one bad board must not stop the run
            failed.append(f"{c['company']}: {e}")
            continue
        for job in normalize(c["ats"], c["slug"], data):
            tier = tier_for(job["title"], job["location"], cfg)
            if not tier:
                continue
            key = f"{c['ats']}:{c['slug']}:{job['id']}"
            if upsert(con, key, c["company"], c["ats"], job, tier, now):
                new_jobs.append({"key": key, "company": c["company"], "title": job["title"], "location": job["location"], "tier": tier})
        marks = ",".join("?" * len(OPEN_STATUSES))
        con.execute(
            f"UPDATE jobs SET status = 'closed' WHERE company = ? AND ats = ? AND last_seen < ? AND status IN ({marks})",
            (c["company"], c["ats"], now, *OPEN_STATUSES),
        )
        con.commit()
    print(json.dumps({"companies_polled": len(companies) - len(failed), "failed": failed, "new_matches": new_jobs}, indent=1))


def probe(args):
    jobs = list(normalize(args.ats, args.slug, fetch(args.ats, args.slug)))
    print(json.dumps({"ats": args.ats, "slug": args.slug, "open_jobs": len(jobs)}))


def list_jobs(args):
    con = db()
    where, params = ("WHERE status = ?", (args.status,)) if args.status else ("", ())
    cols = "key, company, title, location, tier, comp, posted, first_seen, status, score, verdict, url"
    for row in con.execute(f"SELECT {cols} FROM jobs {where} ORDER BY score DESC, first_seen DESC", params):
        print(json.dumps(dict(row)))


def show(args):
    row = db().execute("SELECT * FROM jobs WHERE key = ?", (args.key,)).fetchone()
    if not row:
        sys.exit(f"no job with key {args.key}")
    print(json.dumps(dict(row), indent=1))


def mark(args):
    fields = {k: getattr(args, k) for k in ("status", "score", "verdict", "notes") if getattr(args, k) is not None}
    if not fields:
        sys.exit("nothing to change")
    con = db()
    cur = con.execute(f"UPDATE jobs SET {', '.join(f'{k} = ?' for k in fields)} WHERE key = ?", (*fields.values(), args.key))
    if not cur.rowcount:
        sys.exit(f"no job with key {args.key}")
    if args.with_siblings:  # the same posting listed for other locations, not yet scored
        row = con.execute("SELECT company, title FROM jobs WHERE key = ?", (args.key,)).fetchone()
        con.execute(f"UPDATE jobs SET {', '.join(f'{k} = ?' for k in fields)} WHERE company = ? AND title = ? AND status = 'new'",
                    (*fields.values(), row["company"], row["title"]))
    con.commit()


def add(_args):
    j = json.load(sys.stdin)
    job = {"title": j["title"], "location": j.get("location", ""), "url": j["url"], "posted": j.get("posted", ""),
           "description": j.get("description", ""), "comp": j.get("comp", "")}
    key = "manual:" + re.sub(r"\W+", "-", j["url"].split("//")[-1]).strip("-")[:120]
    con = db()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    is_new = upsert(con, key, j["company"], "manual", job, j.get("tier", "core"), now)
    con.commit()
    print(json.dumps({"key": key, "new": is_new}))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("discover").set_defaults(fn=discover)
    s = sub.add_parser("probe"); s.add_argument("ats", choices=ENDPOINTS); s.add_argument("slug"); s.set_defaults(fn=probe)
    s = sub.add_parser("list"); s.add_argument("--status"); s.set_defaults(fn=list_jobs)
    s = sub.add_parser("show"); s.add_argument("key"); s.set_defaults(fn=show)
    s = sub.add_parser("mark"); s.add_argument("key"); s.add_argument("--status"); s.add_argument("--score", type=int)
    s.add_argument("--verdict"); s.add_argument("--notes"); s.add_argument("--with-siblings", action="store_true"); s.set_defaults(fn=mark)
    sub.add_parser("add").set_defaults(fn=add)
    s = sub.add_parser("shortlist"); s.add_argument("--limit", type=int, default=40); s.set_defaults(fn=shortlist)
    s = sub.add_parser("prefilter"); s.add_argument("--apply", action="store_true"); s.set_defaults(fn=prefilter)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
