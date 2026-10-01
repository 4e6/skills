---
type: Module
title: The printable page
description: render.py writes one self-contained HTML file for print, a phone and a wide screen. Plain rules, weight and space; the glance first; one column that never splits a recipe; a byte-compared example.
tags: [architecture, rendering]
timestamp: 2026-10-01T18:15:00Z
sources: [skills/training-week-meal-plan/scripts/render.py, skills/training-week-meal-plan/assets/plan.css, skills/training-week-meal-plan/examples/**]
source_commit: 5bb4c77a5a1a342bc78b138597f2e5b6cc7a7c99
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
to the week, the recipes and the shopping list; a leftover's *Leftover from
Monday Dinner* links to the card that cooked it, whose band reads the same words;
every dish on the glance with a recipe links to
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
- **No break directly after a sitting's band**, and deliberately no rule keeping a
  day's recipes together — nothing bounds their height, so the rule would buy a
  hole and the split as well.
- **A day's snacks print after its meals**, as a line of the same kind as a
  session's fuel — a small-caps label, the range, then *e.g.* and the food.
  They cost the example a page: the week runs onto a third, and the example
  prints nine pages where it printed eight.
- **The shopping page starts a page of its own**, and opens with the fridge,
  which is read before leaving.
- **The aisle headings are the athlete's shops'.** A list weighed in US units
  prints *Produce*, *Canned Goods, Jars & Seasonings*, *Meat & Seafood* and
  *Dairy, Eggs & Refrigerated*; every other list prints the categories as the
  plan writes them. See [the aisles](#an-aisle-is-a-key-and-the-page-names-it).

# An aisle is a key, and the page names it

`shopping[].category` is a fixed list of seven British headings in the schema,
and the page printed it as written, so a US list bought `Canned black beans —
27 oz` under *Tins, Jars & Seasonings* in all six US runs of 1.2.0
([#20](https://github.com/4e6/skills/issues/20)). The skill's text could not
reach it: a model told to write *Canned Goods* fails the schema.

**The plan keeps writing the seven keys, and `render.py` prints a US shop's name
for four of them** (*Bakery*, *Rice, Pasta & Dry Goods* and *Frozen* read the
same there). Two others were turned down:

- **A second set of names in the enum** would let one list mix *Produce* with
  *Dairy, Eggs & Chilled*, and the walking order would have to cover both.
- **Neutral names everywhere** (*Cans, Jars & Spices*) change every metric page
  too, and *cans* reads no better to a British shopper than *tins* to an
  American one.

**The page reads the country from the units**, since the skill already picks
the units by country ([which countries](/questions/which-countries-the-intake-offers.md)):
a list whose rows are weighed more in ounces, pounds, cups, pints, quarts and
gallons than in grams and litres is a US list. Counted rather than read off the
first row, so one stray `500 ml` does not turn a list British; a tie, or a list
of counts and spoons, keeps the plan's own words. A field naming the system was
the alternative, and turned down because it is one more thing a model can leave
out, and when it did the headings would go back to British. Liberia and Myanmar
weigh in US units too, so their lists get the US names; no run has planned for
either.

A list written into the reply, where there is no page, names its aisles the
same way (`fuelling.md`).

# A drained can is counted first

A row the recipes drain prints the count of containers as its amount and the
weight after it: `Canned black beans 2 cans (18 oz drained)`, where every other
counted row reads `Tinned tomatoes 800 g (2 tins)`. The weight on such a row is
what the recipes take, not what any label says, so printed first it read as a
can size ([the list buys what the week uses](/invariants/the-list-buys-what-the-week-uses.md#a-count-of-the-purchase-is-not-a-second-amount)).
**Whether the food drains is read off the recipe lines**, a line whose head is
the row's name and whose words after the comma say *drained*, matched the way a
line finds its pack, and not where they say *not drained*. **Only a row whose
`pack` names a container is turned round**: a recipe drains spaghetti and
boiled potatoes too, and their rows are weighed as bought, so marking every row
a line drains would call a dry weight a drained one. A list written into the
reply marks the weight too (`when-there-is-no-page.md`).

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

| | Two columns | One column | One column, a band per sitting |
|---|---|---|---|
| without photos | 9 pages | 10 | 12 |
| with photos, 60 mm on screen, 26 mm on paper | 10 | — | — |
| with photos, 80 mm everywhere | — | 15 | 15 |

A page without photos also prints every repeat whole now, which costs it nothing
more; the bands cost the two pages.

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

# Every sitting has a band

Scrolling through the recipes, an athlete could not tell breakfast from dinner:
the day had a band, and the meal was the second word of a 9 pt caption under the
title. Four designs were rendered and compared — the meal as a label above the
title, as headings under the day's band, in front of the title, and a band for
every sitting — and the athlete chose the last: **the day on the left, the meal
on the right, one band per sitting**, stuck to the top of the window until the
next sitting's band pushes it off.

- **Why one line**: only a band that sticks keeps the answer on screen while the
  method is being read, and one line does it where the day-and-meal headings
  took two, a fifth of a phone's screen.
- **What it costs**: the day repeats on every sitting, and two pages on a page
  without photos ([what one column costs](#what-one-column-costs)).
- **The line under the title keeps only the times**, and a size only where the
  Makes line cannot say it: the band says the day and the meal.
- **A main and its side share one band.**
- **A day away repeats its reason under each of its bands**, where a dish is
  kept on it for a later leftover: each band is read on its own, stuck to the
  top of the window or heading a printed page.

# A repeat reads as a first cook

A repeat is the plan's word, not the page's. In the plan it stays: it cooks and
buys again where a leftover does neither, and it points at its first cook so the
model writes a recipe once ([origin, repeat and leftover](/domain/origin-repeat-and-leftover.md)).
On the page it prints whole — its own amounts, the first cook's method, its own
Makes line — so Friday's eggs and Tuesday's are the same card. Until then only a
page with photos did that, and a page without one sent a repeat back to its first
cook; the athlete asked for the two pages to match. A repeat whose first cook has
no method falls back to the pointer, *Cooked again from Tuesday Breakfast*.

# The Makes line is the pot, counted in portions

A batch's card used to say where it was eaten and not how much, and an athlete
asked why the recipe said 200 g and the list bought 600. It leads with the
pot: `Makes 6 portions: Friday Lunch (2), Saturday Lunch (2), Sunday Dinner (2)`.
Shares print as decimals, matching the meta line.
`one portion: …` prints only where the shares are uneven.

**Every card that cooks carries it**, an origin and a repeat alike, wherever
its total can be stated (below), and a leftover, which cooks nothing, carries
its pointer instead. A pot eaten only
where it is cooked says `Makes 1 portion.` and names no sitting, because the band
above already does; its size is then said there and not on the line under the
title. A batch's card keeps its plate on that line, beside the figures it comes
to: split from its size by a pot of six, the figures once read as the pot's.

**The total is withheld whenever it would be anything but the pot the list is
scaled to** — a missing pot, the origin's own sitting absent from its servings, a
sitting named twice or excluded, or a plate that is not a positive whole number
of quarters (which binary floating point adds exactly). Withheld, a batch falls
back to `Makes: A, B` with its brackets, and a pot eaten only where it is cooked
prints no line at all, whether origin or repeat: its sitting alone would repeat
the band, and its size stays on the line under the title. A review caught the
first version printing `Makes: Tuesday Breakfast (0.3)` under a band reading
Tuesday … BREAKFAST, with 0.3 on the line above it as well. An origin kept on a
day away, for a leftover's sake, lists no sitting and so has no line either. The
list's scale and the line read one function's pot, so they cannot disagree.

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
versions; the two lowercasings — names, to look up a pack and whether a line
drains its food, and ASCII units, to tell a US list's aisles — are compared and
never printed), arithmetic is
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
