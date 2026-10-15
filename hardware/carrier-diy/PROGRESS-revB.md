# Rev B-diy progress (2026-10-13)

Status: **all deliverables written.** No git commits were made.

- Generators and tests are updated and `fab/` is regenerated.
- `sh scripts/build.sh` exits 0:
  - ERC: 0 violations.
  - DRC: 0 violations and 0 unconnected items, run at all severities.
  - Schematic parity: 0 issues.
- `pytest -q tests`: 23 passed.
- Docs: `README.md` (Rev B, including the hand-assembly order), `CHANGES-revB.md`, `PRICING.md` and `OPEN-ITEMS.md`.

Next steps for a human:
1. Resolve the OPEN-ITEMS "Before ordering" rows: O1 stack measurement, O2 enclosure room, O3 logic level.
2. Order route (b). Upload `fab/carrier_gerbers.zip` to OSH Park 4-layer and order `fab/carrier_bom_digikey.csv` from Digi-Key.
- 2026-10-13 late: TVS1 moved to Littelfuse's own SMF land (1.3 x 1.4, 1.6 gap), test-first; rebuilt clean.
- 2026-10-14: small fixes (fab-rule minimums, C3 to TDK C3216X5R0J107M160AB, harness 10 k in the kit); rebuilt clean, `pytest -q tests` 25 passed.
