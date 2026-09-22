# Finder launcher — 22 September 2026

The executable `Start NewsAgent.command` starts the local reader and opens the default browser without a Codex conversation. `serve --open-browser` supports the same flow on macOS/Linux. It reuses a listener only when the app and private directory identity match, including while that instance is generating an edition; an unrelated occupied port remains an error. This is a foreground Terminal launcher, not a background service or login item.

The shell syntax and 32 backend tests pass, including identity isolation and reuse with the browser call mocked. Native Finder interaction could not be tested because computer-use permissions were unavailable. No login settings, model configuration or saved editions were changed.

---

# Briefing exports and graph research — 22 September 2026

Each saved edition can now be downloaded as Markdown from About this edition, or exported with `export-briefing` from the CLI. Exports include the written stories, caveats, citation excerpts and links, low-priority items, and coverage limitations. They read the immutable saved edition rather than the current collection. Existing JSON snapshots and SQLite history remain unchanged.

All 30 tests pass, including original-evidence preservation, missing edition handling, overwrite rejection, escaped export markup, coverage retention, downloads, and retrieval beyond the reader's 30-edition list. The CLI export passed with a synthetic edition, and an actual saved edition downloaded successfully through the browser. JavaScript syntax and diff whitespace checks pass. No model calls were needed for validation.

The README and builder guide now distinguish configuration exports, readable edition exports, and full private-directory backups. Graphify was researched from its repository, package metadata and benchmark document; it was not installed or integrated. See [GRAPHIFY.md](GRAPHIFY.md) for the recommendation and proposed evaluation.

---

# Newsletter builder — 22 September 2026

New installations start with a blank profile and sources. A three-step browser flow collects interests, source URLs and model settings, then saves a reusable configuration. Existing private settings and editions are preserved. The engineering creator list is an optional example with social channels disabled by default.

All 25 backend tests pass locally, covering configuration preservation, export/import round trips, overwrite rejection, malformed settings, provider validation, diagnostics without generation, credential exclusion, download responses, source collection and editorial checks. The CLI init/doctor/export/import path also passed in disposable folders. JavaScript syntax and diff whitespace checks pass. A GitHub Actions workflow runs the suite on Python 3.11 and 3.13 without model credentials.

Browser checks used disposable local stores: a non-technical profile completed the builder and survived reload; configuration download succeeded; importing the public example opened a review before saving and retained nine disabled social sources; invalid remote Ollama endpoints were rejected without losing form values. The provider step was inspected at 390px with no horizontal overflow. No live model generation or new social authentication was used for these checks.

Prerequisite checks inspect local software and API-key presence only. They do not certify logins, allowance, model quality or source availability. The website still collects bounded samples from configured sources and does not automatically discover omitted stories across the wider web. This version adds onboarding and portability, not broader collection coverage.

---

# Reading-first cleanup — 22 September 2026

The reader now has one continuous column, plain source lists and a single primary action. Cards, decorative badges, slogans, the hero and the sidebar have been removed. Evidence, archive, connection help and model settings remain available through labeled controls. Research and the reasoning behind the removals are in [DESIGN.md](DESIGN.md).

Browser checks used a disposable local store and mocked collection/model responses: a rejected settings save preserved the entered value; a corrected save survived reload; generation showed progress, disabled repeated submissions and displayed the completed issue; collecting while reading an archived issue preserved the edition and its expanded evidence. Native archive selection worked. The phone layout was checked at 390px with no horizontal overflow. These checks did not consume model allowance or change the user's stored newsletter.

All 16 existing backend tests, JavaScript syntax and diff whitespace checks pass. The frontend now uses non-overlapping polling, request timeouts, ordinary navigation links and one run-error location. Changing sources no longer reloads unsaved settings fields.

The user's latest saved collection has three checked sources and nine unavailable sources. This change makes that limitation visible; it does not repair social authentication or generate a replacement edition. Existing private history and source selections are preserved.

---

# Redesign validation — 22 September 2026

Sixteen tests pass, including new limits on individual story fields, acceptance of LinkedIn organisation URLs, correct company-post routing, rejection of profile-only responses, undated company-page evidence, and explicit rejection of unsupported school-page retrieval. Company responses were tested with fixtures, not live authenticated content.

The public starter and private source settings now contain 12 channels grouped under Nick Saraev, Alex Hormozi, Nate Herk, Y Combinator and a16z. Account links were checked against public search/profile results and creator websites; that does not verify collection access. Nate's Instagram and X links follow the links on his own website. Start Tech was omitted because its identity remained unclear.

The social browser bridge is still disconnected. A read-only a16z MCP attempt reported incomplete browser setup; no posts were returned. YC's LinkedIn page uses `/school/`, which the installed MCP explicitly does not support. Its URL is preserved, with an unavailable connector label, rather than rewritten to a different route.

The saved September 21 edition was shortened to three stories: a two-minute visible summary and four minutes including supporting material. Its original dates, evidence and coverage remain attached; the original edition remains in the archive. It is not a new collection from the revised sources. Private editions are excluded from Git.

The redesigned reader was checked in the browser: source preferences saved and were restored, and evidence expands without leaving the story. Desktop and phone layouts were inspected. Python compilation and JavaScript syntax checks pass. No frontend dependencies, external assets or trackers were added.

---

# Validation — 21 September 2026

This records what was actually exercised in the first implementation. It is not a guarantee of future connector access or editorial accuracy.

**Automated checks**

Fourteen standard-library tests pass. They cover invented citations/quotes, unknown-date and metadata-only evidence, immutable issue evidence snapshots, rejection after a failed review and bounded repair, repeated event keys, the reading budget, old/future dates, collection failures, bounded enrichment and transcript failures, concurrent-run locking, stale input, feedback, source URL restrictions, social response parsing, feed parsing, HTTP host/CSRF checks, private-file isolation, and a complete website-triggered generation with mocked model responses. Python compilation, JavaScript syntax and skill validation also pass.

**Live checks**

- Codex CLI reported an existing ChatGPT login. A real `gpt-6-astra` run with high reasoning effort completed both writing and review, passed citation/output validation, and saved a ten-minute issue. No API key or subscription proxy was used.
- The first issue used the collected public evidence plus three explicitly retrieved supporting documents. It is a first catch-up, not a claim of complete four-platform coverage. It remains private and is not included in this repository.
- yt-dlp retrieved metadata for both starter YouTube channels. Channel-feed dates allowed old videos to be excluded from the seven-day window. Caption retrieval was also tested successfully for one collected video; that later transcript was not used in the already-published first issue.
- RSS collection succeeded for Simon Willison, OpenAI and GitHub. The Pragmatic Engineer and web.dev feeds were separately checked and added for future runs. web.dev returned older entries, so successful fetching must not be presented as fresh news.
- `opencli doctor` found a running daemon but no connected browser extension. LinkedIn, Instagram and X therefore remained explicitly unavailable. Their command interfaces and normalization paths were checked, but authenticated live collection is not verified.
- The reader displayed the real saved issue and personal preferences. Adding a source through the website persisted correctly. Desktop and phone-width layouts were visually inspected.
- Private configuration, history and issues are excluded from Git. Public source templates contain no personal account credentials or collected private material.

**Remaining limits**

Ollama and compatible endpoints have implemented adapters but were not tested against a live model server. Their exact model/schema support must be checked before relying on them. The automatic enrichment step attempts bounded page/transcript retrieval; it is not general web research. The transcript extractor and direct fetcher were exercised, while the first real GPT issue was generated before automatic enrichment was added.

There is no public deployment, recurring schedule, email delivery, visual understanding of videos/Reels, or automatic following-list import. At that version, LinkedIn collection supported personal profiles only; see the September 22 update for the company adapter and remaining school-page limitation. Social access depends on the user's browser and external tools; platform restrictions still apply.

The review pass uses the same model as drafting. Exact quotation checks cannot establish that a claim follows from the quoted passage. No human-labeled relevance/recall benchmark has been completed. Novelty grouping, wrapper-value judgments and career implications still need user feedback and spot checks. This is a usable personal first version, not a proven misinformation filter.
