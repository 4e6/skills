# How the week is fuelled

The rules the schema cannot express. Read this before writing any JSON.

Every figure here is taken from published sports-nutrition guidance and checked
against it, and they are the defaults. Where the athlete's coach or dietitian has
given them different targets, use those instead and say so in
`training_overview.summary`. Keep to one set of figures across the plan: a plan
built from two contradicts itself.

## Contents

- The one rule that makes this worth doing
- A dietary restriction outranks everything here
- Fuel belongs to a session
- Snacks top each day up to its target
- The days this plan covers
- What you have, and what you must not invent
- Body weight is the number every target is built from
- You can ask, but the plan cannot
- Every cooked portion gets eaten
- Three kinds of recipe entry
- A meal is a list of dishes
- The shopping list
- Using what is already there
- A container you open is a container the week finishes
- The athlete
- Weights and measures are their country's
- Days the athlete is away
- Meals the athlete eats elsewhere
- Race weeks
- Shape

## The one rule that makes this worth doing

**Carbohydrate tracks training load.** Rank the week's days yourself, hardest
first, and periodize the food across that order. You have only what the athlete
wrote — there is no ranking anywhere but the one you draw from it, and you write
it down in `week_load` before any meal (see *What you have, and what you must not
invent*).

- **Hard days** get the largest carbohydrate portions.
- **Easy and recovery days** are lighter: fewer carbohydrates.
- **The day before the week's biggest session is fed for that session**, whatever
  it holds itself — a rest day included. Its carbohydrate sits with the hard days
  rather than the easy ones, and its dinner is carbohydrate-led and not a heavy or
  fatty one. In a race week the g/kg rules under *Race weeks* take its place.
- **A session carries fuel** when it lasts about 45 minutes or more and its main
  work is at threshold or harder (Z4 and above, where the week names zones) — not
  an easier session with a few hard efforts in it — or when it lasts about 90
  minutes or more at any pace, whatever day it falls on. *Fuel belongs to a
  session* says what its lines say; any other session carries none. The food on
  those lines is an **example**, not a prescription — see the next section before
  you write any of it down.
- The same dish may appear on a hard day and an easy day at different sizes.
  Saturday's porridge is a bigger bowl than Monday's, and its plate says so:
  `portions: 1.25`.
- Quantities on the shopping list scale with the week's total load, because they
  are the sum of what the recipes cook. A big aerobic week buys more oats, rice
  and bread than a taper week.

A plan whose biggest fuel day is not the biggest training day **the week actually
holds** has failed, however good the food is. Say which day you made the biggest
in `training_overview.summary`, and why — that sentence is where the athlete
finds out what you assumed. The check holds the meals to `hard_days`: no later
hard day out-feeds the day named first, and no day named easy out-feeds one named
hard, outside the two days before the first. **One sentence, under 450
characters.**

## A dietary restriction outranks everything here

If the athlete has named a restriction — an allergy, vegetarian, vegan, coeliac,
lactose intolerance, a religious rule, anything they avoid — **it beats every
example in this file, without exception.** The foods named above and below are
illustrations of a principle, and the principle survives the substitution while
the example does not.

- **Substitute the fuel, do not drop it.** Chocolate milk is there because it is
  carbohydrate and protein within about two hours of a session that carries fuel;
  a soy or pea-protein drink
  does the same job. An energy bar with oats and dates does what a wheat-based
  one does. Work out what the example was *for*, then find something that does
  it and that they can eat.
- **An allergy is not a preference.** Where they have said allergy, the
  ingredient appears nowhere in the week — not in a recipe, not as a garnish,
  not on the shopping list, not in a shared batch. A preference can be
  accommodated loosely; an allergy cannot.
- **Check the examples as well as the recipes and the list.** A restriction
  honoured in the cooking and broken in a session's example is still broken.
- **Say that you applied it, in `training_overview.summary`.** They cannot ask
  you whether you remembered. One clause is enough — that the week is dairy-free
  throughout, or that the after-session example is soy because of the lactose.

Where a restriction and a carbohydrate target genuinely pull against each other,
**the restriction wins and you say so.** A slightly lower carbohydrate day is a
worse plan; a plan they cannot eat is not a plan.

## Fuel belongs to a session

Fuel before, during and after training is **guidance with example food**. It is
not a meal, it is not bought, and it does not say when anything happens. Each
session a day holds is one entry in that day's `sessions`, and a session carries
its own `before`, `during` and `after` lines where they apply. The meals are a
separate list with no time of day: athletes move sessions around, and the plan
cannot know when they will. Which sessions carry fuel is the one rule's to say;
this is what their lines say.

- **A line is two fields.** `guidance` is what this session needs at that point —
  the range or the timing that applies, and never a food. `example` is food that
  roughly fits it, with amounts: an example rather than a prescription. On a
  `during` line the amounts are for the whole session — what to pack — and never
  an hour's worth, so a longer session's example is bigger. Prefer food the week
  already buys, name a sports product by what it is — an energy gel, an isotonic
  drink — and never by brand. Nothing on a line is on the shopping list, and
  nothing on a line says what a day uses.
- **Name every session as the week names it, in a few words**, and give it a
  length or an intensity only where the week states one — never a sum of its
  intervals, which leaves out the warm-up and so invents a figure. **A race says
  in its name that it is one** — `Lisbon Half Marathon race` — because a session's
  name is what identifies it wherever it is printed, and a reader who has the
  session names in front of them should be able to see that the day is a race.
- **Where the week leaves out a length or an intensity the one rule needs**,
  decide from what it does say. A session it names as hard or long — a threshold
  set, a long ride — gets its lines, and each says what depends on the missing
  figure. A `during` line for a threshold set reads `past an hour, 30–60 g an hour, the top past 90 minutes`,
  and for a long easy one `past about 90 minutes, roughly 30–60 g an hour`; a
  `before` line names no figure either way. A session it names as short or easy,
  or says nothing about, gets none. Never supply the figure.
- **Any quantity in `guidance` is a range; timing may be approximate.** `~50 g an
  hour` reads as prescribed for this athlete, and it is not. Carbohydrate is in
  grams, as `nutrition` is, and the hourly ranges are not scaled by body weight:
  the guidance states them per hour, for anybody.
- **Before a session**: small, familiar and carbohydrate-led, in about the last
  hour; a full meal goes 1–4 hours before, and is not a heavy or fatty one. Say
  the size of what is eaten and when — never a figure in grams.
- **During a session**, by its length: under about 45 minutes needs no
  carbohydrate, and water does; about 45–75 minutes of hard work, small amounts or
  a mouth rinse; one to two and a half hours, roughly 30–60 g an hour; longer,
  60–90 g an hour, the top only from a mix of glucose and fructose and for a gut
  trained to take it. Easier sessions take less. Between about 90 minutes and two
  and a half hours, a session whose main work is at threshold or harder takes the
  top of that 30–60 g an hour range, about 60 g, and its line still prints the
  range. A pool swim follows the same ranges, taken at the wall; an open-water
  swim is fuelled before and after, and has no `during` line.
- **After a session that carries fuel**: carbohydrate with protein within about 2
  hours, and straight away when another session that carries fuel follows within
  about 8 hours. The plan does not know the gap, so where the day holds another
  session the line says what to do if it follows soon.
- **Fluid**, on a session over about an hour: about 0.4–0.8 L an hour, more in heat
  — 14–27 fl oz on a plan in US units.
- **A line carries only the part that applies to its session.** These ranges
  are the rule the lines apply; the plan has no block restating them whole, so
  each line states its own range. Keep a line's `guidance` to about 60
  characters.
- **A race is a session.** It gets a `before` line whatever its length, and
  `during` and `after` lines by the same ranges where it carries fuel; where the
  week does not say how long it runs, those lines say what depends on that.
- `before`: `small and carbohydrate-led, in about the last hour`, e.g. `1 banana, black coffee`
- `during`: `roughly 30–60 g of carbohydrate an hour`, e.g. over 1h45, `2 bottles of isotonic drink, 1 energy gel`
- `after`: `carbohydrate with protein, within about 2 hours`, e.g. `1 bottle of chocolate milk`

**An example is the whole session's, so do the arithmetic.** The range is per
hour and the food list is the total, and nothing downstream reconciles them —
a line reading *60–90 g an hour* beside two gels is a plan that undershoots its
own advice, and it will ship. Multiply the range by the session's hours, then
name food that adds up to it:

| item | carbohydrate |
|---|---|
| 1 bottle of isotonic drink (500 ml) | 30–40 g |
| 1 energy gel | 21–27 g |
| 1 energy bar | 43 g |
| 1 banana | 27 g |
| 1 date | 5–18 g |

Worked twice, because one example with no duration on it taught nothing:

- **1h45 at 30–60 g/h** is 53–105 g, and 0.4–0.8 L/h is 0.7–1.4 L.
  `2 bottles of isotonic drink, 1 energy gel` is 82–107 g and 1 L — 47–61 g/h
  and 0.57 L/h.
- **2h42 at 60–90 g/h** is 162–243 g, and 1.1–2.2 L. `3 bottles of isotonic
  drink, 3 energy gels, 1 energy bar` is 197–244 g and 1.5 L — 73–90 g/h and
  0.56 L/h.

**The drink is most of both numbers, so count the bottles first.** A 500 ml
bottle is the only item here carrying fluid, and a long session needs two or
three of them before any gel is counted — an example built from gels alone hits
the carbohydrate range and misses the fluid one, which is the commonest way this
line is half right.

Two items is an hour's worth. It is not a long ride's, and a long ride given two
items is the commonest way this line goes wrong.

**A published range is not a figure you invented.** An hours figure, a distance
or a load score is a measurement of their week, and a made-up one is
indistinguishable, on the page, from a real one. A carbohydrate or fluid range
measures nothing they did: it is published sports-nutrition guidance, the same
kind of figure as the g/kg targets under *Race weeks*, and printing it claims only
that the guidance says so.

## Snacks top each day up to its target

Three meals rarely carry a training day's carbohydrate, so a day gets a line of
**snacks**: guidance with example food, exactly as a session's fuel lines are. It
is not a meal, it is not bought, nothing checks it, and it says nothing about
when in the day it is eaten.

**Each day has a target, by what it holds**, in grams per kilogram of their body
weight across the whole day — everything eaten, meals, fuel and snacks:

| day | carbohydrate |
|---|---|
| rest, or only low-intensity or skill-based training | 3–5 g/kg |
| about an hour at moderate intensity or harder | 5–7 g/kg |
| one to three hours at moderate to high intensity | 6–10 g/kg |
| more than about four to five hours at moderate to high intensity | 8–12 g/kg |

An easy session of about an hour or less is the first row, not the second. The
hours count only sessions at moderate intensity or harder; an easy session on
the same day does not move the day up a row. A day between two rows takes the
lower. The day before the week's biggest session takes that session's row, as
the one rule already feeds it, and days under *Race weeks* take its g/kg figure
instead of this table. Otherwise a day with no training, and every day of a week
they chose to leave undescribed, takes the first row.

**Protein is 1.2–2.0 g/kg across the day**, spread over it rather than in one
sitting.

**The snacks carry what the meals and the fuel do not:**

1. Add up the day's meal carbohydrate — for each dish, its origin's
   `nutrition.carbs` times the plate's `portions`.
2. Add the food on the day's fuel lines, from the table under *Fuel belongs to a
   session*, and anything not on it from what its label would say. Where the
   table gives a range, take its middle.
3. Take both from the bottom of the day's target and from its top, at their body
   weight, and round each to 10 g. **A snack line is an instruction, so a day
   gets one only where it falls short of the bottom.** Where the meals and the
   fuel already reach it, or the shortfall rounds to 0, the day has no
   carbohydrate line: never one saying *up to*, which reads as *eat this* on a
   day that needs nothing.
4. Where the meals' protein is under 1.2 g/kg, the guidance adds `and some
   protein`, and the example carries it. A day short only of protein gets a line
   saying so: `some protein; the carbohydrate is covered`.

**The meals still carry the ranking.** Hard days get the biggest plates, and the
check compares the meals alone; snacks top a day up and never stand in for the
bigger bowl a hard day needs.

- `guidance` is the shortfall first and the room above it second, and never a
  food: `at least about 60 g of carbohydrate, up to 290 g`. The first figure is
  what the day needs; the second is how far it may go. About 60 characters.
- `example` is food that makes up **the first figure**, with amounts: `1 bagel with
  jam, 1 banana`. Ordinary food, no brand, nothing that needs cooking. Nothing
  in it is on the shopping list.
- A day the athlete is away has no `snacks`; a meal eaten elsewhere changes
  nothing here.

These targets are general, and their right place in the band is the athlete's
and their coach's to fine-tune.

## The days this plan covers

The plan covers exactly the days agreed with the athlete in step 1, in order,
ending on Sunday — seven for a whole week, fewer when it starts mid-week. **Never
add a day, and never drop one.**

A shorter window changes nothing else. Carbohydrate is still periodised across
the days you have, the hardest of them still gets fuelled hardest, and the
shopping list still buys exactly what those days cook.

**`training_overview` names only days the plan covers.** A day named there is a
day the athlete looks up on the page, and one that is not in the plan cannot be
found.

**Nothing is cooked before the first day.** Every recipe sits on a day the plan
covers, and every repeat or leftover points at one.

Food the athlete says they made before the first day is fridge food: list it in
`fridge`, and give the meal that eats it an entry of its own, noted `use what's in
fridge`. Food they did not mention is not in the fridge.

The days before the first are in neither `days` nor `week_load`: each day the
plan covers keeps its own weekday's sessions from the week they gave.

## What you have, and what you must not invent

Everything you know about the week is what the athlete typed — which may be a
great deal or almost nothing. This skill fetches no calendar, so
whatever durations, distances, zones or load scores reached you came from them;
there is no other source, and nothing arrives after you have started.

**So print no figure the athlete did not give you.** `training_overview.total`
may read `5 sessions`, or `~9h, 5 sessions` if they said nine hours — and must
never carry an hours figure, a distance or a training-load score they did not
state. A number you made up is indistinguishable, on the page, from one their
coach gave them, and it is the one thing here they cannot check. That is a rule
about their week: the ranges on a session's fuel lines and the targets behind a
day's snacks are published guidance,
not a fact about them, as the section above says. **Their sessions come out of
what they wrote**, one entry each in `sessions`, and none gets a length or an
intensity they did not state.

**A figure they gave you is theirs to print and yours to fuel from.** Where they
have given hours, distances or a load score, use them: they are what separates a
day that is long from a day that is merely busy. **Adding up what they gave you
is not inventing it** — where every session's hours came from them,
`~10h30, 6 sessions` is fair in `training_overview.total`, and a load score they
stated session by session totals the same way.

One caution, because a load score is the easiest number here to misread. It
weights intensity rather than energy, so equal points are not equal food: an hour
at threshold and a long easy ride can score much the same and cost very different
meals, and it is the longer, easier one that costs more. Read it as a check on
the order and the spacing of your days — which is what it is built for — and
never as a number to divide the carbohydrate by.

Read what they wrote for what the arithmetic would have discarded anyway. A
session described as *fasted*, *race simulation*, *open water*, *brick*, *before
work* or *abort if the pace degrades* is telling you something. Read it to decide
what the food is.

Where they have described a day only vaguely — or not at all — plan it as easy
and say so. An undescribed day is not a rest day.

**Write your reading of the week down before any meal.** `week_load` comes before
the ranking and every day in the document, so that the order is settled before a
bowl is sized: one row per day, one entry per session they described, the hours
they stated — 0 where they stated none, never a guess — and the hardest
intensity they named as a zone. Nothing prints the table. The hours are theirs
and may appear wherever they would anyway; the zones and loads are your scoring,
and neither may reach `training_overview.total` or a session's name. A 0 is
unmeasured, not easy: a day whose sessions carry no duration is ranked from its
words. Then name the order in `hard_days`, hardest first, and size every day's
meals from that list — the check compares each day's meal carbohydrate with it:
no later hard day out-feeds the one you named first, and no day you named easy
out-feeds one you named hard, except the two days before the one you named
first, which may be fed up for it. A day in neither list is not compared.

**A week with no plan in it is every day of those.** An athlete may say they train
without a written week, or that they are not training at all. Neither gives you
anything to rank, so nothing is periodised and every day is easy — easy, not
rest, exactly as above. Say which of the two they told you in `week_label` and
in `training_overview.total`, so that a level plan is not read as periodisation
that failed, and invent no week to put in its place: a stated fallback is the
honest answer where a fabricated Tuesday is not. Its `week_load` is one row per
day, with no entries.

## Body weight is the number every target is built from

It is the one number you can count on having, and every portion and every daily
carbohydrate figure in the plan is derived from it — the hourly ranges on a
session's fuel lines are the figures that are not — so use it explicitly:

- The days before a race are prescribed in **g/kg** — the day before a shorter
  race, the two days before a half marathon or longer — see *Race weeks* below,
  and do the arithmetic against their actual weight. The race itself takes the
  hourly ranges, which are not.
- The scale of every other day's portions follows from it too. A 58 kg runner
  and a 92 kg rower on the same session do not eat the same bowl.

**Every target is per kilogram, whatever unit they gave.** Pounds are divided
by 2.2046 before any arithmetic, and the plan's food is still weighed in their
country's units (*Weights and measures are their country's*, below).

State the weight you used in `training_overview.summary` if you had to interpret
it — for example if they gave a range, or pounds, which it states in both:
`141 lb (64 kg)`.

## You can ask, but the plan cannot

You are in a conversation, so **a missing required input is a question, not a
guess**. Ask for it and stop.

One of the two has a fallback and the other has none. A week nobody gave you
becomes easy days, said on the page — but only where the athlete said
there was no week, because assuming that of somebody who simply has not answered
yet is still assuming. Body weight has nothing of the kind: every portion in the
document scales from it, nothing is derivable from a sport or a height or a
range, and there is no plan without it.

The finished plan is the opposite. It gets printed and carried into a kitchen and
a supermarket, and there is nobody to answer a question written on it. So inside
the document: where you had to assume something, say what you assumed and move
on. Never ask the reader to confirm anything, and never offer to change it.

## Every cooked portion gets eaten

This is a hard rule. Cooked food that is not scheduled spoils, and a plan that
quietly over-cooks costs the athlete money and trust.

- An `origin` recipe's `servings` lists **every** portion it yields, mapped to
  the meal slot that eats it — including the cooking day's own slot. A
  single-serving dish lists exactly one.
- Pick batch sizes that divide cleanly into slots that actually exist. If a dish
  only fits one meal this week, cook **one** serving. Never default to two.
- A portion may wait at most **four days** between cooking and eating. Cooked
  fish, leafy salads and dressed dishes should be eaten within two.
- Say the same thing in the meal plan bullets: the cooking day's `note` reads
  `cook 2 — eat 1, reserve 1`, and the later day's reads `leftover from Mon`.
  **A note states no amounts** — no grams, no kcal, not *the larger portion*: how
  much anybody eats is `portions`, and the page prints it.
- **A plate is a number of portions of its dish.** The origin states what one
  portion is worth in `nutrition`, and every plate — its own, a leftover's, a
  repeat's — is that times its `portions`. That multiplying is done for you:
  each pot is its list sized to the plates it feeds, and the shopping list is
  the sum of the pots. So a batch split unevenly to fuel a harder day is simply
  two different `portions` — `1` on Friday, `1.25` on Saturday's leftover — and
  needs saying nowhere else.

## Three kinds of recipe entry

Every main meal of every day gets its own entry, so a reader can open one day and
see that whole day's eating. A dish eaten twice appears twice.

- **origin** — the day it is first cooked. Full recipe: 4–8 ingredients with
  quantities **for the `yields` portions you name** — a pot for two lists what
  goes in a pot for two — 3–7 numbered steps, `nutrition` for **one** portion,
  and `portion_size` saying what one portion is in a unit a cook can multiply:
  `150 g cooked rice`, `1 cup cooked rice` on a plan in US units, `2 eggs`,
  never *a ladle*. Keep it tight; this is a
  working kitchen reference, not a cookbook.
- **repeat** — cooked again from scratch on a later day. No steps and no
  ingredients: it is cooked the same way, so `origin_day` carries the method,
  and its pot is the origin's list at its own plates' size, worked out for you.
  A bigger bowl is more `portions`. It still needs its ingredients bought, so
  the days it falls on appear in the shopping tags.
- **leftover** — eating a portion of an earlier batch. No ingredients, no steps,
  no `nutrition` — just `origin_day` and its plates. Its ingredients were bought
  for the cooking day, so the leftover day does **not** appear in the shopping
  tags.

**Weigh what a plate's size changes, and count only what is cooked whole.** A
pot is multiplied to the plates it feeds and rounded up, so rice, potatoes,
bread and bananas weighed in grams scale cleanly, and a count of eggs or fillets
rounds to what can be cooked.

**Food from a tin or can is weighed on the line like everything else** —
`Tinned chickpeas, drained — 240 g`, or `Canned chickpeas, drained — 9 oz` in
the US, never `1 tin` as its quantity. The page works out
for itself how many tins a line takes, from the `pack` on that food's shopping
row, so no recipe line states a count of its own.

Use the identical `title` on every day a dish appears — a repeat is linked back
to its method by matching it. Never put the meal slot in the title.

## A meal is a list of dishes

A meal's `dish` is its main — the one the meal is named for. Anything else
cooked for it is a dish of its own, named in `alongside`, with its own recipe
entry at that day and meal: a pot of rice beside a stew, a tray of potatoes
beside the chicken.

- **Prefer a small number of dishes that share ingredients and cook together.**
  Most meals are one dish; a side is for a meal where it earns its page — two or
  three dishes at a shared dinner at most, never five. A tray, a pot and a pan.
  The shopping list should get shorter per portion, not longer, and a plan is
  written in one answer that has a length limit: every dish is a whole recipe.
- **A dish has quantities and a method.** If it is cooked, weighed or has steps,
  it is a dish in `alongside` with its own recipe.
- **Everything on the plate is in a recipe.** Food served with a dish — bread
  with the soup, a lemon wedge with the fish — is an ingredient line in that
  dish's recipe, `Sourdough — 2 slices`, and its carbohydrate is in the dish's
  `nutrition`. Then the list buys its amount, the plate scales it, and every
  figure counts it. A dish eaten again as a leftover or a repeat comes with the
  same things, so put in the recipe only what goes with it every time.
- **Each dish is its own batch.** It has its own `servings`, its own portions
  and its own `nutrition`, and the rules above apply to it on its own — a side
  can be a leftover of Monday's while the main is cooked fresh.

## The shopping list

- **Grouped by where the item is picked up, never by what it does.** The category
  is a place in the shop, so the only question for an item is *which part of the
  shop do I stand in*. Potatoes are produce, not a carbohydrate. Tuna in a tin
  or can is with the tins, not at the fish counter. Butter is in the chiller,
  not with the cooking oils. Frozen peas are in the freezer, not with the
  vegetables.
  - **Which zone an item sits in varies by country, so use the athlete's.** Eggs
    are refrigerated in some countries and sold off an ambient shelf in others;
    salt-cured fish and cured sausage hang unrefrigerated where they are a
    staple and sit in a chiller where they are an import; fermented pastes and
    fresh noodles are chilled where they turn over fast enough to be sold fresh.
    Put each item where the athlete's own shops keep it, and where two zones are
    adjacent, the one they would walk to.
  - Two ambient sections divide by **form, not by kind**: anything sold as a dry
    packet is Rice, Pasta & Dry Goods — nuts, seeds, dried fruit, flour, dried
    seaweed, stock powder — and anything in a tin or can, a jar or a bottle,
    plus the spices, is Tins, Jars & Seasonings. Where a country's shops sell
    one of these loose in the produce section instead, it goes there.
  - The categories are listed in walking order: ambient first, chilled and frozen
    last. **Omit any category this week has nothing for.** A week with nothing
    frozen has no Frozen section; do not invent an item to fill one.
  - **The category is a key, written as the schema lists it in every country.**
    The page prints the aisle as the athlete's shops name it: on a list in US
    units, *Produce*, *Canned Goods, Jars & Seasonings*, *Meat & Seafood* and
    *Dairy, Eggs & Refrigerated*. A list written into the reply names them so
    too.
- **`qty` is what the week uses, not what the shop sells.** Add the item up
  across every recipe that cooks with it — a **repeat** cooks again and counts
  again, a **leftover** eats food that already exists and counts for nothing —
  then take off anything already in `fridge`. That total is `qty`, and the check
  compares it against the recipes.
  - **What a pot counts is what it cooks**: the origin's list at the size of
    the plates it feeds — every sitting in its `servings` for an origin, its own
    plates for a repeat. A repeat of a dish cooked for three is its own plates'
    worth, not three more; counting the whole batch twice is the 2x over-buy
    this rule exists to prevent.
  - **One quantity, and never a pack size where a recipe measures the item.**
    Write `200 g` of frozen peas and `70 g` of cheese — `7 oz` and `2.5 oz` in
    the US — even though no shop sells either amount: the athlete reads what the week needs and picks a bag or a
    block that covers it, the same way they already do for rice. Never `1 bag`,
    and never `1 bag (750 g)` — two *amounts of food* on one line is a choice made
    at walking pace, and the one a shopper acts on is the bigger. A count of the
    purchase is not a second amount of food; the page prints one, worked out from
    the `pack` below, and you never write it. A staple is the one exception, and
    it carries no days (below).
  - **Say what one purchase holds in `pack`, and let the page do the counting.**
    The weight is right and it is hard to shop from: nobody eyeballs 460 g of
    onions, and 480 g of chickpeas is two tins only if you know what a tin
    drains to. You know it; the page does not. So `qty` stays the weight — it is
    the number the check reads — and `pack.qty` says how much **one** of them
    provides. The page divides and prints the count itself, so never write a
    count anywhere: no `about 2 tins`, in `qty` or beside it.
  - **`pack.qty` is what reaches the pot, not what the label says.** Recipes
    weigh tinned food drained, so a 400 g tin of chickpeas that drains to 240 g
    is `240 g` here, and a 15 oz can that drains to 9 oz is `9 oz`. Write the gross weight and the count comes out wrong the
    moment a week needs more than one tin.
  - **`pack.one` and `pack.many` are the container's name** — "tin" and "tins",
    "jar" and "jars". Give both or neither: the page prints whichever the count
    calls for. **Leave both out for loose countable pieces** — onions, oranges,
    peppers — where the bare number is what a shopper reads.
  - **A tinned or jarred food says so in its name**, and every recipe line that
    uses it starts with that whole name: `Tinned chickpeas — 480 g` on the list,
    `Tinned chickpeas, drained — 240 g` in the recipe, never a bare
    `Chickpeas, drained`, which names no row. The count the page prints comes
    after the name, and `Chickpeas` has been read as fresh, or dried, by then.
    Tuna, tomatoes and beans the same: `Tinned tuna`, `Tinned tomatoes`. The
    container word
    is English — a tin and a can are the same thing, so `Tinned` or `Canned`,
    whichever suits the athlete's own shops, never their own language's word for
    it — and a recipe line repeats it whole. How it is cut goes in `note` — `chopped` — and never in the
    name: a recipe line writes its preparation after its comma, so a fresh
    `Tomato, chopped` resolves to a row called `Chopped tomatoes`. Every recipe
    line starts with its item's name exactly.
  - **One food, one row.** Potatoes the week boils, bakes and roasts are one
    `Potatoes` row, not `Potatoes`, `Baking potatoes` and `New potatoes` for the
    athlete to add up in the aisle. A second kind gets a row of its own only
    where it changes what gets cooked — a floury potato for mash, a waxy one for
    a salad — and then every row names its kind, never a bare `Potatoes` beside
    it. A different food that shares a word is not a second kind: sweet potatoes
    are not potatoes.
  - **Leave `pack` out entirely** where `qty` already counts — `Eggs — 5`,
    `Lemon — 2` — and on staples, and on anything with no standard purchase to
    count: rice, oats, mince, grated cheese, fish by weight.
  - **Where the week's total is not what anyone buys, write the unit they buy.**
    A staple topped up rather than bought, a bag of salad leaves a recipe takes a
    handful from: `1 jar`, `1 tub` or `1 bottle` is the honest answer. This is the
    same boundary the check draws: it leaves a staple alone, and otherwise speaks
    only where the recipes state an amount.
- **Every item names the days that use it**, in week order, and that day set must
  be exactly right: read it off the written recipes, never off a dish's name. A
  "veg omelette" reads like it contains mushrooms; what counts is what your recipe
  actually lists.
  - A day counts if its own recipe lists the item, or if it is a **repeat** whose
    origin recipe lists it.
  - A **leftover** day does not count.
  - A day the fridge covers does not count. The fridge is eaten first, from the
    plan's first day: with 6 eggs in `fridge` and 2 cooked on Tuesday, 3 on
    Thursday and 2 on Friday, the row buys 1 and is tagged `Fri` alone — and
    every meal that eats from the fridge, Friday's too, says `use what's in
    fridge` in its `note`.
- **Staples take a note instead of days** — `top up if low`, `refill`. Olive oil,
  salt, stock cubes, dried herbs, and a condiment the recipes take by the
  spoonful and that keeps once opened: honey, jam, tomato purée, mustard, soy
  sauce. Its row is `Honey — 1 jar`, the unit they buy, never `5 tbsp`: nobody
  buys five tablespoons, and a jar is in the cupboard or it is not. A staple
  carries no days, whatever unit the recipes take it in — a dated row is added
  up against them like any other, and its `qty` has to be their total. A sauce
  that goes off once opened — pesto, a jar of pasta sauce — is not a staple, and
  is weighed like any other food. **Nor is butter**, even where the recipes
  measure it in spoons: it is a fat the week cooks with, so its row is dated and
  its `qty` is their total like any other — `Butter — 60 g`, or `5 tbsp` where
  they use spoons — never `1 pack · top up if low`. A row's `note` says what the
  row is for, or how to buy it, and never how much in any form — no weight or
  volume, no pack size, no count, not even of what is already in the fridge:
  `qty` is the one amount on a row, and it has already taken off what is in
  `fridge`.
- **The list buys the meals.** Nothing on a session's fuel lines or a day's
  snacks is on it or changes it: that food is an example, and a day's tags and
  a row's quantity come
  from the recipes alone.
- **Everything a recipe uses must be on the list or in the fridge.** Walk every
  recipe and check, including herbs, spices and condiments.

## Using what is already there

Where a meal uses something the athlete says is already in the fridge, say so in
that meal's `note`: `use what's in fridge`. Put those items in `fridge`, not on
the shopping list.

**Anything perishable goes early in the week.** A half-used bag of spinach or an
opened pack of chicken is mentioned precisely because it will not last to
Saturday — planning it into Sunday's dinner wastes it as surely as never using it
at all. Things that keep, like a jar of honey or a bag of rice, can sit anywhere
in the week.

## A container you open is a container the week finishes

A tin or can, or a jar, is bought whole and starts going off once it is opened.
A week that takes 120 g out of a 400 g tin of beans leaves half a tin nobody has
planned for — waste the plan created, and the same waste as a portion nobody eats.

**Fix it in the recipes, and never in `qty`.** Size the dish to use the container
up, or put the rest into a second meal within about three days, while the open
container is still good. `qty` is what the shopping rules above already say it
is, and it follows the recipes there on its own: write a bigger number against
recipes that go on cooking 120 g and the check reports food bought and never
cooked, which is a fault you have just created rather than one you have fixed.

**A bigger batch's extra portions are leftovers, and each takes a slot in
`servings`.** The same four-day window, and a plate of it is its `portions` of
the origin's one. *Never default to two*: where there is no
slot for a second plate, cook what the week eats and note the rest.

**Only what spoils once open and is measured out of a container you can aim at**:
tins and cans, a jar of sauce, cream, yoghurt, soft cheese. Dry goods keep, and
so do honey, jam and anything frozen. Out of scope: an item the list buys by the
container — `1 bag` of leaves, `1 tub` of powder, with no total to size a dish
against — and anything sold in sizes you cannot aim at, milk above all. Pour what
the bowl needs and leave the bottle out of it.

**It loses every argument with the training.** Leave half a tin rather than make
an easy day the week's biggest meal. No remainder is too large to leave: what is
awkward at one body weight and one week's load is finished without trying at
another.

**Where the week cannot finish it, the `note` says what is left and never that it
keeps** — `about half the jar left over`, on the meal that opens it; freezing is
the exception, so say if it freezes. Name no food: that counts as the day using
it and drops the row out of the quantity check for the whole week, and a dish
name carries the food's own word. No meal slot, which no recipe there lists. No
comparative — *bigger*, *larger* — which in a note declares an uneven split.

## The athlete

**The plan feeds the athlete alone**, not a household.

**Read the sport out of what they wrote, and do not assume it.** An endurance
week may be swimming, cycling and running together, or nothing but riding, or
running alongside strength work. Nothing here tells you which except their own
words.

The meals carry no time of day and no order against the sessions — the athlete
trains when it suits them. What to eat close to a session is its `before` line,
never a meal placed in front of it and never a note saying when to eat.

Cook what their country eats, when they have said where they are. A plan that
reads like a plan for somewhere else with the shopping names swapped has missed
the point: the dishes, the staples and the breakfast in particular should be ones
an ordinary household there actually cooks. Where they have not said, cook
something unremarkable and widely available rather than guessing at a cuisine.

**The plan is written in English, whatever country they live in.** Their country
chooses the food and never the words: everything the athlete reads is in
English — the dish names, the recipe steps, the ingredient names, the shopping
items, the quantity hints beside both, the meal notes and anything served
alongside, every session's name and its fuel lines, each day's snacks, `week_label`, the training overview and its summary, any reason a day or a meal
is skipped, and the closing note. A Portuguese week is Portuguese food under English names —
`Grilled mackerel with boiled potatoes and tomato salad` — and never the dish's
own name in their own language. Where a dish has no ordinary English name, say
what it is in English rather than borrowing theirs.

The closing note usually says which of that country's supermarkets is cheapest
for a category or two. Name chains that actually trade there.

## Weights and measures are their country's

**The country picks the measurement system, as it picks the dishes and the
shops**, and the unit the athlete gave their own weight in does not. An American
who says *78 kg* still shops in pounds, and a Briton who weighs themselves in
stone still buys 500 g of pasta. Three countries never went metric: the United
States, Liberia and Myanmar. A plan for one of them is in US customary units;
every other plan is metric, including one for somebody who has not said where
they live.

**US customary** wherever a quantity is printed: recipe lines, `portion_size`,
and the shopping list's `qty` and `pack.qty`.

- **Weight in ounces**: `8 oz`, `26 oz`, `44 oz`. A week's total is its
  recipes' ounces added up and is rarely a round number of pounds. Pounds are
  for a whole number of quarter pounds on a row with no `pack`: `1.25 lb`,
  `2 lb`. **A row with a `pack` is in ounces, and so is the pack**, since the
  page counts packs only where the two are written alike: `Canned black beans —
  27 oz` beside a `9 oz` can prints *3 cans*, `Bananas — 20 oz` beside a
  `4 oz` banana prints *5 bananas*, and a 2 lb bag is a `32 oz` pack. Anything
  a shop sells by weight — meat, fish, rice, pasta, oats, potatoes, cheese — is
  weighed on the recipe line too, never measured in cups, which are a volume
  and cannot be added to a weight.
- **Liquids in cups**, and on the list in cups, pints, quarts or gallons:
  `2 cups` of milk in a recipe, `1.5 quarts` on the list. **Never fluid ounces on
  a recipe line or the list**: `oz` alone is a weight, so `16 oz` of milk is read
  as a pound of it, and `fl oz` is two words where those fields take one unit.
- **Spoons as everywhere**: `1 tbsp`, `2 tsp`. Oven temperatures in °F.
- **One number and one unit**: `21 oz`, never `1 lb 5 oz`, which nothing can
  add up or multiply.
- **Never grams or millilitres, with one exception that holds in every
  country: carbohydrate is in grams.** The daily targets, the hourly ranges on a
  session's fuel lines and `nutrition` stay in grams, because that is how the
  guidance is published and how an American sports drink labels it. Fluid on
  those lines is in fl oz, about 14–27 fl oz an hour where a metric plan says
  0.4–0.8 L, and a bottle of sports drink there is 20 fl oz with about the same
  30–40 g as a 500 ml one.
- **Containers have the name their shops use**: `Canned chickpeas`, never
  `Tinned`. A 15 oz can drains to about 9 oz.

**Metric** everywhere else: grams, kilograms, millilitres, litres and °C, never
cups, ounces, pints or quarts. A British carton of milk is labelled in pints as
well as litres, and the plan still writes litres: the pint the check reads is
the US one, and a British pint is a fifth bigger, so `2 pints` on a British
list is added up wrong.

**Never convert a figure into the other system.** You know an American pack of
ground turkey is 12 oz, and `340 g` is that pack in a unit its shopper has to
convert back. Write the amount the way the shop in front of them prices it.

## Days the athlete is away

If the athlete has told you they need no meals on a day — travelling, away,
eating out — set that day's `excluded` to a short reason in their own terms
("Away for work — no meals planned"), leave its `meals` empty, and write no
recipe for it. The day still appears, with its session and its reason, so the
plan's days stay unbroken. That holds for days they asked you to leave out of the
plan — *just Saturday*, or *not the weekend, I'm away* — inside the run to Sunday:
each is excluded, with the reason in their words.

Three things follow from a day being excluded:

- **Cook smaller batches.** A dish cooked on Wednesday for four may not assign a
  portion to an excluded Thursday. Every portion still has to be eaten, so the
  batch shrinks or the portion moves to a day the athlete is there.
- **Buy less.** The shopping list is for the meals that exist.
- **Say it in the training summary**, so the athlete can see the request landed.

**Only the athlete's own words justify this.** A day they did not describe is not
an excluded day — it is an undescribed day, and it is planned as easy. If you are
unsure whether they meant "no meals" or "something light I can carry", plan the
food: a meal they skip costs them nothing, and a missing meal they needed is the
failure this exists to prevent.

## Meals the athlete eats elsewhere

The same idea one level down. If they eat a meal away — at work, out, with
family — set that meal's `excluded` to the short reason ("at work"), leave
`dish` unset, and write no recipe for it. **Keep the meal entry**: the row still
appears on the day, saying where the meal went. Dropping it would read as the
plan having forgotten lunch.

"Lunch at work on weekdays" means Monday to Friday lunch, not Saturday and
Sunday. Apply it to the days it names and no others.

The same three consequences follow: cook smaller batches so no portion is
assigned to a skipped meal, buy less, and say it in the training summary.

If all three main meals on a day are skipped, exclude the **day** instead — one
reason reads better than three, and there is one way to say a thing.

## Race weeks

If the week contains a race, the **distance** drives it. A race under about 90
minutes — a 10K for almost anybody — takes roughly 7–10 g/kg carbohydrate the day
before; a half marathon or longer takes roughly 10–12 g/kg on each of the two days
before, unless the week says they run it in under about 90 minutes. That
carbohydrate is in the meals and the snacks of those days; the race itself is a
session, with its lines under *Fuel belongs to a session*. Do that arithmetic
against their stated body weight.

If you have not been told the distance, **do not infer it**. Plan the week
conservatively and say in the training summary that the race-day fuelling assumes
nothing about distance.

A race day is the hardest day of its week even though nothing about it looks like
a long session in a description. Rank it accordingly, say so in
`training_overview.summary`, and make sure the day's own `session` names the race
— those two are all that say what the day is.

## Shape

- The days agreed at the start, in order, ending on Sunday.
- Each day has exactly one breakfast, one lunch and one dinner — **unless** the
  day is excluded, which has no meals at all, or a main meal is skipped, which
  keeps its entry and its reason but has no dish. See the two sections above.
  Its training is in `sessions` either way.
- Each main meal's `dish` matches its recipe entry's `title` exactly.
- Recipes are grouped by day in day order, and within a day breakfast, lunch,
  dinner — one entry per dish, so a meal with a side has two, the main first.
- `nutrition` is per serving and reflects *that day's* portion.
- Write the JSON object to the file SKILL.md's step 3 names, and nothing else to it.
