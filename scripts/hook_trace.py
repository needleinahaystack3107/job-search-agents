"""Claude Code hook: log every tool call and sub-agent start/stop to data/trace.jsonl.

Wired in .claude/settings.local.json for PreToolUse, PostToolUse, PostToolUseFailure,
SubagentStart and SubagentStop. Reads the hook payload on stdin. Standard library only.

Privacy: only a short, safe label is stored - a Bash command's description, a file's base name,
a URL's host, a skill or agent name. Never command text, file contents, form values, email
bodies or search queries. Nothing leaves this machine. Never blocks a tool: always exits 0.
"""
import datetime, json, os, sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACE = os.environ.get("JOBSEARCH_TRACE") or os.path.join(ROOT, "data", "trace.jsonl")  # override for tests
AGENTS = os.path.join(ROOT, "data", "trace-agents.json")  # agent_id -> agent_type
KNOWN = {"discoverer", "scorer", "writer", "verifier"}


def label(tool, ti):
    ti = ti or {}
    if tool == "Bash":
        return (ti.get("description") or "shell command")[:70]
    if tool in ("Read", "Write", "Edit", "NotebookEdit"):
        return os.path.basename(ti.get("file_path") or "")[:70]
    if tool in ("Grep", "Glob"):
        return "search files"
    if tool == "WebFetch":
        return urlparse(ti.get("url") or "").netloc
    if tool == "WebSearch":
        return "web search"
    if tool == "Skill":
        return ti.get("skill") or ""
    if tool == "Agent":
        return f"{ti.get('subagent_type') or 'agent'}: {(ti.get('description') or '')[:50]}"
    if tool.startswith("mcp__"):
        parts = tool.split("__")
        server, name = (parts[1] if len(parts) > 1 else ""), parts[-1]
        if "Browser" in server or "chrome" in server:
            act = ti.get("action") or ""
            host = urlparse(ti.get("url") or "").netloc
            return " ".join(x for x in ("browser", name, act, host) if x)[:70]
        if name in ("speak", "listen", "start_voice", "end_voice"):
            return "voice " + name
        return name[:70]
    return ""


def tool_kind(tool):
    if tool.startswith("mcp__"):
        s = tool.split("__")[1] if "__" in tool else ""
        if "Browser" in s or "chrome" in s:
            return "browser"
        if tool.split("__")[-1] in ("speak", "listen", "start_voice", "end_voice"):
            return "voice"
        return "mcp"
    return {"Bash": "shell", "Read": "file", "Write": "file", "Edit": "file", "Grep": "file", "Glob": "file",
            "WebFetch": "web", "WebSearch": "web", "Agent": "agent", "Skill": "skill"}.get(tool, "other")


def load_map():
    try:
        with open(AGENTS) as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return {}


def save_map(m):
    tmp = AGENTS + ".tmp"
    with open(tmp, "w") as f:
        json.dump(m, f)
    os.replace(tmp, AGENTS)


def agent_of(p, amap):
    t = p.get("agent_type") or amap.get(p.get("agent_id") or "", "")
    return t if t in KNOWN else ("main" if not t else t)


def main():
    try:
        p = json.load(sys.stdin)
    except ValueError:
        return
    ev = p.get("hook_event_name", "")
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    amap = load_map()
    out = None
    if ev in ("PreToolUse", "PostToolUse", "PostToolUseFailure"):
        tool = p.get("tool_name", "")
        phase = {"PreToolUse": "pre", "PostToolUse": "post", "PostToolUseFailure": "fail"}[ev]
        out = {"event": "tool", "phase": phase, "tool": tool, "kind": tool_kind(tool),
               "label": label(tool, p.get("tool_input")), "agent": agent_of(p, amap),
               "id": p.get("tool_use_id") or ""}
    elif ev == "SubagentStart":
        aid, at = p.get("agent_id") or "", p.get("agent_type") or ""
        if aid:
            amap[aid] = at
            save_map(amap)
        out = {"event": "agent_start", "agent": at or "agent", "agent_id": aid}
    elif ev == "SubagentStop":
        aid = p.get("agent_id") or ""
        out = {"event": "agent_stop", "agent": p.get("agent_type") or amap.get(aid, "agent"), "agent_id": aid}
    if out:
        try:
            with open(os.path.join(ROOT, "data", "trace-run.txt")) as f:
                out["run"] = f.read().strip()
        except FileNotFoundError:
            out["run"] = "none"
        out["ts"] = ts
        with open(TRACE, "a") as f:
            f.write(json.dumps(out) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
