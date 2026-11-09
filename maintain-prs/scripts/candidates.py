#!/usr/bin/env python3
"""List open PRs/MRs that need maintenance, with the local clones they map to.

Runs the contribution-manager (`prwatch list --keep --json`, so "new" markers are not
consumed), keeps PRs that are behind their target branch, have conflicts or failing CI,
and matches each to git clones under the search roots by comparing remote URLs.

Usage: candidates.py [--all] [--json] [--roots DIR[:DIR...]]

The contribution-manager (https://github.com/m1rm/contribution-manager) is looked up as
$CONTRIBUTION_MANAGER_DIR, then as a "contribution-manager" checkout in one of the search
roots (run via its justfile, which loads its .env), then as `prwatch` on PATH (tokens must
then be in the environment).

Environment:
  CONTRIBUTION_MANAGER_DIR  contribution-manager checkout
  MAINTAIN_PRS_ROOTS        colon-separated directories to search for clones
                            (default: whichever of ~/projects, ~/src, ~/code, ~/git, ~/dev exist)
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

MAX_DEPTH = 3
DEFAULT_ROOTS = "~/projects:~/src:~/code:~/git:~/dev"
SKIP_DIRS = {"node_modules", "vendor", ".cache", "target", "dist", "build", "var"}


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def find_contribution_manager(roots):
    if os.environ.get("CONTRIBUTION_MANAGER_DIR"):
        return Path(os.environ["CONTRIBUTION_MANAGER_DIR"]).expanduser()
    for root in roots:
        d = Path(root).expanduser() / "contribution-manager"
        if (d / "justfile").is_file():
            return d
    return None


def fetch_prs(roots):
    cm_dir = find_contribution_manager(roots)
    if cm_dir and (cm_dir / "justfile").is_file() and shutil.which("just"):
        # The justfile loads the tokens from the contribution-manager's .env.
        cmd = ["just", "--justfile", str(cm_dir / "justfile"), "--working-directory", str(cm_dir),
               "list", "--keep", "--json"]
    elif shutil.which("prwatch"):
        cmd = ["prwatch", "list", "--keep", "--json"]  # tokens must be in the environment
    else:
        sys.exit("contribution-manager not found: set CONTRIBUTION_MANAGER_DIR to its checkout, "
                 "or put prwatch on PATH (https://github.com/m1rm/contribution-manager)")
    res = run(cmd)
    if res.returncode != 0:
        sys.exit(f"{' '.join(cmd)} failed:\n{res.stderr.strip()}")
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError as e:
        sys.exit(f"could not parse contribution-manager JSON ({e}); is it new enough to support --json?")


def norm_url(url):
    """Reduce a git remote or web URL to 'host/path' (lowercase, no .git, no user or port)."""
    url = url.strip()
    m = re.match(r"^[\w.+-]+://(?:[^@/]+@)?([^/:]+)(?::\d+)?/(.+)$", url)
    if not m:
        m = re.match(r"^(?:[^@/]+@)?([^/:]+):(.+)$", url)  # scp-like: git@host:path
    if not m:
        return None
    host, path = m.group(1), m.group(2)
    path = re.sub(r"\.git/?$", "", path).strip("/")
    return f"{host}/{path}".lower()


def find_clones(roots):
    """Yield (path, {remote_name: normalized_url}) for git clones under roots."""
    for root in roots:
        root = Path(root).expanduser()
        if not root.is_dir():
            continue
        stack = [(root, 0)]
        while stack:
            d, depth = stack.pop()
            if (d / ".git").exists():
                res = run(["git", "-C", str(d), "remote", "-v"])
                remotes = {}
                for line in res.stdout.splitlines():
                    parts = line.split()
                    if len(parts) == 3 and parts[2] == "(fetch)":
                        n = norm_url(parts[1])
                        if n:
                            remotes[parts[0]] = n
                yield d, remotes
                continue  # don't descend into clones
            if depth >= MAX_DEPTH:
                continue
            try:
                children = sorted(p for p in d.iterdir() if p.is_dir() and not p.name.startswith(".")
                                  and p.name not in SKIP_DIRS)
            except OSError:
                continue
            stack.extend((c, depth + 1) for c in reversed(children))


def clone_info(path, remotes, pr):
    upstream = norm_url(pr["repo_url"]) if pr.get("repo_url") else None
    head = norm_url(pr["head_repo_url"]) if pr.get("head_repo_url") else None
    up_remotes = [r for r, u in remotes.items() if u == upstream]
    head_remotes = [r for r, u in remotes.items() if u == head]
    if not up_remotes and not head_remotes:
        return None
    branch = pr["head_branch"]
    has_local = run(["git", "-C", str(path), "rev-parse", "--verify", "--quiet",
                     f"refs/heads/{branch}"]).returncode == 0
    current = run(["git", "-C", str(path), "branch", "--show-current"]).stdout.strip()
    dirty = bool(run(["git", "-C", str(path), "status", "--porcelain"]).stdout.strip())
    state = None
    gitdir = run(["git", "-C", str(path), "rev-parse", "--absolute-git-dir"]).stdout.strip()
    for marker, name in (("rebase-merge", "rebase"), ("rebase-apply", "rebase"),
                         ("MERGE_HEAD", "merge"), ("CHERRY_PICK_HEAD", "cherry-pick")):
        if gitdir and (Path(gitdir) / marker).exists():
            state = name
    return {
        "path": str(path),
        "upstream_remotes": up_remotes,
        "head_remotes": head_remotes,
        "has_local_branch": has_local,
        "current_branch": current,
        "dirty": dirty,
        "in_progress": state,
    }


def actions(pr):
    a = []
    behind = pr.get("behind")
    if pr.get("conflicts"):
        a.append("rebase (conflicts)")
    elif behind:
        a.append(f"rebase (behind {behind})")
    elif behind is None:
        a.append("rebase? (behind unknown)")
    if pr.get("ci") == "failed":
        a.append("fix CI")
    return a


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help="include PRs that need nothing")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--roots", default=os.environ.get("MAINTAIN_PRS_ROOTS", DEFAULT_ROOTS),
                    help="colon-separated directories to search for clones")
    args = ap.parse_args()

    roots = [r for r in args.roots.split(":") if r]
    data = fetch_prs(roots)
    clones = list(find_clones(roots))

    out = []
    for pr in data["prs"]:
        acts = actions(pr)
        if not acts and not args.all:
            continue
        matches = [c for c in (clone_info(p, r, pr) for p, r in clones) if c]
        out.append({**pr, "actions": acts, "clones": matches})

    if args.json:
        json.dump({"candidates": out, "errors": data["errors"]}, sys.stdout, indent=2)
        print()
        return

    for e in data["errors"]:
        print(f"! {e['instance']}: {e['error']}")
    if not out:
        print("Nothing to maintain: no open PR is behind, conflicting, or failing CI.")
        return
    for i, pr in enumerate(out, 1):
        sigil = "!" if pr["platform"] == "gitlab" else "#"
        draft = " [draft]" if pr["draft"] else ""
        print(f"{i}. {pr['host']}/{pr['repo']}{sigil}{pr['number']}{draft}: {pr['title']}")
        print(f"   {pr['url']}")
        head = pr["head_repo"] or "(source repo unknown or deleted)"
        print(f"   {head}:{pr['head_branch']} -> {pr['repo']}:{pr['base_branch']}"
              f" | CI: {pr['ci'] or 'none'} | review: {pr['review'] or 'none'}")
        print(f"   needs: {', '.join(pr['actions']) or 'nothing'}")
        if not pr["clones"]:
            print("   clone: none found")
        for c in pr["clones"]:
            flags = []
            if c["current_branch"] == pr["head_branch"]:
                flags.append("branch checked out")
            elif c["has_local_branch"]:
                flags.append("local branch exists")
            else:
                flags.append("no local branch")
            if c["dirty"]:
                flags.append("DIRTY")
            if c["in_progress"]:
                flags.append(f"{c['in_progress'].upper()} IN PROGRESS")
            remotes = ", ".join(f"{r} (fork)" for r in c["head_remotes"]) or "fork: no remote"
            if c["upstream_remotes"]:
                remotes += ", " + ", ".join(f"{r} (upstream)" for r in c["upstream_remotes"])
            print(f"   clone: {c['path']} [{remotes}; {', '.join(flags)}]")


if __name__ == "__main__":
    main()
