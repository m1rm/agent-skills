---
name: find-docs
description: Verify version-sensitive library, framework, SDK, or CLI behavior against documentation. Use for unfamiliar APIs, configuration, migrations, or debugging that depends on third-party behavior. Prefer installed version-matched docs; use remote lookup when local evidence is insufficient.
---

# Documentation lookup

1. Identify the installed version from the project manifest, lockfile, or CLI version.
2. Read relevant installed documentation, types, examples, or source first. If they answer the question, stop; a remote lookup is not mandatory.
3. When external evidence is needed, prefer official version-matched documentation through the current harness's available search/fetch tools or Context7.
4. If `ctx7` is already installed, resolve the library ID before querying it:

```bash
ctx7 library <name> "<specific question>"
ctx7 docs <resolved-library-id> "<specific question>"
```

A user-provided ID such as `/org/project/version` can skip resolution. Match the
project version where available and disclose when only different-version docs exist.
Use at most three Context7 requests per question; stop once the needed contract is clear.

## Boundaries

- Do not install or update tools merely to look up documentation. If Context7 is absent, use available official-doc sources or ask before installing it.
- Use only tools and permission mechanisms available in the current harness. A network failure does not authorize bypassing its sandbox.
- Do not send secrets, proprietary code, or sensitive project details in remote queries.
- Cite the local file or documentation URL supporting the answer. Distinguish documented behavior from inference.
- Report unavailable sources, quota failures, or version uncertainty; do not silently present memory as freshly verified documentation.
