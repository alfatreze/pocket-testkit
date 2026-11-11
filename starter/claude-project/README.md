# Claude project starter: structure and test ladder

Copy these files into a project (Pocket core or any hardware or firmware project) and edit the `<...>` fields. They encode the workflow that worked in Tau Alpha: the owner decides, the agent works from a short status page and an evidence log, every result carries an evidence label, and cheap checks run before long ones.

| File | What it is |
|---|---|
| `CLAUDE.md` | Project instructions: session start, rules, roles (imports the rules file) |
| `AGENTS.md` | Pointer for other coding agents |
| `docs/PROJECT_RULES.md` | Nine rules: evidence labels, test ladder, mutation, long jobs, card writes, worktrees, diagnostics, licences, audit trail |
| `docs/CURRENT_STATUS.md`, `ROADMAP.md`, `AUDIT_TRAIL.md`, `DECISIONS.md`, `handoffs/TEMPLATE.md` | One status page, the order of work, the evidence log, recorded decisions, a handoff form |
| `ladder.json` + `tools/verdict.py` | The test ladder as data; one machine-readable verdict that cannot claim more than was run |
| `tools/check_pocket_json.py` | Validates a Pocket core folder's JSON against the documented limits |
| `tools/check_package.py` | Compares the file on the card with the build output (stale bitstream check) |
| `Makefile` | Ladder targets; the stubs fail until you fill them, so an empty rung never passes |
| `.claude/settings.example.json` | Example permission allow and deny lists |
| `.claude/skills/verify-ladder/SKILL.md` | A skill that runs the ladder and reports the verdict |

## Adopt it

1. Copy the folder's contents to the project root; rename `.claude/settings.example.json` to `settings.json` after reviewing it.
2. Fill the `<...>` fields in `CLAUDE.md` and `docs/CURRENT_STATUS.md`; edit `ladder.json` and the Makefile recipes to your commands (keep the rung names).
3. Run `python3 tools/verdict.py`. Manual rungs (fit, package, device) always report NOT RUN: that is the point.
4. For Pocket work add the [`analogue-pocket-dev`](https://github.com/alfatreze/analogue-pocket-dev-skill) skill and keep the Analogue docs local.

Background: [docs/TESTING_METHODS.md](../../docs/TESTING_METHODS.md). Claude Code docs: [memory and CLAUDE.md](https://docs.claude.com/en/docs/claude-code/memory), [settings](https://docs.claude.com/en/docs/claude-code/settings), [skills](https://docs.claude.com/en/docs/claude-code/skills), [subagents](https://docs.claude.com/en/docs/claude-code/sub-agents), [hooks](https://docs.claude.com/en/docs/claude-code/hooks).
