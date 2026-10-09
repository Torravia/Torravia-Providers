# Contributing

Submit new providers and updates by pull request. Follow the README's catalog
format and versioned directory convention. Keep released version folders unchanged.
Include the provider's license, deterministic saved-response tests, and documented
network timeout/rate-limit behavior. Do not add credentials or personal data.

Catalog checks do not execute submissions. Maintainers must inspect the code and
its tests before running it locally. Do not introduce shell commands, package
installation, daemons, or subprocesses into providers. Use the Python standard library.

Do not duplicate Academic Torrents here; it is maintained in the client. Keep host
runtime/UI changes in the client repository. Providers removed from the catalog
no longer appear in Settings; retain their historical version folders for auditability.
