#!/usr/bin/env sh
# Compare the failing GitHub Actions jobs of a symfony/symfony pull request with
# the same jobs on the last completed push runs of the PR's base branch.
#
# For every failed job it prints the failed step, the failure annotations
# (available before the run's logs are), how often the same job failed at the
# same step on the base branch, and whether a failing package ("KO <path>") is
# one the PR touches. It gives hints, not verdicts: confirm in the logs.
#
# Usage: ci-triage.sh <pr-number> [number of base runs to compare, default 5]
set -eu

pr="${1:?usage: ci-triage.sh <pr-number> [base-runs]}"
depth="${2:-5}"
repo=symfony/symfony
tab="$(printf '\t')"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

base=$(gh pr view "$pr" -R "$repo" --json baseRefName --jq .baseRefName)
head=$(gh pr view "$pr" -R "$repo" --json headRefOid --jq .headRefOid)
# Packages the PR touches, e.g. src/Symfony/Bridge/Twig
gh pr diff "$pr" -R "$repo" --name-only | awk -F/ '$1 == "src" && NF > 4 { print $1"/"$2"/"$3"/"$4 }' | sort -u > "$tmp/packages"

echo "PR #$pr  base: $base  head: $(echo "$head" | cut -c1-11)"
echo "packages touched: $(tr '\n' ' ' < "$tmp/packages")"
echo

gh api "repos/$repo/actions/runs?head_sha=$head&per_page=50" \
  --jq '.workflow_runs[] | "\(.id)\t\(.workflow_id)\t\(.status)\t\(.name)"' > "$tmp/runs"

while IFS="$tab" read -r run workflow status name; do
  gh api "repos/$repo/actions/runs/$run/jobs?per_page=100" \
    --jq '.jobs[] | "\(.id)\t\(.status)\t\(.conclusion)\t\(.name)\t\([.steps[] | select(.conclusion == "failure") | .name] | join(", "))"' > "$tmp/jobs"
  pending=$(awk -F"$tab" '$2 != "completed"' "$tmp/jobs" | wc -l | tr -d ' ')
  awk -F"$tab" '$3 == "failure"' "$tmp/jobs" > "$tmp/failed"
  [ ! -s "$tmp/failed" ] && [ "$pending" = 0 ] && continue

  echo "== $name (run $run, $status, $pending job(s) not finished)"
  if [ ! -s "$tmp/failed" ]; then echo "   no failed job yet"; echo; continue; fi

  # Same workflow on the base branch: one line per job and run.
  : > "$tmp/base"
  gh api "repos/$repo/actions/workflows/$workflow/runs?branch=$base&event=push&status=completed&per_page=$depth" \
    --jq '.workflow_runs[].id' |
  while read -r base_run; do
    gh api "repos/$repo/actions/runs/$base_run/jobs?per_page=100" \
      --jq ".jobs[] | \"$base_run\t\(.conclusion)\t\(.name)\t\([.steps[] | select(.conclusion == \"failure\") | .name] | join(\", \"))\"" >> "$tmp/base"
  done

  while IFS="$tab" read -r job_id _ _ job steps; do
    echo "   FAIL  $job"
    echo "         step: ${steps:-?}"
    case "$steps" in
      Install*|Setup*|"Set up"*|Checkout*|*"composer install"*|*"Cache "*)
        echo "         hint: setup step, not a test: often infrastructure or a flaky download; re-run before investigating" ;;
    esac

    gh api "repos/$repo/check-runs/$job_id/annotations" \
      --jq '.[] | select(.annotation_level == "failure") | .message | split("\n")[0][:160]' 2>/dev/null > "$tmp/annotations" || : > "$tmp/annotations"
    while read -r message; do
      echo "         annotation: $message"
      case "$message" in
        "KO "*)
          path=${message#KO }
          if grep -qxF "$path" "$tmp/packages"; then
            echo "         hint: $path is touched by this PR"
          else
            echo "         hint: $path is NOT touched by this PR"
          fi ;;
      esac
    done < "$tmp/annotations"

    total=$(awk -F"$tab" -v j="$job" '$3 == j' "$tmp/base" | wc -l | tr -d ' ')
    same=$(awk -F"$tab" -v j="$job" -v s="$steps" '$3 == j && $2 == "failure" && $4 == s' "$tmp/base" | wc -l | tr -d ' ')
    if [ "$total" = 0 ]; then
      echo "         base: job not found in the last $depth $base push runs"
    else
      echo "         base: failed at the same step in $same of the last $total $base push runs"
    fi
  done < "$tmp/failed"
  echo
done < "$tmp/runs"
