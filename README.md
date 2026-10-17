# skills

[Agent Skills](https://agentskills.io) from 4e6. Each one is a folder under
`skills/` with a `SKILL.md` at its top, and works in any assistant that reads
the format, except where its row says otherwise.

| Skill | What it does |
|---|---|
| [training-week-meal-plan](skills/training-week-meal-plan/) | Turns one week of endurance training, described in your own words, into a week of meals that tracks it: recipes, a shopping list by aisle, and a printable page. |
| [llm-wiki](skills/llm-wiki/) | Keeps a knowledge base for a codebase inside its repository, as an Open Knowledge Format bundle: why things are the way they are, what must hold, what words mean. Checks it for broken links, and against git for pages the code has moved past. |
| [supervise-work](skills/supervise-work/) | Supervises any task bigger than a quick answer, or a GitHub issue, through research, plan, build and review, with fresh subagents and reviewers, and delivers what was asked for: findings, a plan, a merged change, or work run. Say "supervise work on …" to watch and steer it as it goes. |
| [z-image-turbo-macos](skills/z-image-turbo-macos/) | Generates images from text prompts on your own Apple Silicon Mac, with one model — Z-Image Turbo — on the Mac's GPU. Offline after a one-time setup of about 12 GB; Apple Silicon only. |
| [session-review](plugins/session-review/skills/session-review/) | **Claude Code only.** Reads your past Claude Code sessions and suggests, with evidence, how to improve your everyday work: skills to fix, habits to automate, preferences to write down. Applies nothing. A plugin, installed from the marketplace below. |
| [session-watch](plugins/session-watch/) | **Claude Code only, interactive sessions.** The live counterpart of session-review: when your session goes idle, a small model reads the new part and shows you, in the terminal, what could be improved. Off by default; shown to you, not sent to Claude (the lines are also saved in the session's transcript file); applies nothing. A plugin. |

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

### Claude Code plugins

`session-review` and `session-watch` work only in Claude Code, and are plugins. In Claude Code:

```
/plugin marketplace add 4e6/skills
/plugin install session-review@4e6
```

The `ln -s skills/*` route above does not include it, and there is no zip of
it. `npx skills` lists it too, and installs it as a plain skill, which only
Claude Code can use. Update it in a terminal with `claude plugin marketplace update 4e6` and
`claude plugin update session-review@4e6`, then restart Claude Code.

`session-watch` is in the same marketplace and is **off until you enable it**:

```
/plugin install session-watch@4e6
/plugin enable session-watch@4e6
claude plugin enable session-watch@4e6 --scope local    # or project, or user
```

Enabling persists in the scope you choose, so it runs in every new interactive
session there until `/plugin disable session-watch@4e6`. Each line it shows is
also saved in the session's transcript file as a system notice that Claude is not
sent (checked on Claude Code 2.1.296, in an interactive session and on resume);
the mod writes no files of its own. See
[its README](plugins/session-watch/README.md).

### In Claude or ChatGPT on the web

The web apps install a skill from a zip you upload. Download it here:

- [training-week-meal-plan.zip](https://github.com/4e6/skills/releases/download/training-week-meal-plan-v1.11.0/training-week-meal-plan.zip)

and upload it as the app's own help describes:
[Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude),
[ChatGPT](https://help.openai.com/en/articles/20001066-skills-in-chatgpt).
Upload the zip as it is; it holds the skill's folder, which is what both expect.

An uploaded skill does not update itself. Each new version is a
[release](https://github.com/4e6/skills/releases) with its own zip; to take it,
upload that zip in place of the old one. A version is three numbers: the last
moving alone is a fix, the middle one a change you would notice, the first one
something that stops working as it did.

## Licence

MIT — see [LICENSE](LICENSE). Each skill carries its own copy, so the licence
travels with it when it is installed on its own.
