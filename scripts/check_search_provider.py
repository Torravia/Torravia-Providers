#!/usr/bin/env python3
"""Validate and deliberately execute a trusted Torravia v1 search provider."""
import argparse
import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import sys
import time
from urllib.parse import parse_qs, urlparse

PREFIX = "# torravia-provider: "


def check_metadata(data):
    if len(data) > 512 * 1024:
        raise ValueError("Script exceeds 512 KiB")
    header = next((line for line in data.decode("utf-8").splitlines()[:32] if line.startswith(PREFIX)), None)
    if header is None:
        raise ValueError("Missing metadata comment in the first 32 lines")
    m = json.loads(header[len(PREFIX):])
    if type(m.get("apiVersion")) is not int or m["apiVersion"] != 1:
        raise ValueError("Unsupported apiVersion")
    identifier = m.get("id", "")
    if not isinstance(identifier, str) or not re.fullmatch(r"[a-z][a-z0-9.-]{2,79}", identifier) or ".." in identifier or identifier == "academictorrents":
        raise ValueError("Invalid provider ID")
    for field in ("name", "version", "author", "description"):
        v = m.get(field)
        if not isinstance(v, str) or not v.strip() or len(v) > 240 or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in v):
            raise ValueError(f"Invalid {field}")
    homepage = urlparse(m.get("homepage", ""))
    if homepage.scheme != "https" or not homepage.hostname or homepage.username or homepage.password:
        raise ValueError("Homepage must be HTTPS without credentials")
    return m


def check_result(row):
    title, magnet = row.get("title"), row.get("magnetLink")
    if not isinstance(title, str) or not title.strip() or len(title) > 2048:
        raise ValueError("Invalid result title")
    if not isinstance(magnet, str) or len(magnet) > 32768 or urlparse(magnet).scheme != "magnet":
        raise ValueError("Invalid result magnet")
    hashes = parse_qs(urlparse(magnet).query).get("xt", [])
    if not any(re.fullmatch(r"urn:btih:(?:[0-9a-f]{40}|[a-z2-7]{32})|urn:btmh:1220[0-9a-f]{64}", h, re.I) for h in hashes):
        raise ValueError("Missing valid torrent identity")
    for field, minimum in (("sizeBytes", 0), ("seeders", -1), ("leechers", -1)):
        value = row.get(field)
        if value is not None and (type(value) is not int or value < minimum or value > 9223372036854775807):
            raise ValueError(f"Invalid {field}")
    if row.get("sourceURL") is not None:
        source = urlparse(row["sourceURL"])
        if source.scheme not in ("http", "https") or not source.hostname:
            raise ValueError("Invalid sourceURL")


def execute(path, query, timeout):
    process = subprocess.Popen([sys.executable, "-I", "-u", str(path), "--query", query],
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               cwd=path.parent, env={"PATH": "/usr/bin:/bin", "LANG": "en_US.UTF-8"}, start_new_session=True)
    output, diagnostics = bytearray(), bytearray()
    deadline = time.monotonic() + timeout
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ, True)
            selector.register(process.stderr, selectors.EVENT_READ, False)
            while selector.get_map():
                if time.monotonic() >= deadline:
                    raise ValueError("Provider timed out")
                for key, _ in selector.select(min(0.1, max(0, deadline - time.monotonic()))):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                    elif key.data:
                        output.extend(chunk)
                        if len(output) > 4 * 1024 * 1024:
                            raise ValueError("Stdout exceeds 4 MiB")
                    else:
                        diagnostics.extend(chunk[:max(0, 16384 - len(diagnostics))])
        process.wait(timeout=max(0.01, deadline - time.monotonic()))
        if process.returncode:
            raise ValueError(f"Exit status {process.returncode}: {diagnostics.decode('utf-8', errors='replace')[:2048]}")
        lines = [line for line in output.decode("utf-8").splitlines() if line.strip()]
        if len(lines) > 500:
            raise ValueError("More than 500 results")
        for index, line in enumerate(lines, 1):
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError("Expected an object")
                check_result(row)
            except (ValueError, TypeError) as error:
                raise ValueError(f"Result {index}: {error}") from error
        return len(lines)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        process.stdout.close()
        process.stderr.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider", type=Path)
    parser.add_argument("--query", default="ocean")
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()
    try:
        path = args.provider.resolve(strict=True)
        with path.open("rb") as handle:
            metadata = check_metadata(handle.read(512 * 1024 + 1))
        print(f"Executing trusted provider: {metadata['name']} {metadata['version']}", flush=True)
        count = execute(path, args.query, args.timeout)
        print(f"Valid provider response: {count} result(s)")
    except (OSError, ValueError, TypeError, subprocess.TimeoutExpired) as error:
        print(f"Provider check failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
