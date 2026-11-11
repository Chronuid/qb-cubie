"""Serve a loopback-only read-only monitor and archived public agent steps."""

import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .artifacts import read
from .telemetry import snapshot


def run_view(root, run_id, step=None):
    if not re.fullmatch(r"\d{4,}", run_id):
        raise ValueError("Invalid run ID")
    root = Path(root).resolve()
    state = snapshot(root)
    study = (root / state.get("study_path", ".")).resolve()
    if not study.is_relative_to(root):
        raise ValueError("Study path is outside the monitor root")
    schedule = read(study / "schedule.json")
    row = next((row for row in schedule if row["run_id"] == run_id), None)
    if row is None:
        raise ValueError("Unknown run")
    directory = study / "runs" / run_id / "steps"
    steps = sorted(int(path.name.split("-")[0]) for path in directory.glob("*-request.json"))
    if step is None:
        step = steps[-1] if steps else None
    if step is not None and step not in steps:
        raise ValueError("Unknown step")
    agent = {}
    summary = directory.parent / 'agent.json'
    if summary.is_file():
        agent['stop_reason'] = read(summary).get('status')
    if step is not None:
        for key, suffix in (("context", "request"), ("response", "response"), ("result", "tool")):
            path = directory / f"{step:04d}-{suffix}.json"
            if path.is_file():
                data = read(path)
                agent[key] = data.get("result", data) if key == "result" else data
                if key == "result" and isinstance(agent[key], dict):
                    agent[key].pop("junit_xml", None)
                if key == "response":
                    agent["action"] = data.get("action")
        for previous in reversed([value for value in steps if value <= step]):
            path = directory / f'{previous:04d}-response.json'
            if path.is_file():
                response = read(path)
                if response.get('error'):
                    agent['last_error'] = {**response, 'step': previous + 1}
                    break
    return {"row": row, "step": step, "steps": steps, "agent": agent}


class MonitorServer:
    def __init__(self, root, port=0):
        self.root = Path(root).resolve()
        root_path = self.root
        self.client_seen = threading.Event()
        self.closing = threading.Event()
        self.final_delivered = threading.Event()
        monitor = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urlsplit(self.path)
                try:
                    if parsed.path == "/":
                        data = Path(__file__).with_name("monitor.html").read_bytes()
                        self.respond(data, "text/html; charset=utf-8")
                    elif parsed.path == "/api/state":
                        monitor.client_seen.set()
                        data = snapshot(root_path)
                        data["monitor_closing"] = monitor.closing.is_set()
                        self.respond(json.dumps(data).encode(), "application/json")
                        if data["monitor_closing"]:
                            monitor.final_delivered.set()
                    elif parsed.path == "/api/run":
                        query = parse_qs(parsed.query)
                        step = int(query["step"][0]) if "step" in query else None
                        data = run_view(root_path, query.get("run_id", [""])[0], step)
                        self.respond(json.dumps(data).encode(), "application/json")
                    else:
                        self.send_error(404)
                except (BrokenPipeError, ConnectionResetError):
                    # A closed browser connection cannot receive an HTTP error.
                    pass
                except (OSError, ValueError, KeyError, StopIteration):
                    self.send_error(400, "Monitor data unavailable")

            def respond(self, data, content_type):
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def url(self):
        return f"http://127.0.0.1:{self.server.server_port}"

    def start(self):
        self.thread.start()
        return self.url

    def close(self):
        # Give an attached view a bounded opportunity to receive the final state.
        self.closing.set()
        if self.thread.is_alive() and self.client_seen.is_set():
            self.final_delivered.wait(timeout=2)
        if self.thread.is_alive():
            self.server.shutdown()
        self.server.server_close()
        if self.thread.ident is not None:
            self.thread.join(timeout=5)
