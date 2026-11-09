#!/usr/bin/env bash
# Rebuild every README image of filmforge in Glass, dark and light, wide and phone.
#
#   NODE_PATH=/path/to/node_modules docs/readme/src/build.sh
#
# Needs: python3 (the repo's requirements), node with playwright and three (0.170) in NODE_PATH,
# a Chromium that playwright can launch (a GPU helps; the scenes are WebGL), and ImageMagick.
# 1. terminals.py runs the real tools on examples/the-lantern-moth and writes their output as terminal pages.
# 2. capture.cjs photographs every page at 2x in both colour schemes.
# 3. render.cjs composes the glass scenes from layouts.js, and ImageMagick writes them as WebP.
# The scenes are periodic (render.cjs can write a loop), but the README uses stills: the pages are text, and
# text stays sharper and lighter as a still than as an animated WebP.
set -euo pipefail
SRC=$(cd "$(dirname "$0")" && pwd)
OUT=$(cd "$SRC/.." && pwd)
BUILD="$OUT/build"
: "${NODE_PATH:?set NODE_PATH to a node_modules folder that holds playwright and three}"
export NODE_PATH

python3 "$SRC/terminals.py"
node "$SRC/capture.cjs"
mkdir -p "$BUILD/png"

jobs=()
for l in hero numbers price prompt lint shots stages; do
  for t in dark light; do
    jobs+=("$l:$t:still:$BUILD/png/$l-$t.png" "$l-phone:$t:still:$BUILD/png/$l-$t-phone.png")
  done
done
node "$SRC/render.cjs" "${jobs[@]}"
for f in "$BUILD"/png/*.png; do
  magick "$f" -strip -quality 90 -define webp:method=6 "$OUT/$(basename "$f" .png).webp"
done

du -ch "$OUT"/*.webp | tail -1
