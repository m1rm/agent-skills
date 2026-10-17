---
name: fix-symfony-deprecations
description: Find and fix Symfony deprecations triggered by a project's own code and config, using Symfony AI Mate when it is installed. Use when the user asks to fix, clean up, or reduce Symfony deprecations. Plans first and waits for confirmation; fixes deprecations and nothing else.
argument-hint: "optional: component, path, or target version to focus on"
---

# Fix Symfony deprecations

The job is to remove Symfony deprecation notices that the project's own code, config, and templates cause, without changing behavior. Everything else is out of scope.

## Scope

- In scope: Symfony deprecations (`symfony/*` packages) triggered by code in `src/`, `config/`, `templates/`, `tests/`, `bin/`, or `public/`.
- Out of scope: deprecations from Doctrine, Twig, PHPUnit, or other libraries (report them); deprecations raised inside a third-party bundle (report them, do not upgrade the bundle); dependency updates; refactoring; new features; style fixes; bugs you notice. Write them down under "Noticed, not done" in the report.
- If the user names a component, path, or target version, narrow the scope to it.
- If a fix needs a dependency change or a larger redesign, stop and ask. Do not do it on your own.

## 1. Check for Symfony AI Mate

- Look for `symfony/ai-mate` in `composer.json` and for `vendor/bin/mate`. Read the repository instructions (`AGENTS.md`, `CLAUDE.md`, `mate/AGENT_INSTRUCTIONS.md`) for how to run it, e.g. through a `justfile` recipe or a container.
- If Mate is installed, list its tools (`tools:list`) and inspect the ones you will use (`tools:inspect <tool>`). Use the log tools to search the `php` and `deprecation` channels for deprecation entries, and the profiler tools for deprecations collected per request. Do not assume tool names; use what the listing shows.
- If Mate is not installed, tell the user what it adds (measured deprecations from logs and the profiler instead of guesses from reading code) and ask whether to install it. Install only on a clear yes: look up the current install steps with the `find-docs` skill, run them with the project's Composer wrapper, and commit the installation on its own before any deprecation fix. If the user says no, continue without it.

## 2. Examine

Read only; change nothing yet.

- Find out how this project runs Composer, the console, and tests, and use that wrapper for every command.
- Establish the installed Symfony version from `composer.lock`.
- Collect deprecations from every source available. Do not install tools other than Mate for this:
  - Mate log and profiler tools, if present.
  - The test suite through `symfony/phpunit-bridge` (`SYMFONY_DEPRECATIONS_HELPER`) or PHPUnit's deprecation output, if the project has it configured. Running tests that touch a database needs the user's agreement in the plan.
  - `bin/console debug:container --deprecations`, `lint:container`, `lint:yaml`, `lint:twig`, and `cache:clear` output.
  - Deprecation entries in `var/log/*.log`, if they exist.
  - Static analysis deprecation rules, only if already installed.
- Group what you find by deprecation message. For each group, record the source (file and line in project code), how many times it fires, which Symfony version deprecated it, and the documented replacement from the component's `UPGRADE` or `CHANGELOG` file. Discard entries whose trigger is outside project code; note them for the report.
- Inspect `git status`. If the tree is not clean, stop and ask; do not stash, reset, or commit someone else's work.

## 3. Plan and confirm

Present the plan and stop. Do not change any file until the user confirms it.

The plan contains:

1. Which collection sources you used, and which were unavailable.
2. Each deprecation group: message, locations, the documented replacement with its source link, and the intended fix.
3. The ordered list of commits, one per deprecation group, each with its message.
4. The checks you will run after each commit, and the ones you cannot run.
5. Deprecations you will not fix and why (third-party, needs a dependency change, unclear replacement).

If the user changes the plan, update it and confirm again. If new information during execution contradicts the plan, stop, explain the difference, and wait for confirmation before continuing.

## 4. Execute

- Work on the current branch unless the user wants a new one; never commit on the default branch without asking.
- One commit per deprecation group, so each one can be reviewed and reverted on its own. Do not mix in other changes.
- Use the documented replacement. Do not silence a deprecation (`@`, error handler tweaks, baseline files, `ignoreFile` entries) instead of fixing it, unless the user asks for that.
- After each commit, run the confirmed checks and re-collect the deprecation to confirm it no longer fires. With Mate, that means generating a fresh log entry or profile and searching again; old log entries do not prove anything.
- Follow the repository's commit message convention; otherwise use Conventional Commits, e.g. `refactor(security): replace deprecated X with Y`.
- Never push, open a PR, deploy, run migrations against a real database, or modify data.

## Report

1. Outcome: completed, completed with open items, or blocked (and where).
2. Whether Mate was used, installed, or declined.
3. The commits made, in order, with the deprecation each one removes.
4. Proof per fix: the deprecation was re-collected and no longer fires, or why that could not be checked.
5. Remaining deprecations with their reason (third-party, out of scope, deferred).
6. Noticed, not done: everything out of scope you came across, with file references.
