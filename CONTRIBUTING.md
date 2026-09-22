# Contributing

Small, focused contributions are welcome. Start with an issue describing the user problem, a reproducible failure, or the connector behavior you want to improve. Use synthetic examples instead of private profiles, browser sessions or collected posts.

## Run locally

Python 3.11+ on macOS/Linux is required. The Python backend uses only the standard library; the frontend is plain HTML/CSS/JS with no build step.

```sh
python3 -m newsagent --home /tmp/newsagent-dev serve --port 8766
python3 -m unittest discover -s tests -v
node --check web/app.js
git diff --check
```

Node is only needed for the optional JavaScript syntax check, not for running the app. Tests use fake models and synthetic evidence; no API key or browser login is required. Server tests need loopback networking.

For reader changes, verify desktop and narrow-screen layouts. For builder changes, test an empty data directory, failed validation, save/reload, and configuration import. Avoid model calls just to test form behavior.

## Find the code

- `newsagent/core.py`: configuration, collection, persistence and generation workflow.
- `newsagent/sources.py`: source adapters and normalization.
- `newsagent/editorial.py`: common writing policy, schema and citation validation.
- `newsagent/models.py`: explicit provider adapters with no automatic fallback.
- `newsagent/setup.py`: prerequisite diagnostics without network or model calls.
- `newsagent/server.py` and `web/`: the loopback server, builder and reader.
- `skills/news-brief/`: the optional Codex conversation workflow.

Keep failed access distinct from an empty feed. Preserve publication dates, content provenance, limits and exact source URLs. Never silently treat metadata or search snippets as full evidence. Include relevant tests when changing these contracts.

Before opening a pull request, explain the resulting behavior and relevant validation. Do not include `.local/`, `.env`, credentials, authentication caches, personal exports or scraped private content. Keep frontend dependencies and third-party resources out of the reader. Changes should preserve old editions and existing configurations wherever possible.
