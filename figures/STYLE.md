# Figure style guide

This guide covers the figures in `docs/assets/`. They're built as HTML in
`figures/src/` and rendered to transparent PNGs by `figures/render.py`, so
they drop cleanly into the docs site (light and dark themes) and into
slides.

The guide combines three sources:
- the visual language of the SageBrain Home Week deck (Oct 2026), which
  governanceDUO's `docs/assets/graph-design/*.png` also follow;
- a legibility checklist drawn from the Nature research-figure guide, AIAA
  journal figure guidelines, the Illinois Writers Workshop science style
  guide, and WCAG 2.x contrast rules;
- the author's feedback while the governanceDUO figures were iterated.

## 1. Rules

| Rule | Why |
|---|---|
| **One idea per figure.** Split, don't cram. Pair a compact *layer strip* with a separate *flow diagram* instead of merging them. | Busy figures were the main complaint |
| **Linear flow**, left→right or top→bottom, with **no crossing or overlapping arrows**. Merge parallel arrows into one bracket or rail. | Readable at a glance |
| **No legend or color key.** Every element carries its own text label; color only reinforces it. | Keys are noise. Color alone fails colorblind readers |
| **At most 3 text sizes**: title, label and sub-label, with a clear jump between tiers | Visual hierarchy |
| **Slide-scale type**: labels ≥ 22 px and sub-labels ≥ 17 px at 1× (the render is 2×) | Must stay legible scaled onto a slide or into a docs column |
| **Contrast on fills (WCAG AA)**: text on a card, tile, pill or chip ≥ 4.5:1 against that fill. Use white only on sage blue, teal-dark and navy. Use navy on green, orange, gold, white and muted fills | Every theme, projectors |
| **Nothing small floats on the transparent background.** No single color reaches 4.5:1 on both white and a dark theme; the best possible is about 4.06:1. Any text directly on the background (eyebrows, arrow labels, captions, yes/no) must be **bold and ≥ 19 px** in `--float-text` or `--float-accent`, which both clear 3:1 on white and on dark. Anything smaller goes inside a pill | The docs site has a dark theme, and slides vary |
| **Colorblind-safe**: never distinguish by red vs green alone. Blue, orange, teal and gold carry the categories | About 8% of men |
| **Strokes ≥ 2.5 px** at 1× for arrows and borders, in `--arrow` (≥ 3:1 on white and on dark). No hairlines | They survive downscaling, and stay visible in dark mode |
| **Transparent background**, no drop shadows and no page title inside the figure. The docs page caption gives the title | Pastes cleanly anywhere |
| **Plain words.** No "this repo", no jargon ("canonical", "old-namespace") and no IRIs. File or script names only as a muted sub-label | Figures are read by non-implementers |
| **Integrations are chips.** A small rounded pill (e.g. "Integrated with sagebrain-model") with a bracket to what it spans, not another box-and-arrow | Keeps the main flow linear |
| **Section labels** are small-caps eyebrow text in Sage blue, above a group ("SYNAPSE · SOURCE OF TRUTH") | Groups without drawing boxes around boxes |

## 2. Palette

The palette is sampled from the governanceDUO figures and the Home Week
deck.

| Token | Hex | Use |
|---|---|---|
| `--sage-blue` | `#1a7dbb` | Primary accent, eyebrow labels, layer 1 |
| `--navy` | `#1e293b` | Dark card fill for flow-diagram nodes, with white text |
| `--teal-dark` | `#264653` | Second dark layer and card fill |
| `--green` | `#3dbd8d` | Layer accent |
| `--orange` | `#f2994a` | Layer accent. Also the "next up" tone in the deck |
| `--gold` | `#c2a772` | Integration chips |
| `--slate` | `#5c7080` | Sub-labels inside light fills only (white pills, muted cards). Never on the transparent background |
| `--arrow` | `#7b8794` | Arrows, brackets and connectors: 3.66:1 on white, 4.40:1 on `#1e2129` |
| `--float-text` | `#7b8794` | Bold ≥ 19 px text on the transparent background (arrow labels, captions, yes/no) |
| `--float-accent` | `#3a8fd0` | Bold ≥ 19 px eyebrow labels on the transparent background: 3.49:1 on white, 4.61:1 on `#1e2129`. Sage blue itself is only 3.60:1 on dark |
| `--muted-fill` | `#f4f6f9` | Dashed "derived / optional" cards |
| `--white` | `#ffffff` | Text on dark fills, pill backgrounds |

A dark card with a white label and a light-gray sub-label (`#cbd3de`) is
the default node. A layer's color appears as a 6 px left edge on its node,
so layer identity carries across figures without a key.

## 3. Type

**DM Sans** (Google Fonts, weights 400/500/700) is the deck's font and this
docs site's `theme.font`. Use 700 for titles and labels, 400 for
sub-labels, and 500 for eyebrow labels (uppercase, letter-spacing 0.06em).

## 4. Build

```bash
python figures/render.py             # renders every figures/src/*.html -> docs/assets/<dir>/<name>.png
python figures/render.py kg-layers   # just one
```

`render.py` works in three steps:
1. It runs headless Chrome at device-scale 2 with a transparent default
   background.
2. It trims to the content bounding box plus 16 px of padding.
3. It checks that the corners are fully transparent.

Each HTML file declares its output path in
`<meta name="output" content="docs/assets/knowledge-graph/kg-layers.png">`.
Commit both the HTML source and the PNG. The renderer needs Pillow and
Google Chrome; `kg-pipeline/.venv` already has Pillow.

The renderer refuses in two cases: when the raw screenshot's corners aren't
transparent (an opaque page background), and when content touches the
screenshot edge (a figure wider or taller than the window, which would
otherwise be clipped silently).

## 5. Review checklist

Check every rendered PNG before committing it:

- [ ] No text is clipped or overlapping, and no arrows cross
- [ ] It's legible at 50% scale, which is roughly how it appears in a docs column
- [ ] It reads on white and on the docs dark theme (`#1e2129`), composited both ways, with contrast computed for every text/fill pair and every floating label
- [ ] It has no legend, no in-figure title and no drop shadows
- [ ] Every label is plain language, with no IRIs and no "this repo"
- [ ] Every fact in it matches the page it illustrates
