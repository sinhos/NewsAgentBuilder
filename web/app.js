'use strict';
const $ = (id) => document.getElementById(id);
const token = document.querySelector('meta[name="newsagent-session"]').content;
let state, selectedIssue = '', busy = false, polling;
function el(tag, text, cls) { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (cls) node.className = cls; return node; }
function tell(text, error = false) { $('notice').textContent = text; $('notice').className = error ? 'error' : ''; }
async function api(path, body) {
  const options = body === undefined ? {} : {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Newsagent-Token': token}, body: JSON.stringify(body)};
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Request failed');
  return data;
}
function link(text, url) {
  const a = el('a', text);
  try { const parsed = new URL(url); if (!['https:', 'http:'].includes(parsed.protocol)) return el('span', text); a.href = parsed.href; } catch { return el('span', text); }
  a.target = '_blank'; a.rel = 'noopener noreferrer'; return a;
}
function date(value) { return new Date(value).toLocaleDateString(undefined, {day: 'numeric', month: 'long', year: 'numeric'}); }
function renderCoverage(rows, collectedAt) {
  const box = $('coverage'); box.replaceChildren(el('h3', 'Collection coverage'));
  if (!rows?.length) { box.append(el('p', 'Run a collection to check access.')); return; }
  const counts = el('div', undefined, 'coverage-summary');
  for (const [status, label] of [['checked', 'checked'], ['unavailable', 'unavailable'], ['disabled', 'disabled']]) {
    const n = rows.filter(row => row.status === status).length;
    if (n) counts.append(el('span', `${n} ${label}`, status));
  }
  box.append(counts, el('p', `Collected ${date(collectedAt)}. Recent samples only.`));
  const details = el('details'); details.append(el('summary', 'View source status'));
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
  p.append(el('span', label, 'label'), el('span', story[key]));
  return p;
}
function renderIssue() {
  const issue = state.issues.find(x => x.id === selectedIssue) || state.issues[0];
  const box = $('issue'); box.replaceChildren(); $('issue-outline').replaceChildren();
  if (!issue) {
    const empty = el('div', undefined, 'empty');
    empty.append(el('p', 'YOUR FIRST EDITION', 'eyebrow'), el('h2', 'Your sources. A clearer view.'), el('p', 'Generate a briefing to find what changed, why it matters, and what the evidence actually supports. Choose seven days for your first catch-up.'));
    box.append(empty); renderCoverage(state.collection?.coverage, state.collection?.collected_at); return;
  }
  selectedIssue = issue.id; $('archive').value = selectedIssue;
  const configured = new Set(state.config.sources.filter(s => s.enabled).map(s => s.id));
  const collected = new Set(issue.coverage.filter(s => s.status !== 'disabled').map(s => s.source_id));
  if ([...configured].some(id => !collected.has(id)) || [...collected].some(id => !configured.has(id))) {
    box.append(el('p', 'This edition uses your previous source list. Generate a new briefing to use your current sources.', 'archive-note'));
  }
  const head = el('header', undefined, 'edition-header');
  const stamp = el('p', undefined, 'edition-date');
  const visible = [issue.content.overview, ...issue.content.stories.flatMap(s => [s.title, s.what_changed, s.why_it_matters, s.next_step])].join(' ');
  const skim = Math.max(1, Math.ceil(visible.trim().split(/\s+/).length / 200));
  stamp.append(el('span', date(issue.collected_at)), el('span', `${skim} min summary`, 'read-time'), el('span', `${issue.content.stories.length} stories`));
  head.append(stamp, el('h2', issue.content.title, 'edition-title'), el('p', issue.content.overview, 'overview'));
  box.append(head);
  const evidence = new Map(issue.evidence.map(x => [x.id, x]));
  if (!issue.content.stories.length) box.append(el('p', 'No story cleared the relevance and evidence threshold. Check coverage before drawing conclusions.'));
  issue.content.stories.forEach((story, index) => {
    const article = el('article', undefined, 'story'); article.id = 'story-' + index;
    const top = el('div', undefined, 'story-top'), meta = el('p', undefined, 'story-meta');
    meta.append(el('span', {act:'Worth acting on',understand:'Worth understanding',watch:'Keep an eye on'}[story.importance], 'priority ' + story.importance), el('span', story.topic.replace('-', ' ')));
    top.append(meta, el('span', String(index + 1), 'story-number'));
    article.append(top, el('h3', story.title), field(story, 'what_changed', 'What changed'), field(story, 'why_it_matters', 'Why it matters'), field(story, 'next_step', 'Your takeaway'));
    const sources = [...new Set(story.evidence.map(e => e.source_id))].map(id => evidence.get(id)).filter(Boolean);
    const preview = el('p', undefined, 'evidence-preview'); preview.append(document.createTextNode('Sources · '));
    sources.forEach((source, i) => { if (i) preview.append(document.createTextNode(' / ')); preview.append(link(source.source_name, source.url)); });
    article.append(preview);
    const depth = el('details', undefined, 'story-depth');
    depth.append(el('summary', `Evidence & context · ${story.evidence.length} cited claims`));
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
    for (const [verdict, label] of [['useful','Useful'],['not-relevant','Not for me'],['already-knew','Already knew'],['unsupported','Question the evidence'],['go-deeper','Go deeper']]) {
      const button = el('button', label);
      button.addEventListener('click', async () => {
        try { await api('/api/feedback', {issue_id: issue.id, event_key: story.event_key, verdict}); tell('Feedback saved for the next briefing.'); }
        catch (e) { tell(e.message, true); }
      }); feedback.append(button);
    }
    inside.append(feedback); depth.append(inside); article.append(depth);
    if (story.watch_source_id && evidence.has(story.watch_source_id)) {
      const p = el('p', undefined, 'evidence-preview'); p.append(link('Watch the walkthrough ↗', evidence.get(story.watch_source_id).url), document.createTextNode(' — ' + story.watch_reason)); article.append(p);
    }
    box.append(article);
    const jump = el('a', `${index + 1}. ${story.title}`); jump.href = '#story-' + index; $('issue-outline').append(jump);
  });
  if (issue.content.low_priority.length) {
    const details = el('details', undefined, 'low-priority'); details.append(el('summary', `Also on the radar · ${issue.content.low_priority.length} low-priority items`));
    const list = el('ul', undefined, 'low-list');
    for (const item of issue.content.low_priority) { const li = el('li'), source = evidence.get(item.source_id); li.append(source ? link(item.title, source.url) : el('span', item.title), el('small', item.reason)); list.append(li); }
    details.append(list); box.append(details);
  }
  const verification = el('details', undefined, 'verification');
  verification.append(el('summary', `About this edition · ${issue.reading_minutes} min including context`), el('p', issue.verification + ' ' + issue.selection_note));
  box.append(verification); renderCoverage(issue.coverage, issue.collected_at);
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
    group.append(el('h3', name), el('p', `${sources.filter(s => s.enabled).length} of ${sources.length} channels enabled`));
    for (const source of sources) {
      const row = el('div', undefined, 'source-row'), check = el('input');
      check.type = 'checkbox'; check.checked = source.enabled; check.setAttribute('aria-label', `Enable ${source.name} on ${platformName(source.platform)}`);
      check.addEventListener('change', async () => { const config = structuredClone(state.config); config.sources.find(x => x.id === source.id).enabled = check.checked; await save(config); });
      const text = el('div'); text.append(link(platformName(source.platform) + ' ↗', source.url));
      const coverage = state.collection?.coverage?.find(x => x.source_id === source.id);
      const schoolPage = source.platform === 'linkedin' && new URL(source.url).pathname.startsWith('/school/');
      text.append(el('span', !source.enabled ? 'Disabled' : schoolPage ? 'Saved · connector does not support this page' : coverage ? {checked:'Last collection checked',unavailable:'Connection unavailable',disabled:'Not collected'}[coverage.status] : 'Not collected yet', 'source-state'));
      const remove = el('button', 'Remove'); remove.setAttribute('aria-label', `Remove ${source.name} on ${platformName(source.platform)}`);
      remove.addEventListener('click', async () => { const config = structuredClone(state.config); config.sources = config.sources.filter(x => x.id !== source.id); await save(config); });
      row.append(check, text, remove); group.append(row);
    }
    box.append(group);
  }
}
function renderSettings() {
  const form = $('settings-form'); for (const [key, value] of Object.entries({...state.config.profile, ...state.config.provider})) form.elements.namedItem(key).value = value;
  $('budget').textContent = state.config.profile.reading_minutes;
}
async function refresh(settings = false) {
  const old = state?.issues[0]?.id; state = await api('/api/state');
  if (old !== state.issues[0]?.id) selectedIssue = state.issues[0]?.id || '';
  const archive = $('archive'); archive.replaceChildren();
  if (!state.issues.length) archive.append(new Option('No editions yet', ''));
  for (const issue of state.issues) archive.append(new Option(`${date(issue.created_at)} · ${issue.content.title}`, issue.id));
  archive.value = selectedIssue || state.issues[0]?.id || '';
  if (settings) renderSettings();
  renderSources();
  if (settings || old !== state.issues[0]?.id || !$('issue').hasChildNodes()) renderIssue();
  else if (!state.issues.length) renderCoverage(state.collection?.coverage, state.collection?.collected_at);
  busy = state.job.running;
  for (const id of ['generate', 'collect', 'write']) $(id).disabled = busy;
  $('run-status').textContent = (state.job.stage === 'Ready' ? '' : state.job.stage) + (state.job.error ? ': ' + state.job.error : '');
  if (state.job.error) tell(state.job.error, true);
  if (busy && !polling) polling = setInterval(() => refresh().catch(e => tell(e.message, true)), 4000);
  if (!busy && polling) { clearInterval(polling); polling = undefined; }
}
async function save(config) {
  try { await api('/api/config', config); await refresh(true); tell('Preferences saved. They apply to the next run.'); }
  catch (e) { tell(e.message, true); await refresh(true); }
}
async function run(action) {
  try { tell(''); await api('/api/run', {action, days: Number($('lookback').value)}); await refresh(); }
  catch (e) { tell(e.message, true); }
}
for (const button of document.querySelectorAll('[data-tab]')) button.addEventListener('click', () => { for (const tab of document.querySelectorAll('[data-tab]')) { const active = tab === button; tab.classList.toggle('active', active); tab.setAttribute('aria-pressed', String(active)); $(tab.dataset.tab).hidden = !active; } tell(''); });
$('generate').addEventListener('click', () => run('run'));
$('collect').addEventListener('click', () => run('collect'));
$('write').addEventListener('click', () => run('generate'));
$('archive').addEventListener('change', () => { selectedIssue = $('archive').value; renderIssue(); });
$('settings-form').addEventListener('submit', async (event) => { event.preventDefault(); const data = Object.fromEntries(new FormData(event.target)); const config = structuredClone(state.config); for (const key of Object.keys(config.profile)) config.profile[key] = key === 'reading_minutes' ? Number(data[key]) : data[key]; for (const key of Object.keys(config.provider)) config.provider[key] = data[key].trim(); await save(config); });
$('add-source').addEventListener('submit', async (event) => { event.preventDefault(); const data = Object.fromEntries(new FormData(event.target)); const config = structuredClone(state.config); config.sources.push({...data, id: 'source-' + crypto.randomUUID().slice(0, 12), enabled: true}); await save(config); if (!$('notice').classList.contains('error')) event.target.reset(); });
$('import').addEventListener('submit', async (event) => { event.preventDefault(); try { const data = Object.fromEntries(new FormData(event.target)); await api('/api/import', {...data, platform: 'web', access: 'user-provided text; not independently fetched'}); tell('Evidence imported. Choose “Write from collected material” to use it without collecting again.'); event.target.reset(); await refresh(); } catch (e) { tell(e.message, true); } });
refresh(true).catch(e => tell('Could not connect to the local server: ' + e.message, true));
