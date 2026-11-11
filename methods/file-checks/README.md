# File checks

**Phase:** check before you build · **Cost:** seconds · **Status in this kit:** tools + host tests

## What it does
Validates the files a Pocket core ships with, before anything is copied to a card. The Pocket gives almost no feedback on a malformed JSON file: the core silently misbehaves or is missing from the menu. A stale bitstream on the card silently loads the old core.

## Finds
Invalid JSON, wrong `magic`, fields over the documented length limits, duplicate slot or variable ids, a `shortname` that does not match the folder, too many slots, a missing `.rbf_r`, a card file that differs from the build output.

## Use it when
Always, first: it is the cheapest rung of the ladder and runs before every install.

## Pros and cons
| Pros | Cons |
|---|---|
| Takes seconds, catches silent failures | Limits come from the docs and can change; not a full schema, so a pass does not prove the Pocket accepts the core |
| No hardware or Quartus needed | Cannot see runtime behaviour |

## In this kit
- [`check_pocket_json.py`](../../starter/claude-project/tools/check_pocket_json.py): `python3 tools/check_pocket_json.py path/to/Author.Core`
- [`check_package.py`](../../starter/claude-project/tools/check_package.py): compares SHA-256 of the build output and the card file
- Both are part of the [project starter](../../starter/README.md) and the test ladder. Tests: [`starter/tests/test_templates.py`](../../starter/tests/test_templates.py).

## References
Analogue's [developer docs](https://www.analogue.co/developer/docs) (JSON files section); `analogue-pocket-dev` skill ([`json-files.md`](https://github.com/alfatreze/analogue-pocket-dev-skill)).
