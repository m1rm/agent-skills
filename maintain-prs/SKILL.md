---
name: maintain-prs
description: Bring the user's own open pull requests (GitHub) and merge requests (GitLab, incl. self-hosted) up to date, one at a time — find the ones that are behind their target branch, conflicting, or failing CI via the contribution-manager (prwatch), rebase them in the local clone, resolve conflicts, fix CI failures caused by the PR, and show the result. Never commits new work or pushes; the user reviews and pushes. Use when the user asks to maintain, update, rebase, or refresh their open PRs/MRs, or which of them need a rebase. Not for reviewing other people's PRs or opening new ones (see pull-request).
argument-hint: "optional: PR/MR URL or repository to limit the run to"
---

# Maintain PRs

The job: keep the user's open PRs/MRs mergeable without them having to check each platform. Find the PRs that need work, then handle them **strictly one at a time**: rebase onto the current target branch, resolve conflicts, fix CI failures the PR causes, verify locally, and show exactly what changed. The user decides what gets pushed.

## Hard rules

- **No pushes, ever.** Not `git push`, not `--force-with-lease`, not "update branch" buttons, not `gh`/`glab` commands that change a PR. Print the push command for the user instead.
- **No new commits.** A rebase replays the PR's existing commits; that is the only history rewrite allowed, and only after the user approved the PR (see step 3). Never `git commit`, `--amend`, squash, reword, or `git rebase -i`. CI fixes stay **uncommitted** in the working tree.
- **No outward-facing actions**: no comments, reviews, labels, re-running pipelines, or retargeting the base branch.
- **One PR at a time.** Finish a PR, show the result, and wait for the user before starting the next one. Never leave two PRs half-done.
- **Preserve the user's work.** Never `git stash`, `reset --hard`, `clean`, `checkout -- <file>`, or `rebase --skip`/`--abort` on your own. If a clone is dirty, on another operation, or the local branch differs from the PR head, stop and ask.
- Before rewriting a branch, keep a backup ref (step 4) and tell the user how to restore it.

## Tools

- The [contribution-manager](https://github.com/m1rm/contribution-manager) (`prwatch`), run through `scripts/candidates.py` (relative to this skill's directory). It runs `prwatch list --keep --json` (`--keep`: the user's "new activity" markers are not consumed) and maps each PR to local clones in the usual source directories (`~/projects`, `~/src`, `~/code`, `~/git`, `~/dev`). Override with `MAINTAIN_PRS_ROOTS` (colon-separated) and `CONTRIBUTION_MANAGER_DIR`. If prwatch is missing or too old for `--json`, stop and say so.
- `gh` for GitHub, `glab` for GitLab. Always pass the repository explicitly, including the host for anything but github.com/gitlab.com: `gh … -R owner/repo`, `glab … -R gitlab.example.org/group/project`. If `gh auth status` / `glab auth status` shows the host is not authenticated, ask the user to log in (`! glab auth login --hostname <host>`); do not work around it with tokens from `.env`.

## 1. Find candidates

```bash
python3 -I <skill-dir>/scripts/candidates.py          # human-readable
python3 -I <skill-dir>/scripts/candidates.py --json   # when you need exact fields
```

It lists PRs that are behind their target branch, conflicting, or failing CI, with the fork (`head_repo:head_branch`), target (`repo:base_branch`), CI/review state, and matching clones (remotes, whether the branch exists locally or is checked out, dirty, rebase/merge in progress). Instance errors are printed first; report them, they don't block the others.

Present the list compactly and recommend an order: conflicts and failing CI first, then the furthest behind. Mention PRs where a rebase is optional — green CI, no conflicts, and a project that squash-merges or rebases on merge — since a force-push re-triggers CI and may notify reviewers. Ask which PR to start with, or limit to the one the user named.

## 2. Pick the clone

- Exactly one clone matches and is usable → use it.
- Several match → prefer the one with the branch checked out, then the one with the local branch. Still ambiguous → ask.
- None → ask whether and where to clone the fork (`head_repo_url`); suggest the directory the user's other clones live in. If `head_repo` is empty (fork deleted), report it and skip.
- Dirty, or a rebase/merge/cherry-pick is in progress → stop and ask. Do not stash.

Read the project's contributing docs (`CONTRIBUTING*`, `.github/`, `docs/contributing*`) for rules about rebasing vs. merging, and follow them. If the project asks for merges instead of rebases, ask the user before going on.

## 3. Sync and confirm the plan

From the clone, with `<fork>` = the remote whose URL matches `head_repo_url` (`origin` usually):

```bash
git fetch <fork> <head_branch>
git fetch --no-tags <repo_url> <base_branch>        # upstream target; no remote needed
upstream=$(git rev-parse FETCH_HEAD)
```

Use an existing remote that points to `repo_url` instead of the URL if there is one.

- Local branch missing → `git switch -c <head_branch> --track <fork>/<head_branch>`.
- Local branch equal to `<fork>/<head_branch>` → `git switch <head_branch>`.
- Local branch behind the fork (someone pushed from elsewhere) → `git switch <head_branch> && git merge --ff-only <fork>/<head_branch>`.
- Local branch ahead of or diverged from the fork → **stop and ask**: there is unpushed work.
- The PR contains merge commits (`git log --merges <upstream>..HEAD`) → ask; a plain rebase would flatten them.

Then show the user: PR, clone, the PR's commits (`git log --oneline <upstream>..HEAD`), how many commits upstream gained (`git rev-list --count HEAD..<upstream>`), files both sides touched (`git diff --name-only $(git merge-base HEAD <upstream>) <upstream>` ∩ the PR's files), and whether CI needs fixing. **Wait for a go-ahead.**

## 4. Rebase

```bash
old=$(git rev-parse HEAD)
old_base=$(git merge-base HEAD <upstream>)
git update-ref refs/maintain-prs/<head_branch> "$old"     # backup; not a branch, no clutter
GIT_EDITOR=true git rebase "$upstream"
```

On conflicts, for each stopped commit:

1. Understand both sides: what the PR commit intends (`git show REBASE_HEAD`), and what upstream changed in the conflicting files (`git log --oneline <old_base>..<upstream> -- <file>`, then the relevant commits).
2. Resolve so that the PR's intent is applied on top of upstream's new code. Never drop upstream changes to make the PR apply, and never drop PR changes silently. If upstream already contains the PR's change, or the right resolution is a design decision, stop and ask.
3. `git add` the resolved files, then **show the resolution** — the conflicted files' `git diff --cached` plus a one-line explanation per hunk — and wait for approval before `GIT_EDITOR=true git rebase --continue`.

If the rebase becomes a mess, explain the state and offer `git rebase --abort`; run it only when the user agrees.

## 5. Verify locally

Find the checks CI runs (`.github/workflows/*`, `.gitlab-ci.yml`) and the project's own entry points (`justfile`, `Makefile`, `package.json` scripts, `composer.json` scripts, `tox.ini`/`noxfile.py`, `go test ./...`, `cargo test`, …). Run the lint and test steps that apply to the changed code. Prefer the project's recipes; read them first and run only ones that build, lint, or test — never deploy, publish, release, or clean recipes.

- Don't install tools, start services, or pull large toolchains without asking. Say what you could not run.
- For large monorepos, run the tests of the touched component(s) or package(s) only.

## 6. Fix CI

Only when the PR's CI is failing, or local checks fail after the rebase.

- GitHub: `gh pr checks <number> -R <repo>`, then `gh run view <run-id> --log-failed -R <repo>`.
- GitLab: pipelines of fork MRs usually run in the **fork**, so `glab ci get --merge-request` on the upstream project returns 404. Instead:
  1. `glab mr view <iid> -R <host>/<repo> -F json` → `head_pipeline.id` and `head_pipeline.web_url`; the pipeline's project is the path in `web_url` before `/-/pipelines/`.
  2. `glab ci get --pipeline-id <id> -R <host>/<pipeline-project> -F json` → jobs with `status: failed`.
  3. `glab ci trace <job-id> -R <host>/<pipeline-project>` for each failed job's log (read the tail first).

The remote CI ran on the **old** head; check whether the failure still reproduces after the rebase. Classify each failure:

- **Caused by the PR** → fix it in the working tree, keep the fix minimal and in the PR's scope, re-run the failing check. Leave it uncommitted.
- **Fixed by the rebase** (upstream fixed it) → note it; nothing to change.
- **Broken upstream / unrelated / flaky / infrastructure** (fails the same on the target branch, timeouts, runner errors) → report with evidence; do not "fix" it in this PR.

## 7. Show the result and hand over

Show, in this order:

1. What the rebase did to the PR's commits: `git range-diff <old_base>..<old> <upstream>..HEAD`. Explain any commit that changed beyond the base (conflict resolutions).
2. Uncommitted CI fixes: `git status --short` and `git diff`.
3. Checks run and results, and what was not run.
4. The commands for the user — never run them:
   - commit the fixes, if any (suggest a message; the user decides whether to commit or fold them into a PR commit),
   - push: `git push --force-with-lease=<head_branch>:<old-fork-sha> <fork> <head_branch>` (`<old-fork-sha>` = `<fork>/<head_branch>` as fetched in step 3, so a push someone else made in between is not overwritten),
   - undo: `git reset --hard refs/maintain-prs/<head_branch>` (only if the working tree has nothing to keep), and delete the backup later with `git update-ref -d refs/maintain-prs/<head_branch>`.

Then **stop** and ask whether to continue with the next PR. The next PR in the same clone needs a clean working tree, so the user commits or discards this PR's fixes first.

## Final summary

When the user ends the run, give a short table: PR, what was done (rebased / conflicts resolved / CI fixed / skipped and why), checks, and whether it is ready to push. Do not write files into the repositories.
