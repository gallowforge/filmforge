# Fixes in post, in detail

Every fix is done in post: in your editor, your compositor, or code you own. Each one is a named operation with exact
numbers, written into qa.yaml as `op` and `params` so anyone can do it again and get the same pixels. A fix writes a
new file and never touches the original.

Save the fixed copy beside the painting as `<name>_g.<ext>`. The checking tools (ledger, contact sheet, archive)
read the newest version of each shot by name, in natural order, so they measure the `_g` copy. A repaint is
`_v2`, and its own fix is `_v2_g`. Several operations on one painting go into one `_g` file, in the order qa.yaml
lists them.

## recolour

`op: recolour`, `params: {box: [x0, y0, x1, y1], hue_band: [lo, hi], new_hue: N, sat: S}`

- `box`: in the painting's own pixels (read them off a zoom crop's printed coordinates).
- `hue_band`: the hue band to move, in degrees (red wraps: 345 to 15). Find it from the ledger's palette swatch:
  convert the hex to hue, then take +-10 degrees, or use the forbid rule's own band.
- `new_hue`: the target hue in degrees. Rotate the band so its centre lands there, so the shading inside it survives.
- `sat`: saturation multiplier (1.0 keeps it; 0.8 calms it).
- Move only pixels above 0.25 saturation, and feather the band's edges, so greys in the box stay grey.
- Verify: re-run `ledger.py palette` on the folder with the `_g` file, and zoom the box at 100%.

The Lantern Moth's qa.yaml writes s02's fix this way: `box: [560, 200, 1240, 820]`, `hue_band: [38, 58]`,
`new_hue: 22`, `sat: 0.8`, which moves the match's gold glow to the moth's ember orange inside the box around the
match and the hood.

## blue

`op: blue`, `params: {keep: 0.3}`

Pull every saturated blue (hue 170 to 250) toward a neutral silver, keeping `keep` of the original (0.3 by default).
Use it to keep a colour rule ("no blue until the ending") when paintings drift. Verify with the forbid rule.

## exposure

`op: exposure`, `params: {stops: +N}` (or `-N`)

Multiply linear light by 2 to the power `stops`, with a soft shoulder so highlights roll off instead of clipping. Work
in linear light, not on the gamma-encoded pixels, or the shadows and highlights move by different amounts. Use it for
a deliberate change that matched levels should not level out.

## patch

`op: patch`, `params: {box: [x0, y0, x1, y1], offset: [dx, dy]}`

For a stray figure or object in an area of plain texture (sky, sand, smoke): copy a clean region from a small offset,
feather it, and paste it over the stray. Choose an offset where the texture continues. Verify at 100% for repeats.

## crop

`crop: [x0, y0, x1, y1]` in the shot's `motion` (in the painting's own pixels), applied before the 4K upscale. Use it
for headroom, tangents and a too-loose framing. A crop smaller than 75% of the width will look soft; repaint instead.

## Matched levels (every painting)

Measure each painting's 0.5 and 99.5 percentile luminance, map them to shared black and white targets, and blend the
result 60% with the original so the painting keeps its character. Then one bloom, grain and vignette pass runs over
the whole film, so shots from separate generations cut together. `ledger.py palette` reports exposure jumps in stops
on the painting files; anything over the ledger's `exposure_stops` (1.5 by default) is worth a look in the preview,
and a deliberate change (a time cut to dawn) belongs in the ledger's `expected_jumps`. A jump that matched levels
evens out needs no `_g` file: say so in the fix's `verify` line and check it in the preview.

## The upscale (every painting)

2K paintings go to the film's size with Lanczos, then a sharpen applied only where there are edges, so flat colour
stays clean. Keep the upscaled copies in a `4k/` folder, which `archive.py` leaves out on purpose. Soft paintings
gain most; a painting that is soft at 2K because its subject is small in frame is a scale problem, not this.

## When post is the wrong answer

- The subject is the wrong size, the wrong person, or the wrong number: repaint.
- The beat does not read: repaint (the prompt's MOMENT was wrong).
- More than two fixes on one frame: repaint is usually cheaper than the time, and cleaner.
