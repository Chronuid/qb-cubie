"""Display live persisted study progress without altering the running study."""

import json
import sys
import time

from .monitor import MonitorServer
from .telemetry import snapshot


def display(args):
    previous = None
    try:
        while True:
            state = snapshot(args.study)
            if args.json:
                print(json.dumps(state, ensure_ascii=False), flush=True)
            elif sys.stdout.isatty() or previous != state.get("sequence"):
                if args.watch and sys.stdout.isatty():
                    print("\033[2J\033[H", end="")
                active = state.get("active", {})
                print(f"{state.get('study_id', 'Studie')} · {state.get('phase', 'waiting')} · {state.get('state')}")
                print(f"Läufe: {state.get('completed_runs', 0)}/{state.get('total_runs', 0)} · "
                      f"gelöst {state.get('resolved_runs', 0)} · fehlgeschlagen {state.get('failed_runs', 0)} · "
                      f"nicht verfügbar {state.get('unavailable_runs', 0)}")
                print(f"Aktiv: {active.get('task_id', '—')} · {active.get('mode', '—')} · "
                      f"Schritt {active.get('step', '—')} · {active.get('operation', '—')}")
                print(state.get("message", "Warte auf Studienstatus"), flush=True)
                if args.view:
                    print(json.dumps(state.get("agent", {}).get(args.view), indent=2, ensure_ascii=False), flush=True)
            previous = state.get("sequence")
            if not args.watch or state.get("state") in {"finished", "failed", "interrupted", "prepared"}:
                return state
            if state.get("owner_pid") and not state.get("owner_alive"):
                print("Studienprozess nicht mehr aktiv; letzter gespeicherter Zustand bleibt erhalten.", file=sys.stderr)
                return state
            time.sleep(1)
    except KeyboardInterrupt:
        return {"status": "watch_closed"}


def serve(args):
    server = MonitorServer(args.study, args.port)
    print(f"Live-Monitor: {server.start()} · Strg+C schließt die Ansicht", flush=True)
    try:
        while True:
            server.thread.join(1)
    except KeyboardInterrupt:
        return {"status": "monitor_closed"}
    finally:
        server.close()
