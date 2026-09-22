"""Explicit providers; never switch providers or buy credits on failure."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from .editorial import ISSUE_SCHEMA


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def validate_connection(config):
    """Validate connection settings without contacting a provider or consuming quota."""
    if config["backend"] == "codex":
        return
    base = config["base_url"].rstrip("/")
    p = urlsplit(base)
    if p.scheme not in ("https", "http") or not p.hostname or p.username or p.password or p.query or p.fragment:
        raise ValueError("Invalid model endpoint; do not include credentials, queries or fragments")
    local = p.hostname in ("localhost", "127.0.0.1", "::1")
    if (p.scheme != "https" and not local) or (config["backend"] == "ollama" and not local):
        raise ValueError("Use loopback for Ollama and HTTPS for remote providers")
    if not config["model"].strip():
        raise ValueError("Choose an installed/available model first")
    if config["backend"] == "ollama" and "cloud" in config["model"].lower():
        raise ValueError("Local mode cannot use an Ollama cloud tag")


def generate(text, config):
    validate_connection(config)
    backend = config["backend"]
    if backend == "codex":
        executable = shutil.which("codex")
        if not executable:
            raise ValueError("Codex CLI is missing. You can also write the issue in your Codex conversation.")
        env = os.environ.copy()
        for key in ("OPENAI_API_KEY", "CODEX_API_KEY"):
            env.pop(key, None)
        with tempfile.TemporaryDirectory(prefix="newsagent-model-") as temp:
            root = Path(temp)
            schema = root / "schema.json"
            result = root / "result.json"
            schema.write_text(json.dumps(ISSUE_SCHEMA))
            args = [executable, "exec", "--ignore-user-config", "--skip-git-repo-check", "--ephemeral",
                    "--sandbox", "read-only", "--cd", temp, "--color", "never",
                    "-c", 'forced_login_method="chatgpt"',
                    "-c", 'model_reasoning_effort="high"',
                    "-c", 'web_search="disabled"', "-c", "features.shell_tool=false",
                    "-c", "features.unified_exec=false", "-c", "features.apps=false",
                    "-c", "features.hooks=false", "-c", "features.multi_agent=false",
                    "--output-schema", str(schema), "--output-last-message", str(result)]
            if config.get("model"):
                args.extend(["--model", config["model"]])
            args.append("-")
            run = subprocess.run(args, input=text, text=True, capture_output=True, env=env, timeout=600)
            if run.returncode or not result.exists():
                raise ValueError("Codex generation failed. Check ChatGPT login, quota and model availability. No fallback was used.")
            return json.loads(result.read_text())
    if backend not in ("ollama", "compatible"):
        raise ValueError("Select codex, ollama, or compatible")
    base = config.get("base_url", "").rstrip("/")
    p = urlsplit(base)
    local = p.hostname in ("localhost", "127.0.0.1", "::1")
    model = config.get("model", "")
    headers = {"Content-Type": "application/json", "x-goog-api-client": "newsagentbuilder/0.1"}
    messages = [{"role": "user", "content": text}]
    if backend == "ollama":
        url = base + "/api/chat"
        body = {"model": model, "messages": messages, "stream": False, "format": ISSUE_SCHEMA}
    else:
        url = base + "/chat/completions"
        key = os.environ.get(config.get("key_env", "NEWSAGENT_API_KEY"), "")
        if not local and not key:
            raise ValueError("Set the configured API-key environment variable before starting the server")
        if key:
            headers["Authorization"] = "Bearer " + key
        body = {"model": model, "messages": messages,
                "response_format": {"type": "json_schema", "json_schema": {
                    "name": "briefing", "strict": True, "schema": ISSUE_SCHEMA}}}
    req = Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with build_opener(NoRedirect).open(req, timeout=600) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("Model response too large")
        data = json.loads(raw)
        content = data["message"]["content"] if backend == "ollama" else data["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as exc:
        raise ValueError("Model endpoint failed or returned invalid JSON. Check model/schema support and quota; no fallback used.") from exc
