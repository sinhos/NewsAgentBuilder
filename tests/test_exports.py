import json
from pathlib import Path
import tempfile
import unittest

from newsagent.core import Store, write_json
from newsagent.export import markdown
from test_workflow import fixture


class BriefingExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.store.init()
        self.packet, self.draft = fixture(self.store)
        self.saved = self.store.publish(self.draft)

    def tearDown(self):
        self.temp.cleanup()

    def test_readable_export_preserves_original_evidence_and_limits(self):
        write_json(self.store.home / 'packet.json', {**self.packet, 'items': []})
        output = Path(self.temp.name) / 'export' / 'briefing.md'
        self.store.export_issue(output, self.saved['id'])
        document = output.read_text()
        for field in ('what_changed', 'why_it_matters', 'limitations', 'next_step', 'durability'):
            self.assertIn(self.draft['stories'][0][field], document)
        self.assertIn('https://example.org/release', document)
        self.assertIn('The new release adds a local test runner', document)
        self.assertIn(self.saved['verification'], document)
        self.assertEqual(self.store.issue()['id'], self.saved['id'])
        with self.assertRaises(ValueError):
            self.store.export_issue(output)
        self.assertEqual(output.read_text(), document)

    def test_missing_edition_cannot_create_an_export(self):
        destination = Path(self.temp.name) / 'missing.md'
        with self.assertRaisesRegex(ValueError, 'not found'):
            self.store.export_issue(destination, 'unknown')
        self.assertFalse(destination.exists())

    def test_export_escapes_markup_and_retains_low_priority_and_coverage(self):
        saved = json.loads(json.dumps(self.saved))
        saved['content']['title'] = '<script>alert(1)</script> [misleading](javascript:alert(1))'
        saved['content']['low_priority'] = [{'source_id':self.packet['items'][0]['id'], 'title':'A side note', 'reason':'Not relevant today.'}]
        saved['coverage'] = [{'name':'Example', 'platform':'rss', 'status':'unavailable', 'detail':'Access failed'}]
        result = markdown(saved)
        self.assertNotIn('<script>', result)
        self.assertNotIn('[misleading](javascript:', result)
        self.assertIn('## Low priority', result)
        self.assertIn('**unavailable**', result)
        self.assertIn('Access failed', result)

    def test_old_edition_can_be_exported_outside_reader_archive_limit(self):
        with self.store.db() as db:
            for index in range(31):
                clone = {**self.saved, 'id':f'newer-{index}', 'created_at':f'2099-01-{index + 1:02d}'}
                db.execute('INSERT INTO issues VALUES(?,?,?)', (clone['id'], clone['created_at'], json.dumps(clone)))
        self.assertNotIn(self.saved['id'], [i['id'] for i in self.store.history()])
        self.assertEqual(self.store.issue(self.saved['id'])['content'], self.saved['content'])
