# Looks and sheets

## Writing a look sentence

Five things, in this order, in one sentence: the medium and its pedigree ("a frame from a hand-painted storybook
film"), the line ("confident brush-ink outlines"), the colour ("deep night colours"), the texture ("soft gouache and
watercolour on rough paper, visible paper grain"), the light or faces ("light that comes only from lamps, embers and
the sky"). Point at the references ("in exactly the style of the attached sheets"). Test it on a proof frame; if
two proofs from the same sentence disagree, the sentence is too vague.

## The Lantern Moth (the worked example, 6 shots)

From `examples/the-lantern-moth/style-lock.yaml`:

- Model: GPT Image 2.5, high, 2K, 16:9 (`gpt-image-2.5-high-2k`, 2.75 credits a painting); paintings upscaled to 4K
  in post.
- Look: "A frame from a hand-painted storybook film, in exactly the style of the attached sheets: soft gouache and
  watercolour on rough paper, confident brush-ink outlines, visible paper grain, deep night colours, light that
  comes only from lamps, embers and the sky."
- Avoid: "Avoid: 3D render, CGI, photorealism, anime, plastic, text, letters, signatures, watermark, extra fingers,
  distorted faces."
- References per prompt: one sheet per character (the girl in the red knitted hood; the ember moth) and one plate
  (the headland, the lighthouse and the sea, reused by s01, s05 and s06). Each prompt names which ones it attaches,
  and `style-lock.yaml` says what each one governs.
- Lens: framed like a 35 mm lens at eye height unless the shot says otherwise; no fisheye, no tilt.
- Colour rule: "Absolutely no warm gold light anywhere in the frame." in every prompt before the lamp is lit (s05).
- The lesson it carries: s03's prompt lost the moth's scale lock, the fault that paints a companion too small. The
  sheet carries a scale bar and the ledger a scale lock, and `ledger.py prompts` refuses the prompt before a credit
  is spent.

## Two looks (when the drawing carries the story)

- One model and setting for both; only the look sentence changes.
- LIVING: the house style in full: flowing, hand-drawn lines with their construction left visible, flat graphic
  shapes, layered watercolour with paper grain, rich colour.
- FROZEN: the same style with every line ruled straight: grey hatching, flat perspective like a carved print,
  a narrow palette of slate and bone; only the main characters keep their own colours.
- Each shot picks its look with `look:` in the shot list; `ledger.py prompts` checks that the prompt opens with
  that look, word for word.

## A picture book

- Model: a cheaper setting is fine because pages are seen smaller and still (`gpt-image-2.5-medium-2k`, 1.0 credit,
  an estimate in prices.yaml); vignettes can have transparent backgrounds.
- Faces: big expressive eyes, small noses, soft round faces, emotions readable from across a room.
- Layout in every prompt: a spread (3:2), a page (3:4) or a vignette (1:1), and the text area named ("keep the
  upper third quiet: pale winter sky for text"). All words set in the page, never painted.
- Its quality gate, five points: faces match the references; the right look and the colour-script colours; the text
  area really calm; the page's motif present; it makes you feel the line of text it sits with.

## A material sheet (non-human character)

For a creature or an object-character, identity is its material. Write what it is made of, how the material
behaves in light, and a wrong-materials list. Example (The Lantern Moth):
"a moth made of glowing embers, wings like cooling coals veined with thin gold, two black bead eyes"; wrong
materials: fur, felt, glass, plastic, metal; motion: it flickers rather than flies. Motion that belongs to the
material is scoped to the character only, never to the camera or the world.

## A character sheet prompt (template)

```text
<look sentence>

A character reference sheet on a plain mid-grey background with flat, even, shadowless light: full body front,
full body back and a face close-up, all dead-on and level, plus studies of both hands. <anchor sentence>.
Beside her, at true relative size, <the companion>: <scale lock>. No text, no labels anywhere in the image.

<avoid tail>
```
