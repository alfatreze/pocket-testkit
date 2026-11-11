# The Pocket's own debug tools

**Phase:** observe on the device · **Cost:** none (no extra hardware) · **Status in this kit:** guide only

## What it does
Uses what Analogue OS already provides, available to any developer without a cable.

## Tools
| Tool | What you get | Notes |
|---|---|---|
| **Debug Logging** | A detailed boot and load log in `/System/Logs/` on the SD card | Enable in Tools > Developer |
| **Debug event log (target command 0152)** | A time-stamped 32-bit value your core writes at runtime | The template never issues it, so add a sender; event rate and availability on retail units are not documented |
| **Asset Load Detail** | The file and data slot being loaded | Files under 512 KB may not show |
| **Pause Core Boot / Pause Load Data** | The Pocket halts until you press A, to arm a SignalTap trigger | No effect when a Chip32 loader runs |
| **Statistics overlay** | Video sync rate and status, temperature; power on developer units | |
| **USB SD access** | Pull logs and screenshots over USB-C at about 700 KB/s | Analogue+X attaches, Analogue+Y detaches |
| **JTAG reload** | The Pocket repeats the whole load with the same starting conditions | Enables an unattended reflash-and-retest loop; state is lost on reload |

## Pros and cons
| Pros | Cons |
|---|---|
| Free, shipping build, nothing to install | Narrow: boot, load, video sync and 32-bit events |
| Works for testers on their own units (where the Developer menu is available) | Availability on retail units and event rates are unverified |

## References
Analogue [debugging aids](https://www.analogue.co/developer/docs/debugging-aids), host and target commands; knowledge base KB-241 to KB-243 in the [skill](https://github.com/alfatreze/analogue-pocket-dev-skill). Details: [Pocket notes](../../docs/pocket-notes.md).
