---
name: mkr-code-quality-review
description: Review a diff for structural maintainability problems and substantial simplification opportunities when a strict code-quality review is requested, including during pull-request preparation.
---

# MKR Code Quality Review

Give a demanding, evidence-based review of the requested changes. Look for ways to remove complexity while preserving behavior. Report findings; edit only when separately authorized.

## Scope and integration

Establish the actual base/head or use the supplied diff. Read enough surrounding code to judge ownership, existing extension points, and project conventions.

The `pull-request` workflow can explicitly request this skill as part of its independent review. Follow the current harness's review routing; this skill supplies additional criteria without replacing correctness or security review. In a read-only reviewer task, report findings without edits or test execution.

## Review criteria

- Seek substantial simplifications that delete concepts, branches, state, or layers. Prefer an existing option, hook, or helper over a new mechanism.
- Flag scattered special cases, repeated conditionals, and feature logic leaking into shared infrastructure. Explain the ownership or state-model problem behind them.
- Question wrappers, generic frameworks, and pass-through helpers that add indirection without reducing complexity. Extraction is useful only when it improves cohesion or reuse.
- Flag casts, unclear optionality, and silent fallbacks that conceal broken contracts. Preserve necessary validation at external boundaries.
- Treat file growth as a signal to inspect cohesion. Crossing 1,000 lines alone is not a blocker; identify the concrete responsibility or navigation problem.
- Flag partial updates that can leave inconsistent state. Suggest parallel execution only when operations are independent and it meaningfully improves the flow.

## Findings and judgment

Prioritize structural regressions and high-value simplifications over cosmetic cleanup. Be direct, but support each finding with a file/line reference, the concrete maintenance cost or failure mode, and a simpler alternative with its tradeoff.

Separate problems introduced by the diff from pre-existing debt and optional improvements. A plausible refactor or personal style preference is not enough to block approval. Recommend broader restructuring only when its benefit justifies the scope.

Return a small set of actionable findings ordered by severity. If none meet that bar, say so. State relevant validation limits without inventing test evidence.
