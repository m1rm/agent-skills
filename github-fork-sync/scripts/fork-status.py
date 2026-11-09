#!/usr/bin/env python3
"""Show how each of your GitHub forks compares to its parent repository. Read-only.

For every fork, the branch compared is the parent's default branch (the one `gh repo sync`
updates) against the fork's branch of the same name. Each fork is checked separately, so one
inaccessible parent (deleted, private, blocked by an org policy) does not hide the others.

Status:
  up-to-date      fork branch equals the parent's
  behind          only the parent has new commits: safe to fast-forward
  ahead           only the fork has extra commits: nothing to sync
  diverged        both have commits: a sync would need a merge or a hard reset
  missing-branch  the fork has no branch named like the parent's default (renamed upstream?)
  archived        the fork is archived (read-only)
  error           the fork or its parent could not be read

Usage: fork-status.py [--owner LOGIN] [--hostname HOST] [--repo OWNER/NAME ...] [--json]
  --owner     user or organization whose forks to check (default: the authenticated user)
  --hostname  GitHub host for GitHub Enterprise Server (default: github.com, or $GH_HOST)
  --repo      check only these forks (repeatable); skips listing
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
from concurrent.futures import ThreadPoolExecutor


class APIError(Exception):
    pass


class GH:
    def __init__(self, hostname):
        self.hostname = hostname

    def api(self, path, paginate=False):
        cmd = ["gh", "api", "--hostname", self.hostname, path]
        if paginate:
            cmd[2:2] = ["--paginate", "--slurp"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            msg = (res.stderr or res.stdout).strip().splitlines()
            raise APIError(msg[0] if msg else f"gh api {path} failed")
        data = json.loads(res.stdout)
        if paginate:  # list of pages -> flat list
            data = [item for page in data for item in page]
        return data


def list_forks(gh, owner, me):
    if owner.lower() == me.lower():
        repos = gh.api("user/repos?affiliation=owner&per_page=100", paginate=True)
    else:
        try:
            repos = gh.api(f"orgs/{owner}/repos?type=forks&per_page=100", paginate=True)
        except APIError:
            repos = gh.api(f"users/{owner}/repos?type=owner&per_page=100", paginate=True)
    return sorted(r["full_name"] for r in repos if r.get("fork"))


def check(gh, fork):
    out = {"fork": fork, "parent": None, "branch": None, "fork_default_branch": None,
           "status": "error", "behind": None, "ahead": None, "detail": ""}
    try:
        repo = gh.api(f"repos/{fork}")
        out["fork_default_branch"] = repo.get("default_branch")
        parent = repo.get("parent")
        if not parent:
            out["detail"] = "parent not visible (deleted, private, or no access)"
            return out
        out["parent"] = parent["full_name"]
        branch = parent.get("default_branch")
        out["branch"] = branch
        if repo.get("archived"):
            out["status"], out["detail"] = "archived", "fork is archived"
            return out
        try:
            gh.api(f"repos/{fork}/branches/{urllib.parse.quote(branch, safe='')}")
        except APIError as e:
            if "404" in str(e) or "Not Found" in str(e):
                out["status"] = "missing-branch"
                out["detail"] = (f"fork has no branch {branch!r} (fork default: {out['fork_default_branch']!r}); "
                                 "upstream may have renamed its default branch")
                return out
            raise
        fork_owner = fork.split("/")[0]
        b = urllib.parse.quote(branch, safe="")
        cmp = gh.api(f"repos/{parent['full_name']}/compare/{b}...{fork_owner}:{b}")
        # base = parent branch, head = fork branch
        out["ahead"], out["behind"] = cmp["ahead_by"], cmp["behind_by"]
        out["status"] = {
            "identical": "up-to-date", "behind": "behind", "ahead": "ahead", "diverged": "diverged",
        }.get(cmp["status"], cmp["status"])
        if out["status"] == "diverged":
            out["detail"] = f"fork has {out['ahead']} commit(s) not in the parent"
    except APIError as e:
        out["status"], out["detail"] = "error", str(e)
    return out


ORDER = ["behind", "diverged", "missing-branch", "error", "ahead", "archived", "up-to-date"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--owner")
    ap.add_argument("--hostname", default=os.environ.get("GH_HOST", "github.com"))
    ap.add_argument("--repo", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    gh = GH(args.hostname)
    try:
        if args.repo:
            forks = args.repo
        else:
            me = gh.api("user")["login"]
            forks = list_forks(gh, args.owner or me, me)
    except APIError as e:
        sys.exit(f"could not list forks: {e}")

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda f: check(gh, f), forks))
    results.sort(key=lambda r: (ORDER.index(r["status"]) if r["status"] in ORDER else len(ORDER), r["fork"]))

    if args.json:
        json.dump(results, sys.stdout, indent=2)
        print()
        return

    if not results:
        print("No forks found.")
        return
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"{len(results)} fork(s): " + ", ".join(f"{n} {s}" for s, n in
                                                 sorted(counts.items(), key=lambda kv: ORDER.index(kv[0]) if kv[0] in ORDER else 99)))
    for r in results:
        line = f"{r['status']:<15} {r['fork']}"
        if r["parent"]:
            line += f" <- {r['parent']}"
        if r["branch"]:
            line += f" [{r['branch']}]"
        if r["status"] == "behind":
            line += f" behind {r['behind']}"
        if r["detail"]:
            line += f"  ({r['detail']})"
        print(line)


if __name__ == "__main__":
    main()
