'use strict';
const $ = (id) => document.getElementById(id);
const token = document.querySelector('meta[name="newsagent-session"]').content;
let state, selectedIssue = '', busy = false, pending = false, polling, refreshing;
let sourceSignature = '', issueSignature = '', coverageSignature = '';
let builderStep = 0, builderBase, builderLoaded = false;
function el(tag, text, cls) { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (cls) node.className = cls; return node; }
function tell(text, error = false) { $('notice').textContent = text; $('notice').className = error ? 'error' : ''; }
async function api(path, body) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const options = body === undefined ? {} : {
      method: 'POST', headers: {'Content-Type': 'application/json', 'X-Newsagent-Token': token},
      body: JSON.stringify(body)
    };
    const response = await fetch(path, {...options, signal: controller.signal});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Request failed');
    return data;
  } catch (e) {
    if (e.name === 'AbortError') throw new Error('The local server took too long to respond. Check that it is still running.');
    throw e;
  } finally { clearTimeout(timeout); }
}
function link(text, url) {
  const a = el('a', text);
  try { const parsed = new URL(url); if (!['https:', 'http:'].includes(parsed.protocol)) return el('span', text); a.href = parsed.href; } catch { return el('span', text); }
  a.target = '_blank'; a.rel = 'noopener noreferrer'; return a;
}
function date(value) { return new Date(value).toLocaleDateString(undefined, {day: 'numeric', month: 'long', year: 'numeric'}); }
function renderCoverage(box, rows, collectedAt) {
  box.replaceChildren();
  if (!rows?.length) { box.append(el('p', 'Run a collection to check access.')); return; }
  const counts = el('div', undefined, 'coverage-summary');
  for (const [status, label] of [['checked', 'checked'], ['unavailable', 'unavailable'], ['disabled', 'disabled']]) {
    const n = rows.filter(row => row.status === status).length;
    if (n) counts.append(el('span', `${n} ${label}`, status));
  }
  box.append(counts, el('p', `Collected ${date(collectedAt)}. Recent samples only.`));
  const details = el('div');
  for (const row of rows) {
    const div = el('div', undefined, 'coverage-row');
    div.append(el('strong', `${row.name} · ${platformName(row.platform)}`), el('span', row.status, row.status), el('p', row.detail));
    details.append(div);
  }
  box.append(details);
}
function platformName(platform) {
  return {youtube: 'YouTube', instagram: 'Instagram', linkedin: 'LinkedIn', x: 'X', rss: 'RSS', web: 'Website'}[platform] || platform;
}
function field(story, key, label) {
  const p = el('p', undefined, 'story-field' + (key === 'next_step' ? ' takeaway' : ''));
  p.append(el('span', label + '.', 'label'), el('span', story[key]));
  return p;
}
function renderIssue() {
  const issue = state.issues.find(x => x.id === selectedIssue) || state.issues[0];
  const box = $('issue'); box.replaceChildren();
  if (!issue) {
    const empty = el('div', undefined, 'empty');
    empty.append(el('h1', 'Your newsletter is ready to start'), el('p', 'Choose New briefing to collect from your sources. For your first catch-up, select seven days in Options.'));
    const setup = el('a', 'Review your newsletter setup'); setup.href = '#build'; empty.append(setup);
    box.append(empty); return;
  }
  selectedIssue = issue.id; $('archive').value = selectedIssue;
  const configured = new Set(state.config.sources.filter(s => s.enabled).map(s => s.id));
  const collected = new Set(issue.coverage.filter(s => s.status !== 'disabled').map(s => s.source_id));
  const changedSources = [...configured].some(id => !collected.has(id)) || [...collected].some(id => !configured.has(id));
  const head = el('header', undefined, 'edition-header');
  const stamp = el('p', undefined, 'edition-date');
  const visible = [issue.content.overview, ...issue.content.stories.flatMap(s => [s.title, s.what_changed, s.why_it_matters, s.next_step])].join(' ');
  const skim = Math.max(1, Math.ceil(visible.trim().split(/\s+/).length / 200));
  stamp.append(el('span', date(issue.collected_at)), el('span', `${skim} min read`));
  head.append(stamp, el('h1', issue.content.title, 'edition-title'), el('p', issue.content.overview, 'overview'));
  if (changedSources) head.append(el('p', 'Earlier source list. Your next briefing will use the updated accounts.', 'archive-note'));
  const unavailable = issue.coverage.filter(row => row.status === 'unavailable').length;
  if (unavailable) {
    const note = el('p', undefined, 'coverage-note');
    const help = el('a', `${unavailable} sources unavailable`); help.href = '#sources';
    note.append(document.createTextNode('Limited coverage · '), help); head.append(note);
  }
  box.append(head);
  const evidence = new Map(issue.evidence.map(x => [x.id, x]));
  issue.content.stories.forEach((story, index) => {
    const article = el('article', undefined, 'story'); article.id = 'story-' + index;
    article.append(el('p', `${index + 1} / ${{act:'Act',understand:'Understand',watch:'Watch'}[story.importance]}`, 'story-meta'),
      el('h2', story.title), field(story, 'what_changed', 'What changed'),
      field(story, 'why_it_matters', 'Why it matters'), field(story, 'next_step', 'Takeaway'));
    const sources = [...new Set(story.evidence.map(e => e.source_id))].map(id => evidence.get(id)).filter(Boolean);
    const preview = el('p', undefined, 'evidence-preview'); preview.append(document.createTextNode('Sources · '));
    sources.forEach((source, i) => { if (i) preview.append(document.createTextNode(' / ')); preview.append(link(source.source_name, source.url)); });
    article.append(preview);
    const depth = el('details', undefined, 'story-depth');
    depth.append(el('summary', 'Evidence & context'));
    const inside = el('div', undefined, 'depth-content');
    inside.append(field(story, 'limitations', 'Caveat'), field(story, 'durability', 'What lasts'));
    const list = el('ol', undefined, 'evidence');
    for (const citation of story.evidence) {
      const source = evidence.get(citation.source_id), li = el('li');
      li.append(el('p', citation.claim), el('blockquote', citation.quote));
      if (source) li.append(link(source.title, source.url), el('p', `${source.access} · ${source.published_at ? date(source.published_at) : 'publication date unknown'}`));
      list.append(li);
    }
    inside.append(list);
    const feedback = el('div', undefined, 'feedback');
    const feedbackLabel = el('label', 'Was this useful?');
    const feedbackSelect = el('select'); feedbackSelect.append(new Option('Leave feedback…', ''));
    for (const [value, label] of [['useful','Useful'],['not-relevant','Not relevant'],['already-knew','Already knew'],['unsupported','Question the evidence'],['go-deeper','Explain more']]) {
      feedbackSelect.append(new Option(label, value));
    }
    const feedbackStatus = el('p', '', 'feedback-status'); feedbackStatus.setAttribute('role', 'status');
    feedbackSelect.addEventListener('change', async () => {
      if (!feedbackSelect.value) return;
      feedbackSelect.disabled = true;
      try {
        await api('/api/feedback', {issue_id: issue.id, event_key: story.event_key, verdict: feedbackSelect.value});
        feedbackStatus.textContent = 'Saved for the next briefing.';
      } catch (e) { feedbackStatus.textContent = e.message; }
      finally { feedbackSelect.disabled = false; }
    });
    feedbackLabel.append(feedbackSelect); feedback.append(feedbackLabel, feedbackStatus);
    inside.append(feedback); depth.append(inside); article.append(depth);
    if (story.watch_source_id && evidence.has(story.watch_source_id)) {
      const p = el('p', undefined, 'evidence-preview'); p.append(link('Watch the walkthrough ↗', evidence.get(story.watch_source_id).url), document.createTextNode(' — ' + story.watch_reason)); article.append(p);
    }
    box.append(article);
  });
  if (issue.content.low_priority.length) {
    const details = el('details', undefined, 'low-priority'); details.append(el('summary', `Low priority (${issue.content.low_priority.length})`));
    const list = el('ul', undefined, 'low-list');
    for (const item of issue.content.low_priority) { const li = el('li'), source = evidence.get(item.source_id); li.append(source ? link(item.title, source.url) : el('span', item.title), el('small', item.reason)); list.append(li); }
    details.append(list); box.append(details);
  }
  const verification = el('details', undefined, 'verification');
  verification.append(el('summary', `About this edition · ${issue.reading_minutes} min including context`), el('p', issue.verification + ' ' + issue.selection_note));
  const coverage = el('div'); renderCoverage(coverage, issue.coverage, issue.collected_at);
  verification.append(coverage); box.append(verification);
}
function renderSources() {
  const box = $('source-list'); box.replaceChildren();
  const groups = new Map();
  for (const source of state.config.sources) {
    if (!groups.has(source.name)) groups.set(source.name, []);
    groups.get(source.name).push(source);
  }
  for (const [name, sources] of groups) {
    const group = el('section', undefined, 'source-group');
    group.append(el('h2', name));
    for (const source of sources) {
      const row = el('div', undefined, 'source-row'), check = el('input');
      check.id = 'enable-' + source.id; check.type = 'checkbox'; check.checked = source.enabled; check.setAttribute('aria-label', `Enable ${source.name} on ${platformName(source.platform)}`);
      check.addEventListener('change', async () => { const config = structuredClone(state.config); config.sources.find(x => x.id === source.id).enabled = check.checked; await save(config); });
      const text = el('div'); text.append(link(platformName(source.platform), source.url));
      const coverage = state.collection?.coverage?.find(x => x.source_id === source.id);
      const schoolPage = source.platform === 'linkedin' && new URL(source.url).pathname.startsWith('/school/');
      text.append(el('span', !source.enabled ? 'Disabled' : schoolPage ? 'Saved · connector does not support this page' : coverage ? {checked:'Last collection checked',unavailable:'Connection unavailable',disabled:'Not collected'}[coverage.status] : 'Not collected yet', 'source-state'));
      const remove = el('button', 'Remove'); remove.id = 'remove-' + source.id; remove.setAttribute('aria-label', `Remove ${source.name} on ${platformName(source.platform)}`);
      remove.addEventListener('click', async () => { const config = structuredClone(state.config); config.sources = config.sources.filter(x => x.id !== source.id); await save(config); });
      row.append(check, text, remove); group.append(row);
    }
    box.append(group);
  }
}
function renderSettings() {
  const form = $('settings-form');
  for (const [key, value] of Object.entries({...state.config.profile, ...state.config.provider})) {
    form.elements.namedItem(key).value = value;
  }
}
function setControls() {
  for (const id of ['generate', 'collect', 'write']) $(id).disabled = !state || busy || pending;
  if (state) {
    $('write').disabled ||= !state.collection?.items;
    $('generate').disabled ||= !state.config.profile.description.trim() || !state.config.profile.interests.trim() || !state.config.sources.some(s => s.enabled);
  }
  $('generate').textContent = busy ? 'Working…' : 'New briefing';
  $('today').setAttribute('aria-busy', String(busy));
  for (const control of document.querySelectorAll('#source-list input, #source-list button, form button, #export-config, #import-config')) {
    control.disabled = busy || pending;
  }
}
function syncIssue(force = false) {
  const signature = JSON.stringify([selectedIssue, state.issues.map(i => i.id), state.config.sources]);
  if (force || signature !== issueSignature) {
    renderIssue(); issueSignature = signature;
  }
}
async function refresh() {
  if (refreshing) return refreshing;
  refreshing = (async () => {
    const next = await api('/api/state');
    const first = !state, wasBusy = busy;
    const changedIssues = JSON.stringify(state?.issues.map(i => i.id)) !== JSON.stringify(next.issues.map(i => i.id));
    state = next; busy = state.job.running;
    if (first || changedIssues) {
      selectedIssue = state.issues[0]?.id || '';
      $('archive').replaceChildren(...(state.issues.length ? state.issues.map(issue =>
        new Option(`${date(issue.collected_at)} · ${issue.content.title}`, issue.id)) : [new Option('No editions yet', '')]));
    }
    $('archive').value = selectedIssue;
    if (first) {
      renderSettings();
      if (!state.issues.length && !state.config.profile.description.trim() && !location.hash) location.hash = '#build';
      showPage();
    }
    const signature = JSON.stringify([state.config.sources, state.collection?.coverage]);
    if (signature !== sourceSignature) {
      const focused = document.activeElement?.id;
      renderSources(); sourceSignature = signature;
      if (focused?.startsWith('enable-') || focused?.startsWith('remove-')) $(focused)?.focus();
    }
    const coverageKey = JSON.stringify(state.collection);
    if (coverageKey !== coverageSignature) {
      renderCoverage($('source-coverage'), state.collection?.coverage, state.collection?.collected_at);
      coverageSignature = coverageKey;
    }
    syncIssue(); setControls();
    $('run-status').className = state.job.error ? 'error' : '';
    $('run-status').textContent = state.job.error
      ? `${state.job.error} Your saved edition is unchanged.`
      : busy ? state.job.stage : wasBusy ? (changedIssues ? 'Briefing ready.' : 'Collection finished. See Sources for coverage.') : '';
  })();
  try { await refreshing; }
  finally {
    refreshing = undefined;
    clearTimeout(polling);
    if (busy) polling = setTimeout(() => refresh().catch(e => tell(e.message, true)), 2500);
  }
}
async function save(config) {
  if (pending || busy) return false;
  pending = true; setControls();
  let saved = false;
  try {
    await api('/api/config', config); saved = true;
    await refresh();
    tell('Saved. Changes apply to the next briefing.');
    return true;
  } catch (e) {
    tell(saved ? 'Saved, but the page could not refresh. Reload to reconnect.' : e.message, true);
    if (!saved) { sourceSignature = ''; renderSources(); }
    return saved;
  } finally { pending = false; setControls(); }
}
async function run(action) {
  if (pending || busy) return;
  pending = true; setControls(); tell('');
  $('run-status').className = '';
  $('run-status').textContent = 'Starting…';
  try {
    await api('/api/run', {action, days: Number($('lookback').value)});
    busy = true;
    await refresh();
  } catch (e) { $('run-status').textContent = e.message; $('run-status').className = 'error'; }
  finally { pending = false; setControls(); }
}
function showPage() {
  const page = {'#sources':'sources','#settings':'settings','#build':'builder'}[location.hash] || 'today';
  for (const panel of document.querySelectorAll('.panel')) panel.hidden = panel.id !== page;
  for (const nav of document.querySelectorAll('[data-page]')) {
    const active = nav.dataset.page === page;
    if (active) nav.setAttribute('aria-current', 'page'); else nav.removeAttribute('aria-current');
  }
  if (page === 'builder' && state && !builderLoaded) loadBuilder(state.config);
  if (page !== 'builder') builderLoaded = false;
  document.title = `${{today:'Briefing',sources:'Sources',settings:'Settings',builder:'Build your newsletter'}[page]} · NewsAgentBuilder`;
  tell('');
}

function loadBuilder(config) {
  builderBase = structuredClone(config); builderStep = 0; builderLoaded = true;
  const form = $('builder-form');
  for (const [key, value] of Object.entries({...config.profile, ...config.provider})) form.elements.namedItem(key).value = value;
  form.elements.namedItem('source_urls').value = config.sources.filter(s => s.enabled).map(s => s.url).join('\n');
  const disabled = config.sources.filter(s => !s.enabled).length;
  $('builder-source-note').textContent = disabled ? `${disabled} disabled sources will be kept. You can manage them in Sources.` : '';
  $('builder-checks').replaceChildren(); $('builder-error').textContent = '';
  updateProvider(); renderBuilderStep();
}
function builderConfig() {
  const form = $('builder-form'), config = structuredClone(builderBase);
  const value = name => form.elements.namedItem(name).value.trim();
  for (const key of Object.keys(config.profile)) config.profile[key] = key === 'reading_minutes' ? Number(value(key)) : value(key);
  for (const key of Object.keys(config.provider)) config.provider[key] = value(key);
  if (config.provider.backend === 'codex') config.provider.base_url = '';
  if (config.provider.backend !== 'compatible') config.provider.key_env = 'NEWSAGENT_API_KEY';
  const urls = [...new Set(value('source_urls').split(/\n/).map(s => s.trim()).filter(Boolean))];
  if (!urls.length) throw new Error('Add at least one source URL.');
  config.sources = urls.map(url => {
    const existing = builderBase.sources.find(s => s.url === url);
    if (existing) return {...existing, enabled:true};
    let parsed;
    try { parsed = new URL(url); } catch { throw new Error('Each source needs a full URL starting with https://.'); }
    if (!['https:', 'http:'].includes(parsed.protocol)) throw new Error('Use public HTTP or HTTPS source URLs.');
    const host = parsed.hostname.replace(/^www\./, '');
    const platform = {'youtube.com':'youtube','youtu.be':'youtube','instagram.com':'instagram','x.com':'x','twitter.com':'x','linkedin.com':'linkedin'}[host] || 'rss';
    const parts = parsed.pathname.split('/').filter(Boolean);
    const name = platform === 'rss' ? host : (parts[parts[0] === 'in' || parts[0] === 'company' || parts[0] === 'school' ? 1 : 0] || host).replace(/^@/, '');
    return {id:'source-' + crypto.randomUUID().slice(0,12), name, platform, url, enabled:true};
  });
  config.sources.push(...builderBase.sources.filter(s => !s.enabled && !urls.includes(s.url)));
  if (config.sources.length > 30) throw new Error('Use at most 30 sources, including disabled sources.');
  return config;
}
function updateProvider() {
  const form = $('builder-form'), backend = form.elements.namedItem('backend').value;
  $('builder-endpoint').hidden = backend === 'codex'; $('builder-key').hidden = backend !== 'compatible';
  form.elements.namedItem('model').required = backend !== 'codex';
  form.elements.namedItem('base_url').required = backend !== 'codex';
  form.elements.namedItem('key_env').required = backend === 'compatible';
  $('builder-provider-note').textContent = {
    codex:'Uses the installed Codex CLI and your own ChatGPT login. Inference happens at OpenAI and uses your subscription allowance. No separate API key is needed.',
    ollama:'Uses an installed local model. Start Ollama first and enter its exact model tag. Speed and quality depend on your hardware; this app downloads nothing.',
    compatible:'Uses your chosen endpoint and model. The provider receives your profile and evidence. Its pricing and quotas apply; JSON-schema support is required.'
  }[backend];
  form.elements.namedItem('model').placeholder = backend === 'codex' ? 'Leave empty for the Codex default' : 'Exact installed or available model name';
}
function renderBuilderStep() {
  for (const fieldset of $('builder-form').querySelectorAll('[data-step]')) {
    fieldset.hidden = Number(fieldset.dataset.step) !== builderStep;
    fieldset.disabled = fieldset.hidden;
  }
  $('builder-progress').textContent = `Step ${builderStep + 1} of 3 · ${['Your interests','Your sources','Your model'][builderStep]}`;
  $('builder-back').hidden = builderStep === 0;
  $('builder-next').textContent = builderStep === 2 ? 'Save my newsletter' : 'Continue';
  if (builderStep === 2) {
    const config = builderConfig();
    $('builder-review').replaceChildren(el('strong', 'Your newsletter'),
      el('p', `${config.sources.filter(s => s.enabled).length} sources · ${config.profile.language} · up to ${config.profile.reading_minutes} minutes`),
      el('p', 'Each main story explains what changed, why it matters to you, and the evidence. Low-priority items stay brief.'));
  }
}
function renderChecks(checks) {
  const list = el('ul', undefined, 'setup-checks');
  for (const check of checks) {
    const row = el('li'); row.append(el('strong', `${check.name} · ${{found:'found',missing:'needs setup',manual:'check manually',unsupported:'unsupported'}[check.status]}`), el('p', check.detail)); list.append(row);
  }
  $('builder-checks').replaceChildren(el('p', 'Local prerequisites only. Source access and model generation have not been tested.', 'help'), list);
}
$('builder-form').addEventListener('submit', async event => {
  event.preventDefault(); if (!state || pending || busy) return;
  $('builder-error').textContent = '';
  try {
    if (builderStep < 2) {
      if (builderStep === 1) builderConfig();
      builderStep++; renderBuilderStep();
      $('builder-form').querySelector(`[data-step="${builderStep}"] textarea, [data-step="${builderStep}"] select`).focus();
      return;
    }
    if (await save(builderConfig())) {
      renderSettings(); location.hash = '#briefing';
    }
  } catch (e) { $('builder-error').textContent = e.message; }
});
$('builder-back').addEventListener('click', () => { builderStep--; $('builder-error').textContent = ''; renderBuilderStep(); });
$('builder-form').elements.namedItem('backend').addEventListener('change', event => {
  const form = $('builder-form');
  form.elements.namedItem('model').value = '';
  form.elements.namedItem('base_url').value = event.target.value === 'ollama' ? 'http://127.0.0.1:11434' : '';
  updateProvider();
});
$('builder-form').addEventListener('input', () => $('builder-checks').replaceChildren());
$('builder-check').addEventListener('click', async () => {
  if (pending || busy) return;
  pending = true; setControls(); $('builder-error').textContent = '';
  try { renderChecks((await api('/api/check', builderConfig())).checks); }
  catch (e) { $('builder-error').textContent = e.message; }
  finally { pending = false; setControls(); }
});
$('export-config').addEventListener('click', () => {
  if (!state || busy || pending) return;
  const anchor = el('a'); anchor.href = '/api/export'; anchor.download = 'newsletter-config.json';
  document.body.append(anchor); anchor.click(); anchor.remove();
});
$('import-config').addEventListener('change', async event => {
  const file = event.target.files[0];
  if (!file || pending || busy) return;
  pending = true; setControls();
  try {
    if (file.size > 100000) throw new Error('Configuration files must be under 100 KB.');
    const config = JSON.parse(await file.text());
    await api('/api/check', config);
    loadBuilder(config); location.hash = '#build';
  } catch (e) { tell('Could not import configuration. ' + e.message, true); }
  finally { pending = false; event.target.value = ''; setControls(); }
});
window.addEventListener('hashchange', showPage);
window.addEventListener('focus', () => refresh().catch(e => tell(e.message, true)));
$('generate').addEventListener('click', () => run('run'));
$('collect').addEventListener('click', () => run('collect'));
$('write').addEventListener('click', () => run('generate'));
$('archive').addEventListener('change', () => { selectedIssue = $('archive').value; syncIssue(); });
$('settings-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (!state) return;
  const data = Object.fromEntries(new FormData(event.target)), config = structuredClone(state.config);
  for (const key of Object.keys(config.profile)) config.profile[key] = key === 'reading_minutes' ? Number(data[key]) : data[key];
  for (const key of Object.keys(config.provider)) config.provider[key] = data[key].trim();
  await save(config);
});
$('add-source').addEventListener('submit', async event => {
  event.preventDefault(); if (!state) return;
  const data = Object.fromEntries(new FormData(event.target)), config = structuredClone(state.config);
  config.sources.push({...data, id:'source-' + crypto.randomUUID().slice(0,12), enabled:true});
  if (await save(config)) event.target.reset();
});
$('import').addEventListener('submit', async event => {
  event.preventDefault(); if (pending || busy) return;
  pending = true; setControls();
  try {
    const data = Object.fromEntries(new FormData(event.target));
    await api('/api/import', {...data, platform:'web', access:'user-provided text; not independently fetched'});
    event.target.reset(); await refresh();
    tell('Imported. Use Options → Write from collection in your briefing.');
  } catch (e) { tell(e.message, true); }
  finally { pending = false; setControls(); }
});
showPage();
refresh().catch(e => tell('Cannot connect to the local server. ' + e.message, true));
