# AGENTS.md

## Project knowledge

Durable knowledge about this project — architecture boundaries, the rationale
behind the skills' rules, invariants, domain vocabulary, open questions — lives
in an OKF knowledge bundle at [.wiki/](.wiki/). **Start at
[.wiki/index.md](.wiki/index.md)** and drill down; don't read the whole bundle.

Wiki updates land in the same commit as the change, never as a follow-up, and
that includes re-pinning a page whose text still holds: set its `source_commit`
to the branch's merge base with `main`, and check with `okf.py stale --base
origin/main`. Nothing is pinned after a merge
([why](.wiki/conventions/a-change-and-its-wiki-are-one-commit.md)).
