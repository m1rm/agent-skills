---
name: pull-request
description: >-
  Create a pull request or merge request, or draft its description, for the
  current branch's changes. Use when the user asks to open a PR/MR or to write
  a PR summary or change description for review on GitHub or GitLab.
---

# Workflow

1. Distinguish a description-only request from permission to create a PR. A request to summarize or draft does not authorize pushing or creating anything.
2. Read repository instructions, inspect `git status`, and establish the intended remote, head branch, and actual base branch; do not assume `main`. Inspect the commits and diff using `git log --oneline <base>...HEAD` and `git diff <base>...HEAD`. Uncommitted changes are not part of a published PR; do not commit them automatically.
3. Before creating a PR, request a fresh, read-only review using the current harness's review routing in its global instructions. Pass the task, base/head, diff text or a readable diff artifact, relevant source paths, project rules, and validation evidence. Do not assume an agent name, model, or tool API from another harness. The reviewer reports findings and does not edit or run tests.
4. If independent review is unavailable or fails, report the blocker and ask how to proceed. Do not silently replace it with self-review or switch harnesses. When strict code-quality review is requested, include [mkr-code-quality-review](../mkr-code-quality-review/SKILL.md) in the review task; otherwise use ordinary PR review.
5. Present substantive findings. Apply fixes only within the user's authorized scope; ask before scope-expanding changes. Recheck affected validation and review changed areas when necessary.
6. Draft the description below. For description-only requests, return it and stop; independent review is not required merely to write a summary.
7. Only when PR creation is authorized, verify the destination and push the intended committed branch if necessary (never force-push). Use the available GitHub CLI workflow for GitHub; use the host's supported workflow for other providers. Do not assume GitHub for a GitLab merge request.
8. Create the PR with the verified base/head, title, and description, then return its URL. Never merge or deploy as part of this skill.

---

# Pull Request Format

When creating a pull request or describing code changes for review, always
structure the description using the following three sections.

## 1. Summary

Provide a concise overview of the most important changes introduced by this
pull request. Focus on the "what" — the key modifications, additions, or
removals — so a reviewer can grasp the scope at a glance.

- Keep it to a few bullets or a short paragraph.
- Highlight only the changes that affect behavior, public APIs, or
  architecture.
- Omit trivial formatting or refactoring unless it is the primary purpose of
  the PR.

## 2. Problem

Describe the original problem or motivation that necessitated these changes.
Explain why the current state was insufficient, incorrect, or sub-optimal.

- State the issue clearly (bug, missing feature, performance bottleneck,
  technical debt, etc.).
- Include context such as error messages, user reports, or observed
  behavior.
- If a ticket or issue exists, reference it here (e.g., "Closes #123").

## 3. Solution

Propose the approach taken to tackle the problem outlined above. Explain the
"how" and "why" of the fix or implementation.

- Describe the chosen strategy and any trade-offs considered.
- If alternative approaches were considered, say why this one was chosen.
- If applicable, note any follow-up work, known limitations, or areas that
  need extra scrutiny during review.

---

## Usage Notes

- Use present tense (e.g., "Fixes race condition" rather than "Fixed race
  condition").
- Keep the total description scannable.
- If the PR is a work in progress, mark it as draft and add a **WIP**
  notice at the top.
