# NewsAgentBuilder

Build a personal news briefing around your work, interests and trusted sources. Read what matters, understand the evidence, and get back to your day.

Every important story explains **what changed**, **why it matters to you**, and **what evidence supports it**. Promotions and weak claims are downgraded; quiet days stay short. Your reading budget is a ceiling, not a target.

This is an open-source local application. You own the configuration and history, choose the model, and run it from a browser or Codex. There is no hosted service or project subscription.

## Install and run on your computer

You need **Git and Python 3.11+ on macOS or Linux**. Windows users can try WSL; native Windows is not supported. No Python packages, frontend packages or build step are required for the app itself.

**1. Download the project.** Open a terminal on your computer and run:

```sh
git clone https://github.com/sinhos/NewsAgentBuilder.git
cd NewsAgentBuilder
```

**2. Start the app.** From that project folder, run:

```sh
python3 -m newsagent serve
```

**3. Open the address printed in your terminal.** Once the app has started, copy `http://127.0.0.1:8765` into your browser. Keep the terminal running while you use it.

This address points to **your own computer**. It only works after step 2; it is not a public website or a demo hosted by GitHub. If the browser cannot connect, check the terminal for a startup error.

The first visit opens a three-step builder:

1. Describe your work, interests, exclusions, language and reading budget.
2. Paste your source URLs, one per line.
3. Choose a model, check prerequisites, and save your newsletter.

Once the chosen model and collectors are connected, select **New briefing**. Use **Options & archive → Past 7 days** for an initial catch-up. Runs are manual; the app does not schedule or email editions.

To use it again later, open a terminal in the downloaded `NewsAgentBuilder` folder and repeat step 2. Your saved settings and editions remain on your computer.

## Bring your model

| Connection | What you need | Where inference happens |
|---|---|---|
| Codex | Installed Codex CLI, your ChatGPT login and available allowance | OpenAI |
| Ollama | Running Ollama and an installed local model | Your computer |
| Compatible API | Endpoint, model and your own key where required | Your chosen provider |

For Codex, follow the [official CLI installation guide](https://learn.chatgpt.com/docs/codex/cli), then run `codex login` with ChatGPT. Subscription limits apply; there is no separate API-key fallback. For other providers, see [model setup](docs/USAGE.md#choose-the-model). Model quality and hardware requirements vary.

## Bring your sources

RSS / Atom feeds need no extra collector. YouTube needs **yt-dlp**. Instagram, X and LinkedIn profiles need **OpenCLI**, its browser extension and your signed-in session. LinkedIn company pages need a separate MCP connection. These experimental social connectors can fail; missing coverage is shown explicitly. See [connection instructions](docs/USAGE.md#connect-the-four-platforms).

Start with a few sources you trust. The [optional engineering example](config/examples/engineering-creators.json) includes Nick Saraev, Alex Hormozi and Nate Herk; additional social sources are disabled until you connect them. New users start with an empty source list.

## Save your briefings

Every generated edition is saved automatically on your computer. Reopen recent editions through **Options & archive → Read an edition**. Settings, history and evidence stay in the private `.local/` folder; individual editions are also stored as JSON in `.local/issues/`.

To keep a readable copy elsewhere, open an edition, expand **About this edition**, and choose **Save this briefing (.md)**. The Markdown file includes the summary, caveats, evidence links and coverage gaps. Save it in your own folder or open it in a Markdown notes app. No cloud account is required and nothing is uploaded automatically.

From the project folder, export the latest edition with:

```sh
python3 -m newsagent export-briefing /path/to/your/briefing.md
```

Replace the example path with your chosen location. See [saving and backups](docs/BUILDER.md#save-editions-and-back-up-your-archive). We also assessed [Graphify for archive retrieval](docs/GRAPHIFY.md); it is not a required dependency or an implemented integration.

## Reuse your newsletter setup

In **Settings → Reuse or share your newsletter setup**, download a configuration or import one into the builder for review. Exports contain your profile and source URLs, but no history, collected content or login credentials. Review personal details before sharing.

You can also ask Codex: **“Use $news-brief to make my briefing.”** Open this repository in Codex first. See [builder and configuration guide](docs/BUILDER.md) for CLI examples, separate newsletters and updates.

## What to expect

The app collects bounded samples, writes an edition, reviews it in a second model pass, and checks citation excerpts in code. It does **not** monitor the whole internet, automatically discover every important launch, verify every claim independently, or visually watch videos. The website does not search beyond configured sources; the Codex workflow can investigate further.

Private data stays in ignored `.local/`. A remote model receives your profile and evidence. The reader has no trackers or external scripts. This single-user loopback server is not suitable for public hosting.

[Usage and troubleshooting](docs/USAGE.md) · [Validation and limitations](docs/VALIDATION.md) · [Contributing](CONTRIBUTING.md) · [Design](docs/DESIGN.md)

MIT licensed: see [LICENSE](LICENSE). External models, source content and services have their own licenses and terms. Earlier design research is available in [docs/RESEARCH.md](docs/RESEARCH.md).
