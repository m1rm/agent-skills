#!/usr/bin/env sh
set -eu
repo=$(cd "$(dirname "$0")" && pwd)
target="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$target"
for skill in "$repo"/*/; do
  name=$(basename "$skill")
  [ -f "$skill/SKILL.md" ] || continue
  link="$target/$name"
  if [ -e "$link" ] && [ ! -L "$link" ]; then
    echo "skip $name: $link exists and is not a symlink" >&2
    continue
  fi
  ln -sfn "${skill%/}" "$link"
  echo "linked $name"
done
