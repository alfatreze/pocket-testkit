# Using an AI agent efficiently

Most of this kit assumes an AI agent writes and reviews much of the code while the owner directs it. These habits make that cheap and trustworthy. They come from a review against Analogue's docs and the `analogue-pocket-dev` knowledge base ([review](reviews/testing-audit-2026-11.md)); none was measured as a controlled comparison.

## What to give the agent
| Give | Why | Where |
|---|---|---|
| Project instructions and rules | One status page, an evidence log, recorded decisions | [starter](../starter/README.md) |
| The Pocket knowledge base | Stops invented facts; cite KB ids and treat community-reported entries as leads | [analogue-pocket-dev skill](https://github.com/alfatreze/analogue-pocket-dev-skill) |
| The kit's rules for report codes and debug links | Never raise QR density unasked, never call simulated RTL hardware-working | [`agent/AGENTS.snippet.md`](../agent/AGENTS.snippet.md) |

## Habits
1. **Separate the author of the oracle from the author of the design** (spec, real captures, a second reader, mutation).
2. **Make every check print one machine-readable verdict**; the agent reads the summary, not the log.
3. **Run the ladder cheapest first**; do not start a fit while a cheap rung fails.
4. **Turn each repeated mistake into a check**, not a reminder in a prompt: bridge reads treated as synchronous, per-bit synchronisers on buses, a stale `.rbf_r`, a pin tie-off copied from another core.
5. **One device trip, many questions**: ask for a self-testing build and a written test list.
6. **Do not poll long jobs**: launch in the background, state the finish time, resume on completion.
7. **Trust the source over the summary, and hardware over both**: the Pocket template does not implement every documented command.
8. **Report honestly**: the evidence label, and what was not run.

## Choosing methods
Give the agent the facts and let it follow [choosing a method](choosing.md); for debug links `methods/debug-links/tools/choose_link.py` encodes the rules. Do not let it guess project facts: it reads the fit report and the code.

## Mistakes worth turning into checks
| Mistake | Check |
|---|---|
| Malformed or over-limit JSON | `check_pocket_json.py` |
| Stale bitstream on the card | `check_package.py` |
| Multi-bit crossing through per-bit synchronisers | grep or lint; KB-009 |
| Ignored SDC constraint | parse the fit report; KB-027 |
| Wrong inferred RAM mode | parse the map report; KB-052, KB-058 |
| Test that cannot fail | mutation |
