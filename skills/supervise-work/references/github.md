# GitHub: an issue, a pull request

GitHub is where the work is read, recorded and delivered. For a change, a merged
pull request is the finish line; findings and plans go on the issue. Needs `git` and the GitHub CLI (`gh`), signed in with
access to the repository. The parts about an issue apply only when there is one:
a change made without an issue is still delivered as a pull request.

## Contents

- The issue
- A pull request you were handed
- The worktree
- The plan goes on the issue
- Implement
- The pull request
- Merge and clean up

## The issue

The input is one issue: a number in the current repository, `owner/repo#123`, or
a URL. Without one, there is nothing to work on: say so and stop. The work happens in a
clone of the issue's repository; for an issue elsewhere, find or make that clone
first.

Read the **whole** thread, not just the description: later comments often answer
a question and change the scope in the same breath, and earlier work may have
left a plan or findings there. Follow the issues and pull requests it links to.

Check whether the work has already started: a pull request for the issue, a
branch, an assignee. If it has, continue that work rather than starting over; if
someone else looks to be actively on it, say so on the issue and leave their
branch alone. A closed issue is not worked: say so and stop.

Then state the issue in your own words: what is wrong or missing, and what will
be true when it is done. If you cannot, the issue is underspecified: post the
question on the issue and stop, since there is nothing to build on.

## A pull request you were handed

Work on its branch and do not open a second pull request: skip opening one, and
put the plan in its description or a comment, or on its issue if it has one. Read its description, every review
comment and the state of its checks before the code. The reviews on it are
findings to answer, as below.

## The worktree

To continue an existing branch, look first for a worktree an earlier session left
on it: git will not check a branch out in a second worktree, and the old one is
where to carry on. A pull request from a fork has its branch on the fork, not on
`origin`; check it out through the pull request.

## The plan goes on the issue

If there is an issue, post the final plan as a comment on it. The thread is where
the next person to work on or investigate this code will look, long after this
session and its reasoning are gone; the plan tells them what was found, what was
chosen and what was ruled out. Decisions that are the user's go in it by name.
When the build shows the plan to be wrong, post what changed and why.

## Implement

Commit in steps that each make sense on their own, in the project's commit style.
Run what CI runs — tests, linters, type checks — and check the behaviour the
task describes, not only the unit tests. Unrelated problems you find are a note
in the pull request or a new issue.

Push the branch early, unless the ask says to keep it local: work that lives only in a local worktree is invisible to
everyone else, and is lost with the session. Without push access to the
repository, push to a fork. Give the fork's remote a name of its own: by default
`gh` renames the clone's `origin` to make room for the fork, and remotes are
shared by every worktree of the clone.

## The pull request

Have the change reviewed before opening it; this review is cheap, and the
project's CI and reviewers are not. Open it, filling in the project's template if
it has one. The body says what changed and why, the decisions made and the
alternatives rejected, how it was verified, and, if there is an issue,
`Closes #<n>`.

Wait for the checks. They can take a minute to be reported after the pull
request opens, so none yet is not the same as none at all; a repository with no CI
has none to wait for. Checks that wait on a maintainer — a project may hold a
fork's workflow runs until one approves them — will not arrive on their own. That
is not the same as no CI: run the same commands locally, finish what does not
depend on them, and **do not merge on local results alone**. Stop before the
merge and say that CI has not run and what would unlock it.

Answer every finding — from the checks, from your reviewer, and from any human or
bot review that has arrived — by fixing it or by replying with a reason. Do not
wait for a maintainer's approval unless the project requires one to merge; then
the run stops there, and says so.

## Merge and clean up

Merge when step 6's conditions hold, the way the project merges. If the merge is
refused — a protected branch, a required human review — stop and say what refused
it and what would unlock it.

Once merged, remove what the work left behind: the worktree, its branch, locally
and on the remote it was pushed to (unless the project's merge already deletes it),
and every other worktree or branch made along
the way, such as a subagent's or a branch for an abandoned approach. Leave alone
what this work did not make: other agents share the clone.

After a squash or rebase merge, git sees the branch as unmerged and refuses a
plain delete. The merged pull request is the proof: once its last commit is the
branch's last commit, so nothing local was left unpushed, force the delete. Do not
remove a worktree with uncommitted changes until you have seen what they are.
Leave the worktree before removing it if the session is in it, and leave the
original checkout as you found it.

Tell the user the pull request's link, and, if the run stopped short of the merge,
the worktree's path, which can be removed once the pull request is merged or
closed. If the work turned up something the next person would want and the code
does not say — a dead end, a surprising cause, a follow-up — add it to the issue,
or to the pull request if there is none.
