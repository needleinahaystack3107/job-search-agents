"""Trace log for the monitor. Standard library only.

Each skill calls this when it starts, ends, or hands work to another skill, so the monitor can
show which agent is working and how good its output was when it handed off.

  python3 scripts/trace.py run "weekend check-in"            start a new run (prints its id)
  python3 scripts/trace.py start job-score [--job KEY] [--note TEXT]
  python3 scripts/trace.py end job-score [--job KEY] [--q score=72 verdict=maybe ...] [--note TEXT]
  python3 scripts/trace.py handoff resume-tailor quality-gate [--job KEY] [--q ...] [--note TEXT]

--q takes key=value pairs: the quality of what was handed on (a score, a verdict, failed fact
claims, a voice score). Numbers are stored as numbers. Writes one JSON line per event to
data/trace.jsonl. Nothing leaves this machine.
"""
import argparse, datetime, json, os, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACE = os.path.join(ROOT, "data", "trace.jsonl")
RUN = os.path.join(ROOT, "data", "trace-run.txt")


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def current_run():
    try:
        with open(RUN) as f:
            return f.read().strip() or "none"
    except FileNotFoundError:
        return "none"


def parse_q(pairs):
    out = {}
    for p in pairs or []:
        k, _, v = p.partition("=")
        try:
            out[k] = float(v) if "." in v else int(v)
        except ValueError:
            out[k] = v
    return out


def write(ev):
    ev.setdefault("ts", now())
    ev.setdefault("run", current_run())
    with open(TRACE, "a") as f:
        f.write(json.dumps(ev) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("name", nargs="?", default="")
    for name in ("start", "end"):
        s = sub.add_parser(name); s.add_argument("skill")
        s.add_argument("--job"); s.add_argument("--note"); s.add_argument("--q", nargs="*")
    h = sub.add_parser("handoff"); h.add_argument("src"); h.add_argument("dst")
    h.add_argument("--job"); h.add_argument("--note"); h.add_argument("--q", nargs="*")
    a = ap.parse_args()

    if a.cmd == "run":
        rid = datetime.date.today().isoformat() + "-" + uuid.uuid4().hex[:6]
        with open(RUN, "w") as f:
            f.write(rid)
        write({"event": "run", "run": rid, "note": a.name})
        print(rid)
        return
    ev = {"event": a.cmd, "job": a.job, "note": a.note, "q": parse_q(a.q)}
    if a.cmd == "handoff":
        ev.update({"skill": a.src, "to": a.dst})
    else:
        ev["skill"] = a.skill
    write({k: v for k, v in ev.items() if v not in (None, {}, "")})


if __name__ == "__main__":
    main()
