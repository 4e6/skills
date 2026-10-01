#!/usr/bin/env python3
"""Run training-week-meal-plan on fixed athletes, and grade what it wrote.

    python3 evals/training-week-meal-plan/run.py list
    python3 evals/training-week-meal-plan/run.py run [--case ID ...] [--runs 3]
        [--skill-ref REF] [--model M] [--judge-model M] [--no-judge] [--jobs N]
    python3 evals/training-week-meal-plan/run.py grade RESULTS [--no-judge]
    python3 evals/training-week-meal-plan/run.py report RESULTS [RESULTS ...]

**Run on demand, never in CI and never released.** A run is one agent writing a
whole week, minutes and real money each, and results vary from run to run, so a
case runs several times and is reported as a pass rate. The release zip is
`git archive` of the skill's folder, which is why none of this lives inside it.

**A case is one athlete, saying everything in one message**: the days with their
dates, the week, the weight, the country, restrictions and the fridge. Nothing
is left for the intake to ask, so a run needs nobody to answer it. The dates
are next week's, worked out on the day it runs, because the agent's context
carries the real date and a week in the past is one the skill refuses to plan.
An agent that asks anyway is told once to go ahead, and the check
`planned-without-asking` records that it asked.

**Two layers of grading.** `checks.py` reads the plan and gives the same answer
every time; the judge, an agent with no tools, answers what a script cannot
read, as yes, no or unclear with a reason. `--skill-ref` runs the skill as it
stood at any git ref, and `report` puts several result folders side by side, so
a change is measured as before against after on the same cases.

Results go to `results/` beside this file, which git ignores: the plan, the
page, the reply, the transcript and the grades of every run, and the copy of the
skill that ran.

Python 3.9, standard library only. It runs git and the agent's command line.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Nothing of a run is left in the checkout: not even the checks' byte-code, nor
# the skill's when a check loads its validate.py.
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))

import agents  # noqa: E402
import checks  # noqa: E402

SKILL = "training-week-meal-plan"
CASES = HERE / "cases"
RESULTS = HERE / "results"
NUDGE = "Go ahead with what I've given you, I don't have anything to add."
# Runs at once. The limit is the account, not the machine: a run is one `claude`
# process of about 0.7 GB, mostly waiting on the model. Seven is a wave of the
# six race weeks and their control, so three runs each finish in three waves,
# about 20 minutes, where one at a time takes about two hours. Much wider and the runs
# share the account's rate limit and slow each other down, or are turned away
# and retried.
JOBS = 7
DEFAULT_JUDGE = "opus"
RETRIES = 2
RETRY_WAIT = 60  # seconds, times the attempt
# A file in the sandbox's temporary folder, which every run's shell shares
# (#26), as a command names it: `$TMPDIR/build.py`, `"$TMPDIR"/gen.py`,
# `os.environ["TMPDIR"]+"/parts.json"` or `/tmp/claude-501/x.json`.
SHARED_FILE = re.compile(
    r"""(?:\$\{?TMPDIR\b\}?|environ\[\s*['"]TMPDIR['"]\s*\]\s*\+\s*|(?:/private)?/tmp/claude-\d+)"""
    r"""['"]?(/[\w.\-]+(?:/[\w.\-]+)*)""")
CROSSED = "another run's files reached it"

# Asked of every run. A question is passed by a `yes`.
COMMON_QUESTIONS = [
    ("summary-honest",
     "Does `training_overview.summary` name the day made the biggest fuel day, and "
     "give a reason for it that matches what the athlete said about their week?"),
    ("nothing-invented",
     "Is every measurement of the athlete's own training that the page or the reply "
     "states (a duration, distance, pace, zone, load score, race distance or goal time) "
     "one the athlete gave? The page is everything in the plan except `week_load`, the "
     "assistant's working, which the skill fills in by its own rules. Published "
     "guidance, such as grams per kilogram or grams per hour, is not a measurement of "
     "their training."),
    ("restrictions-kept",
     "Does every dish, and every example food on the fuel and snack lines, respect "
     "the dietary restrictions the athlete stated?"),
    ("no-recent-weeks-claimed",
     "There were no earlier plans for this athlete to look at. Does the reply avoid "
     "saying that this week's dishes differ from, or were varied against, earlier "
     "weeks' plans?"),
    ("disclaimer",
     "Does the reply say that this is general sports-nutrition guidance rather than "
     "medical or dietetic advice?"),
]
# Asked of every run whose week holds a race.
RACE_QUESTIONS = [
    ("race-eve-dinner",
     "Is the dinner on the evening before the race carbohydrate-led, and not heavy "
     "or fatty?"),
    ("race-fuel-lines",
     "The skill's rules: a race always has a `before` line. Carbohydrate during a "
     "session goes by its length: under about 45 minutes none, only water; about "
     "45-75 minutes of hard work, small amounts or a mouth rinse; one to two and a half "
     "hours, roughly 30-60 g an hour; longer, 60-90 g an hour. A session that carries "
     "fuel has an `after` line, carbohydrate with protein within about 2 hours. Do the "
     "race session's lines follow these rules for the race as the athlete described it?"),
]

# Asked of every run whose case names the athlete's `country`. The skill says to
# cook what an ordinary household there cooks, the breakfast in particular, and
# to name shops that trade there.
COUNTRY_QUESTIONS = [
    ("breakfasts-local",
     "Is every breakfast in the plan one an ordinary household in {country} would "
     "make on a weekday? Name any that would be unusual there."),
    ("main-meals-local",
     "Is every lunch and dinner in the plan one an ordinary household in {country} "
     "would cook on a weekday? Name any that would be unusual there."),
    ("lines-local",
     "Is the example food on the sessions' fuel lines and the days' snack lines food "
     "a person in {country} would buy in an ordinary local shop and eat without "
     "thinking it foreign? Sports products (an energy gel, an isotonic drink, an "
     "energy bar) count as ordinary anywhere. Name any that would not be."),
    ("shops-trade-there",
     "Does every supermarket or shop chain the plan or the reply names trade in "
     "{country}? Answer yes if none is named."),
]

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "answers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "verdict": {"enum": ["yes", "no", "unclear"]},
                    "reason": {"type": "string"},
                },
                "required": ["id", "verdict", "reason"],
            },
        }
    },
    "required": ["answers"],
}


def say(*parts):
    print(*parts, file=sys.stderr, flush=True)


def load_cases() -> dict:
    cases = {}
    for path in sorted(CASES.glob("*.json")):
        case = json.loads(path.read_text())
        if case["id"] != path.stem:
            raise SystemExit("%s: id %r differs from its file name" % (path, case["id"]))
        cases[case["id"]] = case
    return cases


def next_week(today: dt.date) -> dict:
    """`{Mon}` … `{Sun}` as `Monday 5 October`, for the Monday after today."""
    monday = today + dt.timedelta(days=7 - today.weekday())
    return {
        (monday + dt.timedelta(days=i)).strftime("%a"):
            "{d:%A} {d.day} {d:%B}".format(d=monday + dt.timedelta(days=i))
        for i in range(7)
    }


def message(case: dict, today: dt.date) -> str:
    return "\n".join(case["message"]).format_map(next_week(today))


def questions(case: dict) -> list:
    asked = COMMON_QUESTIONS + (RACE_QUESTIONS if case.get("race") else [])
    if case.get("country"):
        asked += [(qid, q.format(country=case["country"])) for qid, q in COUNTRY_QUESTIONS]
    return asked + [(q["id"], q["question"]) for q in case.get("judge", [])]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True,
                          text=True).stdout.strip()


def snapshot(ref: str | None, into: Path) -> dict:
    """The skill as it stands at `ref`, or in the working tree, copied to `into`."""
    source = "skills/" + SKILL
    if ref:
        archive = subprocess.run(["git", "archive", ref, source], cwd=REPO, check=True,
                                 capture_output=True).stdout
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["tar", "-x", "-C", tmp], input=archive, check=True)
            shutil.copytree(Path(tmp) / source, into)
        return {"ref": ref, "commit": git("rev-parse", ref), "dirty": False}
    shutil.copytree(REPO / source, into, ignore=shutil.ignore_patterns(
        "plan.json", "plan.html", "plan-[0-9]*", "photos.json", "photos", "__pycache__"))
    return {"ref": None, "commit": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain", "--", source))}


def plan_in(folder: Path):
    plans = sorted(folder.glob("plan-*.json")) or sorted(folder.glob("plan.json"))
    return plans[-1] if plans else None


def run_one(agent, case: dict, n: int, out: Path, skill: Path, today: dt.date) -> dict:
    out.mkdir(parents=True)
    work = Path(tempfile.mkdtemp(prefix="twmp-eval-")).resolve()
    try:
        agent.install_skill(work, skill, SKILL)
        text = message(case, today)
        transcript = out / "transcript.jsonl"
        turns = [agent.run(work, text, transcript)]
        if plan_in(work) is None and turns[0].session_id:
            turns.append(agent.run(work, NUDGE, transcript, resume=turns[0].session_id))
        for made in list(work.glob("plan*.json")) + list(work.glob("plan*.html")):
            shutil.copy2(made, out / made.name)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    (out / "message.md").write_text(text + "\n")
    (out / "reply.md").write_text(turns[-1].reply + "\n")
    result = {
        "case": case["id"],
        "run": n,
        "turns": len(turns),
        "is_error": any(t.is_error for t in turns),
        "api_error": next((t.api_error for t in turns if t.api_error), None),
        "timed_out": any(t.timed_out for t in turns),
        # Killed before it could finish, by Ctrl-C or a crash: not the skill's doing.
        "interrupted": not all(t.finished or t.timed_out for t in turns),
        "cost_usd": round(sum(t.cost_usd for t in turns), 4),
        "models": sorted({m for t in turns for m in t.models}),
        "skill_listed": SKILL in turns[0].listed,
        "skills": [s for t in turns for s in t.skills],
        "read_skill_md": any((p or "").endswith(SKILL + "/SKILL.md") for t in turns for p in t.reads),
        "tools": [name for t in turns for name in t.tools],
        "denied": [d for t in turns for d in t.denied],
    }
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def excluded(result: dict):
    """Why a run says nothing about the skill, or None when it counts.

    The agent was never offered the skill, the run was killed before it could
    finish, or the API turned it away every time it was tried. Counting any of
    those would grade the harness or the account. A run that ran out of time
    counts: the skill had its go.
    """
    if not result.get("skill_listed", False):
        return "the skill was not installed"
    if result.get("interrupted"):
        return "interrupted"
    if result.get("is_error") and result.get("api_error"):
        return "the API turned it away (%s)" % result["api_error"]
    if result.get("crossed"):
        return CROSSED
    return None


def events(out: Path) -> list:
    """The run's transcript, one event a line, leaving out any that do not parse."""
    transcript = out / "transcript.jsonl"
    found = []
    for line in transcript.read_text().splitlines() if transcript.exists() else []:
        try:
            found.append(json.loads(line))
        except ValueError:
            continue
    return found


def session(out: Path):
    """The agent's session the run was, which a copy of its folder shares."""
    return next((e["session_id"] for e in events(out) if e.get("session_id")), None)


def shared_uses(out: Path) -> dict:
    """{file in the shared temporary folder: when this run's tools named it}.

    `mktemp`'s templates (`mealplan.XXXXXX`) are left out: every run gets its
    own folder from one.
    """
    uses = {}
    for event in events(out):
        if event.get("type") != "assistant" or not event.get("timestamp"):
            continue
        for part in event.get("message", {}).get("content", []):
            if part.get("type") != "tool_use":
                continue
            text = " ".join(str(v) for v in (part.get("input") or {}).values())
            for name in set(SHARED_FILE.findall(text)):
                if "XXX" not in name:
                    uses.setdefault(name.rstrip("/"), []).append(event["timestamp"])
    return uses


def crossed(outs: list) -> dict:
    """{run folder: how} for every run another run's files may have reached.

    The sandbox gives every run's shell the same temporary folder (#26), and a
    run once patched and ran a script there that another run had just written
    over: its folder held a plan of Pune for an athlete in Osaka, and every
    script check passed. `agents.py` refuses the names agents give their files
    there, and this catches what gets through:

    - **a plan byte for byte another run's**, which no two runs write alone;
    - **a file in the shared folder that another run named between two of this
      run's own uses of it**, so what this run read back may have been the
      other's. Their timestamps say when; a run that was done with a file
      before the other began is left alone.

    Such a run grades the harness, not the skill, and is set aside like an
    interrupted one. A copy of a run's folder, kept to grade it again or to put
    a rerun into a pass, is the same session and never another run.
    """
    def name(out):
        return "%s #%s" % (out.parent.name, out.name)

    sessions = {out: session(out) for out in outs}

    def another(out, other):
        return other != out and (sessions[out] is None or sessions[other] != sessions[out])

    how = {}
    by_plan = {}
    for out in outs:
        plan = plan_in(out)
        if plan is not None:
            by_plan.setdefault(plan.read_bytes(), []).append(out)
    for same in by_plan.values():
        for out in same:
            others = [o for o in same if another(out, o)]
            if others:
                how[out] = "its plan is byte for byte %s's" % name(others[0])
    uses = {out: shared_uses(out) for out in outs}
    for out in outs:
        for file, times in sorted(uses[out].items()):
            first, last = min(times), max(times)
            other = next((o for o in outs if another(out, o)
                          and any(first < t < last for t in uses[o].get(file, []))), None)
            if other is not None and out not in how:
                how[out] = "%s used $TMPDIR%s between two of its own uses" % (name(other), file)
    return how


def mark_crossed(root: Path) -> dict:
    """Record in each run's result.json whether another run's files reached it."""
    outs = [p.parent for p in sorted(root.glob("*/*/result.json"))]
    how = crossed(outs)
    for out in outs:
        result = json.loads((out / "result.json").read_text())
        if result.get("crossed") == how.get(out):
            continue
        result.pop("crossed", None)
        if out in how:
            result["crossed"] = how[out]
        result["excluded"] = excluded(result)
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return how


def grade_one(agent, case: dict, out: Path, skill: Path, judge_model, judge: bool) -> dict:
    result = json.loads((out / "result.json").read_text())
    result["excluded"] = excluded(result)
    plan_path = plan_in(out)
    run_checks = [
        # Not the skill's fault when it fails: the agent was never offered it.
        {"id": "skill-installed", "passed": result.get("skill_listed", False),
         "detail": "listed" if result.get("skill_listed") else "the agent's skill list lacks it"},
        {"id": "skill-used", "passed": SKILL in result["skills"] or result["read_skill_md"],
         "detail": "skills: %r" % result["skills"]},
        {"id": "planned-without-asking", "passed": result["turns"] == 1,
         "detail": "%d turn(s)" % result["turns"]},
        # Anything refused but opening the page is the harness in the way, not
        # the skill: a row of its own, so it is seen rather than averaged in.
        {"id": "harness-refused-only-open",
         "passed": all(d.startswith("Bash ") and re.search(r"\bopen\b", d) for d in result["denied"]),
         "detail": "; ".join(result["denied"]) or "nothing refused"},
        {"id": "plan-written", "passed": plan_path is not None,
         "detail": plan_path.name if plan_path else "no plan file"},
    ]
    plan = None
    if plan_path is not None:
        try:
            plan = json.loads(plan_path.read_text())
        except ValueError as error:
            run_checks[-1].update(passed=False, detail="does not parse: %s" % error)
    if plan is not None:
        run_checks += checks.run(plan, case["weight_kg"], skill, case.get("checks", []))
    else:
        run_checks += checks.without_plan(case.get("checks", []))
    result["checks"] = run_checks
    # Written before the judge, so a judge that fails cannot take the checks with it.
    for key in ("judge", "judge_cost_usd", "judge_error"):
        result.pop(key, None)
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    if judge and not result["excluded"]:
        if plan is None:
            result["judge"] = [{"id": qid, "verdict": "no", "reason": "no plan to judge"}
                               for qid, _ in questions(case)]
        else:
            try:
                result["judge"], result["judge_cost_usd"] = ask_judge(
                    agent, case, out, plan, skill, judge_model)
            except Exception as error:
                # Every question stays counted, as unclear, so a judge that
                # failed cannot shrink a pass rate's denominator.
                reason = "the judge failed: %s: %s" % (type(error).__name__, error)
                result["judge_error"] = reason
                result["judge"] = [{"id": qid, "verdict": "unclear", "reason": reason}
                                   for qid, _ in questions(case)]
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def ask_judge(agent, case: dict, out: Path, plan: dict, skill: Path, model) -> tuple:
    asked = questions(case)
    try:
        shopping = checks.shopping_text(plan, skill)
    except Exception as error:  # the page is the skill's to fail, not the judge's
        shopping = "(the page could not be rendered: %s)" % type(error).__name__
    prompt = (HERE / "judge.md").read_text().format(
        message=(out / "message.md").read_text().strip(),
        plan=json.dumps(plan, indent=1, ensure_ascii=False),
        shopping=shopping,
        reply=(out / "reply.md").read_text().strip(),
        questions="\n".join("- `%s`: %s" % q for q in asked),
    )
    with tempfile.TemporaryDirectory(prefix="twmp-judge-") as work:
        answer, cost = agent.judge(Path(work), prompt, JUDGE_SCHEMA, model)
    given = {a["id"]: a for a in answer["answers"]}
    verdicts = [
        given.get(qid, {"id": qid, "verdict": "unclear", "reason": "the judge gave no answer"})
        for qid, _ in asked
    ]
    return verdicts, round(cost, 4)


def cmd_list(args):
    for case in load_cases().values():
        print("%-24s %s" % (case["id"], case["title"]))


def cmd_run(args):
    cases = load_cases()
    chosen, unknown = [], []
    for pattern in args.case or ["*"]:
        matched = [c for c in cases if fnmatch.fnmatchcase(c, pattern)]
        unknown += [] if matched else [pattern]
        chosen += [c for c in matched if c not in chosen]
    if unknown:
        raise SystemExit("no such case: " + ", ".join(unknown))
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = RESULTS / (stamp + ("-" + args.label if args.label else ""))
    root.mkdir(parents=True)
    skill = root / "skill"
    meta = {
        "skill": snapshot(args.skill_ref, skill),
        "agent": args.agent,
        "model": args.model,
        "judge_model": None if args.no_judge else args.judge_model,
        "today": dt.date.today().isoformat(),
        "cases": chosen,
        "runs": args.runs,
    }
    (root / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    agent = agents.AGENTS[args.agent](model=args.model, max_budget_usd=args.max_budget_usd)
    today = dt.date.today()

    def one(job):
        case_id, n = job
        out = root / case_id / str(n)
        say("start  %s #%d" % (case_id, n))
        try:
            spent = 0.0
            for attempt in range(1, RETRIES + 2):
                result = run_one(agent, cases[case_id], n, out, skill, today)
                if not (result["is_error"] and result["api_error"]) or attempt > RETRIES:
                    break
                # The API turned the run away (rate limit, overload): the skill
                # never got a fair go, so the run starts again from nothing.
                say("retry  %s #%d  API error %s" % (case_id, n, result["api_error"]))
                spent += result["cost_usd"]
                shutil.rmtree(out)
                time.sleep(RETRY_WAIT * attempt)
            if spent:
                result["retried_cost_usd"] = round(spent, 4)
                (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
            result = grade_one(agent, cases[case_id], out, skill, args.judge_model,
                               not args.no_judge)
            failed = [c["id"] for c in result["checks"] if not c["passed"]]
            if result["excluded"]:
                say("skip   %s #%d  %s" % (case_id, n, result["excluded"]))
            else:
                say("done   %s #%d  %s" % (case_id, n, "failed: " + ", ".join(failed) if failed else "checks pass"))
        except Exception as error:
            say("ERROR  %s #%d  %s: %s" % (case_id, n, type(error).__name__, error))

    # Run-major, so the first wave holds every case once and a pass stopped
    # early still has something to say about each.
    jobs = [(c, n) for n in range(1, args.runs + 1) for c in chosen]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        list(pool.map(one, jobs))
    # Only once every run is in can one be seen to have reached another.
    for out, how in mark_crossed(root).items():
        say("skip   %s #%s  %s: %s" % (out.parent.name, out.name, CROSSED, how))
    print(report([root]))
    say("results: " + str(root))


def cmd_grade(args):
    cases = load_cases()
    root = Path(args.results)
    meta = json.loads((root / "meta.json").read_text())
    agent = agents.AGENTS[meta["agent"]]()
    model = args.judge_model or meta.get("judge_model") or DEFAULT_JUDGE
    mark_crossed(root)
    for result_path in sorted(root.glob("*/*/result.json")):
        out = result_path.parent
        if out.parent.name not in cases:
            say("skip   %s: no such case any more" % out.parent.name)
            continue
        # The case as it is now, against the message the run was given then:
        # a check that changed is applied to the old run.
        try:
            grade_one(agent, cases[out.parent.name], out, root / "skill", model, not args.no_judge)
        except Exception as error:
            say("ERROR  %s  %s: %s" % (out.relative_to(root), type(error).__name__, error))
    print(report([root]))


def summarise(root: Path, reached=()) -> dict:
    """{case: {row: [passes, runs]}} with the cost, for one results folder.

    A run `excluded` says why it counts for nothing, and is counted only in its
    own row, as is one in `reached`, the run folders another run's files reached.
    """
    table, cost = {}, 0.0
    for result_path in sorted(root.glob("*/*/result.json")):
        result = json.loads(result_path.read_text())
        cost += sum(result.get(k, 0) for k in ("cost_usd", "judge_cost_usd", "retried_cost_usd"))
        rows = table.setdefault(result["case"], {})
        # Crossing is worked out afresh across every folder given, so a mark a
        # rerun has since cleared is not kept.
        why = result.get("excluded")
        if why == CROSSED:
            why = None
        why = why or (CROSSED if result_path.parent in reached else None)
        if why:
            row = rows.setdefault("excluded: " + why, [0, 0])
            row[1] += 1
            continue
        for check in result.get("checks", []):
            row = rows.setdefault(check["id"], [0, 0])
            row[0] += check["passed"]
            row[1] += 1
        for answer in result.get("judge", []):
            row = rows.setdefault("judge: " + answer["id"], [0, 0])
            row[0] += answer["verdict"] == "yes"
            row[1] += 1
    return {"table": table, "cost": cost}


def report(roots: list) -> str:
    # Across every folder given, since a before and an after are often run at
    # once, and each run's shell shares the one temporary folder.
    reached = crossed([p.parent for r in roots for p in sorted(Path(r).glob("*/*/result.json"))])
    sums = [summarise(Path(r), reached) for r in roots]
    heads = [Path(r).name for r in roots]
    lines = ["| case | check | " + " | ".join(heads) + " |",
             "|---|---|" + "---|" * len(heads)]
    cases = sorted({c for s in sums for c in s["table"]})
    for case in cases:
        rows = []
        for s in sums:
            for row in s["table"].get(case, {}):
                if row not in rows:
                    rows.append(row)
        for row in rows:
            cells = []
            for s in sums:
                got = s["table"].get(case, {}).get(row)
                if not got:
                    cells.append("")
                elif row.startswith("excluded: "):
                    cells.append("%d set aside" % got[1])
                else:
                    cells.append("%d/%d" % tuple(got))
            lines.append("| %s | %s | %s |" % (case, row, " | ".join(cells)))
    lines.append("| | cost, USD | " + " | ".join("%.2f" % s["cost"] for s in sums) + " |")
    return "\n".join(lines)


def cmd_report(args):
    print(report(args.results))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="the cases")
    run = sub.add_parser("run", help="run cases and grade them")
    run.add_argument("--case", action="append",
                     help="a case id or a pattern such as 'cuisine-*'; repeat for more (default: all)")
    run.add_argument("--runs", type=int, default=3, help="runs per case (default 3)")
    run.add_argument("--skill-ref", help="a git ref to take the skill from (default: working tree)")
    run.add_argument("--agent", default="claude-code", choices=sorted(agents.AGENTS))
    run.add_argument("--model", help="the agent's model (default: its own)")
    run.add_argument("--judge-model", default=DEFAULT_JUDGE,
                     help="the judge's model (default %s)" % DEFAULT_JUDGE)
    run.add_argument("--no-judge", action="store_true", help="script checks only")
    run.add_argument("--jobs", type=int, default=JOBS, help="runs at once (default %d)" % JOBS)
    run.add_argument("--max-budget-usd", type=float, default=8.0, help="cap per agent call")
    run.add_argument("--label", help="appended to the results folder's name")
    grade = sub.add_parser("grade", help="grade a results folder again")
    grade.add_argument("results")
    grade.add_argument("--judge-model", help="default: the one the run used")
    grade.add_argument("--no-judge", action="store_true")
    rep = sub.add_parser("report", help="pass rates, side by side")
    rep.add_argument("results", nargs="+")
    args = parser.parse_args(argv)
    {"list": cmd_list, "run": cmd_run, "grade": cmd_grade, "report": cmd_report}[args.command](args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
