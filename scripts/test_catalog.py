#!/usr/bin/env python3
"""Regression checks for catalog publication; no provider code runs."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from check_catalog import RAW_ROOT, validate


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = dict(apiVersion=1, id='org.example.fixture', name='Fixture', version='1.0.0',
                             author='Tests', description='Generated data', homepage='https://example.org/')
        self.relative = 'providers/org.example.fixture/1.0.0/provider.py'
        file = self.root / self.relative
        file.parent.mkdir(parents=True)
        self.script = ('# torravia-provider: ' + json.dumps(self.manifest) + '\nraise RuntimeError("Must never execute")\n').encode()
        file.write_bytes(self.script)
        (file.parent / 'LICENSE').write_text('Test fixture license')
        self.entry = dict(manifest=self.manifest, scriptURL=RAW_ROOT + self.relative, sha256=hashlib.sha256(self.script).hexdigest())

    def write(self, entries):
        (self.root / 'catalog.json').write_text(json.dumps(dict(schemaVersion=1, providers=entries)))

    def test_empty_and_valid_catalog(self):
        self.write([])
        self.assertEqual(validate(self.root), 0)
        self.write([self.entry])
        self.assertEqual(validate(self.root), 1)

    def test_bad_hash_and_duplicate_are_rejected(self):
        bad = copy.deepcopy(self.entry)
        bad['sha256'] = '0' * 64
        self.write([bad])
        with self.assertRaises(ValueError): validate(self.root)
        self.write([self.entry, self.entry])
        with self.assertRaises(ValueError): validate(self.root)

    def test_metadata_and_url_must_match_published_file(self):
        bad = copy.deepcopy(self.entry)
        bad['manifest']['name'] = 'Changed'
        self.write([bad])
        with self.assertRaises(ValueError): validate(self.root)
        bad = copy.deepcopy(self.entry)
        bad['scriptURL'] = 'https://example.org/latest.py'
        self.write([bad])
        with self.assertRaises(ValueError): validate(self.root)

    def test_reserved_identity_and_path_escape(self):
        for key, value in [('name', 'Academic Torrents'), ('id', '../escape'), ('version', '../escape')]:
            bad = copy.deepcopy(self.entry)
            bad['manifest'][key] = value
            self.write([bad])
            with self.assertRaises(ValueError): validate(self.root)


if __name__ == '__main__':
    unittest.main()
