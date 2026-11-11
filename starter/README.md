# Project starter: structure and test ladder for Claude projects

**Phase:** process · **Status in this kit:** tools tested on the host; the files are templates to adapt

Copy the files in [`claude-project/`](claude-project/) into a project (Pocket core or any hardware or firmware project) and edit the `<...>` fields. They encode the workflow that worked in Tau Alpha: the owner decides, the agent works from a short status page and an evidence log, every result carries an evidence label, and cheap checks run before long ones.

| File | What it is |
|---|---|
| `claude-project/CLAUDE.md` | Project instructions: session start, rules, roles (imports the rules file) |
| `claude-project/AGENTS.md` | Pointer for other coding agents |
| `claude-project/docs/PROJECT_RULES.md` | Nine rules: evidence labels, test ladder, mutation, long jobs, card writes, worktrees, diagnostics, licences, audit trail |
| `claude-project/docs/CURRENT_STATUS.md`, `ROADMAP.md`, `AUDIT_TRAIL.md`, `DECISIONS.md`, `handoffs/TEMPLATE.md` | One status page, the order of work, the evidence log, recorded decisions, a handoff form |
| `claude-project/ladder.json` + `tools/verdict.py` | The test ladder as data; one machine-readable verdict that cannot claim more than was run |
| `claude-project/tools/check_pocket_json.py` | Validates a Pocket core folder's JSON against the documented limits |
| `claude-project/tools/check_package.py` | Compares the file on the card with the build output (stale bitstream check) |
| `claude-project/Makefile` | Ladder targets; the stubs fail until you fill them, so an empty rung never passes |
| `claude-project/.claude/settings.example.json` | Example permission allow and deny lists |
| `claude-project/.claude/skills/verify-ladder/SKILL.md` | A skill that runs the ladder and reports the verdict |

## Adopt it

1. Copy the contents of `claude-project/` to the project root; rename `.claude/settings.example.json` to `settings.json` after reviewing it.
2. Fill the `<...>` fields in `CLAUDE.md` and `docs/CURRENT_STATUS.md`; edit `ladder.json` and the Makefile recipes to your commands (keep the rung names).
3. Run `python3 tools/verdict.py`. Manual rungs (fit, package, device) always report NOT RUN: that is the point.
4. For Pocket work add the [`analogue-pocket-dev`](https://github.com/alfatreze/analogue-pocket-dev-skill) skill and keep the Analogue docs local.

Background: [methodology](../docs/methodology.md), [AI workflow](../docs/ai-workflow.md), [methods](../methods/README.md). Claude Code docs: [memory and CLAUDE.md](https://docs.claude.com/en/docs/claude-code/memory), [settings](https://docs.claude.com/en/docs/claude-code/settings), [skills](https://docs.claude.com/en/docs/claude-code/skills), [subagents](https://docs.claude.com/en/docs/claude-code/sub-agents), [hooks](https://docs.claude.com/en/docs/claude-code/hooks).


## Tests
`python3 tests/test_templates.py` (from this folder): the verdict runner cannot claim more than was run, an unfilled Makefile stub fails, the JSON checks catch the documented mistakes, the package check compares files.
