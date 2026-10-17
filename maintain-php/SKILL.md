---
name: maintain-php
description: Perform an explicitly requested Composer maintenance update in a local PHP project driven by a justfile, with before/after security audits, package changes, and a maintenance report. Not for deployment or database migrations.
---

# PHP maintenance

## Scope and preflight

- Confirm this is an authorized local maintenance update, not a production environment or a report-only request.
- Verify the project root, `justfile`, `composer.json`, and `composer.lock`. If missing, stop and report what is needed; do not initialize a new project.
- Find the recipe that runs Composer in the project's PHP runtime, usually `composer *args`. Read it with `just --list` and `just --show <recipe>`. If no such recipe exists, stop and ask; do not fall back to a host `composer`, which reports on a different PHP runtime.
- Inspect `git status --short` and the existing diff. Preserve unrelated work. If Composer files or files affected by scripts have uncommitted changes, ask before updating; do not stash, reset, or clean automatically.
- Inspect Composer scripts, configured plugins, and every recipe you will run, including its dependencies and anything it calls. If they deploy, migrate, delete data, or have unclear side effects outside maintenance, stop and ask. Never run lifecycle recipes such as `init`, `rebuild`, `clean`, or `reset-db` as part of maintenance. Do not silently disable project hooks or security policies.
- Capture the pre-update lockfile package versions and existing changes as baseline evidence. Use a private temporary directory only if artifacts are needed; do not copy credentials or authentication files.

## Execute sequentially

Run each command separately and retain its output and exit status. Start services first only if the Composer recipe needs them and a start recipe (e.g. `just start`) does nothing beyond starting them:

```bash
just composer --version
just composer audit --locked --format=json
just composer update --no-interaction
just composer audit --locked --format=json
just composer check-platform-reqs
git status --short
git diff --stat
git diff -- composer.json composer.lock
```

- Continue past a pre-update audit's nonzero exit only when its output clearly reports audit findings, not an operational failure. Audit exit-code meanings vary by Composer version; do not equate every nonzero result with a broken command or every successful command with no vulnerabilities.
- Stop on startup, network, authentication, dependency-resolution, plugin, or script failures. Report partial changes; never hide errors with `|| true` or automatically roll back user work.
- An unsuccessful update is not completed maintenance. A read-only post-failure audit may describe the resulting lockfile, but label it as partial state.
- Keep project security policies enabled. Do not change version constraints, ignore advisories, bypass platform requirements, or force major upgrades to make the update pass.
- Allowed changes are Composer-managed dependency files and expected generated/script output. Identify unexpected changes and ask before further mutation.
- No commits, pushes, deployments, migrations, database operations, or application-code edits. Do not install new validation tools.
- Run the project's documented, non-destructive maintenance checks when available, such as static analysis or lint recipes. Skip recipes that depend on database preparation or migrations (test suites often do) and list them as not performed. Dependency audit and platform checks do not prove the application works; report application checks not performed.

## Report

Return a concise maintenance report in the user's language:

1. Project, date, outcome: completed, completed with remaining findings, or blocked/partial.
2. Commands run, failures, and verification not performed.
3. Packages added, removed, and updated with exact before/after versions from the baseline and resulting lockfile, including dev dependencies.
4. Security advisories before/after: affected packages, reported severity/IDs/URLs, resolved and remaining findings. Do not invent CVEs or severity.
5. Abandoned packages separately from security vulnerabilities; include only documented replacements. Report any other policy findings separately.
6. Changed files, distinguishing pre-existing work and Composer/script changes, plus recommended next actions.

Return the report in chat unless the user requests a file and destination. Do not
write customer reports into the repository by default.
