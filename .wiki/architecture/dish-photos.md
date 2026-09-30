---
type: Module
title: Dish photos
description: Where the host can draw, each dish gets a square photo beside its recipe's title. The renderer lists the dishes, names each photo for what it shows, embeds the bytes, and never lets a bad photo cost the page.
tags: [architecture, rendering, photos]
timestamp: 2026-09-30T14:00:00Z
sources: [skills/training-week-meal-plan/references/photos.md, skills/training-week-meal-plan/scripts/render.py, skills/training-week-meal-plan/assets/plan.css]
source_commit: e71d6a4eac78ebe897dd9abea3f82f6815e160b5
---

# Why the renderer does it

Asked for a picture of each dish after running the skill, one host drew thirteen
images in seven and a half minutes and **pasted `<img>` tags into the finished
page by hand** — so the page handed over was no longer the renderer's. The images
were the tool's own PNGs at about 2.4 MB each, the page came to 48.3 MB and the
host's own preview refused it (at 640 px JPEGs it was 1.2 MB and opened). And the
layout was a short strip across each recipe with `object-fit: cover` over images
of mixed shape, which crops the rim of every plate and the top of every bowl.

So photos are a feature of the page, done by the renderer, and **the page's first
page — the week at a glance — never carries one.**

# The interface is a list

The plan, its schema and `validate.py` are untouched: a photo is a fact about the
page, not the plan.

- `render.py plan.json photos.json --list-photos` **writes the list**, a JSON map
  from each dish the page prints to a path for its photo, and prints on stdout
  whether each is `have` or `draw`. It
  began as a one-liner in `photos.md`, which drifted from the renderer twice — it
  named a dish the page drops, and broke on a non-UTF-8 host. Both were the
  renderer's knowledge already.
- `render.py plan.json page.html --photos photos.json` embeds them. A path is
  read only if it is relative, has no `..` and resolves inside the list's folder —
  the photo's counterpart of escaping plan text.

**A photo is named for what it shows, never its position** — a short digest of
the dish's title and its first cook's ingredients, the two things a drawing is
made from. `3.jpg` means whichever dish is third, and four other answers failed
in one review cycle: a date check, a folder per plan, a fresh folder per list,
and the title alone (which kept a stir-fry's chicken picture after it swapped to
tofu). Named for its content, an unchanged dish finds its drawing in another
week, and a changed one gets a path nothing was drawn at. `have` only where the
page's own test of that file passes, so an empty, wrong-kind or oversized file is
drawn again. Nothing is deleted or dated.

# What a photo may be

- **The bytes decide the type** — JPEG, PNG or WebP, read from the first bytes,
  size from the header. Anything else, the plan named by mistake included, is
  never embedded in a page that may be published.
- **150 KB a photo, 2 MB a page, every card counted.** A 480 px square JPEG at
  quality 80 is 45–80 KB. The page cap has no measured basis beyond one preview
  opening 1.2 MB and refusing 48 MB. `photos.md` specifies the photo — square, 480 px, about
  quality 80 — and does not teach resizing: the standard library cannot, and a
  host that draws usually sizes its pictures too. The host that cannot is caught
  before it spends the week: the first photo is made and checked before the rest,
  and one too big with no way to shrink it stops the drawing.
- **A photo never costs the page.** Anything wrong — unreadable, wrong kind, too
  big, past the total, a key naming no dish — is a warning on stderr and that dish
  has no tile; the exit is 0. A photo that is not square gets a warning, and the
  tile shows its centre. Warnings print after the page is written, and none
  says *could not*, which is the exit-2 messages' phrase.

# The layout

The photo floats at the start of the card; the title sits beside it, then the
day and times, the figures, the Makes line and the ingredients; the method starts
beneath, full width. **Two lines are kept whole where there is room** — day · meal · times, and the
figures — and that sizes the tile: **as large as it can be with both beside it on
one line**, the same on every card. On a wide screen that is 60 mm; in print and
on a phone, 26 mm, with both lines running full width beneath. They are held on
one line only on a wide screen, where the room was measured, and wrap in print
and on a phone rather than run into the next column.

It got there in steps, each on a rendered page: beside the title at 30 mm (three
blind readers found titles wrapping to four lines), under the title, then beside
it again and larger. An `<img>`, never a background, because print drops
backgrounds; `alt` is empty, because the title is beside it and plan text never
goes in an attribute. A card without a photo keeps exactly the markup it had.

**Every card, and a repeat printed whole.** The dish's photo is on its first
cook, every repeat and every leftover. On a page with photos a repeat prints its
own amounts and the first cook's method, so the card cooked from on the day is
complete. A page without photos keeps its repeats as pointers.

# What the skill tells the host

Step 6's pointer names a capability — *where your host can make a picture from a
written description* — never a host, and is worded so a host whose only tool is
Python does not try to plot a plate. `photos.md` is loaded only where it applies:
draw only where step 4's check ran, whatever it found; one line to the athlete
first; square and top-down, describing the food and never the athlete; stop at
the first quota, rate-limit or billing error; render once — again only after
fixing a name that matched no dish or a photo over the cap — one handover, never
edit the page; one line in the report, and another only if the athlete was told
photos were coming and the page went out with none or fewer. A host that drew
none says nothing about photos.

# Measured, 2026-09-29

On three plans printed from Chrome, no recipe split in any print and page one is
the same raster with and without photos. The final layout added one or two pages
— the sample's porridge is cooked four times, and each card now carries the
method.

37 simulated host runs, all reading an earlier `photos.md` with resize recipes
and a hand-built list; the current text is unmeasured beyond the rule to make the
first photo and stop if it cannot be shrunk. Every Opus host that could draw and
shrink produced a page
byte-identical to re-rendering its own plan and list, every prompt square and
top-down with no weight or name, and stopped at the first quota error. A host
that could not shrink drew one, stopped and said so. **No host that could not
draw drew anything.** After the pointer was made bold, Sonnet drew; Haiku still
skipped it.

**Still open:** a dish cooked again repeats its photo on every card, and a page
where only some dishes got a photo looks uneven. Not measured: how long drawing
takes on a real host, and a real image tool's output.
