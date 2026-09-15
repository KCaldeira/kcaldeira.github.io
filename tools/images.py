#!/usr/bin/env python3
"""Download and optimize every image the site references locally.

Two passes:
  download  -- fetch full-resolution originals into originals/ (gitignored),
               falling back to the Wayback Machine for anything now missing
  optimize  -- write web-sized, EXIF-stripped copies into assets/images/

Originals are kept out of git but retained on disk as the archival copy, so
the optimization step can be re-run with different settings later.
"""
import concurrent.futures as cf
import hashlib
import io
import json
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
ORIG = ROOT / "originals"
OUT = ROOT / "assets" / "images"
MANIFEST = ROOT / "tools" / ".cache" / "image-manifest.json"
ASSET_MAP = ROOT / "tools" / ".cache" / "asset-map.json"
REPORT = ROOT / "tools" / "image-report.txt"

MAX_EDGE = 1600
JPEG_Q = 82
# A PNG with no transparency and this many distinct colours is photographic
# content (screenshots of maps and photos), where PNG costs ~10x JPEG for no
# visible benefit. Charts and screenshots of text stay PNG and stay sharp.
PHOTO_COLORS = 20000
# Palette quantization is accepted only when the mean per-channel error is
# below this, which keeps plots and diagrams pixel-faithful.
QUANT_MAX_MAE = 1.2
UA = {"User-Agent": "Mozilla/5.0 (compatible; kencaldeira-migration/1.0)"}

Image.MAX_IMAGE_PIXELS = 300_000_000  # some source scans are very large


def build_manifest():
    """Map each local /assets/images/... path to the remote URLs that can
    supply it, best source first."""
    import convert as C

    cache = ROOT / "tools" / ".cache"
    items = json.loads((cache / "posts.json").read_text()) + \
        json.loads((cache / "pages.json").read_text())
    html = "".join(i["content"]["rendered"] for i in items)

    manifest = {}

    def add(local, remote):
        manifest.setdefault(local, [])
        if remote not in manifest[local]:
            manifest[local].append(remote)

    # Every referenced variant maps to the same local file. Prefer the
    # original (no -WxH suffix); keep the sized variants as fallbacks, since
    # a handful of originals are no longer on the server.
    for host_re, prefix in ((C.UPLOADS_RE, ""), (C.WPCOM_RE, "wpcom/")):
        for url in set(re.findall(host_re.pattern.replace("(?i)", "") + r"[^\s\"'\)>]+", html, re.I)):
            url = url.split("?")[0].rstrip(".,;")
            rel = host_re.sub("", url)
            local = "/assets/images/" + prefix + C.SIZE_SUFFIX_RE.sub("", rel)
            base = host_re.pattern  # unused, kept for clarity
            add(local, host_re.sub(lambda m: m.group(0), url))
    # order candidates: unsuffixed original first, then largest variants
    for local, urls in manifest.items():
        def rank(u):
            m = re.search(r"-(\d+)x(\d+)\.\w+$", u)
            return (1, -int(m.group(1))) if m else (0, 0)
        manifest[local] = sorted(set(urls), key=rank)
    MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True))
    return manifest


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def wayback(url):
    """Ask the Wayback Machine for the newest snapshot of a dead URL."""
    api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url, safe="")
    try:
        data = json.loads(fetch(api, timeout=45).decode())
    except Exception:
        return None
    snap = (data.get("archived_snapshots") or {}).get("closest") or {}
    if not snap.get("available"):
        return None
    # the id_ suffix returns the original bytes, without the archive's banner
    ts_url = snap["url"].replace("http://", "https://")
    ts_url = re.sub(r"/web/(\d+)/", r"/web/\1id_/", ts_url)
    try:
        return fetch(ts_url, timeout=90)
    except Exception:
        return None


def download_one(local, urls):
    dest = ORIG / local.removeprefix("/assets/images/")
    if dest.exists() and dest.stat().st_size > 0:
        return local, "cached", dest.stat().st_size
    dest.parent.mkdir(parents=True, exist_ok=True)
    for u in urls:
        try:
            data = fetch(u)
            if data:
                dest.write_bytes(data)
                return local, "ok" if u == urls[0] else "ok-variant", len(data)
        except urllib.error.HTTPError as e:
            last = f"http {e.code}"
        except Exception as e:
            last = type(e).__name__
    for u in urls:
        data = wayback(u)
        if data:
            dest.write_bytes(data)
            return local, "wayback", len(data)
    return local, "MISSING", 0


def cmd_download():
    manifest = build_manifest()
    ORIG.mkdir(exist_ok=True)
    results = []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(download_one, k, v): k for k, v in manifest.items()}
        for i, f in enumerate(cf.as_completed(futs), 1):
            results.append(f.result())
            if i % 25 == 0:
                print(f"  ...{i}/{len(manifest)}", flush=True)
    stat = {}
    for local, how, size in results:
        stat.setdefault(how, []).append((local, size))
    total = sum(s for _, _, s in results)
    lines = [f"originals: {len(results)} images, {total/1e6:.1f} MB"]
    for how in sorted(stat):
        lines.append(f"  {how:12s} {len(stat[how]):4d}")
    for local, _ in sorted(stat.get("MISSING", [])):
        lines.append(f"  MISSING  {local}  <- {manifest[local]}")
    for local, _ in sorted(stat.get("wayback", [])):
        lines.append(f"  RECOVERED FROM ARCHIVE  {local}")
    out = "\n".join(lines)
    REPORT.write_text(out + "\n")
    print(out)


def _mae(a, b):
    """Mean absolute per-channel difference between two same-size images."""
    from PIL import ImageChops, ImageStat
    diff = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
    return sum(ImageStat.Stat(diff).mean) / 3.0


def optimize_one(src):
    rel = src.relative_to(ORIG)
    raw = src.read_bytes()
    try:
        im = Image.open(io.BytesIO(raw))
        im.load()
    except Exception as e:
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        return rel, rel, len(raw), len(raw), f"copied ({type(e).__name__})"

    fmt = (im.format or "").upper()
    if getattr(im, "is_animated", False):
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)          # preserve animated GIFs as-is
        return rel, rel, len(raw), len(raw), "animated"

    w, h = im.size
    if max(w, h) > MAX_EDGE:
        scale = MAX_EDGE / max(w, h)
        im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)

    has_alpha = im.mode in ("RGBA", "LA", "PA") or (
        im.mode == "P" and "transparency" in im.info)
    ncolors = len(im.convert("RGB").getcolors(maxcolors=1 << 24) or [])
    note = "ok"

    def as_jpeg():
        b = io.BytesIO()
        im.convert("RGB").save(b, "JPEG", quality=JPEG_Q, optimize=True, progressive=True)
        return b.getvalue()

    def as_png():
        best = io.BytesIO()
        im.save(best, "PNG", optimize=True)
        best = best.getvalue()
        if not has_alpha and ncolors > 256:
            try:
                q = im.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT)
                qb = io.BytesIO()
                q.save(qb, "PNG", optimize=True)
                if len(qb.getvalue()) < len(best) and _mae(q, im) <= QUANT_MAX_MAE:
                    return qb.getvalue(), True
            except Exception:
                pass
        return best, False

    if fmt in ("JPEG", "MPO"):
        data, out_ext = as_jpeg(), ".jpg"
    elif fmt == "PNG" and not has_alpha and ncolors > PHOTO_COLORS:
        # photographic PNG -> JPEG
        data, out_ext = as_jpeg(), ".jpg"
        note = "png->jpg"
    elif fmt == "PNG":
        data, quantized = as_png()
        out_ext = ".png"
        if quantized:
            note = "png-palette"
    elif fmt == "GIF":
        data, out_ext = raw, rel.suffix
    else:
        b = io.BytesIO()
        im.save(b, fmt or "PNG", optimize=True)
        data, out_ext = b.getvalue(), rel.suffix

    if len(data) >= len(raw) and max(w, h) <= MAX_EDGE and out_ext == rel.suffix:
        data, note = raw, "kept-original"

    dest_rel = rel.with_suffix(out_ext)
    dest = OUT / dest_rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return rel, dest_rel, len(raw), len(data), note


def cmd_optimize():
    srcs = [p for p in ORIG.rglob("*") if p.is_file()]
    if not srcs:
        sys.exit("no originals found; run `images.py download` first")
    OUT.mkdir(parents=True, exist_ok=True)
    tin = tout = 0
    notes = []
    amap = {}
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for rel, dest_rel, a, b, how in ex.map(optimize_one, srcs):
            tin += a
            tout += b
            if rel != dest_rel:
                amap["/assets/images/" + rel.as_posix()] = "/assets/images/" + dest_rel.as_posix()
            if how != "ok":
                notes.append(f"  {how:22s} {rel}")
    ASSET_MAP.write_text(json.dumps(amap, indent=1, sort_keys=True))
    print(f"asset-map: {len(amap)} path(s) changed extension -> re-run convert.py")
    print(f"optimized {len(srcs)} images: {tin/1e6:.1f} MB -> {tout/1e6:.1f} MB "
          f"({100*tout/max(tin,1):.0f}%)")
    for n in sorted(notes):
        print(n)
    with REPORT.open("a") as f:
        f.write(f"\nweb assets: {len(srcs)} images, {tout/1e6:.1f} MB (from {tin/1e6:.1f} MB)\n")
        f.write("\n".join(sorted(notes)) + "\n")


def cmd_prune():
    """Delete web assets no longer referenced by the converted Markdown.

    The download manifest is a superset of what the posts actually use (it is
    built from the raw HTML, which also contains lightbox hrefs and duplicate
    copies of the same image on two hosts), so the committed asset tree is
    reconciled against the real references here.
    """
    refs = set()
    for f in list((ROOT / "_posts").glob("*.md")) + list(ROOT.glob("*.md")):
        refs |= set(re.findall(r"/assets/images/[^\"\)\|\s]+", f.read_text()))
    removed = 0
    freed = 0
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            local = "/assets/images/" + p.relative_to(OUT).as_posix()
            if local not in refs:
                freed += p.stat().st_size
                p.unlink()
                removed += 1
                print(f"  pruned {local}")
    for d in sorted(OUT.rglob("*"), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    kept = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    print(f"pruned {removed} unreferenced asset(s), {freed/1e6:.1f} MB; "
          f"{kept/1e6:.1f} MB kept")


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "tools"))
    cmd = sys.argv[1] if len(sys.argv) > 1 else "download"
    {"download": cmd_download, "optimize": cmd_optimize,
     "prune": cmd_prune}[cmd]()
