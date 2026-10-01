"""Script checks on one run's plan: cheap, and the same answer every time.

Every check returns `(passed, detail)`. They read `plan-<date>.json`, never the
page, and they reuse the skill's own `validate.py` from the copy that ran, so a
check counts a day's food the way the skill's checker does.

**A day's carbohydrate is its meals plus its snack line's `at least` figure.**
The meals are the athlete's plates as the checker's ranking check counts them;
the snack line is the shortfall the host itself worked out to the bottom of the
day's target. Food on a session's fuel lines is not counted, so a case asks
this only of days whose sessions carry no fuel. Bounds are the published
ranges, 5% wide either side, since the rules say *roughly*.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

TOLERANCE = 0.05
AT_LEAST = re.compile(r"at least (?:about |around |roughly |~)?(\d+)\s*g", re.I)
RACE = re.compile(r"\brace\b", re.I)


def load_validate(skill: Path):
    spec = importlib.util.spec_from_file_location("validate", skill / "scripts" / "validate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def printed(plan: dict) -> str:
    """Everything the page can print, as one string: the plan less `week_load`."""
    return json.dumps({k: v for k, v in plan.items() if k != "week_load"}, ensure_ascii=False)


def day(plan: dict, name: str):
    return next((d for d in plan.get("days", []) if d.get("name") == name), None)


def snack_minimum(entry: dict) -> int:
    guidance = (entry.get("snacks") or {}).get("guidance") or ""
    match = AT_LEAST.search(guidance)
    return int(match.group(1)) if match else 0


def check_validates(ctx, spec):
    findings = ctx.validate.run_checks(ctx.plan)
    if not findings:
        return True, "no findings"
    return False, ", ".join(sorted({f["code"] for f in findings}))


def check_dishes_have_recipes(ctx, spec):
    """Every dish a meal names is a recipe's title at that sitting.

    `validate.py` does not check this, and its ranking check skips a day where
    it fails, so a plan can be clean with a meal the page cannot link to a
    method.
    """
    titles = {(r.get("day"), r.get("meal"), r.get("title")) for r in ctx.plan.get("recipes", [])}
    missing = []
    for entry in ctx.plan.get("days", []):
        for meal in entry.get("meals", []):
            label = ctx.validate.SLOT_TO_MEAL.get(meal.get("slot"))
            for dish in ctx.validate.dishes_of(meal):
                if (entry.get("name"), label, dish) not in titles:
                    missing.append("%s %s: %s" % (entry.get("name"), label, dish))
    return not missing, "; ".join(missing) if missing else "every dish has its recipe"


def check_covers(ctx, spec):
    names = [d.get("name") for d in ctx.plan.get("days", [])]
    return names == spec["days"], " ".join(names)


def check_ranked_first(ctx, spec):
    ranked = ctx.validate.ranked_days(ctx.plan.get("training_overview", {}).get("hard_days", ""))
    first = ranked[0] if ranked else None
    return first == spec["day"], "hard_days starts with " + str(first)


def check_race_named(ctx, spec):
    entry = day(ctx.plan, spec["day"])
    if entry is None:
        return False, spec["day"] + " is not in the plan"
    session = entry.get("session") or ""
    names = [s.get("name") or "" for s in entry.get("sessions", [])]
    ok = bool(RACE.search(session)) and any(RACE.search(n) for n in names)
    return ok, "session: %r; sessions: %r" % (session, names)


def check_no_race(ctx, spec):
    found = [
        (d.get("name"), text)
        for d in ctx.plan.get("days", [])
        for text in [d.get("session") or ""] + [s.get("name") or "" for s in d.get("sessions", [])]
        if RACE.search(text)
    ]
    return not found, repr(found) if found else "no session is called a race"


def check_carbs_per_kg(ctx, spec):
    entry = day(ctx.plan, spec["day"])
    if entry is None:
        return False, spec["day"] + " is not in the plan"
    meals = ctx.validate.ranked_carbs(ctx.plan, spec["day"])
    if meals is None:
        return False, "the checker cannot read %s's meals" % spec["day"]
    snacks = snack_minimum(entry)
    per_kg = (meals + snacks) / ctx.weight
    low, high = spec.get("min"), spec.get("max")
    ok = (low is None or per_kg >= low * (1 - TOLERANCE)) and (
        high is None or per_kg <= high * (1 + TOLERANCE)
    )
    wanted = "%s-%s" % (low if low is not None else "", high if high is not None else "")
    return ok, "%.1f g/kg (meals %d g + snacks %d g), wanted %s" % (per_kg, meals, snacks, wanted)


def session_names(plan: dict) -> str:
    return "\n".join(
        text
        for d in plan.get("days", [])
        for text in [d.get("session") or ""] + [s.get("name") or "" for s in d.get("sessions", [])]
    )


def check_not_printed(ctx, spec):
    """`pattern` appears nowhere printed, or with `in: sessions` in no session's name."""
    text = session_names(ctx.plan) if spec.get("in") == "sessions" else printed(ctx.plan)
    match = re.search(spec["pattern"], text, re.I)
    return match is None, ("prints %r" % match.group(0)) if match else "absent"


CHECKS = {
    "validates": check_validates,
    "dishes_have_recipes": check_dishes_have_recipes,
    "covers": check_covers,
    "ranked_first": check_ranked_first,
    "race_named": check_race_named,
    "no_race": check_no_race,
    "carbs_per_kg": check_carbs_per_kg,
    "not_printed": check_not_printed,
}


class Context:
    def __init__(self, plan: dict, weight: float, skill: Path):
        self.plan = plan
        self.weight = weight
        self.validate = load_validate(skill)


def check_id(spec: dict) -> str:
    return spec.get("id") or "-".join(
        [spec["check"]] + [str(spec[k]) for k in ("day",) if k in spec]
    )


def run(plan: dict, weight: float, skill: Path, specs: list) -> list:
    """Every check the case asks for, each as {id, passed, detail}."""
    ctx = Context(plan, weight, skill)
    results = []
    for spec in [{"check": "validates"}, {"check": "dishes_have_recipes"}] + specs:
        try:
            passed, detail = CHECKS[spec["check"]](ctx, spec)
        except Exception as error:  # a plan the check cannot walk fails it
            passed, detail = False, "%s: %s" % (type(error).__name__, error)
        results.append({"id": check_id(spec), "passed": passed, "detail": detail})
    return results
