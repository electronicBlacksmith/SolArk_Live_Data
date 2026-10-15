# Rev B fix progress (handoff for the next session)

Work order: `review-synthesis.md` (detail in `review-fable.md`). Rule: change the
generators (`scripts/design.py`, `gen_lib.py`, `gen_sch.py`, `gen_pcb.py`,
`routes.py`, `build.sh`, `export_fab.sh`) and `tests/`, never the outputs by
hand. Nothing has been committed, ordered, uploaded or posted.

Build: `sh hardware/carrier/scripts/build.sh` (kicad-cli at
`/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`, bundled Python at
`/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3`).
Tests: `tools/.venv/bin/pytest hardware/carrier/tests` (6 pass on the rev A
sources). Pad dump for placement work:
`cd hardware/carrier && $KPY -I scripts/gen_pcb.py place` (needs `carrier.net`).

## State of the files

**No generator, test, README or fab output has been modified.** The only new
file from this session is this one (an interim `HANDOFF-revB.md` was folded in
and removed). `docs/hardware/README.md` shows as modified in git, but that was
already the case before this session started. The rev A build and tests pass
as they did before.

All of the session went into research and a placement/routing plan; the
advisor reviewed the plan (notes folded in below). Implementation starts from
section "Next steps".

## Review-synthesis items: status

| Item | Status | Decision / notes |
|---|---|---|
| 1 Socket holes | planned, not edited | drill 1.65 / pad 2.2 (numbers below); fix "press-fit" wording in README (~lines 135, 197, 217) and `gen_lib.py` descr |
| 4 Flat-solder option | decided, not edited | drop the castellation pads (geometry below); justify in README |
| 6 RX buffer (user approved) | parts verified, not edited | 74LVC2G17GW C80500; ESD C110695; chain and bias below |
| 7 VBUS margin | solved, not edited | 20k + 1.69k / 4.02k 0.1 %; 5.117 V nominal, 5.02–5.22 V |
| 8 Buck hot loop | planned, not edited | F.Cu GND return U2.2 -> C1.2, FB on In2, GND vias beside U2.2 and C1.2 |
| 9 C3 sizing | decided, not edited | keep 100 µF 6.3 V X5R 1206 (C15008); droop maths below; polymer does not fit |
| 10 Test points | planned, not edited | bottom side, right column; list below |
| 5 USB backfeed | not started | delete `docs/hardware/README.md` step ~326–329; "J1 OFF FOR USB" silk |
| 2 J1 envelope | planned, not edited | add bottom-side direct-solder pad set HP1 under J1; do not move J1 |
| 12–13 Housekeeping | not started | build.sh fail on errors; JLC04161H-7628 stackup; DNP pos exclusion; silk 1.0; rotation table |
| 11 Regenerate | not started | after everything else; do not regenerate until the generators are consistent |

## Parts (all verified on primary sources this session)

### U3 buffer: Nexperia 74LVC2G17GW,125 — LCSC **C80500**

- SOT-363 (Nexperia TSSOP6 / "SOT363-2"), JLC **Extended**, 8,160 in stock at
  LCSC, $0.089 @5+. Pages: https://jlcpcb.com/partdetail/C80500 ,
  https://www.lcsc.com/product-detail/C80500.html
- Datasheet Rev. 12 (21 Aug 2023):
  https://assets.nexperia.com/documents/data-sheet/74LVC2G17.pdf
- Pinout (SOT-363, top view, pin 1 top-left): 1 = 1A, 2 = GND, 3 = 2A,
  4 = 2Y, 5 = VCC, 6 = 1Y.
- VCC 1.65–5.5 V; inputs 5 V tolerant (abs max VI +6.5 V); IOFF ±2 µA max
  (VI or VO = 5.5 V, VCC = 0) so an unpowered XIAO cannot load the tap;
  II ±1 µA max; ICC 4 µA max; CI 3.5 pF typ.
- Schmitt thresholds at VCC = 3.0 V: VT+ 1.30–2.20 V (−40..85 °C; 2.40 max at
  125 °C), VT− 0.60–1.50 V (1.70 max at 125 °C), hysteresis 0.40–1.20 V.
- HBM > 2000 V, CDM > 1000 V. Height 1.1 mm max.
- Alternate (clone): JSMSEMI 74LVC2G17GW-JSM **C53436267**, Extended, 2,560
  in stock. Use only if C80500 is out of stock; same pinout.
- Note: the Seeed/review wording said "SN74LVC2G17" (TI). TI's DCK/DBV parts
  were not chosen; the Nexperia GW (SOT-363) part is what is BOMed, and its
  datasheet numbers (above) are the ones to design against (they differ from
  TI's).
- KiCad's `74xGxx:74LVC2G17` symbol does not use `extends` but is multi-unit;
  `gen_sch.py` only handles single-unit symbols, so add a 6-pin symbol to
  `lib/carrier.kicad_sym` with `gen_lib.symbol()` (as done for LMR51610).
  Footprint: `Package_TO_SOT_SMD:SOT-363_SC-70-6` (courtyard ±1.495 × ±1.145,
  pads 1.02 × 0.35 at x ±0.838, y −0.65/0/+0.65; 1,2,3 left top->bottom,
  4,5,6 right bottom->top).

### D3/D4 tap ESD: Prisemi PESDNC2FD5VBS — LCSC **C110695**

- DFN1006-2L, JLC **Extended**, 476,200 in stock, $0.0078 @100+ (MOQ 100 at
  LCSC; JLC assembly pulls from its own stock). https://jlcpcb.com/partdetail/C110695
- Datasheet: https://datasheet.lcsc.com/datasheet/pdf/4ed0a42bb5af4b8d9b79f8083222ae7c.pdf
  (the `lcsc.com/datasheet/C110695.pdf` link returns HTML). Bidirectional,
  VRWM 5.0 V, VBR 5.6 V min @1 mA, IR 1 µA max @5 V, VC 7.5 V @1 A and
  9.5 V @5 A (8/20 µs), Cj 12 typ / 15 pF max @0 V 1 MHz, IEC 61000-4-2/-4-4.
- Package dims (mm): A 0.34–0.50 (height), C 0.95–1.075 (length), D 0.55–0.675
  (width), E 0.45–0.55 (terminal width), F 0.20–0.30 (terminal length), H 0.40
  typ (terminal gap).
- Land pattern drawing (datasheet p.5, "Unit: mm"): two pads 0.40 wide (x)
  × 0.60 (y), pad pitch 0.90, overall 1.30 × 1.10. Reading of the 1.10 figure
  is ambiguous (overall y extent); pad 0.40 × 0.60 at ±0.45 is the safe
  reading. Make a project footprint `carrier:DFN1006-2L` with pads 0.40 × 0.60
  at x ±0.45, courtyard ±0.90 × ±0.60, F.Fab body 1.0 × 0.6. (KiCad's
  `Diode_SMD:D_SOD-882` has pads 0.40 × 0.70 at ±0.35, pitch 0.70 — too
  narrow for this part's 0.90 recommendation.) Fits an 0402-sized slot.
- Rejected: CESDBLC5V0D5 C2910118 (SOD-523, 12 pF): the SOD-523 courtyard
  (±1.295 × ±0.745) is too tall for the row above J1.
- Why 12 pF is fine: Modbus 9600 8N1, source impedance ≈ 11 k (10 k off-board
  + 1 k R3/R4); 11 k × 15 pF = 165 ns << 104 µs bit time.

### Divider (item 7), all 0402 0.1 %, JLC Extended

| Ref | Value | Part | LCSC | Stock (LCSC) |
|---|---|---|---|---|
| R13 | 20 k 0.1 % ±10 ppm | RESI PTFR0402B20K0N9 | **C351700** | 192,195 |
| R14 | 1.69 k 0.1 % ±25 ppm | YAGEO RT0402BRD071K69L | **C723583** | 22,100 |
| R15 | 4.02 k 0.1 % ±25 ppm | RESI PTFR0402B4K02P9 | **C2692896** | 6,820 |

Chain: +5V_BUCK -> R13 20 k -> FB_TOP -> R14 1.69 k -> FB -> R15 4.02 k -> GND
(top = 21.69 k). Vout = 0.8 × (1 + 21.69/4.02) = **5.117 V**.
Window: Vfb 0.788–0.812 (LMR51610 ±1.5 %), ratio ±0.2 % (two 0.1 % parts),
tempco ≤35 ppm/°C × 100 °C ≈ 0.35 % -> ±0.55 % on k, ×k/(1+k) = 0.843 ->
±0.46 %; total ≈ ±1.96 % -> **5.017–5.217 V at the buck (≤5.25 V)**.
After D2 (PMEG4030ER): typical ≈ 4.82 V, worst-min ≈ 4.62 V at the XIAO 5V
pin (VF 0.30–0.45 V, see D2 note below). LMR51610 datasheet: Vfb
0.788/0.800/0.812, RFBT 10–100 k recommended, FB resistors close to the pin,
CIN close to VIN/GND.
Rejected: 22.1 k/4.02 k (5.198 V nominal but 5.285 V max at the buck;
C852648 also only 500 in stock, MOQ 50). Not stocked at LCSC: 21.5 k, 6.49 k,
5.36 k, 53.6 k, 5.49 k; 53 k C852836 out of stock. Other 0.1 % options seen:
10 k C328417 (109,290), 1 k C478866, 1.02 k C2692916 (390), 1.2 k C4101652.
All 0.1 % parts are Extended: note the per-part Extended fee in the README.
Test to update: `test_feedback_divider_sets_about_5v` must sum R13+R14 over
R15 and assert the 5.02–5.22 window (it currently reads R13/R14 only).

### Bias / buffer passives (populated in rev B)

- R5/R6 100 k (C25741, Basic) now **populated**, from BUF_IN_x to +3V3.
  Dongle low (≈0 V) through 11 k vs 100 k -> 0.33 V < VT− min 0.60 V ✓.
  Buffer input leakage 1 µA × 100 k = 0.1 V shift ✓. Unpowered/absent dongle:
  inputs sit at 3.3 V (UART idle = mark) -> no float, no oscillation ✓.
  Documented exception to "nothing drives the tap": with the dongle unpowered
  and the XIAO powered, 3V3 sources ≤30 µA into the dead dongle pin through
  111 k. That is a bias current, not a GPIO drive; record this decision in
  the README passivity section.
- R7/R8 1 k (C11702, Basic) from U3 outputs to RX_x (XIAO D0/D1); keeps the
  "small series R" the review asked for.
- C9 100 nF (C307331, Basic) on U3 VCC, placed beside U3.
- C5/C6 100 pF DNP filters move to BUF_IN_x–GND on the bottom under the
  strip (keep DNP; exclude from BOM and CPL).
- ESP32-S3 datasheet v2.2 Table 2-2: GPIO1 and GPIO2 (XIAO D0/D1) have a
  ~60 µs low-level glitch at power-up. Harmless here: GPIO1/2 are inputs to
  UART RX only, and the buffer output is driven through 1 k. Record in
  `docs/hardware/README.md` §8 glitch row.

### Socket (item 1), Mill-Max 7305-0-15-15-47-27-10-0

Datasheet: solder-mount only (press-fit N/A). Hole .063" = 1.600 mm
recommended; shell 1.499 mm (1.55 max with +0.051); flange dia 1.956,
flange length 0.356, overall 2.667; tail below a 1.6 board = 0.71 mm.
Choice: **drill 1.65, pad 2.2** (`THT_PAD, THT_DRILL = 2.2, 1.65`).
- JLC finished hole = drill +0.13/−0.08 -> 1.57–1.78. Fit: 1.57 ≥ 1.55 ✓
  (drill 1.60 would give 1.52 min < 1.55 max shell: no-fit risk).
- Annular ring worst case (2.2 − 1.78)/2 = 0.21 ≥ 0.20 ✓.
- Pad-to-pad gap at 2.54 pitch: 0.34 ✓. No track fits between pins on any
  layer (THT pads are on all four); everything crossing from the J1 side to
  the top-left strip goes around the pin-row ends (left end: pad edge of pin
  8/1 column at x 106.165 -> tracks at x ≤ 105.9).
- Plus castellation copper is 1.346 mm from the pin centre: 2.2 mm pads leave
  0.25 mm, the socket flange (r 0.978) leaves 0.37 mm and sits 0.3 mm below
  the XIAO anyway. Flat-mount (castellation) option dropped: the official
  Seeed Plus SMD pattern (`lib/seeed/XIAO-ESP32-S3-Plus-SMD.kicad_mod`:
  pads 1–14 2.032 × 0.95 at y ±8.255, 15–23 at y ±8.655, underside 24–34)
  cannot coexist with ≥2.2 mm socket pads.
- gen_lib.py: remove `SMD_W, SMD_L, SMD_C` and the castellation pads,
  courtyard from the XIAO body (±8.9, unchanged in size), descr -> "solder-
  mount Mill-Max 7305", silk text 0.8 -> 1.0, `TAIL = 0.71` [V]. Stack height
  table: XIAO 4.9 and receptacle flange 0.3 remain [inferred].

### C3 (item 9)

Droop budget: 0.5 A step × ~16 µs (buck loop) / 0.3 V ≈ 27 µF effective.
100 µF 6.3 V X5R 1206 at 5 V bias ≈ 30–40 µF [inferred; Samsung DC-bias page
returned HTTP 500]. Low-profile polymer does not fit the 1206 slot or the
height; keep C15008, document the derating and the USB hot-plug inrush
trade-off (bigger C3 = bigger inrush when a plain USB cable is connected).

### Stackup (item 13), JLC04161H-7628 from gsuberland/jlcpcb_autogenerated_stackups

`kicad_stackups/jlcpcb_4L_1.6mm_outer1oz_inner0.5oz_JLC04161H-7628.kicad_pcb`
(copy was in the scratchpad `dl/jlc7628.kicad_pcb`; re-download if needed).
F.Mask 0.01524 "JLCPCB Soldermask" εr 3.8; F.Cu 0.035; prepreg 0.2104
"Nan Ya Plastics NP-155F 7628" εr 4.4 tanδ 0.02; In1.Cu 0.0152; core 1.065
"Nan Ya Plastics NP-155F Core" εr 4.43; In2.Cu 0.0152; prepreg 0.2104; B.Cu
0.035; B.Mask 0.01524; `(copper_finish "None") (dielectric_constraints yes)`.
pcbnew's `GetStackupDescriptor()` has no `GetList` in the bundled Python, so
insert the `(stackup ...)` block into `(setup ...)` by post-processing the
saved `carrier.kicad_pcb` with `sexp.py` at the end of `gen_pcb.main()`, then
check `fab/gerbers/*.gbrjob` shows the 0.0152 inner copper.

## Placement plan (top side only; no bottom assembly)

Board 100..127 × 100..127. Fixed: U1 courtyard x 104.376–127.045, y
100.455–118.345; J1 courtyard x 100.575–112.625, y 120.505–126.995 (pads 0.6 ×
1.7 at y 121.9: pad1 x 103.475, pitch 1.25 -> pad5 108.475, pad6 109.725; MP
pads (101.625,125.1)/(111.575,125.1) 1.0 × 2.7). Copper-to-edge 0.3, netclass
clearance 0.15, hole-to-hole 0.5, via 0.6/0.3. 0402 courtyard 1.95 × 1.03.

### Left strip (x 100.3–104.376), top to bottom

1. Row y ≈ 100.75: R5 at x 101.275 rot 0 (pads 100.765 / 101.785), R6 at
   x 103.325 (pads 102.815 / 103.835). R5-left = BUF_IN_RESP, R5-right =
   +3V3, R6-left = +3V3 (joined to R5-right on F.Cu), R6-right = BUF_IN_REQ.
   +3V3 via at (101.785, 101.3) touching R5-right.
2. U3 at (101.8, 103.2) **rot 90** (2.29 wide × 2.99 tall; courtyard
   101.705–104.695). One pin row at y ≈ 102.362 (inputs at the ends x 101.15
   and 102.45, GND in the middle), the other at y ≈ 104.038 (outputs at the
   ends, VCC in the middle). Verify which row is which with the `place` dump
   and assign RESP/REQ to whichever input ends up where. Vias overlapping the
   end pads: left input (100.62, 102.362), right input (102.98, 102.362), left
   output (100.62, 104.038), right output (102.98, 104.038). GND pin: via
   above the row at (101.8, 101.6) or use the F.Cu pour. VCC: via at
   (101.8, 104.85) fed on B.Cu from the +3V3 via, F.Cu track to the VCC pad
   and right along y 104.85 to C9.
3. C9 at (103.85, 103.2) rot 90 (courtyard 103.335–104.365): lower pad
   +3V3 (from the y 104.85 track), upper pad GND with via at ~(103.9, 101.9).
4. TVS1 centre y 107.04 (courtyard 104.795–109.285), D1 centre y 111.78
   (109.385–114.175), F1 unchanged (114.305–120.295). Move the +12V_P
   track/via at y 108.9 accordingly.
Strip budget: 1.03 + 2.99 + 4.49 + 4.79 + gaps = 13.7 of 14.0 mm.

### Row above J1 (y 118.345–120.505): seven rot-90 0402 slots

Slot centres x = 104.95, 106.10, 107.25, 108.40, 109.55, 110.70, 111.85 at
y 119.35 (courtyard 118.375–120.325; pads at y ≈ 118.84 and 119.86).
Assignment left to right: R7 (RESP out), R8 (REQ out), R3, D3, D4, R4, R15.
- D3 (slot 108.40) and D4 (109.55) sit over J1 pads 5/6 (108.475/109.725):
  lower pad = TAP_x from the J1 pad on F.Cu, upper pad = GND with a GND via
  at ~(108.95, 118.5).
- R3/R4: lower pad = TAP_x (F.Cu from D3/D4), upper pad = BUF_IN_x -> via at
  y ≈ 118.35 **between** XIAO pin columns (pins 8–10 at x 107.315, 109.855,
  112.395; a via must be ≥1.6 mm from a non-GND pin centre, i.e. at a pin's
  x it needs y ≥ 118.62, at the mid-column x (108.585, 111.125) y ≥ 117.99).
- R7/R8: lower pad = BUF_OUT_x via at (x, 120.55) (via bottom edge 120.85 vs
  J1 pad tops 121.05 -> 0.20 clearance), upper pad = RX_x via at y ≈ 118.4.
- R15 (slot 111.85): upper pad FB, lower pad GND with a via at (111.85, 120.55).
- Four vertical In2 tracks run up the band x 104.3–105.65 (0.45 pitch; clear
  of the +12V_P via at (103.6, 108.9)) between the strip and the pin-8 column:
  BUF_IN_RESP to the (100.62,102.362) via (approach at y 101.4, above the
  right-input via), BUF_IN_REQ to (102.98,102.362), BUF_OUT_x from the
  output vias down to the R7/R8 lower vias, RX_x up to y 103.4/104.2 then
  across on In2 straight into U1 THT pads 1 (122.555,101.78) / 2 (120.015,
  101.78).
- +3V3 on B.Cu from U1 pin 12 (117.475,117.02) up at x ≈ 117.5 to y ≈ 105.5,
  left to x ≈ 105.5, up to y ≈ 100.8, left to the (101.785,101.3) via.

### Divider / FB (right of J1, y 119.75 row unchanged in x)

R14 at 113.67 rot 180 becomes 1.69 k: pad 1 (114.18) = FB_TOP, pad 2 (113.16)
= FB. R13 at 115.67 becomes 20 k: pad 1 (116.18) = +5V_BUCK (existing In2 hop
to C7.1), pad 2 (115.16) = FB_TOP. FB from R14.2 to R15's upper pad on F.Cu
(113.16,119.75) -> (112.5,119.2) -> (111.85,118.84), and to U2.3 via In2:
FB via at (112.5, 119.3), In2 to a via at (115.08, 122.263) left of U2 pad 3
(FB pad 115.55–116.15; 0.15 clearance, hole clearance 0.32), short F.Cu
stub into pad 3.

### Hot loop (item 8)

U2 rot 270: pads 1.32 × 0.60; 1 CB (117.75,122.263), 2 GND (116.8,122.263; y
121.603–122.923), 3 FB (115.85,122.263), 4 EN (115.85,124.537), 5 VIN
(116.8,124.537), 6 SW (117.75,124.537). C1 pads 1.15 × 1.80: 1 +12V_P
(113.85,124.875), 2 GND (113.85,121.925; y 121.025–122.825). C2 pads
(115.82,126.1) +12V_P / (116.78,126.1) GND. C7 (0805) pad 1 +5V_BUCK
(119.45,119.75), pad 2 GND (117.55,119.75).
- F.Cu GND return 0.4 wide: U2.2 top -> (116.8,121.2) -> (114.0,121.2) ->
  C1.2 (edges 121.0–121.4; 0.2 from pad 3 top at 121.603). Keep U2.2 -> C7.2.
- GND vias: (116.8,121.1) beside/overlapping U2.2 (0.35 from pads 1 and 3),
  (113.5,120.7) beside C1.2, keep (117.55,126.3) at C2.2. Move the existing
  GND via at (113.0,120.85) to ~(112.7,121.6).
- FB leaves on In2 (shielded by the In1 plane) as above; no FB copper on the
  return path. Set solid zone connections on U2.2/C1.2/C2.2 if the pour is
  used for return (`SetLocalZoneConnection` on those pads).

### Bottom side

- Direct-solder harness pad set HP1 (item 2) under J1 on B.Cu: six pads
  ~1.6 × 2.5 at 1.5 pitch, y ≈ 125.0, x ≈ 103.5–111; nets as J1 (1 +12V_IN,
  2 GND, 3 no net, 4 GND, 5 TAP_RESP, 6 TAP_REQ). Needs the +12V_P B.Cu feed
  (103.6,108.9)->(103.6,125.0)->(112.55,125.0) moved to In2. TAP_x reach HP1
  by vias at (108.475,120.55)/(109.725,120.55) overlapping D3/D4 lower pads
  (check against the R7/R8 lower vias at 104.95/106.10 — no x overlap).
  Update `test_tap_nets_touch_only...` allowed set: {J1.5, J1.6, D3.x, D4.x,
  R3.1, R4.1, HP1.5, HP1.6}; HP1 is copper only (no LCSC, not in BOM).
- Test points (item 10), `TestPoint:TestPoint_Pad_D1.0mm` on B.Cu, right
  column x ≈ 125.5 (and 123.4) y 104–116 at 2.1 pitch: +12V_F (after F1),
  +5V_BUCK, +5V_X, +3V3, GND, TAP_RESP, TAP_REQ, RX_RESP, RX_REQ, plus a
  second GND pad as scope ground. Labels on B.SilkS at 1.0 mm.
- C5/C6 DNP at ~(101.0,104.6)/(102.5,104.6) on B.Cu, tied to the input vias.
- Keep R12/JP1/TP1 proxy parts (y 113.8) and the FOAM TAPE AREA rect
  (105–116.6 × 104–111.2).
- Bottom silk (all text ≥1.0 mm now): the current 0.8 mm texts at x 113.5,
  y 119.9–126.1 collide with HP1; move to x 112–127 in 14-char lines:
  "SolArk carrier", "rev B 2026-10", "J1 OFF FOR USB", "or USB isolator",
  then test-point labels. Put J1/HP1 pinout next to HP1.

### Housekeeping details

- `build.sh`: POSIX sh has no pipefail. Redirect gen_pcb output to a log,
  test `$?`, then `grep -v` the wx noise; drop `|| true`.
- `export_fab.sh`: add `--exit-code-violations` to `sch erc` and `pcb drc`.
- `gen_pcb.py`: `fp.SetExcludedFromPosFiles(dnp or not in_bom)`;
  `min_text_height` 0.8 -> 1.0; stackup post-process; new PLACE entries.
- `gen_sch.py`: POS for U3, C9, R7, R8, R15, D3, D4, HP1, TP2–TP11; NOTES:
  passive path now "tap -> ESD -> 1k -> buffer -> 1k -> GPIO, GPIOs reach only
  buffer outputs"; divider note 5.117 V; rev "B".
- Tests to add: graph walk from U1.1/U1.2 through populated two-terminal
  parts only (U3 is a barrier) must never reach TAP_x and must stay on the
  buffer-output side; U3 VCC = +3V3 with populated C9; R7/R8 populated;
  every assembled part has an LCSC number (HP1/TPs excluded from BOM).
- JLC rotation table in README: add U3 (SOT-363) and D3/D4 (DFN1006) as
  "must check in the JLC preview" (JLC conventions differ from KiCad's);
  re-check J1, D2, TVS1.
- `docs/hardware/README.md`: delete the "plain cable to a battery-powered
  laptop" optional step (~326–329); state "disconnect J1 before a plain USB
  cable, or use a VBUS-blocking isolator"; commissioning numbers: 5V pad
  ≈ 4.6–4.8 V (was 4.6–4.7), G9 line ~208, §6.6, §8 glitch row.

## Notes relevant to `build-cost-options.md` (NOT applied, not approved)

- R13 12 k / R14 2.2 k (1 %): nominal 0.8 × (1 + 12/2.2) = 5.164 V, but with
  ±1.5 % Vfb and ±2 % ratio the buck output reaches ≈5.33 V worst case, which
  breaks the item-7 ceiling (≤5.25 V) unless the ceiling is taken after D2.
  The 0.1 % 20 k + 1.69 k / 4.02 k set above meets it at the buck.
- D2 -> B5819W: B5819W (SOD-123, 1 A) has a higher VF than PMEG4030ER (the
  rev A README quotes PMEG4030ER ≤0.40–0.45 V worst case in this current
  range; B5819W is typically ~0.45–0.6 V at 0.5 A per its datasheets; neither
  number was re-verified this session). Expect ~0.1–0.15 V less at the XIAO
  5V pin (≈4.5 V worst-min); the XIAO's own 3.3 V LDO still has margin but
  the commissioning window in `docs/hardware/README.md` would move.
- TVS1 -> SMAJ18A (DO-214AC): courtyard ≈ 5.0 × 3.0 mm, taller and wider than
  the SMF (SOD-123FL) part; it does not fit the left strip after U3/C9 are
  added (strip budget 13.7 of 14.0 mm). Would need a different placement.
- J1 -> solder pads: the rev B plan already adds a bottom-side pad set HP1 as
  an alternative while keeping J1; if J1 is removed, the row above J1 and the
  harness-side routing above become much simpler.

## Next steps (in order)

1. `design.py`: add U3 (`carrier:74LVC2G17`, `Package_TO_SOT_SMD:SOT-363_SC-70-6`,
   C80500, pins 1 BUF_IN_a, 2 GND, 3 BUF_IN_b, 4 BUF_OUT_b, 5 +3V3, 6
   BUF_OUT_a — assign RESP/REQ after the pad dump), C9, R7, R8, R15, D3, D4
   (`carrier:DFN1006-2L`, C110695), HP1 (6-pad copper footprint, no LCSC,
   in_bom False), TP2–TP11; change R3/R4 pin 2 nets to BUF_IN_x, R5/R6 to
   populated on BUF_IN_x, C5/C6 to BUF_IN_x; R13/R14 values and nets; U1
   pins 1/2 stay RX_RESP/RX_REQ.
2. `gen_lib.py`: THT 2.2/1.65, drop castellation, 74LVC2G17 symbol, DFN1006-2L
   and HP1 footprints, silk 1.0, TAIL 0.71, descr wording.
3. `gen_sch.py`: POS/NOTES/rev B. Run gen_lib, gen_sch, netlist, then
   `gen_pcb.py place` with the new PLACE to dump exact pad coordinates.
4. `routes.py`: re-route per the plan; iterate `build.sh` + DRC
   (`grep -c` / `tail` the report) until clean.
5. `build.sh` / `export_fab.sh` gating, stackup, DNP pos exclusion, tests,
   READMEs, then regenerate everything and compare `.gbrjob`.
6. Run advisor before declaring done; hand back ≤400 words.
