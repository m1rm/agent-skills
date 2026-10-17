---
name: upgrade-symfony
description: Upgrade a Symfony application from one version to another, working through the official UPGRADE and CHANGELOG files, fixing breaking changes, and committing in atomic steps. Use only when the user explicitly asks to upgrade Symfony. Plans first and waits for confirmation; does nothing beyond the upgrade itself.
argument-hint: "<from> <to>, e.g. 7.3 8.0"
---

# Symfony upgrade

The job is exactly one thing: move the project's Symfony packages from version X to version Y and keep the application working. Everything else is out of scope.

## Scope

- In scope: Symfony package constraints and the lockfile, Flex recipe updates for Symfony packages, code and config changes that a documented breaking change or a removed deprecation forces, and the minimum version bumps of other packages that Composer needs to resolve Y.
- Out of scope: unrelated dependency updates, refactoring, new Symfony features, style fixes, fixing deprecations that Y does not remove, fixing bugs you notice, and test or tooling changes that the upgrade does not need. Write them down under "Noticed, not done" in the report instead.
- If a necessary change looks like it grows beyond the upgrade (e.g. a bundle has no release that supports Y), stop and ask. Do not work around it on your own.

## 1. Examine

Read only; change nothing yet.

- Read the repository instructions. Find out how this project runs Composer and the console: a `justfile` recipe, `ddev`, a Docker wrapper, or the host. Use that wrapper for every command, never a host binary that runs a different PHP.
- Establish X from `composer.lock` (`symfony/framework-bundle`, `symfony/http-kernel`) and `extra.symfony.require` in `composer.json`. If it disagrees with what the user said, stop and ask.
- Establish Y and whether it is a minor or a major upgrade. For a major upgrade, Symfony's path goes through the last minor of the current major (e.g. 7.4 before 8.0), with deprecations fixed there. If the project is not on that minor, include the hop in the plan.
- Check the PHP version Y requires against the project's runtime and its `config.platform`.
- List every installed `symfony/*` package plus every bundle and library that requires Symfony. For each third-party package, check whether a released version supports Y.
- Collect the upgrade notes for every version between X and Y. Use the `find-docs` skill if it is installed: the `UPGRADE-<version>.md` files in the symfony/symfony repository for each minor and major in range, and the `CHANGELOG.md` of each installed component. Only read entries for components the project actually uses.
- Search the codebase (`src/`, `config/`, `templates/`, `tests/`, `bin/`, `public/`) for every API, config key, service, or behavior that those notes mark as changed or removed. Record file and line evidence for each hit. A breaking change with no hit needs no work; say so in the plan.
- Inspect `git status`. If the tree is not clean, stop and ask; do not stash, reset, or commit someone else's work.
- Identify the project's own checks (tests, static analysis, `lint:container`, `lint:yaml`, `lint:twig`, `cache:clear`) and which of them need a database.

## 2. Plan and confirm

Present the plan and stop. Do not change any file until the user confirms it.

The plan contains:

1. X, Y, the upgrade path (each hop), and the PHP requirement.
2. The constraint changes, and every non-Symfony package that must move, each with the reason Composer needs it.
3. Each breaking change that affects the project, with file/line evidence, the source (UPGRADE file or CHANGELOG entry with a link), and the intended fix.
4. The Flex recipes that will update.
5. The ordered list of commits (see below), each with its message.
6. The checks you will run after each commit, and the ones you cannot run.
7. Risks and open questions, e.g. a bundle without a compatible release.

If the user changes the plan, update it and confirm again. If new information during execution contradicts the plan, stop, explain the difference, and wait for confirmation before continuing.

## 3. Execute

Work on the current branch unless the user wants a new one; never commit on the default branch without asking. Make one commit per step, so each commit can be reviewed and reverted on its own:

1. Per hop: constraints in `composer.json` and `extra.symfony.require`, then `composer update "symfony/*"` plus only the packages named in the plan (`--with-all-dependencies` only when the plan says why). Commit `composer.json` and `composer.lock` together.
2. One commit per Flex recipe update (`composer recipes:update <package>`). Review each recipe's diff: keep the project's customizations and do not accept changes unrelated to the upgrade without asking.
3. One commit per breaking change or per closely related group (e.g. "replace removed `X` option in security config"). Do not mix unrelated fixes in one commit.

After each commit, run the confirmed checks. If a check fails because of the step you just made, fix it in that commit (amend before moving on) or in a dedicated follow-up commit. If it fails for reasons unrelated to the upgrade, report it and do not fix it.

Follow the repository's commit message convention; otherwise use Conventional Commits, e.g. `chore(deps): upgrade symfony to 8.0`. Reference the UPGRADE section in the commit body where it helps a reviewer.

Never push, open a PR, deploy, run migrations against a real database, or modify data. Never disable tests, checks, or deprecation reporting to make the upgrade pass. Never use `|| true` or `--ignore-platform-reqs`.

## Report

1. Outcome: completed, completed with open items, or blocked (and where).
2. The commits made, in order, with one line each.
3. Packages changed with exact before/after versions.
4. Breaking changes handled, with the source for each, and those that turned out not to apply.
5. Checks run with results, and checks not run.
6. Noticed, not done: everything out of scope you came across, with file references.
