---
type: Module
title: The validator
description: validate.py is the one part of the skill that checks rather than instructs. Three exits, a line on success, findings that name their repair, and tolerance chosen so a malformed plan is described rather than hidden.
tags: [architecture, validation]
sources:
  - resource: skills/training-week-meal-plan/scripts/validate.py
  - resource: skills/training-week-meal-plan/SKILL.md
sources_digest: c55898c59fbcf828
---

# Why it exists

Everything else the skill ships either instructs a model, which may quietly not
follow it, or renders what the model wrote.
Asking a model to check its own arithmetic lands around 95% reliable, which is
fine when a person reads every plan and not otherwise. So the faults that make a
plan actively harmful — food cooked and never eaten, bought and never cooked —
are checked in code ([portion conservation](/invariants/portion-conservation.md),
[the list buys what the week uses](/invariants/the-list-buys-what-the-week-uses.md)),
and so is the one rule the skill exists for: that the meals follow the ranking
the plan itself states ([check 10](#check-10-the-plan-against-its-own-ranking)).

# Three exits, and success is not silent

`0` clean, `1` findings, `2` could not validate. The third exists because
Python's default for an uncaught exception is `1`, which would make *your plan is
broken* and *my checker broke* the same signal.

Exit 2 comes as two messages that callers tell apart: *could not read* means the
path is wrong, *could not validate* means the document. Step 4 answers them
differently, so changing either wording changes the step.

Exit 0 prints a line. Silence-is-golden is a shell convention; the consumer here
is a model reading a transcript, and a clean run and a crashed one both produce
empty output.

**A crash is never a finding.** A code is a claim about the plan; exit 2 is a
statement about the checker and carries a message. There is no schema check in
front of the other checks — no validator library in the standard library — so
they are the first thing to see the document, and an exception on a document too
broken to walk is expected rather than a bug.

# A missing capability is announced

Nothing about the host is guaranteed; a host with no shell is a class, not an
outlier. So a missing interpreter degrades and ships — refusing to hand over
would turn a degraded outcome into none, on exactly the hosts least able to do
anything about it. **The handover says whether the plan was checked and what the
check said.** Three things must not happen instead:

- **suggest installing anything**;
- **offer a careful re-read as the substitute** — a re-read is what the validator
  exists to replace, and naming it as equivalent sounds responsible while
  rebuilding the thing replaced;
- **hand the check to the athlete.** The old text told the athlete to name the portion arithmetic as the thing to
  satisfy themselves about before shopping. Both athletes without code execution
  named it the most annoying line in the reply and rated trust 2 of 5; the
  validator, run afterwards, found nothing on one plan and a wrong day tag on the
  other. So the announcement is one sentence stating a fact and its reason —
  *this plan wasn't run through the checker, and there's no printable page: both
  need Python, which can't run here* — worded once, in `SKILL.md`.

**Repair at most twice, then check once more**, so the report describes the
document actually handed over. Where an unattended pipeline would fail and ship nothing, here
there is a person in the thread and this session is the only chance, so failing
loudly means *to the athlete, by name*: the plan is handed over and the surviving
finding stated.

# Every finding names its repair

A message says what is wrong and the honest ways to fix it, and never offers a
repair that would clear the check by making the plan worse. Examples:

- `recipe-on-uncovered-day` offers *cook it on a covered day* or *it is fridge
  food* — never *add the day*.
- The fridge repair is conditional — *if the athlete said it is already made* —
  and `fuelling.md` adds that food they did not mention is not in the fridge,
  because *list it in `fridge`* is otherwise the cheapest way to clear a finding.
- A day tag on a day the fridge feeds says *what Tuesday uses comes out of the
  fridge, which is eaten first*, not *nothing uses it*, whose repair would be to
  drop a recipe.

**A plan whose days are wrong hears `day-order` and nothing else.** Every other
check reads the days, and answered a missing or extra day as a fact about the
week — one brief asked for Friday back *and* for its portions and shopping gone.
Nothing in the checker knows which days were asked for, so a repair that obeys
*drop Friday* would ship clean. `day-order`'s target is the earliest day named,
through to Sunday: Thursday, Saturday, Sunday is told to put Friday back;
Thursday through the next Wednesday is told to stop at Sunday.

# A meal's dishes are its recipes' titles

The page links a meal to its method by matching each name in `dish` and
`alongside` to a recipe's `title` at that sitting, exactly. A near-miss leaves
the week at a glance naming one breakfast while the recipe and the shopping list
cook another. Check 3 holds the two sides to each other:

- `dish-without-recipe` — a dish the meal names that no recipe at that sitting
  has;
- `recipe-without-dish` — a recipe entered at a sitting whose meal does not name
  it.

A renamed dish draws both, and the first names the other title, because giving
both one title is the usual repair. Case counts: `Fruit Salad` is not
`Fruit salad`.

**Two checks lean on these.** Check 10 compares only days whose meals and
recipes line up, and check 6 compares no quantity at all while one sitting's
food cannot be added up; both leave the fault to check 3 to name. Until 1.1.1
check 3 had no such finding, so both deferred to nothing. A Haiku 4.5 plan from
the first eval run exited 0 with Friday breakfast — the day before its race —
and Sunday lunch each naming a dish the recipe there was not. With the titles
aligned, the same plan has 37 shopping-quantity findings.

# Check 9: the load table covers the week and adds up

`week_load` is the model's scratch work before any meal, and only its shape is
checked: one row for each day the plan covers, none for a day it does not
(`week-load-day-missing`, `week-load-day-not-planned`, `week-load-day-repeated`),
and a day's `day_load` equal to the sum of its entries' `load`, give or take half
a point for the total being written to a whole number (`week-load-day-sum`). The sum is arithmetic, and
the ranking is read from it.

**No entry's own figures are checked.** An entry's `load` is `hours x IF^2 x 100`
only when the model estimated it; when the athlete gave it, from a platform
that works it out its own way, it is copied as it stands, and a check of the
formula would reject the athlete's number. A finding for the sum is an ordinary
finding, because this script has no warning tier: any finding exits 1 and goes
to the repair loop ([carb periodization](/domain/carb-periodization.md#week_load-copies-what-the-athlete-gave-and-estimates-the-rest)).

# Check 10: the plan against its own ranking

`training_overview.hard_days` is the plan's answer to *which days did you fuel
hardest*, hardest first. Check 10 splits it and `easy_days` at top-level commas,
reads each part's leading letters as one day, and sums each day's meal
carbohydrate as the page prints it — each dish's reference portion times its
plate's portions. Two ways to be wrong:

- `hardest-day-outfuelled` — a later hard day out-feeding the day named first;
- `hard-day-under-easy-day` — an easy day out-feeding a hard one.

And one said first, `ranked-day-not-covered`: the ranking names a day the plan
does not cover — a week ranked before it was cut — and when that day is named
first every comparison after it goes silent.

**It may gate because it ranks nothing.** It computes no training load; it holds
the plan to its own statement, so a finding is always a real contradiction, and
both repairs — move the food, or move the day to the other list — are legitimate.

- **A 5% band**: a few grams change nothing for the athlete and cost a repair.
- **The two days before the day named first are exempt only as the heavier
  side.** Race loading and the day-before rule raise exactly those days and
  never lower one. Over 61 plans stored from an earlier generator, all of one fixture week,
  that window took the plans with a finding from 8 to 1.
- **Only whole days are compared** — each main meal there once, not excluded, one
  recipe per dish. A day with a dish whose carbohydrate is not a number is not
  compared: read as nothing, it would look under-fed.
- **A day named in both lists is hard.**
- **A race is held to the ranking like any hard day.** Exempting it meant telling
  a race from training by words in a session name, and three review rounds each
  found a new way that failed (`Race-pace intervals`, `Race weekend 10K`,
  `pre-race`). If a race ever needs telling apart, the way is a field the model
  sets, not a lexicon.

**Known limits.** The two days before the top may be fed above it by any amount,
a blind spot in a week with no race. A day in neither list is never compared, so
`easy_days` written as prose compares nothing, and a repair can silence
`hard-day-under-easy-day` by dropping the day. A first part that names no day
silences the check rather than anchoring it on the next part, which would have
told an athlete to cut the days before a race. `Sat & Sun` reads as Saturday
only: a part is one day.

# Tolerance is matched to what can be answered

The first rule was *no defensive fallbacks — let it raise*. That hid faults: a
day name outside the seven raised and exited 2, and the check suppressed was `day-order`, the one whose purpose is to say the
week is misnamed. A shopping row's day tags outside their abbreviations
(`days-out-of-order`) raised the same way, and that is where the next two
attempts went wrong. So: **where a
comparison can still be answered, degrade and report; raise only for a document
too broken to walk.** The attempts that got there each fixed one half and lost
the other — a sentinel sort order reported a week-order fault that did not
exist; suppressing the check on any unknown tag lost two recognisable tags that
were out of order. What worked was asking a question with an answer: are the
tags it can recognise in week order?

Arithmetic is spelled out where a shorthand means different things on different
runtimes: the ten ASCII digits rather than `\d`, an explicit whitespace set,
**rounding half up** rather than Python's half-to-even.

# What the standard library bounds

The checks match ingredient names to shopping rows by word tokens, and the
standard library limits how well that can be done:

1. **No word segmenter.** Names in scripts without spaces — Japanese, Chinese,
   Thai, Lao, Khmer, Burmese — stay one token.
2. **No Unicode Script property**, so the mark strip is scoped by character name.
3. **The Unicode database moves with the interpreter** — 3.9 ships version 13.
4. **The function-word table is Latin-script only.** The plan is English by
   promise, stated in `SKILL.md` and where the model writes the JSON.
   It is not English-only, though: English borrows (`Tuna in brine`, `Chilli con
   carne`, `pico de gallo`), and keeping only English's own function words would
   break both directions — false `ingredient-not-purchasable` on a correct plan,
   and a missing `day-used-but-untagged` on a wrong one.

A name made **entirely** of function words tokenises to nothing and matches
nothing, itself included. English `the` folds onto French `thé`, so a plan that
named tea in French would draw findings it cannot fix.

**Test on the floor as well as a current Python.** `compatibility` promises 3.9,
a laptop may have two interpreters on `PATH` with shell start-up deciding which
answers, and a newer one accepts syntax 3.9 rejects. Nothing here runs that yet
([which copy is the source](/questions/which-copy-is-the-source.md)).
