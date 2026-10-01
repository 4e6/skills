---
type: Module
title: The evals
description: On-demand behavioural tests for training-week-meal-plan, outside the skill and never released. A headless agent, sealed off from the machine, plans a fixed athlete's week; script checks and a tool-less judge grade it, as pass rates.
tags: [architecture, testing, evals]
timestamp: 2026-10-01T12:16:28Z
sources: [evals/**]
source_commit: 777a0f7fd1cbd29d4601f036f794fd3fd9f2505e
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

# Outside the skill, and run by hand

- **Not in the skill's folder.** The zip is `git archive` of that folder
  ([the zip release](/architecture/the-zip-release.md)), so anything there ships
  to athletes, and judge questions with their expected answers would cost them
  context or tempt an agent browsing the folder.
- **Not in CI.** A run is one agent writing a whole week: minutes and real money
  each, and different every time. Each case runs several times and is reported
  as a pass rate, never as one verdict.

# A run sees the skill and nothing of the machine

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
- **The shell is Claude Code's sandbox**, writing only in the run's folder and
  never reaching the network, with every command allowed inside it. An allowlist
  of commands came first and refused `cd <folder> && python3 …` and
  `python3 …; echo "exit $?"`. Hosts treated one refusal as no Python at all,
  as the skill tells them to, and handed over unchecked plans, which graded as
  the skill's fault.

**The skill's folder is named for the skill.** Claude Code names a skill after
its folder, whatever its frontmatter says: the first run installed the copy as
`skill`, the agent guessed at `meal-plan`, was refused, and wrote a week in prose
with no plan. Every run now records whether the agent was offered the skill
(`skill-installed`) apart from whether it used it (`skill-used`), so the harness
failing never reads as the skill failing.

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
  dish a meal names a recipe, which
  [the validator does not check](/architecture/the-validator.md#check-10-the-plan-against-its-own-ranking).
  - **A day's carbohydrate is its meals plus the snack line's `at least`
    figure**, the shortfall the host worked out itself. Fuel lines are not
    counted, so a case asks this only of days whose sessions carry no fuel.
  - **Bounds are the published range, 5% wide either side**, since the rules say
    *roughly*.
- **A judge**: an agent with no tools that reads the message, the plan and the
  reply, and answers `yes`, `no` or `unclear` with a reason. It takes what a
  script cannot read: whether the summary is honest, whether a dinner is light,
  whether a race distance was assumed. Questions are worded so that `yes` is
  right, and some are asked of every run.

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
- Which country a plan cooks for, [an open issue](https://github.com/4e6/skills/issues/10)
  these cases could carry.

# First measurements

2026-10-01, one run per case, so anecdotes rather than rates. A pass costs about
$12: $1.40–1.70 a run on Opus, and $0.10–0.20 for the judge.

- **Opus 5.5, all seven cases: every script check passed.** The loading days
  came to 7.0 g/kg before the 10K; 10.0 and 10.0 before the half; 10.1 and
  10.1 before the vegan half; 6.9 on the Saturday alone before the sub-90 half,
  inside the 5% band, with Friday unloaded at 4.4. The control's Friday and
  Saturday stayed at 3.1 and 6.5. The judge said `no` once: a reply wishing an
  athlete *hoping for about 1:55* luck *for sub-1:55*.
- **An earlier pass, discarded**, ran under the command allowlist, and two hosts
  handed over unchecked plans because of it. One thing in it was the skill's and
  not the harness's: a vegetarian's list bought plain parmesan, usually made
  with animal rennet, and refried beans, which in the US are often made with lard.
- **Haiku 4.5, the 10K case once**: a clean check, with two meals naming dishes
  no recipe had ([the validator's gap](/architecture/the-validator.md#check-10-the-plan-against-its-own-ranking)),
  and a reply saying the lunches and dinners differ from recent weeks when there
  were none — what step 2 says never to do.

**Not yet**: three runs per case, and more than one run on a small model.

