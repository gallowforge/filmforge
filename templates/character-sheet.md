# Character sheet spec: <handle>

One sheet per character, attached to every prompt the character appears in. The sheet is a measuring tool,
not a portrait: it must agree with itself, and it must carry scale.

## Identity (pasted word for word into prompts as the anchor)

<age, build, face, hair, eyes, skin, costume head to toe, colours, permanent markers>

## The sheet (one image, model and setting from the style lock)

- **Panels:** full body front, full body back, face close-up (dead-on, level), plus face and hand studies for a
  stylised character. Flat, even light on a plain mid-grey field so no lighting bakes in.
- **Scale bar:** the character drawn beside every character or prop they share frames with, at true relative size
  (a companion drawn too small is a repaint in every frame it appears: scale lives on the sheet and in the ledger,
  never in hope).
- **Expressions:** neutral, the film's key emotion, and its opposite.
- **Non-human characters:** a material sheet: what it is made of ("glowing embers, not fur, not glass"), a wrong-materials
  list, and how it moves.

## Locks (copied into continuity.yaml)

- handle: "<the visual handle>"
- anchor: "<the identity paragraph above, one sentence>"
- scale: "<a ratio to something always nearby>"
- never: <what must never change: a colour, a scar, which cheek the soot is on>

## Prompt for the sheet

```text
<style lock look, word for word>

A character reference sheet on a plain mid-grey background with flat, even, shadowless light. <panels>.
<identity paragraph>. <scale bar sentence>. No text, no labels anywhere in the image.

<avoid tail, word for word>
```

## Gate

Read at 100% (contact_sheet.py zoom): face, hands, costume markers, the scale bar. Accept, or repaint the sheet now:
every painting inherits its faults.
