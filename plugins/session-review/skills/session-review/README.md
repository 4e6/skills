# session-review

A [Claude Code](https://code.claude.com) plugin with one skill that reads your
past Claude Code sessions and suggests how to improve your everyday work: skills
to fix, habits to automate, preferences to write down, permissions to allow.
The strongest suggestions come with what happened, one quoted instance, whether
the file they would change already covers it, and the change itself; the rest
come with what happened, in a line, and the places that back it. It applies
nothing; you choose what to act on.

It works **only in Claude Code**. It reads the transcripts Claude Code keeps in
`~/.claude/projects`, which no other assistant has.

## What it looks for

Where the agent got confused, circled, skipped a step, or built something other
than what was planned; where you corrected it or stopped it; where a skill was
loaded and then not followed; sequences you do by hand again and again; and
permission prompts and denials. One occurrence is a note. The same thing in more
than one session is a suggestion, routed to where it belongs: a skill change, a
line in your global instructions, a fact for a project's wiki, a new script or
hook, or a permission rule.

## Install

In Claude Code:

```
/plugin marketplace add 4e6/skills
/plugin install session-review@4e6
```

Then ask, for example, "review my last 30 days of sessions in this project", or
run `/session-review:session-review`.

Linking the repository's `skills/*` does not include it, as it lives under
`plugins/`. `npx skills add 4e6/skills` does list it and installs it as a plain
skill, which works the same in Claude Code.

## Requirements

- Claude Code.
- Python 3, for the script that condenses a transcript. It uses the standard
  library only.
- Subagents, preferably: the skill reads each session in its own, on a small
  model. Without them it does the same passes itself.

## Privacy

It reads your transcripts on your machine, and a script cuts them down and
redacts keys, tokens and passwords it recognises. The condensed text goes only to
your own session's model, through subagents. The skill posts nothing anywhere and
deletes its working files when it is done. Redaction is pattern-based: it is not a
guarantee, so read the report before you share any of it.

## Updating

```
claude plugin marketplace update 4e6
claude plugin update session-review@4e6
```

Run them in a terminal, then restart Claude Code to apply the update.

Claude Code does not update third-party marketplaces by itself unless you turn
that on for this one.

## Licence

MIT — see [LICENSE](LICENSE).
