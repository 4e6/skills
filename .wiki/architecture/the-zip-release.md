---
type: Module
title: The zip release
description: Web hosts install a skill from an uploaded zip. Each skill is released on its own when its version changes, as a zip built from the commit, and README.md's download link is both the offer and the list of skills that get one.
tags: [distribution, release, ci]
timestamp: 2026-09-30T22:05:51Z
sources: [tools/release.py, .github/workflows/release.yml, /README.md, /.gitignore]
source_commit: 6f2d1ba5595c818e020d416797ec5441e3486f45
---

# Why there is a zip at all

Claude and ChatGPT on the web take no folder, no `npx` and no symlink: a skill
is a zip the user uploads. So a third install path sits beside the two in the
README, and unlike them it is a copy that never updates itself — its owner has
to upload a new one. Everything below follows from that.

# Released per skill, when its version changes

- **Each skill is released on its own**, under the tag `<skill>-v<version>`.
  Versions are already per skill (`metadata.version`), and a commit usually
  changes one skill. A release of every skill at once would put a new zip beside
  skills that did not change, and each would ask somebody to upload again for
  nothing.
- **The version is the trigger.** On every push to `main`, CI releases each
  offered skill whose tag does not exist yet. Nobody tags by hand, and a commit
  that changes no version releases nothing.
- **A change that keeps its version does not reach the zip.** It reaches `npx`
  and the symlinks at once, and the web copy at the next version. `check` says
  so as a notice rather than failing, because a typo fix need not cost everyone
  an upload.
- **The tag carries a hyphen, not a slash**, so it is one path segment in the
  download URL.
- GitHub keeps one *latest* release for the whole repository, so with a release
  per skill, `releases/latest/download/...` would name whichever skill was
  released last. The README links each zip's own version instead.

# README.md's link is the list

A skill gets a zip exactly when README.md links one, as
`.../releases/download/<skill>-v<version>/<skill>.zip`. The link is what a
reader follows, so making it the list leaves nothing to drift from it: `check`
fails when the linked version is not the skill's own, so the commit that raises
a version also moves its link. Until CI has released it, minutes after the
merge, the new link is dead.

`z-image-turbo-macos` has no link and no zip. A web host runs skills in its own
Linux sandbox, and the skill works only on the user's Mac
([why](/architecture/z-image-turbo-macos.md)); a zip would install and then fail
every time.

`llm-wiki` has none either: it works on a project's git checkout, which a web
app's chat does not have.

# Built from the commit, not the folder

- **`git archive`, never `zip -r`.** A run made inside the checkout leaves a plan,
  its page and its photos in the skill's own folder, ignored by git
  ([each week's files](/architecture/last-weeks-plan.md)). `zip -r` would ship
  them to strangers; `git archive` takes only what is tracked. `check` compares
  the zip's files with the commit's in both directions.
- **The skill's folder is the zip's top level**, named as the skill, as Claude's
  help asks, rather than its files loose at the root.
- **Stamped with the time of the last commit that touched the skill.** Archiving
  a folder rather than a commit stamps every file with the moment it was built,
  so the same skill came out different each time. With `--mtime` an unchanged
  skill rebuilds to the same bytes. That needs git 2.45 and the whole history in
  CI, not a shallow clone.
- **Built in UTC.** Zip records a file's time in the builder's local zone, so
  the first release, built in UTC, differed by an hour on every file from the
  same zip built on a laptop in BST. The build sets the zone itself.

# What CI checks, and on what

On every pull request and every push to `main`:

- every skill, offered or not, against the specification with `agentskills
  validate` from the `skills-ref` package (it needs Python 3.11, where the
  skills need 3.9);
- every offered zip with `tools/release.py check`.

Nothing else here is checked yet: not this repository's own rules for a skill
([editing a skill](/conventions/editing-a-skill.md)), and not the tests that
stayed in the private codebase ([which copy is the
source](/questions/which-copy-is-the-source.md)). The workflow is where they
would run.

# Not verified

No zip had been uploaded to either web host when this was written. The layout
follows Claude's own help; ChatGPT's help says only that it takes a zip.

# Citations

- Claude Help Center, *How to create custom skills*: "The ZIP should contain the
  skill folder as its root (not a subfolder)." —
  <https://support.claude.com/en/articles/12512198-how-to-create-custom-skills>
- OpenAI Help Center, *Skills in ChatGPT* —
  <https://help.openai.com/en/articles/20001066-skills-in-chatgpt>
- git-archive(1), on a tree rather than a commit: "the current time is used as
  the modification time of each file in the archive."
