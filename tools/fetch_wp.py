#!/usr/bin/env python3
"""Fetch all content from the kencaldeira.com WordPress REST API.

Writes raw JSON snapshots to tools/.cache/ as a provenance record, so the
migration stays reproducible after the WordPress site is switched off.
Idempotent: existing snapshots are reused unless --refresh is given.
"""
import json
import pathlib
import sys
import urllib.error
import urllib.request

SITE = "https://kencaldeira.com"
API = SITE + "/wp-json/wp/v2"
CACHE = pathlib.Path(__file__).parent / ".cache"

POST_FIELDS = "id,date,date_gmt,modified,slug,link,title,content,excerpt,featured_media,status"
ENDPOINTS = {
    "posts": f"{API}/posts?per_page=100&_fields={POST_FIELDS}",
    "pages": f"{API}/pages?per_page=100&_fields={POST_FIELDS}",
    "media": f"{API}/media?per_page=100&_fields=id,date,slug,source_url,mime_type,alt_text,media_details",
}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "kencaldeira-migration/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        # Return the headers object, not dict(): HTTP/2 lowercases header
        # names and only this object looks them up case-insensitively.
        return json.loads(r.read().decode("utf-8")), r.headers


def fetch_all(url):
    """Follow WordPress pagination until every page is retrieved."""
    items, page = [], 1
    while True:
        data, hdrs = get(f"{url}&page={page}")
        if not data:
            break
        items.extend(data)
        total_pages = int(hdrs.get("X-WP-TotalPages") or 1)
        # The API reports TotalPages relative to per_page=1 on some hosts;
        # trust the item count instead and stop on a short page.
        if len(data) < 100 or page >= max(total_pages, 1):
            break
        page += 1
    return items


def main():
    refresh = "--refresh" in sys.argv
    CACHE.mkdir(exist_ok=True)
    for name, url in ENDPOINTS.items():
        out = CACHE / f"{name}.json"
        if out.exists() and not refresh:
            n = len(json.loads(out.read_text()))
            print(f"{name}: cached, {n} items (use --refresh to re-fetch)")
            continue
        items = fetch_all(url)
        out.write_text(json.dumps(items, indent=1, ensure_ascii=False))
        print(f"{name}: fetched {len(items)} items -> {out.relative_to(CACHE.parent.parent)}")


if __name__ == "__main__":
    main()
