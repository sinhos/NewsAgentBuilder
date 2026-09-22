# Build once, adjust as you learn

A newsletter configuration is a portable JSON file with three parts: **profile**, **sources**, and **provider**. The builder edits that configuration; the shared collection, writing, review and citation workflow runs it. It does not generate or execute custom code for each user.

## First newsletter

Run `python3 -m newsagent serve` from the cloned repository and open the printed address. On a new installation, the builder opens automatically. For an existing installation, use **Settings → Open the newsletter builder**.

Describe your actual goals and topics. Include geography when local relevance matters. Choose a language and a 3–20 minute maximum. The writer follows this profile rather than assuming a technical career.

Paste one source URL per line. Social account links are recognized automatically; other new URLs are treated as RSS / Atom feeds. Use **Sources → Add a source → Web page** for ordinary pages. Start with a small list. Source names can be adjusted in an exported configuration; the Sources screen lets you add, disable or remove individual channels.

Choose your model and use **Check prerequisites**. This checks installed tools, profile completeness and API-key presence where applicable. It makes no network or model calls. “Found” does not mean logged in, enough quota, or successful retrieval. Resolve missing prerequisites using [USAGE.md](USAGE.md), then save. Saving alone does not collect or generate anything.

In **Briefing**, choose **Options & archive → Collect only** if you want to inspect coverage before using model allowance. Then select **Write from collection**. **New briefing** runs both stages. An empty collection needs a connected source or a manual import before generation.

## Share a configuration

Use **Settings → Reuse or share your newsletter setup → Download configuration**. This downloads saved settings, so save any edits first. The file contains personal interests, exclusions and source URLs; review these before sharing. Never put secrets in profile fields or endpoint URLs.

On another installation, select **Import a configuration**. Valid files open in the builder for review and only replace settings after **Save my newsletter**. History is preserved. Existing disabled sources are retained when reviewing a configuration in the builder; manage them in Sources.

For a new installation you can also use:

```sh
python3 -m newsagent init --config /path/to/newsletter-config.json
python3 -m newsagent serve
```

`init` never replaces existing settings. To try the optional engineering example on a fresh installation:

```sh
python3 -m newsagent init --config config/examples/engineering-creators.json
python3 -m newsagent serve
```

The example enables three YouTube channels. Social channels remain opt-in and require separate setup. Creator content is a discovery signal, not independent proof of a commercial claim.

Export from the terminal with:

```sh
python3 -m newsagent export /tmp/my-newsletter.json
```

Export refuses to overwrite an existing file. It excludes issue history, evidence, environment-variable values and authentication files.

## Save editions and back up your archive

Every successfully published briefing is saved automatically in the private data directory: the archive database is `history.sqlite3` and complete edition snapshots are in `issues/`. By default these are under `.local/`. Each edition keeps its own evidence and coverage, so later collections do not rewrite its citations.

The browser shows the latest 30 editions in **Options & archive → Read an edition**. Older saved editions remain in storage. Open any displayed edition, expand **About this edition**, and select **Save this briefing (.md)** to download a readable copy. The browser uses its usual download location or prompts for a destination, depending on browser settings.

For a chosen folder, use the terminal:

```sh
python3 -m newsagent export-briefing /path/to/briefing.md
python3 -m newsagent export-briefing /path/to/older-briefing.md --issue EDITION_ID
```

The first command exports the latest edition. For an older edition, replace `EDITION_ID` with the ID in its saved JSON filename. This also works for editions outside the browser's 30-edition list. Export refuses to overwrite an existing file.

Markdown exports contain the complete written edition, citations and collection limitations. They exclude raw collected articles, your configuration and account credentials, but can contain personalized explanations. Review them before sharing. They can be saved in a folder you back up or opened in a Markdown editor; this app does not sync to cloud services.

To back up everything, stop the server and any collection/generation first, then copy the entire private data directory to your backup location. A configuration export alone does not back up editions, and a Markdown export alone does not preserve the full underlying evidence snapshot.

## Keep separate newsletters

Use a different private directory for each configuration and pass the same `--home` on every command for that newsletter:

```sh
python3 -m newsagent --home "$HOME/.newsagent/research" init
python3 -m newsagent --home "$HOME/.newsagent/research" serve --port 8767
```

Those directories hold separate settings and histories. The default `.local/` is excluded from this repository's Git tracking; custom directories are your responsibility to keep private.

## Diagnose and update

```sh
python3 -m newsagent doctor
```

This prints the same prerequisite checks as the builder. To verify real source access, collect and inspect **Sources → Connection status & help**. Provider authentication and model quality require separate verification; the first generation uses your chosen provider's allowance.

To update, stop the server with Ctrl-C, run `git pull --ff-only` from an unchanged checkout, and start `python3 -m newsagent serve` again. Existing `.local/` settings and history are preserved. If you changed tracked files, resolve those changes before pulling. Keep private backups of your data directory if the history matters to you.

There is no recurring scheduler, automatic following-list import or public multi-user service in this version.
