# skills

[Agent Skills](https://agentskills.io) from 4e6. Each one is a folder under
`skills/` with a `SKILL.md` at its top, and works in any assistant that reads
the format.

| Skill | What it does |
|---|---|
| [training-week-meal-plan](skills/training-week-meal-plan/) | Turns one week of endurance training, described in your own words, into a week of meals that tracks it: recipes, a shopping list by aisle, and a printable page. |

## Installing

With the [`skills`](https://github.com/vercel-labs/skills) CLI:

```sh
npx skills add 4e6/skills
```

Or by hand: copy the skill's folder into your assistant's skills directory —
for Claude Code, `~/.claude/skills/`:

```sh
git clone https://github.com/4e6/skills
cp -r skills/skills/training-week-meal-plan ~/.claude/skills/
```

Keep the folder's name as it is. The format requires it to match the skill's
`name`.

## Licence

Each skill carries its own `LICENSE`.
