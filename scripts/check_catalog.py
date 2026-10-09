#!/usr/bin/env python3
"""Validate the published catalog against local files without executing providers."""
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
from check_search_provider import check_metadata

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = 'https://raw.githubusercontent.com/DavidAGInnovation/Torravia-Providers/main/'


def validate(root=ROOT):
    data = (root / 'catalog.json').read_bytes()
    if len(data) > 512 * 1024:
        raise ValueError('Catalog exceeds 512 KiB')
    catalog = json.loads(data)
    if type(catalog.get('schemaVersion')) is not int or catalog['schemaVersion'] != 1:
        raise ValueError('Unsupported catalog schema')
    providers = catalog.get('providers')
    if not isinstance(providers, list) or len(providers) > 200:
        raise ValueError('Invalid provider list')
    ids, names = set(), set()
    for entry in providers:
        m = entry['manifest']
        check_metadata(('# torravia-provider: ' + json.dumps(m)).encode())
        identifier, name = m['id'], m['name'].strip().lower()
        if identifier in ids or name in names or name == 'academic torrents':
            raise ValueError('Duplicate or reserved provider identity')
        ids.add(identifier)
        names.add(name)
        version = m['version']
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}', version) or '..' in version:
            raise ValueError('Use a safe, versioned directory name')
        relative = f'providers/{identifier}/{version}/provider.py'
        if entry['scriptURL'] != RAW_ROOT + relative:
            raise ValueError(f'Expected versioned URL: {RAW_ROOT + relative}')
        file = (root / relative).resolve()
        if not file.is_relative_to(root.resolve()) or (root / relative).is_symlink():
            raise ValueError('Provider path escapes repository')
        script = file.read_bytes()
        if check_metadata(script) != m:
            raise ValueError('Script metadata differs from catalog')
        digest = entry['sha256']
        if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest) or hashlib.sha256(script).hexdigest() != digest:
            raise ValueError('Provider SHA-256 mismatch')
        licenses = list(file.parent.glob('LICENSE*'))
        if not licenses:
            raise ValueError(f'Include a license alongside {relative}')
    return len(providers)


if __name__ == '__main__':
    try:
        print(f'Catalog valid: {validate()} community providers (no code executed).')
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f'Catalog invalid: {error}', file=sys.stderr)
        sys.exit(1)
