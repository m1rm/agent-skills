---
name: symfony-contributor
description: Contribute code to the symfony/symfony repository the way Symfony's contribution guidelines require. Finds issues nobody is working on, picks the right base branch, implements with tests, CHANGELOG/UPGRADE entries, the BC promise and coding standards, drafts the PR title and Q/A table, and tells CI failures caused by the PR from those already broken on the base branch. Use whenever the user works in a clone or fork of symfony/symfony, or asks about contributing to Symfony, Symfony good first issues, a Symfony pull request, Fabbot, or failing Symfony CI, even without saying "contribute". Not for applications that only use Symfony (see upgrade-symfony, fix-symfony-deprecations) or for symfony-docs.
argument-hint: "optional: issue number, PR number, or phase (find, implement, pr, ci)"
---

# Symfony contributor

The job is to help the user get a change into symfony/symfony that reviewers can merge without extra rounds: the right branch, tests, the files Symfony expects to be updated, and a PR that passes the automated checks. The rules come from Symfony's official contributing docs and its CI. The details live in [references/guidelines.md](references/guidelines.md); read the relevant section before deciding on a branch, a BC question, a deprecation, a CHANGELOG entry, or the PR text.

Version numbers, labels, and checks change with every release. Read them from the fetched repository or the live source (`gh`, the docs), never from memory.

The scripts in `scripts/` (relative to this skill's directory) need an authenticated `gh` CLI; they use its built-in `--jq`, so `jq` itself isn't required.

## Scope

- In scope: code contributions to symfony/symfony (components, bridges, bundles, contracts): finding an issue, implementing, preparing the PR, and triaging CI.
- Out of scope:
  - **Security issues.** Never discuss them in public issues or PRs; point the user to https://symfony.com/doc/current/contributing/code/security.html.
  - **Translations**, unless the user is fluent in the language. Symfony doesn't accept machine translations.
  - symfony-docs, and applications that only use Symfony.
- Outward-facing actions are the user's: commenting on issues, pushing, opening or editing a PR. Draft the text and give the exact command; do it yourself only when the user explicitly asks for that action.
- Match the user's level: explain Symfony-specific rules and git operations briefly when they seem new to them.

## 0. Orient

Do this before any phase.

- `git remote -v`: usually `origin` is the user's fork. If there is no `upstream`, use `gh ... -R symfony/symfony` for reads and suggest `git remote add upstream https://github.com/symfony/symfony.git`.
- Learn the current branches: the repository's default branch is the development branch (`gh api repos/symfony/symfony --jq .default_branch`). After fetching it, read the `Branch?` row of its PR template (`git show upstream/<default>:.github/PULL_REQUEST_TEMPLATE.md`), which also lists the maintained bug-fix branches.
- If the user works from their fork's branches, check that they match upstream: compare `git rev-parse origin/<branch>` with `gh api repos/symfony/symfony/commits/<branch> --jq .sha`.
- `git status`: if the tree is not clean, ask before doing anything that touches it.

## 1. Find an issue

- Run `scripts/find-issues.sh` (default label "Good first issue"), and `scripts/find-issues.sh "Help wanted"`. Extra GitHub search terms narrow it, e.g. `-label:"Missing translations"` or `label:Console`. It lists each open issue with its assignees, comment count, and every linked PR with its state.
- For each candidate, read the issue and its latest comments (`gh issue view <n> -R symfony/symfony --comments`) and judge:
  - **Linked PR open or merged**: taken, skip it. **Closed without merge**: still open, but read why it was closed before starting.
  - **Someone asked to work on it**: check the date and whether a PR followed. A claim with no PR after a few weeks is usually fair game; mention it when claiming.
  - **Labels**: `RFC` means there is no decision yet; `Missing translations` needs a native speaker; `Keep open` only stops the stale bot.
  - **Fit**: prefer a clear scope, a maintainer saying "contributions welcome", and an existing pattern in the code to follow.
- Present a short table (issue, component, status, fit) and recommend one.
- Claiming: draft a two-line comment asking whether anyone is working on it and saying what the user plans to do. Maintainers react to PRs more than to claims, so don't wait long for an answer before opening the PR.

## 2. Branch

- Bug fix: the oldest maintained branch with the bug. Feature or deprecation: the development branch. See "Branches" and "What a bug fix may change" in the guidelines; a bug fix that needs a new public method or config option is a feature.
- Create a topic branch from the freshly fetched base: `git switch -c <name> upstream/<base>` (or `origin/<base>` once verified identical). Use a descriptive name, e.g. `fix_12345` or `twig-lint-junit-format`.

## 3. Implement

- Read the code you change, its tests, and how sibling code does the same thing (e.g. other output formats of the same command). Match the existing style and patterns.
- Keep the diff to the change: no drive-by refactoring or style fixes in other files.
- Tests: add tests that prove the fix or the feature. Test methods have no return type.
- Run the relevant tests: `composer update` once at the repository root, then `./phpunit src/Symfony/<Type>/<Name>/` (or a single test file). If Composer fails only because PHP extensions are missing locally, `--ignore-platform-req=ext-<name>` for exactly those extensions is acceptable for a local run (`vendor/` is not committed); name them to the user. If dependencies don't resolve, try `COMPOSER_ROOT_VERSION=<base>.x-dev composer update`.
- Coding standards: PHP-CS-Fixer handles formatting; check the rules it doesn't (exception messages, Yoda conditions, no `else` after `return`, and so on) in the guidelines. Run PHP-CS-Fixer on the changed files if it is installed (`php-cs-fixer fix --dry-run --diff <files>`); otherwise say so, since Fabbot will check it.
- BC promise and deprecations: follow the guidelines exactly; a deprecation needs the PHPDoc, `trigger_deprecation()`, the CHANGELOG, and both UPGRADE files in the same PR.
- CHANGELOG: features and deprecations get an entry in the component's `CHANGELOG.md` under the development version. Check the file's recent history for where entries go.
- Commit: `[Component] Capitalized imperative subject` without a trailing period, with an author email linked to the user's GitHub account.
- To try a console command by hand, the monorepo has no `bin/console`. Write a small script outside the repository that requires `<repo>/vendor/autoload.php`, builds the service the command needs, and registers it with `new Application()` + `addCommand()`. Use realistic fixtures and show the user the actual output, including the exit code.

## 4. Pull request

- Before opening: rebase onto the freshly fetched base (`git fetch upstream && git rebase upstream/<base>`), re-run the tests, and check that `git diff upstream/<base>...HEAD --stat` contains only the intended files.
- Draft the title and body following "Pull request title and body" in the guidelines: `[Component] Description` title, the template table with its exact row labels, `Fix #NNN` in the `Issues` row, then what and why, an example, before/after if behavior changes, and notes for reviewers on trade-offs and alternatives. Print it for the user to copy.
- Check the draft against Fabbot's title regex (it isn't anchored: `prefix:` fails too) and the `| License | MIT` row.
- Pushing after a rebase or amend needs `git push --force-with-lease origin <branch>`. If git says the branch is "behind" its remote after you rewrote history, that's the old version of the same commits: tell the user not to `git pull`, because that would create a merge commit, which Fabbot rejects.
- Open the PR against `symfony/symfony` and the chosen base branch, not the fork.
- Fabbot doesn't re-run when only the title or body changes. If it failed on the title, fix the title and then push something (e.g. reword the commit) to trigger a new run.

## 5. CI triage

- Run `scripts/ci-triage.sh <pr-number>`. For each failed job it prints the failed step, the failure annotations, how often the same job failed at the same step in the last base-branch push runs, and whether a failing package (`KO <path>`) is one the PR touches.
- Treat its output as hints and confirm:
  - **Fails at the same step on the base branch**: read one base log (`gh run view <run> -R symfony/symfony --log-failed`) and check that it's the same error. If it is, the PR didn't cause it. Say so to the user and leave it; the maintainers see the same failure on every PR.
  - **Setup step** (installing packages, services): usually infrastructure. Suggest a re-run before investigating.
  - **Fails only on the PR, in a package the PR touches**: it is probably real. Reproduce locally with the same PHP version and dependency mode if possible, fix, and push.
  - **Fabbot**: find the failing check in the table in the guidelines and apply its fix.
- Logs are only available once the whole workflow run has finished. Until then, use the annotations.
- Static analysis comments: review them; never update baselines or add `@phpstan-` or `@psalm-` annotations to silence them.

## Report

Close every phase with:

1. What was done, with file references and commit hashes.
2. Verification: tests run and their result, checks not run and why.
3. Commands or text the user still has to run or post (push, PR, comments), ready to copy.
4. Open questions or decisions that belong to the user or the reviewers.
5. Sources for every rule you applied that the user might want to cite in the PR (docs links, CI logs).
