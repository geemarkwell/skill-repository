# skill-repository

## Clean Code

[`clean-code`](clean-code/SKILL.md) provides principles for writing, reviewing, and refactoring code. Imported unchanged from [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills/tree/1e53ce294b6aa36c6d18d5a998cf8fda9db7723d/skills/clean-code), commit `1e53ce294b6aa36c6d18d5a998cf8fda9db7723d`. Upstream credits [ClawForge](https://github.com/jackjin1997/ClawForge). Upstream license notices are included in the skill folder.

Install globally for Codex:

```sh
npx skills add https://github.com/geemarkwell/skill-repository --skill clean-code --agent codex --global --yes
```

To require loading before every code-writing task, append this rule to `~/.codex/AGENTS.md` (preserve existing instructions):

```markdown
## Clean code — required for code changes

Before writing, modifying, or refactoring code, always load and apply the `clean-code` skill. Do not wait for an explicit request. If it is not listed among available skills, read `~/.agents/skills/clean-code/SKILL.md` or `~/.codex/skills/clean-code/SKILL.md` directly. Apply its guidance alongside the repository's `CLAUDE.md` and task-specific instructions.
```

Start a new Codex session after changing global instructions.

## Database Migrations

[`database-migrations`](database-migrations/SKILL.md) provides database migration patterns. Imported from [affaan-m/ecc](https://github.com/affaan-m/ecc/tree/ef648e01899ba3e8dc6371642deaaf64b4477775/skills/database-migrations), with its MIT license. Local adaptation loads the skill for all code changes and applies migration guidance when relevant. Migration examples remain unchanged.

Install globally for Codex:

```sh
npx skills add https://github.com/geemarkwell/skill-repository --skill database-migrations --agent codex --global --yes
```

To require loading before every code-writing task, append this rule to `~/.codex/AGENTS.md` (preserve existing instructions):

```markdown
## Database migrations — required for code changes

Before writing, modifying, or refactoring code, always load the `database-migrations` skill. Do not wait for an explicit request. If it is not listed among available skills, read `~/.agents/skills/database-migrations/SKILL.md` or `~/.codex/skills/database-migrations/SKILL.md` directly. Assess database impact and apply its migration guidance when relevant, alongside the repository's `CLAUDE.md` and task-specific instructions. If the task has no database impact, proceed without adding migration work.
```

Start a new Codex session after changing global instructions.
