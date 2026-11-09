---
name: github-fork-sync
description: Sync the user's GitHub forks with their upstream (parent) repositories on GitHub itself — find every fork that is behind, show the plan, and after confirmation fast-forward each fork's branch with `gh repo sync`. Fast-forward only; diverged forks, renamed default branches and inaccessible parents are reported, never forced. Works on the remote forks only; local clones are not touched. Use when the user asks to sync, update, or refresh their GitHub forks, or which forks are behind upstream. Not for GitLab, and not for updating PR branches (see maintain-prs).
argument-hint: "optional: fork (owner/name), owner/org, or GitHub Enterprise host"
---

# GitHub fork sync

The job: bring the user's forks on GitHub up to date with their parents, without ever losing a commit in a fork. Only forks whose branch is strictly **behind** its parent are synced; everything else is reported with what the user could do about it.

## Rules

- **Fast-forward only.** Never `gh repo sync --force`, never `--source`, never a hard reset, never the merge-upstream API on a fork that is ahead or diverged — that would create a merge commit or discard the fork's commits.
- **Confirm before writing.** Syncing pushes to the user's fork. Show the plan first and sync only the forks the user approved.
- **Remote only.** Don't touch local clones, other branches, PRs, or repository settings (renaming default branches, unarchiving, deleting forks).
- **Re-check right before each sync.** Time passes between plan and sync; a fork that is no longer strictly behind is skipped and reported.

## Tools

- `gh`, authenticated for the host (`gh auth status`). If it is not logged in, ask the user to run `! gh auth login` (add `--hostname <host>` for GitHub Enterprise Server).
- `scripts/fork-status.py` (relative to this skill's directory), read-only. It checks each fork separately, so one inaccessible parent doesn't hide the others:

```bash
python3 -I <skill-dir>/scripts/fork-status.py                     # all forks of the authenticated user
python3 -I <skill-dir>/scripts/fork-status.py --owner <org>       # forks owned by an organization
python3 -I <skill-dir>/scripts/fork-status.py --hostname <host>   # GitHub Enterprise Server
python3 -I <skill-dir>/scripts/fork-status.py --repo <owner/name> --json   # one fork, exact fields
```

The compared branch is the **parent's default branch** — the branch `gh repo sync` updates — against the fork's branch of the same name.

## 1. Status

Run the script and present the result grouped by status:

| Status | Meaning | Action |
|---|---|---|
| `behind` | only the parent has new commits | sync (after confirmation) |
| `up-to-date` | identical | none |
| `ahead` | only the fork has extra commits | none; nothing to bring in |
| `diverged` | both sides have commits | report; don't sync (see 3) |
| `missing-branch` | fork has no branch named like the parent's default | report; don't sync (see 3) |
| `archived` | fork is read-only | report |
| `error` | fork or parent unreadable | report the message as is (see 3) |

For `behind` forks, show how many commits behind. If the user wants details for one, list what comes in (the compare API's `commits` are those in the second ref but not the first):

```bash
gh api 'repos/<parent>/compare/<fork-owner>:<branch>...<branch>' --jq '.commits[].commit.message | split("\n")[0]'
```

Ask which `behind` forks to sync: all, a selection, or none.

## 2. Sync

One fork at a time, for each approved fork:

```bash
python3 -I <skill-dir>/scripts/fork-status.py --repo <fork> --json   # must still be "behind"
gh repo sync <fork> --branch <branch> --hostname <host>              # omit --hostname for github.com
python3 -I <skill-dir>/scripts/fork-status.py --repo <fork> --json   # must now be "up-to-date"
```

- If the re-check is no longer `behind`, skip the fork and say why.
- If `gh repo sync` fails, report the error and continue with the next fork. Common causes: the token lacks write access to the fork's contents (fine-grained tokens need **Contents: Read and write** on the fork), or the branch is protected in the fork. Do not retry with other flags.
- If the post-check isn't `up-to-date`, report the actual state.

## 3. What the user can do about the rest

Explain, don't act:

- **diverged**: the fork's branch has its own commits. Show the fork's own commits with `gh api 'repos/<parent>/compare/<branch>...<fork-owner>:<branch>' --jq '.commits[].commit.message | split("\n")[0]'` (swap the refs for the parent's new commits). Options for the user: move that work to a feature branch and then sync with `--force` themselves, or merge upstream in a local clone and push. Name the data loss of `--force` explicitly.
- **missing-branch**: the parent renamed its default branch (e.g. `master` → `main`). The user can rename the fork's branch in the fork's settings, or create the new branch from the parent's; after that, sync works.
- **error** with an org policy or SSO message (e.g. fine-grained token lifetime, SAML authorization): the token isn't allowed to read that org's repository. Point to the URL in the message; nothing else to do here.
- **archived**: unarchive it on GitHub first if it should be kept in sync.

## Report

End with a short summary: synced forks (with commits pulled in), skipped forks and why, and the forks that need the user's attention. Local clones are still on their old state; mention that `git pull` in a clone picks up the sync.
