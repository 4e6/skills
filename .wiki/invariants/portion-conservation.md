---
type: Invariant
title: Every cooked portion is eaten within the plan
description: A recipe's pot must map every portion to a named meal on a day the plan covers, nothing eaten before it is cooked or more than four days after. Held in code, because a plan that over-cooks costs money and trust.
tags: [plan-quality, validation]
timestamp: 2026-09-30T14:00:00Z
sources: [skills/training-week-meal-plan/scripts/validate.py, skills/training-week-meal-plan/scripts/render.py, skills/training-week-meal-plan/references/fuelling.md]
source_commit: 09ce2978e940f31f6b3e3e89ba18422c2c407218
---

# Statement

For every recipe, **portions cooked == portions eaten**, and every portion maps to
a named meal inside the days the plan covers. The allocation is structured —
`servings`, a list of `{day, meal}` sittings on the origin — rather than read from
prose, so the check is exact:

- every sitting is a real meal that eats this dish;
- every dish a meal serves is claimed by exactly one batch;
- nothing is eaten before it is cooked;
- nothing waits longer than the leftover window.

# Portions are sized as well as counted

Counting is not enough. `cooked == eaten` once held while the two halves of a
batch carried 800 and 880 kcal — every leftover in one real week had drifted
toward the eating day's training load, which is periodization applied to a number
it may not touch: you cannot eat 10% more of a box you portioned yesterday.

So there is **one statement, and the sizing holds by construction.** The origin
states one portion's `nutrition` and how many portions its list makes (`yields`);
every plate at every sitting is a number of those portions; and the code computes
the plate's figures, the pot's list and the shopping row. A leftover *is* a share
of the pot, and nothing can claim more than went in. An uneven split to fuel a
harder day is the skill working, and it needs saying nowhere but in the portions.

What checks remain are what the arithmetic cannot do for itself: an ingredient
line that is not a number and a unit where a pot has to multiply it
(`ingredient-quantity-unscalable`), and an origin that does not say what a
portion is worth or how many it makes.

# Days and meals the athlete is away

A day may carry no meals, and a single meal may be eaten elsewhere — a weekday
lunch at work. The invariant is unchanged; the set of sittings shrinks. A batch
for four may not put its fourth portion on an excluded Friday
(`portion-into-excluded-day`, `portion-into-excluded-meal`). The fix is a smaller
batch, not a new meal.

# Additional rules

- **Batches divide into sittings that exist.** A dish that fits one meal this week
  is cooked for one — never default to two.
- **Four days at most.** A portion cooked on day *N* may be eaten up to day
  *N+4* (`leftover-too-old`). Four and not three, because three fails an
  obviously fine plan: a Wednesday bolognese eaten again on Sunday. Four still
  refuses Monday to Saturday. The rules also say cooked fish, leafy salads and
  dressed dishes are eaten within two days; nothing checks that. Perishability varies by dish, and encoding it would
  mean classifying every recipe for little gain, because plans that go wrong go
  wrong by a mile. If real plans fail at exactly four days, the answer is probably
  a per-dish field the model fills in, not a different constant. The error runs
  the safe way: a long-keeping dish is merely used less cleverly.

# What it does not watch

**The pot, not the trolley.** This counts portions coming out of a batch, so it is
blind to a batch that was over-bought — 200 g of peas cooked from a 750 g bag
conserves every portion. That is
[the list buys what the week uses](/invariants/the-list-buys-what-the-week-uses.md),
which exists because a real week failed there while this passed.

**Neither counts containers.** A week that takes 120 g from a 400 g tin conserves
every portion *and* buys exactly what it cooks, and still leaves half an opened
tin. The answer is a rule about what the recipes cook — *a container you open is
a container the week finishes*, in `references/fuelling.md` — and it states no
threshold and loses to periodization: better half a tin left than an easy day
carrying the week's biggest meal. No check enforces it, because a check would
rest on what a tin holds, which the model knows and nothing here can verify.

# Why

Cooked food that is not scheduled spoils, and food waste is one of the main
reasons people abandon meal planning. A plan that quietly over-cooks is worse than
no plan.

# If violated

The plan sends somebody shopping for food that will rot. The repair loop gets two
attempts; after that the plan is still handed over and the surviving finding
stated to the athlete by name ([the validator](/architecture/the-validator.md)).

See [origin, repeat and leftover](/domain/origin-repeat-and-leftover.md) for the
distinction this ledger turns on.
