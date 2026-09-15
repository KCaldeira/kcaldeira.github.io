#!/usr/bin/env python3
"""Check every outbound link and image in the built site, and write a report.

Produces DEAD-LINKS.md: a human-ordered worklist of what is broken, which post
it is in, and what can actually be done about each item. Results are cached in
tools/.cache/link-audit.json so re-runs only re-check what is new or was
previously failing.
"""
import concurrent.futures as cf
import html
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
CACHE = ROOT / "tools" / ".cache" / "link-audit.json"
REPORT = ROOT / "DEAD-LINKS.md"

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

# Status codes that mean "the server is there and answered, but refused an
# automated client". Publishers do this universally; it is not breakage.
# 403 dominates (Cloudflare/Akamai bot protection), plus rate limiting and
# paywalls. These need a human to click, not a fix.
REFUSED = {401, 402, 403, 406, 409, 429, 999}

# A domain that does not resolve at all is unambiguously gone -- no server,
# no parking page, nothing to retry.
DNS_DEAD = ("Name or service not known", "No address associated",
            "nodename nor servname", "Temporary failure in name resolution")


def collect():
    """url -> {posts it appears in, and whether it is an <img> source}"""
    found = defaultdict(lambda: {"pages": set(), "as_image": False})
    for page_file in sorted(SITE.rglob("*.html")):
        page = "/" + page_file.relative_to(SITE).parent.as_posix().lstrip(".")
        page = page.rstrip("/") + "/"
        text = page_file.read_text(errors="replace")
        for m in re.finditer(r'<img[^>]+src="(https?://[^"]+)"', text):
            e = found[html.unescape(m.group(1))]
            e["pages"].add(page)
            e["as_image"] = True
        for m in re.finditer(r'<a[^>]+href="(https?://[^"]+)"', text):
            found[html.unescape(m.group(1))]["pages"].add(page)
    return found


def probe(url):
    """HEAD, then GET on failure (many hosts reject HEAD with 405)."""
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, headers=UA, method=method)
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.status, ""
        except urllib.error.HTTPError as e:
            if method == "GET" or e.code not in (403, 405, 501):
                return e.code, ""
        except urllib.error.URLError as e:
            return 0, str(e.reason)[:80]
        except Exception as e:
            return 0, f"{type(e).__name__}: {str(e)[:60]}"
    return 0, "unreachable"


def main():
    if not SITE.exists():
        sys.exit("no _site/; run jekyll build first")
    found = collect()
    prev = json.loads(CACHE.read_text()) if CACHE.exists() else {}

    # Only re-probe what is new or was previously not-OK.
    todo = [u for u in found
            if u not in prev or not (200 <= (prev[u].get("status") or 0) < 400)]
    print(f"{len(found)} distinct remote URLs; probing {len(todo)}")

    results = dict(prev)
    if todo:
        with cf.ThreadPoolExecutor(max_workers=6) as ex:
            for i, (url, (status, err)) in enumerate(
                    zip(todo, ex.map(probe, todo)), 1):
                results[url] = {"status": status, "error": err}
                if i % 25 == 0:
                    print(f"  ...{i}/{len(todo)}", flush=True)

        suspect = [u for u in todo
                   if not (200 <= (results[u].get("status") or 0) < 400)]
        if suspect:
            print(f"confirming {len(suspect)} failure(s) serially "
                  f"(parallel probing provokes rate limiting)")
            for i, url in enumerate(suspect, 1):
                time.sleep(1.5)
                status, err = probe(url)
                if 200 <= status < 400:
                    print(f"  recovered on retry: {url}")
                results[url] = {"status": status, "error": err}
                if i % 10 == 0:
                    print(f"  ...{i}/{len(suspect)}", flush=True)
    CACHE.write_text(json.dumps(results, indent=1, sort_keys=True))

    host = lambda u: re.sub(r"^https?://([^/]+).*", r"\1", u)
    gone, refused, unclear = [], [], []
    for url, meta in sorted(found.items()):
        r = results.get(url, {})
        st = r.get("status") or 0
        err = r.get("error", "")
        if 200 <= st < 400:
            continue
        row = (url, st, err, sorted(meta["pages"]), meta["as_image"])
        if st == 404 or st == 410 or any(d in err for d in DNS_DEAD):
            gone.append(row)
        elif st in REFUSED:
            refused.append(row)
        else:
            unclear.append(row)

    known_missing = [l.strip() for l in
                     (ROOT / "tools" / "known-missing.txt").read_text().splitlines()
                     if l.strip() and not l.startswith("#")]

    def fmt(rows, show_pages=True):
        lines = []
        # images first: a broken image is visible on the page, a broken link is not
        for url, st, err, pages, as_img in sorted(rows, key=lambda r: (not r[4], r[0])):
            what = "IMAGE" if as_img else "link"
            why = f"HTTP {st}" if st else (err or "unreachable")
            lines.append(f"- **{why}** ({what}) `{url}`")
            if show_pages:
                for p in pages:
                    lines.append(f"  - {p}")
        return lines or ["None."]

    out = ["# Dead links and missing images", "",
           "Generated by `tools/audit_links.py` against the built site. "
           "Re-run after making fixes.", "",
           "Sections are ordered by how certain the problem is. Publishers "
           "routinely return 403 to non-browser clients, so an error code "
           "alone does not prove a link is broken -- only sections 1 and 2 "
           "are known-bad.", "",
           f"| | count |", "|---|---|",
           f"| Images that no longer exist anywhere | {len(known_missing)} |",
           f"| URLs confirmed gone (404 or domain does not resolve) | {len(gone)} |",
           f"| Needs a human look (timeout, 5xx, odd status) | {len(unclear)} |",
           f"| Refused automated requests, almost certainly fine | {len(refused)} |",
           f"| Total distinct outbound URLs checked | {len(found)} |",
           "", "---", "",
           "## 1. Images that no longer exist", "",
           "Absent from the WordPress media library, 404 on the old live site, "
           "and no Wayback snapshot -- already broken before the migration. "
           "Each needs a replacement image or removal of the reference.", ""]
    for p in known_missing:
        out.append(f"- `{p}`")

    out += ["", "## 2. Confirmed gone", "",
            "404, or the domain no longer resolves at all. Broken images here "
            "are visible holes in a post; links are silent.", ""]
    out += fmt(gone)

    out += ["", "## 3. Needs a human look", "",
            "Timeouts, 5xx and unusual statuses -- could be transient, could "
            "be real. Worth clicking.", ""]
    out += fmt(unclear)

    out += ["", "## 4. Refused automated requests (not broken)", "",
            "Publisher bot protection, paywalls and rate limits. These work "
            "in a browser; listed only so they are not mistaken for breakage.",
            ""]
    out += fmt(refused, show_pages=False)

    REPORT.write_text("\n".join(out) + "\n")
    print(f"\nwrote {REPORT.name}: {len(known_missing)} missing images, "
          f"{len(gone)} confirmed gone, {len(unclear)} need a look, "
          f"{len(refused)} refused-but-probably-fine")


if __name__ == "__main__":
    main()
