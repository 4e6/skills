# How the week is fuelled

The rules the schema cannot express. Read this before writing any JSON.

Every figure is published sports-nutrition guidance, and is a default. If the
athlete's coach or dietitian gave other targets, use those and say so in
`training_overview.summary`. Use one set of figures across the plan.

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
first, and periodise the food across that order. Rank only from what the athlete
wrote. Write the ranking in `week_load` before any meal (see *What you have, and
what you must not invent*).

- **Hard days** get the largest carbohydrate portions.
- **Easy and recovery days** get fewer.
- **The day before the week's biggest session is fed for it**, rest day
  included. Its carbohydrate sits with the hard days, and its dinner is
  carbohydrate-led, not heavy or fatty. In a race week, *Race weeks* replaces
  this.
- **A session carries fuel** on any day when either holds:
  - it lasts about 45 minutes or more and its main work is at threshold or
    harder (Z4 and above, where the week names zones), not an easier session with
    a few hard efforts;
  - it lasts about 90 minutes or more at any pace.

  Any other session carries none. *Fuel belongs to a session* says what the lines
  say. The food on them is an **example**, not a prescription.
- The same dish may appear on a hard and an easy day at different sizes.
  Saturday's breakfast may be Monday's dish, bigger: `portions: 1.25`.
- List quantities scale with the week's load, because they sum the recipes.

A plan whose biggest fuel day is not the biggest training day **the week actually
holds** has failed, however good the food is.

- Say which day you made the biggest, and why, in `training_overview.summary`.
  One sentence, under 450 characters. It is where the athlete finds out what you
  assumed.
- Give the reason in their words: their sessions, hours or race. Quote a figure
  only if they gave it. Never a zone, intensity factor or load you estimated.
- The check holds the meals to `hard_days`. No later hard day out-feeds the day
  named first. No day named easy out-feeds one named hard, except in the two days
  before the first.

## A dietary restriction outranks everything here

A named restriction (allergy, vegetarian, vegan, coeliac, lactose intolerance,
religious rule, anything they avoid) **beats every example in this file**.

- **Substitute the fuel, do not drop it.** Work out what the example was for,
  then find something that does it and that they can eat. A soy or pea-protein
  drink replaces a milk drink. An oat-and-date bar replaces a wheat one.
- **An allergy is not a preference.** The ingredient appears nowhere in the
  week: not in a recipe, a garnish, the shopping list or a shared batch.
- **Check the examples too.** A restriction broken in a session's example is
  broken.
- **Say you applied it** in `training_overview.summary`. One clause is enough.
- **If a restriction and a carbohydrate target pull apart, the restriction wins,
  and you say so.**

## Fuel belongs to a session

Fuel before, during and after training is **guidance with example food**. It is
not a meal, it is not bought, and it carries no time of day.

- Each session is one entry in the day's `sessions`. It carries its own
  `before`, `during` and `after` lines where they apply.
- Meals are a separate list with no time of day.
- Which sessions carry fuel is the one rule's to say.

Lines:

- **A line is two fields.**
  - `guidance` is the range or timing for that point. Never a food.
  - `example` is food that roughly fits it, with amounts.
  - On a `during` line the amounts are for the whole session (what to pack), so a
    longer session's example is bigger.
  - Food on a line is what people in the athlete's country have at that moment.
    Take it from what the week already buys where that is what they would have.
  - Name a sports product by what it is (an energy gel, an isotonic drink), never
    by brand.
  - This file names no food for the `before`, `after` and snack lines on purpose:
    it would end up on every athlete's page.
  - The list buys nothing for a line, and nothing on a line says what a day uses.
- **Name every session as the week names it**, in a few words.
  - Give a length or intensity only where the week states one. Never a sum of its
    intervals.
  - A race says so in its name: `Lisbon Half Marathon race`.
- **When the week leaves out a length or intensity the one rule needs**, decide
  from what it says.
  - A session named hard or long (a threshold set, a long ride) gets its lines.
    Each says what depends on the missing figure.
  - `during` for a threshold set: `past an hour, 30–60 g an hour, the top past 90
    minutes`.
  - `during` for a long easy one: `past about 90 minutes, roughly 30–60 g an
    hour`.
  - `before` names no figure either way.
  - A session named short or easy, or not described, gets none.
  - Never supply the figure.
- **A quantity in `guidance` is a range. Timing may be approximate.** `~50 g an
  hour` reads as prescribed for this athlete, and it is not.
- Carbohydrate is in grams. Hourly ranges are not scaled by body weight.

By moment:

- **Before:** small, familiar, carbohydrate-led, in about the last hour. A full
  meal goes 1–4 hours before, and is not heavy or fatty. Say the size and when.
  Never a figure in grams.
- **During, by length:**
  - under about 45 minutes: no carbohydrate, water;
  - about 45–75 minutes of hard work: small amounts or a mouth rinse;
  - one to two and a half hours: roughly 30–60 g an hour;
  - longer: 60–90 g an hour. The top only from a glucose and fructose mix, for a
    gut trained to take it;
  - easier sessions take less;
  - between about 90 minutes and two and a half hours, a session whose main work
    is at threshold or harder takes the top of 30–60 g an hour, about 60 g. Its
    line still prints the range;
  - a pool swim follows the same ranges, taken at the wall;
  - an open-water swim is fuelled before and after, with no `during` line.
- **After a session that carries fuel:** carbohydrate with protein within about 2
  hours. Straight away when another fuelled session follows within about 8
  hours. The plan does not know the gap, so where the day holds another session,
  the line says what to do if it follows soon.
- **Fluid,** on a session over about an hour: about 0.4–0.8 L an hour, more in
  heat. 14–27 fl oz in US units.
- **A line carries only the part that applies.** Each states its own range. Keep
  `guidance` to about 60 characters.
- **A race is a session.** It gets a `before` line whatever its length. It gets
  `during` and `after` lines by the same ranges where it carries fuel. Where the
  week does not say how long it runs, those lines say what depends on that.
  - **A stated goal time is the race's duration.** Size the `during` example from
    it.
  - Never split it into legs, subtract a leg they did not time, or estimate a
    duration they did not give.

Forms:

- `before`: `small and carbohydrate-led, in about the last hour`
- `during`: `roughly 30–60 g of carbohydrate an hour`, e.g. over 1h45, `2 bottles of
  isotonic drink, 1 energy gel`
- `after`: `carbohydrate with protein, within about 2 hours`

**An example is the whole session's, so do the arithmetic.** The range is per
hour and the food list is the total. Nothing downstream reconciles them. Multiply
the range by the session's hours, then name food that adds up to it.

| item | carbohydrate |
|---|---|
| 1 bottle of isotonic drink (500 ml) | 30–40 g |
| 1 energy gel | 21–27 g |
| 1 energy bar | 43 g |
| 1 banana | 27 g |
| 1 date | 5–18 g |

Worked twice:

- **1h45 at 30–60 g/h** is 53–105 g, and 0.4–0.8 L/h is 0.7–1.4 L. `2 bottles of
  isotonic drink, 1 energy gel` is 82–107 g and 1 L: 47–61 g/h and 0.57 L/h.
- **2h42 at 60–90 g/h** is 162–243 g, and 1.1–2.2 L. `3 bottles of isotonic
  drink, 3 energy gels, 1 energy bar` is 197–244 g and 1.5 L: 73–90 g/h and 0.56
  L/h.

Count the bottles first. A 500 ml bottle is the only item here carrying fluid. A
long session needs two or three before any gel is counted. An example of gels
alone hits the carbohydrate range and misses the fluid one. Two items is an
hour's worth, not a long ride's.

**A published range is not a figure you invented.** An hours figure, a distance
or a load score measures their week. A carbohydrate or fluid range measures
nothing they did. It is published guidance, like the g/kg targets under *Race
weeks*.

## Snacks top each day up to its target

Three meals rarely carry a training day's carbohydrate, so a day gets a line of
**snacks**: guidance with example food, like a session's fuel lines. It is not a
meal, it is not bought, nothing checks it, and it says nothing about when it is
eaten.

**Each day has a target by what it holds**, in g/kg of body weight across the
whole day (meals, fuel and snacks):

| day | carbohydrate |
|---|---|
| rest, or only low-intensity or skill-based training | 3–5 g/kg |
| about an hour at moderate intensity or harder | 5–7 g/kg |
| one to three hours at moderate to high intensity | 6–10 g/kg |
| more than about four to five hours at moderate to high intensity | 8–12 g/kg |

- An easy session of about an hour or less is the first row, not the second.
- Hours count only sessions at moderate intensity or harder. An easy session on
  the same day does not move the day up a row.
- A day between two rows takes the lower.
- The day before the week's biggest session takes that session's row.
- Days under *Race weeks* take its g/kg figure instead of this table.
- A day with no training, and every day of a week they left undescribed, takes
  the first row.

**Protein is 1.2–2.0 g/kg across the day**, spread over it.

**The snacks carry what the meals and the fuel do not:**

1. Add the day's meal carbohydrate: for each dish, its origin's
   `nutrition.carbs` times the plate's `portions`.
2. Add the food on the day's fuel lines, from the table above, and anything not
   on it from what its label would say. Take the middle of a range.
3. Take both from the bottom of the day's target and from its top, at their body
   weight. Round each to 10 g. **A day gets a snack line only where it falls
   short of the bottom.** Where the meals and fuel reach it, or the shortfall
   rounds to 0, the day has no carbohydrate line. Never one saying *up to* on a
   day that needs nothing.
4. Where the meals' protein is under 1.2 g/kg, add `and some protein` to the
   guidance, and carry it in the example. A day short only of protein gets
   `some protein; the carbohydrate is covered`.

**The meals still carry the ranking.** Hard days get the biggest plates. The
check compares the meals alone. Snacks never stand in for a bigger bowl.

- `guidance` is the shortfall first, the room above it second, never a food: `at
  least about 60 g of carbohydrate, up to 290 g`. About 60 characters.
- `example` is food that makes up **the first figure**, with amounts. It is what
  people in the athlete's country snack on, chosen as a fuel line's is. Ordinary
  food, no brand, nothing that needs cooking. The list buys nothing for it.
- A day the athlete is away has no `snacks`. A meal eaten elsewhere changes
  nothing here.

These targets are general. Their place in the band is the athlete's and their
coach's to fine-tune.

## The days this plan covers

The plan covers exactly the days agreed in step 1, in order, ending on Sunday.
**Never add a day, never drop one.**

- A shorter window changes nothing else. Periodise across the days you have. The
  hardest still gets fuelled hardest. The list buys exactly what those days cook.
- **`training_overview` names only days the plan covers.**
- **Nothing is cooked before the first day.** Every recipe sits on a covered day.
  Every repeat or leftover points at one.
- Food the athlete says they made before the first day is fridge food. List it in
  `fridge`. Give the meal that eats it its own entry, noted `use what's in
  fridge`. Food they did not mention is not in the fridge.
- Days before the first are in neither `days` nor `week_load`. Each covered day
  keeps its own weekday's sessions from the week they gave.

## What you have, and what you must not invent

Everything you know about the week is what the athlete gave you: a great deal or
almost nothing. Nothing arrives after you start.

**Print no figure the athlete did not give you.** A made-up number looks the same
on the page as a measured one, and they cannot check it.

- `training_overview.total` may read `5 sessions`, or `~9h, 5 sessions` if they
  said nine hours.
- It never carries an hours figure, a distance or a load score they did not
  state.
- Ranges on fuel lines and the targets behind snacks are published guidance, not
  facts about them.
- **Their sessions come out of what they wrote**, one entry each in `sessions`.
  None gets a length or intensity they did not state.

**A figure they gave you is theirs to print and yours to fuel from.** Hours,
distances and load scores separate a long day from a busy one.

- Adding up what they gave you is not inventing it. `~10h30, 6 sessions` is fair
  where every session's hours came from them. Add in minutes, then convert, and
  check the sum. Where any session has no stated duration, print the session
  count only.
- A load score stated session by session totals the same way.
- **A load score weights intensity, not energy.** An hour at threshold and a long
  easy ride can score alike and cost very different meals. The longer, easier one
  costs more. Use it to check the order and spacing of your days, never as a
  number to divide the carbohydrate by.

**Read what they wrote for what the arithmetic discards.** *Fasted*, *race
simulation*, *open water*, *brick*, *before work* and *abort if the pace
degrades* each tell you what the food should be.

**Describe a vague or missing day as easy, and say so.** An undescribed day is
not a rest day.

**Write your reading of the week down before any meal.** `week_load` comes before
the ranking and every day.

- One row per day, one entry per session they described.
- **Copy every figure they gave, exactly:** the time, the intensity factor, the
  load. Never recompute or correct one. Their software may use any formula.
- **Estimate only what they left out.**
  - Hours: 0 where they stated none, never a guess.
  - Intensity factor: one average figure for the whole session, from how they
    described it, warm-up and easy parts included. A session of hard intervals
    inside an easy one lands between the two. Leave it out where they gave only a
    load.
  - Load: `hours x IF^2 x 100`, so an hour at threshold is about 100.
- Nothing prints the table. Their own figures may appear wherever they would
  anyway. An estimated figure never reaches the page, the reply,
  `training_overview.total` or a session's name.
- A 0 is unmeasured, not easy. A day whose sessions carry no duration and no load
  is ranked from its words.
- Then name the order in `hard_days`, hardest first, and size every day's meals
  from it. The check compares each day's meal carbohydrate with it: no later hard
  day out-feeds the first named, and no day named easy out-feeds one named hard,
  except the two days before the first, which may be fed up for it. A day in
  neither list is not compared.

**A week with no plan in it is every day of those.** An athlete may train without
a written week, or not be training at all.

- Nothing is periodised. Every day is easy, not rest.
- Say which of the two they told you in `week_label` and `training_overview.total`,
  so a level plan is not read as periodisation that failed.
- Invent no week. A stated fallback is honest. A fabricated Tuesday is not.
- `week_load` is one row per day, with no entries.

## Body weight is the number every target is built from

Every portion and every daily carbohydrate figure derives from it. The hourly
ranges on fuel lines do not.

- Days before a race are prescribed in **g/kg**: the day before a shorter race,
  the two days before a half marathon or longer. See *Race weeks*. Do the
  arithmetic against their actual weight. The race itself takes the hourly
  ranges.
- Every other day's portions scale with it. A 58 kg runner and a 92 kg rower on
  the same session do not eat the same bowl.
- **Every target is per kilogram, whatever unit they gave.** Divide pounds by
  2.2046 before any arithmetic. The food is still weighed in their country's
  units (*Weights and measures are their country's*).
- State the weight you used in `training_overview.summary` if you had to
  interpret it, such as a range or pounds. Give both: `141 lb (64 kg)`.

## You can ask, but the plan cannot

You are in a conversation, so **a missing required input is a question, not a
guess**. Ask and stop.

- A week nobody gave you becomes easy days, said on the page. Only where the
  athlete said there was no week. Assuming it of someone who has not answered is
  still assuming.
- Body weight has no fallback. Every portion scales from it. Nothing is derivable
  from a sport, a height or a range. No weight, no plan.

The finished plan is the opposite. It is printed and carried into a kitchen and a
supermarket, and nobody can answer a question written on it.

- Where you had to assume something, say what you assumed and move on.
- Never ask the reader to confirm anything. Never offer to change it.

## Every cooked portion gets eaten

A hard rule. Cooked food that is not scheduled spoils, and a plan that over-cooks
costs the athlete money and trust.

- An `origin` recipe's `servings` lists **every** portion it yields, mapped to the
  meal slot that eats it, including the cooking day's own slot. A single-serving
  dish lists exactly one.
- Pick batch sizes that divide into slots that exist. A dish that fits one meal
  this week is cooked for **one**. Never default to two.
- A portion waits at most **four days** between cooking and eating. Cooked fish,
  leafy salads and dressed dishes: within two.
- Notes: the cooking day's `note` reads `cook 2 — eat 1, reserve 1`. The later
  day's reads `leftover from Mon`. **A note states no amounts**: no grams, no
  kcal, not *the larger portion*. How much anybody eats is `portions`, and the
  page prints it.
- **A plate is a number of portions of its dish.**
  - The origin states one portion's worth in `nutrition`. Every plate (its own, a
    leftover's, a repeat's) is that times its `portions`.
  - The multiplying is done for you. Each pot is its list sized to the plates it
    feeds. The shopping list is the sum of the pots.
  - A batch split unevenly to fuel a harder day is two different `portions`: `1`
    on Friday, `1.25` on Saturday's leftover. Say nothing more.

## Three kinds of recipe entry

Every main meal of every day gets its own entry, so one day shows all its eating.
A dish eaten twice appears twice.

- **origin:** the day it is first cooked. Full recipe.
  - 4–8 ingredients, with quantities **for the `yields` portions you name**.
  - 3–7 numbered steps.
  - `nutrition` for **one** portion.
  - `portion_size` says what one portion is, in a unit a cook can multiply: `150 g
    cooked rice`, `1 cup cooked rice` in US units, `2 eggs`. Never *a ladle*.
  - Keep it tight. It is a kitchen reference, not a cookbook.
- **repeat:** cooked again from scratch on a later day.
  - No steps, no ingredients. `origin_day` carries the method.
  - Its pot is the origin's list at its own plates' size, worked out for you. A
    bigger bowl is more `portions`.
  - Its ingredients are bought, so its days appear in the shopping tags.
- **leftover:** eating a portion of an earlier batch.
  - No ingredients, no steps, no `nutrition`. Just `origin_day` and its plates.
  - Its ingredients were bought for the cooking day, so the leftover day does
    **not** appear in the shopping tags.

**Weigh what a plate's size changes. Count only what is cooked whole.** A pot is
multiplied to the plates it feeds and rounded up. Rice, potatoes, bread and
bananas weighed in grams scale cleanly. A count of eggs or fillets rounds to what
can be cooked.

**Food from a tin or can is weighed on the line like everything else.**
`Tinned chickpeas, drained — 240 g`, or `Canned chickpeas, drained — 9 oz` in the
US. Never `1 tin`. The page works out the count from the `pack` on that food's
shopping row, so no recipe line states one.

**Use the identical `title` on every day a dish appears.** A repeat is linked to
its method by matching. Never put the meal slot in the title.

## A meal is a list of dishes

A meal's `dish` is its main, the one the meal is named for. Anything else cooked
for it is a dish of its own, named in `alongside`, with its own recipe entry at
that day and meal.

- **Prefer few dishes that share ingredients and cook together.** Most meals are
  one dish. A side is for a meal where it earns its page: two or three dishes at
  a shared dinner at most, never five. The list should get shorter per portion,
  not longer. Every dish is a whole recipe, and the plan is written in one answer
  with a length limit.
- **A dish has quantities and a method.** Cooked, weighed or with steps: it is a
  dish in `alongside` with its own recipe.
- **Everything on the plate is in a recipe.** Food served with a dish (bread with
  the soup, a lemon wedge with the fish) is an ingredient line in that dish's
  recipe: `Bread — 2 slices`. Its carbohydrate is in the dish's `nutrition`. Put
  in the recipe only what goes with it every time, since a leftover or repeat
  comes with the same things.
- **Each dish is its own batch.** Its own `servings`, portions and `nutrition`.
  A side can be a leftover of Monday's while the main is cooked fresh.

## The shopping list

- **Grouped by where the item is picked up, never by what it does.** The only
  question is *which part of the shop do I stand in*. Potatoes are produce, not a
  carbohydrate. Tinned tuna is with the tins, not the fish counter. Butter is in
  the chiller. Frozen peas are in the freezer.
  - **Which zone an item sits in varies by country. Use the athlete's.** Eggs are
    refrigerated in some countries and ambient in others. Salt-cured fish and
    cured sausage are ambient where they are a staple and chilled where they are
    an import. Fermented pastes and fresh noodles are chilled where they turn
    over fast. Put each item where the athlete's own shops keep it. Where two
    zones are adjacent, use the one they would walk to.
  - **Two ambient sections divide by form, not by kind.**
    - A dry packet is Rice, Pasta & Dry Goods: nuts, seeds, dried fruit, flour,
      dried seaweed, stock powder.
    - A tin or can, a jar or a bottle, plus the spices, is Tins, Jars &
      Seasonings.
    - Where a country's shops sell one of these loose in produce, it goes there.
  - Categories are in walking order, ambient first, chilled and frozen last.
    **Omit any category this week has nothing for.** Never invent an item to fill
    one.
  - **The category is a key, written as the schema lists it in every country.**
    The page prints the aisle as the athlete's shops name it. On a list in US
    units: *Produce*, *Canned Goods, Jars & Seasonings*, *Meat & Seafood*, *Dairy,
    Eggs & Refrigerated*. A list written into the reply names them so too.
- **`qty` is what the week uses, not what the shop sells.** Add the item across
  every recipe that cooks with it. A **repeat** cooks again and counts again. A
  **leftover** counts for nothing. Then take off anything in `fridge`. The check
  compares `qty` against the recipes.
  - **A pot counts what it cooks:** the origin's list at the size of the plates it
    feeds. Every sitting in its `servings` for an origin; its own plates for a
    repeat. A repeat of a dish cooked for three counts its own plates, not three
    more. Counting the whole batch twice is the 2x over-buy this rule prevents.
  - **One quantity. Never a pack size where a recipe measures the item.** `200 g`
    of frozen peas, `70 g` of cheese (`7 oz`, `2.5 oz` in the US), though no shop
    sells either. The athlete picks a bag or block that covers it. Never `1 bag`
    or `1 bag (750 g)`: two amounts on one line. The page prints a count from
    `pack`; you never write one. A staple is the one exception (below).
  - **A count on the list is a whole number, rounded up.** A week can add up to
    6.5 bananas or 2.5 lemons. The list says `7` and `3`. The recipes keep their
    halves. The check expects the whole number above their sum. A weight, a
    volume or a measure (a spoon, a pinch, a centimetre of ginger) is never
    rounded.
  - **`pack` says what one purchase holds. The page does the counting.** `qty`
    stays the weight, which is what the check reads. `pack.qty` says how much
    **one** purchase provides. Never write a count anywhere: no `about 2 tins`, in
    `qty` or beside it.
  - **`pack.qty` is what reaches the pot, not what the label says.** Recipes weigh
    tinned food drained. A 400 g tin of chickpeas that drains to 240 g is `240 g`.
    A 15 oz can that drains to 9 oz is `9 oz`. The gross weight breaks the count
    once a week needs more than one tin.
    - Where `pack` names a container, the page prints the cans first and the
      weight after, marked: `2 cans (18 oz drained)`.
    - It reads *drained* off the recipe lines. Every line of a drained food says
      so after its comma: `Canned black beans, drained`. A food that goes in
      whole, like tinned tomatoes, never does.
  - **`pack.one` and `pack.many` are the container's name:** "tin" and "tins", "jar"
    and "jars". Give both or neither. **Leave both out for loose countable
    pieces** (onions, oranges, peppers), where the bare number is what a shopper
    reads.
  - **A tinned or jarred food says so in its name.** Every recipe line that uses it
    starts with that whole name. `Tinned chickpeas — 480 g` on the list, `Tinned
    chickpeas, drained — 240 g` in the recipe. Never a bare `Chickpeas, drained`,
    which names no row. Same for `Tinned tuna`, `Tinned tomatoes`.
    - The container word is English: `Tinned` or `Canned`, whichever suits the
      athlete's shops. Never their language's word.
    - How it is cut goes in `note` (`chopped`), never the name. A recipe line writes
      preparation after its comma, so a fresh `Tomato, chopped` resolves to a row
      called `Chopped tomatoes`.
    - Every recipe line starts with its item's name exactly.
  - **One food, one row.** Potatoes the week boils, bakes and roasts are one
    `Potatoes` row. A second kind gets its own row only where it changes what is
    cooked (a floury potato for mash, a waxy one for salad). Then every row names
    its kind, with no bare `Potatoes` beside it. Sweet potatoes are not potatoes.
  - **Leave `pack` out** where `qty` already counts (`Eggs — 5`, `Lemon — 2`), on
    staples, and on anything with no standard purchase to count: rice, oats, mince,
    grated cheese, fish by weight.
  - **Where the week's total is not what anyone buys, write the unit they buy.** A
    staple topped up, or a bag of salad leaves a recipe takes a handful from:
    `1 jar`, `1 tub`, `1 bottle`. The check draws the same boundary. It leaves a
    staple alone, and otherwise speaks only where the recipes state an amount.
- **Every item names the days that use it**, in week order. The set must be
  exactly right. Read it off the written recipes, never off a dish's name. A "veg
  omelette" reads like it has mushrooms. What counts is what your recipe lists.
  - A day counts if its own recipe lists the item, or if it is a **repeat** whose
    origin recipe lists it.
  - A **leftover** day does not count.
  - A day the fridge covers does not count. The fridge is eaten first, from the
    plan's first day. With 6 eggs in `fridge` and 2 cooked Tuesday, 3 Thursday, 2
    Friday, the row buys 1 and is tagged `Fri` alone. Every meal that eats from
    the fridge, Friday's too, says `use what's in fridge` in its `note`.
- **Staples take a note instead of days:** `top up if low`, `refill`.
  - Staples: olive oil, salt, stock cubes, dried herbs, and a condiment the recipes
    take by the spoonful that keeps once opened (honey, jam, tomato purée, mustard,
    soy sauce).
  - The row is the unit they buy: `Honey — 1 jar`, never `5 tbsp`.
  - A staple carries no days, whatever unit the recipes use. A dated row is added
    up against the recipes, so its `qty` has to be their total.
  - A sauce that goes off once opened (pesto, a jar of pasta sauce) is not a
    staple. Weigh it like any other food.
  - **Nor is butter**, even where recipes use spoons. Its row is dated and its
    `qty` is their total: `Butter — 60 g`, or `5 tbsp`. Never `1 pack · top up if
    low`.
  - A row's `note` says what the row is for, or how to buy it. Never how much in
    any form: no weight or volume, no pack size, no count, not even of what is in
    the fridge. `qty` is the one amount on a row, and it has already taken off
    `fridge`.
- **The list buys the meals.** Nothing on a session's fuel lines or a day's
  snacks is on it or changes it. Tags and quantities come from the recipes alone.
- **Everything a recipe uses is on the list or in the fridge.** Walk every recipe,
  herbs, spices and condiments included.

## Using what is already there

Where a meal uses something the athlete says is in the fridge, put `use what's in
fridge` in that meal's `note`. Put those items in `fridge`, not on the list.

**Anything perishable goes early in the week.** A half-used bag of spinach or an
opened pack of chicken is mentioned because it will not last to Saturday.
Planning it into Sunday's dinner wastes it as surely as never using it. Things
that keep, like honey or rice, can sit anywhere.

## A container you open is a container the week finishes

A tin, can or jar is bought whole and starts going off once opened. A week that
takes 120 g out of a 400 g tin of beans leaves half a tin nobody planned for.
That is waste the plan created, the same as a portion nobody eats.

**Fix it in the recipes, never in `qty`.**

- Size the dish to use the container up, or put the rest into a second meal
  within about three days.
- `qty` follows the recipes. A bigger `qty` against recipes that still cook 120 g
  makes the check report food bought and never cooked.
- **A bigger batch's extra portions are leftovers.** Each takes a slot in
  `servings`, under the same four-day window. A plate of it is its `portions` of
  the origin's one. *Never default to two*: with no slot for a second plate, cook
  what the week eats and note the rest.

**In scope:** only what spoils once open and is measured out of a container you
can aim at: tins and cans, a jar of sauce, cream, yoghurt, soft cheese. Dry goods
keep. So do honey, jam and anything frozen.

**Out of scope:**

- an item the list buys by the container (`1 bag` of leaves, `1 tub` of powder),
  with no total to size a dish against;
- anything sold in sizes you cannot aim at, milk above all. Pour what the bowl
  needs.

**It loses every argument with the training.** Leave half a tin rather than make
an easy day the week's biggest meal. No remainder is too large to leave.

**Where the week cannot finish it, the `note` says what is left and never that it
keeps.** For example `about half the jar left over`, on the meal that opens it.
Freezing is the exception: say if it freezes.

- Name no food. That counts as the day using it and drops the row out of the
  quantity check for the week. A dish name carries the food's own word.
- Name no meal slot, which no recipe there lists.
- Use no comparative (*bigger*, *larger*). In a note it declares an uneven split.

## The athlete

**The plan feeds the athlete alone**, not a household.

**Read the sport out of what they wrote. Do not assume it.** An endurance week
may be swimming, cycling and running, only riding, or running with strength work.
Only their words say which.

**Meals carry no time of day and no order against the sessions.** What to eat
close to a session is its `before` line. Never a meal placed in front of it, and
never a note saying when to eat.

**Cook what their country eats**, when they have said where they are.

- Dishes, staples and above all breakfast should be ones an ordinary household
  there cooks. A plan that reads like one for somewhere else with the shop names
  swapped has missed the point.
- Where they have not said, cook something unremarkable and widely available.
  Never guess at a cuisine.

**The plan is written in English, whatever country they live in.** Their country
chooses the food, never the words.

- Everything the athlete reads is in English: dish names, recipe steps,
  ingredient names, shopping items and the hints beside them, meal notes,
  anything served alongside, session names and fuel lines, snacks, `week_label`,
  the training overview and summary, any reason a day or meal is skipped, and the
  closing note.
- A Portuguese week is Portuguese food under English names: `Grilled mackerel
  with boiled potatoes and tomato salad`. Never the dish's own name in their
  language.
- A dish with no ordinary English name is described in English. Never borrow
  theirs.

The closing note usually says which of that country's supermarkets is cheapest
for a category or two. Name chains that actually trade there.

## Weights and measures are their country's

**The country picks the measurement system, as it picks the dishes and shops.**
The unit the athlete gave their own weight in does not. An American who says *78
kg* still shops in pounds. A Briton who weighs themselves in stone still buys 500
g of pasta.

- Three countries never went metric: the United States, Liberia and Myanmar.
  A plan for one is in US customary units.
- Every other plan is metric, including one for someone who has not said where
  they live.

**US customary** wherever a quantity is printed: recipe lines, `portion_size`, and
the list's `qty` and `pack.qty`.

- **Weight in ounces:** `8 oz`, `26 oz`, `44 oz`. A week's total is its recipes'
  ounces added up and is rarely a round number of pounds.
  - Pounds are for a whole number of quarter pounds on a row with no `pack`:
    `1.25 lb`, `2 lb`.
  - **A row with a `pack` is in ounces, and so is the pack.** The page counts
    packs only where the two are written alike. `Canned black beans — 27 oz`
    beside a `9 oz` can prints *3 cans*. `Bananas — 20 oz` beside a `4 oz` banana
    prints *5*. A 2 lb bag is a `32 oz` pack.
  - Anything a shop sells by weight (meat, fish, rice, pasta, oats, potatoes,
    cheese) is weighed on the recipe line too. Never in cups, which are a volume
    and cannot be added to a weight.
- **Liquids in cups,** and on the list in cups, pints, quarts or gallons: `2 cups`
  of milk in a recipe, `1.5 quarts` on the list. **Never fluid ounces on a recipe
  line or the list.** `oz` alone is a weight, so `16 oz` of milk reads as a pound
  of it, and `fl oz` is two words where those fields take one unit.
- **Spoons as everywhere:** `1 tbsp`, `2 tsp`. Oven temperatures in °F.
- **One number and one unit:** `21 oz`, never `1 lb 5 oz`, which nothing can add
  up or multiply.
- **Never grams or millilitres, with one exception that holds in every country:
  carbohydrate is in grams.**
  - Daily targets, the hourly ranges on fuel lines and `nutrition` stay in grams.
  - Fluid on those lines is in fl oz: about 14–27 fl oz an hour where a metric plan
    says 0.4–0.8 L.
  - A bottle of sports drink there is 20 fl oz, with about the same 30–40 g as a
    500 ml one.
- **Containers have the name their shops use:** `Canned chickpeas`, never `Tinned`.
  A 15 oz can drains to about 9 oz.

**Metric** everywhere else: grams, kilograms, millilitres, litres and °C. Never
cups, ounces, pints or quarts. A British carton is labelled in pints as well as
litres, and the plan still writes litres. The pint the check reads is the US one,
and a British pint is a fifth bigger, so `2 pints` on a British list adds up
wrong.

**Never convert a figure into the other system.** An American pack of ground
turkey is 12 oz, and `340 g` makes the shopper convert back. Write the amount the
way the shop in front of them prices it.

## Days the athlete is away

If the athlete needs no meals on a day (travelling, away, eating out):

- Set that day's `excluded` to a short reason in their terms (`Away for work — no
  meals planned`).
- Leave its `meals` empty. Write no recipe for it.
- The day still appears, with its session and its reason, so the plan's days stay
  unbroken.
- This holds for days they asked you to leave out inside the run to Sunday, like
  *just Saturday* or *not the weekend, I'm away*. Each is excluded, with the
  reason in their words.

Three things follow:

- **Cook smaller batches.** No portion goes to an excluded day. The batch shrinks
  or the portion moves to a day they are there.
- **Buy less.** The list is for the meals that exist.
- **Say it in the training summary,** so they can see the request landed.

**Only the athlete's own words justify this.** A day they did not describe is
undescribed, and planned as easy. If unsure whether they meant "no meals" or
"something light I can carry", plan the food. A skipped meal costs them nothing.
A missing meal they needed is the failure this prevents.

## Meals the athlete eats elsewhere

The same idea, one level down. If they eat a meal away (at work, out, with
family):

- Set that meal's `excluded` to the short reason (`at work`).
- Leave `dish` unset. Write no recipe.
- **Keep the meal entry,** so the row still appears on the day, saying where the
  meal went. Dropping it reads as the plan forgetting lunch.
- "Lunch at work on weekdays" means Monday to Friday lunch, not the weekend.
  Apply it to the days it names and no others.
- The same three consequences follow: smaller batches, buy less, say it in the
  training summary.
- If all three main meals on a day are skipped, exclude the **day** instead. One
  reason reads better than three.

## Race weeks

If the week contains a race, the **distance** drives it.

- A race under about 90 minutes (a 10K for almost anybody): roughly 7–10 g/kg
  carbohydrate the day before.
- A half marathon or longer: roughly 10–12 g/kg on each of the two days before,
  unless the week says they run it in under about 90 minutes.
- That carbohydrate is in those days' meals and snacks. The race itself is a
  session, with lines under *Fuel belongs to a session*.
- Do the arithmetic against their stated body weight.

**If you have not been told the distance, do not infer it.** Plan the week
conservatively. Say in the training summary that the race-day fuelling assumes
nothing about distance.

**A race day is the hardest day of its week,** though nothing in a description
makes it look like a long session. Rank it so. Say so in
`training_overview.summary`. Make the day's own `session` name the race: those
two are all that say what the day is.

## Shape

- The days agreed at the start, in order, ending on Sunday.
- Each day has exactly one breakfast, one lunch and one dinner, **unless** the
  day is excluded (no meals at all) or a main meal is skipped (its entry and
  reason stay, with no dish). Its training is in `sessions` either way.
- Each main meal's `dish` matches its recipe entry's `title` exactly.
- Recipes are grouped by day in day order, and within a day by breakfast, lunch,
  dinner. One entry per dish, so a meal with a side has two, the main first.
- `nutrition` is per serving and reflects *that day's* portion.
- Write the JSON object to the file step 3 names, and nothing else to it.
