---
type: Open Question
title: Should the plan be sized to daily carbohydrate targets?
description: Published daily bands are whole-day intake — 5–7 g/kg on a moderate day, 6–10 on a high one — and the skill plans three meals with no snacks. Its own example's meals come to about half the band. Add snacks, state the gap, or leave it.
tags: [nutrition, product]
timestamp: 2026-09-30T16:00:00Z
status: open
sources: [skills/training-week-meal-plan/references/fuelling.md, skills/training-week-meal-plan/examples/sample-plan.json]
source_commit: 4757fa27aade35d4ca5a676123a3c9c0eb45d9e3
---

# The question

The skill periodises by ranking: hard days get the largest carbohydrate portions,
easy days less, and [check 10](/architecture/the-validator.md#check-10-the-plan-against-its-own-ranking)
holds the meals to that order. It states no daily target. The published daily
bands ([carb periodization](/domain/carb-periodization.md#daily-targets-checked-and-not-shipped))
would give one — but they count everything eaten in a day, and the plan holds
breakfast, lunch, dinner and session fuel, and no snacks.

# What the numbers say

The shipped example's meals, summed per day as check 10 sums them:

| Day | Training | Meal carbohydrate | At 65 kg |
|---|---|---|---|
| Monday | 1 h easy run | 185 g | 2.8 g/kg |
| Tuesday | 1.8 h threshold bike and brick | 222 g | 3.4 g/kg |
| Wednesday | 1.8 h intervals and strength | 260 g | 4.0 g/kg |
| Thursday | 1 h hard swim | 164 g | 2.5 g/kg |
| Friday | rest, fed for Saturday | 225 g | 3.5 g/kg |
| Saturday | 3.2 h time trial and brick | 345 g | 5.3 g/kg |
| Sunday | threshold run and open-water swim | 271 g | 4.2 g/kg |

The example states no body weight; 65 kg is the middle of the intake's rows.
Session fuel adds to the hard days, but on every training day the meals alone
sit well below the band the training would put the day in — Monday and Thursday
at about half of it. Friday, a rest day, is the one day inside its band. Reaching 6–10 g/kg from three meals means
bowls of 130–220 g of carbohydrate each at 65 kg.

# The options

- **Add a snack**: a slot the schema, the ledger, the list, the glance and both
  validators would all have to learn. The largest change, and the one that makes
  the bands reachable.
- **State the bands and let meals fall short**, saying on the page that the day's
  total includes snacks and fuel the plan does not list. Cheap, but a figure the
  plan visibly does not meet.
- **Size meals to the bands without a snack slot.** Very large plates on hard
  days; the example and every plan change.
- **Leave it**, as now, and keep the ranking as the whole claim. The host is told
  not to look the figures up.

Any of the first three changes every plan and wants measuring first
([editing a skill](/conventions/editing-a-skill.md#how-a-change-to-behaviour-is-measured)),
and whether a meal plan should reach a whole-day band at all is a sports
dietitian's question as much as a design one.
