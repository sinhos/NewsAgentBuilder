# ChatGPT subscriptions, third-party clients, and API proxies

Researched 18 September 2026. Companion to the [main report](RESEARCH.md) and [Ollama assessment](OLLAMA.md). The reviewed proxies were not installed, authenticated, or benchmarked.

## 1. Direct answer

**Yes: tools exist that make subscription-backed Codex access usable from third-party applications, and some expose an API-compatible local endpoint.** That does not turn a regular ChatGPT subscription into unlimited, general-purpose OpenAI API credit.

The useful question is which route provides the needed model access through a maintainable integration, using each user's own account and respecting its limits. For this project, investigate the official local Codex integration first; a proxy is an optional interoperability layer, not a necessary foundation.

## 2. Four categories that should not be conflated

| Route | What actually happens | Assessment |
|---|---|---|
| Official Codex CLI/SDK | Your program controls the official local client under the user's supported authentication | First subscription-backed route to test |
| Third-party agent client | Another agent application provides its own interface and documented provider integration | Can be useful as a host for a portable skill |
| Subscription API proxy | A local server translates API requests and forwards them using account authentication | Technically useful, but adds credential handling and compatibility dependencies |
| ChatGPT website automation | A tool drives browser sessions or imitates web requests | Most fragile fit for a dependable daily worker |

Do not infer the acceptability of every third-party client from the existence of a working login, or claim all third-party use is forbidden. Distinguish first-party integration documentation, third-party feature claims, and unverified assumptions.

## 3. The official route is stronger than many tutorials suggest

OpenAI documents ChatGPT subscription sign-in separately from usage-based API-key authentication. These routes have different account controls and data-handling settings. An adapter must explicitly select the intended route instead of accidentally using an available paid API key. [Authentication documentation](https://learn.chatgpt.com/docs/auth).

The official Codex SDK supports programmatic local agents. Current documentation includes a stable Python package, `openai-codex`, as well as a TypeScript SDK. Python therefore provides a direct option for the proposed core without requiring a JavaScript application. [Codex SDK](https://learn.chatgpt.com/docs/codex-sdk).

For richer client integration, App Server documents managed ChatGPT OAuth, account information, and rate-limit retrieval. It uses an agent protocol rather than simply implementing ordinary Chat Completions. Prefer the documented managed-auth path; avoid owning token refresh unless there is a concrete reason. Its WebSocket transport is marked experimental/unsupported, so a local integration should evaluate the documented stdio path. [App Server](https://learn.chatgpt.com/docs/app-server).

For a first personal prototype, `codex exec` can process evidence packets and emit structured results without a new server. Account-auth CI guidance specifically warns against that advanced workflow in public/open-source repositories. Keep personal runs and authentication local and separate from the public project's CI. [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).

Recommendation: implement a `codex_local` adapter that delegates authentication to the user's supported client, restricts tools, tracks completion/errors, and stops when limits are reached. Keep `ollama_local` as the independent alternative. These are proposed adapters, not implemented features.

## 4. Concrete third-party projects

### OpenCode: an alternative agent host

[OpenCode](https://github.com/anomalyco/opencode) is an MIT-licensed coding agent. Its provider documentation explicitly describes an OpenAI connection with ChatGPT Plus/Pro login. That is a real documented third-party subscription route, although this research did not test the login or establish every model's availability on a particular account. [Provider setup](https://opencode.ai/docs/providers/#openai).

It could run a portable NewsAgentBuilder skill. It is not automatically a drop-in inference backend for the Python worker; its process, permissions, task output, and limits still need an integration contract.

The documentation's broad wording about model availability should not become a promise that every ChatGPT feature is exposed. Test exact model IDs and required capabilities. Do not generalize OpenAI integration behavior to other providers.

### CLIProxyAPI: API-shaped access

[CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI) is an MIT-licensed proxy. It documents Codex OAuth support and multiple API protocol surfaces. Its inspected executor sends requests to a Codex backend using bearer authentication; this is more than a wrapper that only invokes the official CLI. [Executor implementation](https://github.com/router-for-me/CLIProxyAPI/blob/main/internal/runtime/executor/codex_executor_execute.go).

Its appeal is interoperability: an application expecting an OpenAI-compatible interface can point at a local proxy. The service upstream still performs the inference, and account quotas still apply. Translation can also change available parameters, tool behavior, reasoning fields, errors, and streaming semantics. Compatibility should be tested task by task.

The inspected example configuration defaults the listener to all interfaces, stores authentication under a local auth directory, and includes credential-routing and quota-fallback settings. It separately controls the management API. A self-hosted installation intended for one user needs explicit loopback binding, strong client authentication, restricted credential-file permissions, reviewed logs, and deliberate fallback settings. [Example configuration](https://github.com/router-for-me/CLIProxyAPI/blob/main/config.example.yaml).

For NewsAgentBuilder, keep any such connector experimental and opt-in. Use one user's own authorized account, stop on quota exhaustion, and never quietly change model/provider or consume paid fallback credits. Do not make multi-account rotation or quota circumvention part of the product's cost proposition.

The reviewed OpenAI documentation establishes official client integration paths; it does **not** establish blanket approval or a service guarantee for this particular proxy. This research cannot quantify account-enforcement risk. A repository's MIT license grants rights in its code, not rights to an upstream provider's service.

### VibeProxy and Quotio: convenience layers

[VibeProxy](https://github.com/automazeio/vibeproxy) provides a macOS interface around subscription/proxy configuration. Its own README says it is built on CLIProxyAPIPlus and handles OAuth, token management, and routing. It is a convenience option, not a distinct free model provider. Marketing claims about safety or model support need independent verification.

[Quotio](https://github.com/nguyenphutrong/quotio) documents a macOS app and CLI for quota/account management and proxy lifecycle. It may help an advanced user inspect usage, but it is unnecessary for the minimal newsletter core. Both repositories identify MIT licenses. Versions reviewed are recorded in [the repository ledger](research-repositories.json).

Adding several wrappers would multiply the troubleshooting surface: newsletter → agent client → desktop wrapper → proxy → provider. Prefer the shortest integration that meets the user's needs.

## 5. Why this is not the same as a free API subscription

Six distinctions matter:

1. **Billing:** no additional API invoice may be possible, but the subscription itself still costs money and has eligibility conditions.
2. **Quota:** newsletter runs consume the user's available allowance and may compete with coding work. A local proxy does not create extra capacity.
3. **Model access:** a plan's ChatGPT interface, Codex surface, and developer API can expose different models and features.
4. **Tools:** web browsing, connectors, files, images, and other host capabilities do not automatically transfer to an API-compatible proxy.
5. **Privacy:** a local proxy still sends inference input to the upstream service; a hosted third-party relay introduces another operator.
6. **Reliability:** refresh tokens, authentication policies, backend formats, model aliases, and quotas can change independently of the newsletter code.

For example, a browser feature labeled “deep research” should not be advertised as available through a proxy just because text generation works. Likewise, a model-generated citation is not evidence that browsing happened.

Avoid community “free API” endpoints that require uploading a personal account session to an unknown host. They introduce a new trust relationship that is unnecessary for a locally owned project.

## 6. Provider-specific conditions

OpenAI's documented client integration is the relevant starting point for ChatGPT-backed operation. Do not assume another provider permits the same method.

Anthropic's current Claude Code documentation distinguishes signing into the unmodified official binary from third-party applications routing requests through consumer subscription credentials or collecting session tokens. This is one reason a generic “all subscriptions become APIs” promise is misleading. [Claude Code conditions](https://code.claude.com/docs/en/legal-and-compliance).

Gemini CLI has its own authentication and quota rules; Gemini API has separate conditions. Read each integration on its own terms. The main report details the regional API nuance relevant to Switzerland. [Gemini CLI quotas](https://geminicli.com/docs/resources/quota-and-pricing/), [Gemini API terms](https://ai.google.dev/gemini-api/terms).

## 7. Evaluation before supporting a proxy

Use the exact same evidence packet and output contract for Ollama, official Codex, and any optional proxy. Test:

- Correct model routing and accurate reporting of the model actually used.
- Schema fidelity, numeric accuracy, uncertainty, and citation support.
- Timeout, interruption, expired login, malformed output, and exhausted quota.
- Whether retrying repeats a completed task or causes unwanted tool actions.
- Where credentials and prompt/response logs are stored, and which hosts receive data.
- Whether any default fallback changes provider, account, model, or cost.
- Behavior after a proxy or official client update.

Record failure explicitly. A local/extractive fallback can be offered, but it should be marked as a different mode rather than presented as the same model's completed work.

## 8. Product decision

Offer three clear choices during setup:

| User preference | Recommended route |
|---|---|
| No subscription, private local inference | Ollama with a qualified local model |
| Already has supported ChatGPT/Codex access | Official local Codex client integration |
| Already uses a different agent application | Portable skill in that application, with its own supported provider setup |

Provide an advanced compatible-endpoint setting later for users who independently operate a proxy or another local runtime. Do not bundle a proxy, request browser cookies, or turn token export into the standard onboarding flow.

This supports the user's choice of hardware and existing subscriptions while keeping the core project usable without either a hosted business or a paid inference dependency.
