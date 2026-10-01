---
type: Module
title: The evals
description: On-demand behavioural tests for training-week-meal-plan, outside the skill and never released. A headless agent, kept to its own folder, plans a fixed athlete's race week; script checks and a tool-less judge grade it, as pass rates.
tags: [architecture, testing, evals]
timestamp: 2026-10-01T13:06:44Z
sources: [evals/**]
source_commit: 7fb6472b4ab1212455f9834dc081fb9ac778e05c
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
- **What it leaves**: its session under `~/.claude/projects/`, as every Claude
  Code session does, which the nudge needs to resume it.

**The skill's folder is named for the skill.** Claude Code names a skill after
its folder, whatever its frontmatter says: the first run installed the copy as
`skill`, the agent guessed at `meal-plan`, was refused, and wrote a week in prose
with no plan. Every run now records whether the agent was offered the skill
(`skill-installed`) apart from whether it used it (`skill-used`). A run the
skill was never offered to is set aside, with one that was killed before it
finished and one the API turned away every time, in a row of its own: counting
them would grade the harness or the account. A run that runs out of time or
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
  dish a meal names a recipe, which
  [the validator does not check](/architecture/the-validator.md#check-10-the-plan-against-its-own-ranking).
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
  - **The vegan check reads only names of food** — dishes, ingredients, the
    list, fuel and snack examples — so `Dairy, Eggs & Chilled` and *no eggs or
    honey* in a summary do not fail it, and takes `oat milk`, `peanut butter`
    and `egg-free` as plant food. Meat and fish need a word that says so —
    `vegan`, `tofu`, `-style` — since `coconut chicken curry` is chicken. A
    regular expression could not do all of that.
- **A judge**: an agent with no tools that reads the message, the plan and the
  reply, and answers `yes`, `no` or `unclear` with a reason. It takes what a
  script cannot read: whether the summary is honest, whether a dinner is light,
  whether a race's example food adds up over the race. Questions are worded so
  that `yes` is right, and some are asked of every run. **A question that rests
  on one of the skill's rules quotes it**, since the judge never reads the
  skill: asked only whether a 10K's fuel lines fit the race, it answers from its
  own idea of sports nutrition.

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

# Measurements

**2026-10-01, the seven cases three times each on Opus 5.5**: 21 runs, seven at
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
  dishes no recipe had ([#13](https://github.com/4e6/skills/issues/13)), and the
  reply said the lunches and dinners differ from recent weeks when there were
  none, which step 2 says never to do.

**Not yet**: more than one run on a small model.
