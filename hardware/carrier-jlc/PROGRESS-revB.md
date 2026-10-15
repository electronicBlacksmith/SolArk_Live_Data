# Board A (carrier-jlc) Rev B progress

Decisions (2026-10-13):
- J1 -> 5 THT wire pads (no part, no LCSC; NC spare dropped). Saves J1 fee, fixes item 2.
- XIAO on Sullins PRPC040SAAN-RC headers: drill 1.10 / pad 1.70 (Sullins rec. hole 1.00; JLC +0.13/-0.08 -> 1.02-1.23; ring 0.235 >= 0.20).
- U3 74LVC2G17GW C80500 (Ext), C9 100nF C307331, R7/R8 1k C11702, R5/R6 100k populated on BUF_IN, D3/D4 H5VL10B C7420372 (Preferred, pads 0.55x0.60 @ +-0.425), C5/C6 removed.
- TVS1 -> SMF18A C19077512 (Hongjiacheng, Preferred), same SOD-123FL.
- Divider R13 33k 0.1% 25ppm C728559 / R14 6.19k 0.1% 25ppm C705638 -> 5.065 V nom;
  PFM +2.5% ceiling 5.222 V, CCM floor 4.960 V; after PMEG4030ER 0.44 V max @1A -> 4.52 V.
- D2 keep PMEG4030ER (VF 440 mV max @1 A 25 C [V]); DSK34 only 550 mV @3 A.
- Status via JLC API selectSmtComponentList (jlc.py in scratchpad/a).

## Status 2026-10-13 (implementation)
- Done: design.py (parts, constants, JLC_STATUS, STACKUP, CPL_ROTATION), gen_lib (header THT 1.10/1.70,
  SOT363-2 Nexperia land, DFN1006 H5VL10B, 5 harness wire pads 2.54/1.0/1.7, 74LVC2G17 symbol),
  gen_sch (rev B notes), gen_pcb (PLACE, stackup insert, DNP pos), routes (rev B), build.sh/export_fab.sh
  fail on errors. Build rc=0, ERC 0, DRC 0; 16 tests pass (17 after the SOT363 pad-ring test). Board 27x27 (no growth).
- Done 2026-10-13: README (rev B), CHANGES-revB.md, PRICING.md, OPEN-ITEMS.md. Remaining: advisor review, handback.
- 2026-10-14 small fixes (VERIFY-revB.md): DRC rules from design.DRC_RULES >= design.JLC_MIN (ring 0.15, clearance 0.15, hole clearance 0.30); hand-fit kit design.KIT (headers, Kapton, harness 10k); shim required for spacer-off; C3 note. 22 tests.
