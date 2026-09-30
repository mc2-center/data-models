"""Render figures/src/*.html to transparent, trimmed PNGs.

Each source declares where its PNG goes:
    <meta name="output" content="docs/assets/knowledge-graph/kg-layers.png">

Rendering uses headless Google Chrome at device-scale 2 with a transparent
default background (so no page color leaks into the PNG). The screenshot is
trimmed to its content bounding box plus PAD px. Before trimming, the raw
screenshot must have transparent corners (no opaque page background) and
content that stops short of the window edge (no silent clipping). See
figures/STYLE.md.

Usage (from the repo root):
    python figures/render.py              # every figures/src/*.html
    python figures/render.py kg-layers    # just figures/src/kg-layers.html
"""

import argparse
import glob
import os
import re
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "figures", "src")
CHROME = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
PAD = 16
OUTPUT_META_RE = re.compile(r'<meta\s+name="output"\s+content="([^"]+)"')
# Wide/tall enough for any figure; the trim step removes the unused area.
WINDOW = "2000,1600"


def output_path(html_path):
    with open(html_path) as f:
        match = OUTPUT_META_RE.search(f.read())
    if not match:
        raise SystemExit(f'{html_path}: missing <meta name="output" content="docs/assets/...png">')
    return os.path.join(ROOT, match.group(1))


def render(html_path):
    out = output_path(html_path)
    with tempfile.TemporaryDirectory() as tmp:
        raw = os.path.join(tmp, "raw.png")
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
             "--force-device-scale-factor=2", "--default-background-color=00000000",
             # Time for the DM Sans web font to load before the screenshot.
             "--virtual-time-budget=5000", f"--window-size={WINDOW}",
             f"--screenshot={raw}", "file://" + os.path.abspath(html_path)],
            check=True, capture_output=True,
        )
        img = Image.open(raw).convert("RGBA")
    # Checked on the raw screenshot, before cropping: after the crop and
    # padding below, the corners are always our own transparent padding.
    # An opaque page background fills all four corners; oversized content
    # reaches an edge but leaves some corner clear - report which it is.
    raw_corners = [(0, 0), (img.width - 1, 0), (0, img.height - 1), (img.width - 1, img.height - 1)]
    if all(img.getpixel(c)[3] != 0 for c in raw_corners):
        raise SystemExit(f"{html_path}: page background isn't transparent - set html,body{{background:transparent}}")
    bbox = img.getbbox()
    if bbox is None:
        raise SystemExit(f"{html_path}: rendered fully transparent - nothing drawn")
    if bbox[2] >= img.width or bbox[3] >= img.height or any(img.getpixel(c)[3] != 0 for c in raw_corners):
        raise SystemExit(f"{html_path}: content reaches the {WINDOW} window edge and may be clipped - "
                         "shrink the figure or raise WINDOW")
    cropped = img.crop(bbox)
    canvas = Image.new("RGBA", (cropped.width + 2 * PAD, cropped.height + 2 * PAD), (0, 0, 0, 0))
    canvas.paste(cropped, (PAD, PAD), cropped)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    canvas.save(out)
    print(f"{os.path.relpath(html_path, ROOT)} -> {os.path.relpath(out, ROOT)}  ({canvas.width}x{canvas.height})")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("names", nargs="*", help="Figure names (figures/src/<name>.html); default: all")
    args = parser.parse_args()
    if not os.path.isfile(CHROME):
        sys.exit(f"Google Chrome not found at {CHROME} - set CHROME=/path/to/chrome")
    paths = ([os.path.join(SRC_DIR, f"{n}.html") for n in args.names] if args.names
             else sorted(glob.glob(os.path.join(SRC_DIR, "*.html"))))
    missing = [p for p in paths if not os.path.isfile(p)]
    if missing:
        sys.exit(f"not found: {missing}")
    for path in paths:
        render(path)


if __name__ == "__main__":
    main()
