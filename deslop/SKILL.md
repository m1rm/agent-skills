---
name: deslop
description: Remove unnecessary AI-generated code from a requested diff while preserving behavior and local style.
disable-model-invocation: true
---

# Remove AI code slop

Inspect the requested diff and surrounding code. For branch-wide cleanup, establish the actual base branch. Edit only when cleanup is authorized; report findings for review-only requests.

## Focus Areas

- Extra comments that are unnecessary or inconsistent with local style
- Defensive checks or try/catch blocks that are abnormal for trusted code paths
- Casts to `any` used only to bypass type issues
- Deeply nested code that should be simplified with early returns
- Other patterns inconsistent with the file and surrounding codebase

## Guardrails

- Preserve behavior, including validation and error handling at external boundaries. Report bugs separately unless a fix is authorized.
- Prefer minimal, focused edits over broad rewrites.
- Keep the final summary brief.
