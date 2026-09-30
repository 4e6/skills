---
type: Glossary Term
title: Carb periodization
description: Carbohydrate scaled to each day's training, hardest days fed hardest, and fuel stated per session as sourced guidance with example food. What each figure is, where it comes from, and which need a professional.
tags: [nutrition, domain]
timestamp: 2026-09-30T14:00:00Z
sources: [skills/training-week-meal-plan/references/fuelling.md]
source_commit: 4757fa27aade35d4ca5a676123a3c9c0eb45d9e3
---

Rather than a constant daily diet, **carb periodization** scales carbohydrate to
what each day demands. It is the skill's one claim: any model will write a meal
plan, and this one is worth running only because Saturday is deliberately the
biggest fuel day *because* Saturday is the long session.

# The rule

**Across the days the plan covers** — one to seven, from the first day to Sunday
([the intake](/architecture/the-intake.md#which-days-where-the-athlete-is-to-sunday)).
It is a ranking, so it applies to any run of days, and it gets thinner as the
window does: over two days it is one hard day and one easy one.

The model ranks the days itself, hardest first, from what the athlete said, and
first records its reading in `week_load`: one row per day, the hours they stated —
**0 where they gave none**, meaning unmeasured — the hardest intensity they named
as a zone, and a load the model computes from those. That comes before any meal. Measured without that step, a shipped example fed its
fourth-hardest day below an easy Monday, and a live run fed the eve of the week's
biggest session at 4.3 g/kg. Then:

- **The meals are sized by the day.** Hard days get the largest carbohydrate
  portions, easy days are lighter, and the same dish may be a bigger bowl on
  Saturday than on Monday. The list follows, because it is the sum of what the
  recipes cook. The plan states its ranking in `hard_days` and `easy_days`, and
  [check 10](/architecture/the-validator.md#check-10-the-plan-against-its-own-ranking)
  holds the meals to it.
- **The day before the week's biggest session is fed for it**, whatever it holds
  itself, with a carbohydrate-led dinner that is not heavy or fatty; in a race
  week the race rules take its place. **Inference, and it needs a professional:**
  no source read states it outside race loading, and *not heavy or fatty* is a
  pre-event row, which is one to four hours before, not the evening before.
- **Fuel belongs to a session**, not to a meal ([below](#fuel-is-guidance-for-a-session)).
- **Snacks top each day up to its daily target**, as guidance with example food
  ([below](#daily-targets-and-the-snacks-that-reach-them)).

`week_load` is the model's reasoning and **is never printed**.

# Fuel is guidance for a session

A session carries fuel when it lasts **about 45 minutes or more with its main
work at threshold or harder**, or **about 90 minutes or more at any pace** —
whatever day it falls on. A two-hour easy ride carries fuel; a short hard day's
strength session does not.

Each of a day's `sessions` has optional `before`, `during` and `after` lines, and
each line is two fields:

- `guidance` — the range or timing, never a food: `roughly 30–60 g of
  carbohydrate an hour`;
- `example` — food that roughly fits it, with amounts: `1 bottle of isotonic
  drink, 1 energy bar`.

Fuel used to be a meal, and a plan printed a pre-session snack before lunch and
the bike's fuel after it — a timetable nobody gave, since a week in words has no
start times and athletes move sessions around. So the meals carry no time of day,
and **sports nutrition is not on the shopping list**: the list buys the meals.

**There is no plan-wide fuelling block**, on the page or in the schema. The
ranges live in `references/fuelling.md`, which the lines apply. What that gives up
is an ordering — writing the ranges out before applying them — and it is
unmeasured.

# The figures, and where each comes from

**These are the only figures the host uses.** `fuelling.md` and step 2 tell it
not to look up other guidelines. A host once searched the web for protein and
carbohydrate recommendations mid-run; whatever it finds is unchecked, varies by
run, and can contradict what the skill ships.

| Part | What the rules state | Source | Needs a professional |
|---|---|---|---|
| Gate | ~45 min or more, main work at threshold or harder — not an easier session with a few hard efforts | T16 Table 2, sustained high intensity 45–75 min | **Yes** |
| Gate | or ~90 min or more at any pace | K17, carbohydrate / endurance | **Yes** |
| Before | a small, familiar, carbohydrate-led snack in about the last hour | K17 (30 against 120 min before); B19 p. 121 | No |
| Before | a full meal 1–4 h before, not heavy or fatty | T16 Table 2, pre-event | No |
| Before | the size and timing, and **no figure in grams** | no source gives one for the last hour; a live plan once invented the during range carried backwards | No |
| During | under ~45 min: no carbohydrate, water | T16 Table 2; J14 Fig. 1 | No |
| During | ~45–75 min of hard work: small amounts or a mouth rinse | T16 Table 2; J14 | No |
| During | 1–2½ h: roughly 30–60 g an hour | T16 Table 2; J14 Fig. 1 | No |
| During | ~90 min–2½ h at threshold or harder: the top of that range, about 60 g | T16's own row, top selected by PW22 Fig. 2. M26 puts such work at 90 g/h and is **not followed**: above the range, a theoretical model, and its authors declare industry ties | **Yes** |
| During | longer: 60–90 g an hour, the top only from glucose and fructose and a trained gut | T16 Table 2; J14; B19 Table 2 | No |
| During | easier sessions take less | J14 §5 | No |
| During | the hourly ranges are not scaled by body weight | J14; T16 Table 2 units | No |
| During | a pool swim follows the same ranges, taken at the wall | S14 pp. 366–367 | No |
| During | an open-water swim is fuelled before and after, with no during line | judgement; S14's open-water paper read as abstract only | **Yes** |
| After | carbohydrate with protein within about 2 h | T16 pp. 551, 557; K17 point 11 | No |
| After | straight away when another fuel-carrying session follows within ~8 h | T16 Table 2 | No |
| Fluid | on a session over ~1 h: about 0.4–0.8 L an hour, more in heat | T16 p. 556; Sawka 2007 via T16 | **Heat and sweat rate: yes** |

**No protein amount, and the reason is nutritional.** T16 gives 15–25 g or
0.25–0.3 g/kg within 0–2 h (p. 551); K17 gives 20–40 g or 0.25–0.40 g/kg (points
7 and 11). A per-kilogram figure would break the rule that hourly guidance is
for anybody, and a gram figure cannot be checked against a bar whose label nobody
has seen.

**Why the gate needs a professional.** Neither source says a session below it
should go unfuelled; whether it should is a train-low choice T16 leaves to a
dietitian and coach. The cut-offs are the nearest sourced rows, not a rule anybody
published.

**Inferences, stated as such:**

- **A snack in the last hour and a meal 1–4 h before are a pairing, not a
  sentence from a source.** T16 gives 1–4 h for pre-event fuelling; one K17 study
  found carbohydrate 30 minutes before beat 120; B19 has a small snack in the
  warm-up. None says *the snack goes late and the meal goes early*.
- **Threshold means Z4 and above** where the week names zones — the rules say to
  read a session's main work rather than its highest zone alone.

**Where the week leaves out a length or an intensity**, a session it names as hard or long gets lines saying what depends on the missing figure — *past an
hour, 30–60 g an hour, the top past 90 minutes* — and the figure is never supplied
([nothing about the athlete is invented](/invariants/nothing-about-the-athlete-is-invented.md)).

## Daily targets, and the snacks that reach them

Each day has a carbohydrate target by what it holds, in g/kg across the whole
day. The figures were checked against T16's open-access Dietitians of Canada
edition on 2026-09-30:

| Day | Situation, as T16 words it | Carbohydrate | Source |
|---|---|---|---|
| Light | low intensity or skill-based activities | 3–5 g/kg/day | T16, DC edition Table 1, p. 15 |
| Moderate | a moderate exercise programme, ~1 h a day | 5–7 g/kg/day | the same |
| High | endurance, 1–3 h a day at moderate to high intensity | 6–10 g/kg/day | the same |
| Very high | more than 4–5 h a day at moderate to high intensity | 8–12 g/kg/day | the same |

**Protein: 1.2–2.0 g/kg/day**, higher for short periods of intensified training
or reduced energy intake, spread in moderate amounts across the day and after
hard sessions — about 0.3 g/kg after key sessions and every 3–5 hours
(DC edition p. 17). Page numbers are the edition's printed ones.

The bands are **whole-day intake**, to be fine-tuned to the individual. Three
meals rarely reach them — on the example as it stood before snacks, training
days' meals came to between half and nine-tenths of the band's bottom
([the measurement](/questions/daily-carbohydrate-targets.md)) — so a day carries
a line of **snacks** that closes the gap:

- **Treated as a fuel line is**: `guidance` and an `example` of food. Never on
  the shopping list, never checked, and no time of day.
- **A line is an instruction, so it appears only on a day that falls short.** The
  day's band at the athlete's stated weight, less the meals' carbohydrate — each
  dish's, and anything in `extra` estimated from its label — and the fuel lines'
  food, taking the middle of a table range, gives `at least` the shortfall to the
  band's bottom and `up to` its top, rounded to 10 g; the example food makes up
  the first figure. A day that already reaches the bottom, or falls short by less
  than rounds to 10 g, has no carbohydrate line. `and some protein` where the
  meals are under 1.2 g/kg, and a day short of protein alone says `some protein;
  the carbohydrate is covered`.

  **An *up to* line was tried and taken out**: `up to about 80 g of carbohydrate,
  e.g. 1 apple, 1 pot of fruit yoghurt, a handful of pretzels` meant the day was
  already fed and snacks were optional, and it read as *eat these*. A small-caps
  label and concrete food make any line an instruction, so the only honest
  optional line is none.
- **Food eaten with a dish every time is in its recipe.** Bread with the soup is
  an ingredient line, so its carbohydrate is in the dish's `nutrition` and the
  arithmetic counts it exactly; `extra` is left for what varies between sittings
  or carries next to nothing. A review found the example's Monday snack line
  existed only because its soup's sourdough, then an `extra`, was never counted.
- **The meals still carry the ranking.** Check 10 compares meals alone, so snacks
  top a day up and never stand in for a hard day's bigger plates.

**Measured, 2026-09-30, twice**, on four simulated hosts — three Opus, one
Sonnet — each with its own copy of the skill and an athlete whose opening message
answered everything: a 70 kg UK triathlete twice, a 58 kg vegetarian marathoner,
and an 82 kg lactose-intolerant cyclist planning Thursday to Sunday.

- **First round**, with a line on every day: every plan checked clean on the first
  run, no host searched the web, no snack food reached a shopping list, and every
  day's range reproduced from that host's own meals and fuel. Two hosts put a
  one-hour easy run in the moderate band and two in the light one; the rows now
  say an easy hour or less is light.
- **Second round**, minimum-first and only on short days: every plan clean on the
  first run, no web search, no line led with *up to*, and lines went only to days
  short of their band's bottom — 7 of 25 days, each `at least` figure reproducing
  from the host's own meals and fuel, each example making up that minimum. The
  easy hour went to the light band in every run. An hour's hard swim with an easy
  45-minute run was read as moderate in this round and as high in the first,
  about 20–60 g between a line and none, so the rows now count only sessions at
  moderate intensity or harder.
- **Third round**, after the review's fixes: every plan clean, one after a
  repair round for shopping rounding; no web search; every line reproducing from
  the host's own meals and fuel, taking a range's middle. The hard swim with an
  easy run went to the moderate band in both runs that met it. The protein-only
  line appeared for the first time, on three days of the marathoner's week. No
  host wrote an `extra` at all, so moving served-every-time food into recipes was
  not exercised. One host gave a one-hour hard swim no fuel lines, a miss in the
  fuel rules rather than the snacks, which the snack line then made up.
- **Not measured**: a real host; Haiku; a host without Python, whose reply prints
  the line; a race week; a plan whose meals carry an `extra`; and whether any
  athlete eats to the line.

**Inferences, and they need a professional:**

- T16's rows describe a training *programme*; the skill applies them day by day,
  to what each day holds.
- The moderate row is T16's *moderate exercise programme, ~1 h a day*, which
  states no intensity. The skill reads it as an hour at moderate intensity or
  harder, puts an easy hour or less in the light row, and counts only sessions at
  moderate intensity or harder toward a day's hours. An hour of hard work could
  equally be read as the bottom of the high row.
- A day between two rows takes the lower; a rest day, and every day of an
  undescribed week, takes the light row, since T16 gives no rest-day row; the day
  before the week's biggest session takes that session's row.
- The protein test counts the meals alone; fuel food such as a yoghurt after a
  swim is not counted toward it.
- T16 notes that when a session's quality or intensity matters less, reaching
  these targets matters less. The skill applies them to every day, easy days
  included, and leaves the fine-tuning to the athlete and their coach.

## What an example's food adds up to

A line's `example` has to add up to its `guidance` over the session's hours, so
the rules carry a table to do the arithmetic with:

| item | carbohydrate | source |
|---|---|---|
| 1 bottle of isotonic drink (500 ml) | 30–40 g | USDA FDC 1459988; K17 (0.061–0.08 g/ml) |
| 1 energy gel | 21–27 g | a range across two commercial gels; no single product |
| 1 energy bar | 43 g | USDA FDC 2659987 |
| 1 banana | 27 g | USDA FDC 173944 (26.9 g) |
| 1 date | 5–18 g | USDA FDC 171726 and 168191, by variety |

These are US products' label values; no other country's labels were checked.

## Why the ranges are not higher for trained athletes

Asked whether *30–60 g an hour* is too low for a trained athlete on a 1 h 45
threshold ride:

- **The ranges are already written for trained athletes.** J14's Fig. 1 says so;
  aspiring athletes are told to go lower.
- **Training status does not change what is absorbed** — J14 §6 reports trained
  and untrained oxidising 0.95 against 0.96 g/min.
- **Weekly volume is not a proxy for a trained gut.** What the sources tie
  tolerance to is practice eating during exercise, which a week's description
  cannot show.
- **Gut training changes symptoms, not a number** — no source gives the g/h it
  adds.
- **Intensity is the one thing that moved**: a hard session over 90 minutes takes
  the top of its range.

# A published range is not an invented figure

The rule against printing a figure the athlete did not give covers
**measurements of their week** — hours, distances, a load score. A carbohydrate
or fluid range measures nothing they did; it is guidance, like the g/kg race
targets, and the rules say so beside the rule it could be read as breaking.

# Race weeks

The **distance** drives the shape of the week. The carbohydrate is in the meals
of the days before; the race is a session with its own lines.

| Race | Carbohydrate before it | Source | Needs a professional |
|---|---|---|---|
| under ~90 min — a 10K for almost anybody | roughly 7–10 g/kg the day before | T16 Table 2; B19 p. 121 | No |
| half marathon or longer | roughly 10–12 g/kg on each of the two days before, unless run in under ~90 min | T16 Table 2, loading; p. 557 | **Inference:** that a non-elite half runs over 90 min |

Targets are **per kilogram**, which is why body weight is required.

**A race without its distance is not inferred.** The week is planned
conservatively and the training summary says race-day fuelling assumes nothing
about distance. The skill could ask, since it is in a conversation, but its rules
do not tell it to.

**A race day is the hardest day of its week**, even though nothing in a
description makes it look like a long session. It is ranked first, the summary
says so, and the day's `session` names the race — and
[check 10](/architecture/the-validator.md#check-10-the-plan-against-its-own-ranking)
then holds its meals to that.

# Sources

A literature read, not a sports dietitian's review; the *Needs a professional*
column says where that matters most.

- **T16** — Thomas, Erdman & Burke, *Nutrition and Athletic Performance*, MSSE
  48(3):543–568, 2016.   Thresholds cross-checked against the Dietitians of Canada edition, because the
  publisher PDF renders `<` and `>` wrongly. The DC edition is open access:
  <https://www.dietitians.ca/DietitiansOfCanada/media/Documents/Resources/noap-position-paper.pdf>
- **J14** — Jeukendrup, *A step towards personalized sports nutrition*, Sports
  Med 44 Suppl 1, 2014.
- **K17** — Kerksick et al., *ISSN position stand: nutrient timing*, JISSN 14:33,
  2017.
- **B19** — Burke, Jeukendrup, Jones & Mooses, IJSNEM 29(2):117–129, 2019.
- **S14** — Shaw, Boyd, Burke & Koivisto, *Nutrition for Swimming*, IJSNEM
  24(4):360–372, 2014.
- **Sawka et al. 2007**, *Exercise and fluid replacement*, MSSE 39(2):377–390,
  as cited in T16.
- **J17** — Jeukendrup, *Training the Gut for Athletes*, Sports Med 47 Suppl 1,
  2017; the gut-training reading.
- **PW22** — Podlogar & Wallis, *New Horizons in Carbohydrate Research and
  Application for Endurance Athletes*, Sports Med 52 Suppl 1, 2022.
- **M26** — Morton et al., *From Metabolism to Medals*, J Nutr 156(5):101442,
  2026; the authors declare ties to a sports-nutrition company.
- Gut training and dose: Martinez et al. 2023 and King et al. 2018 in full; Cox
  et al. 2010, Costa et al. 2017 and Miall et al. 2018 from the abstract only.
- **USDA FoodData Central** — label values for the per-item table: banana 173944,
  energy bar 2659987, isotonic drink 1459988, dates 171726 and 168191.
