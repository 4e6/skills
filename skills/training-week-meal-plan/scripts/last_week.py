#!/usr/bin/env python3
"""Last week's lunches and dinners, so this week's can be different.

    python3 scripts/last_week.py DIRECTORY FIRST_DAY      always one JSON line

FIRST_DAY is the new plan's first day, as YYYY-MM-DD. The answer is
`{"found": false}` or `{"found": true, "mains": [...]}`, and it exits 0 either
way: finding nothing is an ordinary week, not a failure. Exit 2 means FIRST_DAY
was not a date, and carries a message rather than an answer.

**This is the only thing that reads an earlier plan, and what it hands back is
narrow on purpose.** The document sits in whatever folder the host runs in,
where anyone could have left a file with the right name, and every free-text
field in it -- notes, the summary, the closing note, a method step -- is text
that would be read back into the host's context. So the host never opens it.
This hands back dish names and nothing else, each one line and short.

Which files: those directly in DIRECTORY, named for their first day the way the
skill's step 3 names them, whose first day falls in the calendar week before
FIRST_DAY's. A plan always ends on a Sunday, so that window is also the whole
staleness rule: last week's plan is one to seven days old. **Last week may be
two plans** -- one written on Monday, the rest of the week re-planned from
Thursday -- so the newest gives the days it covers and each older one only the
days before that: what was actually on the table, with nothing from a plan that
was replaced.

**Skipped, never repaired**: a file validate.py could not validate at all, one
whose day names do not say which dates they are, a symbolic link, and a file too
large to be a week's plan. A plan with findings is still read -- plans ship
with findings after two repairs, and plans written without Python were never
checked, and a dish name is sound whatever the quantities say.

Python 3.9, standard library only, no network, no writes -- byte-code included,
since importing validate.py would otherwise leave a cache in the skill's own
directory. It lists the one directory it was handed and opens only the names in
that window.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys

# Before the import below, which would otherwise write __pycache__ beside it.
sys.dont_write_bytecode = True

from validate import DAY_INDEX, DAY_NAMES, is_excluded, main_meals, run_checks  # noqa: E402

# Step 3's name for a dated plan document. It is a second copy of step 3's
# rule, so the two change together.
NAME = re.compile(r"^plan-(\d{4}-\d{2}-\d{2})\.json$")

# The meals whose repeat an athlete notices. Breakfast repeats as a matter of
# course, and the fuelling rules expect it to.
MAINS = ("Lunch", "Dinner")

# At most a lunch and a dinner a day, and no name longer than a line.
MAX_MAINS = 14
MAX_LENGTH = 60

# A week's plan is tens of kilobytes. Anything past this is not one, and
# reading it would stall the step that asked.
MAX_BYTES = 1_000_000

# What a name may not carry into the host's context: control characters, the
# marks that reorder or hide text, and the invisible tag characters that can
# spell out a whole sentence. Listed rather than asked of unicodedata, whose
# answer for a character depends on which Python is installed. ZWJ and ZWNJ
# stay: they join and part letters and can reorder nothing.
HIDDEN = (
    (0x0000, 0x001F),
    (0x007F, 0x009F),
    (0x00AD, 0x00AD),
    (0x061C, 0x061C),
    (0x180E, 0x180E),
    (0x200B, 0x200B),
    (0x200E, 0x200F),
    (0x202A, 0x202E),
    (0x2060, 0x2064),
    (0x2066, 0x2069),
    (0xD800, 0xF8FF),
    (0xFEFF, 0xFEFF),
    (0xFFF9, 0xFFFB),
    (0xE0000, 0xE007F),
    (0xF0000, 0x10FFFF),
)


def hidden(c: str) -> bool:
    code = ord(c)
    return any(low <= code <= high for low, high in HIDDEN)


def clean(value) -> str:
    """One short line of text, or nothing.

    A name cannot carry a newline or a direction override into the host's
    context, and length is capped, so it cannot carry a paragraph either.
    """
    if not isinstance(value, str):
        return ""
    kept = "".join(c for c in value if not hidden(c))
    return " ".join(kept.split())[:MAX_LENGTH].strip()


def candidates(directory: str, first_day: datetime.date) -> list:
    """(date, path) for every plan named in last week's window, newest first."""
    monday = first_day - datetime.timedelta(days=first_day.weekday())
    start, end = monday - datetime.timedelta(days=7), monday - datetime.timedelta(days=1)
    found = []
    try:
        names = os.listdir(directory)
    except OSError:
        return []
    for name in names:
        match = NAME.match(name)
        if not match:
            continue
        try:
            day = datetime.date.fromisoformat(match.group(1))
        except ValueError:
            continue
        path = os.path.join(directory, name)
        # A link is a path the name did not come from.
        if start <= day <= end and os.path.isfile(path) and not os.path.islink(path):
            found.append((day, path))
    return sorted(found, reverse=True)


def eaten(path: str, day: datetime.date):
    """(day index, dish names) for each day the plan says was eaten at home, or
    None when the plan is to be skipped.

    **A day's dishes count for the date its name gives, and nothing else here is
    trusted.** So the names have to say which dates they are: each one a
    weekday, strictly after the one before, the first being the weekday the file
    is named for. A plan that skips a day is still read -- its names still say
    which dates they are. Borrowing validate's `day-order` instead skipped that
    plan and missed a name like `Friday,Saturday`, because it compares the names
    joined with commas.

    A day or a meal marked `excluded` was eaten elsewhere, and a slot's meal is
    the first one listed in it, which is the one the checks count.
    """
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return None
        plan = json.loads(raw.decode("utf-8"))
        # The same test validate.py's exit 2 applies: a document the checks
        # cannot walk is one nothing here should read names out of either.
        run_checks(plan)
        days = plan["days"]
        indices = [DAY_INDEX[entry["name"]] for entry in days]
        if not indices or indices[0] != day.weekday():
            return None
        if any(later <= earlier for earlier, later in zip(indices, indices[1:])):
            return None
        out = []
        for entry, index in zip(days, indices):
            if is_excluded(entry):
                continue
            meals = main_meals(entry)
            names = []
            for slot in MAINS:
                meal = meals.get(slot)
                if meal is not None and not is_excluded(meal):
                    names.append(clean(meal.get("dish")))
            out.append((index, names))
        return out
    except Exception:
        return None


def last_week(directory: str, first_day: datetime.date) -> list:
    """Lunch and dinner names, in the order the days were eaten."""
    found = []
    # Days from here on are already answered by a newer plan.
    covered_from = len(DAY_NAMES)
    for day, path in candidates(directory, first_day):
        if day.weekday() >= covered_from:
            continue
        days = eaten(path, day)
        if days is None:
            continue
        for index, names in days:
            if index < covered_from:
                found += [(index, name) for name in names]
        covered_from = day.weekday()

    names = []
    for _, name in sorted(found, key=lambda pair: pair[0]):
        if name and name not in names:
            names.append(name)
    return names[:MAX_MAINS]


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Last week's lunches and dinners.")
    parser.add_argument("directory", help="where the plans are written")
    parser.add_argument("first_day", help="the new plan's first day, YYYY-MM-DD")
    args = parser.parse_args(argv)

    # The shape is checked before the calendar: from 3.11, fromisoformat also
    # takes forms step 3 never writes, and the answer must not depend on which
    # Python is installed.
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.first_day):
            raise ValueError(args.first_day)
        first_day = datetime.date.fromisoformat(args.first_day)
    except ValueError:
        print("not a date: " + args.first_day + " (expected YYYY-MM-DD)", file=sys.stderr)
        return 2

    mains = last_week(args.directory, first_day)
    if mains:
        print(json.dumps({"found": True, "mains": mains}, ensure_ascii=False))
    else:
        print(json.dumps({"found": False}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
