# The prompt grammar

Twelve slots, always in this order, as plain paragraphs (no slot labels in the prompt itself). Every image prompt
in a production follows it: sheets and plates use the slots that apply.

## Rules per slot

1. **LOOK**: the style lock's look, character for character. `ledger.py prompts` fails a prompt that does not open
   with it (whitespace and quote style are normalised; words are not).
2. **REFERENCES**: one clause per attachment, in attach order, saying what it governs and what it does not ("the
   attached plate governs the headland and the sea, nothing else"). End with the relight clause.
3. **SHOT**: framing size from the shot list, camera height, lens feel, and placement on thirds. Write positions in
   frame terms ("on the left third"), never "her left" unless you mean the character's own left.
4. **SUBJECT AND SCALE**: each character as handle, anchor, then scale lock, word for word from the ledger. Give
   sizes as ratios to something in frame. State counts exactly ("exactly one boat", "a hundred small ember moths
   on the lamp glass").
5. **MOMENT**: one instant, not a sequence. The emotion as something visible: a jaw set, eyes on a hand.
6. **SETTING**: place, weather, time of day; what the background holds; what it must not hold.
7. **LIGHT**: direction, quality and temperature, and where the light comes from in the world (a lamp, embers, the
   sky). Never a studio fixture.
8. **COLOUR**: the colour-script words for this scene.
9. **TEXT AREA**: only when words will be set over the painting: name the area and what fills it ("keep the upper
   third quiet: pale winter sky for text"). All words are set in post, never painted.
10. **CONTINUITY**: each prop and state the ledger lists for this shot, word for word.
11. **LOCKS**: each forbidden-colour clause that covers this shot, word for word; any negation specific to this
   shot ("the great lens stays dark and cold").
12. **AVOID**: the avoid tail, character for character, last.

## House rules

- Handles, not names. Names are listed in the ledger's `names:` and the lint fails a prompt that contains one.
- No aspect ratio in the prompt; it is a model setting.
- No meta-commentary ("this is for a film about..."). Every word should change a pixel.
- Under the style lock's `max_chars` (3500 by default): long prompts dilute the lock.

## A full prompt, annotated (The Lantern Moth, s02)

```text
A frame from a hand-painted storybook film, in exactly the style of the attached sheets: soft gouache and
watercolour on rough paper, confident brush-ink outlines, visible paper grain, deep night colours, light that comes
only from lamps, embers and the sky.                                                           <- 1 LOOK

References: the attached sheet of the girl in the red knitted hood governs her face, hood, coat and proportions;
the attached sheet of the ember moth governs its material, wing shape and size. Relight both to this scene; do not
copy the sheets' flat light.                                                                   <- 2 REFERENCES

A medium shot inside the cold lamp room at the top of the lighthouse, the great dead lens filling the right half
of the frame.                                                                                  <- 3 SHOT, 6 SETTING
Kneeling at its wick on the left third is the girl in the red knitted hood, a nine-year-old girl, small for her
age, in a red knitted hood, an oversized rust oilskin coat to her shins and black rubber boots.  <- 4 handle + anchor
A spent match smokes between her fingers, and there is a smudge of soot on her left cheek.     <- 10 state
On the floor at her knee stands a small brass hand-lantern with one cracked green pane;         <- 10 prop
inside it, the ember moth, a moth made of glowing embers, wings like cooling coals veined with thin gold, two black
bead eyes, is just beginning to glow; its wingspan equals a child's open hand, never smaller than a palm and never
larger than a face.                                                                            <- 4 handle + anchor + scale

The moment: the match has just died; she has not yet noticed the glow at her knee.            <- 5 MOMENT

Light: cold blue-grey moonlight through the lamp-room windows from the left; the moth's small orange glow from the
lantern, low and right, warming only the underside of her face.                               <- 7 LIGHT

Colours: slate and ink; the moth's ember orange is the only warm colour.                       <- 8 COLOUR

Absolutely no warm gold light anywhere in the frame.                                           <- 11 LOCKS

Avoid: 3D render, CGI, photorealism, anime, plastic, text, letters, signatures, watermark, extra fingers,
distorted faces.                                                                               <- 12 AVOID
```

## The same grammar fixing a fault (The Lantern Moth, s03's repaint)

s03's first prompt left the moth's scale lock out of slot 4 (`ledger.py prompts` flags it), and in the example's QA
notes the painting drew the moth as a spark above her hand. Frame QA's corrected prompt (in `qa.yaml`) changes three
things and nothing else:

- slot 4 gains the scale lock word for word ("its wingspan equals a child's open hand, never smaller than a palm and
  never larger than a face"), and a ratio to something in frame: "the moth is the second-largest shape in the frame
  after her face";
- slot 3 moves her open palm up close to the camera on the right third, so the moth sits where the eye lands;
- slot 10 keeps the prop the ledger carries in view: "at the lower right, a small brass hand-lantern with one
  cracked green pane stands on the floor".

The look, the references, the light, the colour, the lock and the avoid tail stay word for word, so the repaint
still belongs to the same film as s02 and s04.
