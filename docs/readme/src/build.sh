#!/usr/bin/env bash
# Rebuild every README image of filmforge in Glass, dark and light, wide and phone.
#
#   NODE_PATH=/path/to/node_modules docs/readme/src/build.sh
#
# Needs: python3 (the repo's requirements), node with playwright and three (0.170) in NODE_PATH,
# a Chromium that playwright can launch (a GPU helps; the scenes are WebGL), ImageMagick and ffmpeg.
# ONLY="hero lint" rebuilds just those images.
# 1. terminals.py runs the real tools on examples/the-lantern-moth and writes their output as terminal pages.
# 2. capture.cjs photographs every page at 2x in both colour schemes, and every frame of a page that moves.
# 3. render.cjs composes the glass scenes from layouts.js; ImageMagick writes the stills as WebP and ffmpeg the loop.
# The hero is the one loop: 8 seconds at 12 frames a second in which a film goes down the stage rail
# (pages/track.html). Its glass and its text plates hold still, so only the rail is paid for in bytes and the
# text stays as sharp as in a still. Every other image is a still.
set -euo pipefail
SRC=$(cd "$(dirname "$0")" && pwd)
OUT=$(cd "$SRC/.." && pwd)
BUILD="$OUT/build"
: "${NODE_PATH:?set NODE_PATH to a node_modules folder that holds playwright and three}"
export NODE_PATH

python3 "$SRC/terminals.py"
node "$SRC/capture.cjs"
rm -rf "$BUILD/png"; mkdir -p "$BUILD/png"

jobs=()
for l in ${ONLY:-hero numbers price prompt lint shots stages}; do
  for t in dark light; do
    if [ "$l" = hero ]; then        # the loop, encoded by render.cjs: quality 88 wide, 84 on the phone
      jobs+=("hero:$t:loop:$OUT/hero-$t.webp:88" "hero-phone:$t:loop:$OUT/hero-$t-phone.webp:84")
    else
      jobs+=("$l:$t:still:$BUILD/png/$l-$t.png" "$l-phone:$t:still:$BUILD/png/$l-$t-phone.png")
    fi
  done
done
node "$SRC/render.cjs" "${jobs[@]}"
shopt -s nullglob
for f in "$BUILD"/png/*.png; do
  magick "$f" -strip -quality 90 -define webp:method=6 "$OUT/$(basename "$f" .png).webp"
done

du -ch "$OUT"/*.webp | tail -1
