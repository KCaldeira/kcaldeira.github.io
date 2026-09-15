#!/usr/bin/env python3
"""Convert the WordPress JSON snapshot into Jekyll Markdown.

HISTORICAL. This ran the one-time migration off WordPress. `_posts/` is now
the hand-maintained source of truth, so this script refuses to run without
--force: re-running it would overwrite real edits with the 2026 snapshot.
Kept for provenance -- it documents exactly how the posts were derived.

The source markup vocabulary is small and fully enumerated (it is plain
Gutenberg output), so this hand-rolls the conversion rather than using a
generic HTML->Markdown library, which mangles <figure>/<figcaption> pairs
and table alignment.

Anything this script does not recognise is recorded in
tools/convert-report.txt rather than silently dropped.
"""
import html
import json
import pathlib
import re
import sys
from collections import Counter
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "tools" / ".cache"
POSTS_DIR = ROOT / "_posts"
REPORT = ROOT / "tools" / "convert-report.txt"

# Written by tools/images.py: photographic PNGs are re-encoded as JPEG, so the
# local path an image ends up at can differ in extension from the source URL.
_ASSET_MAP_FILE = CACHE / "asset-map.json"
ASSET_MAP = json.loads(_ASSET_MAP_FILE.read_text()) if _ASSET_MAP_FILE.exists() else {}


def _load_title_overrides():
    """slug -> corrected title, from tools/title-overrides.tsv."""
    f = ROOT / "tools" / "title-overrides.tsv"
    out = {}
    if not f.exists():
        return out
    for line in f.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "\t" not in line:
            continue
        slug, title = line.split("\t", 1)
        out[slug.strip()] = title.strip()
    return out


TITLE_OVERRIDES = _load_title_overrides()


def _load_link_replacements():
    """old url -> new url, from tools/link-replacements.tsv."""
    f = ROOT / "tools" / "link-replacements.tsv"
    out = {}
    if not f.exists():
        return out
    for line in f.read_text().splitlines():
        line = line.rstrip()
        if not line or line.startswith("#") or "\t" not in line:
            continue
        parts = line.split("\t")
        if len(parts) >= 2 and parts[1].strip():
            out[parts[0].strip()] = parts[1].strip()
    return out


LINK_REPLACEMENTS = _load_link_replacements()

UPLOADS_RE = re.compile(r"https?://(?:www\.)?kencaldeira\.com/wp-content/uploads/", re.I)
# Older posts still point at kencaldeira.files.wordpress.com, the WordPress.com
# CDN from an earlier incarnation of the site. Those are Ken's own images and
# would die with that account, so they get mirrored too -- under their own
# prefix, because 8 of the 14 filenames collide with self-hosted uploads.
WPCOM_RE = re.compile(r"https?://kencaldeira\.files\.wordpress\.com/", re.I)
SIZE_SUFFIX_RE = re.compile(r"-\d+x\d+(?=\.[A-Za-z0-9]+$)")
# Hot-linked third-party images only reachable over http would be blocked as
# mixed content on the HTTPS site; these hosts serve the same file over https.
HTTPS_UPGRADE = ("assets.climatecentral.org",)

# Inline text colour carries meaning in 7 posts (it marks quoted email and
# external material), so it is preserved -- but mapped to theme-aware classes
# instead of hardcoded hex, which would be illegible in dark mode.
COLOR_CLASS = {
    "#0000ff": "tc-blue",
    "#000080": "tc-navy",
    "#800000": "tc-maroon",
    "#808080": "tc-gray",
    "#000000": "tc-plain",
    "vivid-cyan-blue": "tc-blue",
    "black": "tc-plain",
}

BLOCK_TAGS = {"p", "div", "figure", "table", "thead", "tbody", "tr", "th", "td",
              "ul", "ol", "li", "h1", "h2", "h3", "h4", "h5", "h6", "hr",
              "figcaption", "blockquote", "iframe", "br", "img"}
INLINE_KEEP = {"sub", "sup"}   # no Markdown equivalent; emitted as raw HTML
VOID = {"img", "br", "hr", "source", "meta", "link", "input"}

report = Counter()


# --------------------------------------------------------------------------
# minimal DOM
# --------------------------------------------------------------------------
class Node:
    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = dict(attrs or {})
        self.children = []
        self.parent = parent
        self.text = ""

    def cls(self):
        return self.attrs.get("class", "").split()

    def __repr__(self):
        return f"<{self.tag} {self.attrs.get('class','')}>"


class DOM(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root")
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        t = Node("#text", parent=self.cur)
        t.text = data
        self.cur.children.append(t)


def parse(src):
    d = DOM()
    d.feed(src)
    d.close()
    return d.root


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def local_asset(url):
    """Rewrite a hosted-image URL to a local /assets/images/... path.

    The -WxH size suffix is dropped so every WordPress-generated variant of
    one image collapses onto a single local file.
    """
    if not url:
        return url
    if url in LINK_REPLACEMENTS:
        return LINK_REPLACEMENTS[url]
    if UPLOADS_RE.search(url):
        path = UPLOADS_RE.sub("", url).split("?")[0]
        local = "/assets/images/" + SIZE_SUFFIX_RE.sub("", path)
        return ASSET_MAP.get(local, local)
    if WPCOM_RE.search(url):
        path = WPCOM_RE.sub("", url).split("?")[0]
        local = "/assets/images/wpcom/" + SIZE_SUFFIX_RE.sub("", path)
        return ASSET_MAP.get(local, local)
    if url.startswith("http://") and any(hh in url for hh in HTTPS_UPGRADE):
        return "https://" + url[len("http://"):]
    return url


def plain_text(node):
    """Concatenate descendant text, stripped of markup."""
    if node.tag == "#text":
        return node.text
    return "".join(plain_text(c) for c in node.children)


def collapse(s):
    return " ".join(s.split())


MD_SPECIAL = re.compile(r"([\\`*_\[\]])")


def esc(text):
    """Escape Markdown-significant characters in a text node."""
    return MD_SPECIAL.sub(r"\\\1", text)


def attr_quote(s):
    return collapse(s).replace("\\", "").replace('"', "&quot;")


def color_class(node):
    style = node.attrs.get("style", "")
    m = re.search(r"color:\s*(#[0-9a-fA-F]{3,6})", style)
    if m:
        return COLOR_CLASS.get(m.group(1).lower())
    for c in node.cls():
        m = re.fullmatch(r"has-(.+)-color", c)
        if m and m.group(1) != "inline":
            return COLOR_CLASS.get(m.group(1))
    return None


def youtube_id(url):
    m = re.search(r"(?:youtube\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{6,})", url or "")
    return m.group(1) if m else None


# --------------------------------------------------------------------------
# inline rendering
# --------------------------------------------------------------------------
def split_ws(s):
    """Split into (leading ws, core, trailing ws).

    Markdown emphasis and link syntax cannot hold leading/trailing spaces
    inside the delimiters, but the source routinely puts them there
    (`<a ...>a YouTube video </a>in which`), so the whitespace has to be
    moved outside the delimiters rather than stripped.
    """
    m = re.fullmatch(r"(\s*)(.*?)(\s*)", s, re.S)
    return m.group(1), m.group(2), m.group(3)


def render_inline(node, ctx=""):
    out = []
    for c in node.children:
        t = c.tag
        if t == "#text":
            out.append(esc(c.text))
        elif t in ("em", "i"):
            lead, core, trail = split_ws(render_inline(c, ctx))
            out.append(f"{lead}_{core}_{trail}" if core else lead or trail)
        elif t in ("strong", "b"):
            lead, core, trail = split_ws(render_inline(c, ctx))
            out.append(f"{lead}**{core}**{trail}" if core else lead or trail)
        elif t == "a":
            href = c.attrs.get("href", "")
            lead, core, trail = split_ws(render_inline(c, ctx))
            if not core:
                out.append(lead or trail)
            elif not href:
                out.append(lead + core + trail)
            else:
                out.append(f"{lead}[{core}]({local_asset(href)}){trail}")
        elif t == "br":
            out.append("  \n" if ctx != "cell" else "<br>")
        elif t in INLINE_KEEP:
            out.append(f"<{t}>{render_inline(c, ctx)}</{t}>")
        elif t == "span":
            cc = color_class(c)
            inner = render_inline(c, ctx)
            out.append(f'<span class="{cc}">{inner}</span>' if cc else inner)
        elif t == "img":
            # a bare inline image outside a figure
            src = local_asset(c.attrs.get("src", ""))
            out.append(f'![{attr_quote(c.attrs.get("alt",""))}]({src})')
        elif t in ("small", "code", "cite", "abbr", "u", "s", "strike", "big", "font"):
            out.append(render_inline(c, ctx))
            report[f"note:inline-unwrapped:{t}"] += 1
        else:
            out.append(render_inline(c, ctx))
            report[f"inline-unknown:{t}"] += 1
    return "".join(out)


# --------------------------------------------------------------------------
# block rendering
# --------------------------------------------------------------------------
def strip_tag(node, tag):
    """A shallow copy of `node` with all `tag` descendants removed."""
    out = Node(node.tag, node.attrs)
    out.text = node.text
    for c in node.children:
        if c.tag == tag:
            continue
        out.children.append(strip_tag(c, tag))
    return out


def image_include(img, caption="", link=""):
    src = local_asset(img.attrs.get("src", ""))
    alt = attr_quote(img.attrs.get("alt", ""))
    parts = [f'src="{src}"']
    if alt:
        parts.append(f'alt="{alt}"')
    if caption:
        parts.append(f'caption="{caption}"')
    if link:
        parts.append(f'link="{link}"')
    return "{% include figure.html " + " ".join(parts) + " %}"


def render_figure_image(fig):
    """<figure class="wp-block-image"> -> a figure.html include."""
    img = first(fig, "img")
    if img is None:
        report["figure-image-without-img"] += 1
        return ""
    src = local_asset(img.attrs.get("src", ""))
    alt = attr_quote(img.attrs.get("alt", ""))
    cap_node = first(fig, "figcaption")
    caption = attr_quote(render_inline(cap_node)) if cap_node is not None else ""
    link = ""
    a = first(fig, "a")
    if a is not None and a.attrs.get("href"):
        href = a.attrs["href"]
        # A link wrapping the image that merely points at the image file itself
        # is WordPress's lightbox behaviour, not a real destination.
        if local_asset(href) != src:
            link = href
    return image_include(img, caption, link)


def render_gallery(fig):
    imgs = list(findall(fig, "img"))
    srcs = [local_asset(i.attrs.get("src", "")) for i in imgs]
    alts = [attr_quote(i.attrs.get("alt", "")) for i in imgs]
    items = "|".join(srcs)
    return ("{% include gallery.html srcs=\"" + items + "\""
            + (f' alts="{"|".join(alts)}"' if any(alts) else "")
            + " %}")


def render_embed(fig):
    ifr = first(fig, "iframe")
    url = ifr.attrs.get("src", "") if ifr is not None else plain_text(fig)
    vid = youtube_id(url)
    if vid:
        title = attr_quote(ifr.attrs.get("title", "")) if ifr is not None else ""
        cap_node = first(fig, "figcaption")
        caption = attr_quote(render_inline(cap_node)) if cap_node is not None else ""
        s = f'{{% include youtube.html id="{vid}"'
        if title:
            s += f' title="{title}"'
        if caption:
            s += f' caption="{caption}"'
        return s + " %}"
    report["embed-not-youtube"] += 1
    u = collapse(plain_text(fig)) or url
    return f"<{u}>" if u.startswith("http") else ""


def render_table(fig_or_table):
    table = fig_or_table if fig_or_table.tag == "table" else first(fig_or_table, "table")
    if table is None:
        return ""
    rows = list(findall(table, "tr"))
    if not rows:
        return ""
    grid, aligns = [], []
    for ri, tr in enumerate(rows):
        cells = [c for c in tr.children if c.tag in ("td", "th")]
        grid.append([collapse(render_inline(c, "cell")).replace("|", "\\|") for c in cells])
        if ri == 0:
            for c in cells:
                a = c.attrs.get("data-align") or ("center" if "has-text-align-center" in c.cls() else "")
                aligns.append(a)
    header_is_th = all(c.tag == "th" for c in rows[0].children if c.tag in ("td", "th"))
    width = max(len(r) for r in grid)
    aligns += [""] * (width - len(aligns))
    for r in grid:
        r += [""] * (width - len(r))

    def sep(a):
        return {"center": ":---:", "right": "---:", "left": ":---"}.get(a, "---")

    lines = []
    if header_is_th:
        lines.append("| " + " | ".join(grid[0]) + " |")
        lines.append("| " + " | ".join(sep(a) for a in aligns) + " |")
        body = grid[1:]
    else:
        lines.append("| " + " | ".join([""] * width) + " |")
        lines.append("| " + " | ".join(sep(a) for a in aligns) + " |")
        body = grid
    for r in body:
        lines.append("| " + " | ".join(r) + " |")

    caption = ""
    if fig_or_table.tag == "figure":
        cn = first(fig_or_table, "figcaption")
        if cn is not None:
            caption = collapse(render_inline(cn))
    out = "\n".join(lines)
    if caption:
        out += f"\n{{: .table-caption}}\n{caption}"
    return out


def render_list(node, depth=0):
    bullet_ol = node.tag == "ol"
    lines = []
    i = 0
    for li in [c for c in node.children if c.tag == "li"]:
        i += 1
        marker = f"{i}." if bullet_ol else "-"
        pad = "  " * depth
        inline = collapse(render_inline(li)).strip()
        lines.append(f"{pad}{marker} {inline}")
        for sub in li.children:
            if sub.tag in ("ul", "ol"):
                lines.append(render_list(sub, depth + 1))
    return "\n".join(lines)


def first(node, tag):
    for c in findall(node, tag):
        return c
    return None


def findall(node, tag):
    for c in node.children:
        if c.tag == tag:
            yield c
        yield from findall(c, tag)


def render_blocks(node, slug):
    """Render the children of `node` as a list of block strings."""
    out = []
    for c in node.children:
        t, classes = c.tag, c.cls()
        if t == "#text":
            if c.text.strip():
                out.append(collapse(esc(c.text)))
            continue
        if t == "p":
            s = render_inline(c).strip()
            if s:
                cc = color_class(c)
                if cc:
                    s = f'<span class="{cc}">{s}</span>'
                if "has-text-align-center" in classes:
                    s += "\n{: .text-center}"
                out.append(s)
            continue
        if t in ("h1", "h2", "h3", "h4", "h5", "h6"):
            img = first(c, "img")
            if img is not None:
                # Mis-marked source block: a figure pasted inside a heading is
                # really an image plus its caption, not a heading.
                caption = attr_quote(collapse(render_inline(strip_tag(c, "figure"))))
                out.append(image_include(img, caption))
                report["note:heading-as-image"] += 1
                continue
            # Demote in-content h1 to h2: the page title is already the h1.
            level = max(2, int(t[1]))
            out.append("#" * level + " " + collapse(render_inline(c)).strip())
            continue
        if t == "hr":
            out.append("* * *")
            continue
        if t == "figure":
            if "wp-block-table" in classes or first(c, "table") is not None:
                out.append(render_table(c))
            elif "wp-block-gallery" in classes:
                out.append(render_gallery(c))
            elif "wp-block-embed" in classes or first(c, "iframe") is not None:
                out.append(render_embed(c))
            elif first(c, "img") is not None:
                out.append(render_figure_image(c))
            else:
                report["figure-unknown"] += 1
            continue
        if t == "table":
            out.append(render_table(c))
            continue
        if t in ("ul", "ol"):
            out.append(render_list(c))
            continue
        if t == "iframe":
            out.append(render_embed(c))
            continue
        if t == "div":
            if "highwire-cite-title" in classes:
                out.append("**" + collapse(render_inline(c)).strip() + "**\n{: .citation-title}")
                continue
            if "highwire-cite-authors" in classes:
                out.append(collapse(render_inline(c)).strip() + "\n{: .citation-authors}")
                continue
            # wp-block-image / columns / column / embed__wrapper are pure
            # layout wrappers around real blocks -- unwrap them.
            known = any(k in " ".join(classes) for k in
                        ("wp-block-image", "wp-block-column", "wp-block-embed__wrapper",
                         "wp-block-group", "wp-block-buttons", "highwire-cite"))
            if not known and classes:
                report["div-unwrapped:" + classes[0]] += 1
            out.extend(render_blocks(c, slug))
            continue
        if t == "img":
            out.append(image_include(c))
            continue
        if t == "br":
            continue
        if t == "blockquote":
            inner = render_blocks(c, slug)
            out.append("\n".join("> " + ln if ln else ">" for b in inner for ln in b.split("\n")))
            continue
        if t in ("span", "em", "strong", "b", "i", "a", "sub", "sup", "small", "code"):
            s = render_inline(Wrap(c)).strip()
            if s:
                out.append(s)
            continue
        report[f"block-unknown:{t}"] += 1
        out.extend(render_blocks(c, slug))
    return [b for b in out if b and b.strip()]


class Wrap:
    """Present a single node as a one-child container for render_inline."""
    def __init__(self, node):
        self.children = [node]


# --------------------------------------------------------------------------
# front matter + file writing
# --------------------------------------------------------------------------
def yaml_str(s):
    s = collapse(html.unescape(s))
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def convert_item(item, media_by_id):
    slug = item["slug"]
    body_blocks = render_blocks(parse(item["content"]["rendered"]), slug)
    body = "\n\n".join(body_blocks).strip() + "\n"
    body = re.sub(r"\n{3,}", "\n\n", body)

    fm = {
        "title": yaml_str(TITLE_OVERRIDES.get(slug, item["title"]["rendered"])),
        "date": item["date"] + "+00:00" if "+" not in item["date"] else item["date"],
        "slug": slug,
        "wp_id": str(item["id"]),
    }
    fid = item.get("featured_media") or 0
    if fid and fid in media_by_id:
        fm["image"] = local_asset(media_by_id[fid]["source_url"])
    return fm, body


def main():
    check = "--check" in sys.argv
    if "--force" not in sys.argv:
        sys.exit(
            "refusing to run: _posts/ is the hand-maintained source of truth "
            "now, and this would overwrite it from the WordPress snapshot.\n"
            "The migration is done; edit the Markdown in _posts/ directly.\n"
            "Pass --force only if you really mean to regenerate everything."
        )
    report.clear()
    posts = json.loads((CACHE / "posts.json").read_text())
    pages = json.loads((CACHE / "pages.json").read_text())
    media = json.loads((CACHE / "media.json").read_text())
    media_by_id = {m["id"]: m for m in media}

    POSTS_DIR.mkdir(exist_ok=True)
    for f in POSTS_DIR.glob("*.md"):
        f.unlink()

    written = 0
    for p in posts:
        fm, body = convert_item(p, media_by_id)
        date = p["date"][:10]
        lines = ["---", "layout: post"]
        for k, v in fm.items():
            lines.append(f"{k}: {v}")
        lines += ["---", "", body]
        (POSTS_DIR / f"{date}-{p['slug']}.md").write_text("\n".join(lines))
        written += 1

    for pg in pages:
        # A page carrying `hand_edited: true` has been rewritten by hand since
        # the import (the About page has), so the WordPress snapshot must not
        # overwrite it.
        target = ROOT / f"{pg['slug']}.md"
        if target.exists() and re.search(r"^hand_edited:\s*true\s*$",
                                        target.read_text(), re.M):
            print(f"skipped {target.name} (hand_edited: true)")
            continue
        fm, body = convert_item(pg, media_by_id)
        lines = ["---", "layout: page", f"permalink: /{pg['slug']}/"]
        for k, v in fm.items():
            if k != "date":
                lines.append(f"{k}: {v}")
        lines += ["---", "", body]
        target.write_text("\n".join(lines))

    lines = [f"{k}\t{v}" for k, v in sorted(report.items())]
    REPORT.write_text("\n".join(lines) + ("\n" if lines else ""))
    print(f"wrote {written} posts + {len(pages)} page(s)")
    notes = {k: v for k, v in report.items() if k.startswith("note:")}
    bad = {k: v for k, v in report.items() if not k.startswith("note:")}
    for label, d in (("notes (deliberate transformations)", notes),
                     ("UNHANDLED markup", bad)):
        if d:
            print(f"{label}:")
            for k, v in sorted(d.items()):
                print(f"  {v:5d}  {k}")
    if not bad:
        print("no unhandled markup")
    if check and bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
