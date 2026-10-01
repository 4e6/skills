# Evals

Behavioural tests for the skills: an agent runs a skill on a fixed athlete,
and what it wrote is graded. They are run by hand when a change to a skill's
behaviour needs measuring. They are never run in CI, and never released: a
skill's zip is built from its own folder, and nothing here is in it.

Only `training-week-meal-plan` has them so far: six race weeks, from a 10K to
an Ironman, and a control week with no race.

## Running them

You need the `claude` command line, signed in, and Python 3.9 or newer. Each run
is one agent writing a whole week, which takes several minutes and costs real
money, so start small:

```sh
python3 evals/training-week-meal-plan/run.py list
python3 evals/training-week-meal-plan/run.py run --case race-10k-saturday --runs 1
python3 evals/training-week-meal-plan/run.py run
```

The last is every case three times, seven runs at once: about 20 minutes and
$35 on Opus. `--jobs` changes how many run at once. The limit is your account's
rate limit, not the machine (a run is one `claude` process of about 0.7 GB,
mostly waiting on the model): much wider than seven and the runs slow each other
down. A run the API turns away is started again, twice at most.

`--model` picks the agent's model and `--judge-model` the judge's (default
`opus`); `--no-judge` runs the script checks alone. Results land in
`evals/training-week-meal-plan/results/<time>[-label]/`, which git ignores. For
each run it keeps the plan, the page, the reply, the transcript and
`result.json` with every grade, and the folder keeps a copy of the skill that
ran.

### Before and after

Run the same cases on the skill as it was and as it is, then put them side by
side:

```sh
python3 evals/training-week-meal-plan/run.py run --skill-ref main --label before
python3 evals/training-week-meal-plan/run.py run --label after
python3 evals/training-week-meal-plan/run.py report evals/training-week-meal-plan/results/*-before evals/training-week-meal-plan/results/*-after
```

Without `--skill-ref` the skill comes from the working tree, uncommitted edits
included. `grade RESULTS` grades a results folder again without running the
agent, for when a check or a judge question changes. It applies the cases as
they are now to the messages the runs were given then, and with `--no-judge` it
drops the judge's earlier answers rather than keeping ones it did not check.

## What a run sees

Each run starts in a new folder outside any checkout, with the skill under test
installed as a project skill: none of your skills, memory, CLAUDE.md or MCP
servers. It can read, write and search inside that folder only, and run shell
commands in Claude Code's sandbox, which writes only in that folder, reads
nothing in your home folder and never reaches the network. It has nothing that
publishes, browses the web or puts up a menu, and it may not open the page it
makes. What it does leave is its session, under `~/.claude/projects/`, as every
Claude Code session does, and an empty entry there for each judge.

Because the shell reads nothing in your home folder, `python3` must not resolve
to a shim there (pyenv, asdf): the agent would find no Python and hand over an
unchecked plan. A system or Homebrew Python is fine.
The athlete's message gives everything the intake asks for, with next week's
dates worked out on the day it runs. An agent that asks a question anyway is
told once to go ahead, and the run records that it asked.

## How a run is graded

- **Script checks** (`checks.py`) read the plan and give the same answer every
  time: the plan is the skill's own `validate.py` clean, every dish a meal names
  has a recipe (which `validate.py` does not check), it covers the right
  days, the race is ranked first and named as one, a loading day is fed in its
  band and an ordinary day is not, a long race's `during` line gives 60–90 g an
  hour, and a vegan plan names no animal food. A day's band is read back from
  its snack line: meals, fuel and the line's `at least` come to the band's
  bottom, and with its `up to` to its top. The total alone cannot tell 7–10 from
  10–12, because snacks top every day up to its band's bottom.
- **The judge** is an agent with no tools that reads the athlete's message, the
  plan and the reply, and answers each question `yes`, `no` or `unclear` with a
  reason. Some questions are asked of every run (the summary, invented figures,
  restrictions, no claim to have varied on earlier weeks, the disclaimer), some
  of every race week, and some by one case.

`report` prints how often each check passed and each question was answered
`yes`, per case. A run that says nothing about the skill is set aside in a row
of its own and counted nowhere else: the agent was never offered the skill, the
run was killed, or the API turned it away three times. Every other run counts:
one that runs out of time is graded on whatever plan it wrote, one with no plan
fails every check on the plan, and a judge that fails answers `unclear` to
every question.

## Adding a case

A case is one JSON file in `evals/training-week-meal-plan/cases/`, named for its
`id`:

- `message`: the athlete's message, one string per line. `{Mon}` to `{Sun}`
  become next week's dates (`Monday 5 October`).
- `weight_kg`: the weight the message gives, which the per-kilogram checks use.
- `race`: whether the week holds a race, which adds the race-week questions.
- `checks`: script checks from `checks.py`'s `CHECKS`, each with what it needs:
  a `day`; a `min` and `max` in g/kg for a band, or `below` for the band a day
  must stay under; a `pattern`. An `id` names one where the default would
  repeat.
- `judge`: the case's own questions, each with an `id`. Word them so that `yes`
  is the right answer.
