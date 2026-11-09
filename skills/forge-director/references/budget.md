# Budgeting a production

## The arithmetic

For every billable item: price x quantity x (1 + repaint buffer). Paintings and sheets are priced per image, music
per second, video per clip of a fixed length (a 7 s shot on a 5 s model is two clips). A video shot also needs its
keyframe painting. The reserve (5%) is never planned into.

```text
spendable = credits x (1 - reserve)
plan      = sum(price x qty x (1 + buffer))
fits      = plan <= spendable
```

Default buffers (config/prices.yaml): paintings 30%, sheets 50% (a sheet drifts more and every painting inherits
it), plates 30%, video 50%, music 0% (takes are planned explicitly).

## The three tiers budget.py always prints

1. **Full plan**: the shot list as written.
2. **Painted holds only**: every video shot told in painted key poses that snap from one to the next (default two
   poses, the keyframe counting as one). This is how a painted film tells motion: the classic precedent is a
   short film told almost entirely in still images.
3. **Must-haves only**: priority 1 items, video converted to poses.

## When the plan does not fit

`budget.py` prints the cheapest path, in a director's order:

1. Video shots become painted key poses, lowest priority and most expensive first.
2. The repaint buffer drops to 15%: more slips are fixed in post, where they cost nothing.
3. Optional shots go (priority 3, then 2), then optional assets.
4. Still short: the film is too long for the credits. Shorten it, or wait for the next allowance.

Recommend one path, in words, from budget.py's own lines. Example wording: "Tell the beam shot in two painted poses
instead of Kling video (saves 45.17), and do the same for the other five; the plan then fits at 60.53."

## The animatic gate (when real motion is on the table)

When a film could be animated with paid video, paint one keyframe per shot first and cut them to the music as a
timed moving storyboard. Watching the whole film as paintings costs a few percent of the motion budget and settles
story, pacing and look before the expensive part. The Lantern Moth shows the scale: as an animatic it is its six
paintings (16.50) and its score (5.80); the same six shots as Kling video add 195.00 in clips before retakes
(below). The gate after the animatic is where the owner chooses: the whole film animated, a hero cut, or the
painted film alone.

## Worked numbers

- **The finish plan** (`tests/fixtures/finish_plan.yaml`, a test fixture): 13 paintings x 2.75 = 35.75; cue 1,
  95.24 s, 13.81; cue 2, 115.17 s, 16.70; total 66.26 of 70.71, 4.45 left. No repaint buffer: every slip has to be
  fixed in post. `budget.py --credits 70.71 --retake 0 --reserve 0` reproduces the plan; with the defaults it
  reports 9.81 over, exits 2, and suggests a 15% buffer first (saves 5.36), still 4.45 short.
- **The Lantern Moth** (`budget.py shotlist.yaml --production production.yaml` in the example folder): two sheets
  and a plate 8.25 (11.82 with their buffers), a 40 s score 5.80, six paintings 16.50 (21.45 with the 30% buffer):
  39.08 of 66.50 spendable. With 33.30 already spent it fits with 27.42 to spare, room for 7 more paintings with
  retakes.
- **The same film as video** (`budget.py` on its shot list with every shot set to `kind: video`): each 6 s shot is
  two 5 s Kling clips (32.50) plus its keyframe, so motion alone is 195.00, 292.50 with the 50% video buffer, and
  the plan is 265.07 over. The fit plan turns all six into painted key poses and lands at 60.53.
- **A picture book:** pages at medium quality cost 1.0 credit each (an estimate in prices.yaml, shown with `~`)
  against 2.75 at high, so the same credits buy almost three times as many pages.

## Prices

Read from `config/prices.yaml`. `live: true` entries were read from the live price list; others are estimates and
show as `~` in budget.py. Re-check before a production's first spend.
