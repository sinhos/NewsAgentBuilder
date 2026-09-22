# NewsAgentBuilder

Personal news briefings for people who want to understand what matters without scrolling all day. Every important story explains **what changed, why it matters to you, and what evidence supports it**.

This is an early, working local version: a Codex skill, a private reading website, configurable sources, model-based writing and review, citation checks, history, and feedback. It targets a maximum 15-minute read. It does not guarantee complete coverage or error-free interpretation.

**Start here** — Python 3.11+ on macOS/Linux, no runtime packages:

```sh
python3 -m newsagent init
python3 -m newsagent serve
```

Open **http://127.0.0.1:8765**. Review the starter sources and choose **Generate briefing**. Keep the server running while using it. Nothing runs on a recurring schedule by default.

In Codex, open this repository and ask **“Use $news-brief to make my briefing.”** The skill can also investigate original evidence before writing. If skill discovery has not refreshed, ask Codex to read `skills/news-brief/SKILL.md` directly.

**Source access:** YouTube uses installed yt-dlp; LinkedIn profiles, Instagram accounts and X accounts use installed OpenCLI with a connected, signed-in browser. These are experimental connectors, not guaranteed platform access. Failures are visible. Public RSS feeds provide additional evidence; you can also import content yourself.

**Model choice:** use your existing ChatGPT login through Codex, a local Ollama model, or an explicitly configured compatible endpoint. Subscription limits still apply. The app provides no unlimited free API and never switches to a paid fallback.

Settings and generated material stay in the ignored `.local/` folder. The website has no trackers, external scripts, or frontend dependencies. Do not expose the local server publicly.

Read the [setup and usage guide](docs/USAGE.md) and [validation results and limitations](docs/VALIDATION.md).

```sh
python3 -m unittest discover -s tests -v
```

Code is available under the [MIT license](LICENSE). Model licenses, source-content rights and external service terms are separate.

Optional deeper reading:

- [Short research guide](docs/RESEARCH.md)
- [Full analysis and implementation roadmap](docs/RESEARCH-DETAILED.md)
- [Ollama, local models, and hardware](docs/OLLAMA.md)
- [ChatGPT subscriptions and third-party tools](docs/SUBSCRIPTION-BACKENDS.md)

The research documents are dated design references. Use the usage guide for what the implementation currently does.
