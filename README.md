# skills

[Agent Skills](https://agentskills.io) from 4e6. Each one is a folder under
`skills/` with a `SKILL.md` at its top, and works in any assistant that reads
the format.

| Skill | What it does |
|---|---|
| [training-week-meal-plan](skills/training-week-meal-plan/) | Turns one week of endurance training, described in your own words, into a week of meals that tracks it: recipes, a shopping list by aisle, and a printable page. |
| [z-image-turbo-macos](skills/z-image-turbo-macos/) | Generates images from text prompts on your own Apple Silicon Mac, with one model — Z-Image Turbo — on the Mac's GPU. Offline after a one-time setup of about 12 GB; Apple Silicon only. |

## Installing

With the [`skills`](https://github.com/vercel-labs/skills) CLI:

```sh
npx skills add 4e6/skills                                    # every skill
npx skills add 4e6/skills --list                             # see what is here
npx skills add 4e6/skills --skill training-week-meal-plan    # just this one
```

It installs into the project you run it in; add `-g` to install for your user
instead — for Claude Code, `~/.claude/skills/`.

Or by hand: link each skill's folder into your assistant's skills directory —
for Claude Code, `~/.claude/skills/`:

```sh
git clone https://github.com/4e6/skills
cd skills
mkdir -p ~/.claude/skills
ln -s "$PWD"/skills/* ~/.claude/skills/
```

Each skill gets its own link, so the skills you already have stay where they
are, and a `git pull` updates the linked skills in place. Run the `ln` again when
a new skill appears; the ones already linked answer `File exists` and are left
alone. To pick one skill rather than all of them, link that folder alone, or
copy it with `cp -r`.

Keep each folder's name as it is. The format requires it to match the skill's
`name`.

### In Claude or ChatGPT on the web

The web apps install a skill from a zip you upload. Download it here:

- [training-week-meal-plan.zip](https://github.com/4e6/skills/releases/download/training-week-meal-plan-v1.0/training-week-meal-plan.zip)

and upload it as the app's own help describes:
[Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude),
[ChatGPT](https://help.openai.com/en/articles/20001066-skills-in-chatgpt).
Upload the zip as it is; it holds the skill's folder, which is what both expect.

An uploaded skill does not update itself. Each new version is a
[release](https://github.com/4e6/skills/releases) with its own zip; to take it,
upload that zip in place of the old one.

## Licence

MIT — see [LICENSE](LICENSE). Each skill carries its own copy, so the licence
travels with it when it is installed on its own.
