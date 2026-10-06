# A photo of each dish

Only where your host has a tool that makes a picture from a written description.
Drawing one with code, a plotting library or an SVG is not that: skip this file.
And only where step 4's check ran, whatever it found: without Python there is no
page to put a photo on, and every drawing would be spent for nothing.

This happens inside step 6, before its command: list the dishes, say one line,
make the photos, then render once with the photos added.

## Which dishes, and the list

One photo per dish that has its recipe, by its title; every card for that dish
shows it, the day it is cooked again and its leftovers too. Let the renderer
write the list, from the plan in your working directory, rather than typing
titles, since a title has to match the plan exactly:

```
python3 <this skill's directory>/scripts/render.py <the plan's file> photos.json --list-photos
```

It writes `photos.json` beside the plan, naming the dishes the page will print,
makes a photos folder beside it, and prints one line per dish: draw or have, the
path, and the title. Draw only the dishes marked draw, and save each at its
path. A dish marked have is already drawn: the same dish, with the same
ingredients, drawn before for this plan or an earlier one. A draw at a path
where a file already is means that file will not do, and the command says why:
fix that before drawing it again. A path never drawn is a file that is not
there, and that dish simply has no photo. If it exits 2, read
the message: it is the plan, or where you asked for the list, and the page is
still yours to render without photos.

## Say one line, then draw

Before the first drawing, tell the athlete in one plain line that you are drawing
a photo of each dish for their page and that it takes a few minutes. Name no
tool, file or step. Nothing else until step 7.

Draw each dish from its own recipe, never from the athlete: no weight, no name,
no diet. Ask for a square picture where the tool takes a size.

```
Food photography, top-down view, square: {what is on the plate, naming the ingredients you can see}. Rustic ceramic plate or bowl, natural daylight, clean wooden table, minimal styling, soft shadows, magazine quality, no text, no logos.
```

A drawing that fails is left out. At the first quota, rate-limit or billing
error, stop drawing and render with what you have.

## What each photo is

- **Square, 640 by 640 pixels**, cropped to the plate's centre if it was drawn
  another shape. Ask for that size where the tool takes one, rather than a
  larger picture shrunk afterwards.
- **A JPEG at about quality 80**, which comes to about 55 to 70 KB. PNG and WebP are
  read too, but a photo saved as PNG is usually over the cap.
- **At most 400 KB each, and 10 MB together**, a photo counted once for every card
  that shows it: the page is one file, and a heavy one will not open in a
  preview.
- **At the path the list gave it.**

Make them that way with whatever your host already uses for pictures; install
nothing. Make the first one before drawing the rest: if it comes out over 400 KB
and your host cannot make it smaller, stop, and the page goes out without
photos. A photo that is too big is left off the page, and the command says
which.

## Render once

Run step 6's command with `--photos photos.json` added at the end. It exits 0
even when a photo is left out, and says which one and why. Render once more only
when what it said is a name that matched no dish or a photo that was too big,
and only after fixing exactly that. Otherwise do not draw again or render again.

There is one page and one handover. Never edit the page, and never read it back
to check it: it is mostly the photos' bytes. Step 7 may render it once more with
the photos linked rather than carried, to publish, and that copy is small
enough to read where a publishing tool asks to. Hand it over as step 7 says. An
exit 2 is the command or the plan, never a photo: step 6's four messages, or a
usage line if the list's name went missing.

## In the report

One line in step 7: the photos were made for this plan, so they show the idea
of each dish rather than their plate. If there is a page and it went out
with none, or with fewer than the dishes, say so in one more plain line, and why: nothing here
makes pictures, the drawing failed, or a quota ran out. Name no files and quote
none of what the command said.
