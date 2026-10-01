"""Script checks on one run's plan: cheap, and the same answer every time.

Every check returns `(passed, detail)`. They read `plan-<date>.json`, never the
page, and they reuse the skill's own `validate.py` from the copy that ran, so a
check counts a day's food the way the skill's checker does.

**A day's target is read back from its snack line.** The host works out a
day's snacks as the gap from its meals and fuel to the bottom of the day's band
(`at least`) and to its top (`up to`). So meals, fuel and the first figure come
to the bottom of the band the host aimed at, and with the second to its top. A
check on the total alone cannot tell a band from the one above it, since the
snacks top any day up to its band's bottom: a day wrongly loaded at 10-12 g/kg
measures 10.0, inside 7-10. The meals are the athlete's plates as the checker's
ranking check counts them; fuel-line food is counted from the fuelling table's
items, at each range's middle, and anything else on a line is not. Bounds are
5% wide either side, since the rules say *roughly*.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

TOLERANCE = 0.05
AT_LEAST = re.compile(r"at least (?:about |around |roughly |~)?(\d+)\s*g", re.I)
UP_TO = re.compile(r"up to (?:about |around |roughly |~)?(\d+)\s*g", re.I)
WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
# A count, then at most one word before the item: `2 caffeinated energy gels`.
COUNT = r"\b(\d+|an?|one|two|three|four|five|six)\s+(?:[a-z-]+\s+)?"
# A volume or weight in an example is never a count: `a 500 ml bottle` is one.
MEASURE = re.compile(r"\b\d+(?:\.\d+)?\s*(?:ml|l|cl|g|kg|oz)\b\s*", re.I)
# The fuelling table's items, at the middle of each range.
FUEL_ITEMS = [
    (re.compile(COUNT + r"bottles? of isotonic", re.I), 35),
    (re.compile(COUNT + r"energy gels?\b", re.I), 24),
    (re.compile(COUNT + r"energy bars?\b", re.I), 43),
    (re.compile(COUNT + r"bananas?\b", re.I), 27),
    (re.compile(COUNT + r"dates?\b", re.I), 11.5),
]
# Animal food, and the words that make one of them plant food when they come
# just before it (`oat milk`, `peanut butter`) or just after it (`egg-free`,
# `butter beans`). A regular expression could not hold both without either
# failing `soy yoghurt` or passing `whole milk`.
ANIMAL = re.compile(
    r"\b(?:chicken|beef|pork|lamb|bacon|ham|turkey|salmon|tuna|mackerel|cod|prawns?|"
    r"shrimps?|anchov(?:y|ies)|fish sauce|eggs?|honey|whey|ghee|gelatine?|milk|"
    r"buttermilk|yogh?urts?|butter|cheeses?|cheddar|parmesan|feta|mozzarella|cream|"
    r"mayo(?:nnaise)?)\b",
    re.I,
)
# Meat and fish are made plant food only by a word that says so: `coconut
# chicken curry` and `soy sauce chicken` are chicken, where `coconut yoghurt`
# is not yoghurt.
FLESH = re.compile(
    r"chicken|beef|pork|lamb|bacon|ham|turkey|salmon|tuna|mackerel|cod|prawns?|"
    r"shrimps?|anchov(?:y|ies)", re.I)
SAYS_SO = {"vegan", "plant-based", "tofu", "chickpea", "seitan", "jackfruit", "soy-based"}
PLANT = {
    "soy", "soya", "oat", "almond", "peanut", "cashew", "coconut", "rice", "hemp",
    "pea", "plant", "plant-based", "vegan", "dairy-free", "tofu", "chickpea", "nut",
    "hazelnut", "sunflower", "seed", "cocoa", "flax", "chia",
}
# And the words that say it is left out: `maple syrup instead of honey`.
LEFT_OUT = {"instead", "no", "not", "without"}
NOT_ANIMAL_AFTER = re.compile(
    r"[- ]?free\b|-style\b| (?:substitute|alternative|replacer|beans?)\b", re.I)
# A qualifier written after the food, as lists do: `Yoghurt, soy`, `Milk (oat)`.
QUALIFIED_AFTER = re.compile(r"\s*[,(]\s*([a-z-]+)", re.I)
JOINS = {"and", "with", "&", "or", "+"}
RACE = re.compile(r"\brace\b", re.I)
# The example foods in the skill's own text (issue #10).
ANCHORS = re.compile(
    r"\b(?:porridge|oatmeal|overnight oats|bagels?|chocolate milk|sourdough|bolognese|lentil soup)\b", re.I)
# A weight or volume in each system. Spoons, counts, cloves and slices are in
# neither: they read the same everywhere.
UNITS = {
    "metric": re.compile(r"\d\s*(?:g|grams?|kg|kilos?|ml|l|litres?|liters?|cl|dl)\b", re.I),
    "us": re.compile(r"\d\s*(?:lbs?|pounds?|oz|ounces?|fl\.? oz|cups?|pints?|quarts?|qts?|gallons?|gals?)\b", re.I),
}


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


def snack_figure(entry: dict, pattern):
    guidance = (entry.get("snacks") or {}).get("guidance") or ""
    match = pattern.search(guidance)
    return int(match.group(1)) if match else None


def fuel_food(entry: dict) -> float:
    """The carbohydrate in a day's fuel-line examples, from the items the table names."""
    total = 0.0
    for session in entry.get("sessions", []):
        for line in ("before", "during", "after"):
            example = MEASURE.sub("", (session.get(line) or {}).get("example") or "")
            example = re.sub(r"\s*\(\s*\)", "", example)
            example = re.sub(r"\b(\d+)\s*x\s+", r"\1 ", example)
            for pattern, grams in FUEL_ITEMS:
                for match in pattern.finditer(example):
                    count = match.group(1).lower()
                    total += grams * (int(count) if count.isdigit() else WORDS[count])
    return total


def day_carbs(ctx, name: str):
    """(bottom, top, detail) in g/kg: the band the host aimed this day at.

    `top` is None where the day has no snack line, and then `bottom` is simply
    what the meals and fuel come to.
    """
    entry = day(ctx.plan, name)
    if entry is None:
        raise LookupError(name + " is not in the plan")
    meals = ctx.validate.ranked_carbs(ctx.plan, name)
    if meals is None:
        raise LookupError("the checker cannot read %s's meals" % name)
    fuel = fuel_food(entry)
    at_least, up_to = snack_figure(entry, AT_LEAST), snack_figure(entry, UP_TO)
    bottom = (meals + fuel + (at_least or 0)) / ctx.weight
    top = (meals + fuel + up_to) / ctx.weight if up_to is not None else None
    detail = "%.1f%s g/kg (meals %d g, fuel %d g, snacks %s to %s g)" % (
        bottom, "" if top is None else "-%.1f" % top, meals, fuel, at_least, up_to)
    return bottom, top, detail


def check_validates(ctx, spec):
    findings = ctx.validate.run_checks(ctx.plan)
    if not findings:
        return True, "no findings"
    return False, ", ".join(sorted({f["code"] for f in findings}))


def check_dishes_have_recipes(ctx, spec):
    """Every dish a meal names is a recipe's title at that sitting.

    `validate.py` checks this itself from 1.1.1 (`dish-without-recipe`). Before
    that a plan could be clean with a meal the page cannot link to a method, and
    `--skill-ref` can still run such a version.
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
    """The day is fed in the band `min`-`max` g/kg: its bottom reached, its top the one aimed at."""
    try:
        bottom, top, detail = day_carbs(ctx, spec["day"])
    except LookupError as error:
        return False, str(error)
    low, high = spec["min"], spec["max"]
    ok = low * (1 - TOLERANCE) <= bottom <= high * (1 + TOLERANCE)
    if top is not None:
        ok = ok and abs(top - high) <= high * TOLERANCE
    return ok, "%s, wanted %s-%s" % (detail, low, high)


def check_not_loaded(ctx, spec):
    """The day is fed below the loading band that starts at `below` g/kg."""
    try:
        bottom, top, detail = day_carbs(ctx, spec["day"])
    except LookupError as error:
        return False, str(error)
    limit = spec["below"]
    ok = bottom < limit * (1 - TOLERANCE) and (top is None or top <= limit * (1 + TOLERANCE))
    return ok, "%s, wanted below %s" % (detail, limit)


def food_names(plan: dict) -> list:
    """Every name the plan gives food: dishes, ingredients, the list, and fuel and snack examples."""
    names = []
    for recipe in plan.get("recipes", []):
        names.append(recipe.get("title") or "")
        names += [i.get("item") or "" for i in recipe.get("ingredients") or []]
    for group in plan.get("shopping", []):
        names += [i.get("name") or "" for i in group.get("items", [])]
    for entry in plan.get("days", []):
        for meal in entry.get("meals", []):
            names += [meal.get("dish") or ""] + list(meal.get("alongside") or [])
        for session in entry.get("sessions", []):
            names += [(session.get(k) or {}).get("example") or "" for k in ("before", "during", "after")]
        names.append((entry.get("snacks") or {}).get("example") or "")
    return [n for n in names if n]


def check_vegan(ctx, spec):
    """No animal food is named anywhere the plan names food."""
    found = []
    for name in food_names(ctx.plan):
        for match in ANIMAL.finditer(name):
            before = [w.strip(".") for w in re.split(r"[,;(]", name[: match.start()])[-1].lower().split()]
            # The word just before, or the one before that across a modifier
            # (`plant-based Greek yoghurt`), but never across a join: in
            # `Rice with egg` the rice qualifies nothing.
            near = before[-1:] if before[-1:] and before[-1] in JOINS else before[-2:]
            qualifiers = SAYS_SO if FLESH.fullmatch(match.group(0)) else PLANT
            if (near and near[-1] not in JOINS and any(w in qualifiers for w in near)) or LEFT_OUT & set(before):
                continue
            if NOT_ANIMAL_AFTER.match(name, match.end()):
                continue
            after = QUALIFIED_AFTER.match(name, match.end())
            if after and after.group(1).lower() in qualifiers:
                continue
            found.append(name)
    return not found, "; ".join(sorted(set(found))) if found else "no animal food"


def check_race_during(ctx, spec):
    """The race's `during` guidance gives the range `pattern` matches.

    A race over two and a half hours takes 60-90 g an hour; this reads only the
    range, and the judge whether the example food adds up to it.
    """
    entry = day(ctx.plan, spec["day"])
    if entry is None:
        return False, spec["day"] + " is not in the plan"
    lines = [
        ((s.get("during") or {}).get("guidance") or "")
        for s in entry.get("sessions", [])
        if RACE.search(s.get("name") or "")
    ]
    ok = any(re.search(spec["pattern"], line) for line in lines)
    return ok, "during: %r" % lines


def check_anchor_foods(ctx, spec):
    """None of the skill's own example foods is named, in the dishes or on the daily lines.

    These are the foods the skill's text uses as examples, nearly all British.
    For an athlete elsewhere, one turning up suggests the example was copied
    rather than the country's food chosen; the UK case is the control, where
    they belong. `where` is `dishes` (each meal's dishes) or `lines` (the
    session fuel lines and the snack line, short and written every day, where
    copying would show first).
    """
    if spec["where"] not in ("dishes", "lines"):
        raise ValueError("where is dishes or lines, not %r" % spec["where"])
    names = []
    for entry in ctx.plan.get("days", []):
        if spec["where"] == "dishes":
            for meal in entry.get("meals", []):
                names += [meal.get("dish") or ""] + list(meal.get("alongside") or [])
        else:
            for session in entry.get("sessions", []):
                names += [(session.get(k) or {}).get("example") or "" for k in ("before", "during", "after")]
            names.append((entry.get("snacks") or {}).get("example") or "")
    counts = {}
    for name in names:
        for match in ANCHORS.finditer(name):
            key = re.sub(r"^bagels$", "bagel", match.group(0).lower())
            counts[key] = counts.get(key, 0) + 1
    return not counts, (", ".join("%s x%d" % kv for kv in sorted(counts.items()))
                        if counts else "none of them")


def check_units(ctx, spec):
    """At least `share` of the weighed quantities are in `system`, the country's.

    Read from the shopping list's quantities and the recipes' ingredient lines,
    which is what the athlete shops and cooks by. A quantity in neither system
    (a spoon, a count) is left out.
    """
    quantities = [i.get("qty") or "" for g in ctx.plan.get("shopping", []) for i in g.get("items", [])]
    quantities += [i.get("qty") or "" for r in ctx.plan.get("recipes", []) for i in r.get("ingredients") or []]
    counts = {name: sum(1 for q in quantities if unit.search(str(q))) for name, unit in UNITS.items()}
    weighed = sum(counts.values())
    share = counts[spec["system"]] / weighed if weighed else 0.0
    return share >= spec["share"], "%s in %d of %d weighed quantities (%s)" % (
        spec["system"], counts[spec["system"]], weighed,
        ", ".join("%s %d" % kv for kv in sorted(counts.items())))


def check_not_printed(ctx, spec):
    match = re.search(spec["pattern"], printed(ctx.plan), re.I)
    return match is None, ("prints %r" % match.group(0)) if match else "absent"


CHECKS = {
    "validates": check_validates,
    "dishes_have_recipes": check_dishes_have_recipes,
    "covers": check_covers,
    "ranked_first": check_ranked_first,
    "race_named": check_race_named,
    "no_race": check_no_race,
    "carbs_per_kg": check_carbs_per_kg,
    "not_loaded": check_not_loaded,
    "race_during": check_race_during,
    "vegan": check_vegan,
    "not_printed": check_not_printed,
    "anchor_foods": check_anchor_foods,
    "units": check_units,
}


class Context:
    def __init__(self, plan: dict, weight: float, skill: Path):
        self.plan = plan
        self.weight = weight
        self.validate = load_validate(skill)


def check_id(spec: dict) -> str:
    return spec.get("id") or "-".join(
        [spec["check"]] + [str(spec[k]) for k in ("day", "where", "system") if k in spec]
    )


ALWAYS = [{"check": "validates"}, {"check": "dishes_have_recipes"}]


def without_plan(specs: list) -> list:
    """Every check the case asks for, failed: a run with no plan fails them all."""
    return [{"id": check_id(s), "passed": False, "detail": "no plan"} for s in ALWAYS + specs]


def run(plan: dict, weight: float, skill: Path, specs: list) -> list:
    """Every check the case asks for, each as {id, passed, detail}."""
    ctx = Context(plan, weight, skill)
    results = []
    for spec in ALWAYS + specs:
        try:
            passed, detail = CHECKS[spec["check"]](ctx, spec)
        except Exception as error:  # a plan the check cannot walk fails it
            passed, detail = False, "%s: %s" % (type(error).__name__, error)
        results.append({"id": check_id(spec), "passed": passed, "detail": detail})
    return results
