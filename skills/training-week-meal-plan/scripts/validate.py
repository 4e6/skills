#!/usr/bin/env python3
"""The plan checks, as code rather than as prompt instructions.

A plan that tells somebody to cook four portions and eat two is worse than no
plan at all, and asking a model to check its own arithmetic lands somewhere
around 95% reliable. That is fine when a person reads every plan and not fine
when nobody does. So these checks are code.

    python3 scripts/validate.py plan.json            0 clean, 1 findings, 2 could not validate
    python3 scripts/validate.py plan.json --json     the findings as JSON

Exit 0 prints a line saying so, rather than staying silent: a silent success and
a crash are indistinguishable to anything reading output rather than status.

Exit 2 means the check could not read the document at all. It carries a message
and never a finding code, because a code would be a claim about the plan and
this is a statement about the checker.

Python 3.9, standard library only, no network, no writes. It reads one file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

DAY_ABBRS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

MEAL_NAMES = ["Breakfast", "Lunch", "Dinner"]

DAY_INDEX = {name: i for i, name in enumerate(DAY_NAMES)}
DAY_ABBR_OF = dict(zip(DAY_NAMES, DAY_ABBRS))
DAY_OF_ABBR = dict(zip(DAY_ABBRS, DAY_NAMES))

SLOT_TO_MEAL = {"breakfast": "Breakfast", "lunch": "Lunch", "dinner": "Dinner"}

# How many days a cooked portion may wait before it is eaten.
MAX_LEFTOVER_DAYS = 4

# The macros a serving states, in the order a mismatch reads best.
MACROS = ["kcal", "carbs", "protein", "fat", "fibre"]

# The exact set of characters ECMAScript's string trim removes: its WhiteSpace
# and LineTerminator productions, plus the byte-order mark — a set fixed by a
# published standard rather than by whichever interpreter runs the file.
#
# This is spelled out rather than left to Python's own strip, which does not
# remove the byte-order mark and does remove the four information separators and
# the next-line character. Ingredient identity in the repeat check is keyed on a
# trimmed name, so one invisible byte-order mark inside a name would decide
# whether two repeats list the same thing. No test corpus written in English
# can show that.
JS_WHITESPACE = (
    "\t\n\v\f\r "
    "\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005"
    "\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f"
    "\u205f\u3000\ufeff"
)


def js_trim(text: str) -> str:
    """Trim exactly what ECMAScript trims. See the constant above."""
    return text.strip(JS_WHITESPACE)


# Function words dropped before two names are compared, limited to the ones a
# plan written here could ever contain.
#
# Two names for the same food can order their words differently, and neither
# token set is a subset of the other while the connecting particles are counted.
# Both sides of every comparison are tokenised by the same function, so a word
# dropped here is dropped symmetrically.
#
# The words are the particles of many languages, taken together rather than
# per language. The compatibility field says the plan is written in English, so
# Burmese particles and Korean jamo are not words these plans reach. What is
# kept is every function word whose every letter is Latin, or of the
# script-neutral kinds that punctuation and modifiers belong to. Not ASCII —
# Icelandic með and Azerbaijani və are in, and an ASCII rule would drop them.
# That is the whole rule, and it is mechanical.
#
# Keeping only the English words was the obvious cut and it is the wrong one,
# because English borrows. Tuna in brine, chilli con carne, pasta al dente and
# pico de gallo are English shopping-list names whose middle word belongs to
# another language, and this table drops all four. A table that did not would
# report an unpurchasable ingredient, or a day tag nothing uses, on a correct
# plan — and would miss a day used but untagged, because a name that stops
# matching the prose takes its day out of the set the tag is compared against.
#
# So what is left out is every word that folds to something other than Latin:
# Greek, Cyrillic, Devanagari, Thai, Korean and the rest. Reaching one means
# naming a dish in its own script, which the compatibility field says these
# plans do not do — a promise about the output rather than something the format
# prevents. That is what makes leaving them out cheap rather than free.
#
# One of the entries, s, is not an English word. The list is sorted, so it sits
# in the middle rather than at either end. Do not read that as nobody writing
# it: s is here because six Slavic languages use it as their word for with, and
# because an apostrophe is a token boundary, so a shopping item named
# Shepherd's pie leaves a bare s behind and has to go on matching prose that
# writes it shepherds pie. Deleting it as an artefact would take both with it.
# The list is not grouped by language, which is why the point is spelled out.
#
# The matching bare t from don't is deliberately absent. Dropping a residue
# earns its place by making two spellings of a name agree. Dropping s does:
# Shepherd's pie and shepherds pie both reduce to the same two tokens, because
# the crude singulariser also takes the s off shepherds. Nothing rescues t that
# way — don't reduces to don and dont to dont, which do not meet either way —
# and it costs something instead, by making T-bone steak the same token set as
# Bone-in steak rather than a larger one.
#
# Two more residues are deliberately absent, and adding either would make
# matching worse or no better. Not d: Vitamin D would become
# one token and then match Vitamin C. Not o: O'Brien potatoes is a dish whose
# head is the residue, and OBrien splits to one token anyway, so dropping o
# reconciles no pair of spellings.
#
# That argument does not generalise, and this list must not be read as though it
# did. Nine single letters are in it, one language or another using each as a
# function word. So every Vitamin name that ends in one of the nine reduces to a
# single token, and they all match each other. Keeping d, o and t out buys the
# three letters nobody's function words reach. The wider fault is older than this file
# and is not repaired here, so do not tidy the single letters away.
FUNCTION_WORDS = [
    "a", "aamma", "af", "ah", "ak", "al", "alla", "am", "amb", "amin", "and", "ani",
    "ao", "aos", "ar", "at", "au", "aux", "av", "avec", "az", "bil", "bilan", "bilen",
    "ci", "com", "con", "cu", "da", "dan", "das", "de", "dei", "del", "della", "delle",
    "dem", "den", "dengan", "der", "des", "dhe", "di", "die", "din", "do", "dos", "du",
    "e", "el", "els", "em", "en", "es", "et", "ha", "het", "i", "ile", "ilə", "im",
    "in", "ir", "iyo", "ja", "ka", "ku", "la", "las", "le", "les", "los", "ma", "mal",
    "me", "med", "mei", "met", "með", "mit", "mo", "na", "nan", "ne", "ng", "ni",
    "ning", "no", "och", "od", "of", "og", "op", "or", "oraz", "pa", "s", "sa", "se",
    "si", "so", "su", "sy", "ta", "the", "ti", "u", "un", "und", "v", "va", "van", "ve",
    "vid", "við", "vo", "von", "və", "w", "wa", "wantaim", "we", "wetem", "y", "ya",
    "yang", "z", "za", "ze", "zo", "zum", "zur",
]

# Packaging and preparation words. They belong in a shopping-list entry and
# never in the prose that names the same thing, so they are dropped before
# matching an item against a meal-plan bullet.
QUALIFIERS = {
    "loaf",
    "bag",
    "tin",
    "bottle",
    "jar",
    "pack",
    "tub",
    "box",
    "cube",
    "powder",
    "drink",
    "whole",
    "canned",
    "tinned",
    "jarred",
    "frozen",
    "dry",
    "dried",
    "fresh",
    "mixed",
    "ground",
    "short",
    "slice",
    "piece",
}

IRREGULAR = {
    # Plurals the -s rule gets wrong, and all of them unit words.
    #
    # singular("boxes") is "boxe", which is in no table, so `2 boxes` of cereal
    # was never recognised as a pack. The rest sit under the length guard —
    # three letters or fewer are returned untouched — so `2 kgs` read as a count
    # of an imaginary noun rather than two kilos, dropping the row out of the
    # comparison, and a repair landing on one printed `1 kgs` onto a page. "grs"
    # is the one that is not English at all — it is how Spanish and Portuguese
    # abbreviate grams, and without it 500 grs and 500 gr on two rows of the same
    # plan silently stopped comparing. Every abbreviation in the unit tables that
    # survives pluralisation is here; the long forms the -s rule already
    # handles.
    "boxes": "box",
    "cls": "cl",
    "dls": "dl",
    "grs": "gr",
    "kgs": "kg",
    "lbs": "lb",
    "mgs": "mg",
    "mls": "ml",
    "ozs": "oz",
    "qts": "qt",
    "gals": "gal",
    "leaves": "leaf",
    "loaves": "loaf",
    "potatoes": "potato",
    "tomatoes": "tomato",
    "berries": "berry",
}

ALL_DIGITS = re.compile("[0-9]+")

SCOPED_BASE = ("LATIN ", "GREEK ", "CYRILLIC ")


def _is_scoped_base(ch: str) -> bool:
    """Whether a combining mark after this character is decoration.

    Scoped by the character's Unicode name, because the standard library has no
    Script property. That approximates the script rather than equalling it: the
    two disagree on 271 assigned characters in the basic plane, all of them
    fullwidth Latin, Roman numerals, ordinal indicators, superscript or modifier
    letters, or combining Cyrillic letters — none of them a letter a food name
    is written with.
    """
    try:
        return unicodedata.name(ch).startswith(SCOPED_BASE)
    except ValueError:
        return False


def fold_for_matching(text: str) -> str:
    """Lower-cased, and stripped of the marks that are decoration.

    Lower-case first, then decompose.

    Marks are dropped only over Latin, Greek and Cyrillic. Stripping every
    combining mark would fold a voiced Japanese syllable onto its unvoiced one,
    and every Devanagari vowel sign off its consonant. Those are not the same
    words with the decoration taken off; they are different words.
    """
    out = []
    decorated = False
    for ch in unicodedata.normalize("NFD", text.lower()):
        if unicodedata.category(ch)[0] == "M":
            if decorated:
                continue
            out.append(ch)
            continue
        decorated = _is_scoped_base(ch)
        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))


# What tokenising actually consults.
#
# Folded the same way the tokens are. A stopword is looked up with a folded
# token, so it has to be stored folded: one stored as written can only match if
# it survives folding unchanged. The words above are stored folded
# already, so none of them changes here. Folding anyway is what keeps the rule
# true for a word added by hand later, which is the case that went wrong before.
STOPWORDS = {fold_for_matching(word) for word in FUNCTION_WORDS}


def _utf16_length(word: str) -> int:
    """Length in UTF-16 code units, the unit the thresholds below are set in.

    Python counts code points. The two differ above the basic plane, and the
    length tests below are thresholds, so counting the other way would move them
    silently on any name carrying an astral character.
    """
    return sum(2 if ord(ch) > 0xFFFF else 1 for ch in word)


def singular(word: str) -> str:
    irregular = IRREGULAR.get(word)
    if irregular:
        return irregular
    if word.endswith("ies") and _utf16_length(word) > 4:
        return word[:-3] + "y"
    if word.endswith("ss") or _utf16_length(word) <= 3:
        return word
    if word.endswith("s"):
        return word[:-1]
    return word


def _split_on_non_word(text: str) -> list:
    """Split on anything that is not a letter, a digit or a combining mark.

    Character-wise rather than by regular expression, because this Python has
    neither a script nor a general-category class in its regex engine. A run of
    separators yields an empty string here where a regex would collapse it;
    tokenising skips empty words, so that costs nothing.

    A combining mark belongs in the word, not between words: a Devanagari vowel
    sign and a Thai tone mark are marks, and splitting on them shreds the word.
    """
    parts = []
    current = []
    for ch in text:
        if unicodedata.category(ch)[0] in ("L", "N", "M"):
            current.append(ch)
        else:
            parts.append("".join(current))
            current = []
    parts.append("".join(current))
    return parts


def tokenize(name: str) -> set:
    """A food name reduced to comparable tokens.

    Accents stripped, lower-cased, split on punctuation, crudely singularised,
    so that two orderings of the same words become the same set.

    There is no word segmenter here, so a script that puts no space between
    words stays one token. That is a bounded limitation: the generous
    subset-either-way rule below degenerates to string equality for Japanese,
    Chinese, Thai, Lao, Khmer and Burmese. The plan is written in English.

    The table of function words consulted here holds only words written in Latin
    script, so a name carrying a function word from another script keeps it as a
    token and stops matching. That would report an ingredient as unpurchasable,
    or a day tag as unused, on a correct plan — and miss a day that is used but
    untagged. The first is the one a reader hits soonest, because a larger token
    set breaks name matching before it breaks the prose test.

    What is left out is the words of scripts these plans are not written in — a
    promise about the output rather than something the format prevents.

    The all-digits test uses an explicit zero-to-nine range. Python's digit
    class also matches Devanagari and Arabic-Indic digits, and whether such a
    token is dropped is a difference no English corpus can show.
    """
    tokens = set()
    for word in _split_on_non_word(fold_for_matching(name)):
        if not word or word in STOPWORDS or ALL_DIGITS.fullmatch(word):
            continue
        tokens.add(singular(word))
    return tokens


def is_subset(a: set, b: set) -> bool:
    return a <= b


def same_set(a: set, b: set) -> bool:
    return a == b


def symmetric_size(a: set, b: set) -> int:
    return len(a - b) + len(b - a)


def without(a: set, drop: set) -> set:
    return a - drop


def is_strict_subset(a: set, b: set) -> bool:
    return a < b


def names_match(a: str, b: str) -> bool:
    """Whether two food names plausibly denote the same thing.

    Subset either way counts, so a bare name matches a qualified one. That
    generosity is deliberate and has a known cost: a bare name also matches a
    more specific dish built on it. Deciding those needs a model; failing a good
    plan is worse than missing a marginal one.
    """
    ta = tokenize(a)
    tb = tokenize(b)
    if not ta or not tb:
        return False
    return is_subset(ta, tb) or is_subset(tb, ta)


def best_matches(name: str, candidates: list) -> list:
    """The candidates that match a name most closely.

    An exact token-set match beats a subset one, and among subsets the smallest
    difference wins. Without this, a bare name resolves to itself and to every
    dish built on it, which is how a shopping item ends up tagged with a day
    that never touches it.

    Ties are returned whole: two equally good candidates are genuinely
    ambiguous, and guessing between them is the model's job.
    """
    tokens = tokenize(name)
    if not tokens:
        return []
    scored = []
    for candidate in candidates:
        other = tokenize(candidate)
        if not other:
            continue
        if same_set(tokens, other):
            scored.append((0, candidate))
        elif is_subset(tokens, other) or is_subset(other, tokens):
            scored.append((1 + symmetric_size(tokens, other), candidate))
    if not scored:
        return []
    best = min(score for score, _ in scored)
    return [candidate for score, candidate in scored if score == best]


# What separates a food from how it differs: `Eggs, large`, `Eggs (large)`.
# The ideographic and Arabic commas and the full-width parenthesis too, so a
# plan in Japanese or Arabic has the same form; the exact name works whatever
# the separator.
COMMAS = re.compile("[,\uff0c\u3001\u060c(\uff08]")


def head_tokens(name: str) -> set:
    """The food a name names: the tokens before the first comma, less the words
    QUALIFIERS already treats as how a food is sold or kept, so frozen berries
    are berries. A head that is nothing but those words is kept whole.
    """
    head = tokenize(COMMAS.split(name, 1)[0])
    food = without(head, QUALIFIERS)
    return food if food else head


def fridge_rows(name: str, shopping_names: list) -> list:
    """The shopping rows a fridge entry answers: the food it is, not a word it
    shares.

    best_matches reads a strict superset as a more specific spelling of the
    same food, which is right for `Eggs, large` against `Eggs` and wrong for
    `Peanut butter` against `Butter`. Telling a qualifier from a food by its
    words needs a vocabulary in every language, so this reads the comma the
    plan's own naming puts there instead.

    An entry answers a row when the two names are the same set of words, or
    when the text before the first comma is the same food and one whole name is
    contained in the other, the closest of those as best_matches ranks them.
    Without the containment clause `Berries, goji` answers `Berries, frozen`;
    with it, this only ever answers pairs names_match accepts. An exact match
    beats any head match and a tie is returned whole. Anything else answers no
    row: it is a food of its own, and that includes a qualifier written after
    the food with no comma, `Huevos grandes` against `Huevos`.
    """
    tokens = tokenize(name)
    if not tokens:
        return []
    head = head_tokens(name)
    exact = []
    by_head = []
    for row in shopping_names:
        other = tokenize(row)
        if not other:
            continue
        if same_set(tokens, other):
            exact.append(row)
        elif (
            head
            and same_set(head, head_tokens(row))
            and (is_subset(tokens, other) or is_subset(other, tokens))
        ):
            by_head.append((symmetric_size(tokens, other), row))
    if exact or not by_head:
        return exact
    best = min(distance for distance, _ in by_head)
    return [row for distance, row in by_head if distance == best]


def line_rows(item: str, shopping_names: list, fridge_names: list) -> list:
    """The shopping rows a recipe line draws on, read against the list and the
    fridge together.

    Against the list alone a `Peanut butter` line had nowhere to land but
    `Butter`. With the fridge's names beside it, best_matches prefers the exact
    spelling, and a fridge-only hit is handed to whichever row fridge_rows says
    that entry answers, or to none. Deduplicated, since a line can tie between
    a row and a fridge entry answering that same row.
    """
    on_the_list = set(shopping_names)
    candidates = list(dict.fromkeys(list(shopping_names) + list(fridge_names)))
    rows = []
    for hit in best_matches(item, candidates):
        found = [hit] if hit in on_the_list else fridge_rows(hit, shopping_names)
        for row in found:
            if row not in rows:
                rows.append(row)
    return rows


def mentions(text: str, name: str) -> bool:
    """Whether free prose names an item, for a side no recipe lists.

    Qualifiers are dropped first: a shopping entry naming a packaged form and a
    bullet naming the food are the same food.
    """
    tokens = without(tokenize(name), QUALIFIERS)
    if not tokens:
        return False
    return is_subset(tokens, tokenize(text))


def slot_key(day: str, meal: str) -> str:
    return day + " " + meal


# Where to order a day name that is not one of the seven: after all of them.
#
# Such a name has no place in the week, so any position given it is arbitrary.
# This is used only where every finding is reported anyway and the sort decides
# the order they are listed in. Where the sort's *outcome* is the finding, the
# check is skipped instead: see the day-tag check below.
UNKNOWN_DAY = len(DAY_NAMES)


def day_position(name) -> int:
    return DAY_INDEX.get(name, UNKNOWN_DAY)


# What a message prints for a property that is simply not there, which is a
# different value from one explicitly set to null and prints differently. Both
# are reachable only through a document the published schema forbids, and a
# message prints both rather than failing on either.
MISSING = "undefined"


def rendered(value) -> str:
    """A JSON value as a message prints it: JSON's spelling, not Python's.

    Three cases where Python's own spelling would mislead.

    None becomes the four letters n, u, l, l, as JSON writes it. An empty
    string would read as a day excluded for no reason, which is a different
    fault with a different repair. Booleans lower-case for the same reason.

    And a float that is a whole number loses its trailing zero. JSON has one
    numeric type, so a document written with a decimal point is the same number
    as one without. Here it survives parsing as a float and would print an extra
    two characters into the message — on a document the schema accepts, since a
    whole-numbered float is an integer to anything checking that.
    """
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def is_excluded(obj: dict) -> bool:
    """Whether a day or a meal is excluded.

    The presence of the field is the marker, never its truthiness: an empty
    reason is excluded-with-no-reason, which is a different fault and must not
    silently un-exclude the day.
    """
    return "excluded" in obj


def main_meals(day: dict) -> dict:
    out = {}
    for meal in day["meals"]:
        name = SLOT_TO_MEAL.get(meal["slot"])
        if name and name not in out:
            out[name] = meal
    return out


def recipes_by_slot(plan: dict) -> dict:
    """Every recipe entry at each (day, meal), in plan order: a meal is a list
    of dishes, so a slot holds one entry per dish."""
    out = {}
    for recipe in plan["recipes"]:
        key = slot_key(recipe["day"], recipe["meal"])
        out.setdefault(key, []).append(recipe)
    return out


def dishes_of(meal: dict) -> list:
    """Every dish a meal names, the main first."""
    main = [meal["dish"]] if meal.get("dish") else []
    return main + list(meal.get("alongside") or [])


def origins_by_title(plan: dict) -> dict:
    out = {}
    for recipe in plan["recipes"]:
        if recipe["kind"] == "origin" and recipe["title"] not in out:
            out[recipe["title"]] = recipe
    return out


def origin_of(plan: dict, recipe: dict):
    """The entry carrying this dish's recipe: itself, or the origin it points at."""
    if recipe["kind"] == "origin":
        return recipe
    for r in plan["recipes"]:
        if r["kind"] == "origin" and r["title"] == recipe["title"] and r["day"] == recipe.get("origin_day"):
            return r
    return None


def portions_at(recipe: dict) -> float:
    """How many reference portions one entry's plates add up to: one where it
    states none, which on a plan for one person is the athlete's one bowl."""
    plates = recipe.get("plates")
    if not plates:
        return 1.0
    return float(sum(p["portions"] for p in plates))


def batch_portions(plan: dict, recipe: dict) -> float:
    """How many reference portions this entry's pot holds: an origin cooks for
    every sitting in its servings, a repeat for its own, and a leftover eats out
    of its origin's."""
    if recipe["kind"] == "repeat":
        return portions_at(recipe)
    origin = origin_of(plan, recipe)
    if origin is None:
        return 0.0
    servings = origin.get("servings")
    if servings is None:
        servings = [{"day": origin["day"], "meal": origin["meal"]}]
    total = 0.0
    for slot in servings:
        for r in plan["recipes"]:
            if r["day"] == slot["day"] and r["meal"] == slot["meal"] and r["title"] == origin["title"]:
                total += portions_at(r)
                break
    return total


def batch_factor(plan: dict, recipe: dict):
    """The pot over what the origin's list is written for, or None where there
    is no list to scale."""
    origin = origin_of(plan, recipe)
    if origin is None or not origin.get("yields"):
        return None
    return batch_portions(plan, recipe) / origin["yields"]


def ingredient_day_index(plan: dict) -> dict:
    """Which days actually use each ingredient, read off written recipes.

    Never inferred from a dish's name: what matters is what its recipe lists.

    A day that cooks the dish again counts, because it needs the ingredients
    again and carries no ingredient block only because it points at the first
    day's. A day that eats a portion cooked earlier does not: that ingredient
    was bought and used on the cooking day.
    """
    origins = origins_by_title(plan)
    index = {}
    for recipe in plan["recipes"]:
        if recipe["kind"] == "leftover":
            continue
        source = recipe if recipe["kind"] == "origin" else origins.get(recipe["title"])
        if not source:
            continue
        for ingredient in source.get("ingredients") or []:
            index.setdefault(ingredient["item"], set()).add(recipe["day"])
    return index


def items_named_in(text: str, item_names: list) -> set:
    """Which shopping items a day's prose names, keeping only the specific ones.

    A specific name in a bullet matches both itself and the bare food on the
    list. Only the more specific one is really named, so any item whose tokens
    are a strict subset of another match is dropped.
    """
    hits = {}
    for name in item_names:
        if mentions(text, name):
            hits[name] = without(tokenize(name), QUALIFIERS)
    out = set()
    for name, tokens in hits.items():
        eclipsed = any(
            other != name and is_strict_subset(tokens, other_tokens)
            for other, other_tokens in hits.items()
        )
        if not eclipsed:
            out.add(name)
    return out


def day_prose(plan: dict) -> dict:
    """A day's prose: every meal's `note` and `extra`, and nothing else.

    The schema has no `extra` now — bread served with a dish is in its recipe —
    but a plan written before that may carry one, and there `with sourdough`
    beside a dinner is what tags the bread that day. `note` is read whole, because
    `cook 2 — eat 1` is one statement and not two halves. A session's fuel lines
    are never read: their food is an example, not a purchase.
    """
    out = {}
    for day in plan["days"]:
        parts = []
        for meal in day["meals"]:
            parts.append(meal.get("note") or "")
            parts.append(meal.get("extra") or "")
        out[day["name"]] = " ".join(part for part in parts if part)
    return out


def finding(check: int, code: str, message: str, where: str = "") -> dict:
    """One thing wrong with a plan.

    The location is a path into the plan document and the message names the
    specific fix, because a repair is targeted rather than a regeneration.
    """
    return {"check": check, "code": code, "message": message, "where": where}


def expected_run(plan: dict) -> list:
    """The run of days this plan should be.

    The earliest day it names up to its first Sunday, through to Sunday: a gap is
    a day to put back, days out of order before that Sunday are days to
    reorder, and days after it are the next week's, one too many. A Sunday
    written first is no bound. An empty list is an empty run, and names outside
    the seven count only towards the length.
    """
    names = [day["name"] for day in plan["days"]]
    sunday = names.index("Sunday") if "Sunday" in names else -1
    scope = names[: sunday + 1] if sunday > 0 else names
    known = [n for n in scope if isinstance(n, str) and n in DAY_INDEX]
    if not known:
        return DAY_NAMES[len(DAY_NAMES) - min(len(names), len(DAY_NAMES)):]
    return DAY_NAMES[min(DAY_INDEX[n] for n in known):]


def outside_the_run(plan: dict):
    """Whether a day is one of the seven and outside the expected run.

    Only asked once the days are right: a plan whose days are wrong hears the
    day-order finding and nothing else, so wherever this is asked the plan's
    days are the run.
    """
    run = set(expected_run(plan))

    def outside(day) -> bool:
        return isinstance(day, str) and day in DAY_INDEX and day not in run

    return outside


def check_day_meal_completeness(plan: dict) -> list:
    """The structural faults that every other check depends on.

    The days not being a run that ends on Sunday, every day being excluded, a
    main meal missing altogether, and a meal naming a dish no recipe at its
    sitting has, or a recipe there no dish names. The portion ledger skips a
    slot that has no recipe, and check 10 a day whose meals and recipes do not
    line up, on the grounds that this check already reported it, so without
    these the fault would be reported by nothing at all.

    Then the recipes that sit where the plan cannot reach them: one entered on
    a day the plan does not cover, and a pointer at nothing, at the wrong day,
    or at a day that is not earlier. A plan that starts mid-week is where those
    arrive — Friday's leftover of a Wednesday chilli nobody cooked — and the
    ledger balances every one of them.

    The rest are deliberately absent, with four exceptions that arrived when a
    plate became a number of portions. An origin with no `nutrition` or no
    `yields`, a pointer with figures of its own, and a repeat with a list of
    its own each leave the page nothing sound to multiply, and without them
    here the checker would pass a plan clean while the page printed the wrong
    pot.
    """
    findings = []
    names = [day["name"] for day in plan["days"]]
    # An empty list expects an empty run, which `week-entirely-excluded`
    # below then reports.
    expected = expected_run(plan)

    if ",".join(names) != ",".join(expected):
        want = ", ".join(expected)
        got = ", ".join(names)
        return [finding(3, "day-order", "days must be " + want + ", got " + got, "days")]

    if all(is_excluded(day) for day in plan["days"]):
        findings.append(
            finding(
                3, "week-entirely-excluded", "every day is excluded; there is no week to plan", "days"
            )
        )

    meals_present = {}
    for day in plan["days"]:
        if is_excluded(day):
            continue
        meals_present[day["name"]] = main_meals(day)

    for day in plan["days"]:
        if is_excluded(day):
            continue
        meals = meals_present[day["name"]]
        for meal_name in MEAL_NAMES:
            if meal_name not in meals:
                where = "days." + day["name"] + "." + meal_name
                lowered = meal_name.lower()
                findings.append(
                    finding(3, "missing-meal", day["name"] + " has no " + lowered, where)
                )

    # Each dish a meal names against the entries at its sitting, by title and
    # exactly, since that is how the page links a meal to its method. Without
    # this the page names one breakfast while the recipe and the list cook
    # another, and check 10 drops the day without a word, because it compares
    # only days whose meals and recipes line up and leaves the rest to here.
    by_slot = recipes_by_slot(plan)
    for day in plan["days"]:
        if is_excluded(day):
            continue
        meals = meals_present[day["name"]]
        for meal_name in MEAL_NAMES:
            meal = meals.get(meal_name)
            if meal is None or is_excluded(meal):
                continue
            sitting = day["name"] + " " + meal_name.lower()
            dishes = dishes_of(meal)
            titles = [r["title"] for r in by_slot.get(slot_key(day["name"], meal_name)) or []]
            unnamed = [t for i, t in enumerate(titles) if t not in dishes and titles.index(t) == i]
            for dish in dishes:
                if dish in titles:
                    continue
                if unnamed:
                    repair = (
                        "; the entry there that no dish names is "
                        + ", ".join("'" + rendered(t) + "'" for t in unnamed)
                        + ": if this dish is that recipe, give both one title, and otherwise"
                        + " write this dish's recipe at this sitting"
                    )
                else:
                    repair = (
                        "; write its recipe at this sitting, or, if its recipe is entered"
                        + " under another title, give both one title"
                    )
                findings.append(
                    finding(
                        3,
                        "dish-without-recipe",
                        sitting + " names '" + rendered(dish) + "', which no recipe at that"
                        + " sitting has" + repair,
                        "days." + day["name"] + "." + meal_name,
                    )
                )
            for title in unnamed:
                findings.append(
                    finding(
                        3,
                        "recipe-without-dish",
                        "'" + rendered(title) + "' is entered for " + sitting + ", but that meal"
                        + " names no such dish; name it in the meal's `dish` or `alongside` by"
                        + " this exact title, or, if the meal does not eat it, take the entry out",
                        "recipes." + day["name"] + "." + meal_name,
                    )
                )

    uncovered = outside_the_run(plan)
    origins = origins_by_title(plan)
    for recipe in plan["recipes"]:
        where = "recipes." + recipe["day"] + "." + recipe["meal"]
        title = recipe["title"]
        if uncovered(recipe["day"]):
            findings.append(
                finding(
                    3,
                    "recipe-on-uncovered-day",
                    "'" + title + "' is entered on " + recipe["day"] + ", which this plan does"
                    + " not cover; cook it on a day the plan covers and point any repeat or"
                    + " leftover of it at that day, or, if the athlete said it is already made,"
                    + " list it in `fridge` and give the meal that eats it an entry of its own",
                    where,
                )
            )
        if recipe["kind"] == "origin":
            if not recipe.get("nutrition"):
                findings.append(
                    finding(
                        3,
                        "origin-without-nutrition",
                        "'" + title + "' is an origin entry with no `nutrition`; every plate of"
                        + " this dish is that one reference portion times its `portions`, so it is"
                        + " required here",
                        where,
                    )
                )
            if recipe.get("yields") is None:
                findings.append(
                    finding(
                        3,
                        "origin-without-yields",
                        "'" + title + "' is an origin entry with no `yields`; say how many"
                        + " reference portions its ingredient list makes, so the pot can be sized"
                        + " to the plates it feeds",
                        where,
                    )
                )
            if not recipe.get("ingredients"):
                findings.append(
                    finding(
                        3,
                        "origin-without-ingredients",
                        "'" + title + "' is an origin entry with no `ingredients`; write the"
                        + " list its `yields` portions are cooked from, since every repeat of it"
                        + " and the shopping list are sized from that list",
                        where,
                    )
                )
            continue
        origin_day = recipe.get("origin_day")
        if not origin_day:
            continue
        origin = origins.get(title)
        # A pointer at a day the plan does not cover comes first, because the
        # next branch would invite adding that day back.
        if uncovered(origin_day):
            findings.append(
                finding(
                    3,
                    "pointer-to-uncovered-day",
                    "'" + title + "' on " + recipe["day"] + " points at " + origin_day
                    + ", which this plan does not cover; nothing is cooked before the first"
                    + " day, so cook it on a day the plan covers and point this there, or, if the"
                    + " athlete said it is already made, list it in `fridge` and give this meal an"
                    + " entry of its own",
                    where,
                )
            )
        elif origin is None:
            findings.append(
                finding(
                    3,
                    "pointer-to-nothing",
                    "'" + title + "' points at " + origin_day
                    + " but no day carries the full recipe",
                    where,
                )
            )
        elif origin["day"] != origin_day:
            findings.append(
                finding(
                    3,
                    "pointer-to-wrong-day",
                    "'" + title + "' points at " + origin_day + " but the recipe is on "
                    + origin["day"],
                    where,
                )
            )
        # A day name outside the seven is neither earlier nor later: no
        # finding, and no KeyError either.
        elif (
            origin_day in DAY_INDEX
            and recipe["day"] in DAY_INDEX
            and DAY_INDEX[origin_day] >= DAY_INDEX[recipe["day"]]
        ):
            findings.append(
                finding(
                    3,
                    "pointer-not-earlier",
                    "'" + title + "' on " + recipe["day"] + " points at " + origin_day
                    + ", which is not earlier",
                    where,
                )
            )
        if recipe.get("nutrition"):
            findings.append(
                finding(
                    3,
                    "pointer-with-nutrition",
                    "'" + title + "' on " + recipe["day"] + " is a " + recipe["kind"]
                    + ", so its figures are " + origin_day + "'s reference portion times its"
                    + " `plates`; remove its own `nutrition`",
                    where,
                )
            )
        if recipe["kind"] == "repeat" and recipe.get("ingredients"):
            findings.append(
                finding(
                    3,
                    "repeat-with-ingredients",
                    "'" + title + "' on " + recipe["day"] + " cooks " + origin_day
                    + "'s recipe again; its pot is that list sized to its own `plates`, so it"
                    + " carries no ingredients of its own — a bigger bowl is more `portions`",
                    where,
                )
            )
    return findings


def check_portion_ledger(plan: dict) -> list:
    """Portions cooked equal portions eaten, inside the same week."""
    findings = []
    by_slot = recipes_by_slot(plan)

    # A claim is on one dish at one sitting, (day, meal, title): a meal is a
    # list of dishes, and keyed on the slot alone a main and its side would be
    # two claims on one sitting. A list rather than a set, because a dish
    # claimed twice prints its claimants and the duplication is the fault.
    claimed = {}

    def claim(key: str, title: str, by: str) -> None:
        claimed.setdefault(key + "|" + title, []).append(by)

    for recipe in plan["recipes"]:
        if recipe["kind"] == "repeat":
            # Cooking the dish again feeds that day and consumes nothing from
            # the earlier batch.
            claim(
                slot_key(recipe["day"], recipe["meal"]),
                recipe["title"],
                recipe["day"] + "'s " + recipe["title"],
            )
            continue
        if recipe["kind"] != "origin":
            continue

        where = "recipes." + recipe["day"] + "." + recipe["meal"]
        title = recipe["title"]

        # Absent or null means one serving, eaten where it is cooked. An empty
        # list is kept as an empty list, which is why this is not a truthiness
        # test: only null is coalesced, and the schema that
        # would have made an empty list impossible is not enforced here.
        servings = recipe.get("servings")
        if servings is None:
            servings = [{"day": recipe["day"], "meal": recipe["meal"]}]

        cooked_here = any(
            s["day"] == recipe["day"] and s["meal"] == recipe["meal"] for s in servings
        )
        if not cooked_here:
            lowered = recipe["meal"].lower()
            findings.append(
                finding(
                    4,
                    "cook-day-not-served",
                    "'" + title + "' is cooked on " + recipe["day"] + " for " + lowered
                    + " but that slot is not in its servings",
                    where,
                )
            )

        for slot in servings:
            key = slot_key(slot["day"], slot["meal"])
            claim(key, title, recipe["day"] + "'s " + title)
            lowered = slot["meal"].lower()

            excluded_day = next(
                (d for d in plan["days"] if d["name"] == slot["day"] and is_excluded(d)), None
            )
            if excluded_day:
                # Reported here rather than left to the no-slot fault, which
                # would say the slot does not exist and send the model looking
                # for a missing meal. The slot is absent on purpose; the batch
                # is one portion too big.
                reason = rendered(excluded_day["excluded"])
                findings.append(
                    finding(
                        4,
                        "portion-into-excluded-day",
                        "'" + title + "' cooks a portion for " + slot["day"] + " " + lowered
                        + ", but " + slot["day"] + " is excluded ('" + reason
                        + "'); cook a smaller batch",
                        where,
                    )
                )
                continue

            target_day = next((d for d in plan["days"] if d["name"] == slot["day"]), None)
            target_meal = main_meals(target_day).get(slot["meal"]) if target_day else None
            if target_meal and is_excluded(target_meal):
                # Same shape as the excluded day: the slot is absent on
                # purpose, so pointing at a missing meal sends the wrong way.
                reason = rendered(target_meal["excluded"])
                findings.append(
                    finding(
                        4,
                        "portion-into-excluded-meal",
                        "'" + title + "' cooks a portion for " + slot["day"] + " " + lowered
                        + ", but that meal is eaten elsewhere ('" + reason
                        + "'); cook a smaller batch",
                        where,
                    )
                )
                continue

            eaters = by_slot.get(key) or []
            if not eaters:
                findings.append(
                    finding(
                        4,
                        "portion-with-no-slot",
                        "'" + title + "' cooks a portion for " + slot["day"] + " " + lowered
                        + ", which is not a meal in this plan",
                        where,
                    )
                )
                continue
            if not any(e["title"] == title for e in eaters):
                findings.append(
                    finding(
                        4,
                        "portion-slot-eats-something-else",
                        "'" + title + "' assigns a portion to " + slot["day"] + " " + lowered
                        + ", but that meal is "
                        + ", ".join("'" + e["title"] + "'" for e in eaters),
                        where,
                    )
                )

            # Both positions, or no comparison at all. A day name outside the
            # seven is neither earlier nor later, so neither branch below fires
            # and nothing is emitted. Raising instead would be worse
            # than useless here: the completeness check exists precisely to
            # report that fault, and an exception would stop it being reached.
            here = DAY_INDEX.get(recipe["day"])
            there = DAY_INDEX.get(slot["day"])
            if here is None or there is None:
                continue
            gap = there - here
            if gap < 0:
                findings.append(
                    finding(
                        4,
                        "portion-eaten-before-cooking",
                        "'" + title + "' assigns a portion to " + slot["day"]
                        + ", before it is cooked on " + recipe["day"],
                        where,
                    )
                )
            elif gap > MAX_LEFTOVER_DAYS:
                findings.append(
                    finding(
                        4,
                        "leftover-too-old",
                        "'" + title + "' is cooked " + recipe["day"] + " and eaten "
                        + slot["day"] + ", " + str(gap) + " days later; the limit is "
                        + str(MAX_LEFTOVER_DAYS),
                        where,
                    )
                )

    for day in plan["days"]:
        for meal_name in MEAL_NAMES:
            key = slot_key(day["name"], meal_name)
            where = "days." + day["name"] + "." + meal_name
            lowered = meal_name.lower()
            # Once per dish with an entry here; a slot with no recipe is the
            # completeness check's, and so is one dish entered twice.
            seen = set()
            for eater in by_slot.get(key) or []:
                if eater["title"] in seen:
                    continue
                seen.add(eater["title"])
                owners = claimed.get(key + "|" + eater["title"]) or []
                if not owners:
                    findings.append(
                        finding(
                            4,
                            "meal-with-no-portion",
                            day["name"] + " " + lowered + " eats '" + eater["title"]
                            + "', but no recipe cooks a portion for it",
                            where,
                        )
                    )
                elif len(owners) > 1:
                    findings.append(
                        finding(
                            4,
                            "slot-claimed-twice",
                            day["name"] + " " + lowered + "'s '" + eater["title"]
                            + "' is claimed by " + ", ".join(owners),
                            where,
                        )
                    )
    return findings


def purchasable(plan: dict) -> list:
    """Everything the athlete will have: bought or already in.

    Names only: nothing that reads this needs to know where a name came from.
    """
    out = []
    for group in plan["shopping"]:
        for item in group["items"]:
            out.append(item["name"])
    for item in plan["fridge"]:
        out.append(item["name"])
    return out


def check_ingredient_coverage(plan: dict) -> list:
    """Every ingredient a recipe uses is bought or already in the fridge.

    Recipe to list. This direction catches ingredients used but not bought; it
    structurally cannot see a shopping-list day that nothing uses, which is what
    the day-tag check is for.
    """
    findings = []
    available = purchasable(plan)
    for recipe in plan["recipes"]:
        if recipe["kind"] != "origin":
            continue
        for i, ingredient in enumerate(recipe.get("ingredients") or []):
            if not any(names_match(ingredient["item"], name) for name in available):
                where = (
                    "recipes." + recipe["day"] + "." + recipe["meal"] + ".ingredients[" + str(i) + "]"
                )
                findings.append(
                    finding(
                        1,
                        "ingredient-not-purchasable",
                        "'" + recipe["title"] + "' uses " + ingredient["item"]
                        + ", which is neither on the shopping list nor in the fridge",
                        where,
                    )
                )
    return findings


def days_bought(actual: set, cover, claimed: set) -> tuple:
    """The days a row buys for, given what the fridge covers.

    The fridge is eaten first, from the plan's first day, so the days a row is
    bought for are always a suffix of the days that use it: once the fridge runs
    out, every later day buys. With no fridge entry answering the row, every
    day that uses it. With the coverage known (a set),
    exactly the days after it. With it unknown (None), any non-empty suffix:
    once a day is tagged every later day that uses the row is too, and the last
    one always is. A day outside the seven has no place in the week, so there
    is no suffix to take and every day is demanded. Returns allowed, required.
    """
    if cover is _ABSENT or any(day not in DAY_INDEX for day in actual):
        return set(actual), set(actual)
    if cover is not None:
        rest = set(actual) - cover
        return rest, set(rest)
    using = sorted(actual, key=day_position)
    first = next((i for i, day in enumerate(using) if day in claimed), -1)
    return set(actual), set(using[-1:] if first < 0 else using[first:])


def check_usage_day_tags(plan: dict) -> list:
    """Each shopping item's day tag names exactly the days that use it.

    List to recipe, run as its own pass. This is the only check that can catch a
    tag naming a day that does not use the item, because the coverage check
    never visits an item on a day whose recipe does not list it.

    Items with no day tag are staples and are exempt.

    A day tag is a day that eats what is bought: a day the fridge feeds uses
    the row and buys nothing, so it is not tagged. See days_bought for what
    that demands when the code can and cannot tell how far the fridge reaches.
    """
    findings = []
    index = ingredient_day_index(plan)
    prose = day_prose(plan)
    item_names = [item["name"] for group in plan["shopping"] for item in group["items"]]
    coverage = fridge_coverage(plan)

    # Resolve each ingredient to the shopping item it most plausibly is, so a
    # loose subset match cannot credit a day to the wrong item, nor a fridge
    # food that shares a word with a row. Prose is still read against
    # the list alone: a whole day is one string there, and offered the
    # fridge's names, chocolate milk named beside plain milk eclipses the row.
    fridge_names = [item["name"] for item in plan["fridge"]]
    days_by_item = {}
    for ingredient_name, days in index.items():
        for name in line_rows(ingredient_name, item_names, fridge_names):
            days_by_item.setdefault(name, set()).update(days)

    mentioned = {day: items_named_in(text, item_names) for day, text in prose.items()}
    outside = outside_the_run(plan)

    for group in plan["shopping"]:
        for item in group["items"]:
            tagged = item.get("days") or []
            if not tagged:
                continue
            where = "shopping." + group["category"] + "." + item["name"]

            actual = set(days_by_item.get(item["name"]) or set())
            for day, names in mentioned.items():
                if item["name"] in names:
                    actual.add(day)

            # An abbreviation outside the enum has no position in the week, and
            # giving it one decides the answer: the same three tags would report
            # a fault or not depending only on whether the unrecognised one sits
            # between the two real ones. That is a fact about the sort, not
            # about the document.
            #
            # So this asks the question the athlete actually has, which has an
            # answer either way: **are the days it can recognise in week
            # order?** An unrecognised tag is passed over rather than given a
            # position. A sentinel position would report faults that are not
            # there, and staying silent whenever any tag was unrecognised would
            # suppress ones that are. This errs towards saying something true.
            readable = [abbr for abbr in tagged if abbr in DAY_OF_ABBR]
            ordered = sorted(readable, key=lambda abbr: DAY_INDEX[DAY_OF_ABBR[abbr]])
            if ",".join(readable) != ",".join(ordered):
                findings.append(
                    finding(
                        2,
                        "days-out-of-order",
                        item["name"] + " tags " + ", ".join(tagged)
                        + "; days are listed in week order",
                        where,
                    )
                )

            claimed = {DAY_OF_ABBR[abbr] for abbr in tagged if abbr in DAY_OF_ABBR}
            cover = coverage.get(item["name"], _ABSENT)
            allowed, required = days_bought(actual, cover, claimed)

            # Sorted into week order before it reaches a message. Python set
            # iteration order is arbitrary, so any set that becomes output is
            # sorted first; only membership tests read one unordered.
            for day in sorted(claimed - allowed, key=day_position):
                abbr = DAY_ABBR_OF.get(day, MISSING)
                # A day the fridge feeds is used, so "nothing uses it" would be
                # false. Say what is true: the fridge pays for that day, and
                # where it pays for every day the row has nothing to buy.
                fed = isinstance(cover, set) and day in cover
                if not fed:
                    message = item["name"] + " is tagged " + abbr + ", but nothing on " + day + " uses it"
                elif allowed:
                    message = (
                        item["name"] + " is tagged " + abbr + ", but what " + day
                        + " uses of it comes out of the fridge, which is eaten first"
                        + " — tag only the days that eat what is bought"
                    )
                else:
                    message = (
                        item["name"] + " is tagged " + abbr
                        + ", but the fridge covers every day that uses it"
                        + " — nothing needs buying, so take " + item["name"]
                        + " off the list"
                    )
                findings.append(finding(2, "day-tagged-but-unused", message, where))
            # A day of the seven the plan does not cover is the completeness
            # check's `recipe-on-uncovered-day`, which says to move the dish.
            uncovered = {d for d in actual if outside(d)}
            for day in sorted(required - claimed - uncovered, key=day_position):
                findings.append(
                    finding(
                        2,
                        "day-used-but-untagged",
                        day + " uses " + item["name"] + " but the tag does not list "
                        + DAY_ABBR_OF.get(day, MISSING),
                        where,
                    )
                )
    return findings



# ------------------------------------------------------------------- check 6

# Mass and volume, each normalised to one unit.
#
# Symbols rather than words, because a plan may be written in any language and
# kg is kg in every one of them that weighs in kilos. The spelled-out English
# forms are here because an English plan writes them.
MASS_UNITS = {
    "mg": 0.001,
    "g": 1,
    "gr": 1,
    "gram": 1,
    "gramme": 1,
    "kg": 1000,
    "kilo": 1000,
    "kilogram": 1000,
    "oz": 28.349523125,
    "ounce": 28.349523125,
    "lb": 453.59237,
    "lbs": 453.59237,
    "pound": 453.59237,
}

VOLUME_UNITS = {
    "ml": 1,
    "millilitre": 1,
    "milliliter": 1,
    "cl": 10,
    "dl": 100,
    "l": 1000,
    "litre": 1000,
    "liter": 1000,
    # US customary, which a plan for the United States, Liberia or Myanmar
    # writes. Without them a week measured in cups and bought by the quart was
    # never added up: each was a counting noun the other did not share. The
    # fluid ounce is not here and cannot be — `fl oz` is two words where a
    # quantity takes one, and a bare `oz` is the weight above — so the skill
    # keeps it off every line this reads. The pint and the quart are the US ones;
    # a British pint is a fifth bigger, and the skill keeps pints off a metric
    # plan for that reason.
    "cup": 236.5882365,
    "pint": 473.176473,
    "quart": 946.352946,
    "qt": 946.352946,
    "gallon": 3785.411784,
    "gal": 3785.411784,
}

# Measures a cook pours rather than weighs. They are compared as volumes and
# multiplied as spoons are, to the half: a pot of one and a third cups is
# `1½ cups`, where the hundredth the litre takes would print `1.34 cups`.
COOKS_MEASURES = {"cup", "pint", "quart", "qt", "gallon", "gal"}

# The fractions a quantity is written with, vulgar and typed.
FRACTIONS = {
    "½": 0.5,
    "⅓": 1 / 3,
    "⅔": 2 / 3,
    "¼": 0.25,
    "¾": 0.75,
    "⅕": 0.2,
    "⅙": 1 / 6,
    "⅛": 0.125,
    "⅜": 0.375,
    "⅝": 0.625,
    "⅞": 0.875,
}

# Digits, spacing and the decimal comma, spelled out rather than left to this
# engine's classes.
#
# The digit class is the ten ASCII ones and the space class is exactly the
# characters trimmed above; this engine's `\d` also matches an Arabic-Indic
# three and its `\s` does not match a byte-order mark. Either would be a
# quantity read or missed on a document nobody would think to write a test for.
_SPACE = "[" + re.escape(JS_WHITESPACE) + "]"
QUANTITY = re.compile(
    "^([0-9]+(?:[.,][0-9]+)?)?"
    + _SPACE
    + "*(["
    + "".join(FRACTIONS)
    + "]|[0-9]/[0-9])?"
    + _SPACE
    + "*(\\w+)?$"
)

AMBIGUOUS_COMMA = re.compile("^[0-9]{1,3},[0-9]{3}$")
PARENTHETICAL = re.compile(r"\([^)]*\)")
# A comma splits the quantity from the knife instruction — but not when it is
# the decimal point, which is what it is in most of the languages a plan may be
# written in. `1,5 kg` is one number; `20 g, roughly chopped` is two things.
NOT_DECIMAL_COMMA = re.compile(",(?![0-9])")


def _all_letters(word: str) -> bool:
    """Whether every character is a letter.

    A unit is letters only, and this engine has no `\\p{L}`. `\\w` is the
    nearest thing it does have and is wider — it admits digits and the
    underscore — so the surplus is taken back off here rather than left to make
    `2 kg2` a quantity.
    """
    return bool(word) and all(unicodedata.category(ch)[0] == "L" for ch in word)


def written_quantity(text: str):
    """The number and unit word a quantity is written with, before conversion.

    Split out of the parser so a finding can answer in the units the row already
    uses. Matched against the raw head rather than the folded one, because the
    word is going back onto a page: folding lower-cases and strips accents, so a
    plan writing `2 Löffel` would be repaired to `2 loffel`.

    Returns a (number, word) pair; the word is None for a bare number.
    """
    # `2 kg (about 16)` is a quantity with a gloss and `20 g, roughly chopped`
    # is a quantity with a knife instruction. In both the quantity is in front.
    head = js_trim(NOT_DECIMAL_COMMA.split(PARENTHETICAL.sub(" ", text))[0])
    if not head:
        return None

    match = QUANTITY.match(head)
    if not match:
        return None
    whole, fraction, word = match.group(1), match.group(2), match.group(3)
    if whole is None and fraction is None:
        return None
    # A unit is letters only, and this engine has no `\p{L}+`, so the pattern
    # above asks for `\w` and the surplus — digits and the underscore — comes
    # off here. It has to come off here rather than only in the caller: the
    # formatter reads this function alone to decide which word a row writes its
    # unit with, so a unit ending in a digit would otherwise reach a row.
    # Unreachable through today's call sites, and this file's whole contract is
    # that it does not matter whether it is reachable.
    if word is not None and not _all_letters(word):
        return None

    number = 0.0
    if whole is not None:
        # A comma is a decimal point in most of the languages a plan may be
        # written in and a thousands separator in the rest. Exactly three digits
        # after it is the only shape that can be a group, so that shape is the
        # only one read as one.
        # A comma is a decimal point — and where it might not be, nothing is
        # read at all. `1,250` is a litre and a quarter in most of the
        # eighty-eight languages and twelve hundred and fifty in the rest, and
        # guessing was wrong in both directions: read as a group it made a
        # correct Portuguese row look 1000x too big, and read as a decimal it
        # made an English ingredient of `1,000 g` look like one gram — which
        # produced a converging repair, so the plan shipped telling the athlete
        # to buy a gram of pasta. There is no reading of that shape this file is
        # entitled to, so it refuses it and the item goes unchecked.
        if AMBIGUOUS_COMMA.match(whole):
            return None
        number += float(whole.replace(",", "."))
    if fraction is not None:
        if fraction in FRACTIONS:
            number += FRACTIONS[fraction]
        else:
            top, bottom = fraction.split("/")
            if float(bottom) == 0:
                return None
            number += float(top) / float(bottom)
    return (number, word)


def parse_amount(text: str):
    """`600 g`, `1½ tins`, `4` — or None.

    Deliberately narrow. Once a parenthetical gloss and a trailing preparation
    clause are off it, what is left has to be a number and at most one unit
    word, so `90 g dry per serving` parses to nothing rather than to 90: it is a
    per-serving figure wearing a batch quantity's clothes, and reading it as 90
    would invent a shortfall on a plan that is fine. Everything unreadable skips
    its item, which is the safe direction.

    Returns a (value, unit) pair. The unit is grams for anything weighed,
    millilitres for anything measured, and otherwise the counting noun itself —
    a tin, a bunch, or the empty string for a bare number. Counting nouns are compared as
    strings and never interpreted, which is the only way the sum can work in a
    language nothing here speaks.
    """
    written = written_quantity(text)
    if written is None:
        return None
    value, word = written
    if word is not None and not _all_letters(word):
        return None

    if word is None:
        return (value, "")
    noun = singular(fold_for_matching(word))
    if noun in MASS_UNITS:
        return (value * MASS_UNITS[noun], "g")
    if noun in VOLUME_UNITS:
        return (value * VOLUME_UNITS[noun], "ml")
    return (value, noun)


def format_amount(amount) -> str:
    """`750 g`, `2.5 tin`, `4`. Rounded, because 0.1 + 0.2 is not 0.3.

    Rounded half **up**, which is not what this language's built-in round does:
    it rounds half to even, so a quantity landing exactly on a half would go
    down as often as up. Every value reaching here is positive, so adding a half
    and truncating is the whole of it.
    """
    value, unit = amount
    rounded = int(value * 1000 + 0.5) / 1000
    return rendered(rounded) + (" " + unit if unit else "")


# Below this two quantities are the same quantity; floats are not exact.
QUANTITY_EPSILON = 0.001

def row_scale(source: str, unit: str):
    """What one of the row's own units is worth, and the word it writes it with."""
    written = written_quantity(source)
    parsed = parse_amount(source)
    if written is None or parsed is None or parsed[1] != unit:
        return None
    number, word = written
    if not number or not parsed[0]:
        return None
    return (parsed[0] / number, word)


def in_row_units(amount, source: str):
    """The amount counted in the row's own units and rounded as it will print.

    None where the row is not able to say it. One function for both the message
    and the comparison, because they have to agree: whatever is printed is what
    the repair hands back, and what comes back is what gets compared.
    """
    scale = row_scale(source, amount[1])
    if scale is None:
        return None
    per_unit, word = scale
    # Three decimals, always with a point: this skill writes English, so its
    # decimal mark is a point.
    rounded = int((amount[0] / per_unit) * 1000 + 0.5) / 1000
    # A row too coarse to hold the answer cannot give it. Three decimals of a
    # kilo is half a gram, so a real need of 0.4 g came back as "the week needs
    # only 0 kg of it", an instruction to buy none of something the week cooks
    # with, spending one of the two repairs there are on advice that is wrong.
    # Saying it in grams is the honest answer.
    if rounded == 0 and amount[0] > QUANTITY_EPSILON:
        return None
    return (rounded, word)


def singular_as_written(word: str) -> str:
    """The word made singular, still spelled the way the row spelled it.

    The singulariser is consulted in lower case because that is how its table is
    keyed — every other caller has already folded — but the answer goes back
    onto a page, so the row's own capitals come with it.
    """
    lower = word.lower()
    one = singular(lower)
    if one == lower:
        return word
    # Only where the singular is a word this file knows. The -s rule cannot tell
    # a plural from a singular that ends in one: German "2 Glas" stemmed to
    # "gla", so a week needing one was repaired to "1 Gla", a non-word, printed.
    # Requiring the stem to be a unit or a container recognises tins, boxes, kgs
    # and lbs, and leaves every word it has no opinion about exactly as the row
    # wrote it. The cost is a foreign plural that stays plural at one, which is
    # a wart where the other is gibberish.
    if one not in MASS_UNITS and one not in VOLUME_UNITS and one not in PACKAGE_NOUNS:
        return word
    if word == word.upper():
        return one.upper()
    if word[:1] == word[:1].upper():
        return one[:1].upper() + one[1:]
    return one


def format_amount_like(amount, source: str) -> str:
    """The amount, re-spelled the way the row itself writes quantities.

    Every one of these numbers is handed to the model as a repair to copy, and
    whatever it copies is printed verbatim. Normalising — grams, millilitres, a
    singularised noun — would tell a plan written in pounds to set 907.185 g and
    repair `2 latas` to `2 lata`, both of which contradict the instruction to
    write in the athlete's own units.

    So the amount is scaled back through the row's own factor and printed with
    the row's own word. Where the row measures something else entirely — a count
    of bags against recipes in grams — there is nothing to scale through and the
    normalised form is what the repair wants anyway.
    """
    # The decimal mark is the plan language's, not the row's, and this skill
    # writes English: a point, including where the need is too small for the
    # row's unit and the answer is given in the canonical one. A row that wrote
    # a comma against that instruction is not echoed.
    in_row = in_row_units(amount, source)
    if in_row is None:
        return format_amount(amount)
    rounded, word = in_row
    number = rendered(rounded)
    if word is None:
        return number
    # The row wrote `3 tins` and the week needs one of them, so carrying its
    # word through unchanged says `1 tins` — onto a page, in a string the model
    # is told to copy. The singulariser is an English-shaped rule and that is
    # the bound: it fires only where the stem is a unit or a container this file
    # knows, and leaves every other word exactly as the row wrote it.
    #
    # It runs in one direction on purpose. A row written `1 tin` whose week
    # needs two is answered `2 tin`, and that is left alone: taking an s off at
    # exactly one is right wherever the distinction exists, while putting one on
    # is a guess about a language this file does not know it is reading. The
    # number is what the repair is for; the model writes the plural.
    return number + " " + (singular_as_written(word) if rounded == 1 else word)


def snap_to_row(amount, source: str):
    """The amount, snapped to what the row is able to write.

    The finding prints the need rounded to three decimals of the row's own unit
    and the model is told to copy that back. Comparing what comes back against
    an unrounded need in grams then never agrees: a thousandth of a pound is
    0.45 g, four hundred times the epsilon. A row of two pounds was answered
    with "set qty to 0.661 lb", and 0.661 lb with the same instruction under the
    opposite code, for ever. With two repairs allowed that is a plan that never
    generates, and only where the units are imperial.

    So the comparison is made against the number the message will name. Metric
    rows are unaffected: a thousandth of a kilo is the gram already allowed.
    """
    in_row = in_row_units(amount, source)
    scale = row_scale(source, amount[1])
    if in_row is None or scale is None:
        return amount
    return (in_row[0] * scale[0], amount[1])


# A shop prices pounds in quarters at most: 1.25 lb, 1.5 lb, 2 lb. A week's total
# is its recipes' ounces added up, and most sums of ounces are no quarter pound,
# so in pounds they come out in sixteenths — 26 oz of rice is `1.625 lb`. The
# repairs below once handed exactly that back to be copied, and so the lists
# copied it. Such a figure is said in ounces, the unit the recipes summed in.
def in_pounds(source: str) -> bool:
    """Is this quantity written in pounds?"""
    written = written_quantity(source)
    if written is None or written[1] is None or not _all_letters(written[1]):
        return False
    return MASS_UNITS.get(singular(fold_for_matching(written[1]))) == MASS_UNITS["lb"]


# How far from a whole quarter a weight may be and still be one, in quarters. A
# row in pounds counts as right within half a thousandth of a pound of the need
# (`snap_to_row`), and a need that close to a quarter is that quarter: calling it
# odd would answer a right `1.25 lb` with `20.006 oz`.
QUARTER_EPSILON = 0.004


def odd_pounds(grams: float) -> bool:
    """Is this weight something other than a whole number of quarter pounds?"""
    quarters = grams / MASS_UNITS["lb"] * 4
    return abs(quarters - round(quarters)) > QUARTER_EPSILON


def in_ounces(grams: float) -> str:
    return rendered(int(grams / MASS_UNITS["oz"] * 1000 + 0.5) / 1000) + " oz"


def pack_in_other_weight(item: dict) -> bool:
    """Is this row's pack a weight written in something other than pounds?"""
    pack = item.get("pack")
    if not isinstance(pack, dict) or not isinstance(pack.get("qty"), str):
        return False
    one = parse_amount(pack["qty"])
    return one is not None and one[1] == "g" and not in_pounds(pack["qty"])


def in_ounces_instead(amount, source: str, item: dict) -> bool:
    """Does a repair to this row in pounds have to say it in ounces?

    Where the figure is no whole quarter, and where the pack is in ounces: the
    page counts packs only where the two are written alike, so handing back
    `1.5 lb` beside a `4 oz` banana is a row it cannot count. A row in pounds
    beside a pack in pounds is counted, and is left in pounds, though the skill
    writes both in ounces.
    """
    return (
        amount[1] == "g"
        and in_pounds(source)
        and (odd_pounds(amount[0]) or pack_in_other_weight(item))
    )


def repair_like(amount, source: str, item: dict) -> str:
    """The amount a repair tells the row to set: in its own unit, or in ounces."""
    if in_ounces_instead(amount, source, item):
        return in_ounces(amount[0])
    return format_amount_like(amount, source)


def pack_in_ounces(item: dict, buy: str) -> str:
    """The rest of a repair that moves a row to ounces while its pack is in pounds.

    The page counts packs only where the row and the pack are written alike, so
    moving the row alone would silently take the count off it.
    """
    # Read only where the schema's shape holds: a pack written as a string, or a
    # number for its quantity, is a fault the schema reports, and it must not
    # take every other finding down with it.
    pack = item.get("pack")
    if not isinstance(pack, dict) or not isinstance(pack.get("qty"), str):
        return ""
    if not buy.endswith(" oz") or not in_pounds(pack["qty"]):
        return ""
    grams = parse_amount(pack["qty"])
    if grams is None:
        return ""
    return ", and pack.qty to " + in_ounces(grams[0]) + " so the page can still count it"


# Measures a list writes as nouns, which this reads as counts and which are not
# what anyone buys: a spoon, a pinch, a length of ginger. A count of them is
# never rounded up to the whole one. The singular here takes an s off and no
# more, so `pinches` reads as `pinche`, and both are listed.
MEASURES = {
    "tablespoon", "tbsp", "teaspoon", "tsp", "pinch", "pinche",
    "dash", "dashe", "cm", "centimetre", "inch", "inche",
}


# Containers, for telling a pack from another way of measuring.
#
# English only, and that is a bounded miss rather than a gap: a list saying
# `1 saco` is caught by the other arm, which reads the gloss — `1 saco (750 g)`
# states its grams in symbols every language shares. What the pair cannot see is
# a packaging word in another language with no gloss beside it, and the cost of
# that is silence, which is the direction this check errs in everywhere else.
PACKAGE_NOUNS = {
    "bag",
    "bottle",
    "box",
    "can",
    "carton",
    "jar",
    "jug",
    "loaf",
    "pack",
    "packet",
    "punnet",
    "sachet",
    "tin",
    "tray",
    "tub",
}

GLOSS = re.compile(r"\(([^)]*)\)")


def gloss_amounts(text: str) -> list:
    """The amounts a parenthetical states — `1 bag (750 g)` says 750 g in passing.

    This is what makes the pack test work in a language this file does not
    speak: the noun is local and the unit symbol is not.
    """
    out = []
    for match in GLOSS.finditer(text):
        amount = parse_amount(match.group(1))
        if amount is not None:
            out.append(amount)
    return out


# Absent from the usage table, as distinct from present and unreadable.
_ABSENT = object()


# The number words a line may start with. No article: `a pinch` read as one
# pinch multiplies into `1½ pinch`, so a line that is not a quantity has to be
# written as one where its pot is multiplied — which is what check 5 is for.
WORD_NUMBERS = [
    (re.compile(r"^(?:a\s+)?half\b\s*(?:an?\b\s*)?", re.IGNORECASE), 0.5),
    (re.compile(r"^(?:a\s+)?quarter\b\s*(?:of\s+)?(?:an?\b\s*)?", re.IGNORECASE), 0.25),
]
LOOSE = re.compile(
    r"^([0-9]+(?:[.,][0-9]+)?)?\s*([½⅓⅔¼¾⅕⅙⅛⅜⅝⅞]|[0-9]/[0-9])?\s*([^\W\d_]+)?(?:\s+(.+))?$"
)
_DIGIT = re.compile(r"[0-9]")


def loose_quantity(text: str):
    """A recipe line's head as a cook writes one: `90 g dry`, `half, sliced`,
    a bare handful. A line is multiplied, never summed by its own text, so the extra
    words ride along. A bare noun is one of it. A second number anywhere is a
    compound — `1 lb 5 oz`, `2 x 200 g` — and is refused rather than
    half-scaled. Returns (number, word, rest, written)."""
    head = js_trim(NOT_DECIMAL_COMMA.split(PARENTHETICAL.sub(" ", text))[0])
    if not head:
        return None
    for pattern, value in WORD_NUMBERS:
        found = pattern.match(head)
        if not found:
            continue
        rest = js_trim(head[found.end():])
        if _DIGIT.search(rest):
            return None
        words = rest.split()
        word = words[0] if words else None
        return (value, word, " ".join(words[1:]), False)
    match = LOOSE.match(head)
    if not match:
        return None
    whole, fraction, word, rest = match.group(1), match.group(2), match.group(3), match.group(4)
    if rest and _DIGIT.search(rest):
        return None
    if whole is None and fraction is None:
        return (1.0, word, "", False) if word and not rest else None
    written = written_quantity((whole or "") + (fraction or ""))
    if written is None:
        return None
    return (written[0], word, rest or "", True)

def _floor(value: float) -> float:
    return float(value // 1)


def _ceil(value: float) -> float:
    return -float((-value) // 1)


def _js_number(value: float) -> str:
    """A number as JSON writes it: a whole float without Python's `.0`."""
    if value == int(value):
        return str(int(value))
    return repr(value)


def _with_halves(value: float, mark: str) -> str:
    whole = int(_floor(value))
    if value - whole < 0.5 - 1e-9:
        text = _js_number(value)
        return text.replace(".", ",") if mark == "," else text
    return str(whole) + "½" if whole else "½"


def scale_line(qty: str, factor: float, mark: str = "."):
    """A recipe line at a pot's size: (text, amount), or None where it cannot
    be multiplied. Exactly 1 is the line as written. Otherwise the words stay
    and the number rounds up — weights and volumes to the whole unit, kilos and
    litres to the hundredth, counts and cups to the half below three and the
    whole from three — because the pot has to hold at least what the plates claim."""
    if factor == 1:
        return (qty, parse_amount(qty))
    loose = loose_quantity(qty)
    if loose is None:
        return None
    number, word, rest, written = loose
    # The tail from the line without its gloss, as the head was: a comma inside
    # `(400 g, drained)` is the gloss's.
    bare = PARENTHETICAL.sub(" ", qty)
    cut = NOT_DECIMAL_COMMA.search(bare)
    tail = bare[cut.start():] if cut else ""
    need = number * factor
    noun = singular(fold_for_matching(word)) if word is not None else None
    mass = MASS_UNITS.get(noun) if noun is not None else None
    volume = VOLUME_UNITS.get(noun) if noun is not None else None
    unit = mass if mass is not None else volume

    def up(v: float, step: float) -> float:
        return _ceil(v / step - 1e-9) * step

    if unit is None or noun in COOKS_MEASURES:
        value = up(need, 0.5) if need < 3 else up(need, 1)
        shown = _with_halves(value, mark)
    elif unit >= 100:
        value = _floor(up(need, 0.01) * 100 + 0.5) / 100
        shown = _js_number(value)
        if mark == ",":
            shown = shown.replace(".", ",")
    else:
        value = up(need, 1)
        shown = _js_number(value)
    words = " ".join(w for w in (word, rest) if w)
    text = (shown + " " + words if words else shown) + tail
    # Only what the row reader could read at the written size adds to a row:
    # a number written as one and a unit with nothing after it.
    if not written or rest:
        return (text, None)
    if mass is not None:
        amount = (value * mass, "g")
    elif volume is not None:
        amount = (value * volume, "ml")
    else:
        amount = (value, noun if noun is not None else "")
    return (text, amount)


def scale_quantity(qty: str, factor: float, mark: str = "."):
    line = scale_line(qty, factor, mark)
    return None if line is None else line[0]


def check_batch_scaling(plan: dict) -> list:
    """Every line a pot is multiplied by can be multiplied — only where it has
    to be: a list printed at the size it was written needs no parsing."""
    findings = []
    said = set()
    for recipe in plan["recipes"]:
        if recipe["kind"] == "leftover":
            continue
        origin = origin_of(plan, recipe)
        factor = batch_factor(plan, recipe)
        if origin is None or factor is None or factor == 1:
            continue
        for i, line in enumerate(origin.get("ingredients") or []):
            if scale_quantity(line["qty"], factor) is not None:
                continue
            key = (origin["title"], i)
            if key in said:
                continue
            said.add(key)
            findings.append(
                finding(
                    5,
                    "ingredient-quantity-unscalable",
                    "'" + origin["title"] + "' lists " + line["item"] + " as '" + line["qty"]
                    + "', and a pot of this dish is cooked at another size than its `yields`"
                    + " — so the line has to be multiplied, and it is not a number and a"
                    + " unit. Write it as one, e.g. '1 tsp'.",
                    "recipes." + origin["day"] + "." + origin["meal"] + ".ingredients[" + str(i) + "]",
                )
            )
    return findings


def ingredient_usage(plan: dict, names: list, shopping_names: list) -> dict:
    """What the week's recipes take of each thing on the list, summed.

    None against a name means do not compare this one: something contributing to
    it could not be read, or an ingredient resolved to two items at once and
    charging both would invent a shortfall in one of them.

    Leftovers take nothing — the food exists already. A repeat takes its own
    quantities where it states them and the origin's where it does not, so a
    bigger Saturday bowl is a bigger Saturday shop.
    """
    origins = origins_by_title(plan)
    usage = {}
    # The day each amount is eaten, index for index with the amounts: the
    # cooking day, so a repeat is its own day and a leftover is none.
    days = {}
    # A sample of how the recipes wrote each name, so the pack finding can
    # answer in the athlete's own units: a row counting bags shares no unit with
    # its recipes, so without this the repair fell back to grams and told a week
    # weighing in ounces to set 453.592 g.
    measured_as = {}

    # A recipe sitting on a day — or in a meal — the athlete said they are away
    # for is the completeness check's finding, which answers *delete it*. Adding
    # its ingredients up meanwhile answers *buy more food for that day*: on a
    # correct away-week with its recipes left in, three rows were told to buy
    # for a day nobody is there.
    # A main meal the week eats but no recipe entry describes is the
    # completeness check's finding, and its ingredients are not in the document
    # to add up: the total silently loses a meal's worth of food and this answers
    # *buy less* while that check answers *write the recipe*.
    by_slot = recipes_by_slot(plan)
    for day in plan["days"]:
        if is_excluded(day):
            continue
        for name, meal in main_meals(day).items():
            if is_excluded(meal):
                continue
            here = by_slot.get(slot_key(day["name"], name)) or []
            if not here:
                return None
            # A side named with no entry of its own loses its food from the
            # total exactly as a whole missing meal does.
            if any(not any(r["title"] == dish for r in here) for dish in dishes_of(meal)):
                return None

    for day in plan["days"]:
        if is_excluded(day) and any(r["day"] == day["name"] for r in plan["recipes"]):
            return None
        for name, meal in main_meals(day).items():
            if not is_excluded(meal):
                continue
            if any(r["day"] == day["name"] and r["meal"] == name for r in plan["recipes"]):
                return None

    # The same shape one step out: a recipe on a day the plan does not cover is
    # the completeness check's `recipe-on-uncovered-day`, and adding it up would
    # tell the list to buy for a day nobody is planning.
    uncovered = outside_the_run(plan)
    if any(uncovered(r["day"]) for r in plan["recipes"]):
        return None

    # A line that ties between a row and a fridge entry answering that same row
    # is one row, as line_rows reads it for the day tags, so the tie is not
    # taken for ambiguity and the row left uncompared.
    on_the_list = set(shopping_names)

    def collapse(matches: list) -> list:
        if len(matches) < 2:
            return matches
        rows = set()
        for m in matches:
            rows.update([m] if m in on_the_list else fridge_rows(m, shopping_names))
        if len(rows) == 1 and next(iter(rows)) in matches:
            return list(rows)
        return matches

    for recipe in plan["recipes"]:
        if recipe["kind"] == "leftover":
            continue
        # An origin with no ingredient block is the completeness check's
        # `origin-without-ingredients`, which answers *write the list*; adding up
        # what is there would answer *buy less* for a forgotten recipe.
        if recipe["kind"] == "origin" and not recipe.get("ingredients"):
            return None
        # A pot is the origin's list at this pot's size, and the code sizes it.
        # A repeat carrying a list of its own, a pointer to nothing, or an
        # origin that does not say what it yields leaves no factor to multiply
        # by, and adding up a guess meanwhile puts a second instruction in the
        # same brief.
        if recipe["kind"] == "repeat" and recipe.get("ingredients"):
            return None
        origin = origin_of(plan, recipe)
        if origin is None or not origin.get("ingredients"):
            return None
        factor = batch_factor(plan, recipe)
        if factor is None:
            return None
        source = []
        for line in origin["ingredients"]:
            scaled = scale_line(line["qty"], factor)
            source.append(
                {
                    "item": line["item"],
                    "qty": None if scaled is None else scaled[0],
                    "amount": None if scaled is None else scaled[1],
                }
            )

        for ingredient in source:
            matches = collapse(best_matches(ingredient["item"], names))
            # An ingredient that resolves to nothing is the coverage check's
            # finding, and it means the week's usage is provably incomplete
            # without saying where. Renaming one potato used to put three
            # instructions in one brief — buy the new name, drop the day tag,
            # and halve the potatoes — of which only the first is right and the
            # third compounds the error. Nothing is comparable until every
            # ingredient lands somewhere, so nothing is compared.
            if not matches:
                return None
            # One ingredient, two plausible items. The coverage check already
            # accepts that ambiguity by name; charging the quantity to both
            # would be a claim.
            if len(matches) > 1:
                for name in matches:
                    usage[name] = None
                continue
            name = matches[0]
            if usage.get(name, _ABSENT) is None:
                continue
            amount = ingredient["amount"]
            if amount is None or ingredient["qty"] is None:
                usage[name] = None
            else:
                usage.setdefault(name, []).append(amount)
                days.setdefault(name, []).append(recipe["day"])
                measured_as.setdefault(name, ingredient["qty"])

    # Fridge names are candidates so that an ingredient spelled the fridge's way
    # resolves somewhere rather than being forced onto a shopping row it only
    # half matches. What they must not do is keep the usage: a fridge entry
    # spelled one degree more specifically took a day's eggs out of the shopping
    # row's total and nothing read them again, so a correct plan was told it had
    # bought twice what it needed.
    #
    # So each fridge-only name hands its usage to the row it answers to, by
    # fridge_rows, so `Eggs, large` hands its eggs to `Eggs` and `Peanut butter`
    # keeps its own, and an ambiguous one takes those rows out of the
    # comparison rather than guessing between them.
    for name, amounts in list(usage.items()):
        if name in on_the_list:
            continue
        del usage[name]
        eaten = days.pop(name, [])
        matched = fridge_rows(name, shopping_names)
        if len(matched) > 1:
            for row in matched:
                usage[row] = None
            continue
        if not matched:
            # In the fridge and on no row: nothing bought, nothing compared.
            continue
        row = matched[0]
        if amounts is None:
            usage[row] = None
        elif usage.get(row, _ABSENT) is not None:
            usage.setdefault(row, []).extend(amounts)
            days.setdefault(row, []).extend(eaten)
        if name in measured_as:
            measured_as.setdefault(row, measured_as[name])
            del measured_as[name]
    return (usage, measured_as, days)


def _rows_named_in_prose(plan: dict, names: list, shopping_names: list) -> set:
    """The rows a day's prose names, which states no amount anybody can add up.

    Read against the fridge's names too, with a fridge-only hit handed to the
    row it answers to: prose saying `a couple of large eggs` resolves to the
    fridge's `Eggs, large` rather than the list's `Eggs`, and without the remap
    the row it exempts is not the row that gets compared.

    The remap stays best_matches rather than fridge_rows, on purpose:
    this is an exemption, so a generous remap errs towards comparing less,
    where the strict one would compare a Milk row on a day whose prose drinks
    plain milk beside a chocolate milk that eclipses it.
    """
    on_the_list = set(shopping_names)
    in_prose = set()
    for text in day_prose(plan).values():
        for name in items_named_in(text, names):
            if name in on_the_list:
                in_prose.add(name)
            else:
                in_prose.update(best_matches(name, shopping_names))
    return in_prose


def _fridge_amounts(plan: dict, shopping_names: list) -> dict:
    """What is already in the fridge, keyed by the shopping row it answers to.

    Resolved by fridge_rows, so a fridge spelled one degree more specifically
    than its row, `Eggs, large`, still counts, and a different food sharing a
    word with a row, `Peanut butter` against `Butter`, is not charged against
    it. None where the amount cannot be used: no quantity, one nobody can read,
    or an entry answering two rows, since taking it off both would invent a
    shortfall. Shared by the quantity check and the fridge coverage, so the
    quantity a row buys and the days it is tagged take the fridge off
    identically.
    """
    in_fridge = {}
    for item in plan["fridge"]:
        amount = parse_amount(item["qty"]) if item.get("qty") else None
        matches = fridge_rows(item["name"], shopping_names)
        if len(matches) > 1:
            for name in matches:
                in_fridge[name] = None
            continue
        if not matches:
            # In the fridge and not on the list: nothing to take anything off.
            continue
        name = matches[0]
        in_fridge[name] = None if name in in_fridge else amount
    return in_fridge


def _row_counts(plan: dict) -> dict:
    """How many rows carry each name, staple or not."""
    rows = {}
    for group in plan["shopping"]:
        for item in group["items"]:
            rows[item["name"]] = rows.get(item["name"], 0) + 1
    return rows


def fridge_coverage(plan: dict) -> dict:
    """Which days the fridge feeds, for each row a fridge entry answers.

    The fridge is eaten first, from the plan's first day: the days are walked
    in week order, each taking its need off what is left, until one needs more
    than is left, and that day and every later one buy. The same subtraction
    the quantity check makes, laid out along the week.

    A row no fridge entry answers is absent. A set, possibly empty, is the days
    the fridge fully feeds, and only when everything bearing on it can be read.
    None means an entry answers the row and the code cannot tell how far it
    reaches, which days_bought bounds rather than demands.
    """
    out = {}
    shopping_names = [item["name"] for group in plan["shopping"] for item in group["items"]]
    in_fridge = _fridge_amounts(plan, shopping_names)
    if not in_fridge:
        return out
    names = list(dict.fromkeys(shopping_names + [item["name"] for item in plan["fridge"]]))
    found = ingredient_usage(plan, names, shopping_names)
    in_prose = _rows_named_in_prose(plan, names, shopping_names)
    rows = _row_counts(plan)
    for name, spare in in_fridge.items():
        taken = None if found is None else found[0].get(name, _ABSENT)
        eaten = [] if found is None else found[2].get(name, [])
        readable = (
            found is not None
            and spare is not None
            and taken is not None
            and name not in in_prose
            and rows.get(name, 0) == 1
        )
        if taken is _ABSENT:
            taken = []
        if (
            not readable
            or any(amount[1] != spare[1] for amount in taken)
            or any(day not in DAY_INDEX for day in eaten)
        ):
            out[name] = None
            continue
        # Summed per day in document order, so both engines add the same
        # floats in the same order and agree at the boundary.
        per_day = {}
        for i, amount in enumerate(taken):
            day = eaten[i]
            per_day[day] = per_day.get(day, 0) + amount[0]
        left = spare[0]
        fed = set()
        for day in sorted(per_day, key=day_position):
            need = per_day[day]
            if need > left + QUANTITY_EPSILON:
                break
            left -= need
            fed.add(day)
        out[name] = fed
    return out


def shopping_quantities(plan: dict) -> dict:
    """What each shopping item is bought at against what the week takes of it.

    An item appears here only when there is something to say about it:
    everything that bears on it parses, no day's prose names it, and it is not a
    staple. Everything else is absent rather than guessed at — this is where
    every deliberate miss of the check below is decided, and the check only
    compares.

    The bought amount may carry a different unit from the need, and that is not
    an oversight: a list counting bags where the recipes weigh grams is the
    defect itself, so it has to survive this far to be reported.
    """
    shopping_names = [item["name"] for group in plan["shopping"] for item in group["items"]]
    names = list(dict.fromkeys(shopping_names + [item["name"] for item in plan["fridge"]]))
    found = ingredient_usage(plan, names, shopping_names)
    # The coverage check has something to say about this plan, and until it is
    # answered nothing here can be trusted to be a whole week.
    if found is None:
        return {}
    usage, measured_as, _ = found

    # A day's prose names what no recipe lists — `with sourdough` beside a
    # dinner — and prose carries no quantity anybody can add up. An item any day
    # names that way is not summable, so it is left alone.
    in_prose = _rows_named_in_prose(plan, names, shopping_names)

    # What is already in the fridge is not bought again, so it comes off what
    # the list has to carry. An entry with no quantity, or one nobody can read,
    # takes its item out of the comparison rather than counting as zero.
    in_fridge = _fridge_amounts(plan, shopping_names)

    # A name on more than one row has no single quantity to compare, and no
    # unambiguous repair either: telling the model to write the week's total
    # against the first row leaves the second one still on the list. Counted
    # over every row, staple or not, because a name split between a dated row
    # and a top-up-if-low one is ambiguous in the same way — and because the
    # finding would otherwise be filed against a row that was never compared.
    rows = _row_counts(plan)

    out = {}
    for group in plan["shopping"]:
        for item in group["items"]:
            # Staples say `top up if low` rather than a quantity, which is
            # exactly why they carry no days — the same exemption the day-tag
            # check makes.
            if not (item.get("days") or []):
                continue
            if item["name"] in in_prose or rows.get(item["name"], 0) > 1:
                continue

            taken = usage.get(item["name"])
            # Nothing uses it at all. That is the day-tag check's finding to
            # make, and it says something this cannot: which day is imaginary.
            if not taken:
                continue
            unit = taken[0][1]
            if any(amount[1] != unit for amount in taken):
                continue

            bought = parse_amount(item["qty"])
            if bought is None:
                continue
            if bought[1] != unit:
                # The units disagree, and exactly one shape of that is a fault
                # this can name: a list counting what the recipes weigh.
                # `1 bag (750 g)` against a recipe weighing 200 g is a pack
                # sitting in `qty`.
                #
                # Everything else is two ways of measuring rather than a defect,
                # and reporting it misdiagnoses the plan out loud. Grams against
                # millilitres wants a density nothing here has: a list weighing
                # the yoghurt its recipes pour is not a pack. Where the recipes
                # count and the list weighs, the list is the more precise of the
                # two, and 500 g of carrots is how a shop sells carrots.
                # A bare 6 is a count, not a pack, and 5 bunches is a measure
                # this file will not convert rather than a container. Naming either a
                # pack prints a repair for a fault the row does not have, so the
                # row has to look like packaging first: a container word, or a
                # gloss stating the amount in the unit the recipes use.
                list_counts = bought[1] not in ("", "g", "ml")
                packaged = bought[1] in PACKAGE_NOUNS or any(
                    a[1] == unit for a in gloss_amounts(item["qty"])
                )
                if unit not in ("g", "ml") or not list_counts or not packaged:
                    continue

            need = sum(amount[0] for amount in taken)
            if item["name"] in in_fridge:
                spare = in_fridge[item["name"]]
                if spare is None or spare[1] != unit:
                    continue
                need -= spare[0]
                # The fridge covers the week on its own, so the item does not
                # belong on the list at all — a different repair from a wrong
                # number, and one `qty` has no way to say. The day-tag check
                # says it: every day the row is tagged is one the fridge feeds.
                if need <= QUANTITY_EPSILON:
                    continue
            out[item["name"]] = ((need, unit), bought, measured_as.get(item["name"]))
    return out


def check_shopping_quantities(plan: dict) -> list:
    """The list buys what the week uses.

    The coverage check matches the two lists by name and the day-tag check by
    day. Nothing read the third field, so `Frozen peas — 1 bag (750 g)` sat on a
    real plan whose only pea recipe took 200 g, and the 550 g bought and never
    cooked is food waste the portion ledger exists to prevent and structurally
    cannot see: the ledger counts portions coming out of the pot, and this is
    what went into it.

    `qty` is therefore one quantity, and it is the week's — never the shelf's.
    That single meaning is what lets this compare exactly, with no tolerance
    band.

    Three codes. Two are the arithmetic in either direction; the third is a
    quantity that never was one — `1 bag (750 g)` counts bags where the recipes
    weigh grams, which the first version of this read as an incomparable unit
    and skipped. That is the conservative rule applied to the one row it must
    not skip, so a list coarser than the recipes is now the finding rather than
    the reason for silence. Only in that direction: where the recipes count and
    the list weighs, the list is the more precise of the two.

    Every finding states the total, so the repair is a copy rather than
    arithmetic the model has already got wrong once.
    """
    findings = []
    # Keyed by name, and safe to look up that way: a name sitting on more than
    # one row is left out of the table entirely, so whatever is in it is on
    # exactly one row and reports exactly once.
    quantities = shopping_quantities(plan)

    for group in plan["shopping"]:
        for item in group["items"]:
            sums = quantities.get(item["name"])
            if sums is None:
                continue
            # The need as the message will spell it, which is what the repair
            # hands back. Comparing finer than the row can write is a loop.
            # Both sides snapped, not just the need. The message prints each of
            # them rounded to three decimals of the row's unit, so leaving the
            # bought amount exact let a row written finer than that render
            # identically on both sides of a sentence saying they disagree.
            need = snap_to_row(sums[0], item["qty"])
            bought = snap_to_row(sums[1], item["qty"])
            measured = sums[2]
            where = "shopping." + group["category"] + "." + item["name"]
            # A count is bought whole. Bigger plates scale a recipe's count to
            # the half, so the week's sum can land on one, and `Bananas — 6.5`
            # is a row no shop can sell. The list buys the whole number above,
            # which makes a counted row the one row allowed to buy more than
            # the week cooks, by less than one. A weight or a volume stays
            # exact, and so does a measure such as a spoon: nobody buys one,
            # and `3.5 tsp` of butter is a block either way. `exact` is kept for
            # the message, and is None wherever the week's sum was whole already.
            exact = None
            if need[1] not in ("g", "ml") and need[1] not in MEASURES and need[1] == bought[1]:
                whole = _ceil(need[0] - QUANTITY_EPSILON)
                if abs(whole - need[0]) > QUANTITY_EPSILON:
                    exact = need
                    need = (whole, need[1])
            # The need unsnapped, since the repair may leave the row's unit: a
            # sixteenth of a pound snapped to a thousandth is not whole ounces.
            # A count never does, and is said as the whole number above.
            if exact is None:
                buy = repair_like(sums[0], item["qty"], item)
            else:
                buy = format_amount_like(need, item["qty"])
            have = format_amount_like(bought, item["qty"])
            and_pack = pack_in_ounces(item, buy)

            if bought[1] != need[1]:
                # The row counts bags and the recipes weigh, so there is no row
                # unit to scale through and the canonical one would answer a
                # week written in ounces with 453.592 g. The recipes' own
                # wording is the next best thing the plan has.
                in_recipe_units = repair_like(sums[0], measured or item["qty"], item)
                findings.append(
                    finding(
                        6,
                        "shopping-quantity-is-a-pack",
                        item["name"] + " is on the list as " + have
                        + ", but the week's recipes measure it rather than counting"
                        + " packs, and it needs " + in_recipe_units
                        + ". The list states the amount, not the packaging, so set qty to "
                        + in_recipe_units + pack_in_ounces(item, in_recipe_units)
                        + " — the athlete picks a pack that covers it.",
                        where,
                    )
                )
                continue
            if abs(bought[0] - need[0]) <= QUANTITY_EPSILON:
                # Right, and written in a figure no shop prices.
                if in_pounds(item["qty"]) and odd_pounds(sums[0][0]):
                    findings.append(
                        finding(
                            6,
                            "shopping-quantity-in-odd-pounds",
                            item["name"] + " is on the list as " + have
                            + ", which is what the week needs, in a fraction of a"
                            + " pound no shop prices. A pound is written only in"
                            + " whole quarters; set qty to " + buy + and_pack + ".",
                            where,
                        )
                    )
                # Right, and in pounds beside a pack in ounces, which the page
                # cannot count.
                elif in_ounces_instead(sums[0], item["qty"], item):
                    findings.append(
                        finding(
                            6,
                            "shopping-quantity-in-pounds-beside-ounces",
                            item["name"] + " is on the list as " + have
                            + ", which is what the week needs, but its pack is not in"
                            + " pounds and the page counts packs only where the two"
                            + " are written alike. A row with a pack is in ounces"
                            + " like its pack; set qty to " + buy + ".",
                            where,
                        )
                    )
                continue

            if bought[0] < need[0]:
                if exact is not None and bought[0] >= exact[0] - QUANTITY_EPSILON:
                    # Enough for the week, and not a number anyone can buy.
                    message = (
                        item["name"] + " is on the list as " + have + ", and the week's recipes"
                        + " take " + format_amount_like(exact, item["qty"]) + " of it, but a"
                        + " shop sells whole ones. Set qty to " + buy + ": a count on the list"
                        + " is rounded up to the whole number."
                    )
                else:
                    needs = buy + " of it" if exact is None else (
                        format_amount_like(exact, item["qty"]) + " of it, " + buy + " bought whole")
                    message = (
                        item["name"] + " is on the list as " + have
                        + ", but the week needs " + needs + " — the athlete comes home"
                        + " without enough to cook what the plan says to cook. Set qty to "
                        + buy + and_pack + "."
                    )
                findings.append(finding(6, "shopping-quantity-short", message, where))
            else:
                # The surplus is spelled the way the need is. Where the row is
                # too coarse to hold the need the answer is given in the
                # canonical unit — and spelling the difference in the row's unit
                # anyway let it round back up to the whole purchase, which reads
                # as though none of it is used.
                # A rounded count is over the week by more than the rounding:
                # 8 against 6.5 is 1.5 never cooked, and the week needs 6.5.
                used = need if exact is None else exact
                gap = (bought[0] - used[0], need[1])
                needs = buy + " of it" if exact is None else (
                    format_amount_like(exact, item["qty"]) + " of it, " + buy + " bought whole")
                if in_row_units(need, item["qty"]) is None:
                    spare = format_amount(gap)
                elif buy.endswith(" oz") and in_pounds(item["qty"]):
                    # Moved to ounces with the need, and from the unsnapped
                    # sides for the same reason: 2 lb against 23 oz is 9 oz
                    # over, where the snapped need left 8.992.
                    spare = in_ounces(sums[1][0] - sums[0][0])
                else:
                    spare = format_amount_like(gap, item["qty"])
                findings.append(
                    finding(
                        6,
                        "shopping-quantity-excess",
                        item["name"] + " is on the list as " + have
                        + ", but the week needs only " + needs + " — " + spare
                        + " bought and never cooked. Set qty to " + buy + and_pack
                        + ", even where a shop only sells a bigger pack: the athlete reads"
                        + " what they need and picks one that covers it.",
                        where,
                    )
                )
    return findings


SYMBOL_UNITS = {"cl", "dl", "g", "gr", "kg", "l", "lb", "mg", "ml", "oz"}

# **The noun is ASCII letters**, and it has to exclude digits at *both* ends of
# the run rather than only at the front. SYMBOL_UNITS is an ASCII table, so
# nothing is lost by it — and what is gained is independence from the Unicode
# version the interpreter carries. Python 3.9's tables are frozen at Unicode 13,
# and thousands of codepoints in the first astral plane alone are unassigned
# there and letters in later versions. Asking "is this a letter" is therefore a
# question whose answer depends on which Python runs the file: "2 kg" with such
# a character glued to it would read as a mass on one and as nothing on another.
#
# It also means the captured run needs no trimming. A word class matches
# digits, and the scan resumes past whatever it swallows, so under one "about
# 2 400 g tins" and "about 2x400 g tins" could each go silent.
#
# **What may follow the unit is a closed list, and that is the shape of this
# predicate.** "2 l'oignon plus gros" is ordinary French and the bare "l" before
# the apostrophe is the litre symbol, so a legal hint fired a finding and spent
# one of the two repairs a plan gets. Excluding the apostrophe fixed that
# sentence and not the same sentence written with a modifier letter, a Hawaiian
# okina or a fullwidth form. A list of what must not follow has no end; a list
# of what may is ten characters long, and everything outside it fails toward
# silence.
#
# The digit and space classes stay spelled out, as QUANTITY above.
# What may follow a unit is a closed list; what may not has no end. `\\Z` and not
# `$`, because this engine's `$` also matches before a final newline.
AFTER_UNIT = "(?=\\Z|[" + re.escape(JS_WHITESPACE + ")]},;:./-\u2013\u2014") + "])"

# A dash may stand where the space between the number and the unit goes, as in
# the attributive "about 2 400-g tins".
_JOIN = "(?:[-\u2013\u2014]" + _SPACE + "*)?"

AMOUNT_IN_TEXT = re.compile(
    "([0-9]+(?:[.,][0-9]+)?)" + _SPACE + "*" + _JOIN + "([A-Za-z]+)" + AFTER_UNIT
)


def states_an_amount(text: str) -> bool:
    """Does this text state a mass or a volume anywhere in it?

    Latin-script unit symbols only,
    whatever language surrounds them: a hit fires a finding, so knowing the
    French spelling of a litre and not the Portuguese one would fail a French
    plan and ship the identical Portuguese one. A spelled-out unit is missed in
    every language, and so is a symbol in another script — both silence, which
    is the direction this file errs in everywhere.
    """
    for match in AMOUNT_IN_TEXT.finditer(text):
        if singular(fold_for_matching(match.group(2))) in SYMBOL_UNITS:
            return True
    return False


def check_shopping_notes(plan: dict) -> list:
    """A row's note says what the row is for, or how to buy it, and never how much.

    `1 L already in the fridge covers Tue and Wed` puts the fridge's amount
    beside the row's, and the larger of two amounts is the one that gets bought.
    A row's `note` is read here and nowhere else — never a meal's.

    Its reach is the amount detector's, which is a minority of the rule: a count,
    a unit in words, a symbol in another script and native digits are silent.
    The rule is also written on the `note` description and in the fuelling
    reference, and this teaches only the cases it can see. A pack size fires,
    and should; a nutrition figure fires, and should not, and is declared
    rather than fixed. Staples are not exempt.
    """
    findings = []
    for group in plan["shopping"]:
        for item in group["items"]:
            note = js_trim(item.get("note") or "")
            if not note or not states_an_amount(note):
                continue
            findings.append(
                finding(
                    6,
                    "shopping-note-states-an-amount",
                    item["name"] + ' has note "' + note
                    + '", which states an amount beside the ' + item["qty"]
                    + " in qty. Two amounts on one row get shopped at the larger."
                    + " What is already in the fridge is in fridge, and qty has"
                    + " already taken it off. A note says what the row is for, or how"
                    + ' to buy it, and never how much in any form — not "1 L",'
                    + ' not "1 litre", not "2 bottles": take the amount out of the'
                    + " note, or leave note out of this row.",
                    "shopping." + group["category"] + "." + item["name"],
                )
            )
    return findings


# How far a day named lighter may exceed one named heavier before it is a
# finding: 5%. A few grams of carbohydrate change nothing for the athlete and
# cost a repair round; the inversions this exists for are far wider.
RANKING_BAND = 1.05

# The days before the day named first that may be fed like it: two. Race
# loading runs over one or two days, and the day before the biggest session is
# fed for it, so a plan is right to out-feed a hard day there.
RANKING_EXEMPT_DAYS = 2

# Every spelling of a day the ranking check reads, lower-cased: the full
# names, the three-letter forms, and the four longer abbreviations people write.
RANKED_DAY = {name.lower(): name for name in DAY_NAMES}
RANKED_DAY.update({abbr.lower(): name for name, abbr in DAY_ABBR_OF.items()})
RANKED_DAY.update(
    {"tues": "Tuesday", "weds": "Wednesday", "thur": "Thursday", "thurs": "Thursday"}
)

# ASCII letters and nothing else. Never a case-insensitive flag: under one, this
# class also matches İ, ı, ſ and the Kelvin sign, none of which is a letter of
# any day's name.
LEADING_LETTERS = re.compile("[A-Za-z]+")


def top_level_parts(text: str) -> list:
    """The comma-separated parts of a day list, outside any parentheses.

    Trimmed as js_trim trims, with empty parts dropped. A closing bracket
    never takes the depth below zero, so a stray one cannot hide every comma
    after it.
    """
    parts = []
    depth = 0
    current = ""
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append(current)
            current = ""
            continue
        current += ch
    parts.append(current)
    return [part for part in (js_trim(p) for p in parts) if part != ""]


def ranked_days(text: str) -> list:
    """The day each part of a day list names, in order, or None for a part naming none."""
    out = []
    for part in top_level_parts(text):
        match = LEADING_LETTERS.match(part)
        out.append(RANKED_DAY.get(match.group(0).lower()) if match else None)
    return out


def _readable_carbs(origin) -> bool:
    """Whether an origin states its reference portion's carbohydrate as a number.

    Anything else is a fault the day checks name, and read as nothing it would
    make the day look under-fed.
    """
    nutrition = origin.get("nutrition") if origin is not None else None
    if not isinstance(nutrition, dict):
        return False
    carbs = nutrition.get("carbs")
    return isinstance(carbs, (int, float)) and not isinstance(carbs, bool)


def _athlete_carbs(plan: dict, recipe: dict):
    """What the athlete's plate of this dish carries, or None with no plate for them.

    A plate is a number of portions of its origin's reference portion, rounded
    half up; an entry with no plates is one portion.
    """
    reference = origin_of(plan, recipe)["nutrition"]["carbs"]
    plates = recipe.get("plates")
    if plates is None:
        plates = [{"eater": 0, "portions": 1}]
    mine = [p for p in plates if p.get("eater") == 0]
    if not mine:
        return None
    return sum(_floor(reference * p["portions"] + 0.5) for p in mine)


def ranked_carbs(plan: dict, name: str):
    """A day's meal carbohydrate, or None when the day cannot be compared.

    Only a day whose meals are whole is compared: each main slot there once,
    not excluded, and served by exactly one recipe per dish it names, the main
    and everything alongside it. A missing, moved or doubled recipe, a dish
    named that no recipe has, or a dish whose figures cannot be read, is a fault
    the day and portion checks already name, and comparing that day would add
    advice to fix the wrong thing.
    Skipping errs on the silent side. Only the athlete's own plates count: the
    published schema has no fields for anyone else.
    """
    day = next((d for d in plan["days"] if d["name"] == name), None)
    if day is None or is_excluded(day):
        return None
    carbs = 0
    for meal_name in MEAL_NAMES:
        meals = [m for m in day["meals"] if SLOT_TO_MEAL.get(m["slot"]) == meal_name]
        if len(meals) != 1 or is_excluded(meals[0]):
            return None
        recipes = [
            r for r in plan["recipes"] if r["day"] == name and r["meal"] == meal_name
        ]
        dishes = sorted(dishes_of(meals[0]))
        if not dishes or sorted(r["title"] for r in recipes) != dishes:
            return None
        # A dish whose figures cannot be read is check 3's to name; read as
        # nothing it would make the day look under-fed.
        if not all(_readable_carbs(origin_of(plan, r)) for r in recipes):
            return None
        plates = [_athlete_carbs(plan, r) for r in recipes]
        if all(p is None for p in plates):
            return None
        carbs += sum(p for p in plates if p is not None)
    return carbs


def check_ranking_is_fuelled(plan: dict) -> list:
    """The meals follow the ranking the plan states.

    `hard_days` is the plan's own answer to which days it fuelled hardest,
    hardest first, and `easy_days` names the rest. This holds the meals to that
    answer and computes no load of its own, so the plan is compared only with
    itself. Two ways to be wrong: a later hard day out-feeding the day named
    first, and an easy day out-feeding a hard one.

    If the first part of `hard_days` names no day, nothing fires. The two days
    before the day named first are exempt only as the heavier side, since
    those are the days a plan may feed up for it; a hard day there fed too
    little is still a finding. A race day is held to the ranking like any
    hard day: it is ranked hardest and fed the largest portions.
    """
    findings = []
    where = "training_overview.hard_days"
    overview = plan["training_overview"]
    hard = ranked_days(overview["hard_days"])
    # A ranked day the plan does not cover: a week ranked before it was cut to
    # its window. Said first, because when it is the day named first nothing
    # below has anything to compare against.
    uncovered = outside_the_run(plan)
    for name, days in (("hard_days", hard), ("easy_days", ranked_days(overview["easy_days"]))):
        for i, day in enumerate(days):
            if day is None or days.index(day) != i or not uncovered(day):
                continue
            findings.append(
                finding(
                    10,
                    "ranked-day-not-covered",
                    "`" + name + "` names " + day + ", which this plan does not cover. Rank only the"
                    + " days the plan covers.",
                    "training_overview." + name,
                )
            )
    top = hard[0] if hard else None
    if not top:
        return findings

    def unique(days):
        return [d for i, d in enumerate(days) if d is not None and days.index(d) == i]

    hard_days = unique(hard)
    # A day named in both lists is a double day split across them, and the
    # plan has called it hard: it is never the easy side of a comparison.
    easy_days = [d for d in unique(ranked_days(overview["easy_days"])) if d not in hard_days]
    exempt = {
        d for d in DAY_NAMES if 1 <= DAY_INDEX[top] - DAY_INDEX[d] <= RANKING_EXEMPT_DAYS
    }
    carbs = {}

    def carbs_of(day):
        if day not in carbs:
            carbs[day] = ranked_carbs(plan, day)
        return carbs[day]

    top_carbs = carbs_of(top)
    if top_carbs is not None:
        for day in hard_days[1:]:
            day_carbs = carbs_of(day)
            if day in exempt or day_carbs is None or not day_carbs > top_carbs * RANKING_BAND:
                continue
            findings.append(
                finding(
                    10,
                    "hardest-day-outfuelled",
                    day + " is named after " + top + " in `hard_days`, and its meals"
                    + " carry " + rendered(day_carbs) + " g of carbohydrate against "
                    + top + "'s " + rendered(top_carbs) + " g. The day named first is"
                    + " the one fuelled hardest: give " + top + " the most, or name "
                    + day + " first.",
                    where,
                )
            )

    for hard_day in hard_days:
        hard_carbs = carbs_of(hard_day)
        if hard_carbs is None:
            continue
        for easy_day in easy_days:
            easy_carbs = carbs_of(easy_day)
            if easy_day == hard_day or easy_day in exempt or easy_carbs is None:
                continue
            if not easy_carbs > hard_carbs * RANKING_BAND:
                continue
            findings.append(
                finding(
                    10,
                    "hard-day-under-easy-day",
                    hard_day + " is named in `hard_days` and its meals carry "
                    + rendered(hard_carbs) + " g of carbohydrate, less than the "
                    + rendered(easy_carbs) + " g on " + easy_day + ", which"
                    + " `easy_days` names. Apart from the days just before the day"
                    + " named first, which may be fed for it, a hard day is fuelled"
                    + " above every easy day: give " + hard_day + " more, give "
                    + easy_day + " less, or move one of them to the other list.",
                    where,
                )
            )
    return findings


CHECK_TITLES = {
    1: "Check 1 — ingredient coverage (recipe → shopping list)",
    2: "Check 2 — usage-day tags (shopping list → recipe)",
    3: "Check 3 — day × meal completeness",
    4: "Check 4 — portion ledger",
    5: "Check 5 — servings state their own size",
    6: "Check 6 — the list buys what the week uses",
    9: "Check 9 — the load table covers the week it orders, and adds up",
    10: "Check 10 — the meals follow the ranking the plan states",
}


def check_week_load_days(plan: dict) -> list:
    """Check 9's day codes: `week_load` scores each day of the plan, once.

    It matters most on a plan that starts mid-week, which is where a reading of
    the days before it survives into the table. Each entry's own figures are not
    checked here.
    """
    findings = []
    run = expected_run(plan)
    planned = set(run)
    seen = set()
    # Read with a default, because this file has no schema gate and a host
    # that left the table out should hear that it scores no day, not that the
    # checker could not read the document.
    for i, row in enumerate(plan.get("week_load") or []):
        where = "week_load[" + str(i) + "]"
        if row["day"] not in planned:
            findings.append(
                finding(
                    9,
                    "week-load-day-not-planned",
                    "`week_load` scores " + row["day"] + ", which this plan does not cover. It"
                    + " has one entry per day of `days`.",
                    where,
                )
            )
            continue
        if row["day"] in seen:
            findings.append(
                finding(9, "week-load-day-repeated", "`week_load` scores " + row["day"] + " twice.", where)
            )
            continue
        seen.add(row["day"])
    for day in run:
        if day not in seen:
            findings.append(
                finding(
                    9,
                    "week-load-day-missing",
                    "`week_load` does not score " + day + ", which this plan covers.",
                    "week_load",
                )
            )
    return findings


def run_checks(plan: dict) -> list:
    """Every check, in the order the findings read best.

    Nothing looks at the document's shape first. There is no schema gate in
    front of this, so a document too broken to walk raises and the caller turns
    that into the could-not-validate exit.

    **That is the floor, not a licence.** Where a check can still read a
    document the schema forbids, it reports a finding naming the fault rather
    than raising. Getting this backwards cost three faults, all of the same
    shape. A day name outside the seven, an abbreviation outside its enum and a
    null exclusion reason are all impossible under the published schema and all
    perfectly survivable, with a finding naming the fault. This file used to
    exit instead — and in the first of the three, the check whose
    entire purpose is to say the week is misnamed was the one being suppressed.
    """
    # A plan whose days are not the run it should be hears day-order and
    # nothing else, as the completeness check already stops at it. Every other
    # check reads the days, or recipes entered on them, and would answer a
    # missing day as a fact about the week — one brief asking for Friday back
    # and for its portions, its shopping and its reading gone. Here nothing
    # knows which days were asked for, so a repair that drops one would ship
    # clean.
    completeness = check_day_meal_completeness(plan)
    if any(f["code"] == "day-order" for f in completeness):
        return completeness
    return (
        check_portion_ledger(plan)
        + check_ingredient_coverage(plan)
        + check_usage_day_tags(plan)
        + check_batch_scaling(plan)
        + completeness
        + check_shopping_quantities(plan)
        + check_shopping_notes(plan)
        + check_ranking_is_fuelled(plan)
        + check_week_load_days(plan)
    )


def repair_brief(findings: list) -> str:
    """The findings, grouped by check, so the shape of the problem is visible."""
    if not findings:
        return ""
    lines = []
    for check in sorted({f["check"] for f in findings}):
        lines.append("\n" + CHECK_TITLES[check] + ":")
        for f in findings:
            if f["check"] != check:
                continue
            prefix = f["where"] + ": " if f["where"] else ""
            lines.append("  - " + prefix + f["message"])
    return js_trim("\n".join(lines))


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Check a meal plan for consistency.")
    parser.add_argument("path", help="the plan document to check")
    parser.add_argument(
        "--json", action="store_true", dest="as_json", help="print the findings as JSON"
    )
    args = parser.parse_args(argv)

    # Two separate failures, because they want opposite responses and used to
    # print the same sentence. Not finding the file means the path is wrong or
    # the plan was never written; reading it and then failing a check means the
    # document's shape defeats the checks. Telling somebody to fix their plan's
    # shape when nothing was ever read is worse than saying nothing.
    #
    # Both exit 2, and neither is ever a finding: they are statements about the
    # checker rather than claims about the plan.
    # Bytes here, characters below. Only *finding* the file belongs with the
    # path: text that is not valid UTF-8 is a document written badly at the
    # right path, the same as one that will not parse, and both want the same
    # response. Decoding inside this block reported them as a path problem.
    try:
        with open(args.path, "rb") as handle:
            raw = handle.read()
    except Exception as error:
        print("could not read " + args.path + ": " + str(error), file=sys.stderr)
        return 2

    # Decoding and parsing belong with the checks, not with opening the file. A
    # document that will not decode or will not parse — a trailing comma, a
    # truncated write, a fence left around it — is one somebody wrote badly at
    # the right path, and the repair is to write it again. Grouping either with
    # a missing file would send them to check a path that was correct all along.
    try:
        plan = json.loads(raw.decode("utf-8"))
        findings = run_checks(plan)
    except Exception as error:
        print("could not validate " + args.path + ": " + str(error), file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(findings, ensure_ascii=False))
    elif findings:
        print(repair_brief(findings))
    else:
        print(args.path + ": no findings")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
