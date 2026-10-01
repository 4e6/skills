---
type: Module
title: The intake
description: Step 1 asks for the week, the weight, three optional things and which days — on a menu where the host has one, in one message where it does not. Why each row is the row it is, and how the days are settled.
tags: [architecture, intake]
timestamp: 2026-10-01T15:01:23Z
sources: [skills/training-week-meal-plan/SKILL.md, skills/training-week-meal-plan/references/fuelling.md]
source_commit: 6baaea7682972296b9ace115aa6a8e9adacec9c5
---

# What it asks

Two things are required and never invented: **the week** and **the body
weight**. Three are optional and asked anyway: dietary restrictions, what is in
the fridge, and where they live. And, where the athlete has not said, **which
days** the plan covers ([nothing about the athlete is invented](/invariants/nothing-about-the-athlete-is-invented.md)).

# A menu where there is one, and never a requirement

Most questions have a handful of common answers, so step 1 offers them as a menu
where the host has a tool for one, described by what it does rather than by any
host's name for it. **The tool is never a requirement**: with `allowed-tools` absent, a skill written around its author's
client asks a stranger's agent for a tool that is not there. So the fallback —
every question in one message — sits beside the menu as the same step, not a
lesser one. The questions never become a message each.

**No count is written into the rule.** Adding a question once made every
sentence that said *five* false at the same moment.

# Why each row is the row it is

- **Weight: `55`, `65`, `75`, `85` kg, each with its pounds, and a typed row.**
  Between 50 and 90 kg, picking the nearest is at worst 5 kg out — single-digit
  per cent of a day's carbohydrate, narrower than the band the g/kg targets are
  quoted across. Off either end the error has no ceiling, and the skill says so.
  It is never a licence to round on the athlete's behalf: an unstated weight is
  still a question.
- **Both units on every weight row, because the weight's unit is the athlete's
  and the food's is the country's.** The rows were kilograms only, with pounds
  left to the typed row. The menu goes up before the place is answered, so it
  cannot pick one unit, and an American may well know their weight in
  kilograms. A typed figure still needs its unit: a bare `100` is a 100 kg
  rower or a 45 kg runner, so a number with no unit is read without asking only
  where the other reading is impossible.
- **The typed row never gets an option of its own.** Every such tool renders a
  free-text row, and an option saying *I'll type it* is the same choice written
  twice. A question whose only named answer is a default carries one option.
- **The fridge's example is there to be read, not picked.** *A handful of
  spinach, 200 g cooked lentils, 2 ripe avocados* shows the shape wanted — a few
  things with rough amounts, measured three ways so no one of them reads as the
  required format. Everything in it keeps for days, not weeks: the failed
  candidates were root vegetables — potatoes, then carrots — which keep for
  weeks, and a vegetable that looks perishable and is not is the standing trap
  in this line. **It carries no meat, fish, dairy, egg, gluten, nut or soy**, because
  it is read beside the diet question, and an earlier example with chicken and
  yoghurt, shown to a vegetarian, read as *nobody was listening*. The fridge
  needs no *declined* row: an empty fridge and no answer buy the same food.
- **Two menus, split by how a question is answered.** Menus cap at four
  questions. The first holds the ones answered by pointing (weight, restrictions,
  place, and the days when still open); the second the fridge and the week,
  whose real answers are typed. **The second waits for the first answer**, so a
  row nobody could foresee — lentils to somebody who just said pulses — can be
  swapped.
- **Place: `United Kingdom`, `United States`, `Canada`, `Australia`, and the
  typed row.** Hosts told to offer *three or four broad regions* each invented
  their own, and athletes typed a country anyway. A region picks no dish and
  names no shop. The four are where an English plan reads without a language gap ([which countries is open](/questions/which-countries-the-intake-offers.md)).
- **The optional three are asked even when the required two came first**, once,
  together, on one menu — the fridge included. *Ask only for what is missing*
  was read as licence to skip them, and an athlete who opened with weight and
  week got porridge, mince and a generic shop. *The fridge included* because the
  two-menu split is for a cold start: a host that applied it here split the
  fridge off, took *just go ahead* on the first menu as the end of the asking,
  and never asked about the fridge. Whatever comes back, *just go ahead*
  included, ends the asking.
- **A pasted week is said to have come from them.** The skill reads no calendar,
  so *I've got your week from* a service is a claim about something it never saw.

**Measured, blind, on 2026-09-24**, simulated athletes answering hosts that
loaded only the skill: twelve intake runs a side, plus two reruns of the revised
text on the after side, which is why its denominators run higher:

| fault | before | after |
|---|---|---|
| a food the stated diet excludes shown in the intake | 4/6 | 0/8 |
| two menus in one turn | 4/4 | 0/4 |
| place rows invented, or regions | 6/6 | 0/8 |
| *3–4 runs a week* placed without asking the days | 2/2 | 0/2 |
| coeliac athlete told the plan is not for her | 1/1 | 0/1 |
| optional three not asked together, once | 0/4 | 1/4, then 0/2 after the fridge clause |
| prompts before planning, worst scenario | 1 | 3 |

What it cost: more prompts before planning in the worst case. The athletes'
surveys came out level, and nearly every complaint on both sides was about the
plan rather than the intake — session fuel missing from the shopping list, and
metric units for a US shopper. The fridge example measured was *200 g opened
tofu*; lentils replaced it afterwards, because tofu is soy, and were not
re-measured.

# Which days: where the athlete is, to Sunday

A plan runs from its first day through to Sunday, one to seven days, and the
frontmatter `description` and the README say so rather than *seven days*. Planning
Monday to Sunday on a Thursday produced a Friday *chilli, left over from
Wednesday* that nobody cooked, and bought three days of food nobody would eat.
The rule is **a chosen start is honoured, a guessed one is rolled**:

- **Their words decide first.** *Next week* is Monday to Sunday; a named day is
  its next occurrence, today included; a pasted week with dates names its own.
- **The guess is tomorrow, not today.** A host knows the date and not the time,
  so a rule about the afternoon could never run, and a plan shopped for today has
  mostly missed today's meals.
- **The question is conditional, and always has two rows or more**, each with
  its dates: `From today`, `From tomorrow` (dropped when tomorrow is Sunday),
  `Next week`. Nothing is asked on a Sunday, where the guess is a whole week.
  Dates on every row, because an athlete can check a date and cannot check
  *tomorrow*.
- **Their words are not rolled.** *This week* starts tomorrow; said on a
  Saturday or a Sunday it leaves only Sunday or nothing, and the skill asks with
  two rows, the days left and next week, rather than silently planning next
  week. Whether a Sunday *this week* should simply mean next week is not
  settled.
- **Today is never guessed.** Without a date in the host's context or from the
  athlete, the question is `A whole week, Monday to Sunday` or `The rest of this
  week`, then what day it is, and the file name carries no date ([last week's plan](/architecture/last-weeks-plan.md)).
  The skill never tells the host to run `date`, which in a sandbox reads the
  sandbox's clock.
- **The line that ends step 1 names the days, with their dates** — on the path
  that asks nothing it is the only place a wrong weekday can be caught.

**Nothing is cooked before the first day.** Food made earlier is `fridge` food
with a meal entry of its own; food the athlete did not mention is not in the
fridge. The validator holds it (`recipe-on-uncovered-day`,
`pointer-to-uncovered-day`), because the portion ledger alone balances a
Wednesday pot in a Thursday plan against itself and notices nothing.

Eighteen simulated runs across fifteen scenarios on 2026-09-24 each landed on
the window the rules call for. Not measured: Sonnet and Haiku hosts, and a real
host's own date line.

# A week nobody gave is easy days

The week question's two no-plan rows, `Recreational — no set plan` and
`Not training this week`, produce the same food: every day **easy, not rest**.
They replaced a fixed template week — six sessions, Saturday the biggest — which
answered *we have no week* by inventing one. Easy days assert nothing the athlete
did not say.

- **It is chosen, never inferred.** Silence, or a week that could not be parsed,
  is still a question.
- **Easy, not rest.** Somebody not training is still walking and carrying
  shopping, and carbohydrate periodised down to resting is the expensive
  direction to be wrong in.
- **The page says which it was**, in `week_label` and `training_overview.total`,
  because level days with no explanation read as periodisation that did not
  happen.

**Sessions without days are a question too.** *Three or four runs a week* says
what, not when. The host asks which days, in the same turn as anything else
pending. Only if the athlete cannot say, or says to choose, does it place them —
every placed session one they named, an unconfirmed one planned easy — and says
in `training_overview.summary` that the days were its choice.

Body weight gets no equivalent. A week has a defensible fallback; a weight has
none, because every portion in the document scales from it.

# A medical diet is a restriction

`SKILL.md` closes by saying the plan is general guidance, *not for anyone
managing a clinical condition or an eating disorder*. A coeliac athlete met that
sentence under a plan built round her diet and could not tell whether it applied
to her. It does not: a condition **whose treatment is leaving a food out** —
coeliac, an allergy — is a restriction the plan already honours, so the line is
worded not to turn her away, and says labels and whoever looks after the
condition have the last word. The line is drawn by the treatment, not by the
word *medical*.

What the sentence *is* about is untouched: a condition whose treatment is **how
much somebody eats** — insulin-treated diabetes, kidney disease, an eating
disorder. Whether the skill should say so before planning, or decline, is
[open](/questions/conditions-treated-by-how-much-you-eat.md). The skill's
`README.md` still carries the unqualified sentence.
