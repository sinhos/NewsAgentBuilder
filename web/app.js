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
  const box = $('coverage'); box.replaceChildren(el('h3', 'Source coverage'));
  if (!rows?.length) { box.append(el('p', 'No collection yet. Your first run will check each enabled source.')); return; }
  box.append(el('p', `Collected ${date(collectedAt)}. Bounded samples; missing sources are not a quiet news day.`));
  for (const row of rows) { const div = el('div', undefined, 'coverage-row'); div.append(el('strong', row.name), el('span', row.status, row.status), el('p', row.detail)); box.append(div); }
}
function renderIssue() {
  const issue = state.issues.find(x => x.id === selectedIssue) || state.issues[0];
  const box = $('issue'); box.replaceChildren();
  if (!issue) {
    const empty = el('div', undefined, 'empty');
    empty.append(el('p', 'YOUR FIRST EDITION', 'eyebrow'), el('h2', 'A clearer view of what matters.'), el('p', 'Your priorities and starter sources are ready. Make a briefing here, or ask Codex to use $news-brief. The first catch-up can cover seven days; daily runs cover the last 24 hours.'), el('p', 'You will see the evidence, the practical implications, and anything the collector could not access.'));
    box.append(empty); renderCoverage(state.collection?.coverage, state.collection?.collected_at); return;
  }
  selectedIssue = issue.id; $('archive').value = selectedIssue;
  box.append(el('p', `${date(issue.created_at)} · ${issue.reading_minutes} min read · ${issue.provider.backend}`, 'edition-date'), el('h2', issue.content.title, 'edition-title'), el('p', issue.content.overview, 'overview'));
  const evidence = new Map(issue.evidence.map(x => [x.id, x]));
  if (!issue.content.stories.length) box.append(el('p', 'No story cleared the editorial threshold in this collection. Check coverage before drawing conclusions.'));
  for (const story of issue.content.stories) {
    const article = el('article', undefined, 'story');
    article.append(el('p', `${story.importance} / ${story.topic}`, 'story-meta'), el('h3', story.title));
    for (const [key, label] of [['what_changed', 'What changed'], ['why_it_matters', 'Why it matters to you'], ['next_step', 'Your next step'], ['durability', 'What lasts'], ['limitations', 'What is still uncertain']]) {
      const paragraph = el('p', undefined, key === 'limitations' ? 'caveat' : ''); paragraph.append(el('span', label, 'label'), document.createTextNode(story[key])); article.append(paragraph);
    }
    const details = el('details', undefined, 'evidence'); details.append(el('summary', `Evidence · ${story.evidence.length} cited claims`));
    const list = el('ol');
    for (const citation of story.evidence) { const source = evidence.get(citation.source_id); const li = el('li'); li.append(el('p', citation.claim), el('blockquote', citation.quote)); if (source) { li.append(link(source.title, source.url), el('p', `${source.source_name} · ${source.access} · ${source.published_at ? date(source.published_at) : 'publication date unknown'}`)); } list.append(li); }
    details.append(list); article.append(details);
    if (story.watch_source_id && evidence.has(story.watch_source_id)) { const p = el('p'); p.append(link('Watch at the source', evidence.get(story.watch_source_id).url), document.createTextNode(' — ' + story.watch_reason)); article.append(p); }
    const feedback = el('div', undefined, 'feedback');
    for (const [verdict, label] of [['useful', 'Useful'], ['not-relevant', 'Not for me'], ['already-knew', 'Already knew'], ['unsupported', 'Question the evidence'], ['go-deeper', 'Go deeper']]) { const button = el('button', label); button.addEventListener('click', async () => { try { await api('/api/feedback', {issue_id: issue.id, event_key: story.event_key, verdict}); tell('Feedback saved for the next briefing.'); } catch (e) { tell(e.message, true); } }); feedback.append(button); }
    article.append(feedback); box.append(article);
  }
  if (issue.content.low_priority.length) { const details = el('details'); details.append(el('summary', `Low priority · ${issue.content.low_priority.length} items`)); const list = el('ul', undefined, 'low-list'); for (const item of issue.content.low_priority) { const li = el('li'); const source = evidence.get(item.source_id); li.append(source ? link(item.title, source.url) : el('span', item.title), el('small', item.reason)); list.append(li); } details.append(list); box.append(details); }
  box.append(el('p', issue.verification + ' ' + issue.selection_note, 'verification'));
  renderCoverage(issue.coverage, issue.collected_at);
}
function renderSources() {
  const box = $('source-list'); box.replaceChildren();
  for (const source of state.config.sources) {
    const row = el('div', undefined, 'source-row'); const check = el('input'); check.type = 'checkbox'; check.checked = source.enabled; check.setAttribute('aria-label', `Enable ${source.name}`);
    check.addEventListener('change', async () => { const config = structuredClone(state.config); config.sources.find(x => x.id === source.id).enabled = check.checked; await save(config); });
    const text = el('div'); text.append(el('strong', source.name)); const sub = el('p'); sub.append(document.createTextNode(source.platform + ' · '), link(source.url, source.url)); text.append(sub);
    const remove = el('button', 'Remove'); remove.addEventListener('click', async () => { const config = structuredClone(state.config); config.sources = config.sources.filter(x => x.id !== source.id); await save(config); });
    row.append(check, text, remove); box.append(row);
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
  if (settings) { renderSettings(); renderSources(); }
  renderIssue();
  busy = state.job.running;
  for (const id of ['generate', 'collect', 'write']) $(id).disabled = busy;
  $('run-status').textContent = state.job.stage + (state.job.error ? ': ' + state.job.error : '');
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
