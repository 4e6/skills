# When there is no page

Read this before writing the plan if this host has no way to run a command at
all — no shell, no code execution. Otherwise read it at step 7, whenever step 6
made no page. Either way the athlete reads the week wherever they read your
reply, most likely on a phone, so what you write is the page and is designed as
one.

## Contents

- Size every batch for the pot it cooks
- Where the week goes
- For a phone
- The order
- Batch lines show their own arithmetic
- The sentence about checking
- An example

## Size every batch for the pot it cooks

On the page, the code scales each recipe to the plates it feeds. Without a page
nothing does, so every ingredient line you print has to be the pot it describes:

- **Writing the plan knowing there will be no page**, make an origin's `yields`
  the portions its sittings add up to: for each sitting in `servings`, the
  recipe entry at that sitting counts 1 where it has no `plates`, otherwise
  the `portions` on its `plates`, added up. A soup for Monday's dinner and
  Wednesday's lunch yields 2; with a 1.25 bowl on Wednesday it yields 2.25. Its
  list is then that pot and prints as written.
- **Every line you print comes from the plan's list as written**, at the page's
  factor: an origin's at its pot ÷ `yields`, a repeat's at its own portions (1
  where it has no `plates`) ÷ `yields`. Never scale a line you have already
  scaled — rounding twice drifts from what the shopping list counted. A factor
  of 1 prints the line as written. Otherwise round up, never down, as the page
  does: kilos, litres, pounds and decilitres to the hundredth; every other
  weight or volume to the whole unit; spoons, cups, cloves and anything
  counted to the half below three and to the whole from three. A line with no
  single number to multiply — a pinch, to taste, 1 lb 5 oz — prints as written.
- **A repeat's line is in the reply only.** The plan's repeat still carries no
  ingredients, but its pot is still bought.
- **The shopping list is the sum of the pots**, repeats included.

Reached at step 7, the plan was written for the page to scale: leave it as it is and
print each line at its factor. Those are the amounts the page would have
printed, so the shopping list and anything the check said still hold.

## Where the week goes

Where the host can show a panel beside the chat — an artifact or a canvas, for
instance — write the week there, in the order below: it can be saved,
scrolled and printed. The reply then carries the top, one line saying the week
is in the panel, and the closing lines. That is an example, never a
requirement: where there is none, the reply is the page.

Write the plan document first, as step 3 says, even with no file to put it in,
and write the page from it. Never paste the JSON. The batch lines and the list
come out of it, and a week written freehand loses the bookkeeping it forces.
`week_load` stays off the reply, as it stays off the page: it is your reading
of the week, not something the athlete gave you to print.

## For a phone

No code blocks and no tables anywhere in the week: both scroll sideways in a
chat bubble. Bold lines, short lists and plain sentences render everywhere.
Ingredients go on one line, separated by commas: the quantity, then the item,
and any preparation in brackets — *1 onion (diced)*.

## The order

1. **The top, four lines at most** — all a phone shows before the first scroll:
   `week_label` and `training_overview.total`, which is how an athlete who chose
   a level week sees it is level because they said so; the biggest fuel day and
   why, from `hard_days` and `training_overview.summary`; the restriction
   applied; and what you
   assumed — from the conversation, since the plan has no field for it.
2. **The days, in order from the first, each whole on its own.** A bold line
   with the day and its session; each session's `before`, `during` and `after`
   as one short line each — its `example` and when, not the guidance around it;
   then breakfast, lunch and dinner, each with its `extra` beside the dish.
   - **Where a dish is first cooked:** its name, its batch line, one line of
     ingredients with quantities, then the plan's own numbered steps as
     written. The page renders the plan; it is not a second draft of it. A
     dish cooked for one sitting from four ingredients or fewer keeps its
     ingredient line and drops its steps, because the line is the method.
   - **A leftover:** one line, pointing back, with its portions where they are
     not one.
   - **A repeat:** one line saying it is cooked fresh, as on the day it points
     back to — never *the same pot*, which reads as keeping food for days —
     plus its own ingredient line where its pot is not the origin's. No steps.
   - A side in `alongside` is written the way its dish is. Anything `excluded`
     prints its reason.
3. **The shopping list, last and in one block**, so it screenshots with no
   recipe in between: what comes from the `fridge` first, then each aisle, one
   row per item — its name and its quantity as the plan states it, and its
   `note` where it has one, since that is where *check the label is gluten-free*
   lives. No count of tins or packs: only the page works that out.
4. **After the list:** its `closing_note`, the sentence about checking, and the
   disclaimer.

## Batch lines show their own arithmetic

Build each from the origin's `servings`, not from the meal's `note`: *cook 3 —
Wed dinner, Thu lunch, Fri lunch*. The number is the portions the pot holds —
its sittings added up — and a sitting that is not one portion says how many, so the numbers
visibly add up: *cook 4 — Fri dinner (1¼), Sat dinner (1¾), Sun lunch*. The
athlete can see that every portion has a meal without working anything out.
That is bookkeeping they can read, never a check you claim.

## The sentence about checking

Step 7 of SKILL.md has three shapes for whether the plan was checked, and they
hold here unchanged. If the check ran and only the page failed, say what it
found in your own words — never its output — and that no printable page could
be made. If nothing checked the plan, use the one sentence *Not checked* gives. It
states a fact about the plan and names the reason. It is never a task for the
athlete, never a file or a script name, and never a claim that the plan was
checked.

## An example

The `>` is how this file marks an example, not how the reply is formatted. The
numbers are illustrative.

> **Monday — rest day**
>
> - **Breakfast: Porridge with banana** — cook 1 — Mon breakfast.
>   80 g oats, 400 ml milk, 1 banana, 1 tbsp honey.
> - **Dinner: Red lentil soup** — cook 2 — Mon dinner, Wed lunch.
>   160 g red lentils, 1 onion, 2 carrots, 1 litre stock, 1 tsp cumin.
>   1. Soften the chopped onion and carrots in a little oil, 8 minutes.
>   2. Add the lentils, cumin and stock; simmer 20 minutes and blend.
>   3. Keep the second portion covered in the fridge.
>
> **Wednesday — run 40 min easy**
>
> - **Lunch: Red lentil soup**, left over from Monday. Reheat until steaming.
>
> **Saturday — long ride 3 h**
>
> - Before: 1 banana, in the last hour.
> - During: 2 bottles of sports drink and a bar.
> - After: chocolate milk, within 2 hours.
> - **Breakfast: Porridge with banana**, cooked fresh as on Monday (1¼ portions):
>   100 g oats, 500 ml milk, 1½ bananas, 1½ tbsp honey.
