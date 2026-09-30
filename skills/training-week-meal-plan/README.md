# training-week-meal-plan

An [Agent Skill](https://agentskills.io) that turns one week of endurance
training — described in your own words — into a week of meals that tracks it.

Hard days get the carbohydrate. Easy days do not. Every portion you cook is
assigned to a meal that eats it, so nothing is cooked to be thrown away, and the
shopping list is grouped by where things sit in the shop rather than by what they
do.

## What you get

- **Every day from the first you need through to Sunday** — the rest of this
  week, or all of next — breakfast, lunch and dinner, plus in-session and
  post-session fuel on the days that need it.
- **Recipes with quantities** — 4–8 ingredients, 3–7 steps, written as a kitchen
  reference rather than a cookbook.
- **A shopping list** grouped by aisle, with each item tagged with the days that
  use it.
- **Leftovers accounted for**: cook two, eat one, and the plan says which day the
  other one is for.
- **A printable page** — one self-contained HTML file, handed to you as a private
  page or a file where your client can do that, and otherwise opened in your
  browser or pointed at, and printed with Cmd-P. Nothing to install, and laid
  out so the recipes sit under the day that cooks them, no recipe is split across
  a page, and the shopping list can be torn off.

## What it asks you for

Two things, and it will not invent either:

- **your training week, in your own words** — paste a coach's week, or describe
  it roughly. Hours, zones or a planned load score against each session make the
  plan sharper, if you have them. If you have no week to give, say so and it
  plans easy days and says on the plan that it did — it will not invent a
  week for you;
- **your body weight**, which is what the carbohydrate targets are built from.
  There is no fallback for this one.

Three it will use if you offer them: dietary restrictions, what is already in
your fridge, and where you live — which chooses the dishes and names the shops.

## Requirements

**Python 3.9 or newer**, which macOS and every Linux already have — and it is
optional. It buys three things: the checks over the finished plan, which are the
arithmetic that makes sure every portion cooked gets eaten and every ingredient
a recipe uses is on the shopping list; the printable page; and a look at last
week's plan, if it is in the same folder, so this week's lunches and dinners
differ from it. Nothing else: the rest of the skill is instructions and a JSON
schema. Its scripts never go online, and there are no API keys and no accounts.
Where your assistant can publish the page, it hands it over that way, kept
private.

Without Python the plan is still written — into the reply itself, since there is
no page to open. It just is not checked and there is nothing to print, and the
skill says so when it hands the plan over rather than leaving you to assume.

## Licence

MIT — see [LICENSE](LICENSE).

**This is general sports-nutrition guidance, not medical or dietetic advice.** It
is not for anyone managing a clinical condition or an eating disorder.
