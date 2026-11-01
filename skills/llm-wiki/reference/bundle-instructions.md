# The bundle's own instruction file

One file written **into** the bundle by A5, `<bundle>/AGENTS.md`, so that the
rules for editing it arrive with the directory instead of having to be sought
out. Read this file when running A5; it is not needed for any other operation.

## Contents

- **Before writing it** — the collision check, which is a `lint` run and not an
  `ls`, and what to do with each kind of file it finds.
- **`<bundle>/AGENTS.md`** — the template.
- **What it reaches, and what it does not** — the ways the mechanism does not
  fire, and why a generated index cannot link it.

## Before writing it

**Check for a collision first**, and check it with `lint` rather than by eye. A
bundle that predates A5 may already hold a concept at one of these names, at any
depth and in any case — `architecture/agents.md` is an ordinary page name under
this skill's own kebab-case convention, and it stops being a concept the moment
these rules apply to it:

```sh
"$OKF/.venv/bin/python" "$OKF/okf.py" --bundle "$WIKI" lint     # read every W018
```

`ls` is the wrong instrument: the exempt names are three, not two, the match is
case-insensitive, and a collision three directories down is the likely one.
**Run `lint` before `index --write`, not in A4's order** — by the time A4's
warning prints, its own `index --write` has already dropped the page's entry.

* **A file with YAML frontmatter is a concept**, not instructions. `okf.py` skips
  these names, so it would drop out of the index, out of `stale`, and out of the
  concept count, silently. `lint` reports it as `W018`. Rename the concept and
  fix its inbound links before writing anything here.
* **A file without frontmatter is already doing this job.** Merge into it; do not
  overwrite. The template below is a starting point, not a canonical form to
  restore. What happens to a `CLAUDE.md` here depends on whether the project
  keeps its own (A5).

## `<bundle>/AGENTS.md`

````markdown
# This directory is an OKF knowledge bundle

Durable knowledge about this project: why things are the way they are, what must
hold, what words mean here, where the boundaries fall, and what bites people.
Which type each is, is `reference/concept-types.md`'s to say. A reason goes in the
`# Why` section of the page it explains; a `Decision` page is for a fork between
alternatives that no single page owns, and the user says yes to it first. **Not**
documentation of the code — the code documents itself, and a page restating it is
wrong within a week.

**Invoke the `llm-wiki` skill before writing or editing anything here.** It
carries the frontmatter contract, the concept types, the half-life rule that
decides what may be written at all, and the index and lint steps that follow
every edit. Without it you will produce a page that looks fine and is not:
missing `type`, an unpinned `sources_digest`, absent from its index. A host
without that skill follows this file directly and stays conservative: copy the
frontmatter shape of a neighbouring page, and never invent a `type`.

Reading needs no skill. Start at `index.md` and drill down; don't read the whole
bundle. If a page contradicts the code, reality wins — say so rather than reading
past it.

Three things hold either way:

- `index.md` and `log.md` are reserved names, and `AGENTS.md` (or a `CLAUDE.md`)
  is instructions. Every other `.md` here is a concept and needs a `type`.
- Every edit is followed by `okf.py index --write` and `okf.py lint`. That script
  ships with the `llm-wiki` skill. If you do not have it, say the index was not
  regenerated rather than skipping the step in silence — a stale index is exactly
  what it catches.
- A wiki change lands in the same commit as the change it describes.
````

## What it reaches, and what it does not

**Claude Code loads it on demand** (v2.1.277 or later): when its Read tool opens
a file in that directory. The docs do not say whether that includes files in its
subdirectories, where nearly every page sits, so whether one file at the bundle
root covers every concept is unverified. Other hosts that read `AGENTS.md` may load it too,
each in its own way.

Five ways it does not fire, and the last is the largest:

* A **`CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md`** in the working
  directory or above it, or in the bundle itself, turns it off under Claude
  Code's default *Project instructions* setting; `claude-md-and-agents-md` turns
  it back on.
* **Claude Code without `AGENTS.md` support**: before v2.1.277, sometimes the
  first session after upgrading to it, with its built-in AGENTS.md plugin
  disabled, or in a directory added with `--add-dir`.
* An agent that **writes a new page without reading one first** never triggers it.
* A host that does not read `AGENTS.md` gets nothing, by construction.
* **Only the Read tool is documented to trigger it**, not Edit, Write, `cat`,
  `sed` or `grep`. An agent told to prefer shell commands for file work — an
  increasingly common instruction, and the one under which a bundle is most
  likely to be edited by `sed -i` or a heredoc — may never load the file at all.
  That is the write path, which is the path this exists to close.

So it converts a rule you had to go looking for into one that arrives with the
directory. It is not a gate, and only a `PreToolUse` hook is.

**Do not link it from a generated `index.md`.** `index --write` renders indexes
from concept frontmatter, so a hand-added link to it is stripped on the next run
unless that index carries the `<!-- okf:manual -->` marker — which costs the
index its regeneration. It is reached by the host, not by navigation.
