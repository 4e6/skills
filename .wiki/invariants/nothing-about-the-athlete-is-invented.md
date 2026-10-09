---
type: Invariant
title: Nothing about the athlete is invented
description: No figure about the athlete's week that they did not give may be printed, and a missing required input is a question, never a guess. What they did give is theirs to print and to fuel from.
tags: [plan-quality, intake]
sources:
  - resource: skills/training-week-meal-plan/references/fuelling.md
  - resource: skills/training-week-meal-plan/SKILL.md
sources_digest: d5196c2ccefd1cf8
---

# Statement

**No measurement of the athlete's week that they did not give may be printed** —
hours, distances, a load score. A made-up figure is indistinguishable on the page
from a real one, and the week in their own words is the only source there is.

The other half is as easy to lose: **a figure they did give is theirs** — to
print, and to fuel from.

# What follows

- **A missing required input is a question.** There is a conversation, so the
  week and the weight are asked for rather than guessed. Inside the finished
  document, which is printed and carried into a kitchen, the plan says what it
  assumed and never asks.
- **Body weight has no fallback.** Every portion scales from it, so a made-up one
  is wrong on every page at once
  ([the intake](/architecture/the-intake.md#what-it-asks)).
- **A week nobody gave is easy days**, chosen by the athlete and said on the page
  — never a template week with invented sessions
  ([the intake](/architecture/the-intake.md#a-week-nobody-gave-is-easy-days)).
- **Sessions without days are asked about**; if the host must place them, the
  summary says so.
- **A session named hard or long whose length or intensity is missing** gets
  fuel lines that say what depends on the missing figure, and never the figure;
  one named short or easy, or not described, gets none
  ([carb periodization](/domain/carb-periodization.md#the-figures-and-where-each-comes-from)).
- **`week_load` copies the figures they gave and estimates only the rest.** Hours
  are 0 where none were given, meaning *unmeasured*. An intensity factor or a load
  the model estimated is its scoring and never reaches the page, the reply,
  `training_overview.total` or a session's name; one the athlete gave may appear
  wherever it would anyway
  ([carb periodization](/domain/carb-periodization.md#week_load-copies-what-the-athlete-gave-and-estimates-the-rest)).
- **The reply gives the biggest day's reason in their words**, quoting a figure
  only if they gave it. What it lists as assumed is limited to which days, which
  units and a session's day; it never lists the model's own scoring, which is how
  an estimate used to reach the athlete.
- **A stated goal time is the race's duration.** It is not split into legs, and a
  leg the athlete never timed is not subtracted from it; an unstated duration is
  not estimated.
- **Today's date is never guessed**, and a file is never named for a guessed one
  ([last week's plan](/architecture/last-weeks-plan.md)).
- **The fridge holds what they said** — the validator's repair messages say so,
  because *list it in the fridge* is otherwise the cheapest way to clear a
  finding.

# What it does not cover

**Adding up what they gave is not inventing.** Where every session's hours came
from them, `~10h30, 6 sessions` is fair in `training_overview.total`, and a load
score stated session by session totals the same way. The sum is made in minutes,
and where any session has no stated duration the line prints the session count
alone. This is the likeliest place for a later edit to over-tighten the rule, and
for a sum to be wrong: nothing checks the line.

**A published range is not an invented figure.** A carbohydrate or fluid range
per hour, a daily or race-week g/kg target, and a snack range worked from one at
their stated weight measure nothing the athlete did; it is sourced
guidance, and printing it claims only that the guidance says so
([carb periodization](/domain/carb-periodization.md#a-published-range-is-not-an-invented-figure)).

# If violated

The page carries a number that looks measured and is not — the athlete fuels a
session they never described, or shops for a week they never planned.
