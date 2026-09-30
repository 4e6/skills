---
type: Module
title: The printable page
description: render.py writes one self-contained HTML file for print, a phone and a wide screen. Plain rules, weight and space; the glance first; one column that never splits a recipe; a byte-compared example.
tags: [architecture, rendering]
timestamp: 2026-09-30T17:59:25Z
sources: [skills/training-week-meal-plan/scripts/render.py, skills/training-week-meal-plan/assets/plan.css, skills/training-week-meal-plan/examples/**]
source_commit: 36cd180908e7f0820c5f9881c1f3ddf776de7eb9
---

# One file, and Cmd-P

The plan is a document before it is a file: the athlete carries it into a
kitchen and a shop. A typesetting engine cannot travel with the skill and the
sandbox has no network to fetch one, so `render.py` writes **one self-contained
HTML file** with `assets/plan.css` inlined, and the athlete prints it. One file
because it gets mailed and copied to a phone, and a sidecar asset is a broken
document on arrival. Photos, where there are any, are data URIs for the same
reason ([dish photos](/architecture/dish-photos.md)).

HTML gains one thing over paper: a link is live. Three links under the title jump
to the week, the recipes and the shopping list; a repeat's *where the method is*
links to the recipe that has it; every dish on the glance with a recipe links to
it, and a side with none prints plain. On a wide screen the rail beside the page
carries the same links and the glance's again ([a wide screen](#a-wide-screen-is-the-paper-with-the-week-beside-it)).
**An id is a position or a fixed word, never plan text**: `recipe-<n>` and `day-<n>`, and the parts' own `glance`, `week`, `recipes` and `shopping`.

# A plain design, and why plain is load-bearing

One system typeface, no cover, **no background fill that prints**: browsers drop
backgrounds when printing unless the reader has turned that on, so a design made
of tints is one the commonest printer throws away. This one is made of rules,
weight and space. A faint panel behind a recipe's figures was tried once and
taken out — it drew more attention than two reference lines should.

Print is the target:

- **A4, with a measure capped below the page area**, so Letter is a different
  amount of white space rather than a different document.
- **Page one is the masthead and the glance, nothing else**; the week starts a
  page.
- **Recipes print in one column, as a wide screen shows them** — the full
  176 mm, the ingredients in two columns, a photo at 80 mm with the method
  beneath it. They printed in two flowing 84 mm columns until 2026-09-30, which
  saved paper and read differently from the screen; an athlete asked for the PDF
  to look like the page. See [what one column costs](#what-one-column-costs).
- **No break inside a recipe**, in both the modern and the legacy spelling. It is
  an avoid, not a guarantee: a recipe taller than a page splits anyway.
- **A long word breaks anywhere in a recipe**, in every medium. The two print
  columns carried the rule, and when they went it went with them: a review
  caught a 150-character address in a method losing 47 characters past the
  page's edge, clipped without a word.
- **A dot before each ingredient**, so the list reads as one: a character, since
  the list's own marker hangs in the gap of a two-column list and a drawn circle
  is a fill. Screen readers are given empty text for it.
- **No break directly after a day band**, and deliberately no rule keeping a
  day's recipes together — nothing bounds their height, so the rule would buy a
  hole and the split as well.
- **A day's snacks print after its meals**, as a line of the same kind as a
  session's fuel — a small-caps label, the range, then *e.g.* and the food.
  They cost the example a page: the week runs onto a third, and the example
  prints nine pages where it printed eight.
- **The shopping page starts a page of its own**, and opens with the fridge,
  which is read before leaving.

# A phone is the other reader

Measured before it was designed for: at 390 px the page was fourteen screens
with the list at the end, values squeezed to 160 px, and both two-column lists
breaking mid-row. The fix is CSS, no script:

- **One narrow rule, tied to the sheet rather than a device** — whenever the
  sheet cannot show at its full width (176 mm plus padding). Below it both lists
  are one column and each label sits above its value. Scoped to `screen`, so
  printing from a phone is still A4.
- **A box to tick on each shopping row** — a native checkbox wrapped with the row
  in a label, no name, no form, cleared on reload. In print it is an empty ruled
  square for a pen, sized explicitly, because a box with its appearance removed
  prints as a dot. The fridge list has none: nothing on it is bought.
- **Links in the text's black in every medium**, or they print blue.

Not exercised: a real phone viewer. Preview surfaces — a mail attachment, a file
manager, an artifact panel — may make the links and boxes inert, and the page
then degrades to its text.

# Page one is the week at a glance

Printed, the page ran to ten sheets and more, with the week on the first three, and a
reader wanted *one page that fits the fridge*. So page one is a table: a row per
day, the day's training and its breakfast, lunch and dinner by name.

- **Names only**, and nothing computed — no day total, because the plan states
  none. Portion notes would double a row read from across a kitchen.
- **A row per day the plan covers**, never seven.
- **The week starts page two**, so pinning page one takes nothing from the stack.
- **Nothing holds the table whole.** Keeping it together moved it off page one and
  left the masthead alone there, so step 6 says the glance *comes first*, not that
  it *is* page one.
- **Hidden on a phone**, where five columns do not fit. That is a loss: a phone
  gets neither the grid nor its links.
- **Shown on a wide screen as well as in the rail.** The rail was first built to
  replace it there, and the athlete asked for it back: it is page one of the
  paper, and the screen is the paper.

Measured over eleven plans printed from Chrome, the glance costs about a page, and
the two-column recipes of the time paid it back, with one or two pages to spare
on nine of the eleven; the example went from ten to eight. Four simulated readers, reading blind, all
found Thursday's dinner and training on page one (one of four before), and rated
the sheet to pin 4.0 against 2.75. **What they said against it:** all four wanted
the batch notes on the glance, three the session fuelling, and three asked for
page numbers. Two judges found one wide column easier at the stove, since a
method line wraps more in an 84 mm column, and columns end unevenly, with a hole
up to one recipe tall — the price of never splitting a recipe. One column is what
the page prints now.

# What one column costs

Printed from Chrome, the sample:

| | Two columns | One column |
|---|---|---|
| without photos | 9 pages | 10 |
| with photos, 60 mm on screen, 26 mm on paper | 10 | — |
| with photos, 80 mm everywhere | — | 15 |

A card with an 80 mm photo is about 105 mm tall, so a 267 mm page holds two; the
method under the photo is what sets that height. Tried and turned down for the
screen's sake: the method **beside** the photo (66 mm, 12 pages, a card reads as
one block but the method runs narrower than the screen's) and a 52 mm photo on
paper only (12 pages, paper and screen differ). The athlete chose paper that is
the screen, at three more sheets.

# A wide screen is the paper, with the week beside it

A page that fitted a phone and an artifact panel was a narrow strip on a desktop.
The fix keeps the one column and spends the width on two things, CSS for the
layout and one element from `render.py`:

- **The paper's measure wherever it fits**, from about 790 px: the sheet grows
  to 176 mm of text, and the card is the printed card, photo at 80 mm. Between a
  phone and that, nothing changed — laid out element by element at 390 px and
  700 px, the old and new pages were identical, before the ingredient dots
  below were added at every width.
- **A rail beside the sheet from 1180 px**, sticky, with its own scroll when the
  week is taller than the window: the parts of the page, then each day with its
  training and dishes, the day linking into the week and a dish to its recipe.
  It is built from the glance's own cells, so the two cannot name a meal
  differently. It hides the links under the title; it is hidden in print and
  on narrower screens. 1100 px was tried first and scrolled sideways.
- **Kept to one column.** Wider layouts were built and shown first — recipes two
  or three across, day cards in a grid — and turned down: a grid leaves holes
  under the shorter card, and the athlete wanted the recipes as one column
  under the week.

# The Makes line is the pot, counted in portions

A batch's card used to say where it was eaten and not how much, and an athlete
asked why the recipe said 200 g and the list bought 600. It now leads with the
pot: `Makes 6 portions: Friday Lunch (2); Saturday Lunch (2); Sunday Dinner (2)`.
Only an origin carries it. Shares print as decimals, matching the meta line.
`one portion: …` prints only where the shares are uneven.

**The total is withheld whenever it would be anything but the pot the list is
scaled to** — a missing pot, the origin's own sitting absent from its servings, a
sitting named twice or excluded, or a plate that is not a positive whole number
of quarters (which binary floating point adds exactly). Withheld, it falls back
to `Makes: A; B` with its brackets. The list's scale and the line read one
function's pot, so they cannot disagree.

# Emphasis is the one markup that travels

The renderer parses exactly two inline patterns, bold and italic, so the
committed example does not print raw asterisks. **Escaping runs before the
substitution**, and the order is the security property: afterwards the only
angle brackets are the ones the substitution inserts, so a dish name containing
markup cannot become markup. The document title takes the escape alone. **An id
is a position, never words** — `recipe-<n>` — because a title would need case
mapping to become an id, and plan text never goes in an attribute.

# The example is compared byte for byte

`examples/sample-plan.html` is meant to be exactly what `render.py` produces
from `examples/sample-plan.json`, byte for byte, so the committed example is the
page that ships. Nothing in this repository checks it yet
([which copy is the source](/questions/which-copy-is-the-source.md)). A byte comparison is worth what its determinism is worth,
so the hazards are pinned: no set is iterated (string hashing is seeded per
process), nothing is sorted (collation is locale-shaped), no case mapping reaches printed text or an id (the Unicode database moves between
versions; the one lowercasing, of names to look up a pack, is compared and never
printed), arithmetic is
only of the kind that gives the same result on every platform, with every
fraction printed as its shortest round-tripping `repr`, and there is no
timestamp, date or generator string. The file is written with an explicit
encoding and a `\n` newline. A page with photos keeps all of it. `.gitattributes` pins
the committed example to LF, so a checkout that converts line endings cannot
break the comparison.

**Regenerate the example whenever the renderer or the stylesheet changes**, and check that it re-renders identically on Python 3.9 and on a current Python.

# The stylesheet is its own design

`plan.css` answers to nobody else's design. It is deliberately plain, and the
rules above are its specification. How a change
to it is judged is by printing and reading it
([editing a skill](/conventions/editing-a-skill.md#judging-a-change-to-the-page)).
