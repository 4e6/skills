---
type: Module
title: Dish photos
description: Where the host can draw, each dish gets a square photo beside its recipe's title. The renderer lists the dishes, names each photo for what it shows, embeds the bytes — or, to publish, links them — and never lets a bad photo cost the page.
tags: [architecture, rendering, photos]
sources:
  - resource: skills/training-week-meal-plan/references/photos.md
  - resource: skills/training-week-meal-plan/scripts/render.py
  - resource: skills/training-week-meal-plan/assets/plan.css
sources_digest: f187fa5560b8f4c2
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
- `--link-photos` beside `--photos` points at them instead, for a host that
  publishes the page with its photos beside it: the source is the list's path,
  percent-encoded, and every check above still runs, so a photo the embedded page
  would drop is dropped here too. The page must be written in the list's folder,
  and prints a `link` line per photo, the files to publish
  ([publishing a page with photos](/architecture/the-handover.md#publishing-a-page-with-photos)).

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
- **400 KB a photo, 10 MB a page, every card counted.** A 640 px square JPEG at
  quality 80 was 55–68 KB for the sample's eleven dishes, whose twenty-one cards
  came to 1.26 MB; scaled from the 80 KB once seen at 480 px, another tool's could
  reach 140 KB. The caps were 150 KB and 2 MB, which a week of those would have
  passed, dropping photos from a page that would have opened: a false alarm. The
  failure they guard against is the 48 MB page of raw PNGs a preview refused, so
  they are set to refuse that and nothing sized as asked — 21 cards at 400 KB is
  8.4 MB, and the cap a page of about 13.5 MB, under the 16 MB a Claude artifact
  may be. Where between 1.2 MB, which opened, and 48 MB a preview gives up is
  still unmeasured. `photos.md` specifies the photo — square, 640 px, about
  quality 80, asked for at that size rather than drawn larger and shrunk — and
  does not teach resizing: the standard library cannot, and a
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
times, the figures, the Makes line and the ingredients; the method starts
beneath, full width. **Two lines are kept whole where there is room** — the
times, and the figures — and that sizes the tile: **as large as it can be with both beside it on
one line**, the same on every card. At the paper's 176 mm measure — in print,
and on any screen wide enough for it — that is 80 mm; on a screen between that
and a phone, 60 mm. A phone has no room beside it, so there the photo heads the
card at the same 60 mm, the title under it and everything else running full
width. They are held on one line only on a screen, where the room was
measured, and may wrap in print rather than run off the card.

**A phone's photo was 26 mm beside the title until the athlete asked for it
larger.** Three were rendered at 390 px: 40 mm beside the title, 50 mm with the
times beside it too, and the full width of the card above the title. Beside
the title, 50 mm left a column narrow enough to break a title into four lines;
the full width, 360 px, made the recipes 20.4 screens long against 12.6. The
full-width layout capped at 60 mm, the tile the next screen size up shows, was
chosen: 227 px, and 16.9 screens.

Paper had 26 mm tiles in 84 mm columns until 2026-09-30, when the recipes went to
one column so the PDF would look like the screen. The athlete then asked for the
photos larger, 66 mm and on to 80 mm; 80 mm keeps both lines whole beside it
(91 mm against the figures' 85 mm), and costs pages — see
[what one column costs](/architecture/the-printable-page.md#what-one-column-costs).

It got there in steps, each on a rendered page: beside the title at 30 mm (three
blind readers found titles wrapping to four lines), under the title, then beside
it again and larger. An `<img>`, never a background, because print drops
backgrounds; `alt` is empty, because the title is beside it and plan text never
goes in an attribute. A card without a photo keeps exactly the markup it had.

**Every card.** The dish's photo is on its first cook, every repeat and every
leftover. A repeat prints whole, with or without photos
([a repeat reads as a first cook](/architecture/the-printable-page.md#a-repeat-reads-as-a-first-cook));
it once did only on a page with photos.

# What the skill tells the host

Step 6 names a capability — the tools and skills *that make a picture from a
written description* — never a host, and is worded so a host whose only tool is
Python does not try to plot a plate. It tells the host to **list** what it has
and read `photos.md` if anything is there. It once said *where your host can make
a picture*, which left the judgement to the host: in a real run an agent skipped
the photos without looking, though a local image skill was installed, and never
told the athlete. A condition about what the host can do is answered from memory;
a list is answered from the session. No tool is named, since one that exists on
one host is wrong on the next, and no example is given, as
[editing a skill](/conventions/editing-a-skill.md) allows only those every page
would accept. `photos.md` is loaded only where it applies:
draw only where step 4's check ran, whatever it found; one line to the athlete
first; square and top-down, describing the food and never the athlete; stop at
the first quota, rate-limit or billing error; render once — again only after
fixing a name that matched no dish or a photo over the cap, or with the photos
linked where step 7 publishes — one handover, never edit the page and never read
it back except where a publishing tool asks to read the linked copy; one line
in the report, and another whenever a page went out with none or fewer, with
the reason in a plain clause — nothing there makes pictures, the drawing
failed, or a quota ran out. It used to say nothing about photos where none
were drawn, so an athlete never learned a feature had been skipped; the
silence was right only while "no tool" meant a host that could not draw, and
it hid the host that did not look. Where there is no page — no Python, so
`photos.md` was never read — the reply says nothing about photos: there is
nothing to be missing from, and "nothing here makes pictures" would be false
of a host that was never asked. The reason names no tool, as the one line
before drawing does not.

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

**A real host, 2026-09-30.** Opus in Claude Code, drawing with
[Z-Image Turbo](/architecture/z-image-turbo-macos.md) on an M5 Pro: seven dishes
at 480 px took 279 s, each drawn at 1024×1024 and shrunk, plus 47 s to redraw one
whose count of bread rolls was wrong. That is why the photo became 512 px: drawn
at its own size it takes about 9 s. The page came to about 620 KB. The same day
the tile grew to 80 mm, which a Retina screen shows at about 600 device pixels and
paper at 200 dpi from 640, so the photo became 640 px: eleven dishes in 161 s,
about 14 s each, and the sample's page with them 1.75 MB.

**A smaller photo carries forward.** `have` tests a file's bytes and type, not
its size, so a dish drawn at 480 or 512 px for an earlier week is kept rather
than redrawn at 640, and is softer at 80 mm until its title or ingredients
change.

**Still open:** a dish cooked again repeats its photo on every card, and a page
where only some dishes got a photo looks uneven. Not measured: any other image
tool's output, and where between 1.2 MB and 48 MB a preview gives up.
