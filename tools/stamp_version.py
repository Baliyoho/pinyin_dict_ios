#!/usr/bin/env python3
"""Stamp sw.js with a hash of everything that affects what the app serves.

The service worker is cache-first, so a deploy only reaches phones that already
installed the app if the cache name changes. Run this before every deploy.

sw.js hashes itself with its VERSION line blanked out — otherwise stamping it
would change the hash that produced the stamp, and a change to the worker's own
logic would not bump the cache name at all.
"""
import hashlib
import re
from pathlib import Path

PUBLIC = Path(__file__).resolve().parent.parent / "public"
SW = PUBLIC / "sw.js"
VERSION_LINE = re.compile(rb'const VERSION = "[^"]*";')

assets = sorted(p for p in PUBLIC.rglob("*") if p.is_file())

digest = hashlib.sha256()
for path in assets:
    body = path.read_bytes()
    if path == SW:
        body = VERSION_LINE.sub(b'const VERSION = "";', body)
    digest.update(path.relative_to(PUBLIC).as_posix().encode())
    digest.update(body)
version = digest.hexdigest()[:12]

text = SW.read_text(encoding="utf-8")
updated, count = re.subn(r'const VERSION = "[^"]*";', f'const VERSION = "{version}";', text)
if count != 1:
    raise SystemExit("sw.js: expected exactly one VERSION line, found %d" % count)
SW.write_text(updated, encoding="utf-8")
print(f"sw.js VERSION = {version}  ({len(assets)} assets)")
