---
type: Convention
title: A change and its wiki are one commit
description: A PR changes the code and every page it touches in one squashed commit, and pins each page to the content of its sources, so nothing is pinned after a merge.
tags: [process, wiki]
sources: [AGENTS.md, skills/llm-wiki/scripts/okf.py]
sources_digest: 2010d656102cd1f9
---

# The rule

A change lands as one commit with every wiki page it touches, PRs squashed on
merge. That covers a page whose text still holds, too: the review of it is
recorded in the same PR by pinning it (`okf.py pin <page>`) after the change's
last edit to its sources. Nothing is pinned after a merge.

# Why the pin is content, not a commit

A page used to be pinned by `source_commit`, and `stale` called it stale
whenever its sources changed after that commit. Two fixes in turn failed the
same way, because a commit hash is a name for history and a squash merge, a
rebase and a shallow clone each rewrite or cut off history:

- **A pin written in the PR names a commit that exists only before the merge.** A
  squash gives the change a new hash, so every merged PR left its pages stale
  until a second commit to main pinned them. Every PR from #8 to #24 was followed
  by one, touching up to 20 pages, nearly all for the pin alone.
- **The fix that followed pinned the branch's merge base and skipped a commit that
  changed the page along with its sources.** It worked, but only through that
  exemption: any edit to the page in the same PR, a typo included, vouched for
  every unread change to its sources, and a pin to a branch's own commit was
  `S006` after the squash. Dates went the same way. A timestamp kept by hand was
  rewritten by the squash like the hash beside it, and one derived from git is
  the merge time.

`sources_digest` is a digest of the content of the files `sources` matches. It
is the same on main as on the branch whenever those files are the same, so the
squash, a rebase and a shallow clone leave it alone, and no commit follows the
merge. The tests that showed this ran a two-commit branch squashed after main
had moved, a rebase onto a moved main, a shallow clone, and a checkout with
CRLF line endings: all clean.

# What follows

- **Pin last.** The digest is of the sources on disk, so pin after the final edit
  to them; a source edited after the pin is stale again. The page may be edited
  afterwards. A file the change adds counts before it is staged: the digest sees
  what `git add .` would, so the pin needs no `git add` first and does not flip
  when the file is added.
- **Pin only what was read.** `pin` takes pages by name and has no "all" form;
  the one bulk form, `--migrate`, converts only pages that are current under the
  old commit pin. A pin is the statement that the sources were read and the page
  is right about them.
- **A page is reviewed before the PR merges.** Run `stale` once the change is
  made; it lists every page whose sources differ from what it was pinned at. Each
  is rewritten or re-pinned in the same PR.
- **A broad glob is stale whenever anything under it changes.** Main changing an
  unrelated file inside a page's `sources` flags the page, and so does main
  changing the same file as the branch. The first is why `sources` names the
  files a page depends on; the second is correct, since the pin on the branch
  predates what main did.
- **The timestamp is gone.** A hand-kept date was wrong as soon as the page was
  merged; `git log -1 --format=%cI -- <page>` says when it last changed, and
  nothing here requires the field.
- **Pages pinned the old way still work**, by the commits after `source_commit`,
  and `lint` says `W022` until `pin --migrate` or a pin by name moves them. This
  repository's pages were all moved in one commit. A branch merged with a merge
  commit or a rebase is not a special case any more: the digest does not read it.
