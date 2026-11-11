# <Project name>: instructions for Claude Code

<One line: what this project is, e.g. an Analogue Pocket openFPGA core with a soft RISC-V CPU.>

## 1. Start of a session
1. Read `docs/CURRENT_STATUS.md` (one page: what is shipped, installed, in flight), then `docs/ROADMAP.md` (what is next; the owner sets the order), then the newest file in `docs/handoffs/`.
2. `docs/AUDIT_TRAIL.md` is the evidence log; `docs/DECISIONS.md` holds the owner's recorded decisions (do not re-litigate them).
3. For Pocket work load the `analogue-pocket-dev` skill and read its knowledge base before designing any experiment.

## 2. Rules
@docs/PROJECT_RULES.md

## 3. Roles
- **Claude:** does the work in this repo: design, code, host tests, simulation, docs, build scripts.
- **The owner:** sets priorities, approves card writes and long builds, tests on the device.
