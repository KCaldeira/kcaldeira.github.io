#!/usr/bin/env python3
"""Verify the built _site against the WordPress snapshot.

Checks URL parity (every old permalink still resolves), that every image
reference resolves to a real file, and that the feed and sitemap are complete.
"""
import json
import pathlib
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
CACHE = ROOT / "tools" / ".cache"

fails = []


def check(cond, msg):
    if cond:
        print(f"  ok    {msg}")
    else:
        print(f"  FAIL  {msg}")
        fails.append(msg)


def main():
    if not SITE.exists():
        sys.exit("no _site/; run jekyll build first")
    posts = json.loads((CACHE / "posts.json").read_text())
    pages = json.loads((CACHE / "pages.json").read_text())

    print("URL parity (WordPress permalink -> built page):")
    missing = []
    for p in posts + pages:
        path = urllib.parse.urlparse(p["link"]).path          # /YYYY/MM/slug/
        if not (SITE / path.strip("/") / "index.html").exists():
            missing.append(path)
    check(not missing, f"all {len(posts) + len(pages)} WordPress URLs resolve")
    for m in missing[:10]:
        print(f"        missing: {m}")

    known_missing = {
        ln.strip() for ln in (ROOT / "tools" / "known-missing.txt").read_text().splitlines()
        if ln.strip() and not ln.startswith("#")
    }

    print("\nlocal asset references:")
    refs, broken = set(), []
    for html in SITE.rglob("*.html"):
        refs |= set(re.findall(r'(?:src|href)="(/assets/[^"]+)"',
                               html.read_text(errors="replace")))
    for r in sorted(refs):
        if not (SITE / r.lstrip("/")).exists():
            broken.append(r)
    unexpected = [b for b in broken if b not in known_missing]
    check(not unexpected,
          f"all {len(refs)} local asset references resolve "
          f"({len(broken)} known-missing allowed)")
    for b in unexpected:
        print(f"        broken: {b}")
    stale = sorted(known_missing - set(broken))
    if stale:
        print(f"        note: {len(stale)} known-missing entries are no longer "
              f"referenced and can be dropped from known-missing.txt")

    print("\nfeed and sitemap:")
    feed = SITE / "feed.xml"
    check(feed.exists(), "feed.xml exists")
    if feed.exists():
        n = len(ET.fromstring(feed.read_text())
                .findall("{http://www.w3.org/2005/Atom}entry"))
        limit = 30
        expected = min(limit, len(posts))
        check(n == expected, f"feed lists {expected} most recent posts (found {n})")
    sm = SITE / "sitemap.xml"
    check(sm.exists(), "sitemap.xml exists")
    if sm.exists():
        locs = [e.text for e in ET.fromstring(sm.read_text())
                .iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        check(len(locs) >= len(posts), f"sitemap lists {len(locs)} URLs")
        check(all(l.startswith("https://kencaldeira.com/") for l in locs),
              "sitemap URLs use the production domain")

    print("\nstructure:")
    check((SITE / "index.html").exists(), "home page exists")
    check((SITE / "about" / "index.html").exists(), "/about/ exists")
    check((SITE / "CNAME").exists() and
          (SITE / "CNAME").read_text().strip() == "kencaldeira.com",
          "CNAME is kencaldeira.com")
    home = (SITE / "index.html").read_text()
    # Count distinct post URLs, not anchor occurrences: the home page features
    # the newest post above the archive, so one post can legitimately be
    # linked more than once.
    linked = set(re.findall(r'<a href="(/\d{4}/\d{2}/[^"]+/)"', home))
    check(len(linked) == len(posts),
          f"home links all {len(posts)} distinct posts (found {len(linked)})")

    print("\nremote images still hot-linked (for the dead-link pass):")
    remote = set()
    for html in SITE.rglob("*.html"):
        remote |= set(re.findall(r'<img[^>]+src="(https?://[^"]+)"',
                                 html.read_text(errors="replace")))
    for r in sorted(remote):
        print(f"  remote  {r[:100]}")

    print()
    if fails:
        print(f"FAILED: {len(fails)} check(s)")
        sys.exit(1)
    print("all checks passed")


if __name__ == "__main__":
    main()
