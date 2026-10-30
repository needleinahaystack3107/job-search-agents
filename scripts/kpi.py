"""KPIs for the job search, shared by the monitor and the weekly report. Standard library only.

Reads data/application-log.csv, data/jobs.db and data/trace.jsonl. Nothing leaves this machine.

  python3 scripts/kpi.py            print the KPI snapshot as JSON
"""
import csv, datetime, json, os, sqlite3
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "data", "application-log.csv")
DB = os.path.join(ROOT, "data", "jobs.db")
TRACE = os.path.join(ROOT, "data", "trace.jsonl")
AGENTS = os.path.join(ROOT, "config", "agents.json")
OUTCOMES = ("rejected", "interview", "offer")


def load_config():
    with open(AGENTS) as f:
        return json.load(f)


def load_log():
    try:
        with open(LOG, newline="") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []


def load_trace():
    out = []
    try:
        with open(TRACE) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        pass
    except FileNotFoundError:
        pass
    return out


def parse_ts(s):
    try:
        return datetime.datetime.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def applications(rows, today):
    subs = [r for r in rows if r["event"] == "submitted"]
    by_day = Counter(r["date"] for r in subs)
    days = [(today - datetime.timedelta(days=i)).isoformat() for i in range(27, -1, -1)]
    series = [{"date": d, "n": by_day.get(d, 0)} for d in days]
    last7 = sum(x["n"] for x in series[-7:])
    prev7 = sum(x["n"] for x in series[-14:-7])
    return {
        "series": series,
        "total": len(subs),
        "last7": last7,
        "prev7": prev7,
        "avg_per_day_7": round(last7 / 7, 2),
        "days_at_target_7": None,  # filled by caller with the target
        "first_date": min((r["date"] for r in subs), default=None),
    }


def ranking_quality(rows):
    """Per submitted application: the gate verdict at send time and the outcome so far."""
    apps = {}
    for r in rows:
        k = r["key"]
        if r["event"] == "submitted":
            d = r["detail"].lower()
            gate = "flagged" if "gate verdict was flagged" in d else ("ready" if "gate verdict ready" in d else "unknown")
            apps[k] = {"company": r["company"], "title": r["title"], "date": r["date"], "gate": gate, "outcome": "waiting"}
    for r in rows:
        if r["key"] in apps and r["event"] in OUTCOMES:
            apps[r["key"]]["outcome"] = r["event"]
    by_gate = defaultdict(Counter)
    for a in apps.values():
        by_gate[a["gate"]][a["outcome"]] += 1
    n = len(apps)
    responded = sum(1 for a in apps.values() if a["outcome"] != "waiting")
    interviews = sum(1 for a in apps.values() if a["outcome"] in ("interview", "offer"))
    return {
        "submitted": n,
        "sent_ready": sum(1 for a in apps.values() if a["gate"] == "ready"),
        "sent_flagged": sum(1 for a in apps.values() if a["gate"] == "flagged"),
        "responses": responded,
        "interviews": interviews,
        "by_gate": {g: dict(c) for g, c in by_gate.items()},
        "apps": sorted(apps.values(), key=lambda a: a["date"]),
        "note": "Under about 20 submissions older than 14 days, response rates are noise." if n < 20 else "",
    }


def store_snapshot():
    try:
        con = sqlite3.connect(DB)
        rows = con.execute("select status, count(*) from jobs group by status").fetchall()
        maybes = con.execute(
            "select company, title, score from jobs where status in ('scored','flagged') and score >= 60 order by score desc limit 10").fetchall()
        con.close()
    except sqlite3.Error:
        return {"by_status": {}, "maybes": []}
    seen, uniq = set(), []
    for c, t, s in maybes:
        if (c, t) not in seen:
            seen.add((c, t))
            uniq.append({"company": c, "title": t, "score": s})
    return {"by_status": dict(rows), "maybes": uniq}


def agent_stats(trace, cfg):
    """Per agent: calls, time spent, and the quality of what it handed on."""
    skill_to_agent = {s: a["id"] for a in cfg["agents"] for s in a["skills"]}
    stats = {a["id"]: {"calls": 0, "seconds": 0.0, "handoffs": 0, "q": defaultdict(list), "last": None} for a in cfg["agents"]}
    open_starts = {}
    for ev in trace:
        sk = ev.get("skill")
        ag = skill_to_agent.get(sk)
        if not ag:
            continue
        st = stats[ag]
        st["last"] = ev.get("ts")
        key = (sk, ev.get("job"), ev.get("run"))
        if ev["event"] == "start":
            open_starts[key] = parse_ts(ev.get("ts"))
            st["calls"] += 1
        elif ev["event"] == "end":
            t0 = open_starts.pop(key, None)
            t1 = parse_ts(ev.get("ts"))
            if t0 and t1:
                st["seconds"] += (t1 - t0).total_seconds()
        elif ev["event"] == "handoff":
            st["handoffs"] += 1
        for k, v in (ev.get("q") or {}).items():
            if isinstance(v, (int, float)):
                st["q"][k].append(v)
            elif k == "verdict":
                st["q"]["verdict_" + str(v)].append(1)
    out = {}
    for ag, st in stats.items():
        q = {}
        for k, vals in st["q"].items():
            q[k] = {"n": len(vals), "avg": round(sum(vals) / len(vals), 2), "sum": sum(vals)}
        out[ag] = {"calls": st["calls"], "minutes": round(st["seconds"] / 60, 1), "handoffs": st["handoffs"], "quality": q, "last": st["last"]}
    return out


def active_skills(trace, minutes=30):
    """Skills started and not yet ended in the last `minutes`."""
    now = datetime.datetime.now(datetime.timezone.utc)
    open_ = {}
    for ev in trace:
        key = (ev.get("skill"), ev.get("job"), ev.get("run"))
        if ev.get("event") == "start":
            open_[key] = ev
        elif ev.get("event") == "end":
            open_.pop(key, None)
    act = []
    for ev in open_.values():
        t = parse_ts(ev.get("ts"))
        if t and (now - t).total_seconds() < minutes * 60:
            act.append(ev)
    return act


def tool_activity(trace, minutes=30):
    """Hook events (scripts/hook_trace.py): live tool calls and sub-agents, per agent."""
    now = datetime.datetime.now(datetime.timezone.utc)
    evs = [e for e in trace if e.get("event") in ("tool", "agent_start", "agent_stop")]
    open_tools, open_agents = {}, {}
    for e in evs:
        if e["event"] == "tool":
            if e.get("phase") == "pre":
                open_tools[e.get("id") or id(e)] = e
            else:
                open_tools.pop(e.get("id"), None)
        elif e["event"] == "agent_start":
            open_agents[e.get("agent_id") or e.get("agent")] = e
        else:
            open_agents.pop(e.get("agent_id") or e.get("agent"), None)

    def fresh(e, mins):
        t = parse_ts(e.get("ts"))
        return t and (now - t).total_seconds() < mins * 60

    recent = [e for e in evs if fresh(e, minutes)]
    counts = defaultdict(Counter)
    for e in recent:
        if e["event"] == "tool" and e.get("phase") == "pre":
            counts[e.get("agent", "main")][e.get("kind", "other")] += 1
    return {
        "active_tools": [e for e in open_tools.values() if fresh(e, 10)],
        "active_agents": [e for e in open_agents.values() if fresh(e, 120)],
        "tail": [e for e in evs if e["event"] != "tool" or e.get("phase") != "post"][-120:],
        "counts": {a: dict(c) for a, c in counts.items()},
        "window_min": minutes,
    }


def funnel(rows, today):
    """Whole-search funnel: store stages from jobs.db, outcomes from the application log."""
    stages = {}
    try:
        con = sqlite3.connect(DB)
        q = lambda sql: con.execute(sql).fetchone()[0]
        stages["discovered"] = q("select count(*) from jobs")
        stages["in_range"] = q("select count(*) from jobs where status not in ('excluded','closed')")
        stages["scored"] = q("select count(*) from jobs where score is not null")
        stages["shortlisted"] = q("select count(*) from jobs where score >= 60")
        con.close()
    except sqlite3.Error:
        pass
    apps_dir = os.path.join(ROOT, "applications")
    stages["packets"] = sum(os.path.isdir(os.path.join(apps_dir, d)) for d in os.listdir(apps_dir)) if os.path.isdir(apps_dir) else 0

    events = defaultdict(set)
    sent_on, flagged = {}, set()
    for r in rows:
        events[r["key"]].add(r["event"])
        if r["event"] == "submitted":
            sent_on.setdefault(r["key"], r["date"])
            if "flagged" in r.get("detail", ""):
                flagged.add(r["key"])
    sent = set(sent_on)
    out = {o: sorted(k for k in sent if o in events[k]) for o in OUTCOMES}
    closed = set().union(*out.values()) if out else set()
    pending = sent - closed
    stale = {k for k in pending if (today - datetime.date.fromisoformat(sent_on[k])).days > 30}
    by_gate = {}
    for name, keys in (("ready", sent - flagged), ("override", sent & flagged)):
        by_gate[name] = {"sent": len(keys), "rejected": len(keys & set(out["rejected"])),
                         "interview": len(keys & (set(out["interview"]) | set(out["offer"])))}
    stages.update({
        "submitted": len(sent),
        "acknowledged": sum(1 for k in sent if "acknowledged" in events[k] or events[k] & set(OUTCOMES)),
        "rejected": len(out["rejected"]),
        "interview": len(out["interview"]),
        "offer": len(out["offer"]),
        "pending": len(pending - stale),
        "no_response": len(stale),
    })
    responses = len(closed)
    stages["response_rate"] = round(responses / len(sent), 3) if sent else 0
    stages["by_gate"] = by_gate
    return stages


def snapshot(today=None):
    today = today or datetime.date.today()
    cfg = load_config()
    rows = load_log()
    trace = load_trace()
    target = cfg["kpi"]["target_applications_per_day"]
    apps = applications(rows, today)
    apps["days_at_target_7"] = sum(1 for x in apps["series"][-7:] if x["n"] >= target)
    return {
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "config": cfg,
        "applications": apps,
        "ranking": ranking_quality(rows),
        "store": store_snapshot(),
        "funnel": funnel(rows, today),
        "agents": agent_stats(trace, cfg),
        "active": active_skills(trace),
        "tools": tool_activity(trace),
        "trace_tail": [e for e in trace if e.get("event") not in ("tool", "agent_start", "agent_stop")][-60:],
        "run": trace[-1].get("run") if trace else None,
    }


if __name__ == "__main__":
    print(json.dumps(snapshot(), indent=1, default=str))
