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

Dead-link pass, deferred until the site is live: the 6 unrecoverable images,
5 hot-linked images already returning 403/404 (PNAS, Science, 2× Twitter,
Carnegie), 1 Gmail-attachment image URL that only renders for Ken, inline
Twitter links (account no longer used), and WordPress's old `/feed/` path,
which is now `/feed.xml`.
