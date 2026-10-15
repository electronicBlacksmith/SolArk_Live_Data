# Local DFM checks for the JLC carrier board

Research date 2026-10-14. KiCad 10.0.6 on macOS. Board: `hardware/carrier-jlc`.
Tags: **[V]** = checked against a primary source or reproduced in a local trial;
**[I]** = inferred, not confirmed.

## Why KiCad DRC passed and JLC DFM did not

- `carrier.kicad_pro` has `min_silk_clearance 0.0` and there is no
  `carrier.kicad_dru`. With a 0 clearance, KiCad only flags silk that actually
  overlaps a mask opening. JLC wants 0.15 mm. [V]
- KiCad's built-in DRC has no check for silk line width (it checks text only),
  THT-to-SMD spacing, or a "recommended" annular ring tier. Custom rules can add
  all three. [V]
- `--subtract-soldermask` cuts the silk at the mask opening edge. That leaves
  0 mm clearance, which JLC still flags. [I] (from the KiCad forum, see Sources)
- **Caveat:** `carrier.kicad_pcb` and `fab/` were regenerated at 22:04 today,
  possibly after the JLC upload. Some count mismatches below may come from that
  board change. [I]

## Trial

The trial ran on a copy of the board in the session scratchpad
(`scratchpad/dfm-trial/board`). Nothing in the repo was touched. Each rule
file was dropped in as `carrier.kicad_dru` and checked with
`kicad-cli pcb drc --severity-all --format json`. kicad-cli loads
`<project>.kicad_dru` from beside the `.kicad_pro` automatically. [V]

## JLC category → local check

| JLC flag (count) | Local check | Local count | Matters for our build? |
|---|---|---|---|
| Silkscreen to pad (49 red) | kicad-druid rule `JLCPCB: Pad to Silkscreen` (`silk_clearance` 0.15 mm) | **49, exact match** [V] | **Yes, fix it.** Silk is clipped off the pads, so the print gets ragged and refdes near pads become unreadable. This is cosmetic, but it is red at JLC and the fix is cheap (pull silk ≥0.15 mm off the pads). |
| Silkscreen line width (64 orange) | Project rule `assertion "A.Line_Width >= 0.15mm"` on silk graphics | **52 items** (54 gerber draws <0.15, 62 <0.153) [V] | **Yes, fix it.** All 50 lines, 1 circle and 1 polygon are 0.12 mm in our own generated footprints. JLC's minimum is 0.15 mm [V]. JLC counts gerber draws, not KiCad items, so the counts will never match exactly. |
| Silkscreen to hole (31 red) | Custom `physical_hole_clearance` 0.15 mm on silk (the condition form below) | **10** pairs (9 distinct holes, all vias) [V]. Did not match 31 at any threshold from 0.15 to 1.0 mm | **Low.** Every hit is a **tented** via (`tenting front/back yes`) [V]. Silk over a tented via prints a little uneven, nothing worse. Worth clearing the silk text that sits over vias (`12V OFF FOR USB`, `G`, `USB`). Count gap unexplained [I]. |
| THT to SMD (32 red / 18 orange) | Custom symmetric `physical_clearance` 2 mm, THT pad ↔ SMD pad | **32, exact match** [V]. Closest pairs: J1.5–D4.1 0.50 mm, J1.4–D3.1 0.50 mm, J1.5–C1.1 0.78 mm | **Mostly a JLC assembly note.** It matters for wave or selective THT soldering, and we hand-solder J1/U1. Real nuisance: D3/D4 sit 0.5 mm from J1 pins, so an iron can reflow or knock them. Mild margin is worth adding. The orange 18 did not match any band (2–2.5 mm gives 10, 2–3 mm gives 31) [I]. |
| Annular ring (33 orange) | Custom `annular_width` 0.2 mm on vias, warning severity | **26** (all vias: 0.6/0.3, ring 0.15) [V]. PTH rings are 0.30 (U1) and 0.35 (J1), so they are not the extra 7 | **No.** JLC multilayer PTH ring is min 0.15 / recommended 0.20 mm, and vias only need a diameter 0.1 mm (0.15 preferred) larger than the hole [V]. Our 0.15 ring is 3x the via requirement. This is a JLC process note. The 7-item gap is unexplained [I]. |
| Soldermask opening exposing trace (1 orange) | **Not expressible in KiCad DRC.** It needs "same net but not connected to this pad", and the rule language has no such test. Use the pcbnew script below | **1 at 0.05 mm margin** (R13.2, same-net `/FB` track near but not entering its pad); 3 at JLC's documented 0.09 mm (adds R6.2, C8.2) [V geometry, I that R13.2 is JLC's item] | **Check it.** An exposed same-net trace next to a pad can wick solder off the pad. Low risk for 0402/0603, but cheap to move. |
| Trace width, pad to board edge, pad spacing (green) | kicad-druid trace-width / edge-clearance rules plus the existing `min_copper_edge_clearance 0.3` | 0 [V] | No. Informational. |

Different-net mask bridging is already covered by KiCad's built-in
`solder_mask_bridge` check (`allow_soldermask_bridges_in_footprints no`). [V]

## Tools evaluated

| Tool | What it checks | Status | Licence | macOS install | KiCad 10 | Verdict |
|---|---|---|---|---|---|---|
| **Cimos/kicad-druid** (successor of Cimos/KiCad-CustomDesignRules) | JLC/PCBWay `.kicad_dru`: drill/annular, clearances, trace, silk-to-pad, text size, slots, edge. Generated from `capabilities/JLCPCB.toml`. Ships test boards and CI lint | v1.2.0, 2026-09-03 [V] | MIT [V] | Vendor one text file | README says syntax works on 8/9/10 [V]. Ran clean on 10.0.6 [V] | **Use it.** Declarative text, no code. Small project (37★, repo created 2026-08), so pin by SHA and review diffs. |
| labtroll/KiCad-DesignRules | Older JLC `.kicad_dru` (18 rules, KiCad 7) | Last push 2024-11 [V] | **No licence** [V] | n/a | untested | Skip (no licence, stale). ziteh/kicad-design-rules is a fork with the same push timestamp and 0★ [V]. |
| KiCad 10 built-in DRC + custom rules | Everything in the table except mask-exposing-trace | 10.0.6 installed [V] | GPL-3 | already present | yes | **Core of the stack** (it is what `build.sh` already runs). |
| KiBot (INTI-CMNB) | Wraps KiCad DRC/ERC as preflights. Has JLCPCB output templates (gerbers/drill/pos/BOM). **No geometry checks of its own** [V] | v1.9.1, 2026-07-28. KiCad 10 support in changelog [V] | AGPL-3.0 [V] | pip/Docker (big dependency tree) | yes [V] | Not needed. `build.sh` already does what it would. |
| KiKit (yaqwsx) | `kikit fab jlcpcb` exports files and runs KiCad DRC (`--drc`, on by default) [V]. Panelization. No extra DFM | v1.8.1, 2026-08-05. v1.8.0 added KiCad 10 [V] | MIT [V] | pip into the KiCad Python | yes [V] | Not needed for DFM. Consider only if we panelize. |
| Bouni/kicad-jlcpcb-tools | Action plugin: JLC parts DB, BOM/CPL, rotations, gerber zip, KiCad 10 variants [V]. **No DFM checks** | 2026.04.03, active [V] | MIT [V] | KiCad PCM | yes [V] | Not a DFM tool. |
| gerbonara (jaseg) | Gerber/Excellon/IPC-356 read/write/render library. No DRC [V] | 1.6.3, 2026-04-25 [V] | Apache-2.0 [V] | pip | n/a (gerber level) | Only useful for writing a gerber-level checker ourselves. Not needed now. |
| pcb-tools (curtacircuitos) | Gerber parsing/render | **Archived** [V] | Apache-2.0 | – | – | Skip. |
| gerbv | Gerber viewer. No DFM | v2.13.0, 2026-03 [V] | GPL-2.0 | brew (not allowed here) / source | n/a | Visual check only. |
| tracespace | JS gerber renderer/viewer | Last push 2025-01 [V] | MIT | npm | n/a | Visual check only. |
| aklofas/kicad-happy | AI-agent skill bundle. `analyze_pcb.py` (7.5k lines) does heuristic annular/via stats from its own S-expression parser. No geometric silk/mask checks [V] | very active [V] | MIT [V] | git | claims yes | Skip. It is a heuristic, fast-moving parser, not a geometry engine. |
| JLC online DFM (dfm.jlcpcb.com / order flow) | The real JLC categories | web only [V] | proprietary | browser | gerbers | Keep as the final check before ordering. Cannot run in CI. |
| JLCONE desktop | Quoting/ordering client (brew cask exists) [V] | – | proprietary | – | – | Whether it runs DFM offline is unconfirmed [I]. |
| NextPCB NextDFM / HQDFM | Full gerber DFM (closed freeware) | – | proprietary | Windows desktop [I] | gerbers | Not on macOS. Closed binary. Skip. |

No open-source tool reimplements JLC's DFM categories. Best available is KiCad
DRC with a JLC rule file, plus small pcbnew scripts. [V for the tools above; I
that nothing else exists]

## Recommended setup

### 1. `carrier.kicad_dru` (beside `carrier.kicad_pro`), the gate

- Vendor kicad-druid `JLCPCB/JLCPCB.kicad_dru` at tag **v1.2.0** (commit
  `8af046d6a1839320a360a4b6790ac11eb27a78ae`, sha256
  `6ffbe1bbbda83193781bc5df646cf1b9c44aa88ce0d311b2808bf5f5c399d0e7`).
- That file is the 4-layer, 1 oz outer / 0.5 oz inner variant. It matches our
  stackup: F/B.Cu 0.035 mm, In1/In2 0.0152 mm. [V]
- To respect the no-static-values rule, have the generator (`gen_pcb.py` or a
  new `gen_rules.py`) write the file:
  - vendored druid block, checked against the sha256;
  - then the project block, with thresholds taken from `design.py`;
  - plus a header that names the source tag and the JLC capabilities URL.
- **Order matters:** KiCad applies the *last* matching rule per constraint
  type, so the project block must come after druid's rules. [V, druid header]

```
# ===== Project additions (must stay AFTER the kicad-druid block) =====
# JLC: silkscreen min line width 0.15 mm. NOTE: a (layer ...) clause does NOT filter
# assertion constraints (it matched courtyard/fab/edge items: 170 hits), so the
# layer test lives in the condition (52 hits, all silk).
(rule "PROJECT: Silkscreen line width"
	(condition "(A.Layer == 'F.SilkS' || A.Layer == 'B.SilkS') && A.Type != 'Text' && A.Type != 'Text Box'")
	(constraint assertion "A.Line_Width >= 0.15mm"))
```

Two rectangles have silk at exactly 0.15 mm. They pass this rule, but may be
among JLC's 64 orange flags. If JLC still flags them, raise the threshold to
0.153 mm (6 mil); that gives 62 gerber draws, close to JLC's 64.

This gate block, plus druid, currently fails `export_fab.sh` (exit 5) on 49
silk-to-pad and 52 silk-width violations. That is intended: fix the footprints
in `gen_lib.py` before ordering. No change to `export_fab.sh` is needed. Its
existing `--severity-all --exit-code-violations` run picks the file up. [V]

### 2. Advisory pass (never fails the build)

THT-to-SMD, silk-to-hole and the annular tier are JLC process notes for us. A
`(severity warning)` rule **still fails** the current gate, because it runs
with `--severity-all` [V: exit 5]. Two options were rejected:

- Switching the gate to `--severity-error`. Project warnings such as
  `silk_over_copper` would then stop gating.
- `(severity exclusion)`. It does pass with `--severity-error --severity-warning`
  [V], but it misuses exclusions.

Instead, run a second DRC on a temporary copy that uses an advisory rule file
(the gate file plus the rules below), and print a summary:

```
(rule "ADVISORY: THT pad to SMD pad < 2 mm (JLC THT-to-SMD)"
	(severity warning)
	(condition "A.Type == 'Pad' && B.Type == 'Pad' && ((A.Pad_Type == 'Through-hole' && B.Pad_Type == 'SMD') || (A.Pad_Type == 'SMD' && B.Pad_Type == 'Through-hole'))")
	(constraint physical_clearance (min 2mm)))
(rule "ADVISORY: Silkscreen to hole < 0.15 mm (JLC silkscreen-to-hole)"
	(severity warning)
	(condition "A.Layer == 'F.SilkS' || A.Layer == 'B.SilkS' || B.Layer == 'F.SilkS' || B.Layer == 'B.SilkS'")
	(constraint physical_hole_clearance (min 0.15mm)))
(rule "ADVISORY: Via annular ring < 0.2 mm (JLC multilayer recommended)"
	(severity warning)
	(condition "A.Type == 'Via'")
	(constraint annular_width (min 0.2mm)))
```

Sketch for `scripts/dfm_advisory.sh`, called at the end of `build.sh` and
always exiting 0:

```sh
T=$(mktemp -d)
# fp-lib-table + lib/ are needed, or 7 spurious lib_footprint_issues appear
cp -R carrier.kicad_pcb carrier.kicad_pro fp-lib-table lib "$T"/
cat carrier.kicad_dru scripts/advisory.dru.part > "$T"/carrier.kicad_dru
$K pcb drc --severity-all --format json -o "$T"/adv.json "$T"/carrier.kicad_pcb >/dev/null || true
python3 -I -c 'import json,sys,re,collections as c; v=json.load(open(sys.argv[1]))["violations"]
for k,n in c.Counter((re.search(r"rule \x27([^\x27]*)\x27",x["description"]) or [0,x["type"]])[1] for x in v).items(): print(n,k)' "$T"/adv.json
$KPY -I scripts/dfm_mask_check.py carrier.kicad_pcb 0.05 || true
rm -rf "$T"
```

This sketch, including the exact summary one-liner, was run on a scratch
copy. Results:

- with only pcb + pro copied: 7 `lib_footprint_issues` appeared;
- with `fp-lib-table` + `lib/` added: those went away (169 violations, all
  real). [V]

Measured with the advisory file on today's board:

| Rule | Count |
|---|---|
| THT-SMD | 32 |
| Silk-to-hole | 10 |
| Annular tier | 26 |
| Silk width (gate) | 52 |
| Silk-to-pad (gate) | 49 |

[V]

### 3. Mask-exposing-trace script (pcbnew API, no extra dependencies)

Trial script, run with the KiCad bundled Python as
`$KPY -I script.py carrier.kicad_pcb 0.05`:

```python
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
margin = int(float(sys.argv[2]) * 1e6)          # mm -> nm, from config
found = []
for cu, mk in ((pcbnew.F_Cu, pcbnew.F_Mask), (pcbnew.B_Cu, pcbnew.B_Mask)):
    aps = [(p, p.GetSolderMaskExpansion(cu), f"{fp.GetReference()}.{p.GetNumber()}")
           for fp in b.GetFootprints() for p in fp.Pads() if p.IsOnLayer(mk)]
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK" or t.GetLayer() != cu:
            continue
        ts = t.GetEffectiveShape(cu)
        for p, e, name in aps:
            ps = p.GetEffectiveShape(cu)
            if not ts.Collide(ps, e + margin):
                continue
            same = t.GetNetCode() == p.GetNetCode()
            if same and ts.Collide(ps, 0):
                continue                         # normal pad entry
            found.append((name, "same-net" if same else "diff-net", t.GetNetname()))
for f in found:
    print(f)
print("total", len(found))
```

`GetSolderMaskExpansion(F_Cu)` returns the local margin correctly (TH1/TH2:
148000 nm). [V]

What it does:

- Take each pad that has an opening on F/B.Mask.
- For each track on the matching copper side, test
  `track.Collide(pad, expansion + margin)`.
- Skip same-net tracks that actually touch the pad (normal pad entry).
- Report everything else.

`margin` comes from config: 0.05 mm reproduces JLC's single flag, and 0.09 mm
is JLC's documented "mask opening to neighbouring trace". This is new feature
code, so per the repo rules it needs TDD:

- a pytest that builds a tiny board via pcbnew (one pad, one same-net stub
  0.04 mm away, one connected track), with the expected result 1 hit;
- `ruff`/`mypy --strict` if it lives under `tools/`.

### 4. Rule regression fixture (recommended)

KiCad can silently disable a check. Seen in the trial:

- **A `(layer "?.SilkS")` clause on a `physical_hole_clearance` rule switched
  off the THT-to-SMD `physical_clearance` rule completely** (0 instead of 32).
  Rewriting the layer test as a condition fixed it. [V, KiCad 10.0.6]
- A one-directional THT→SMD condition matched 0 pairs. The symmetric form is
  required. [V]
- An unknown severity (`info`) silently turned the rule off, with no parse
  error. [V]

Keep a small known-bad board with one violation per rule (druid's test-board
approach), and assert the exact per-rule counts in `make check`. Without that,
a KiCad upgrade or a rule edit can quietly drop a check.

## Risks

- **Count drift vs JLC.** JLC counts gerber primitives with its own thresholds
  (silk width 64 vs our 52; silk-to-hole 31 vs 10; annular 33 vs 26). Local
  checks are a pre-filter. Still run JLC's online DFM before paying. [V/I]
- **Upstream rule file trust.** kicad-druid is small and young. It is a
  declarative text file (no executable code), the full 272 lines were reviewed
  in this trial, and it is pinned by tag + sha256. Re-review the diff on each
  bump, and check thresholds against
  https://jlcpcb.com/capabilities/pcb-capabilities, which changes over time.
- **Threshold choices are ours:**
  - 2 mm THT-SMD was fitted to JLC's count; JLC publishes no number [I].
  - 0.2 mm annular tier is JLC's PTH recommendation applied to vias [I].
- **Board changed after upload.** Re-run JLC DFM on the current gerbers to
  confirm the mapping. [I]
- **Security.** No new executables beyond KiCad. No network at build time once
  the rule file is vendored. Uploading gerbers to JLC's web DFM discloses the
  design, which ordering does anyway.

## Sources

- kicad-druid: https://github.com/Cimos/kicad-druid (README, JLCPCB/JLCPCB.kicad_dru @ v1.2.0, TESTBOARD.md)
- labtroll: https://github.com/labtroll/KiCad-DesignRules
- JLC capabilities: https://jlcpcb.com/capabilities/pcb-capabilities
- JLC web DFM: https://dfm.jlcpcb.com
- KiCad forum, JLC silkscreen overlap: https://forum.kicad.info/t/jlcpcb-silkscreen-overlap/58557
- KiCad forum, JLC design rules: https://forum.kicad.info/t/design-rules-for-jlcpcb/46087
- KiBot: https://github.com/INTI-CMNB/KiBot (CHANGELOG, docs/source/configuration/preflights/DRCOptions.rst)
- KiKit: https://github.com/yaqwsx/KiKit (releases v1.8.0/v1.8.1, docs/fabrication/intro.md)
- kicad-jlcpcb-tools: https://github.com/Bouni/kicad-jlcpcb-tools
- gerbonara: https://github.com/jaseg/gerbonara, https://pypi.org/project/gerbonara/
- pcb-tools: https://github.com/curtacircuitos/pcb-tools
- gerbv: https://github.com/gerbv/gerbv
- tracespace: https://github.com/tracespace/tracespace
- kicad-happy: https://github.com/aklofas/kicad-happy
- JLCONE cask: https://formulae.brew.sh/cask/jlcone
- NextDFM: https://nextpcb.com/about-nextdfm.html
