"""Single-user, loopback-only UI. Not a public hosting server."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import secrets
import threading
from urllib.parse import urlsplit

from .core import ROOT
from .setup import check_setup


def make_server(store, port=8765):
    token = secrets.token_urlsafe(32)
    job = {"running": False, "stage": "Ready", "error": ""}
    guard = threading.Lock()

    def progress(stage):
        with guard:
            job["stage"] = stage

    def launch(action, days):
        if action not in ("collect", "generate", "run") or type(days) is not int or not 1 <= days <= 14:
            raise ValueError("Invalid run request")
        with guard:
            if job["running"]:
                raise ValueError("A run is already in progress")
            job.update(running=True, stage="Starting", error="")

        def run():
            try:
                if action in ("collect", "run"):
                    store.collect(days, progress)
                if action in ("generate", "run"):
                    store.generate(progress)
                progress("Finished")
            except Exception as exc:
                with guard:
                    job["error"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__ + "; see local setup instructions"
                    job["stage"] = "Run stopped; your previous issue is unchanged"
            finally:
                with guard:
                    job["running"] = False
        threading.Thread(target=run, daemon=True).start()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def host_ok(self):
            return self.headers.get("Host") in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

        def reply(self, code, body, typ="application/json; charset=utf-8", headers=None):
            data = json.dumps(body, ensure_ascii=False).encode() if isinstance(body, (dict, list)) else body.encode()
            self.send_response(code)
            self.send_header("Content-Type", typ)
            self.send_header("Content-Length", str(len(data)))
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if not self.host_ok():
                return self.reply(403, {"error": "Local access only"})
            path = urlsplit(self.path).path
            if path in ("/", "/app.js", "/style.css"):
                name = "index.html" if path == "/" else path[1:]
                typ = {"index.html": "text/html", "app.js": "text/javascript", "style.css": "text/css"}[name]
                return self.reply(200, (ROOT / "web" / name).read_text().replace("__SESSION_TOKEN__", token), typ + "; charset=utf-8")
            if path == "/api/export":
                return self.reply(200, store.config(), headers={"Content-Disposition": 'attachment; filename="newsletter-config.json"'})
            if path == "/api/state":
                history = store.history()
                try:
                    packet = store.packet()
                    collection = {"collected_at": packet["collected_at"], "items": len(packet["items"]), "coverage": packet["coverage"]}
                except ValueError:
                    collection = None
                with guard:
                    status = dict(job)
                if not status["running"] and store.is_running():
                    status = {"running": True, "stage": "A run is active in Codex or another terminal", "error": ""}
                return self.reply(200, {"config": store.config(), "issues": history, "collection": collection, "job": status})
            self.reply(404, {"error": "Not found"})

        def do_POST(self):
            if not self.host_ok() or self.headers.get("X-Newsagent-Token") != token:
                return self.reply(403, {"error": "Reload the local page to reconnect"})
            origin = self.headers.get("Origin")
            if origin and origin not in {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}:
                return self.reply(403, {"error": "Cross-origin request rejected"})
            if self.headers.get("Content-Type") != "application/json":
                return self.reply(415, {"error": "Use JSON"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size <= 0 or size > 100000:
                    raise ValueError("Request size is invalid")
                body = json.loads(self.rfile.read(size))
                if not isinstance(body, dict):
                    raise ValueError("Expected a JSON object")
                if self.path == "/api/config":
                    with guard:
                        if job["running"]:
                            raise ValueError("Wait for the current run before changing settings")
                    store.save_config(body)
                elif self.path == "/api/check":
                    from .core import validate_config
                    return self.reply(200, {"checks": check_setup(validate_config(body))})
                elif self.path == "/api/run":
                    launch(body.get("action", "run"), body.get("days", 1))
                elif self.path == "/api/import":
                    store.import_item(body)
                elif self.path == "/api/feedback":
                    store.add_feedback(body.get("issue_id"), body.get("event_key"), body.get("verdict"))
                else:
                    return self.reply(404, {"error": "Not found"})
                self.reply(200, {"ok": True})
            except (ValueError, TypeError, KeyError) as exc:
                self.reply(400, {"error": str(exc)})
            except Exception:
                self.reply(500, {"error": "Operation failed; no provider fallback was used"})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
