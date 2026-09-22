# Your personal briefing

This first version is a local application with a plain HTML/CSS/JS interface, a Python standard-library backend, and a Codex skill. Python 3.11+ on macOS/Linux is required. There are no npm packages or Python runtime dependencies. Optional collection/model tools are separate installations.

## Open the reader

From the repository folder:

```sh
python3 -m newsagent init
python3 -m newsagent serve
```

Open `http://127.0.0.1:8765`. Keep the terminal running. A fresh installation opens the newsletter builder: enter your profile, add source URLs, choose a model, check prerequisites and save. Existing installations keep their settings. See [the builder guide](BUILDER.md) for imports, exports and separate newsletters. Choose **New briefing** to collect and generate, or use **Options & archive** to do the stages separately. On the first run, choose the seven-day catch-up if useful. Future runs default to 24 hours. Nothing runs periodically unless you arrange a schedule.

The website runs on your computer; it is not deployed publicly. Do not expose this development server through a tunnel or bind it to a public interface. Public hosting would need a different authentication/deployment design.

## Ask in Codex

You do not need the Codex app open to use the website. On macOS, double-click `Start NewsAgent.command` in the repository folder: it starts the local server and opens your browser. Keep its Terminal window running; Ctrl-C stops the server. Reopening the launcher reuses a running instance with the same private data directory. This does not install a login item or start anything automatically after a restart.

On macOS/Linux, `python3 -m newsagent serve --open-browser` provides the same behavior from a terminal. The selected provider still needs its normal setup. Choosing Codex uses the installed CLI and saved login; you do not need to conduct a conversation here for each briefing.

Open this repository and ask: **“Use $news-brief to make my briefing.”** The repository skill lives under `.agents/skills/news-brief` (linked to the portable `skills/news-brief` folder). A new conversation or skill refresh may be needed for discovery. You can also explicitly ask Codex to read `skills/news-brief/SKILL.md` in an existing conversation.

This mode uses the model in your conversation and can investigate supporting sources. Before its two model passes, the website attempts at most two recent video transcripts and four short feed items' original pages. Failed retrieval stays labeled. It does not search the wider web for missing facts. Use the Codex workflow for deeper verification.

## Connect the four platforms

| Platform | This version's route | What still needs the user |
|---|---|---|
| LinkedIn profiles | OpenCLI `linkedin posts --profile-url …` | Connected browser extension and signed-in session |
| LinkedIn companies | `mcporter call linkedin.get_company_posts` | Configured LinkedIn MCP and signed-in session; returns undated page text |
| LinkedIn school pages (including YC) | Saved in source list | Current connector does not support these pages; explicitly import accessible posts |
| X | OpenCLI `twitter tweets …` | Connected browser extension and signed-in session |
| Instagram | OpenCLI `instagram user …` | Connected browser extension and signed-in session |
| YouTube | yt-dlp channel metadata; selected transcripts through the evidence command | Installed yt-dlp; transcript availability is best-effort |

OpenCLI is an external dependency, not bundled or automatically installed. Run `opencli doctor` to check its browser bridge. Follow [OpenCLI's setup instructions](https://github.com/jackwener/opencli) to connect the extension, then sign in to the platforms yourself. The application never logs you in, exports cookies, posts, likes or follows.

These are experimental third-party collection routes. Platform restrictions and account conditions still apply; a disclaimer does not change them. LinkedIn restricts scraping/automation. If you do not want to use a browser connector, disable it and explicitly import material you can access. Connection failure is reported, never treated as “no news.” No complete following-list import is implemented.

Instagram's adapter may return captions without a post permalink, in which case the issue links to the profile and labels that limitation. Images/Reels are not visually inspected. YouTube collection does not imply a video was watched. Only a successfully fetched transcript becomes transcript evidence.

## Choose the model

- **Codex:** the website uses your installed CLI and ChatGPT login, with high reasoning effort and no API-key fallback. Leave the model field empty for the CLI default or choose an available model. Two passes consume your normal allowance; one additional repair pass is allowed if output validation fails. It ignores personal CLI config, disables shell/browser tools and runs in an isolated temporary working directory with a read-only sandbox. It never exports your authentication.
- **Ollama:** enter `http://127.0.0.1:11434` and an installed model tag. Disable Ollama cloud features for strict local operation. No models are downloaded by this app.
- **Compatible endpoint:** an advanced option for a provider such as Gemini or a separately operated local proxy. Enter a base URL ending in `/v1` or the provider's documented equivalent, model name and an environment-variable name. Set the key in your own terminal before starting the app. JSON-schema support is required. Keys are not saved in settings. For Gemini the documented base is `https://generativelanguage.googleapis.com/v1beta/openai`.

This project does not supply free GPT/Claude API access or bundle subscription proxies. A user-operated proxy can be connected where compatible, but provider terms, quotas, credentials and breakage remain separate concerns. No multi-account rotation, quota circumvention or paid fallback is implemented. A free API allowance is conditional; it is not a promise of free inference everywhere.

Sources: [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode), [Codex configuration](https://learn.chatgpt.com/docs/config-file/config-sample), [Gemini compatibility](https://ai.google.dev/gemini-api/docs/openai), [Ollama](https://docs.ollama.com/).

## Short summaries, optional depth

The reader shows what changed, why it matters and a practical takeaway. Expand **Evidence & context** for caveats, durable lessons, supporting excerpts and feedback. Future editions prefer three stories (maximum five) and enforce short field limits. Fifteen minutes is a ceiling. The reader uses one continuous column. Options and the archive are under **Options & archive**; source management and connection help live under **Sources**. Missing-source counts stay visible beside the edition. Old editions retain their original sources and dates when you change the list.

## Evidence and privacy

The app stores your settings, evidence packets, issues and feedback in `.local/`, excluded from Git. Keep this folder private. Use `python3 -m newsagent --home /your/private/folder …` to move storage outside the checkout. Deleting that folder removes local history; source-provider/model-provider retention is separate. The app has no telemetry, trackers, remote fonts or external frontend scripts.

An issue keeps its evidence and coverage snapshot, so a later collection cannot rewrite old citations. Code checks the output structure, source IDs, exact quoted excerpts, main-story date/content requirements and reading budget. Model review checks interpretation, but does not certify factual correctness. Review consequential claims yourself and use **Question the evidence** feedback when needed.

For additional evidence:

```sh
python3 -m newsagent evidence 'https://example.org/article' --title 'Article title'
python3 -m newsagent evidence 'https://www.youtube.com/watch?v=VIDEO_ID' --title 'Video title' --youtube
```

Only supply `--published YYYY-MM-DD` when verified from the source. Imports use a JSON object with `title`, `url`, `text`, `published_at`, `platform`, and `access` (all strings). Leave an unknown date empty. Run `python3 -m newsagent import /path/to/evidence.json`. Imports join the current packet; generating uses them, while a new collection starts a fresh packet.

## What is deliberately bounded

Collection takes recent samples rather than reading an entire platform. It keeps at most eight items per source and forty overall (sixty with explicit imports). Known old items are excluded from the selected lookback; undated items remain marked as undated. The writer compares recent editions to reduce repetition, but semantic deduplication is model-dependent. Feedback is supplied to later runs rather than silently changing preferences.

The default starter is blank. The optional `config/examples/engineering-creators.json` follows Nick Saraev, Alex Hormozi and Nate Herk on YouTube, with additional social channels disabled until you connect them. See [source links and limitations](SOURCES.md). These are discovery sources, not independent validation of commercial claims or hiring trends. Swiss career coverage remains incomplete.

## Check the implementation

```sh
python3 -m unittest discover -s tests -v
```

Tests use synthetic evidence and fake provider responses. Live connector/model results are documented separately in `docs/VALIDATION.md`. The original research remains available in `RESEARCH.md` and its linked references.
