import argparse
import errno
import json
from pathlib import Path
import sys

from .core import DEFAULT_HOME, Store
from .editorial import prompt


def main():
    parser = argparse.ArgumentParser(description="Your evidence-led personal briefing")
    parser.add_argument("--home", type=Path, default=DEFAULT_HOME, help="Private data directory (default: ignored .local/)")
    sub = parser.add_subparsers(dest="action", required=True)
    p = sub.add_parser("init", help="Create private settings; existing settings are preserved")
    p.add_argument("--config", type=Path, help="Start from a shared newsletter configuration")
    sub.add_parser("doctor", help="Check local prerequisites without calling a model")
    p = sub.add_parser("export", help="Export your newsletter settings, without history or credentials")
    p.add_argument("file", type=Path)
    p = sub.add_parser("export-briefing", help="Save an edition as readable Markdown (latest by default)")
    p.add_argument("file", type=Path)
    p.add_argument("--issue", help="Saved edition ID; omit for the latest")
    p = sub.add_parser("serve", help="Open the local reading and setup interface")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--open-browser", action="store_true", help="Open the reader automatically; reuse this newsletter if already running")
    for action in ("collect", "run"):
        p = sub.add_parser(action)
        p.add_argument("--days", type=int, default=1)
    sub.add_parser("generate", help="Write and review a briefing from the current evidence")
    sub.add_parser("packet", help="Print the evidence packet for the current Codex conversation")
    sub.add_parser("prompt", help="Print the complete editorial prompt and evidence")
    p = sub.add_parser("publish", help="Validate and save an issue written in this Codex conversation")
    p.add_argument("file", type=Path)
    p = sub.add_parser("import", help="Add explicitly supplied evidence JSON to the current packet")
    p.add_argument("file", type=Path)
    p = sub.add_parser("evidence", help="Fetch a supporting page or YouTube transcript into the packet")
    p.add_argument("url")
    p.add_argument("--title", required=True)
    p.add_argument("--published", default="", help="Only set when the publication date is verified")
    p.add_argument("--youtube", action="store_true")
    sub.add_parser("latest")
    args = parser.parse_args()
    store = Store(args.home)
    try:
        if args.action == "init":
            store.init(args.config)
            print(f"Private settings: {store.config_path}")
        elif args.action == "doctor":
            from .setup import check_setup
            store.init()
            for check in check_setup(store.config()):
                print(f"{check['status'].upper()} — {check['name']}: {check['detail']}")
        elif args.action == "export":
            store.export_config(args.file)
            print(f"Saved {args.file}. Contains your profile and source URLs; review before sharing.")
        elif args.action == "export-briefing":
            store.export_issue(args.file, args.issue)
            print(f"Saved briefing: {args.file}")
        elif args.action == "serve":
            from .server import make_server, reader_is_running
            import webbrowser
            if not store.config_path.exists():
                store.init()
            try:
                server = make_server(store, args.port)
            except OSError as exc:
                if args.open_browser and exc.errno == errno.EADDRINUSE and reader_is_running(store, args.port):
                    webbrowser.open(f"http://127.0.0.1:{args.port}")
                    print("Your newsletter is already running. Opened its reader.")
                    return
                if exc.errno == errno.EADDRINUSE:
                    raise ValueError("That port is occupied. Use serve --port 8767, or stop the other server first.") from exc
                raise
            print(f"Open http://127.0.0.1:{server.server_port} — keep this terminal running", flush=True)
            try:
                if args.open_browser:
                    webbrowser.open(f"http://127.0.0.1:{server.server_port}")
                server.serve_forever()
            finally:
                server.server_close()
        elif args.action in ("collect", "run"):
            store.collect(args.days, lambda text: print(text, flush=True))
            if args.action == "run":
                issue = store.generate(lambda text: print(text, flush=True))
                print(f"Saved issue: {issue['id']}")
            else:
                print(f"Collected {len(store.packet()['items'])} evidence items. See packet.json for coverage.")
        elif args.action == "generate":
            issue = store.generate(lambda text: print(text, flush=True))
            print(f"Saved issue: {issue['id']}")
        elif args.action == "packet":
            print(json.dumps(store.packet(), indent=2, ensure_ascii=False))
        elif args.action == "prompt":
            print(prompt(store.packet(), {"issues": store.previous(), "feedback": store.feedback()}))
        elif args.action == "publish":
            with store.lock():
                issue = store.publish(json.loads(args.file.read_text()))
            print(f"Saved issue: {issue['id']}")
        elif args.action == "import":
            print(json.dumps(store.import_item(json.loads(args.file.read_text())), ensure_ascii=False))
        elif args.action == "evidence":
            print(json.dumps(store.evidence(args.url, args.title, args.published, args.youtube), ensure_ascii=False))
        elif args.action == "latest":
            history = store.history()
            print(json.dumps(history[0] if history else {}, ensure_ascii=False, indent=2))
    except KeyboardInterrupt:
        return
    except Exception as exc:
        print(f"Stopped: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
