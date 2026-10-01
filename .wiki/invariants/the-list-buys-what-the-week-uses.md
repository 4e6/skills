---
type: Invariant
title: The shopping list buys what the week uses
description: Each row's quantity is what the recipes cook with, less what the fridge holds, and its days are the days that eat what it buys. One amount of food per row and never a pack size — except a staple, which is the jar and carries no days.
tags: [plan-quality, shopping, validation]
timestamp: 2026-10-01T15:01:23Z
sources: [skills/training-week-meal-plan/scripts/validate.py, skills/training-week-meal-plan/scripts/render.py, skills/training-week-meal-plan/references/fuelling.md]
source_commit: 6baaea7682972296b9ace115aa6a8e9adacec9c5
---

# Statement

For every row, **`qty` is what the week's recipes take of it**, summed across
every day that cooks with it and less anything the athlete said is already in the
fridge.

**One amount of food per row, and never a pack size where a recipe measures the
item** — `200 g` of peas, though no shop sells that amount. Buying is the
shopper's step: nobody expects a 500 g bag of rice to match a list that says
500 g, and frozen peas are the same problem, only less familiar.

**A row's `note` says what the row is for or how to buy it, never how much** —
not a weight, a pack, a count or what is in the fridge. `qty` has already taken
the fridge off. `shopping-note-states-an-amount` catches a note with a number and
a unit symbol; a count, a unit written as a word, or a symbol in another script
gets past it, and a nutrition figure such as `18 g protein` trips it.

# Measured, on a real week

An athlete reported *the shopping list contains frozen peas 750 g while the plan
only uses 200 g*. Walking every recipe on that plan against its list found seven rows like it, the
peas included — jam 340 g for 30 g, olives 200 g for 30 g, bread 800 g for 370 g.
Everything else was inside pack granularity, which is the whole difficulty: read
as *what to buy*, a quantity has to be a pack, and a pack cannot be checked
against a recipe. Flagging only a large overshoot moves the argument to the edge
of the band and still cannot tell the athlete which side they are on. The way
out is a **meaning**, not a threshold: `qty` is what the week uses, and with one
meaning the comparison is exact.

**A second amount on the row was tried and taken out.** `200 g (bag of 750 g)`
reads well sitting still and fails standing up: two amounts on one row is a
decision made at walking pace, and the one a shopper acts on is the larger.

# Where the week's total is not what anyone buys

- **The unit bought is the quantity.** A bag of salad leaves a recipe takes a
  handful from is `1 bag`.
- **A staple is the jar it is, and carries no days** — oil, and condiments the
  recipes take by the spoonful and that keep once opened: `Honey — 1 jar`, never
  `5 tbsp`. Carrying no days is what keeps it out of the comparison, not its name:
  a dated honey row weighed in grams is compared like any other. A sauce that
  goes off once opened is not a staple.
- **Butter is not a staple.** It is a fat the week cooks with, so its row is
  dated and its `qty` is the recipes' total in their own unit. That is a rule in
  the prose that no check draws.

# A count of the purchase is not a second amount

`Tinned chickpeas — 480 g (2 tins)`: the model states `pack`, how much **one
purchase provides** — 240 g drained for a chickpea tin, because recipes weigh
tinned food drained — and the page prints `ceil(qty / pack)`. `pack` itself is
**never printed**, which is what stops it becoming the second amount that cost the
first attempt its life. Acting on either half of the row puts the same food in the
trolley.

- **A recipe line's count is its own**, from that line's weight against its
  food's `pack`, never copied from the row. A container is counted only where the
  line takes whole ones, within a twentieth of a pack — a cook who reads `1 can` beside 250 g of a 400 g tin tips in the whole can and takes the next meal's food. A loose
  piece takes the nearest whole number, and nothing where that rounds to none.
- **`pack` is unverified, and nothing checks it.** A tin is 400 g in one country
  and 425 g in another, so a check would fail correct plans. A wrong `pack` gives
  a wrong count, silently.
- The count on the page is deliberately weaker than it could be — a line's food
  is matched by the head of its name before any comma — and its failure mode is a
  missing count, never a wrong one.

# Names that match

- **A tinned or jarred food carries its container word, and every recipe line
  starts with that whole name** — `Tinned chickpeas`, and `Tinned chickpeas,
  drained` on the line. A name is read first; `Tomatoes — 800 g (2 tins)` was read
  as fresh. The matcher is word-based, so `Chickpeas, drained` against a `Tinned
  chickpeas` row matches nothing and switches the quantity check off for the plan.
- **How it is cut goes in `note`, never the name** — a row named for a
  preparation pulls a line to the wrong item.
- **One food, one row.** Three potato rows are three numbers to add up in the
  aisle. A second kind earns its own row only where it changes what gets cooked.

# A day tag is a day that eats what is bought

A row's days are the days that eat what it **buys**. **The fridge is eaten first,
from the plan's first day**: the days are walked in order, each taking its need
off what is left, and the first day that needs more than is left — and every
later one — buys. So the days a row buys for are always a suffix of the days that
use it. A plan once printed `Eggs 11 (Mon, …)` where Monday's eggs came out of the
fridge.

| the fridge | what the check demands |
|---|---|
| answers no row | every day that uses it |
| answers the row, every amount readable | exactly the days after the fridge runs out |
| answers the row, how far it reaches unreadable | any non-empty suffix |

A tag on a day the fridge feeds is `day-tagged-but-unused`, with a message saying
the fridge is eaten first. A model that tags every using day draws that finding;
the message tells it how to fix it.

# Enforced by

Check 6 compares each dated row's `qty` with the recipes' total, less the fridge:
`shopping-quantity-short`, `shopping-quantity-excess`, and
`shopping-quantity-is-a-pack` for a list counting what the recipes weigh. Each
message states the week's total in the row's own unit, so the repair is a copy,
and always with a decimal point. Check 2 compares the day tags.

# What it deliberately does not compare

**Some faults switch check 6 off for the whole plan**, because adding up the rest
would give advice that compounds them: an ingredient matching no row, a meal or
side with no recipe entry, a recipe on an excluded or uncovered day, a repeat
with a list of its own, a pointer to nothing, an origin with no `yields` or no
ingredient block. Each is a finding of its own, so the list is unchecked only
while something else is being repaired. The last was once silent — the list went
unchecked and nothing said why — until `origin-without-ingredients` was added.
The schema cannot require the field, because only an origin carries one. A meal
or side naming a dish no recipe at its sitting has was silent the same way
until 1.1.1 added `dish-without-recipe`.

The rest are per row. Each is a place where comparing would be a claim rather than
a sum:

- **A quantity that will not parse** — `90 g dry per serving`, `handful`,
  `1 lb 5 oz`, `16 fl oz`. One number and at most one unit word is all that is
  read, which is why the skill keeps fluid ounces off the list and the recipes
  of a plan in US units.
- **Two sides measured differently** — grams against millilitres wants a density
  nothing has, and `½ head` against a count is not a disagreement about a
  half. Exactly one crossing is reported: a list *counting* what the recipes
  *weigh* (`shopping-quantity-is-a-pack`). Cups, pints, quarts and gallons
  were counting nouns until 1.2.0, so a week measured in cups and bought by the
  quart went unchecked; they are volumes now. Spoons are still counted, so a
  cup on one side and tablespoons on the other still go unchecked.
- **The food on more than one row** — there is no single quantity, and no
  unambiguous repair.
- **A row the fridge covers for the whole week** — check 2 then says to take it
  off the list.
- **Days that are wrong** — the checker says `day-order` and nothing else, or the
  list would be told to buy less for the day it is being asked to put back.
- **A food named in a meal's prose** — its `note` — takes that row out of the
  comparison **for the whole week**, since prose states no amount, and tags the
  row for that day. That is why the *container you open* note may name no food,
  and one reason a meal has no `extra` any more: food served with a dish is an
  ingredient in its recipe, where its amount is compared. A plan written before
  that may still carry one, and it is read as prose. A session's fuel lines and a
  day's snacks are not prose: their food is an example, and it is not on the
  list.

# What it takes on trust

- **A row with no days is a staple**, so dropping a row's tags silences both the
  quantity and the day checks on it.
- **An origin's quantities are the whole batch.** Nothing can check that a list
  written for one portion was not labelled as four.

# If violated

The athlete pays for food nobody cooks, or reaches the stove short. Every quantity
finding goes through the repair loop with the rest
([the validator](/architecture/the-validator.md)).
