---
name: maintain-hugo
description: Perform an explicitly requested maintenance update of a local Hugo site — theme/module updates (Hugo modules, git submodules, vendored modules, npm), before/after builds with deprecation comparison, Hugo version compatibility checks, and a maintenance report. Not for deployment, content edits, or upgrading the Hugo binary.
---

# Hugo maintenance

## Scope and preflight

- Confirm this is an authorized local maintenance update, not a production server or a report-only request. If the user only asks what could be maintained, do the baseline and dry-run steps and report; do not mutate the repository.
- Verify the project root: a site config (`hugo.{toml,yaml,json}`, legacy `config.{toml,yaml,json}`, or `config/_default/`). If none exists, stop; do not initialize a new site.
- Run `hugo config` and note which config sources are in effect. If a root config file and `config/_default/` both define the same keys, report it as a finding; do not merge them.
- Detect how themes and components are pulled in. Several may apply at once:
  - **Hugo modules**: `go.mod` plus `[module] imports` / `module.toml`. Requires `go` on PATH.
  - **Vendored modules**: `_vendor/` exists. Hugo builds from `_vendor/` over `go.mod`, so an update must be re-vendored or it has no effect.
  - **Git submodules**: `.gitmodules` entries, usually under `themes/`.
  - **Copied themes**: a plain directory under `themes/` with no upstream reference. Report it; do not update it.
  - **npm**: `package.json` with a lockfile (PostCSS, Tailwind, etc.). Use the package manager that matches the lockfile.
- Detect Hugo version requirements and compare them with local `hugo version` (including whether it is `extended`): CI pins (`.github/workflows/*`, `.gitlab-ci.yml`, `netlify.toml`, `vercel.json`, `wrangler.toml`, `Dockerfile`, `.tool-versions`, `mise.toml`), `module.hugoVersion` in the site config, and each theme's `min_version` / `[module.hugoVersion]` from its `theme.toml` or config. A local Hugo version newer than the CI pin can hide breakage in production and the reverse can create it, so report every mismatch.
- If a `justfile` or `Makefile` wraps Hugo, read the recipes with `just --show <recipe>` or the Makefile itself. Use them only when they do nothing beyond building or updating modules. Never run deploy recipes, `hugo deploy`, or anything that publishes, uploads, or cleans directories.
- Inspect `git status --short` and the existing diff. Preserve unrelated work. If `go.mod`, `go.sum`, `_vendor/`, submodules, `package.json`, or lockfiles have uncommitted changes, ask before updating; do not stash, reset, or clean automatically.
- Check hygiene and report findings; do not change anything here without asking: `public/`, `resources/_gen/`, and `.hugo_build.lock` should be git-ignored and untracked (`git ls-files`, `git check-ignore -v`).

## Baseline

Build into a private temporary directory, never into `public/`, so existing output is not overwritten. Use `hugo build` when available (`hugo build --help`); otherwise use plain `hugo`.

```bash
hugo version
go version                                   # Hugo modules only
hugo mod graph                               # Hugo modules only
go list -m -u -json all                      # Hugo modules only: available updates
git submodule status                         # submodules only
hugo build --logLevel warn --printPathWarnings --destination <tmpdir>/before
```

- Record the build's exit status, every `WARN`/`ERROR` line, and the page/alias counts. A broken baseline build is a finding, not a reason to stop: dependency updates are often the fix.
- For npm, also run the package manager's `outdated` and `audit` commands and retain their output.

## Update sequentially

Run each command separately and retain its output and exit status.

- **Hugo modules**: `hugo mod get -u ./...`, then `hugo mod tidy`, then `hugo mod verify`. If `_vendor/` exists, then run `hugo mod vendor`.
- **Git submodules**: read the branch tracked in `.gitmodules`, then run `git submodule update --remote <path>` per theme. Record old and new commits, and `git -C <path> log --oneline <old>..<new>` for the report.
- **npm**: update within the existing version ranges only (`npm update`, `pnpm update`, `yarn upgrade`, matching the lockfile).

Rules:

- Do not change major versions. Go module major versions live under a new path (`/v2`), so `-u` never crosses them. Report available majors; do not rewrite import paths or npm ranges.
- Do not install, upgrade, or downgrade the Hugo or Go binaries, and do not change CI Hugo pins. Report mismatches and recommend a pin.
- Stop on network, authentication, checksum (`hugo mod verify`), or resolution failures. Report partial changes. Never hide errors with `|| true`, and never roll back automatically.
- Allowed changes are `go.mod`, `go.sum`, `_vendor/`, submodule gitlinks, and npm manifests/lockfiles produced by the commands above. Identify any other changed file and ask before further mutation.
- No commits, pushes, deployments, content edits, or template/config edits during the update. Do not install new tools.

## Verify

```bash
hugo build --logLevel warn --printPathWarnings --destination <tmpdir>/after
git status --short
git diff --stat
git diff -- go.mod go.sum .gitmodules package.json
```

- Compare the warnings, errors, and page/alias counts with the baseline. Classify each remaining warning by origin:
  - **Project-owned**: site config keys, `layouts/`, `assets/`, `content/`. The fix is in this repository.
  - **Upstream**: the path points into the module cache, `_vendor/`, or `themes/<submodule>`. The fix belongs upstream. Do not fork or override theme templates to silence it.
- A build that passes does not mean the site looks right. Report visual or functional checks not performed.
- If a build that passed before now fails, report the breaking module change with its version range and the restore command (`git checkout -- go.mod go.sum`, or the old submodule commit). Do not run it without asking.

## Follow-up offer

After the report, offer to fix project-owned deprecations. Name the exact replacement from each warning (e.g. config `languageCode` → `locale`). Apply only on confirmation, rebuild, and confirm the warning is gone. Offer hygiene fixes (`.gitignore`, untracking `.hugo_build.lock`, duplicate config) the same way.

Offer a Hugo version pin the same way when none exists:

- If the project already uses a version manager (`mise.toml`, `.tool-versions`) or CI pins Hugo, pin it there.
- Otherwise, declare the range Hugo itself checks in the site's module config (`[module.hugoVersion]`, or `[hugoVersion]` inside `config/_default/module.toml`). Set `min` to the oldest version the config needs (e.g. 0.158.0 for `locale`) and `max` to the version just tested. Outside the range, Hugo prints a "not compatible with this Hugo version" warning but still builds. On a rolling Hugo install, that warning signals that maintenance is due.
- If a `max` already exists and the local Hugo version is above it, offer to raise `max` to the version you just verified, but only after a clean "after" build.

## Report

Return a concise maintenance report in the user's language:

1. Project, date, outcome: completed, completed with remaining findings, or blocked/partial.
2. Tooling: local Hugo and Go versions, extended or not, CI pins, and theme minimum versions, with any mismatches.
3. Commands run, failures, and verification not performed.
4. Dependency changes with exact before/after versions or commits: modules, submodules, npm packages. List available major upgrades separately.
5. Build before/after: exit status, counts, and warnings resolved, remaining (project-owned vs upstream), and new.
6. npm audit findings before/after, if applicable. Do not invent CVEs or severity.
7. Hygiene findings, changed files (separating pre-existing work from maintenance changes), and recommended next actions.

Return the report in chat unless the user requests a file and destination. Do not write reports into the repository by default.
