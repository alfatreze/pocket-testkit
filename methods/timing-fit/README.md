# Timing, resources and fit gates

**Phase:** build gates · **Cost:** minutes (map) to hours (full fit) · **Status in this kit:** guide only

## What it does
Uses Quartus's own reports to decide whether a design is acceptable, in the cheapest order: block fits, a synthesis (map) gate, then the full fit.

## Gates, cheapest first
| Gate | Checks | Caveat |
|---|---|---|
| **Block fit** (a stand-alone Quartus project per block at the target clock) | A block meets the clock alone | An upper bound only: placement of the integrated design is worse. Use it to reject blocks that fail alone |
| **Map report gate** (after `quartus_map`) | Resource budget, inferred RAM modes and sizes, ignored SDC constraints, synchroniser chains turned into block RAM | Parse the report with a script and fail on a miss |
| **Timing estimate after synthesis** | An early slack estimate | Before placement there is no real routing delay: compare it with a past fit before trusting it |
| **Full fit** | Setup and hold in both corners, total negative slack, resource use | Hours; fit results vary by seed |

## Rules of thumb (community-reported unless noted)
- At 90-99% occupancy placement dominates timing: identical RTL spread about 1.2 ns over four seeds, and hold can fail in the fast corner while passing slow. One failing fit is not proof a change broke timing; three or four seeds are data, ten is a lottery.
- Fail the build on ignored SDC constraints (a multicycle aimed at a register that was merged away is silently dropped).
- Multi-bit clock crossings never use per-bit synchroniser chains; Quartus can turn synchroniser chains into block RAM.
- Say how long a fit will take and the finish time before launching it; do not poll.

## Pros and cons
| Pros | Cons |
|---|---|
| Real timing and resource evidence for the shipped build | Slow; hours per fit |
| Gates can run unattended | Seeds, and a build stamp, make bitstreams differ between identical runs |

## References
Quartus reports; the `analogue-pocket-dev` skill knowledge base: KB-009, KB-010, KB-011, KB-027, KB-051 ([repo](https://github.com/alfatreze/analogue-pocket-dev-skill)). Evidence for the rules above is community-reported; see [Pocket notes](../../docs/pocket-notes.md).
