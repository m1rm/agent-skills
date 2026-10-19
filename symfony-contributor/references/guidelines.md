# Symfony contribution rules

Condensed from the official contributing docs (symfony-docs branch `8.2`, read 2026-10-19), the repository's `.github/PULL_REQUEST_TEMPLATE.md`, and the shared Fabbot workflow (`symfony-tools/fabbot`). When a rule matters for a decision, check the live source; the docs and checks change.

## Contents

1. [Branches](#branches)
2. [What a bug fix may change](#what-a-bug-fix-may-change)
3. [Coding standards that tools don't fix](#coding-standards-that-tools-dont-fix)
4. [Backward compatibility](#backward-compatibility)
5. [Deprecations](#deprecations)
6. [CHANGELOG and UPGRADE files](#changelog-and-upgrade-files)
7. [Commits](#commits)
8. [Pull request title and body](#pull-request-title-and-body)
9. [Fabbot checks](#fabbot-checks)
10. [Other CI checks](#other-ci-checks)
11. [Sources](#sources)

## Branches

- **Bug fix**: the *oldest maintained branch* that contains the bug. Fixes are merged up into newer branches automatically.
- **New feature or deprecation**: the current development branch.
- The `Branch?` row of `.github/PULL_REQUEST_TEMPLATE.md` names the current branches, e.g. `8.2 for features / 6.4, 7.4, 8.1 for bug fixes`. It is updated with every release, so read it from a freshly fetched base branch. Cross-check with https://symfony.com/releases if in doubt.
- Translation updates and additions always go to the oldest maintained branch.

## What a bug fix may change

Patch releases are strict, so a bug fix targeting a maintained branch must not:

- add classes, or public/protected methods, or global functions;
- add configuration options;
- add deprecations;
- add or update PHPDoc annotations (fixing wrong ones may be accepted);
- change exception messages (automated systems may rely on them);
- add Composer dependencies or support a new major version of one;
- do coding-standard fixes or refactoring, except small changes for consistency;
- improve performance, unless the change is local, algorithmic and backed by numbers;
- change the web design of built-in pages (exception page, toolbar, profiler).

It must come with tests that cover the fix and must not break valid existing tests. If the current buggy behavior is widely used as a feature, it is not a bug fix. If the docs and the code disagree, the code's behavior counts as correct.

## Coding standards that tools don't fix

PHP-CS-Fixer (config: `.php-cs-fixer.dist.php`) fixes formatting. These rules need a human (or you):

- Exception and error messages: built with `sprintf()`, start with a capital letter, end with a dot, use double quotes around technical names (never backticks), use `get_debug_type()` instead of `::class` for class names of values.
- Yoda conditions for `==`, `!=`, `===`, `!==` against a variable; identical comparison unless type juggling is needed.
- No `else`, `elseif` or `break` after a branch that returns or throws.
- Public methods before protected before private (constructor, `setUp()` and `tearDown()` first).
- `return null;` for explicit null, `return;` for void.
- Test methods have no return type (Fabbot enforces this).
- In PHPDoc type unions, `null` goes last.
- Commands and options are named and described in the imperative mood ("Lint a template", not "Lints").
- Collection-like APIs use `get()`, `set()`, `has()`, `all()`, `replace()`, `remove()`, `clear()`, `isEmpty()`, `add()`, `register()`, `count()`, `keys()` only when there is one main relation; otherwise `getXXX()`, `setXXX()`, and so on.
- No `readonly` classes: use readonly properties (Fabbot enforces this).
- Don't touch files unrelated to the change, not even to fix their coding style.

## Backward compatibility

Full tables: https://symfony.com/doc/current/contributing/code/bc.html. The points that come up most:

- Minor versions never break BC for public API. Code tagged `@internal` or `@experimental` is excluded.
- A new argument can only be added as the last argument, and only through the documented pattern: comment it out in the signature, document it with `@param`, read it with `func_num_args()`/`func_get_arg()`, and trigger a deprecation if the default will change or the argument becomes required in the next major.
- Making a class, method, property or constant `final` is a BC break. Announce it with `@final since Symfony X.Y` instead. Never add a plain `@final` in a minor version.
- Experimental features (`@experimental`) can stay experimental for one minor version and cannot be introduced in an LTS version.

## Deprecations

- Only on the development branch (the next minor), never in a patch release after stability.
- A new class, interface, trait, or method can't be introduced as deprecated.
- PHPDoc: `@deprecated since Symfony X.Y, use Replacement instead.` Use the FQCN if the replacement is in another namespace. Fabbot fails if a `@deprecated` annotation doesn't mention Symfony.
- Runtime: `trigger_deprecation('symfony/package-name', 'X.Y', 'The "%s" class is deprecated, use "%s" instead.', Old::class, New::class);`. For a deprecated class, place the call after the `use` statements.
- In the same PR: the component's `CHANGELOG.md` (`* Deprecate ...`), `UPGRADE-X.Y.md` (under the component name), and `UPGRADE-<next major>.0.md` (`* Remove ...`).
- Removing deprecated code happens only on the next major branch, with a CHANGELOG entry.

## CHANGELOG and UPGRADE files

- New features and deprecations get an entry in the `CHANGELOG.md` at the root of the modified component, bridge, or bundle, under the development version's section (e.g. `8.2`).
- Entries follow the commit message style: short, capitalized, imperative verb first, no trailing period. Prefix with `[BC BREAK]` or `[DEPRECATION]` when relevant. No third-level headings.
- The docs say "new entries must be added on top of the list". Recent commits in symfony/symfony append to the bottom of the section instead. Follow what the file's recent history shows (`git log -p -5 -- path/to/CHANGELOG.md`) and mention it in the PR if unsure.
- Never edit the root `CHANGELOG-*.md` files; they are generated at release time.
- `UPGRADE-*.md` entries are needed for BC breaks and deprecations.

## Commits

- Subject: the component, bridge, or bundle in square brackets, then a capitalized imperative sentence without a trailing period: `[HttpClient] Add support for streaming large responses`. Several components: `[Translation][TwigBridge] ...`.
- The commit author email must be linked to the contributor's GitHub account (Fabbot checks this).
- No merge commits (Fabbot fails). Update a branch with `git rebase`, never `git merge` or `git pull` after history was rewritten.
- No need to squash: Symfony squashes when merging and keeps the PR number in the message.
- Force-push with the branch named explicitly: `git push --force-with-lease origin <branch>`.

## Pull request title and body

- Title: same format as a commit subject, `[Component] Description`.
- Fabbot rejects titles matching `(feat|fix|docs|style|refactor|perf|test|chore|revert|build|ci|types?|wip)` followed by `:` or `(` **anywhere** in the title, case-sensitive. That catches `feat: ...`, and also words like `prefix:` or `test(`. Capitalized `Fix ...` is fine.
- Body: keep the template's table with its exact row labels (`Branch?`, `Bug fix?`, `New feature?`, `Deprecations?`, `Issues`, `License`). Fabbot requires the `| License | MIT` row.
- `Issues`: prefix each issue with `Fix #` (closing keyword: it links the PR to the issue and closes the issue on merge). If the PR only covers part of an issue, `Ref #NNN` is fine, but keep it in the `Issues` row. If there is no issue, say so and explain the motivation below the table.
- Replace the HTML comment block with: what the change does and why, a short example (PHP, YAML, command line), a before/after comparison if behavior changes, and anything reviewers should know (trade-offs, alternatives considered, follow-ups).
- Unfinished work: open as a draft.
- A new feature without an issue: discuss it first on the Symfony Slack `#contribs` channel, or open an issue alongside the PR.

## Fabbot checks

The `Fabbot / Checks` job runs these checks on files changed by the PR:

| Check | Fails when | Fix |
|---|---|---|
| PHP-CS-Fixer | style differs from `.php-cs-fixer.dist.php` | apply the patch from the log, or run PHP-CS-Fixer locally on the changed files |
| Twig-CS-Fixer | Twig style issues | apply the patch from the log |
| codespell | typos | apply the patch from the log |
| readonly classes | a `readonly class` is added | use readonly properties |
| merge commits | the PR contains a merge commit | rebase onto the base branch, force-push |
| commit email | a commit's author email isn't linked to a GitHub account | add the email to GitHub, or amend the author and force-push |
| test method return types | a test method declares a return type | remove it |
| `@deprecated` mentions Symfony | `@deprecated` without "Symfony" | use `@deprecated since Symfony X.Y, ...` |
| PR title/body | no `\| License \| MIT` row, or a conventional-commit title | fix the description or title, then push (see below) |
| YAML/JSON syntax | invalid file | fix the file |
| translation messages | placeholders not in double quotes, or messages not ending with a dot | apply the suggested patch |
| executable files | executable bit on a file without a shebang | `chmod -x <file>` |

The workflow runs on `pull_request` events `opened`, `synchronize`, and `reopened`, not `edited`. Changing the title or body doesn't re-run Fabbot, and "Re-run job" replays the old event, including the old title. To re-check after editing, push again (e.g. reword the commit and force-push).

## Other CI checks

- **Unit tests** run on several PHP versions plus `low-deps` and `high-deps` variants. Logs become available only when the whole workflow run finishes; before that, read the job's annotations (`gh api repos/symfony/symfony/check-runs/<job-id>/annotations`).
- **Check return types** (Unit Tests, PHP 8.4): `php .github/patch-types.php lint` loads every class in the repository. Exit code `1` lists missing return types (fix those if they are yours). Exit code `255` is a PHP fatal error, often caused by something already broken on the base branch.
- **Integration and TTY tests** need services (Redis, databases, a TTY). Failures there are frequently shared with the base branch.
- **PHPStan and Psalm** may comment on possible type errors. Review each one, but don't update their baseline files and don't add `@phpstan-` or `@psalm-` annotations.
- The docs' rule of thumb: a test failure usually points to a real problem in your change, but it can be unrelated. If you suspect that, check whether the target branch fails too and leave a comment.

## Sources

- Contributing code: https://symfony.com/doc/current/contributing/code.html
- Conventions (CHANGELOG, deprecations): https://symfony.com/doc/current/contributing/code/conventions.html
- Coding standards: https://symfony.com/doc/current/contributing/code/standards.html
- Maintenance (what bug fixes may change): https://symfony.com/doc/current/contributing/code/maintenance.html
- BC promise: https://symfony.com/doc/current/contributing/code/bc.html
- Reviews: https://symfony.com/doc/current/contributing/reviews.html
- Releases and maintained branches: https://symfony.com/releases
- Fabbot workflow: https://github.com/symfony-tools/fabbot/blob/main/.github/workflows/fabbot.yml
- Doc sources: https://github.com/symfony/symfony-docs/tree/8.2/contributing
