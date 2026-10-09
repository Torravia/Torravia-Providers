# Torravia provider interface v1

Providers require external Python 3 and use only the standard library. They are
not compatible with qBittorrent plugins. This repository does not bundle Python.

## Author a provider

A provider is one UTF-8 `.py` file, at most 512 KiB. In its first 32 lines include a
single-line JSON metadata comment with the exact prefix `# torravia-provider: `:

```python
# torravia-provider: {"apiVersion":1,"id":"org.example.research","name":"Example Research","version":"1.0.0","author":"Your name","description":"Search a research index.","homepage":"https://example.org/"}
```

Use a stable reverse-domain-style ID, starting with a lowercase letter, 3–80 ASCII
characters from `a-z`, `0-9`, `.` and `-`. Paths, consecutive dots, and the reserved
ID `academictorrents` are rejected. All text fields are required, nonempty, free of
control characters, and at most 240 characters. The homepage must use HTTPS and
contain no username or password. Version is an author-provided display string;
`apiVersion` determines compatibility.

Torravia starts a new process for every search:

```text
python3 -I -u /cached/provider.py --query "the user's query"
```

Arguments are passed directly without a shell. `-I` isolates Python's import paths
and environment configuration; it does not sandbox the script. Stdin is closed.
Only PATH and LANG are supplied in the child environment. Avoid local module
imports and external dependencies. Scripts should apply network timeouts, respect
rate limits, and exit when terminated.

Print one JSON object per line to **stdout**:

```json
{"title":"Ocean observations","magnetLink":"magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567","sizeBytes":4096,"seeders":8,"leechers":0,"sourceURL":"https://example.org/dataset/123"}
```

`title` and a valid `magnetLink` are required. `sizeBytes` defaults to zero (unknown),
and must be nonnegative. `seeders` and `leechers` default to -1 (unknown) and must be
at least -1. Optional `sourceURL` must be HTTP or HTTPS. The displayed provider name
comes from catalog metadata, not from returned results. Titles are limited
to 2,048 characters and magnets to 32,768. Invalid lines fail the provider search.
Resolve `.torrent` links to valid magnets within the provider; raw torrent download
URLs are not accepted as results in version 1.

Use **stderr** for diagnostics. Exit zero with no output for a successful search
with no results; exit nonzero for errors. Maximum stdout is 4 MiB and 500 result
lines. Stderr diagnostics are truncated. The runner has a 30-second upper bound;
the selected search mode may impose a shorter timeout. Cancellation terminates
the process, escalating to SIGKILL if necessary. Do not launch subprocesses or
daemons: process-tree management is not part of this interface.

Results enter Torravia's existing title matching, duplicate merging, tracker
availability checks, sorting, and download queue. A failure in one provider does
not prevent another provider's successful results from appearing.

Enabled external providers can run availability searches with the query
`healthcheck`. Empty results are valid. Disabled providers do not run during
background availability checks. Catalog discovery and activation do not execute provider code. The managed approval record stores a SHA-256
fingerprint; files changed outside installation are rejected, including on restart.
This detects edits, not malicious code approved by a user.

## Minimal development example

This example emits generated fixture data and contacts no actual index. Replace
its search logic with your site's documented API or parser. It is documentation,
not a provider bundled into the app.

```python
# torravia-provider: {"apiVersion":1,"id":"org.example.research","name":"Example Research","version":"1.0.0","author":"Your name","description":"Generated development fixture.","homepage":"https://example.org/"}
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("--query", required=True)
query = parser.parse_args().query

if "ocean" in query.lower():
    print(json.dumps({
        "title": "Ocean observations fixture",
        "magnetLink": "magnet:?xt=urn:btih:0123456789abcdef0123456789abcdef01234567",
        "sizeBytes": 4096,
        "sourceURL": "https://example.org/dataset/123",
    }))
```

Run `python3 scripts/check_search_provider.py /path/to/provider.py --query ocean`.
This tool deliberately executes the supplied provider; use it only with code you
trust. It checks metadata, exit status, output limits, JSON fields, and magnets.
Test empty matches, Unicode queries, network errors, pagination, and malformed
responses in your own repository using saved response fixtures. Then test through a development catalog before submitting a pull request. See the repository README for publishing instructions.

