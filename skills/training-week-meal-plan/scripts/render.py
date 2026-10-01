#!/usr/bin/env python3
"""Turn a finished plan into one printable page.

    python3 scripts/render.py plan.json plan.html      0 wrote it, 2 could not
    python3 scripts/render.py plan.json plan.html --photos photos.json
    python3 scripts/render.py plan.json photos.json --list-photos

The output is a single self-contained file. The stylesheet beside this script
is inlined into it, so there are no sidecar assets and nothing to fetch: the
athlete can mail the file to themselves, open it anywhere, and press Cmd-P.

Exit 0 prints a line saying where it wrote, rather than staying silent — a
silent success and a crash look identical to anything reading output rather
than status.

The four exit-2 messages are four different repairs, which is why they are four
messages. Read the message, not only the number. Writing the list of photos,
"could not list" stands where "could not render" would, and the stylesheet is
not read.

This renders; it does not check. validate.py owns the checking, and keeping the
two apart is what lets a plan that failed a check still be handed over as a
document. **Two computations here are facts about the page** rather than
verdicts on the plan, and no checker output reaches this file: the count beside
a quantity -- how many tins or pieces a weight comes to, from the pack the row
states -- and the size of each pot. A recipe's list is written for `yields`
portions and a repeat's bigger bowl is a number of `portions`, so the page
multiplies the one by the other and each plate's figures are the origin's one
portion times its own. The multiplying is validate.py's own scale_line, imported
rather than copied, so the list the checker adds up is the list the page prints.
A batch's `Makes` line states that pot in portions, and only when it is the pot
the list is scaled to -- makes_line says when that is. The aisle headings are
read from the plan too, never asked of it: a list weighed in US units prints a
US shop's names for the schema's fixed categories -- in_us_units says when.

Python 3.9, standard library only, no network. It reads the plan, the stylesheet
and, when handed a list of photos, the image files that list names inside its
own folder, and writes the one file it was told to write -- and, asked for the
list of photos, the photos folder beside that list for the drawings to go in.

A photo is a warning when it cannot be used, and never an exit 2: the dish goes
without its tile and the page is written. The warnings print after the page is
written, so a plan that cannot be rendered never has photo lines beside it, and
none of them says "could not" -- that phrase is the four messages above.

The bytes are an artifact: examples/sample-plan.html is this script's output for
examples/sample-plan.json, and has to come out the same byte for byte wherever
it is rendered, so nothing here may vary between machines or interpreters. That
rules out iterating a set (hash order), sorting (collation), case mapping (the
Unicode database moves between versions), and any timestamp.

It does **not** rule out the count above, and the distinction is the point of
the rule rather than an exception to it: what is banned is a result that differs
between one machine and another. Dividing two decimal strings in IEEE 754
doubles and flooring the answer gives the same number on every Python 3.9+ on
every platform. So does printing a fractional number: number() prints the repr, the
shortest form that round-trips, which is fixed across platforms. A sum is printed
either where every term is a whole number of quarters, which binary floating
point adds exactly -- the `Makes` total -- or rounded to two places, which is
correctly rounded on every platform -- a sitting's share of its plates. Adding a computation whose result could vary -- anything
reading the environment, the clock, a hash, or a locale -- is still ruled out.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import re
import sys
from pathlib import Path

# Before the import below, which would otherwise write __pycache__ beside it --
# a second file this was never told to write, in the skill's own directory.
sys.dont_write_bytecode = True

from validate import (  # noqa: E402
    MASS_UNITS,
    VOLUME_UNITS,
    dishes_of,
    scale_line,
    singular,
    written_quantity,
)

CSS_PATH = Path(__file__).resolve().parent.parent / "assets" / "plan.css"

# A dish's photo, where the host that ran the skill could draw one.
#
# One file may be 400 KB: a 640 px square JPEG at quality 80 is about 55-70 KB where
# measured, and could reach 140 KB by the 80 KB once seen at 480 px, so the cap
# is there to refuse an image tool's own output -- a PNG of about 2.4 MB -- and
# not a photo sized as asked. The page's photos together may be 10 MB, every card
# counted, because each card embeds its bytes again: the sample week's
# twenty-one cards at 400 KB each would come to 8.4 MB, and the cap itself is a
# page of about 13.5 MB once the bytes are base64 -- under the 16 MB some
# hosts allow a published page, and far from the 48 MB page a preview refused.
# Tighter caps than these refused photos from pages that would have opened.
PHOTO_MAX_BYTES = 400 * 1024
PHOTOS_MAX_BYTES = 10 * 1024 * 1024

# The cards that carry the dish's photo: every one. A leftover is the same
# plate, and a card you eat from is a card you look for.
PHOTO_KINDS = ("origin", "repeat", "leftover")

# The only markup a plan is allowed to carry: bold and italic, so a string
# written with emphasis prints as emphasis rather than as raw asterisks.
#
# Known limitation: a session written with asterisks for repetitions, as in
# 2*20min alongside 3*1km, has the run between the first and second asterisk
# italicised and the asterisks themselves dropped. Deliberately not
# special-cased.
EMPHASIS = re.compile(r"\*\*(.+?)\*\*|\*(.+?)\*", re.DOTALL)

# A meal row's slot, as the matching recipe spells the same meal.
SLOT_TO_MEAL = {"breakfast": "Breakfast", "lunch": "Lunch", "dinner": "Dinner"}

# A day, as a shopping row's usage tag spells it.
DAY_ABBR_OF = {
    "Monday": "Mon",
    "Tuesday": "Tue",
    "Wednesday": "Wed",
    "Thursday": "Thu",
    "Friday": "Fri",
    "Saturday": "Sat",
    "Sunday": "Sun",
}

# The line that sends a card to the one carrying the method. A leftover always
# has it; a repeat prints the method itself, and falls back to the line only
# where its origin has no steps to print.
KIND_LEAD = {
    "repeat": "Cooked again from ",
    "leftover": "Leftover from ",
}

# The three parts of the page a reader jumps between, as (id, heading). The
# heading and the link under the title are both built from here, so a link can
# never name its part in other words than the part names itself. The ids are
# fixed ASCII and never plan text: an attribute is the one place a value could
# stop being text.
SECTIONS = (("week", "The week"), ("recipes", "Recipes"), ("shopping", "Shopping list"))
HEADING = dict(SECTIONS)

# The shopping list's aisles as a US shop names them, keyed by the plan's own
# category. The plan always writes the key: the schema's categories are a fixed
# list, so a list is grouped and walked in one order whatever country it is for,
# and only the heading it prints changes. A key not here prints as written.
US_AISLES = {
    "Fruit & Vegetables": "Produce",
    "Tins, Jars & Seasonings": "Canned Goods, Jars & Seasonings",
    "Meat & Fish": "Meat & Seafood",
    "Dairy, Eggs & Chilled": "Dairy, Eggs & Refrigerated",
}

# The weights and volumes of US customary, singular and lower-case as the unit
# tables key them. Every other unit in those tables is metric.
US_UNITS = ("oz", "ounce", "lb", "pound", "cup", "pint", "quart", "qt", "gallon", "gal")

# The glance is a fourth place to jump to, from the rail only: under the title
# it is the first thing after the links, so a link to it would go nowhere.
GLANCE = ("glance", "The week at a glance")


def section_heading(key) -> str:
    return '<h2 id="' + key + '">' + HEADING[key] + "</h2>"


def esc(value) -> str:
    """Escape for HTML, quotes included. Every plan value goes through this."""
    return html.escape(str(value), quote=True)


def _emphasise(match) -> str:
    strong = match.group(1)
    if strong is not None:
        return "<strong>" + strong + "</strong>"
    return "<em>" + (match.group(2) or "") + "</em>"


def prose(value) -> str:
    """Escape, then convert emphasis — in that order, which is the safe one.

    After escaping, the only angle brackets left in the string are the ones this
    substitution puts there, so a dish name containing markup cannot become
    markup. Doing it the other way round would let the plan inject elements.
    """
    return EMPHASIS.sub(_emphasise, esc(value))


def number(value) -> str:
    """Print a number the same way on every interpreter, escaped like everything else.

    Most numeric fields the schema declares are integers. A plate's `portions`
    is not — it is counted in quarters — so the float branch prints every
    fractional plate, share and `Makes` total, as well as a plan somebody
    hand-edited to 520.0. An integral float prints as the integer; any
    other prints the shortest form that round-trips, which has been fixed since
    3.1.

    **The escape is not decoration.** Nothing here validates, and step 6 renders
    even when the check found something — so this is the one component
    guaranteed to run on plans nothing has looked at, and a model that emits a
    string where the schema says integer gets it printed. Without the escape
    that string is markup, and the page would carry whatever it said. Escaping
    an integer is a no-op, so this costs nothing on every plan that is correct.

    It is a funnel rather than a check for the same reason the two above are:
    refusing would mean an athlete whose plan has one bad field gets no page at
    all, and the whole point of step 6 is that a document still comes out.
    """
    if isinstance(value, float):
        if value.is_integer():
            return esc(int(value))
        return esc(repr(value))
    return esc(value)


def head(plan) -> str:
    overview = plan["training_overview"]
    rows = [
        ("Load", overview["total"]),
        ("Hard days", overview["hard_days"]),
        ("Easy days", overview["easy_days"]),
    ]
    out = ['<header class="masthead">']
    out.append("<h1>" + prose(plan["week_label"]) + "</h1>")
    # A phone gets the page as one long scroll, and the list the athlete carries
    # into the shop is at the very end of it. Hidden in print, where a page is
    # turned rather than jumped to.
    out.append(
        '<nav class="jump">'
        + " &middot; ".join('<a href="#' + key + '">' + label + "</a>" for key, label in SECTIONS)
        + "</nav>"
    )
    out.append('<dl class="overview">')
    for label, value in rows:
        out.append("<div><dt>" + label + "</dt><dd>" + prose(value) + "</dd></div>")
    out.append("</dl>")
    out.append('<p class="summary">' + prose(overview["summary"]) + "</p>")
    out.append("</header>")
    return "\n".join(out)


def meal_body(meal, name=prose, bookkeeping=True) -> str:
    """What a meal row says, in precedence order.

    The two leading cases are exclusive rather than additive, and that is the
    whole point of writing them as early returns. An excluded reason is printed
    **in place of** the dish, so a plan that carries both — which the schema
    forbids and no check rejects — must print the reason alone. Appending them
    instead produces a page telling the athlete to eat chicken pasta at work.

    That case is reachable rather than theoretical: step 6 renders even when the
    check found something, so this is the one component guaranteed to run on
    plans nothing has validated.

    The glance prints a meal through this too, with its own name function — a
    dish linked to its recipe — and without the bookkeeping, so the two parts of
    the page that name a meal have one precedence between them rather than two
    copies of it. The dishes are the checker's own dishes_of, imported for the
    reason scale_line is: the page names the meals the check added up.
    """
    if "excluded" in meal:
        return '<span class="excluded">' + prose(meal["excluded"]) + "</span>"

    body = " \u00b7 ".join(name(dish) for dish in dishes_of(meal))
    if not bookkeeping:
        return body
    if "note" in meal:
        body += ' <span class="note">(' + prose(meal["note"]) + ")</span>"
    # Not in the schema any more, and still printed where an older plan has one.
    if "extra" in meal:
        body += ' <span class="extra">' + prose(meal["extra"]) + "</span>"
    return body


def meal_line(meal) -> str:
    return (
        '<li class="meal ' + esc(meal["slot"]) + '">'
        + '<span class="slot">' + prose(meal["label"]) + "</span>"
        + '<span class="meal-body">' + meal_body(meal) + "</span>"
        + "</li>"
    )


FUEL_PARTS = (("before", "Before"), ("during", "During"), ("after", "After"))


def fuel_line(label: str, line) -> str:
    """One line of guidance with its example food, under a small-caps label.

    A session's fuel and a day's snacks print alike, because they are alike:
    a range to meet and food that roughly meets it, never bought.
    """
    example = ""
    if line.get("example"):
        example = ' <span class="example">e.g. ' + prose(line["example"]) + "</span>"
    return (
        '<li><span class="slot">' + label + "</span>"
        + '<span class="fuel-body">' + prose(line.get("guidance", "")) + example + "</span></li>"
    )


def sessions(day) -> str:
    """A day's sessions, each named, with its fuel lines under it.

    Above the meals and never among them: the meals carry no time of day, and
    interleaving the two prints a timetable nobody gave. Every session is named,
    including on a day with one — this page has no unbreakable card to pay for a
    repeated line, and naming each is plainer than a rule about when not to.
    """
    listed = day.get("sessions", [])
    if not listed:
        return ""
    out = ['<ul class="sessions">']
    for session in listed:
        out.append('<li class="training"><span class="training-name">' + prose(session.get("name", "")) + "</span>")
        lines = [(label, session[key]) for key, label in FUEL_PARTS if key in session]
        if lines:
            out.append('<ul class="fuel">')
            for label, line in lines:
                out.append(fuel_line(label, line))
            out.append("</ul>")
        out.append("</li>")
    out.append("</ul>")
    return "\n".join(out)


def days(plan) -> str:
    # No block stating the fuel ranges above Monday: each session's own lines
    # carry what applies to it, and the plan has no field restating the ranges.
    out = ['<section class="week">', section_heading("week")]
    for n, day in enumerate(plan["days"], 1):
        out.append('<section class="day" id="' + day_anchor(n) + '">')
        out.append(
            '<div class="day-head"><h3>' + prose(day["name"]) + "</h3>"
            + '<span class="session">' + prose(day["session"]) + "</span></div>"
        )
        training = sessions(day)
        if training:
            out.append(training)
        # Exclusive, for the same reason the meal rows above are: the reason is
        # printed *in place of* the food, so a day carrying both — which the
        # schema forbids and no check rejects — must not say the athlete is away
        # and then tell them what to cook. The day keeps its heading and its
        # session either way, so the plan's days stay unbroken rather than
        # developing a hole.
        if "excluded" in day:
            out.append('<p class="excluded">' + prose(day["excluded"]) + "</p>")
        elif day["meals"]:
            out.append('<ul class="meals">')
            for meal in day["meals"]:
                out.append(meal_line(meal))
            out.append("</ul>")
            # After the meals, because it is what the day needs beyond them. Not
            # on a day the athlete is away: the reason stands alone there.
            # A bare string is taken as the guidance rather than dropped: the
            # line is an instruction, and a plan nothing validated still prints.
            snacks = day.get("snacks")
            if isinstance(snacks, str) and snacks.strip():
                snacks = {"guidance": snacks}
            if isinstance(snacks, dict):
                out.append('<ul class="fuel snacks">' + fuel_line("Snacks", snacks) + "</ul>")
        out.append("</section>")
    out.append("</section>")
    return "\n".join(out)


def glance(plan) -> str:
    """The week at a glance: a row per day, its training and its three meals.

    The sheet that goes on the fridge, so it is names only. A meal's note and
    extra are portion bookkeeping the day below carries, and on a row read from
    across the kitchen they would double its height. Nothing computed: the
    training cell is the day's own one-line summary, and there is no day total
    because the plan states none.

    A row per plan["days"], never a fixed seven: a week that starts tomorrow
    has fewer. A column per slot rather than per label, because a column has
    one heading. Plain loops, never a set or a sort, for the reason
    recipe_days gives. A meal's cell is meal_body's, so its precedence is the
    week's — the reason in place of the food — and an away day keeps its
    training as it does in days().

    It is a summary, and on a plan that failed its check it says less than the
    week: one meal per slot, the first, and nothing for a slot outside the
    three. The week below prints every meal in full.

    Each dish links to its recipe by position, through recipe_anchor, so a link
    is an id this file wrote rather than plan text. A dish with no recipe block
    — a side nobody wrote a method for, or a plan that failed its check — is
    printed plain rather than as a link to nothing. The targets are listed
    once and searched in plan order, so the first recipe for a sitting wins. A
    list rather than a dict, because a key is plan values and this renders
    plans nothing validated: a title that is a list would be unhashable, and
    the page must still come out.
    """
    out = ['<section class="glance" id="' + GLANCE[0] + '">', "<h2>" + GLANCE[1] + "</h2>", '<table class="glance-table">']
    out.append('<colgroup><col class="glance-day"><col class="glance-when"><col><col><col></colgroup>')
    out.append(
        '<thead><tr><th scope="col">Day</th><th scope="col">Training</th>'
        + "".join('<th scope="col">' + label + "</th>" for label in SLOT_TO_MEAL.values())
        + "</tr></thead>"
    )
    out.append("<tbody>")
    for day, cells in glance_days(plan):
        row = (
            '<tr><th scope="row">' + prose(day["name"]) + "</th>"
            + '<td class="glance-training">' + prose(day["session"]) + "</td>"
        )
        if cells is None:
            row += '<td class="excluded" colspan="3">' + prose(day["excluded"]) + "</td>"
        else:
            row += "".join("<td>" + cell + "</td>" for cell in cells)
        out.append(row + "</tr>")
    out.append("</tbody>")
    out.append("</table>")
    out.append("</section>")
    return "\n".join(out)


def glance_days(plan):
    """[(day, cells)]: a day and what the glance prints for each of its slots.

    cells is None on a day the athlete is away, and otherwise one string per
    slot, "" for a slot with no meal. The glance and the rail both print from
    here, so the two can never name a day's meals differently.
    """
    targets = [
        ((recipe["day"], recipe["meal"], recipe["title"]), recipe_anchor(plan, recipe))
        for recipe in kept_recipes(plan)
    ]
    result = []
    for day in plan["days"]:
        if "excluded" in day:
            result.append((day, None))
            continue
        cells = []
        for slot in SLOT_TO_MEAL:
            # The first meal in the slot. A second one is a plan the check
            # would have questioned, and it still prints in full below.
            meal = None
            for candidate in day["meals"]:
                if candidate["slot"] == slot:
                    meal = candidate
                    break
            if meal is None:
                cells.append("")
                continue

            def named(dish, sitting=(day["name"], SLOT_TO_MEAL[slot])):
                for key, anchor in targets:
                    if key == sitting + (dish,):
                        return '<a href="#' + anchor + '">' + prose(dish) + "</a>"
                return prose(dish)

            cells.append(meal_body(meal, name=named, bookkeeping=False))
        result.append((day, cells))
    return result


def day_anchor(n) -> str:
    """The id a day of the week carries: its position, from one, as recipe_anchor's is."""
    return "day-" + str(n)


def rail(plan) -> str:
    """The week beside the page on a wide screen: each day, its training and its dishes.

    The glance again, down the side and always in view, so any day or dish is
    one click away however far down the page the reader is. A day's name links
    to it in the week, and a dish to its recipe, exactly as on the glance. Above
    them, the four parts of the page, named as they name themselves.

    Screen only, and only where the window is wide enough for it beside the
    sheet: the stylesheet hides it everywhere else, and in print.
    """
    parts = (GLANCE,) + SECTIONS
    out = ['<nav class="rail" aria-label="Contents">']
    out.append('<p class="rail-title">' + prose(plan["week_label"]) + "</p>")
    out.append(
        '<ul class="rail-parts">'
        + "".join('<li><a href="#' + key + '">' + label + "</a></li>" for key, label in parts)
        + "</ul>"
    )
    out.append('<ol class="rail-week">')
    for n, (day, cells) in enumerate(glance_days(plan), 1):
        out.append(
            '<li><a class="rail-day" href="#' + day_anchor(n) + '">' + prose(day["name"]) + "</a>"
            + '<span class="rail-training">' + prose(day["session"]) + "</span>"
        )
        if cells is None:
            out.append('<p class="excluded">' + prose(day["excluded"]) + "</p>")
        elif any(cells):
            out.append('<ul class="rail-dishes">' + "".join("<li>" + cell + "</li>" for cell in cells if cell) + "</ul>")
        out.append("</li>")
    out.append("</ol>")
    out.append("</nav>")
    return "\n".join(out)


# -------------------------------------------------------------- the pots

def scale_quantity(qty: str, factor: float):
    """A recipe line at a pot's size, or None where it cannot be multiplied.

    **validate.py's own**, not a copy: the page has to print the pot the
    checker added up, and two copies of one rounding rule were caught
    disagreeing on `1.5 kilos` before this was one. The one module this
    script imports from outside the standard library, and it is the script
    beside it in the same skill; dishes_of comes from it too, so the page
    names a meal's dishes the way the checker counts them.
    """
    scaled = scale_line(qty, factor)
    return None if scaled is None else scaled[0]


def _floor(value: float) -> float:
    return float(value // 1)


def origin_of(plan, recipe):
    """The entry carrying this dish's recipe: itself, or the origin it points at."""
    if recipe["kind"] == "origin":
        return recipe
    for r in plan["recipes"]:
        if r["kind"] == "origin" and r["title"] == recipe["title"] and r["day"] == recipe.get("origin_day"):
            return r
    return None


def _numeric(value):
    """A number the arithmetic may use, or None: nothing here validates, so a
    plan may carry a string where the schema says number, and the page still
    has to render."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def portions_at(recipe):
    """The portions one entry's plate adds up to — one where it states none —
    or None where a plate's portions is not a number."""
    plates = recipe.get("plates")
    if not isinstance(plates, list) or not plates:
        return 1.0
    total = 0.0
    for plate in plates:
        value = _numeric(plate.get("portions")) if isinstance(plate, dict) else None
        if value is None:
            return None
        total += value
    return total


def batch_factor(plan, recipe):
    """The pot over what the origin's list is written for, or None.

    None, and the list printed as written, wherever the pot or the list's size
    is not a positive number: multiplying by zero or a negative prints a list of
    nothing, which is worse than one the week does not match."""
    origin = origin_of(plan, recipe)
    yields = _numeric(origin.get("yields")) if origin is not None else None
    if yields is None or yields <= 0:
        return None
    pot = portions_at(recipe) if recipe["kind"] == "repeat" else pot_of(plan, origin)
    if pot is None or pot <= 0:
        return None
    return pot / yields


def servings_of(origin):
    """The sittings an origin's pot is eaten at, read once for the pot and the
    Makes line both: its servings where they are a list, and otherwise — absent,
    null, or anything else a plan nothing validated can carry — one sitting,
    where it is cooked. validate.py reads absent or null the same way."""
    servings = origin.get("servings")
    if isinstance(servings, list):
        return servings
    return [{"day": origin["day"], "meal": origin["meal"]}]


def sittings_of(plan, origin):
    """(sitting, entry, share) for each sitting the origin's servings name.

    Absent servings means one, eaten where it is cooked. An entry is None where
    the sitting names nothing on the page — including where it is not a
    {day, meal} at all, since nothing here validates — and a share is None
    where there is no entry or a plate's portions is not a number.
    """
    out = []
    for slot in servings_of(origin):
        entry = entry_at(plan, slot, origin["title"])
        out.append((slot, entry, None if entry is None else portions_at(entry)))
    return out


def pot_of(plan, origin):
    """The portions an origin's pot cooks: its sittings' plates, added in order.

    A sitting that names no entry adds nothing, and a share that is not a number
    makes the pot unknown. The list is scaled to this number and the Makes line
    states it, so both read it here rather than each adding up their own.
    """
    pot = 0.0
    for _slot, entry, share in sittings_of(plan, origin):
        if entry is None:
            continue
        if share is None:
            return None
        pot += share
    return pot


def entry_at(plan, slot, title):
    """The entry eating `title` at this sitting, or None — including where the
    sitting is not a {day, meal} at all, since nothing here validates."""
    if not isinstance(slot, dict) or "day" not in slot or "meal" not in slot:
        return None
    for r in plan["recipes"]:
        if r["day"] == slot["day"] and r["meal"] == slot["meal"] and r["title"] == title:
            return r
    return None


def portions_phrase(value) -> str:
    """`1 portion`, `0.75 portions`: singular only for exactly one, and only for
    a number — a string the plan wrote is printed as written, escaped."""
    return number(value) + (" portion" if _numeric(value) == 1.0 else " portions")


def _in_quarters(entry) -> bool:
    """Every plate at this sitting is a positive whole number of quarters: what a
    plate is counted in, and what binary floating point adds exactly. Plate by
    plate rather than their sum, so a negative plate cannot hide inside a share
    that looks whole."""
    plates = entry.get("plates")
    if not isinstance(plates, list) or not plates:
        return True
    for plate in plates:
        value = _numeric(plate.get("portions")) if isinstance(plate, dict) else None
        if value is None or value <= 0 or (value * 4) % 1 != 0:
            return False
    return True


def makes_line(plan, recipe, skip):
    """(line, plate): what a card's pot makes, and where it is eaten when that
    is anywhere else, or ""; and whether the line's number is this card's own
    plate, which the meta line then need not state again.

    Every card that cooks carries it: an origin, and a repeat, which cooks its
    own pot at its own plate's size. A pot eaten only where it is cooked says
    how much and nothing more -- `Makes 1 portion.` -- because the band above
    the card already names that sitting. A batch eaten at more than one names
    every sitting it feeds, so the reader sees where the rest goes.

    The total leads when it is the pot the ingredient list below is scaled to,
    and only then — a number the list does not back is the contradiction this
    line exists to remove. On an origin it is withheld unless the pot is
    positive; the origin's own sitting is among the servings, or the pot would
    leave out a plate that eats from it; every sitting is named once and found;
    none was dropped as excluded, which leaves the line and stays in the pot;
    and every plate is a positive whole number of quarters. The last is what
    keeps the sum exact: quarters add without rounding in binary floating
    point, where 1.1 + 2.2 prints 3.3000000000000003. The schema says quarters
    and nothing checks it. A repeat's total is its own plate, under the two
    conditions that apply to one plate: a positive pot and whole quarters.

    Without a total, a pot eaten only where it is cooked has no line at all, a
    repeat's and an origin's alike: the band already names the sitting, and the
    meta line keeps the plate's size. Otherwise a share is bracketed unless it
    is 1, and a lone sitting elsewhere keeps its bracket, or nothing on the
    card would say how big its plate is. A bracket prints its share to two
    places, because a share is itself a sum of plates and two plates of 0.1 and
    0.2 would print 0.30000000000000004.
    """
    # A repeat's pot is its own plate, eaten where it is cooked, and its list is
    # scaled to it. The same conditions as an origin's total: a pot the list is
    # scaled to, and plates in whole quarters.
    if recipe["kind"] == "repeat":
        if batch_factor(plan, recipe) is None or not _in_quarters(recipe):
            return "", False
        return '<p class="serves">Makes ' + portions_phrase(portions_at(recipe)) + ".</p>", True
    # Only an origin lists where its batch goes: servings belong to origins, and
    # a repeat or leftover that copied its origin's would list the batch twice.
    # Its sittings are the pot's own, read through servings_of, so an origin
    # whose servings are absent or malformed still says what its list cooks.
    if recipe["kind"] != "origin":
        return "", False
    sittings = [
        (slot, entry, share)
        for slot, entry, share in sittings_of(plan, recipe)
        if isinstance(slot, dict) and "day" in slot and "meal" in slot
    ]
    # The other direction of the same reconciliation: a portion mapped to a
    # sitting the week says is not happening must not be listed as somewhere
    # this batch is eaten. Dropping the line entirely when nothing survives
    # is right too — an empty "Makes:" would read as a defect in the recipe.
    listed = [t for t in sittings if (t[0]["day"], t[0]["meal"]) not in skip]
    if not listed:
        return "", False

    keys = [(slot["day"], slot["meal"]) for slot, _entry, _share in sittings]
    total = None
    if (
        recipe["kind"] == "origin"
        and batch_factor(plan, recipe) is not None
        and (recipe["day"], recipe["meal"]) in keys
        and all(keys.count(key) == 1 for key in keys)
        and len(listed) == len(sittings)
        and all(entry is not None and _in_quarters(entry) for _slot, entry, _share in listed)
    ):
        total = pot_of(plan, recipe)

    # With a total, the one sitting listed is the origin's own: the conditions
    # above put it among the servings and drop nothing.
    if total is not None and len(listed) == 1:
        return '<p class="serves">Makes ' + portions_phrase(total) + ".</p>", True
    # Without one, the origin's own sitting alone would only repeat the band.
    if len(listed) == 1 and (listed[0][0]["day"], listed[0][0]["meal"]) == (recipe["day"], recipe["meal"]):
        return "", False

    parts = []
    for slot, _entry, share in listed:
        part = prose(slot["day"]) + " " + prose(slot["meal"])
        if share is not None and share != 1.0:
            part += " (" + number(round(share, 2)) + ")"
        parts.append(part)
    lead = "Makes: " if total is None else "Makes " + portions_phrase(total) + ": "
    # Commas between the sittings: a day and a meal are fixed words, so none
    # can hold one.
    return '<p class="serves">' + lead + ", ".join(parts) + "</p>", False


def plate_nutrition(plan, recipe):
    """This sitting's figures: the origin's one portion times this plate's portions,
    rounded half up — Python's round() would take halves to even."""
    origin = origin_of(plan, recipe)
    reference = (origin or {}).get("nutrition")
    if not isinstance(reference, dict):
        reference = {}
    portions = portions_at(recipe)
    out = {}
    for key in ("kcal", "carbs", "protein", "fat", "fibre"):
        value = _numeric(reference.get(key, 0))
        # Whatever cannot be multiplied is printed as the plan wrote it, and
        # `number()` escapes it on the way to the page.
        out[key] = reference.get(key, 0) if value is None or portions is None else int(
            _floor(value * portions + 0.5)
        )
    return out


def portion_size_to_print(plan, recipe, skip):
    """The origin's `portion_size`, where it is the only thing on the card that
    turns a share into an amount — or None.

    That is a batch whose sittings eat unequal shares, on its origin and its
    leftovers: `Monday Dinner (0.75), Tuesday Lunch (1.25)` with one portion at
    400 g cooked is 300 g now and 500 g boxed, and nothing else on either card
    says so. Everywhere else the list already does. A single sitting's list is
    scaled to its plate, a repeat cooks its own, and an even batch is its list
    divided by the Makes line's count.

    Uneven among the sittings the Makes line lists, so an excluded one — which
    the line drops — cannot make equal shares on the card read as uneven.

    The string is the model's, printed as written: nothing computes or checks
    it, which is a second reason to print it only where it earns its place.
    """
    if recipe["kind"] not in ("origin", "leftover"):
        return None
    origin = origin_of(plan, recipe)
    if origin is None or "portion_size" not in origin:
        return None
    shares = []
    for slot, entry, share in sittings_of(plan, origin):
        if isinstance(slot, dict) and (slot.get("day"), slot.get("meal")) in skip:
            continue
        if entry is not None and share is not None and share not in shares:
            shares.append(share)
    return origin["portion_size"] if len(shares) > 1 else None


def recipe_anchor(plan, recipe) -> str:
    """The id a recipe's block carries: its position in the plan, from one.

    A position and never words. The title would need case mapping to become an
    id, which the docstring rules out, and it is plan text, which never goes in
    an attribute. Found by identity, because two entries may be equal.
    """
    for i, r in enumerate(plan["recipes"]):
        if r is recipe:
            return "recipe-" + str(i + 1)
    raise ValueError("a recipe that is not in the plan")


def recipe_block(plan, recipe, skip, packs, photo=None) -> str:
    time = recipe["time"]
    nutrition = plate_nutrition(plan, recipe)
    cook_label = time.get("cook_label", "cook")
    # The times alone: the band above the card names the day and the meal.
    meta = [
        "prep " + number(time["prep"]) + " min",
        esc(cook_label) + " " + number(time["cook"]) + " min",
    ]
    makes, plate_said = makes_line(plan, recipe, skip)
    # A bigger bowl says how much bigger, in the unit its figures are counted in,
    # and what one of those is where the recipe says. A lone plate with no
    # reason, on a card whose pot is that plate and whose Makes line says so,
    # is said there once. A batch's plate stays here, beside the figures it
    # comes to, rather than only in a bracket under them.
    plates = recipe.get("plates")
    if isinstance(plates, list):
        for plate in plates:
            if plate_said and len(plates) == 1 and isinstance(plate, dict) and "note" not in plate:
                continue
            if isinstance(plate, dict) and "portions" in plate:
                why = " (" + prose(plate["note"]) + ")" if "note" in plate else ""
                meta.append(portions_phrase(plate["portions"]) + why)
    size = portion_size_to_print(plan, recipe, skip)
    if size is not None:
        meta.append("one portion: " + prose(size))
    macros = [
        number(nutrition["kcal"]) + " kcal",
        number(nutrition["carbs"]) + " g carbs",
        number(nutrition["protein"]) + " g protein",
        number(nutrition["fat"]) + " g fat",
        number(nutrition["fibre"]) + " g fibre",
    ]

    # A card with a photo says so in its class, so the stylesheet can float the
    # photo and contain it without touching a card that has none.
    pictured = " pictured" if photo is not None else ""
    out = ['<article class="recipe ' + esc(recipe["kind"]) + pictured + '" id="' + recipe_anchor(plan, recipe) + '">']

    # The photo floats at the start of the card and everything down to the
    # ingredients sits beside it, the title first. A square, because a panoramic
    # strip crops the plate's rim away. An <img> rather than a background,
    # because print drops backgrounds; alt is empty, because the title is beside
    # it and plan text never goes in an attribute.
    if photo is not None:
        out.append('<img class="recipe-photo" src="' + photo + '" alt="">')
    out.append("<h4>" + prose(recipe["title"]) + "</h4>")

    # Beside a photo, the two times are one unit the stylesheet keeps on one
    # line; what follows them may wrap.
    if photo is not None:
        head = '<span class="nb">' + " &middot; ".join(meta[:2]) + "</span>"
        out.append('<p class="recipe-meta">' + " &middot; ".join([head] + meta[2:]) + "</p>")
    else:
        out.append('<p class="recipe-meta">' + " &middot; ".join(meta) + "</p>")

    # The macros are this sitting's plate — the origin's portion times this
    # entry's portions — so on every card they are the second line, and every
    # card reads the same way: the plate and what it comes to, then what to do
    # about it. A batch's plate is stated on the meta line directly above them;
    # a pot that is the plate, by the Makes line directly below.
    # They used to follow the pointer and the Makes line, which split
    # `2 portions` from its kcal by a pot of six and made the figures read as
    # the pot's. A leftover's pointer, which is the whole of its block, is now
    # its last line, under its figures: one card shape was judged worth more
    # than the pointer leading.
    out.append('<p class="macros">' + " &middot; ".join(macros) + "</p>")

    # Where a card points at another, it does so before its ingredients: on a
    # repeat whose origin has no method, arriving at the pointer first is the
    # difference between "this is Monday's again, here is this morning's
    # amount" and a recipe with its method missing.
    #
    # The pointer names the sitting that cooked the dish, and those words link
    # to its card, whose band reads the same: "Leftover from Monday Dinner" is
    # a tap on a phone rather than a scroll back through the week. No check
    # that the origin is on the page, because one found always is:
    # kept_recipes keeps every origin a surviving entry names by (title,
    # origin_day), which is the key origin_of matches, and recipe_days prints
    # every kept entry. An origin not found is a broken plan, and the sentence
    # names the day alone, without a link.
    #
    # A repeat is printed whole instead: its own amounts, the first cook's
    # method, and no pointer, so the card you cook from on the day is complete
    # and reads exactly as the first cook's does. A leftover cooks nothing and
    # keeps its pointer.
    origin = origin_of(plan, recipe)
    lead = KIND_LEAD.get(recipe["kind"])
    whole = recipe["kind"] == "repeat" and origin is not None and "steps" in origin
    if lead is not None and "origin_day" in recipe and not whole:
        if origin is not None:
            sitting = (
                '<a href="#' + recipe_anchor(plan, origin) + '">'
                + prose(origin["day"]) + " " + prose(origin["meal"]) + "</a>"
            )
        else:
            sitting = prose(recipe["origin_day"])
        out.append('<p class="pointer">' + lead + sitting + ".</p>")

    # The Makes line is the pot, so it sits on the list the pot is cooked from.
    # A leftover carries the pointer and no Makes line, since it cooks nothing.
    # A repeat carries both only where its origin has no method to print: it
    # still cooks its own pot, and the pointer says where the method was meant
    # to be.
    if makes:
        out.append(makes)


    # The pot this entry cooks: the origin's list at this pot's size. A leftover
    # cooks nothing, so it lists nothing.
    factor = batch_factor(plan, recipe)
    lines = []
    if recipe["kind"] != "leftover" and origin is not None:
        for line in origin.get("ingredients") or []:
            scaled = scale_quantity(line["qty"], factor) if factor is not None else None
            lines.append({"item": line["item"], "qty": scaled if scaled is not None else line["qty"]})
    if lines:
        out.append('<ul class="ingredients">')
        for ingredient in lines:
            # The line's own count, never the shopping row's: it is computed
            # from the quantity it sits beside, so a repeat's list prints its
            # own day's count rather than the origin's.
            head = ingredient["item"].split(",")[0].strip().lower()
            out.append(
                "<li>" + prose(ingredient["item"])
                + ' <span class="qty">' + prose(ingredient["qty"]) + "</span>"
                + hint_span(counted(ingredient["qty"], packs.get(head), True)) + "</li>"
            )
        out.append("</ul>")

    steps = recipe["steps"] if "steps" in recipe else origin["steps"] if whole else None
    if steps is not None:
        out.append('<ol class="steps">')
        for step in steps:
            out.append("<li>" + prose(step) + "</li>")
        out.append("</ol>")

    out.append("</article>")
    return "\n".join(out)


def excluded_sittings(plan):
    """Every (day, meal) the athlete is not eating here, as the recipes spell it.

    The third site of one rule, and the one a search for the word would not have
    found: this section never reads an exclusion, which is exactly why it went on
    printing Friday's cooking instructions under a Friday that says the athlete
    is away.

    A list rather than a set: sets iterate in hash order, and nothing in a
    byte-compared artifact may do that.
    """
    sittings = []
    for day in plan["days"]:
        if "excluded" in day:
            # The schema is explicit that no recipe may name an excluded day.
            sittings.extend((day["name"], meal) for meal in SLOT_TO_MEAL.values())
            continue
        for meal in day["meals"]:
            if "excluded" in meal and meal["slot"] in SLOT_TO_MEAL:
                sittings.append((day["name"], SLOT_TO_MEAL[meal["slot"]]))
    return sittings


def kept_recipes(plan):
    """The recipes to print: excluded sittings dropped, unless something needs them.

    Filtering is a judgement about the plan, which this file otherwise leaves to
    validate.py, and it is right here for a reason that does not generalise:
    this page is rendered after a failed check on purpose, so a plan carrying
    the contradiction does reach it.

    **The second clause is the one that matters, and dropping without it was
    worse than not dropping at all.** A repeat or a leftover carries no method —
    it points at the day that has it. Remove an origin whose sitting is excluded
    and every later serving of that dish still points at a day the page no longer
    shows, so a meal the athlete *is* eating becomes uncookable. That is a worse
    failure than the contradiction the filter exists to remove, so an origin
    something surviving still points at is kept: the exclusion says nobody eats
    it that morning, not that the method stops existing.
    """
    skip = excluded_sittings(plan)
    dropped = [r for r in plan["recipes"] if (r["day"], r["meal"]) in skip]

    # What the survivors still point at: (title, the day carrying the method).
    needed = [
        (r["title"], r.get("origin_day"))
        for r in plan["recipes"]
        if (r["day"], r["meal"]) not in skip and r.get("origin_day") is not None
    ]

    kept = []
    for recipe in plan["recipes"]:
        if recipe not in dropped:
            kept.append(recipe)
        elif recipe["kind"] == "origin" and (recipe["title"], recipe["day"]) in needed:
            kept.append(recipe)
    return kept


def recipe_days(plan):
    """The kept recipes bucketed by the day that eats them, in the week's order.

    The athlete arrives at this section with a day in hand — it is Thursday,
    what am I cooking — so the day is the key, and a flat run of every dish in
    the plan makes them read every caption to find it.

    No sort and no set, because the page is compared byte for byte and both
    vary between interpreters: the order is plan["days"] as the plan states it.
    A day nothing survives for is not emitted at all, since a heading with
    nothing under it reads as a defect in the page rather than as an empty day.
    A recipe naming a day the week does not list still prints, in a group of its
    own after the plan's days — this file renders plans that failed a check, so that
    is reachable, and dropping the recipe would lose a meal silently.

    The dict is a lookup and is never iterated, so nothing here depends on its
    insertion order either.
    """
    groups = []
    at = {}
    for day in plan["days"]:
        if day["name"] not in at:
            at[day["name"]] = len(groups)
            groups.append((day["name"], []))
    for recipe in kept_recipes(plan):
        if recipe["day"] not in at:
            at[recipe["day"]] = len(groups)
            groups.append((recipe["day"], []))
        groups[at[recipe["day"]]][1].append(recipe)
    return [group for group in groups if group[1]]


def sittings_in(group):
    """[(meal, [recipe])]: one day's recipes gathered under the meal that eats them.

    In the order the plan first names each meal, and a list rather than a dict
    or a sort, for the same reason as recipe_days: the page is compared byte
    for byte. A main and its side at one sitting share one band.
    """
    sittings = []
    for recipe in group:
        for meal, dishes in sittings:
            if meal == recipe["meal"]:
                dishes.append(recipe)
                break
        else:
            sittings.append((recipe["meal"], [recipe]))
    return sittings


def away_reasons(plan):
    """Day name -> the reason the week gives for planning no meals on it."""
    return {day["name"]: day["excluded"] for day in plan["days"] if "excluded" in day}


def recipes(plan, photos=None) -> str:
    photos = photos or {}
    skip = excluded_sittings(plan)
    away = away_reasons(plan)
    # Built once for the whole section: a line's count needs its food's pack,
    # and the pack lives on the shopping row rather than on the line.
    packs = packs_by_name(plan)
    out = ['<section class="recipes">', section_heading("recipes")]
    for name, group in recipe_days(plan):
        out.append('<section class="recipe-day">')
        for meal, dishes in sittings_in(group):
            # A band for each sitting, the day on the left and the meal on the
            # right: scrolled to the middle of a method, the band stuck to the
            # top of the window still says which meal this is.
            out.append('<section class="sitting">')
            out.append(
                '<h3 class="sitting-band"><span class="band-day">' + prose(name) + "</span> "
                + '<span class="band-meal">' + prose(meal) + "</span></h3>"
            )
            # The exclusion rule reaches one site further once the recipes are
            # grouped. kept_recipes keeps an origin on an excluded day when a
            # surviving leftover still points at its method, so without this the
            # band would print a day name over a day the week says has no meals.
            # The day's own reason goes under it, worded exactly as the week
            # words it — the method survives the exclusion; the meal does not.
            # Under every band of the day, not only the first: each band is
            # read on its own, stuck to the top of the window or at the head
            # of a printed page, and each of its recipes needs the reason.
            if name in away:
                out.append('<p class="excluded">' + prose(away[name]) + "</p>")
            for recipe in dishes:
                # Only a string can be a key: this renders plans that failed the
                # check, and a title of any other shape must still print.
                title = recipe["title"]
                photo = photos.get(title) if photos and recipe["kind"] in PHOTO_KINDS and isinstance(title, str) else None
                out.append(recipe_block(plan, recipe, skip, packs, photo))
            out.append("</section>")
        out.append("</section>")
    out.append("</section>")
    return "\n".join(out)


def shop_item(item, skip_days, drained=False) -> str:
    aside = []
    if "days" in item:
        # A day the athlete is away uses nothing, so naming it here is simply
        # false. Dropping it is a claim about *which days*, which is decidable
        # from the week alone — unlike the quantity beside it, which is a sum
        # this file must not recompute. See shop_sheet.
        used = [day for day in item["days"] if day not in skip_days]
        if used:
            aside.append(", ".join(prose(day) for day in used))
    if "note" in item:
        aside.append(prose(item["note"]))
    tail = ""
    if aside:
        tail = ' <span class="when">(' + " &mdash; ".join(aside) + ")</span>"
    # A count of the purchase, set beside the amount rather than after the
    # days: this half is read in the shop and the tags are read at home.
    #
    # A drained weight is not what any label says. `18 oz` of beans is two
    # 15 oz cans, and a shopper reading `18 oz (2 cans)` against those labels
    # decides the list was converted from grams. So where the recipes drain
    # the food, the count of containers is the amount and the weight is the
    # aside, marked as drained: `2 cans (18 oz drained)`. With no container to
    # count, the weight stays the amount and is marked all the same.
    weight = prose(item["qty"])
    count = counted(item["qty"], item.get("pack"), False)
    pack = item.get("pack")
    if drained and count and (pack.get("one") or pack.get("many")):
        amount = ' <span class="qty">' + prose(count) + "</span>" + hint_span(item["qty"] + " drained")
    elif drained:
        amount = ' <span class="qty">' + weight + "</span>" + hint_span(
            (count + ", " if count else "") + "drained")
    else:
        amount = ' <span class="qty">' + weight + "</span>" + hint_span(count)
    #
    # A box to tick, and the whole row is its label so the row is the target.
    # No name and no form: nothing is submitted and nothing is kept, so a
    # reload clears it, which is fine for a list. In print it is an empty
    # square for a pen. No space after the box: its margin is the gap, so a
    # row that wraps hangs exactly under its text. The fridge list has none, because nothing on it is
    # bought.
    return (
        '<li><label><input type="checkbox">' + prose(item["name"])
        + amount + tail + "</label></li>"
    )


# --------------------------------------------------------------- the count --
#
# The page works the count out rather than printing one the plan states. A row
# says how much the week uses and how much one purchase provides; dividing is
# this renderer's job, on both lists.
#
# **This is arithmetic, and the docstring's byte-for-byte rule permits it.**
# That rule is about results that vary between machines or interpreters, because
# the example page has to come out the same byte for byte. Dividing two decimal
# strings in IEEE 754 doubles and flooring the result does not vary: every
# Python 3.9+ on every platform gives the same double. What the rule protects
# against is a dict order or a hash seed leaking onto the page, and none of that
# is here.
#
# **It is deliberately weak**: no unit tables, no name folding, no fuzzy
# matching. Its failure mode is a missing count, never a wrong one.

#: `4.2 / 1.4` is `3.0000000000000004`, so a bare ceil answers 4 where the
#: answer is 3.
EPSILON = 1e-9

#: How far from a whole pack a recipe line may sit and still be one. 250 g of a
#: 240 g drained tin is one tin (0.042, inside); 120 g of it is half (0.5,
#: outside). Containers only — produce is almost never within 5% of a whole
#: piece, and gating loose pieces would suppress most of the useful counts.
WHOLE_PACK_TOLERANCE = 0.05

#: The number and the unit out of "4 g", or out of "300 g, cubed". Deliberately narrower than the
#: checker's reader of the same field: no unit tables and no conversion, because
#: a pack is defined to be written in the row's own measure, so the units only
#: have to match as written.
_AMOUNT = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*([^\s,]*)")


def amount(text):
    """`(value, unit)` from a quantity string, or None."""
    if not isinstance(text, str):
        return None
    found = _AMOUNT.match(text)
    if not found:
        return None
    return float(found.group(1)), found.group(2)


def counted(quantity, pack, whole_only: bool):
    """The count a quantity comes to against a pack, as a string, or ``""``.

    Silence wherever the arithmetic cannot be done — no pack, a quantity that
    does not parse, two different units. Never an error: the cost of silence is
    a missing parenthetical and this page is carried into a shop.
    """
    if not isinstance(pack, dict):
        return ""
    used = amount(quantity)
    one = amount(pack.get("qty"))
    if not used or not one or used[1] != one[1] or one[0] <= 0:
        return ""
    x = used[0] / one[0]
    if whole_only:
        # `floor(x + 0.5)` rather than round(): Python rounds halves to even,
        # so a line at exactly half a piece would count down to the even
        # number rather than up.
        n = int(x + 0.5)
        if n < 1:
            return ""
        if (pack.get("one") or pack.get("many")) and abs(x - n) > WHOLE_PACK_TOLERANCE:
            return ""
    else:
        n = int(-(-(x - EPSILON) // 1))
        if n < 1:
            return ""
    noun = (pack.get("one") or pack.get("many")) if n == 1 else (pack.get("many") or pack.get("one"))
    return (str(n) + " " + noun) if noun else str(n)


def packs_by_name(plan) -> dict:
    """Every row's pack, keyed by the row's name and by its singular.

    A recipe line writes its row's name — the same words — optionally followed
    by a preparation after a comma, which the schema requires and which makes
    the lookup a dict rather than a matcher. The trailing-s key is what resolves
    "Chicken breast" against a "Chicken breasts" row; measured over 642 real
    lines, head-and-fold resolves 98.3% and the exact head alone 96.3%. Every
    remaining miss is a food already in the fridge or on no row at all, which
    would carry no pack either way.

    Legitimate because the plan is written in English by construction, and a
    trailing s is an English plural.

    Two passes, and the order is the whole of why. A single pass inserting each
    row's name and its singular together lets a plural row claim the singular
    key before the row that owns it is reached: a list carrying both "Peppers"
    and "Pepper" would give every Pepper line the peppers' pack -- a *wrong*
    count, where everything else here fails by printing none. Exact names are
    claimed first; aliases only fill what is still free.
    """
    rows = []
    for group in plan.get("shopping") or []:
        for item in group.get("items") or []:
            pack = item.get("pack")
            name = (item.get("name") or "").strip()
            if isinstance(pack, dict) and name:
                rows.append((name.lower(), pack))
    found = {}
    for name, pack in rows:
        found.setdefault(name, pack)
    for name, pack in rows:
        if name.endswith("s"):
            found.setdefault(name[:-1], pack)
    return found


#: A recipe line that drains its food says so after the comma, the way the
#: skill writes one: `Tinned chickpeas, drained and rinsed`.
DRAINED = re.compile(r"\bdrained\b")


def drained_heads(plan) -> dict:
    """The name of every food a recipe line drains, lower-cased, as dict keys.

    Read off the lines rather than asked of the plan, because the lines say it
    already: a model writes `Canned black beans, drained` without being asked,
    and a field it had to remember is a field it can leave out. A key is the
    line's head before its comma, which is how packs_by_name keys a line too.
    """
    found = {}
    for recipe in plan.get("recipes") or []:
        for line in recipe.get("ingredients") or []:
            head, comma, rest = str(line.get("item") or "").partition(",")
            if comma and DRAINED.search(rest.lower()):
                found.setdefault(head.strip().lower(), True)
    return found


def drains(item, heads) -> bool:
    """Whether the recipes weigh this row's food drained.

    The row's name, or the row's name less a plural s, as packs_by_name
    resolves a "Chicken breast" line to a "Chicken breasts" row.
    """
    name = str(item.get("name") or "").strip().lower()
    return name in heads or (name.endswith("s") and name[:-1] in heads)


def hint_span(text: str) -> str:
    """The aside beside a quantity, in quieter ink at the same size.

    Usually a count. Takes the computed string rather than an entry, because the
    row's count and the line's are worked out from different numbers and only
    the markup is shared. A drained row turns it round, and the weight is the
    aside (shop_item).
    """
    if not text:
        return ""
    return ' <span class="qty-hint">(' + prose(text) + ")</span>"


def in_us_units(plan) -> bool:
    """Whether the shopping list is weighed in US customary units.

    The skill picks the units by the athlete's country, so they are the one
    place the page can read the country from without a field of its own. Read
    from the rows' quantities, counted rather than read off the first, so a
    stray `500 ml` on a list in ounces and pounds does not turn its aisles
    British; a tie, and a list of counts and spoons alone, stays as written.
    The unit is lower-cased only when it is ASCII, which every unit in the
    tables is, so no case mapping depends on the Unicode database.
    """
    us = metric = 0
    for group in plan.get("shopping") or []:
        for item in group.get("items") or []:
            written = written_quantity(str(item.get("qty") or ""))
            word = written[1] if written else None
            if not word or not word.isascii():
                continue
            unit = singular(word.lower())
            if unit in US_UNITS:
                us += 1
            elif unit in MASS_UNITS or unit in VOLUME_UNITS:
                metric += 1
    return us > metric


def shop_sheet(plan) -> str:
    """The fridge, the list and the closing note — one page, one page break.

    The break sits on this wrapper rather than on the list, because what is
    already in the fridge is read before leaving and belongs at the top of the
    page you carry to the shop.
    """
    # Which days buy nothing, so a usage tag does not name a day the week says
    # the athlete is away.
    #
    # **The quantity beside it is deliberately left alone**, and that boundary is
    # the point rather than an omission. It is the sum of an item across every
    # recipe that cooks with it, so correcting it means re-deriving that sum from
    # the ingredient lists — which is the check this file exists *not* to
    # duplicate, and a second implementation that disagreed with the real one
    # would be worse than an over-inclusive list. Buying a little too much is
    # recoverable; a quantity that no longer matches anything is not. For the
    # same reason a single excluded *meal* is not filtered here at all: whether
    # the remaining sittings still use an item is only answerable by matching
    # ingredients to shopping names, which is that same check.
    skip_days = [DAY_ABBR_OF[d["name"]] for d in plan["days"] if "excluded" in d]

    out = ['<section class="shop-sheet">']

    if plan["fridge"]:
        out.append('<section class="fridge">')
        out.append("<h2>Already in the fridge</h2>")
        out.append('<ul class="fridge-list">')
        for entry in plan["fridge"]:
            line = "<li>" + prose(entry["name"])
            if "qty" in entry:
                line += ' <span class="qty">' + prose(entry["qty"]) + "</span>"
            out.append(line + "</li>")
        out.append("</ul>")
        out.append("</section>")

    aisles = US_AISLES if in_us_units(plan) else {}
    drained = drained_heads(plan)

    out.append('<section class="shopping">')
    out.append(section_heading("shopping"))
    out.append('<div class="shop-cols">')
    for category in plan["shopping"]:
        out.append('<section class="shop-cat">')
        name = category["category"]
        out.append("<h3>" + prose(aisles.get(name, name)) + "</h3>")
        out.append('<ul class="shop-list">')
        for item in category["items"]:
            out.append(shop_item(item, skip_days, drains(item, drained)))
        out.append("</ul>")
        out.append("</section>")
    out.append("</div>")
    out.append("</section>")

    if "closing_note" in plan:
        out.append('<p class="closing">' + prose(plan["closing_note"]) + "</p>")

    out.append("</section>")
    return "\n".join(out)


def sniff(data):
    """(type, width, height) from an image's own first bytes, or None.

    The bytes decide, never the file's name: a drawing saved as .png that is
    really a JPEG is a JPEG, and a file that is not one of the three -- the plan
    named by mistake, a GIF, an SVG, a header cut short -- is not embedded in a
    page that may be published. The sizes are read from the header alone.
    """
    big = "big"
    little = "little"
    if data[:3] == b"\xff\xd8\xff":
        i = 2
        while i + 1 < len(data):
            if data[i] != 0xFF:
                return None
            while i < len(data) and data[i] == 0xFF:
                i += 1
            if i >= len(data):
                return None
            marker = data[i]
            i += 1
            # Markers with no length after them.
            if marker == 0x01 or 0xD0 <= marker <= 0xD8:
                continue
            # The image data or its end, and no frame header before it.
            if marker in (0xD9, 0xDA):
                return None
            if i + 2 > len(data):
                return None
            length = int.from_bytes(data[i:i + 2], big)
            # A start-of-frame: every C0-CF but the three that are not one.
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                if i + 7 > len(data):
                    return None
                height = int.from_bytes(data[i + 3:i + 5], big)
                width = int.from_bytes(data[i + 5:i + 7], big)
                return ("image/jpeg", width, height) if width and height else None
            if length < 2:
                return None
            i += length
        return None
    if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR" and len(data) >= 24:
        width = int.from_bytes(data[16:20], big)
        height = int.from_bytes(data[20:24], big)
        return ("image/png", width, height) if width and height else None
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        width = height = 0
        if chunk == b"VP8 " and len(data) >= 30 and data[23:26] == b"\x9d\x01\x2a":
            width = int.from_bytes(data[26:28], little) & 0x3FFF
            height = int.from_bytes(data[28:30], little) & 0x3FFF
        elif chunk == b"VP8L" and len(data) >= 25 and data[20] == 0x2F:
            bits = int.from_bytes(data[21:25], little)
            width = (bits & 0x3FFF) + 1
            height = ((bits >> 14) & 0x3FFF) + 1
        elif chunk == b"VP8X" and len(data) >= 30:
            width = int.from_bytes(data[24:27], little) + 1
            height = int.from_bytes(data[27:30], little) + 1
        return ("image/webp", width, height) if width and height else None
    return None


def photo_titles(plan):
    """Each title that carries a tile, first appearance first, with its block count.

    The recipes the page prints, in the order it prints them, so a photo's
    place in the running total is its place on the page. A list of pairs rather
    than a dict, because the order is the point.
    """
    titles = []
    for _name, group in recipe_days(plan):
        for recipe in group:
            if recipe["kind"] not in PHOTO_KINDS or not isinstance(recipe["title"], str):
                continue
            for entry in titles:
                if entry[0] == recipe["title"]:
                    entry[1] += 1
                    break
            else:
                titles.append([recipe["title"], 1])
    return titles


def depicts(plan, title):
    """A short digest of what a dish's photo shows: its title and its ingredients.

    The ingredients are the first cook's, in the plan's order -- every card for
    the dish shows the one photo, and the photo is drawn from that recipe. A
    title that is not well-formed text still digests.
    """
    items = []
    for recipe in plan["recipes"]:
        if recipe.get("kind") == "origin" and recipe.get("title") == title:
            for line in recipe.get("ingredients") or []:
                items.append(str(line.get("item", "")) if isinstance(line, dict) else str(line))
            break
    shown = json.dumps([title, items], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(shown.encode("utf-8", "surrogatepass")).hexdigest()[:12]


def read_photo(folder, given, list_name):
    """((bytes, (type, width, height)), None) for a photo the page can use, or (None, why).

    One test of a usable photo on its own, asked in two places: by the page,
    which embeds it, and by the list, which says have only where this passes --
    a file that is empty, the wrong kind or too big is still draw. It reads the
    header, not the whole image, so a file cut short after its header passes;
    and the page's total across photos is the page's alone to apply.
    """
    try:
        relative = Path(given)
        target = (folder / relative).resolve()
        inside = not relative.is_absolute() and ".." not in relative.parts and target.is_relative_to(folder)
    except Exception:
        return None, given + " is not a file that will open"
    if not inside:
        return None, given + " is outside the folder " + list_name + " is in"
    try:
        if not target.is_file():
            raise OSError("not a file")
        with open(target, "rb") as handle:
            data = handle.read(PHOTO_MAX_BYTES + 1)
    except Exception:
        return None, given + " is not a file that will open"
    if len(data) > PHOTO_MAX_BYTES:
        return None, given + " is over the " + str(PHOTO_MAX_BYTES) + " bytes one photo may be; shrink it"
    found = sniff(data)
    if found is None:
        return None, given + " is not a JPEG, PNG or WebP"
    return (data, found), None


def load_photos(path, titles):
    """Title -> data URI for the photos the list names, and the warnings.

    titles is photo_titles(plan): the dishes the page prints, in page order,
    each with its number of cards -- computed once, so the count main reports is
    the count walked here.

    Nothing here costs the page. A photo that cannot be used is a warning and
    its dish has no tile, and anything unforeseen is one warning and no photos
    at all -- the page is the product, and a photo is not.

    A path is read only when it is relative, has no "..", and lands inside the
    folder the list is in once links are followed: that folder is what the
    renderer was handed, and a list is not a way to reach anything else.

    A dish either has its photo wherever it appears or has none, so the running
    total counts the photo once per block that carries it, and a photo that
    would pass the total is skipped while later, smaller ones may still fit.
    """
    photos = {}
    warnings = []

    def quoted(text):
        return json.dumps(text, ensure_ascii=False)

    try:
        listing = Path(path)
        try:
            names = json.loads(listing.read_bytes().decode("utf-8"))
            if not isinstance(names, dict):
                raise ValueError("it is not a JSON object of dish titles")
        except Exception as error:
            return {}, ["no photos: " + path + " will not open: " + str(error)]
        folder = listing.resolve().parent
        total = 0
        for title, blocks in titles:
            if title not in names:
                continue
            given = names[title]
            lead = "no photo for " + quoted(title) + ": "
            if not isinstance(given, str):
                warnings.append(lead + "its entry is not a path")
                continue
            usable, problem = read_photo(folder, given, listing.name)
            if usable is None:
                warnings.append(lead + problem)
                continue
            data, found = usable
            if total + len(data) * blocks > PHOTOS_MAX_BYTES:
                warnings.append(
                    lead + "the page's photos would pass " + str(PHOTOS_MAX_BYTES) + " bytes"
                )
                continue
            kind, width, height = found
            if abs(width - height) * 20 > max(width, height):
                warnings.append(
                    "photo for " + quoted(title) + " is " + str(width) + "x" + str(height)
                    + ", not square; the tile shows its centre"
                )
            total += len(data) * blocks
            photos[title] = "data:" + kind + ";base64," + base64.b64encode(data).decode("ascii")
        on_page = [entry[0] for entry in titles]
        for key in names:
            if key not in on_page:
                warnings.append("no dish on the page is called " + quoted(key) + "; its photo is not used")
    except Exception as error:
        return {}, ["no photos: " + str(error)]
    return photos, warnings


def document(plan, css, photos=None) -> str:
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>" + esc(plan["week_label"]) + "</title>",
            "<style>",
            css,
            "</style>",
            "</head>",
            "<body>",
            rail(plan),
            '<main class="sheet">',
            head(plan),
            glance(plan),
            days(plan),
            recipes(plan, photos),
            shop_sheet(plan),
            "</main>",
            "</body>",
            "</html>",
            "",
        ]
    )


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    # A photo's warning quotes a dish's title, which may be in any script; on a
    # stderr that cannot encode it, printing the warning would crash the run
    # after the page was written.
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Render a meal plan as a printable page.")
    parser.add_argument("path", help="the plan document to render")
    parser.add_argument("out", help="where to write the printable page, or the list with --list-photos")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--photos", help="a JSON object of dish title to image file, beside the images")
    mode.add_argument(
        "--list-photos",
        action="store_true",
        help="write the list of photos the page would show instead of the page",
    )
    args = parser.parse_args(argv)

    # The stylesheet is the skill's own file rather than anything the caller
    # named, so it gets its own message. Folded into the one below, a skill
    # copied without its assets directory would report that the plan could
    # not be rendered, sending somebody to fix a plan that is fine.
    #
    # The list of photos uses no stylesheet, so it does not ask for one.
    css = ""
    try:
        if not args.list_photos:
            css = CSS_PATH.read_bytes().decode("utf-8")
        # A style element ends at the first closing sequence whatever its case,
        # so this cannot be left to valid CSS never containing one.
        if "</style" in css.lower():
            raise ValueError("the stylesheet would close its own style element")
    except Exception as error:
        print(
            "could not read the stylesheet " + str(CSS_PATH) + ": " + str(error),
            file=sys.stderr,
        )
        return 2

    # Finding the file and making sense of it are two failures with opposite
    # repairs, the same split validate.py makes. Bytes here, characters below:
    # text that is not valid UTF-8 is a document written badly at the right
    # path, which is the second case and not the first.
    try:
        with open(args.path, "rb") as handle:
            raw = handle.read()
    except Exception as error:
        print("could not read " + args.path + ": " + str(error), file=sys.stderr)
        return 2

    # The list of photos is written here rather than by a line the host types:
    # which dishes the page prints is this file's knowledge, and it already reads
    # and writes UTF-8 whatever the locale.
    #
    # Each photo is named for what it shows -- a short digest of the dish's
    # title and its ingredients, the two things a drawing is made from -- in a
    # photos folder beside the list, where --photos looks for them. Not for its
    # position: a numbered 3.jpg means whichever dish is third, so a list made
    # again after the plan changed, or last week's in the same folder, would put
    # an old drawing under a new dish. Not for the title alone either: a stir-fry
    # that swapped its chicken for tofu keeps its name and must not keep its
    # picture. Named for what it shows, a dish that did not change -- listed
    # again, in another week, under another file name -- finds its drawing, and
    # one that changed in any way gets a path nothing was drawn at. Nothing is
    # deleted or dated to tell them apart.
    #
    # The list is a .json file or nothing: the two commands differ by one flag,
    # and the one that writes a page must never be answered by writing a list
    # over it.
    if args.list_photos and not args.out.lower().endswith(".json"):
        print("could not write " + args.out + ": the list of photos is a .json file", file=sys.stderr)
        return 2
    photos, warnings, titles = {}, [], []
    try:
        plan = json.loads(raw.decode("utf-8"))
        if args.list_photos:
            titles = photo_titles(plan)
            drawings = "photos"
            listing = {title: drawings + "/" + depicts(plan, title) + ".jpg" for title, _ in titles}
            # ASCII escapes: the list round-trips through any JSON reader, a
            # title that is not well-formed text included.
            page = json.dumps(listing, indent=1) + "\n"
        else:
            if args.photos is not None:
                titles = photo_titles(plan)
                photos, warnings = load_photos(args.photos, titles)
            page = document(plan, css, photos)
    except Exception as error:
        doing = "list" if args.list_photos else "render"
        print("could not " + doing + " " + args.path + ": " + str(error), file=sys.stderr)
        return 2

    # Refuse to write over the plan itself. By this point it has been read into
    # memory, so the write would succeed, report success, and leave the athlete
    # holding HTML where their only copy of the document used to be — the worst
    # shape a failure can take, because nothing looks wrong.
    #
    # It is worth a guard rather than a warning because the two paths are
    # exactly what step 6 says is easiest to get wrong. resolve() follows a
    # symlink; the stat comparison catches a hard link, which resolve() cannot
    # see. Both are best-effort: a path that cannot be inspected is not a reason
    # to refuse a write that would otherwise be fine.
    same = False
    try:
        same = Path(args.path).resolve() == Path(args.out).resolve()
        if not same and Path(args.out).exists():
            source, target = Path(args.path).stat(), Path(args.out).stat()
            same = (source.st_dev, source.st_ino) == (target.st_dev, target.st_ino)
    except Exception:
        same = False
    if same:
        print(
            "could not write " + args.out + ": that is the plan itself",
            file=sys.stderr,
        )
        return 2

    # Both of these are load-bearing for the byte comparison: the explicit
    # encoding overrides whatever the host's default is, and the explicit
    # newline stops the platform translating the line endings on the way out.
    try:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(page)
    except Exception as error:
        print("could not write " + args.out + ": " + str(error), file=sys.stderr)
        return 2

    # The folder the drawings go in, made here because the list names it: a host
    # whose image tool will not make a parent folder would lose every drawing.
    # Each dish's path is printed on one line of its own, whatever the title
    # holds, because the host reads the paths off these lines.
    if args.list_photos:
        try:
            beside = Path(args.out).resolve().parent
            (beside / drawings).mkdir(exist_ok=True)
        except Exception as error:
            print("could not write " + args.out + ": " + str(error), file=sys.stderr)
            return 2
        # Which dishes still need a drawing, so a list made again is not a
        # reason to draw again: have only where the page's test of one photo
        # passes, and draw for the rest -- an empty, wrong-kind or oversized file
        # included. A file that is there and still draw says why, on stderr, so
        # the host fixes what was wrong rather than drawing the same file again.
        name = Path(args.out).name
        for title, _ in titles:
            try:
                usable, problem = read_photo(beside, listing[title], name)
                present = (beside / listing[title]).exists()
            except Exception as error:
                usable, problem, present = None, listing[title] + ": " + str(error), True
            shown = " ".join(title.split()).encode("utf-8", "replace").decode("utf-8")
            print(("have " if usable is not None else "draw ") + listing[title] + " " + shown)
            if usable is None and present:
                print("the file at " + problem, file=sys.stderr)
        print("wrote " + args.out + " listing " + str(len(titles)) + " dishes")
        return 0
    if args.photos is None:
        print("wrote " + args.out)
        return 0
    for warning in warnings:
        print(warning, file=sys.stderr)
    print(
        "wrote " + args.out + " with photos of " + str(len(photos)) + " of "
        + str(len(titles)) + " dishes"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
