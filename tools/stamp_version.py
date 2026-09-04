#!/usr/bin/env python3
"""Stamp sw.js with a hash of everything it precaches.

The service worker is cache-first, so a deploy only reaches phones that already
installed the app if the cache name changes. Run this before every deploy.
"""
import hashlib
import re
from pathlib import Path

PUBLIC = Path(__file__).resolve().parent.parent / "public"
SW = PUBLIC / "sw.js"

assets = sorted(
    p for p in PUBLIC.rglob("*")
    if p.is_file() and p != SW and p.suffix in {".html", ".css", ".js", ".json", ".txt", ".png", ".webmanifest"}
)

digest = hashlib.sha256()
for path in assets:
    digest.update(path.relative_to(PUBLIC).as_posix().encode())
    digest.update(path.read_bytes())
version = digest.hexdigest()[:12]

text = SW.read_text(encoding="utf-8")
updated, count = re.subn(r'const VERSION = "[^"]*";', f'const VERSION = "{version}";', text)
if count != 1:
    raise SystemExit("sw.js: expected exactly one VERSION line, found %d" % count)
SW.write_text(updated, encoding="utf-8")
print(f"sw.js VERSION = {version}  ({len(assets)} assets)")
