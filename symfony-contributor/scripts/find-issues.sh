#!/usr/bin/env sh
# List open symfony/symfony issues with a label, plus their assignees, comment
# counts and every pull request linked to them (state: OPEN, CLOSED, MERGED).
#
# Usage: find-issues.sh [label] [extra GitHub search terms]
#   find-issues.sh                          # "Good first issue"
#   find-issues.sh "Help wanted" -label:"Missing translations"
#   find-issues.sh Bug label:Console label:"Status: Confirmed"
set -eu

label="${1:-Good first issue}"
[ $# -gt 0 ] && shift
extra="$*"

printf 'issue\tupdated\tcomments\tassignees\tlinked PRs\tlabels\ttitle\n'
gh api graphql --paginate \
  -f q="repo:symfony/symfony is:issue is:open label:\"$label\" $extra sort:updated-desc" \
  -f query='
query($q: String!, $endCursor: String) {
  search(type: ISSUE, query: $q, first: 50, after: $endCursor) {
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on Issue {
        number title updatedAt
        labels(first: 10) { nodes { name } }
        assignees(first: 3) { nodes { login } }
        comments { totalCount }
        closedByPullRequestsReferences(first: 10, includeClosedPrs: true) { nodes { number state } }
        timelineItems(first: 100, itemTypes: [CROSS_REFERENCED_EVENT, CONNECTED_EVENT]) {
          nodes {
            ... on CrossReferencedEvent { source { ... on PullRequest { number state repository { nameWithOwner } } } }
            ... on ConnectedEvent { subject { ... on PullRequest { number state } } }
          }
        }
      }
    }
  }
}' --jq '.data.search.nodes[] | [
    "#\(.number)",
    .updatedAt[:10],
    (.comments.totalCount | tostring),
    ([.assignees.nodes[].login] | join(",") | if . == "" then "-" else . end),
    ([(.closedByPullRequestsReferences.nodes[] | "#\(.number):\(.state)"),
      (.timelineItems.nodes[] | (.source // .subject)
        | select(.number != null)
        | select((.repository.nameWithOwner // "symfony/symfony") == "symfony/symfony")
        | "#\(.number):\(.state)")]
      | unique | join(" ") | if . == "" then "-" else . end),
    ([.labels.nodes[].name] | join(",")),
    .title
  ] | @tsv'
