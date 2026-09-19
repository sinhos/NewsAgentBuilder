# NewsAgentBuilder: the simple plan

A shorter version of the research completed on 18 September 2026. This describes what we recommend building; the application is not implemented yet.

**The idea**

A free, open-source tool that creates a personal news briefing from sources the user chooses. It explains the few developments that matter to their work and keeps everything else brief.

For example, two people can follow the same channels but receive different briefings: a web developer needs different information from an AI researcher.

The idea is feasible. The hardest parts are getting reliable access to sources and checking claims. Writing the summaries is only one step.

**What the user would do**

1. Describe their work, interests, tools, and available reading time.
2. Add sources, or choose a small starter list.
3. Choose how to run the model: on their computer or through a supported existing subscription.
4. Preview a briefing and adjust what counts as useful.
5. Schedule future runs on their computer.

The “builder agent” guides this setup and saves the user's preferences. Everyone uses the same underlying software, configured differently. It does not need to generate a new program for each person.

**What the newsletter should contain**

- **Important:** a few explanations of what changed, why it matters to this person, and what they could do next.
- **Worth watching:** short titles for promising but uncertain developments.
- **Low priority:** optional titles marked as repeated, promotional, weakly supported, or irrelevant to this profile.
- **Coverage:** a brief note about sources that could not be checked.

Every important explanation should link to supporting evidence and distinguish confirmed information from a creator's claim. Several people repeating the same announcement should count as one story.

Do not force content into every edition. “Nothing important changed in the sources checked” is a useful result.

**How it can run without API charges**

| Option | Plain-English explanation | Main trade-off |
|---|---|---|
| Ollama | Runs a downloaded model on the user's computer | No provider inference bill, but needs suitable hardware and time |
| Existing ChatGPT/Codex access | Uses the user's supported subscription through a local client | Can avoid an additional API bill, but consumes subscription limits |
| Free cloud allowance | Uses a provider's limited free service | Availability and limits can change |

Start with **Ollama**, then add the subscription option. Let users choose; there is no need to make everyone use the same hardware.

Ollama is the software that runs a model. The model does the reasoning. A smaller model is a sensible first experiment on an ordinary laptop, but quality and speed need testing on real articles. The detailed report contains model and memory comparisons.

Third-party subscription tools do exist. However, official Codex integration is the first route worth testing before adding a proxy. A proxy is a translator between applications; it does not create extra usage allowance or turn a subscription into unlimited API access. See the [subscription report](SUBSCRIPTION-BACKENDS.md) for the specific tools reviewed.

**Which sources to support first**

Start with blogs and news feeds, official announcements, and GitHub releases. Add selected YouTube channels next, where usable transcripts are available.

Keep Reddit, X, Instagram, and LinkedIn optional for later. Access rules, charges, missing permissions, and changing interfaces make them harder to support reliably. Importing someone's followed accounts and reading those accounts' content are also separate problems.

Agent Reach can help connect to sources. It does not supply the model, decide what is true, or guarantee access to every platform.

**What is worth reusing**

Study [Tech News Digest](https://github.com/draco-agent/tech-news-digest) for its newsletter workflow and [Holo RSS Reader](https://github.com/helebest/holo-rss-reader) for feed collection. Keep Agent Reach available for optional connectors. Inspect and test selected components before installing a large collection of skills.

**What to build first**

1. Make a briefing for yourself from 10–20 sources, using an explicit work profile.
2. Check it daily: did it save time, make unsupported claims, repeat stories, or miss something important?
3. Build a small Python application that collects updates, remembers previous stories, and saves a local HTML or Markdown briefing.
4. Once the brief is consistently useful, add the guided setup that makes it a builder for other people.
5. Add more sources and optional email delivery gradually.

Use a simple local database to remember history. Keep personal settings, credentials, and briefings outside the public repository. A scheduled run needs the computer to be awake, or a catch-up run when it starts again.

The first milestone should be **a useful personal briefing that you trust after checking its sources**. Prove that before expanding into a universal builder.

Optional detail: [full analysis and roadmap](RESEARCH-DETAILED.md) · [Ollama and hardware](OLLAMA.md) · [subscription tools](SUBSCRIPTION-BACKENDS.md).
