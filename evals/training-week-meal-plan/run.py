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
import json
import shutil
import subprocess
import sys
import tempfile
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
     "Does the race session carry a `before` line, and are its `during` and `after` "
     "lines (or their absence) consistent with the race as the athlete described it?"),
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
    """The common questions, the race week's where it is one, and the case's own,
    less any the case says do not apply to it (`skip_judge`)."""
    asked = COMMON_QUESTIONS + (RACE_QUESTIONS if case.get("race") else [])
    asked = [q for q in asked if q[0] not in case.get("skip_judge", [])]
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
    work = Path(tempfile.mkdtemp(prefix="twmp-eval-"))
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


def grade_one(agent, case: dict, out: Path, skill: Path, judge_model, judge: bool) -> dict:
    result = json.loads((out / "result.json").read_text())
    plan_path = plan_in(out)
    run_checks = [
        # Not the skill's fault when it fails: the agent was never offered it.
        {"id": "skill-installed", "passed": result.get("skill_listed", False),
         "detail": "listed" if result.get("skill_listed") else "the agent's skill list lacks it"},
        {"id": "skill-used", "passed": SKILL in result["skills"] or result["read_skill_md"],
         "detail": "skills: %r" % result["skills"]},
        {"id": "planned-without-asking", "passed": result["turns"] == 1,
         "detail": "%d turn(s)" % result["turns"]},
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
    result["checks"] = run_checks
    if judge and plan is not None:
        result["judge"], result["judge_cost_usd"] = ask_judge(agent, case, out, plan, judge_model)
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def ask_judge(agent, case: dict, out: Path, plan: dict, model) -> tuple:
    asked = questions(case)
    prompt = (HERE / "judge.md").read_text().format(
        message=(out / "message.md").read_text().strip(),
        plan=json.dumps(plan, indent=1, ensure_ascii=False),
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
    chosen = args.case or list(cases)
    unknown = [c for c in chosen if c not in cases]
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
            run_one(agent, cases[case_id], n, out, skill, today)
            result = grade_one(agent, cases[case_id], out, skill, args.judge_model,
                               not args.no_judge)
            failed = [c["id"] for c in result["checks"] if not c["passed"]]
            say("done   %s #%d  %s" % (case_id, n, "failed: " + ", ".join(failed) if failed else "checks pass"))
        except Exception as error:
            say("ERROR  %s #%d  %s: %s" % (case_id, n, type(error).__name__, error))

    jobs = [(c, n) for c in chosen for n in range(1, args.runs + 1)]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        list(pool.map(one, jobs))
    print(report([root]))
    say("results: " + str(root))


def cmd_grade(args):
    cases = load_cases()
    root = Path(args.results)
    meta = json.loads((root / "meta.json").read_text())
    agent = agents.AGENTS[meta["agent"]]()
    model = args.judge_model or meta.get("judge_model")
    for result_path in sorted(root.glob("*/*/result.json")):
        out = result_path.parent
        grade_one(agent, cases[out.parent.name], out, root / "skill", model, not args.no_judge)
    print(report([root]))


def summarise(root: Path) -> dict:
    """{case: {row: [passes, runs]}} with the cost, for one results folder."""
    table, cost = {}, 0.0
    for result_path in sorted(root.glob("*/*/result.json")):
        result = json.loads(result_path.read_text())
        cost += result.get("cost_usd", 0) + result.get("judge_cost_usd", 0)
        rows = table.setdefault(result["case"], {})
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
    sums = [summarise(Path(r)) for r in roots]
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
                cells.append("%d/%d" % tuple(got) if got else "")
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
    run.add_argument("--case", action="append", help="a case id; repeat for more (default: all)")
    run.add_argument("--runs", type=int, default=3, help="runs per case (default 3)")
    run.add_argument("--skill-ref", help="a git ref to take the skill from (default: working tree)")
    run.add_argument("--agent", default="claude-code", choices=sorted(agents.AGENTS))
    run.add_argument("--model", help="the agent's model (default: its own)")
    run.add_argument("--judge-model", default="opus", help="the judge's model (default opus)")
    run.add_argument("--no-judge", action="store_true", help="script checks only")
    run.add_argument("--jobs", type=int, default=1, help="runs at once (default 1)")
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
