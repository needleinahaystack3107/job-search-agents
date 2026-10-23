"""Weekly KPI report for the job search. Standard library only.

  python3 scripts/weekly_report.py         write reports/weekly-<date>.md and print its path

Top KPI: applications per day (target in config/agents.json), with ranking quality held as a
guard so volume never rises by sending weaker packets. Per-agent handoff quality comes from
data/trace.jsonl. Small numbers are labelled as such; nothing here is a trend until it is.
"""
import datetime, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpi  # noqa: E402

ROOT = kpi.ROOT


def main():
    s = kpi.snapshot()
    today = datetime.date.today()
    ap, rk, cfg = s["applications"], s["ranking"], s["config"]
    tg = cfg["kpi"]["target_applications_per_day"]
    g = cfg["kpi"]["guards"]
    lines = [
        f"# Weekly job-search review, {today.isoformat()}",
        "",
        "## Top KPI: applications per day",
        "",
        f"- Last 7 days: **{ap['last7']}** ({ap['avg_per_day_7']}/day). Previous 7 days: {ap['prev7']}.",
        f"- Days at or above the target of {tg}: **{ap['days_at_target_7']} of 7**.",
        "- By day: " + ", ".join(f"{x['date'][5:]} {x['n']}" for x in ap["series"][-7:]),
        "",
        "## Guard: ranking quality (volume must not rise by lowering this)",
        "",
        f"- Submitted so far: {rk['submitted']} ({rk['sent_ready']} sent with a ready verdict, {rk['sent_flagged']} sent over a flag).",
        f"- Responses: {rk['responses']}; interviews: {rk['interviews']}.",
    ]
    for gate, c in rk["by_gate"].items():
        lines.append(f"- Gate `{gate}` at send time: " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())))
    if rk["note"]:
        lines.append(f"- {rk['note']}")
    lines += ["", "## Agents: handoff quality this far", ""]
    lines.append("| Agent | Runs | Minutes | Handoffs | Quality carried on handoff |")
    lines.append("|---|---|---|---|---|")
    for a in cfg["agents"]:
        st = s["agents"][a["id"]]
        q = ", ".join(f"{k} {v['avg']} (n={v['n']})" for k, v in st["quality"].items()) or "no data yet"
        lines.append(f"| {a['name']} | {st['calls']} | {st['minutes']} | {st['handoffs']} | {q} |")
    v = s["agents"]["verifier"]["quality"]
    lines += ["", "Guards from config: fact-check failures "
              f"{g['fact_check_failures']}, voice at least {g['min_voice']}, recruiter read at least {g['min_recruiter']}."]
    if v:
        ff = v.get("failed_first_pass", {}).get("sum")
        lines.append(f"Writer claims caught by the Verifier on first pass: {ff if ff is not None else 'not logged'}.")
    lines += ["", "## Store", ""]
    lines.append("- Status counts: " + ", ".join(f"{k} {n}" for k, n in sorted(s["store"]["by_status"].items())))
    lines.append("- Best maybes: " + "; ".join(f"{m['company']} {m['title']} ({m['score']})" for m in s["store"]["maybes"][:6]))
    lines += ["", "## For Claude to add when presenting this",
              "", "- What limited volume this week (too few postings above 75, flags, the candidate's time, forms).",
              "- One change to try next week, and how its effect on the guards will be checked.", ""]
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    path = os.path.join(ROOT, "reports", f"weekly-{today.isoformat()}.md")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(path)


if __name__ == "__main__":
    main()
