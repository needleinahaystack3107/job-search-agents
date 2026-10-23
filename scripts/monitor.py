"""Live monitor for the job search. Standard library only.

  python3 scripts/monitor.py            serve on http://127.0.0.1:8765 (local only)

Shows the agent graph (HQ / main session, Scout, Writer, Verifier), lights up whichever skill is
running, draws each handoff with the quality it carried, and shows the KPIs. The page is
scripts/monitor.html; data comes from scripts/kpi.py (trace, application log, job store).
Binds to 127.0.0.1 so nothing is reachable from outside this machine.
"""
import http.server, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kpi  # noqa: E402

PORT = int(os.environ.get("MONITOR_PORT", "8765"))
PAGE = os.path.join(HERE, "monitor.html")


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/state"):
            body = json.dumps(kpi.snapshot(), default=str).encode()
            ctype = "application/json"
        elif self.path in ("/", "/index.html"):
            with open(PAGE, "rb") as f:  # read each time, so page edits show on reload
                body = f.read()
            ctype = "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"monitor on http://127.0.0.1:{PORT}", flush=True)
    srv.serve_forever()
