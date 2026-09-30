---
type: Module
title: The printable page
description: render.py writes one self-contained HTML file for print and a phone. A plain design made of rules, weight and space, the week at a glance first, recipes that never split, and a byte-compared example whose determinism is engineered.
tags: [architecture, rendering]
timestamp: 2026-09-30T14:00:00Z
sources: [skills/training-week-meal-plan/scripts/render.py, skills/training-week-meal-plan/assets/plan.css, skills/training-week-meal-plan/examples/**]
source_commit: 4757fa27aade35d4ca5a676123a3c9c0eb45d9e3
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
it, and a side with none prints plain.

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
- **Recipes print in two flowing columns** — on a screen they are one scroll.
  The whole section flows, because each day on its own was measured worse, and
  the engine packs rather than `render.py`, which cannot measure a recipe and
  must not reorder them. **The RECIPES heading sits outside the column box**:
  spanning it across columns stranded it at the foot of a page, because Chrome
  does not carry `break-after: avoid` across a spanning element.
- **No break inside a recipe**, in both the modern and the legacy spelling. It is
  an avoid, not a guarantee: a recipe taller than a column splits anyway.
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

Measured over eleven plans printed from Chrome, the glance costs about a page and
the columns pay it back, with one or two pages to spare on nine of the eleven;
the example went from ten to eight. Four simulated readers, reading blind, all
found Thursday's dinner and training on page one (one of four before), and rated
the sheet to pin 4.0 against 2.75. **What they said against it:** all four wanted
the batch notes on the glance, three the session fuelling, and three asked for
page numbers. Two judges found one wide column easier at the stove, since a
method line wraps more in an 84 mm column, and columns end unevenly, with a hole
up to one recipe tall — the price of never splitting a recipe.

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
