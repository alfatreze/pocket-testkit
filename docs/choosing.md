# Choosing a testing method

Start from the question, not the tool. Details per method are in [methods/](../methods/README.md).

## By question

| Question | First choice | Then |
|---|---|---|
| Are my JSON and package files right? | [File checks](../methods/file-checks/README.md) | |
| Is my algorithm, parser or format right? | [Host tests](../methods/host-tests/README.md) | [Fuzzing](../methods/fuzzing/README.md) for parsers |
| Does a small control block never overflow or deadlock? | [Formal](../methods/formal/README.md) | simulation |
| Does my RTL do what I think, and is it wired right? | [Simulation](../methods/simulation/README.md) | whole-core simulation |
| Will it meet timing and fit? | [Timing and fit](../methods/timing-fit/README.md) | |
| What did the device do, when someone else ran it or I am away from my desk? | [Report codes](../methods/report-codes/README.md) | the [event log](../methods/pocket-native/README.md) |
| What are the live registers, memory or signals, at my desk? | [Debug links](../methods/debug-links/README.md) | [CHOOSING](../methods/debug-links/CHOOSING.md) picks the link |
| Why does it fail to boot or load? | [Pocket's own tools](../methods/pocket-native/README.md) | Pause Core Boot with SignalTap |
| Did a change break something nobody re-ran? | [CI](../methods/ci/README.md) | |

## By situation

| Situation | Use |
|---|---|
| New project | The [project starter](../starter/README.md), then file checks and host tests |
| About to spend hours on a fit | The cheap rungs first ([ladder](methodology.md#1-the-ladder-cheapest-first)) |
| A tester sends a screenshot or photo | [Report codes](../methods/report-codes/README.md) (decode it) |
| Closed retail unit, on the move | Report codes, the event log, or a serial UART ([SERIAL](../methods/debug-links/SERIAL.md)) |
| At a desk with a genuine Blaster | A debug link |
| An AI agent does most of the work | [AI workflow](ai-workflow.md) |

## Rule of thumb
Prefer the method that answers the question **earliest on the ladder**. Use report codes when the data must leave the device without a cable or a person with tools; use a debug link when you need live access at a desk; do both when you can: a link to find the bug, a report code to prove the fix on the shipped build.
