# Testing methods

One folder per method. Each README has the same sections: what it does, what it finds, when to use it, pros and cons, how it is done in this kit, references. To choose, see [choosing a method](../docs/choosing.md); for the thinking behind the order see [methodology](../docs/methodology.md).

| Phase | Method | Answers | Cost | In this kit |
|---|---|---|---|---|
| **Check before you build** | [file-checks](file-checks/README.md) | Are the JSON and the package files right? | seconds | tools + tests |
| | [host-tests](host-tests/README.md) | Is the algorithm, format or parser right? | low | used throughout |
| | [fuzzing](fuzzing/README.md) | Does a parser survive any input? | low | guide |
| | [formal](formal/README.md) | Can this control logic never overflow or deadlock? | medium | guide |
| **Simulate** | [simulation](simulation/README.md) | Does the RTL, or the whole core with a Pocket host model, behave? | minutes to an hour | testbenches for the link RTL |
| **Build gates** | [timing-fit](timing-fit/README.md) | Does it meet timing and fit? | minutes to hours | guide |
| **Observe on the device** | [report-codes](report-codes/README.md) | What did the device do, from anyone, with no cable? | none | **code + tests + real-device use** |
| | [debug-links](debug-links/README.md) | What are the live registers, memory, signals? | cable and a build | RTL simulated only |
| | [pocket-native](pocket-native/README.md) | Why does it fail to boot or load? | none | guide |
| **Process** | [ci](ci/README.md) | Did something break that nobody re-ran? | low | one workflow |
| | [effectiveness](effectiveness/README.md) | Which methods found real bugs, at what cost, across projects? | minutes per result | **tool + tests** (outcome records, ingest, report) |

"Guide" means the method is described with its trade-offs and references but no code is included. "Code" means tools and tests are in the folder. Nothing in this kit has been run on a Pocket except the report codes (real screenshots and photos of Tau Alpha's pages).
