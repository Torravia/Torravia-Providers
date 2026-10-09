# Torravia community providers

A separate catalog for community search providers used by [Torravia](https://github.com/Torravia/Torravia).
Provider implementations and catalog contributions belong here, outside the client repository and its releases.

Academic Torrents remains built into Torravia and enabled by default. The initial
community catalog is empty; the development example in the interface documentation
is generated fixture data, not a published search provider.

## How users discover providers

Torravia reads `catalog.json` at startup and every six hours while running. The
existing **Settings → Search → Refresh** action requests it again immediately.
New catalog entries appear as disabled rows with the existing switches. Discovery
retrieves metadata only. Enabling an entry asks for approval, retrieves the code,
and verifies both its SHA-256 hash and metadata. There are no file or URL installation
controls. Python 3 is required only for community providers.

A changed implementation becomes disabled until the user enables and approves its
current version. Removed entries disappear. If the catalog is unavailable, Torravia
keeps its last valid cached catalog and approved versions. At least one source stays
enabled; Academic Torrents is the fallback.

## Contribute a provider

1. Read [the interface](docs/provider-interface.md), write a single UTF-8 Python
   script using standard-library dependencies, and include the required metadata header.
2. Add it at `providers/<id>/<version>/provider.py`. Include a license and saved-response
   tests in the provider folder. Version folders are immutable after publication;
   updates use a new version folder with the same stable provider ID.
3. Test trusted code with `python3 scripts/check_search_provider.py path/to/provider.py --query ocean`.
   This command intentionally executes the supplied script. Test empty matches,
   Unicode, network failure, malformed responses, and pagination too.
4. Compute `shasum -a 256 path/to/provider.py`. Add an entry to `catalog.json` with
   the exact header metadata, versioned raw HTTPS script URL, and resulting lowercase hash.
5. Run `python3 scripts/check_catalog.py`, then open a pull request in this repository.
   CI validates catalog metadata and hashes without executing providers. Maintainers
   review source, fixture tests, license, and published endpoints before merging.

Catalog shape (the example is not an actual catalog entry):

```json
{
  "schemaVersion": 1,
  "providers": [
    {
      "manifest": {
        "apiVersion": 1,
        "id": "org.example.research",
        "name": "Example Research",
        "version": "1.0.0",
        "author": "Your name",
        "description": "Search a research index.",
        "homepage": "https://example.org/"
      },
      "scriptURL": "https://raw.githubusercontent.com/Torravia/Torravia-Providers/main/providers/org.example.research/1.0.0/provider.py",
      "sha256": "<64 lowercase hexadecimal characters>"
    }
  ]
}
```

There can be at most 200 entries and the catalog must fit in 512 KiB. IDs and
case-insensitive display names must be unique; Academic Torrents is reserved.
Implementations must also fit in 512 KiB. The client accepts interface v1 only.
A changed hash or metadata requires renewed user approval, regardless of version text.

## Maintenance

This repository currently belongs to the Torravia organization; community contributions are welcome
through pull requests. Publication requires a maintainer merge. Community governance
and additional maintainers can be established separately; catalog publication does
not give contributors access to the Torravia client repository or its releases.

Reports about a provider belong here. Client UI, catalog loading, runner bugs, and
Academic Torrents changes belong in the [client repository](https://github.com/Torravia/Torravia).
