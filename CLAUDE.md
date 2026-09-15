# kencaldeira.com — static site

Jekyll site on GitHub Pages, migrated from WordPress. 72 posts (2015–2025) plus
an About page. Served at `kencaldeira.com` via the `CNAME` file; DNS is managed
at GoDaddy.

## Git

**Ken commits and pushes himself, unless he specifically requests otherwise.**
By default, do not run `git commit`, `git push`, or `gh` commands that write to
the remote: make the file changes, report what changed, and leave the
committing to him. When he does ask for a commit or push, go ahead and do it.

## `_posts/` is the source of truth — edit it directly

The WordPress migration is **done** and will not be re-run. Edit the Markdown in
`_posts/` and `about.md` normally.

`tools/convert.py` performed the one-time import and would overwrite everything
from the 2026 WordPress snapshot, so it now **refuses to run without `--force`**.
It is kept only as provenance: together with the committed snapshot in
`tools/.cache/`, it documents exactly how each post was derived. Same for
`tools/title-overrides.tsv` and `tools/link-replacements.tsv` — a record of what
was corrected during the migration, not live configuration. Their contents are
already baked into `_posts/`.

## Pipeline

```
tools/fetch_wp.py            # WordPress REST API -> tools/.cache/*.json (committed, provenance)
tools/images.py download     # full-res originals -> originals/ (gitignored)
tools/images.py optimize     # web assets -> assets/images/, writes .cache/asset-map.json
tools/images.py prune        # drop assets no longer referenced by _posts/
tools/convert.py             # snapshot -> _posts/*.md + pages
tools/verify.py              # check the built _site/ (run after jekyll build)
```

Order matters: `optimize` re-encodes photographic PNGs as JPEG and records the
extension changes in `asset-map.json`, which `convert.py` then applies to image
paths. So run `optimize` **before** `convert.py`.

Use the project venv: `.venv/bin/python tools/…` (Pillow is installed there).

## Building locally

No bundler, and Jekyll needs two workarounds on this machine:

```bash
export GEM_HOME="$PWD/vendor/gems" PATH="$PWD/vendor/gems/bin:$PATH"
export JEKYLL_NO_BUNDLER_REQUIRE=true   # else it tries to resolve the Gemfile's github-pages gem
jekyll build && .venv/bin/python tools/verify.py
```

`vendor/gems` holds a local Jekyll plus a **stub `em-websocket` gem**: real
Jekyll wants it for `serve --livereload`, it needs native extensions, and
there is no `ruby-dev` and no sudo here. `jekyll build` never loads it.
`jekyll serve` will not work — preview with a static server instead:

```bash
cd _site && python3 -m http.server 8080
```

Node here is v18; headless-browser tooling needs v20+, so visual checks are
Ken's to make in a browser.

## Site conventions

- **Links to other domains open in a new tab.** Handled centrally by
  `_includes/external-links.html`, pulled in by `_layouts/default.html`, which
  adds `target="_blank"` and `rel="noopener noreferrer"` to any link whose
  hostname differs from the site's. Do not annotate links individually, and do
  not reach for `jekyll-target-blank` — it is not on the GitHub Pages plugin
  allowlist. Internal links, `mailto:` and `#fragment` links are left alone.

## Invariants worth not breaking

- `permalink: /:year/:month/:title/` in `_config.yml` reproduces the WordPress
  URLs exactly. Changing it breaks every inbound link and search result.
  `tools/verify.py` asserts parity against the snapshot.
- `tools/known-missing.txt` lists 6 images that exist nowhere (absent from the
  media library, 404 live, no Wayback snapshot). `verify.py` allows exactly
  those and fails on any new broken reference.
- Inline text colour carries meaning in 7 posts (it marks quoted email and
  external material). It maps to `.tc-*` classes with light/dark tokens in
  `assets/css/main.css` — do not flatten it to plain text.

## Outstanding

State as of 15 Sep 2026. The site is **live** at `https://kencaldeira.com` with a
valid certificate and Enforce HTTPS on. Everything below is follow-up.

### Two GoDaddy changes Ken needs to make (Claude cannot)

1. **`www` over HTTPS is broken.** The certificate covers only
   `kencaldeira.com` (`SAN: DNS:kencaldeira.com`), so `https://www.kencaldeira.com`
   fails TLS. `http://www...` is fine — it 301s to the apex. Cause: the `www`
   CNAME points at `kencaldeira.com`; GitHub only adds `www` to the cert when it
   points at `kcaldeira.github.io`.
   → In GoDaddy DNS for **kencaldeira.com**, edit the `www` CNAME:
   `kencaldeira.com` → `kcaldeira.github.io` (TTL is 1 hour, so allow for that).
   → Then re-trigger issuance: `gh api -X PUT repos/KCaldeira/kcaldeira.github.io/pages -f cname=`
   followed by the same call with `-f cname=kencaldeira.com`. A same-value PUT is
   *not* enough — the domain has to be removed and re-added. Confirm with
   `openssl s_client -connect kencaldeira.com:443 -servername kencaldeira.com | openssl x509 -noout -ext subjectAltName`
   and expect both names.

2. **`kencaldeira.org` still forwards to the stale mirror.** It 301s to
   `https://kencaldeira.wordpress.com`, a WordPress.com copy of this blog whose
   newest post is March 2025 (it is missing the Nov 2025 Chopin post).
   → GoDaddy → kencaldeira.org → **DNS tab, bottom of the page → Forwarding**
   (not the DNS records table: the apex `A` records `15.197.225.128` /
   `3.33.251.168` are GoDaddy's forwarding servers and are locked). Set
   destination `https://kencaldeira.com`, **301 permanent, forward only, no
   masking**. The DNS records will look unchanged afterwards — verify by
   following the redirect, not by reading the zone.

**Never touch** on either domain: the `MX` records (`smtp.secureserver.net`,
`mailstore1.secureserver.net`) or the mail CNAMEs — that is live email. Nor the
NS records, nor the four apex `A` records on `.com`.

### Retire the old hosting

The old site was **GoDaddy Managed WordPress** (IP `160.153.0.83`,
`host.secureserver.net`). Turn off auto-renew on the Managed WordPress plan and
any SSL / site-security add-on — GitHub supplies the certificate now.
**Keep** the domain registrations, GoDaddy DNS, and the email product.
`Account Settings → Renewals & Billing` lists every product in one place.
There is also a GoDaddy "Website" product attached to `kencaldeira.org` worth
checking. Prefer switching auto-renew off over cancelling immediately: the paid
term then preserves the rollback option, which is restoring the apex `A` record
to `160.153.0.83`.

Once `.org` is repointed, `kencaldeira.wordpress.com` has no inbound path from
either domain but stays publicly indexed, competing with the real site. Deleting
or privatising it is the natural last step; the 14 images rescued from
`kencaldeira.files.wordpress.com` are now hosted locally, so nothing depends on it.

### Dead-link pass

See `DEAD-LINKS.md` (regenerate with `.venv/bin/python tools/audit_links.py`
after a build). Of 310 outbound URLs: **24 confirmed gone**, 13 worth a human
look, and 62 that merely refuse automated requests and are fine in a browser —
do not "fix" those. Plus the 6 images in `tools/known-missing.txt`; note that
**4 of those 6 were screenshots of Ken's own tweets**, and he no longer uses
Twitter, so deleting those figures and keeping the surrounding text is probably
the right call. Also still open: inline Twitter links, and WordPress's old
`/feed/` path (now `/feed.xml`) which would need `jekyll-redirect-from` to keep
working for existing subscribers.

### CIunit split

`CIUNIT-HANDOFF.md` is ready to hand to whoever works on `ciunit.github.io`.
Regenerate with `.venv/bin/python tools/ciunit_handoff.py` after editing the
judgment calls in `tools/post-classification.tsv`. **If a post moves, leave a
redirect** — every post URL has been indexed since as early as 2015.
