import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from newsagent.core import ROOT, Store, validate_config
from newsagent.editorial import prompt
from newsagent.setup import check_setup


class BuilderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / 'first')
        self.store.init()

    def tearDown(self):
        self.temp.cleanup()

    def test_fresh_profile_is_generic_and_init_preserves_existing_settings(self):
        config = self.store.config()
        self.assertEqual(config['profile']['description'], '')
        self.assertEqual(config['sources'], [])
        config['profile']['description'] = 'An architect in Milan'
        self.store.save_config(config)
        self.store.init()
        self.assertEqual(self.store.config(), config)
        with self.assertRaisesRegex(ValueError, 'already exist'):
            self.store.init(ROOT / 'config/examples/engineering-creators.json')
        self.assertEqual(self.store.config(), config)

    def test_export_import_roundtrip_excludes_private_data_and_wont_overwrite(self):
        path = Path(self.temp.name) / 'newsletter.json'
        (self.store.home / 'packet.json').write_text('{"private": "never export this"}')
        with patch.dict('os.environ', {'NEWSAGENT_API_KEY': 'test-secret-not-for-export'}):
            self.store.export_config(path)
        content = path.read_text()
        self.assertNotIn('never export this', content)
        self.assertNotIn('test-secret-not-for-export', content)
        imported = Store(Path(self.temp.name) / 'second')
        imported.init(path)
        self.assertEqual(imported.config(), self.store.config())
        self.assertEqual(imported.history(), [])
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.store.export_config(path)
        self.assertEqual(path.read_text(), content)

    def test_invalid_import_never_creates_settings(self):
        path = Path(self.temp.name) / 'bad.json'
        config = self.store.config()
        config['provider']['backend'] = 'unrecognized'
        path.write_text(json.dumps(config))
        imported = Store(Path(self.temp.name) / 'second')
        with self.assertRaises(ValueError):
            imported.init(path)
        self.assertFalse(imported.config_path.exists())

    def test_optional_example_is_valid_and_social_sources_are_opt_in(self):
        config = validate_config(json.loads((ROOT / 'config/examples/engineering-creators.json').read_text()))
        self.assertTrue(any(s['enabled'] for s in config['sources']))
        self.assertTrue(all(not s['enabled'] for s in config['sources'] if s['platform'] != 'youtube'))

    def test_diagnostics_do_not_call_models_or_expose_secrets(self):
        config = self.store.config()
        config['sources'] = [{'id':'feed', 'name':'Example', 'platform':'rss', 'url':'https://example.org/feed', 'enabled':True}]
        with patch('newsagent.setup.shutil.which', return_value=None), patch('newsagent.models.generate') as generate:
            checks = check_setup(config)
        generate.assert_not_called()
        self.assertEqual(next(c['status'] for c in checks if c['name'] == 'Codex CLI'), 'missing')
        config['provider'] = {'backend':'compatible', 'base_url':'https://example.org/v1', 'model':'example', 'key_env':'TEST_NEWS_KEY'}
        with patch.dict('os.environ', {'TEST_NEWS_KEY':'never-return-the-value'}):
            checks = check_setup(config)
        self.assertNotIn('never-return-the-value', json.dumps(checks))
        self.assertEqual(next(c['status'] for c in checks if c['name'] == 'API key'), 'found')

    def test_provider_validation_catches_errors_before_save(self):
        base = self.store.config()
        for provider in [
            {'backend':'ollama', 'base_url':'https://example.org', 'model':'local', 'key_env':'NEWSAGENT_API_KEY'},
            {'backend':'compatible', 'base_url':'https://example.org?key=secret', 'model':'model', 'key_env':'NEWSAGENT_API_KEY'},
            {'backend':'ollama', 'base_url':'http://localhost:11434', 'model':'', 'key_env':'NEWSAGENT_API_KEY'},
        ]:
            config = copy.deepcopy(base)
            config['provider'] = provider
            with self.assertRaises(ValueError):
                self.store.save_config(config)
            self.assertEqual(self.store.config(), base)

    def test_editorial_prompt_uses_the_readers_profile(self):
        packet = {'profile': {**self.store.config()['profile'], 'description':'Architect', 'interests':'Urban planning'},
                  'window_start':'2026-09-22', 'collected_at':'2026-09-22', 'items':[], 'coverage':[]}
        text = prompt(packet)
        self.assertIn('Urban planning', text)
        self.assertNotIn('Priorities: profile-specific durable CS skills', text)


if __name__ == '__main__':
    unittest.main()
