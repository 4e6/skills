---
type: Glossary Term
title: Origin, repeat and leftover
description: The three kinds of recipe entry. A repeat cooks the dish again and buys it again; a leftover eats a portion already cooked and buys nothing. Getting that backwards is silent in both directions.
tags: [domain, plan]
timestamp: 2026-09-30T20:29:56Z
sources: [skills/training-week-meal-plan/references/fuelling.md, skills/training-week-meal-plan/references/plan-schema.json]
source_commit: 6baaea7682972296b9ace115aa6a8e9adacec9c5
---

Every main meal of every day gets its own recipe entry, so a dish eaten more than
once appears more than once, as one of three kinds:

| Kind | Means | Carries |
|---|---|---|
| **origin** | the day the dish is first cooked | the full recipe: ingredients for `yields` portions, steps, one portion's `nutrition`, `portion_size`, and `servings` — the sittings its pot feeds |
| **repeat** | cooked again from scratch on a later day | `origin_day` and its plates' `portions`; its pot is the origin's list at that size, computed |
| **leftover** | a portion from an earlier batch | `origin_day`, its plates' `portions`, and reheat rather than cook times |

**Only the origin states a quantity.** Every plate is a number of the origin's
portions, and every pot is its list sized to the plates it feeds. A leftover of
`portions: 1.25` is a quarter more of a pot that already exists; a repeat of
`portions: 1.25` is a bigger pot, and its page lists 100 g of oats because the
code multiplied the origin's 80.

# The distinction that matters

A **repeat cooks again**, so it needs the ingredients again. A **leftover eats
something already cooked**, so its ingredients were bought and used on the origin
day. That one difference drives three checks and is easy to get backwards:

- **The portion ledger** counts a leftover against the origin's `servings` — the
  batch has to be big enough. A repeat consumes nothing from the earlier batch
  ([portion conservation](/invariants/portion-conservation.md)).
- **The day tag** on a shopping row counts a repeat's day and not a leftover's:
  Wednesday's porridge is a repeat, so oats are tagged `Wed`. A day the fridge
  feeds is like a leftover day here — it uses the food and buys none.
- **The shopping quantity** adds a repeat's oats and a leftover's nothing
  ([the list buys what the week uses](/invariants/the-list-buys-what-the-week-uses.md)).
  Getting it backwards is arithmetic rather than a missing label, so it reads as
  a number the athlete has no way to question.

# Why a repeat exists at all

Some dishes are not worth batching — eggs on toast is faster to make twice than
to store. Collapsing repeat into leftover would mean either buying twice for a
reheat or under-buying for a second cook.

Collapsing it into a second origin was asked about too, and kept apart: the
model would write the list and the method twice, and two copies of one dish can
disagree about its figures. The distinction is the plan's alone — **the page
prints a repeat as a first cook**, whole, with its own Makes line
([the printable page](/architecture/the-printable-page.md#a-repeat-reads-as-a-first-cook)).

# In the validator

A repeat with a list of its own is `repeat-with-ingredients`; a pointer with
figures of its own is `pointer-with-nutrition`; an origin with no `yields`, no `nutrition` or no `ingredients` leaves nothing to
multiply. Each is a finding, because without them
the checker would pass a plan clean while the page printed the wrong pot.

# A meal is a list of dishes

A meal names a main and anything `alongside` it, and each dish has its own
recipe. The ledger keys on `(day, meal, title)`, so a main and its side at one
sitting are two claims on two dishes, not a double count.
