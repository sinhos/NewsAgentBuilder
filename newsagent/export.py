"""Portable, readable exports from an edition's immutable evidence snapshot."""
import html
import re
from urllib.parse import quote, urlsplit


def text(value):
    value = html.escape(' '.join(str(value).split()), quote=False)
    return re.sub(r'([\\`*_{}\[\]()#+!|~])', r'\\\1', value)


def link(label, url):
    if urlsplit(url).scheme not in ('http', 'https'):
        return text(label)
    encoded = quote(url, safe=":/?#[]@!$&'*,;=%+")
    return f'[{text(label)}](<{encoded}>)'


def markdown(issue):
    content = issue['content']
    evidence = {entry['id']: entry for entry in issue['evidence']}
    lines = [f"# {text(content['title'])}", '',
             f"Collected: {text(issue['collected_at'])} · Up to {issue['reading_minutes']} min including context", '',
             text(content['overview']), '']
    for index, story in enumerate(content['stories'], 1):
        lines += [f"## {index}. {text(story['title'])}", '', f"Priority: {text(story['importance'])}", '']
        for key, label in [('what_changed','What changed'), ('why_it_matters','Why it matters'),
                           ('next_step','Takeaway'), ('limitations','Caveat'), ('durability','What lasts')]:
            lines += [f'**{label}.** {text(story[key])}', '']
        lines += ['### Evidence', '']
        for citation in story['evidence']:
            source = evidence[citation['source_id']]
            lines += [text(citation['claim']), '', '> ' + text(citation['quote']), '',
                      link(source['title'], source['url']), '',
                      f"{text(source['access'])} · Published: {text(source['published_at'] or 'unknown')}", '']
        if story['watch_source_id'] in evidence:
            source = evidence[story['watch_source_id']]
            lines += [link('Watch the source', source['url']) + ' — ' + text(story['watch_reason']), '']
    if content['low_priority']:
        lines += ['## Low priority', '']
        for brief in content['low_priority']:
            source = evidence[brief['source_id']]
            lines += [f"- {link(brief['title'], source['url'])} — {text(brief['reason'])}"]
        lines.append('')
    lines += ['## Coverage and verification', '', text(issue['verification']), '', text(issue['selection_note']), '']
    for row in issue['coverage']:
        lines += [f"- {text(row['name'])} ({text(row['platform'])}): **{text(row['status'])}** — {text(row['detail'])}"]
    lines += ['', f"Edition: {text(issue['id'])}", '']
    return '\n'.join(lines)
