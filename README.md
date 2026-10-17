# agent-skills

Personal skills for Claude Code.

Adapted from [marco-kretz/dotfiles](https://github.com/marco-kretz/dotfiles/tree/main/agents/.agents/skills) (commit `ff1aa9b`). Changes: dropped the Codex-only `agents/openai.yaml` files and added `disable-model-invocation: true` to `deslop`, and switched `maintain-php` from DDEV to `just` recipes.

## Install

```sh
git clone git@github.com:m1rm/agent-skills.git ~/projects/agent-skills
~/projects/agent-skills/install.sh
```

`install.sh` symlinks every skill directory into `~/.claude/skills/`, so `git pull` updates them. It refuses to replace an existing non-symlink entry.

## Own skills

- `upgrade-symfony`: upgrades Symfony from one version to another using the UPGRADE/CHANGELOG files, with a confirmed plan and atomic commits.
- `fix-symfony-deprecations`: fixes Symfony deprecations from project code, using Symfony AI Mate when present.
