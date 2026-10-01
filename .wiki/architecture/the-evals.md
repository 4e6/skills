---
type: Module
title: The evals
description: On-demand behavioural tests for training-week-meal-plan, outside the skill and never released. A headless agent, kept to its own folder, plans a fixed athlete's race week or an ordinary week abroad; script checks and a judge grade it.
tags: [architecture, testing, evals]
timestamp: 2026-10-01T21:38:33Z
sources: [evals/**]
source_commit: d50e1524b262a45d4613b1900179681b7eda1d55
---

# What they are for

`validate.py` checks a plan's arithmetic. Nothing checked whether an agent using
the skill writes the right plan, and [editing a skill](/conventions/editing-a-skill.md)
forbids cutting prose on argument alone for that reason. The evals are the
measurement: an agent runs the skill on a fixed athlete, and what it wrote is
graded. Race weeks came first, because their figures are prescribed per
kilogram and a wrong day is easy to name
([carb periodization](/domain/carb-periodization.md#race-weeks)).

# Seven cases: the race distances, and a control

Each case is a distance the rules treat differently, so a wrong band shows up as
a number:

- **a 10K**, the day before at 7–10 g/kg;
- **a half marathon**, the two days before at 10–12 g/kg, and **one run in
  under 90 minutes**, loaded like the shorter race;
- **a 5-hour gran fondo, a half Ironman with a lake swim, and a vegan Ironman**:
  two days loaded, and the race's `during` line at 60–90 g an hour with example
  food that adds up over the race. That line is the one the rules call the
  commonest to get wrong. The triathlons add an open-water swim with nothing
  during it, and the vegan one loading at up to 864 g a day with no animal food;
- **a control**, the half-marathon week with a long run in place of the race,
  so nothing gets loaded or called a race.

The first set held a race given no distance, one on the plan's first day, and a
vegan half marathon. They went to keep the list short: the first two test rules
the long events do not reach, and those are now untested.

# Six countries, one week

The skill says to cook what an ordinary household in the athlete's country
cooks, while up to 1.5.0 nearly every food its own text named as an example
was British: porridge, a bagel with jam, chocolate milk, sourdough, bolognese,
lentil soup. From 1.6.0 it names no food for the `before`, `after` and snack
lines, so what the count finds there is the model's own choice.
The `cuisine-*` cases ask whether those examples pull a plan back to Britain
([#10](https://github.com/4e6/skills/issues/10)): the same training week, weight
and empty fridge for an athlete in Osaka, São Paulo, Pune, Kraków and Denver,
and in Manchester as the control, where the examples are at home. The week is
ordinary rather than a race, with a threshold run and a long run, so the
session lines and the snack lines every day are written, the short lines with a
format to copy, where copying would show first. **The Denver athlete gives
their weight in pounds**, as an American would. Every country case also counts
the units the plan weighs food in, against its country's system, and so does
the gran fondo, whose American gives kilograms: the pair tells the country's
unit from the athlete's. Both US cases also fail a list with a pound in
anything but whole quarters, such as `1.625 lb`, or a row written in another
unit from its pack, which the page cannot count.

**A count of the examples is evidence, not a verdict.** Porridge is an ordinary
breakfast in Poland and in Brazil, and chocolate milk sells everywhere. So the
script counts the examples in the dishes and on the lines, a pass meaning none,
and a judge answers whether an ordinary household there would make each
breakfast, cook each lunch and dinner, and buy the line food without thinking
it foreign, and whether the shops named trade there.

**The judge measures what is foreign, not what was copied.** Chocolate milk on
an Osaka after-line passes it, being on sale there; whether it came from the
skill's example is the count's question. Asked the Osaka questions of a
Manchester week, and the Kraków ones of a Pune week, it answered `no` to all
eight, each naming the dish or the shop, so a `yes` is not a judge that cannot
say no.

**A second line question asks what is typical, not what is foreign**: whether
the food after a session and on a snack line is what people there typically
have at that moment, not merely something on sale there. The first passed every
plan of four versions of the lines; this one told them apart, naming kefir in
Kraków and a rice ball in Osaka where a plan had chocolate milk. It is noisy:
the same Kraków chocolate milk drew `no` in two of three runs of one pass and
`yes` in another, so a difference of one or two runs in eighteen is not one.

# Outside the skill, and run by hand

- **Not in the skill's folder.** The zip is `git archive` of that folder
  ([the zip release](/architecture/the-zip-release.md)), so anything there ships
  to athletes, and judge questions with their expected answers would cost them
  context or tempt an agent browsing the folder.
- **Not in CI.** A run is one agent writing a whole week: minutes and real money
  each, and different every time. Each case runs several times and is reported
  as a pass rate, never as one verdict.

# A run sees the skill and as little of the machine as it can

Each run is the agent's command line in a new folder outside any checkout, with
the skill copied in as a project skill. Every choice below removes something that
would otherwise answer instead of the skill:

- **Project settings only**, so none of the author's own skills, memory or
  `CLAUDE.md`. Started inside this checkout, a run would load this repository's
  `CLAUDE.md` and its wiki instructions, which is why the folder is outside it.
- **No MCP servers.** The author's machine has a meal-plan server and a training
  calendar, either of which would plan the week itself.
- **A fixed set of tools**: read, write, search, and a shell. Nothing that
  publishes (a run would publish pages to the author's account), browses the web
  or puts up a menu. Anything else is refused rather than asked about, so no run
  waits on a person, and `open` is refused so none opens a browser on the
  machine running it.
- **The file tools reach only the run's folder.** Allowed bare, they reach
  anywhere: a run wrote a generator script to `/tmp` and ran it, where seven
  parallel runs could overwrite each other's, and step 2's search for earlier
  plans could find a real one of the author's. **The folder is named by its
  absolute path, in both spellings.** A rule for `./**` let a relative path
  through and refused the absolute one hosts mostly write, `/private/var/…` on
  macOS, where a temporary folder is also `/var/…`: five of the first seven runs
  of a pass had their plan's Write refused, and one handed over its week in the
  reply. Every run now reports anything refused other than `open`, in a row of
  its own.
- **The shell is Claude Code's sandbox**, writing only in the run's folder,
  reading nothing in the home folder (so `python3` must not be a shim there)
  and never reaching the network, with every
  command allowed inside it. An allowlist of commands came first and refused
  `cd <folder> && python3 …` and `python3 …; echo "exit $?"`, and the sandbox's
  own auto-allow still refused heredocs and variable assignments. Hosts treated
  one refusal as no Python at all, as the skill tells them to, and handed over
  unchecked plans, which graded as the skill's fault.
- **The sandbox's temporary folder is shared, so a name there is refused.**
  The sandbox sets every run's `$TMPDIR` to `/tmp/claude-<uid>`, whatever the
  command line is started with, and agents write their generator there. Osaka's
  run patched and ran `$TMPDIR/build.py` after Pune's had written over it, and
  handed over Pune's plan, clean under every script check; only the judge
  caught it ([#26](https://github.com/4e6/skills/issues/26)). Refusing the
  whole folder broke every command: zsh writes each heredoc there and Claude
  Code a `cwd-…` file after each command. Those names have no dot, and an
  agent's (`build.py`, `parts.json`) have one, so the sandbox refuses writing
  `/tmp/claude-<uid>/**/*.*`, in both spellings, and nothing else there.
  **Reading them is refused too**, since the folder keeps whatever any session
  on the machine left, and a run whose write was refused could still run the
  `build.py` already there. That needs Claude Code's own files out of the
  folder, since it keeps each command's output there under a dotted name and
  every command printed nothing: `CLAUDE_CODE_TMPDIR` puts them in `.tmp`
  inside the run's folder. Agents refused `$TMPDIR` find that folder and
  write their scripts there, so it is not under `.claude/`, where Claude Code
  refuses every Write. Heredocs, `python3 -`, `tempfile`, `cd` and background
  commands all still work.
- **What it leaves**: its session under `~/.claude/projects/`, as every Claude
  Code session does, which the nudge needs to resume it.

**The skill's folder is named for the skill.** Claude Code names a skill after
its folder, whatever its frontmatter says: the first run installed the copy as
`skill`, the agent guessed at `meal-plan`, was refused, and wrote a week in prose
with no plan. Every run now records whether the agent was offered the skill
(`skill-installed`) apart from whether it used it (`skill-used`). A run the
skill was never offered to is set aside, with one that was killed before it
finished, one the API turned away every time, and **one another run's files
reached**, in a row of its own: counting them would grade the harness or the
account. The last is a plan byte for byte another run's, or a file in the
shared temporary folder that another run named between two of this run's own
uses of it, by the transcripts' timestamps. It catches what the refusal lets
through, a name with no dot or a shared path still to turn up, and `report`
looks across every folder it is given, since a before and an after are often
run at once. **A copy of a run is not another run**: a folder copied to grade
it again, or a rerun copied into its pass, has the same session, and review
found `report` setting aside all 42 runs of a pass beside its copy. `report`
works the crossing out afresh each time, so a rerun clears a mark `run` saved. A run that runs out of time or
writes no plan counts, and fails every check on the plan, so a pass rate is
never flattered by the runs that went worst.

**The athlete says everything in the first message**: the days with their dates,
the week, the weight, the country, restrictions and the fridge. A run needs
nobody to answer it, and the intake is not what is tested. The dates are next
week's, worked out on the day it runs, because the agent's context carries the
real date and the skill refuses to plan a day already gone. An agent that asks
anyway is told once to go ahead, and the run records that it asked.

# Seven at a time

The limit on parallel runs is the account, not the machine. A run is one
`claude` process of about 0.7 GB, mostly waiting on the model, and the author's
machine has 15 cores and 48 GB. Every run shares the account's rate limit, so
much wider and they slow each other down, or are turned away. Seven is one wave
of the seven cases, so the default three runs each take three waves, about 20
minutes, where one at a time took two hours. Jobs go out run by run rather than
case by case, so a pass stopped early still has every case once. A run the API
turns away starts again from nothing, twice at most: the skill never got a fair
go, and counting it would grade the account.

# Two layers of grading

- **Script checks**, the same answer every time. They reuse `validate.py` from
  the copy of the skill that ran, so a day's food is counted the way the skill's
  own checker counts it. Every plan must be clean under it, and must give every
  dish a meal names a recipe. The validator checks that itself from 1.1.1
  (`dish-without-recipe`, after the first eval run found the gap), and the evals
  keep their own check for runs of a skill from before it. **Every counted row
  on the list must be a whole number**, in every case: a half count is what no
  shop sells, and `validate.py` lets it through on a row it cannot compare,
  such as one whose recipe writes `half, diced`.
  - **A day's band is read back from its snack line.** The host works out the
    line as the gap from the day's meals and fuel to its band's bottom (`at
    least`) and top (`up to`). The first version took meals plus `at least` and
    checked it against a range, and review showed that could not tell a day
    loaded at 10–12 g/kg from one fed at 7–10: the snacks top every day up to
    its band's bottom, so a wrongly loaded day measures 10.0, inside 7–10. Now
    the bottom must be reached and the top must be the band's. **A day with no
    snack line has no top to read**, so one whose meals alone reach a higher
    band's bottom still passes; meals rarely come that close.
  - **Fuel-line food is counted** from the fuelling table's items at each
    range's middle; anything else on a line is not.
  - **Bounds are 5% wide either side**, since the rules say *roughly*.
  - **The skill's example foods are counted** in a country case's dishes and
    on its lines, by name, and the US case's weights and volumes by system.
  - **The aisle headings are read off the page**, the one check that does:
    the plan's categories are the same fixed keys in every country, so
    whether a US shopper reads *Tins* is the renderer's doing. The check
    renders the plan again with the copy of the skill that ran, rather than
    reading the agent's own page, which a run may not have made; a US case
    fails on *Tins*, *Chilled*, *Fruit & Vegetables* or *Meat & Fish*, a
    metric one on *Canned*, *Refrigerated*, *Produce* or *Seafood*.
  - **The vegan check reads only names of food** — dishes, ingredients, the
    list, fuel and snack examples — so `Dairy, Eggs & Chilled` and *no eggs or
    honey* in a summary do not fail it, and takes `oat milk`, `peanut butter`
    and `egg-free` as plant food. Meat and fish need a word that says so —
    `vegan`, `tofu`, `-style` — since `coconut chicken curry` is chicken. A
    regular expression could not do all of that.
- **A judge**: an agent with no tools that reads the message, the plan, the
  shopping list as the page prints it, and the reply, and answers `yes`, `no` or
  `unclear` with a reason. It gets the printed list from 1.5.0's measurement on:
  reading only the JSON, it took a row's `pack`, which the page never prints,
  for a can size. It takes what a script cannot read: whether the summary is
  honest, whether a dinner is light, whether a race's example food adds up over
  the race. Questions are worded so that `yes` is right, and some are asked of
  every run. **A question that rests on one of the skill's rules quotes it**,
  since the judge never reads the skill: asked only whether a 10K's fuel lines
  fit the race, it answers from its own idea of sports nutrition. A case that
  names the athlete's **country** gets four more: breakfasts, lunches and
  dinners, the line food, and the shops.

# Against the method the bundle used before

The measurements recorded elsewhere here used subagents as hosts, a responder
playing a frozen athlete, and a blind pairwise judge per scenario
([editing a skill](/conventions/editing-a-skill.md#how-a-change-to-behaviour-is-measured)).
The evals keep the isolated host and give up two things:

- **No responder**, since every case answers everything up front. Testing the
  intake needs one.
- **No pairwise judge yet.** A change is measured as pass rates before against
  after, the skill taken from any git ref, side by side. A blind X-against-Y
  judgement, which catches what an absolute question misses, is still to build.

# Not covered

- The intake's menus, and anything else that needs a person answering.
- Hosts with no Python, which change how a batch is sized
  ([when there is no page](/architecture/the-handover.md)).
- Web search, which 1.1 stopped forbidding and which the evals take away.
- Any agent but Claude Code. The adapter keeps the agent's command line apart
  from everything else, so another can be added.
- An athlete who names no country, where the skill says to cook something
  unremarkable rather than guess at a cuisine.

# Measurements

**2026-10-01, the country cases three times each on Opus 5.5, on four versions
of the line examples** ([#10](https://github.com/4e6/skills/issues/10)): 72 runs,
about $116, graded together once the second line question existed.

- **1.4.0**: the British examples, `1 bottle of chocolate milk` on an `after`
  line and `1 bagel with jam, 1 banana` on a snack line.
- **Three countries**: each line's example in a British, a Mexican and a
  Turkish version, and a line's food said to be the athlete's country's.
- **From the week**: a line's food taken from what the week's meals use, with
  examples fine anywhere, `1 glass of milk, 1 banana`.
- **1.6.0**, this change: a line's food is what people in the athlete's country
  have at that moment, from the week's food where that is what they would
  have, and the text names no food for these lines at all.

| 18 runs each | 1.4.0 | three countries | from the week | 1.6.0 |
|---|---|---|---|---|
| `after` lines with chocolate milk, of 36 | 26 | 17 | 0 | 21 |
| `after` lines with milk and a banana, of 36 | 2 | 4 | 25 | 6 |
| judge: the lines are what people there typically have | 14 | 16 | 14 | 18 |
| judge: no line food is foreign there | 18 | 18 | 18 | 18 |
| porridge or oatmeal breakfasts, of 126 | 50 | 43 | 40 | 48 |

- **Whatever the text names spreads.** The three countries' `milk blended
  with a banana` turned up word for word three times in São Paulo, and as
  `milk blended with 1 banana` once in Pune. From the week's `1 glass of milk,
  1 banana` was 25 of 36 `after` lines, every one in Manchester and Denver, and
  pushed out the kefir, lassi and rice balls the other passes had.
- **Most of 1.4.0's chocolate milk was the model's own.** With no food named,
  it stayed on every São Paulo, Manchester and Denver `after` line, where the
  judge called it typical (the achocolatado of São Paulo); on half of Kraków's,
  the other half kefir with a sweet yeast bun or a bread roll; and on none of
  Osaka's (a rice ball and a carton of milk, once drinking yoghurt) or Pune's
  (milk and a banana, a sweet lassi).
- **The breakfasts were the model's own in every version.** Porridge stayed at
  11 to 14 of 21 Kraków breakfasts and 13 to 14 of Manchester's, and oatmeal at
  10 to 14 of Denver's, whatever the text said. The dinners and the shops were
  local throughout.
- **A copy of a harmless example is still a copy**: while the text gave the
  `before` line `1 banana, black coffee`, it came back word for word on 5, 6
  and 1 of 36 lines in the three passes that had it.
- A script check for the from-the-week rule, counting line food the week's
  recipes and list name, passed 18 of 18 on that draft and 2 of 54 elsewhere,
  and went with the rule.
- One Osaka run on the three-country draft handed over a Pune plan through the
  shared temporary folder (above), and was run again. Graded again with that
  check, no run in the four passes had been reached by another.

**2026-10-01, the country cases and the gran fondo once each on Opus 5.5**,
skill 1.5.0, with the shared temporary folder closed
([#26](https://github.com/4e6/skills/issues/26)): 7 runs at once, 7 minutes,
$10, script checks only. **Every plan validated clean, nothing was refused but
`open`, and no run was set aside.** Pune and Denver wrote their generator to
`$TMPDIR/gen.py` as before, were refused, and within a minute wrote it in the
run's `.tmp` instead; Denver first tried which names got through, and wrote
`$TMPDIR/genprobe`, the gap the setting aside is for. Each run took 4.0–6.3
minutes, as before. A wave on the first version, which refused only writes and
left Claude Code's files in the shared folder, found their folder there and was
refused the Write tool on it twice, which is why `.tmp` is in the run's folder.

**Graded again**, three of the day's earlier passes besides Osaka's had runs
another had reached, 7 runs: Kraków appended its days to the gran fondo's
`build.py` and noticed, and one Denver run ran the other's two seconds after it
was written. Their grades were their cases' usual ones, Denver's example foods
failing as in every Denver run, so no finding below changes.

**2026-10-01, the two US cases three times each on Opus 5.5**, 1.5.0 rebased
onto 1.4.0's ounces ([#23](https://github.com/4e6/skills/issues/23)): 6 runs, 6
minutes, $10. **Both rules held together.** Every list was whole in its
counts, wrote no pound but a whole quarter and no row in another unit from its
pack, and every drained can printed its count first (`2 cans (18 oz drained)`,
`3 cans (12 oz drained)` of tuna), 9 rows. The judge said every list could be
bought as written, 6 of 6. Its two `no`s were the ones below: Denver's week
added up to *~5h20* for 5h10, and the gran fondo ridden *at roughly tempo*.

**2026-10-01, the country cases and the gran fondo three times each on Opus
5.5**, skill 1.3.0 with 1.5.0's change, whose list rounds a count up to the
whole number and whose page prints a drained can as `1 can (9 oz drained)`
([#23](https://github.com/4e6/skills/issues/23)): 21 runs, 19 minutes, $36.
Against 1.3.0's 21 runs, graded again with the new check and the new judge
input:

- **No list carried a half count**, 21 of 21, where 1.3.0's had one in 8 of
  21: `Bananas 6.5`, `Garlic 15.5 cloves`, `Onions 7.5`, `Lemons 0.5`. Most
  were metric lists. Two runs wrote one and were told by the checker to round
  it up, and did.
- **The judge said every US list could be bought as written**, 6 of 6, where
  1.3.0's Denver run with *6.5 bananas* got its one `no`. Its reasons still
  name `1.312 lb` of oats and `2 tsp` of butter as odd and buyable
  ([#18](https://github.com/4e6/skills/issues/18)).
- **Every drained can printed as one**, on 10 US and 8 metric rows, beans and
  tuna. No tin of tomatoes did. A sauerkraut row with no container printed
  `150 g (drained)`; review found the same of drained spaghetti, so 1.5.0
  marks only a row whose pack names a container.
- The one `no` elsewhere was the gran fondo adding its sessions up to *~9h45*
  for 9h15 and calling the race *tempo effort*, under *nothing invented*, as
  before. `anchor_foods` failed as it did on 1.3.0.

**2026-10-01, the two US cases three times each on Opus 5.5, three times**,
for 1.4.0 ([#18](https://github.com/4e6/skills/issues/18)): 6 runs, 7 minutes
and $10 each time, the last on 1.4.0 merged with 1.3.0's aisle names. That
last run passed every check but Denver's example-food counts, the aisles and
the judge included: two rows in pounds, both whole quarters with no pack
(`Potatoes 1.25 lb`), every other weight in ounces, all 52 rows beside a weighed
pack in its unit, and every list under *Produce* and *Canned Goods, Jars &
Seasonings*. The run before it is described below.

**The rule as released weighs in ounces**, with a pound only for a whole
quarter on a row with no pack, and a row with a pack in ounces like its pack.
Every weight in all six runs was in ounces, not one row in pounds, and all 52
rows beside a weighed pack shared its unit (`Bananas 19 oz` beside a `4 oz`
banana, `Ground turkey 24 oz` beside a `16 oz` pack). No odd-pound finding
fired, and every plan validated clean. Two gran fondo replies called the race a
*tempo effort*, which the judge rightly said the athlete never gave; that is
the reply, not the units. Denver's example-food counts failed, as in every
Denver run.

**The draft before it** wrote a pound only in whole quarters and any other
figure in ounces, and said a row and its pack share a unit, illustrated with the
failure: `2 lb` of bananas beside a `4 oz` banana *prints no count at all*. The
results of that run follow. **One run copied the example exactly**, so an
example of what goes wrong is written as one to follow; the rule now gives
only examples to copy.

**In the draft's run, no list wrote an odd pound**, where 1.2.0 had written one
in two of three gran fondo runs (`1.625 lb` of rice, `3.625 lb` of chicken) and
1.2.0's first draft in four of six.

- Every row in pounds was a whole quarter (`1 lb`, `1.25 lb`, `2.5 lb`,
  `3.75 lb`), and totals that were not went to ounces (`26 oz` of rice,
  `22.5 oz`, `23 oz` of broccoli). Some whole quarters stayed in ounces too
  (`44 oz` of chicken), which the rule allows. Every plan validated clean and
  the judge said yes throughout; Denver's example-food counts failed as in
  every Denver run before (oatmeal, bagels, chocolate milk).
- **The text did it alone.** The validator's new finding for a right row in odd
  pounds never fired in any transcript, and no repair landed on a row in
  pounds. Against the 64 stored plans from before, the released validator
  differs from the old only on 18 rows: the 17 odd ones, and one `Bananas 2 lb`
  beside a `4 oz` banana.
- **One row and its pack still disagreed:** `Bananas 2 lb` beside a `4 oz`
  banana, which prints no count, the text's own example word for word. The US
  cases now check that a row and its weighed pack share a unit.
- *Is it the line on converting body weight?* `fuelling.md` divides pounds by
  2.2046, and that line might have primed the model to convert the food too.
  The stored runs say not: every odd figure was a whole or half number of
  ounces over 16, and most came from the gran fondo, whose athlete gives
  kilograms. The line stayed, and the figures went.

**2026-10-01, the country cases and the gran fondo three times each on Opus
5.5**, skill 1.3.0, whose page prints a US shop's aisle names on a list in US
units ([#20](https://github.com/4e6/skills/issues/20)): 21 runs, 20 minutes,
$35. **No US list printed *Tins*, and no metric list changed.**

- **Every US page read as a US shop's**: *Produce*, *Canned Goods, Jars &
  Seasonings*, *Meat & Seafood*, *Dairy, Eggs & Refrigerated*, in 6 of 6 runs.
  The same check, graded again on 1.2.0's runs, failed all 12, three of Denver
  and three of the gran fondo in each of its two passes.
- **Every metric page kept the plan's own headings**, 15 of 15, as the 15 runs
  of 1.2.0 did.
- **Every plan weighed in its country's system**, 55–77 quantities in US units
  on the US plans and none on the metric ones.
- **What the judge found against it was not the headings**: a Denver list
  bought `6.5` bananas and a `9 oz` can, a can's drained weight as its pack,
  under `shops-in-its-units` ([#23](https://github.com/4e6/skills/issues/23)); a São Paulo page said *~5h20* for sessions adding
  up to 5h10, under *nothing invented*. One Kraków run wrote a script to `/tmp`
  and was refused, its plan finished in its own folder.

**2026-10-01, the country cases and the gran fondo three times each on Opus
5.5**, skill 1.2.0, which says the country picks the units
([#17](https://github.com/4e6/skills/issues/17)): 21 runs, 18 minutes, $34.
**Every plan weighed in its country's system, and nothing else.**

- **Both Americans got US units in every run**: Denver 54 of 54, 56 of 56 and
  60 of 60 weights and volumes, and the gran fondo, whose athlete gives
  kilograms, 62 of 62, 57 of 57 and 55 of 55. Before, the gran fondo had none in
  three runs and Denver none in one of four. The judge said every shopping
  list could be bought in the US as written, six of six.
- **The five metric countries stayed metric**: not one US quantity in 15 runs.
- **Carbohydrate stayed in grams and fluid went to fl oz** on the US fuel
  lines (`60–90 g of carbohydrate an hour; 14–27 fl oz of fluid an hour`), and
  every can on the list and in the recipes was *canned*. The aisle above them
  still read *Tins, Jars & Seasonings*: the categories are a fixed list in the
  schema, which the rule cannot reach
  ([#20](https://github.com/4e6/skills/issues/20)).
- **The pound rule ran into the pack count.** 12 rows stayed in ounces past a
  pound, 9 of them beside a pack in ounces (`Canned black beans 27 oz`, a
  `9 oz` can), which the page can count; three had no pack and broke the rule.
  Four rows went to pounds beside a pack in ounces (`Bananas 2 lb`, a `4 oz`
  banana), and the page, which counts packs only where the two units are
  written alike, printed no count. The rule was then given its exception, a
  row with a pack stays in the pack's unit, and the two US cases run three
  times again (6 runs, 7 minutes, $10): every quantity in US units again, no
  row in pounds beside a pack in ounces, 13 in ounces beside one, and one
  without a pack still in ounces past a pound (`Chicken breast 56 oz`).
- **What is left is odd precision.** A row adds its recipes up exactly, so
  ounces summed into pounds came out as `1.625 lb` of rice or `1.063 lb`, which
  the judge called odd and still buyable. Rounding the row would break
  [the sum it is checked against](/invariants/the-list-buys-what-the-week-uses.md)
  ([#18](https://github.com/4e6/skills/issues/18)).
- The one `no` was the gran fondo's reply calling the race *tempo effort*, an
  intensity the athlete never gave, under *nothing invented*. The example
  foods were where they were in the first country run below — porridge or
  oatmeal in every Kraków, São Paulo, Denver and Manchester week, chocolate
  milk on their after-lines — except that no Osaka or Pune line had chocolate
  milk this time.

**2026-10-01, the country cases three times each on Opus 5.5**, skill 1.1.1:
18 runs, $28: the first five cases in 14 minutes, Denver's three, added after
review, in six more. **The examples did not pull the cooking back to
Britain; the after-session example was copied across.**

- **The judge answered `yes` to every country question in every run.**
  Osaka's weeks were natto rice, ginger pork and udon; Pune's poha, upma, dal and
  rajma; Kraków's rye bread with curd cheese, buckwheat, pierogi and kefir; São
  Paulo's bread rolls, tapioca crepes, rice and beans; Denver's pancakes,
  breakfast burritos and chili. Every closing note named local chains: Gyomu
  Super, Assaí, DMart, Biedronka, King Soopers.
- **The examples in the dishes were ones the country eats anyway**, by the
  judge's reading. Porridge was a breakfast in every Kraków, São Paulo and
  Denver week (as oatmeal in Denver) and in none of Osaka's or Pune's; São
  Paulo's was `Oat porridge with banana and honey` all three times, and two of
  Denver's `Oatmeal with banana, peanut butter and honey`, close to the skill's
  own `Porridge with banana` with honey. Bolognese was a lunch and a dinner in
  one São Paulo week, bagels one Denver week's breakfast. Sourdough and lentil
  soup appeared in no run.
- **Chocolate milk after a session was copied across**: on every after-line in
  Kraków, São Paulo and Denver, a third of Osaka's and Pune's, where the others
  were a rice ball with milk, flavoured milk or a sweet lassi. The judge found it
  ordinary everywhere.
- **The units were a coin toss.** Denver's athlete, in pounds, got ounces: 72
  of 72, 54 of 58 and 65 of 65 weights and volumes. The gran fondo's American,
  in kilograms, got grams in all three plans, 0 of 74, 66 and 81 in US units.
  That looked like the athlete's unit deciding, until a fourth Denver run, on
  1.1.2, weighed 0 of 65 in US units for the same athlete in pounds. The skill
  said nothing about units, so the model chose
  ([#17](https://github.com/4e6/skills/issues/17)). The ounces
  ran past a pound (`Potatoes 34 oz`), and Denver's own question, whether a
  shopper there could buy the list as written, was `no` once: milk in
  millilitres, `Butter 1 tbsp` and `Garlic 6.5 cloves`.
- **The control is where the examples were**: porridge at 15 of 21 Manchester
  breakfasts, bolognese in two weeks, a bagel or a crumpet with jam on the
  snack lines.

**What this does not settle.** One model, one week, three runs a country, and
the country typed into the message rather than picked from the intake's menu.
#10's other half, the same cases on other examples, is the measurement of four
versions above: the lines copy what they are given, and the breakfasts were the
model's own.

**2026-10-01, the seven cases three times each on Opus 5.5**, skill 1.1: 21 runs, seven at
a time, 20 minutes, $36. Each run took 4.3–6.6 minutes.

- **Every script check passed in every run.** Every plan passed the checker
  clean, with every dish's recipe present. Every race was ranked first and named
  as a race. The two days before each long race were fed at 10.0–12.0 g/kg in all
  15 measurements, and the day before the 10K at 7.0–10.0 in all three. The sub-90
  half's Saturday came to 7.2–8.3 with its Friday at 4.2–5.2, and the control's
  Friday and Saturday stayed at 3.1–4.0 and 6.1–6.2. Every long race's `during`
  line gave 60–90 g an hour, and two of the triathlons' lines said it starts after
  the swim. The vegan Ironman named no animal food, and no run claimed variety
  against earlier weeks.
- **The judge said `no` three times, all to *nothing invented*, and all real.**
  A 10K's page assumed the race takes 40–60 minutes, a duration the athlete never
  gave. An Ironman's `during` example was sized for about 10 hours on the bike and
  run, taken from the 11h30 target less a swim the athlete never timed. A half
  Ironman's `total` said *~4h25* for sessions that add up to 4h35.

**Earlier, one run per case** of a first set that held a race with no distance,
one on the plan's first day and a vegan half marathon. Every script check
passed, and the race given no distance had none assumed in its session names.
Two things in it were the skill's and not the harness's:

- **Vegetarian groceries:** a vegetarian's list bought plain parmesan (usually
  made with animal rennet) and refried beans (often made with lard in the US).
- **Haiku 4.5, the 10K case once:** the plan checked clean with two meals naming
  dishes no recipe had ([#13](https://github.com/4e6/skills/issues/13), fixed in
  1.1.1), and the
  reply said the lunches and dinners differ from recent weeks when there were
  none, which step 2 says never to do.

**Not yet**: more than one run on a small model.
