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

There is no public deployment, recurring schedule, email delivery, visual understanding of videos/Reels, or automatic following-list import. LinkedIn collection currently supports personal profiles, not company pages. Social access depends on the user's browser and external tools; platform restrictions still apply.

The review pass uses the same model as drafting. Exact quotation checks cannot establish that a claim follows from the quoted passage. No human-labeled relevance/recall benchmark has been completed. Novelty grouping, wrapper-value judgments and career implications still need user feedback and spot checks. This is a usable personal first version, not a proven misinformation filter.
