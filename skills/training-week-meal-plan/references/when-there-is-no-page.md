# When there is no page

Read this in either case:

- **Before writing the plan,** if this host cannot run any command (no shell, no
  code execution).
- **At step 7,** whenever step 6 made no page.

The athlete reads the week wherever they read your reply, most likely on a phone.
What you write is the page, so design it as one.

## Contents

- Size every batch for the pot it cooks
- Where the week goes
- For a phone
- The order
- Batch lines show their own arithmetic
- The sentence about checking
- An example

## Size every batch for the pot it cooks

On the page, code scales each recipe to the plates it feeds. Without a page,
nothing does. Every ingredient line you print has to be the pot it describes.

- **Writing the plan knowing there will be no page:** make an origin's `yields`
  the portions its sittings add up to.
  - For each sitting in `servings`, the recipe entry at that sitting counts 1
    where it has no `plates`, otherwise the `portions` on its `plates`. Add them.
  - A soup for Monday's dinner and Wednesday's lunch yields 2. With a 1.25 bowl on
    Wednesday it yields 2.25.
  - Its list is then that pot and prints as written.
- **Every line you print comes from the plan's list as written, at the page's
  factor.**
  - An origin's factor is its pot ÷ `yields`.
  - A repeat's is its own portions (1 where it has no `plates`) ÷ `yields`.
  - Never scale a line you have already scaled. Rounding twice drifts from the
    shopping list.
  - A factor of 1 prints the line as written.
  - Otherwise round up, never down, as the page does:
    - kilos, litres, pounds and decilitres: to the hundredth;
    - every other weight or volume: to the whole unit;
    - spoons, cups, pints, quarts, gallons, cloves and anything counted: to the
      half below three, to the whole from three.
  - A line with no single number to multiply (a pinch, to taste, 1 lb 5 oz)
    prints as written.
- **A repeat's line is in the reply only.** The plan's repeat still carries no
  ingredients, but its pot is still bought.
- **The shopping list is the sum of the pots,** repeats included.

Reached at step 7, the plan was written for the page to scale. Leave it as it is
and print each line at its factor. Those are the amounts the page would have
printed, so the shopping list and anything the check said still hold.

## Where the week goes

Where the host can show a panel beside the chat (an artifact or a canvas), write
the week there, in the order below. It can be saved, scrolled and printed. The
reply then carries the top, one line saying the week is in the panel, and the
closing lines. Where there is no panel, the reply is the page.

- Write the plan document first, as step 3 says, even with no file to put it in.
  Write the page from it.
- Never paste the JSON.
- The batch lines and the list come out of the document. A week written freehand
  loses the bookkeeping it forces.
- `week_load` stays off the reply, as it stays off the page. It is your reading of
  the week.

## For a phone

- No code blocks and no tables anywhere in the week. Both scroll sideways in a
  chat bubble.
- Use bold lines, short lists and plain sentences.
- Ingredients go on one line, separated by commas: the quantity, then the item,
  with preparation in brackets. *1 onion (diced)*.

## The order

1. **The top, four lines at most.** All a phone shows before the first scroll:
   - `week_label` and `training_overview.total`, so an athlete who chose a level
     week sees it is level because they said so;
   - the biggest fuel day and why, from `hard_days` and
     `training_overview.summary`;
   - the restriction applied;
   - what you assumed, from the conversation. The plan has no field for it.
2. **The days, in order from the first, each whole on its own.**
   - A bold line with the day and its session.
   - Each session's `before`, `during` and `after` as one short line each: its
     `example` and when, not the guidance around it.
   - Then breakfast, lunch and dinner.
   - Then the day's `snacks` as one short line: its `guidance` and its `example`.

   Each dish:
   - **Where first cooked:** its name, its batch line, one line of ingredients with
     quantities, then the plan's own numbered steps as written. The page renders
     the plan. It is not a second draft of it. A dish cooked for one sitting from
     four ingredients or fewer keeps its ingredient line and drops its steps. The
     line is the method.
   - **A leftover:** one line, pointing back, with its portions where they are not
     one.
   - **A repeat:** one line saying it is cooked fresh, as on the day it points back
     to. Never *the same pot*, which reads as keeping food for days. Add its own
     ingredient line where its pot is not the origin's. No steps.
   - **A side in `alongside`** is written the way its dish is.
   - **Anything `excluded`** prints its reason.
3. **The shopping list, last and in one block,** so it screenshots with no recipe
   in between.
   - What comes from the `fridge` first, then each aisle, named as the page names
     it (*the category is a key* in `fuelling.md`).
   - One row per item: its name and its quantity as the plan states it, and its
     `note` where it has one. That is where *check the label is gluten-free*
     lives.
   - No count of tins or packs. Only the page works that out.
   - A tinned food the recipes drain says so after its quantity: `18 oz drained`.
     No can's label says 18 oz.
   - Spaghetti or potatoes a recipe drains are weighed as bought, and say nothing.
4. **After the list:** its `closing_note`, the sentence about checking, and the
   disclaimer.

## Batch lines show their own arithmetic

Build each from the origin's `servings`, not from the meal's `note`:
*cook 3 — Wed dinner, Thu lunch, Fri lunch*.

- The number is the portions the pot holds: its sittings added up.
- A sitting that is not one portion says how many, so the numbers visibly add up:
  *cook 4 — Fri dinner (1¼), Sat dinner (1¾), Sun lunch*.
- The athlete can see every portion has a meal. That is bookkeeping they can read,
  never a check you claim.

## The sentence about checking

Step 7 of SKILL.md has three shapes for whether the plan was checked. They hold
here unchanged.

- If the check ran and only the page failed, say what it found in your own words,
  never its output, and that no printable page could be made.
- If nothing checked the plan, use the one sentence *Not checked* gives.
- It states a fact about the plan and names the reason. Never a task for the
  athlete, a file or a script name, or a claim that the plan was checked.

## An example

The `>` marks an example here. It is not how the reply is formatted. The numbers
are illustrative, and the athlete lives in Turkey. The lines before and after a
session say what goes there rather than naming a food, as in `fuelling.md`.

> **Monday — rest day**
>
> - **Breakfast: Eggs with tomatoes and peppers, with bread** — cook 1 — Mon breakfast.
>   2 eggs, 2 tomatoes, 1 green pepper, 1 tsp butter, 100 g bread.
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
> - Before: *what people in Turkey have before a ride, with amounts*, in the
>   last hour.
> - During: 2 bottles of sports drink and a bar.
> - After: *what people in Turkey have after one, with amounts*, within 2 hours.
> - **Breakfast: Eggs with tomatoes and peppers, with bread**, cooked fresh as on
>   Monday (1½ portions): 3 eggs, 3 tomatoes, 1½ green peppers, 1½ tsp butter,
>   150 g bread.
