---
name: news-brief
description: Create or update the user's personal daily news briefing in NewsAgentBuilder, focused on their work, durable skills and evidence. Use when asked to make their newsletter, briefing or news catch-up in this project.
---

Run from this repository. The application is `python3 -m newsagent`; read `docs/USAGE.md` for setup or connection failures. Private data lives in ignored `.local/` unless `--home` overrides it. Never commit profiles, collected content, issues or credentials.

For a briefing in this conversation, use the current model; do not launch another model process just to write it:

1. Run `python3 -m newsagent init` if needed. Read the private config. Preserve the user's sources/preferences; propose starter sources only if none exist.
2. Run `python3 -m newsagent collect --days 1` (up to 7 for an explicitly requested catch-up). Inspect `.local/packet.json`. Report inaccessible platforms. Do not present web-search results as having read a signed-in social feed.
3. Read `newsagent/editorial.py` for the output schema and editorial policy. Read recent issues/feedback through `Store.previous()` and `Store.feedback()` when checking novelty.
4. Use Agent Reach, if available, to retrieve primary evidence for the few likely important stories. When unavailable, use an available web tool. Obtain actual source content rather than relying on search snippets. Add selected pages with `python3 -m newsagent evidence URL --title TITLE --published VERIFIED_DATE`; omit the date when unknown. For a YouTube video add `--youtube`; if transcription fails, retain metadata-only status. Imports use the documented JSON contract.
5. Write `.local/draft.json` matching `ISSUE_SCHEMA`. Source IDs refer to this packet. Include exact short supporting excerpts, distinguish source claims from conclusions, group reposts, and assess genuine value beyond a base-model wrapper. A 15-minute budget is a maximum. Do not fill quiet days. Use older research only as clearly dated background. Career forecasts must retain methodology, geography and uncertainty.
6. Review the draft against the actual evidence before publishing: names, numbers, availability, central claims, career implications and whether each quote really supports the claim. A matching quote alone is not a fact check. Omit/downgrade unsupported stories. Run `python3 -m newsagent publish .local/draft.json`; fix validation failures rather than bypassing them.
7. Show the key conclusions in the conversation and point to the local reader (`python3 -m newsagent serve`). Mention material coverage gaps. No email, social posts, public publishing or recurring schedule is implied by making one issue.

For website-triggered runs, the application owns the model process and review pass. It currently supports Codex, Ollama and a user-configured compatible endpoint. Do not export browser cookies, install a proxy, switch provider, or consume paid fallback credits automatically. Browser connectors use only the existing user-controlled session.
