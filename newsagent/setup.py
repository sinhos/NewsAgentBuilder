"""Local prerequisite checks. No network requests, auth-file reads or model calls."""
import os
import shutil
import sys
from urllib.parse import urlsplit


def check_setup(config):
    checks = []

    def add(name, status, detail):
        checks.append({"name": name, "status": status, "detail": detail})

    add("Python", "found" if sys.version_info >= (3, 11) else "missing", "Python 3.11 or newer is required.")
    profile = config["profile"]
    complete = bool(profile["description"].strip() and profile["interests"].strip())
    add("Your profile", "found" if complete else "missing", "Describe your work or goals and what you want to follow.")
    provider = config["provider"]
    if provider["backend"] == "codex":
        add("Codex CLI", "found" if shutil.which("codex") else "missing",
            "Run codex login with your own ChatGPT account. Login, model access and allowance are not checked here.")
    elif provider["backend"] == "ollama":
        add("Ollama", "manual", "Start Ollama and install the selected local model. Server availability and model quality are not checked here.")
    else:
        local = urlsplit(provider["base_url"]).hostname in ("localhost", "127.0.0.1", "::1")
        present = bool(os.environ.get(provider["key_env"]))
        add("API key", "found" if present or local else "missing",
            "Local endpoint: a key may be optional." if local else f"Set {provider['key_env']} before starting the server. Only its presence is checked; its value is never returned.")
        add("Endpoint", "manual", "Confirm model access, JSON-schema support and pricing with your provider. No test generation is made.")
    enabled = [s for s in config["sources"] if s["enabled"]]
    add("Sources", "found" if enabled else "missing", f"{len(enabled)} enabled. Actual access is checked when you collect.")
    platforms = {s["platform"] for s in enabled}
    if "youtube" in platforms:
        add("YouTube", "found" if shutil.which("yt-dlp") else "missing", "Install yt-dlp for channel collection. Captions may be unavailable.")
    browser = any(s["platform"] in ("x", "instagram") or
                  s["platform"] == "linkedin" and urlsplit(s["url"]).path.startswith("/in/") for s in enabled)
    if browser:
        add("Social browser connector", "found" if shutil.which("opencli") else "missing",
            "OpenCLI needs its connected extension and your signed-in browser. Run opencli doctor to check the connection.")
    if any(s["platform"] == "linkedin" and urlsplit(s["url"]).path.startswith("/company/") for s in enabled):
        add("LinkedIn companies", "found" if shutil.which("mcporter") else "missing",
            "Configure the LinkedIn MCP connection separately. Finding mcporter does not confirm that connection.")
    if any(s["platform"] == "linkedin" and urlsplit(s["url"]).path.startswith("/school/") for s in enabled):
        add("LinkedIn school pages", "unsupported", "The current connector cannot collect these pages. Disable them or import accessible posts manually.")
    if platforms & {"rss", "web"}:
        add("Public feeds and pages", "manual", "No extra collector installation. Sites can still block access; web-page dates may be unknown.")
    return checks
