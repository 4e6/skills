# work-on-github-issue

An [Agent Skill](https://agentskills.io) that takes one GitHub issue to a
reviewed pull request, in any GitHub repository.

Give your assistant an issue — `#123`, `owner/repo#123` or a link — and it:

1. reads the issue and its whole thread, and checks whether work on it has
   already started;
2. works in a git worktree of its own, so several agents can share one clone;
3. writes a plan and has a fresh reviewer check it before any code is written,
   asking you only about the decisions that are yours;
4. implements and tests the change;
5. opens a pull request that closes the issue;
6. works the review — its own reviewers and your project's CI and review — until
   the change is approved;
7. hands the pull request to you. It merges only when you say so.

It follows your project's own rules where they differ — `CONTRIBUTING.md`,
`AGENTS.md`, the pull request template, what CI runs.

## Requirements

- `git`, and the [GitHub CLI](https://cli.github.com) (`gh`) signed in with
  access to the repository.
- A clone of the repository to work in.
- Reviews work best in an assistant that can start subagents; one that cannot
  reviews its own work in a separate pass.

It uses the network: it reads the issue, pushes a branch, opens a pull request
and, when it needs an answer nobody is there to give, comments on the issue.
