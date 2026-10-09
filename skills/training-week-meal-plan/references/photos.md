# A photo of each dish

Use this only where your host has a tool that makes a picture from a written
description. Drawing with code, a plotting library or an SVG is not that: skip
this file.

Use it only where step 4's check ran, whatever it found. Without Python there is
no page to put a photo on.

This happens inside step 6, before its command:

1. List the dishes.
2. Say one line.
3. Make the photos.
4. Render once, with the photos added.

## Which dishes, and the list

One photo per dish that has a recipe, by its title. Every card for that dish
shows it, including its repeats and leftovers.

Let the renderer write the list. Titles must match the plan exactly.

```
python3 <this skill's directory>/scripts/render.py <the plan's file> photos.json --list-photos
```

It writes `photos.json` beside the plan, makes a photos folder beside it, and
prints one line per dish: draw or have, the path, and the title.

- Draw only the dishes marked draw. Save each at its path.
- **have** means the same dish, with the same ingredients, was drawn before for
  this plan or an earlier one.
- A draw at a path where a file already is means that file will not do. The
  command says why. Fix that before drawing again.
- A path never drawn is a dish with no photo.
- If it exits 2, read the message. It is the plan, or where you asked for the
  list. Render the page without photos.

## Say one line, then draw

Before the first drawing, tell the athlete in one plain line that you are
drawing a photo of each dish for their page and that it takes a few minutes.
Name no tool, file or step. Say nothing else until step 7.

Draw each dish from its own recipe, never from the athlete: no weight, no name,
no diet. Ask for a square picture where the tool takes a size.

```
Food photography, top-down view, square: {what is on the plate, naming the ingredients you can see}. Rustic ceramic plate or bowl, natural daylight, clean wooden table, minimal styling, soft shadows, magazine quality, no text, no logos.
```

- A drawing that fails is left out.
- At the first quota, rate-limit or billing error, stop drawing and render with
  what you have.

## What each photo is

- **Square, 640 by 640 pixels.** Crop to the plate's centre if drawn another
  shape. Ask for that size where the tool takes one. Do not shrink a larger one.
- **A JPEG at about quality 80,** about 55 to 70 KB. PNG and WebP are read, but a
  PNG is usually over the cap.
- **At most 400 KB each and 10 MB together.** A photo counts once for every card
  that shows it. The page is one file, and a heavy one will not open in a
  preview.
- **At the path the list gave it.**

Use whatever your host already uses for pictures. Install nothing.

Make the first photo before the rest. If it is over 400 KB and your host cannot
make it smaller, stop. The page goes out without photos. A photo that is too big
is left off the page, and the command says which.

## Render once

Run step 6's command with `--photos photos.json` added at the end.

- It exits 0 even when a photo is left out, and says which and why.
- Render again only when it named a name that matched no dish or a photo that was
  too big, and only after fixing exactly that.
- Otherwise do not draw again or render again.

There is one page and one handover.

- Never edit the page.
- Never read it back to check it. It is mostly the photos' bytes.
- Step 7 may render it once more with the photos linked rather than carried, to
  publish. That copy is small enough to read where a publishing tool asks.
- An exit 2 is the command or the plan, never a photo: step 6's four messages, or
  a usage line if the list's name went missing.

## In the report

One line in step 7: the photos were made for this plan, so they show the idea of
each dish rather than their plate.

If the page went out with no photos, say why in one more plain line. Name no files
and quote none of what the command said.
