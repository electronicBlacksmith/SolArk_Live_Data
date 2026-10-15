# Carrier PCB review (independent, Fable)

Scope: `hardware/carrier/` in the uncommitted working tree on 2026-10-12 (design.py /
gen_*.py, `carrier.kicad_pcb`, `fab/`; `hardware/` is not yet tracked by git). Read-only review. I re-ran DRC with `--severity-all`
(0 violations), dumped the netlist, pad coordinates, tracks and zones with pcbnew,
rendered every copper layer, and checked parts against primary sources (cited).
I also read Seeed's XIAO ESP32S3 Plus V1.1 KiCad PCB (downloaded to scratch) to
check the castellation geometry under the socket flanges.

Verdict: **no P0 found.** The netlist, polarities, the XIAO pin map and the
passive-only property are correct. Four P1 items, all mechanical/assembly, should
be fixed before ordering. Twelve P2s.

Notation: coordinates are KiCad board coordinates (board spans 100..127 mm in x
and y; y increases downward). [V] = verified against a primary source, [I] =
inferred/calculated.

---

## P1 findings

### P1-1 Receptacle holes: 1.52 mm finished hole is the Mill-Max *minimum*; JLC's PTH tolerance goes below it

- Where: `scripts/gen_lib.py` XIAO footprint (THT pad 2.0 mm, drill 1.52),
  `fab/gerbers/carrier.drl` tool T2 = 1.520 mm x14, `README.md` lines 135, 217, 259.
- Evidence: Mill-Max's catalog page lists the 7305 series as **"solder mount in .060
  (1.52 mm) min. mounting hole"**; press-fit versions are other series (1305, 0400,
  2400, 8401). Source: a mirrored catalog PDF
  (https://static.chipdip.ru/lib/278/DOC012278175.pdf) seen only as a search
  excerpt; the PDF itself and mill-max.com were unreachable. Distributor data for 7305-0-15-15-47-27-10-0: solder termination, no
  tail, 2.67 mm overall, 1.96 mm flange, 1.52 mm mounting hole, accepts 0.64-0.94 mm
  pins (DigiKey https://www.digikey.com/en/products/detail/mill-max-manufacturing-corp/7305-0-15-15-47-27-10-0/1765737,
  Arrow https://www.arrow.com/en/products/7305-0-15-15-47-27-10-0/mill-max.html).
  JLCPCB's finished-hole tolerance for plated holes is +0.13/-0.08 mm
  (https://jlcpcb.com/capabilities/pcb-capabilities), so a 1.52 drill can arrive at
  1.44 mm and some boards will not accept the shell. The README calls them
  "press-fit" three times, which they are not; they rely on solder (step 3 does
  solder them, so the assembly step is right, the description is wrong).
- Fix: set the finished hole to 1.60 mm (JLC: 1.52-1.73) and the pad to 2.2 mm
  (annular ring 0.30 mm, pad-to-pad gap at 2.54 pitch = 0.34 mm, still above the
  0.127 clearance rule). Rename "press-fit" to "solder-mount" in README and the
  parts table. Keep ENIG.

### P1-2 Flat-solder option: carrier castellation pads come within 0.06 mm of the Plus's 1.27 mm castellations (bridging D0/GPIO1 to GPIO38, etc.)

- Where: `scripts/gen_lib.py` SMD castellation pads 1.524 x 1.85 mm at y = +/-7.925
  (pins 1-14 only); `lib/carrier.pretty/XIAO_ESP32S3_Socket_SMD.kicad_mod`.
- Evidence: Seeed's Plus V1.1 PCB (`XIAO ESP32S3 Plus_V1.1_250724.kicad_pcb`,
  footprint `XIAO-HALF-HOLE-23P`) puts round 0.90 mm castellation pads with 0.60 mm
  half-holes at 1.27 mm pitch on the board edge between the 2.54 mm pins (pads
  15-20 beside pins 1-7, pads 21-23 beside pins 8-10). Their copper reaches to
  1.27 - 0.45 = 0.82 mm from the 2.54 mm pin centre; the carrier pad is 1.524 wide,
  i.e. 0.762 mm from the pin centre. Gap 0.06 mm. Seeed's own Plus SMD footprint
  (`lib/seeed/XIAO-ESP32-S3-Plus-SMD.kicad_mod`) uses 0.95 mm wide pads for this
  reason. The carrier pads also stop 0.045 mm inside the XIAO edge (y 8.85 vs edge
  8.895), so there is no toe for a fillet or inspection.
- Fix: castellation pads 0.95-1.0 mm wide in the pitch direction and extend them
  ~1 mm past the XIAO edge (as Seeed's Plus footprint does, y to 9.3 mm), or drop
  the flat option from README. Socketed assembly is unaffected (see P2-1).

### P1-3 Stack height rests on two unverified numbers and a model that cannot verify them

- Where: `README.md` "Height stack-up" (7.57 / 7.6 mm), `gen_lib.py` XIAO_THK = 4.9,
  SOCKET_GAP = 0.3, TAIL = 0.77.
- Evidence: No Seeed source states the Plus height; the wiki gives 21 x 17.8 mm only
  (https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/), retailers give
  packaging dimensions. The Mill-Max flange thickness (0.3) is not in any distributor
  table and the drawing could not be fetched. The 2.67 mm "overall length" might
  include the flange (README assumes so). The margin is 1.4 mm to the 9.0 mm design
  limit; if the XIAO is 5.5 mm with the U.FL plug and the flange is 0.5 mm, you are
  at 8.4 mm with 0.8 mm tape and at 9.2 mm with the 1.6 mm tape mentioned in line 26.
- Fix: before ordering, measure a real Plus (USB-C top to PCB bottom, and with the
  U.FL plug seated) and one 7305 receptacle. Gate the order on it (README risk 4
  already says so; make it a checklist item in the build steps, not a risk note).

### P1-4 J1 mated plug and wire exit extend past the 28 mm envelope

- Where: J1 at (106.6, 123.75), footprint `JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal`.
- Evidence: the connector housing front face is at y = 126.25 (F.Fab), the board
  edge at 127.0, and the envelope allows 28 mm, i.e. 0.5-1 mm beyond the edge
  depending on where the board sits in the cavity. A GH
  side-entry plug latch sits roughly flush with the housing when mated, and the six
  wires leave perpendicular to the edge; the bend radius of 28-30 AWG wire with the
  housing adds several mm beyond the edge. The LCSC part (XY-SM06B-GHS-TB,
  https://www.lcsc.com/product-detail/C51940119.html, 10.75 x 4.85 x 4.35 mm) is a
  JST GH clone whose own drawing I could not open; the README's 4.25 mm height is
  0.1 mm under LCSC's figure.
- Fix: measure the dongle cavity first (is there free space beyond this board
  edge for a GH plug plus a wire bend?). If yes, no change. If no, the connector
  concept has to change and neither easy alternative is free: rotating J1 inward
  puts a 4.35 mm connector under the XIAO (XIAO courtyard ends at y 118.35, the
  rotated face would be at y ~122, and the wires would have to pass under a
  0.3 mm gap); a vertical GH (BM06B-GHS-TBT, ~4 mm tall) needs 1.6 + 4 + plug
  and a wire exit upward beside the XIAO, which has not been checked against the
  10 mm envelope. Direct-solder harness pads (no connector) are the fallback that
  fits for certain. Either way correct the README height to 4.35 mm.

---

## P2 findings

### P2-1 Socket flanges are 0.37 mm from the Plus's 1.27 mm castellation copper
- Flange radius 0.98 mm at the 2.54 mm pin; nearest 1.27 castellation copper
  (round pad r 0.45 at 1.80 mm centre distance) leaves 0.37 mm [I from the Seeed
  Plus PCB]. Only GPIO pairs are involved (D0..D6 with IO38..IO10, D7..D9 with
  IO11..IO13); pins 12-14 (3V3/GND/5V) have no 1.27 neighbour. Not a short as
  designed, but there is no margin for a bent flange or a shifted XIAO.
- Fix: firmware rule "never configure the 1.27-pitch GPIOs as outputs"; optionally
  a Kapton strip along the XIAO edges between the flanges.

### P2-2 Hot-loop return goes through the planes, and the hot-loop GND pads use thermal relief
- Where: C1 (113.85, 123.4), U2 GND pad 2 (116.8, 122.263), FB track
  (115.85, 122.26) -> (115.16, 119.75), R13/R14 row at y 119.75, +12V_P track along
  y ~124.5-125.
- Evidence (pcbnew dump): on F.Cu the direct path from C1's GND pad to U2 pad 2 is
  walled off by U2 pad 3 + the FB track on one side and the +12V_P feed on the
  other; U2 pad 2 reaches GND via a 0.4 mm track to C7's GND pad. The return
  therefore runs C1 -> F.Cu pour (thermal spokes) -> vias -> In1 -> vias -> C7 ->
  U2. All four zones are thermal-relief. Works at 1.1 MHz/0.5 A with an adjacent
  GND plane, but it is not the TI layout (Cin GND directly to the GND pin,
  https://www.ti.com/lit/ds/symlink/lmr51610.pdf section 10).
- Fix: solid zone connection for C1, C2, C7, C8 and U2 pad 2; add a short F.Cu
  GND link C1 pad -> U2 pad 2 above the FB track (there is room at y 122.3-123.3
  between C1 and pad 3 if the FB track leaves pad 3 downward first, which it does).

### P2-3 VBUS at the XIAO is 4.5-4.7 V at 450 mA; raise the buck to ~5.2-5.3 V
- Nominal Vout 0.8 x (1 + 27k/5.1k) = 5.035 V [V, R13/R14 1 % parts]. Worst low:
  Vfb 0.788, R tolerances, -1.5 % regulation = 4.80 V [I]. D2 PMEG4030ER Vf ~0.33 V
  typ / 0.40 V max at 0.45 A [V, Nexperia datasheet
  https://assets.nexperia.com/documents/data-sheet/PMEG4030ER.pdf: 380/440 mV at
  1 A, 295/330 mV at 0.1 A] -> +5V_X = 4.4-4.7 V. The XIAO's own LMBR4010 (Plus
  schematic D2) takes another ~0.3 V -> ~4.1-4.4 V at the SGM6029, which still
  regulates 3.3 V. Functional, but the README's "4.7-4.9 V at C3" is optimistic.
- Fix: R13 28.7k (5.30 V) or 28k (5.19 V), and move the `tests/test_design.py`
  Vout window (currently 4.95-5.15 V) with it. The carrier's C3 is rated 6.3 V;
  the XIAO's own VBUS-side parts were not checked against 5.3 V (see could not
  verify), so 5.2 V is the safer step.

### P2-4 PPTC hold current at 70 °C equals the 0.3 A target
- SMD1812P050TF/60 = R+O SMD1812-050-60: Ihold 0.50 A, Itrip 1.0 A, 60 V, R1max
  1.4 ohm; derating 0.43 A @50 °C, **0.35 A @60 °C, 0.30 A @70 °C**, 0.23 A @85 °C
  [V, LCSC-hosted datasheet
  https://atta.szlcsc.com/upload/public/pdf/source/20250414/001E61D6A0C78432CBCACDD44FA2AE48.pdf,
  linked from https://jlcpcb.com/partdetail/C462518; the derating table is the
  series table, the /60 part is the SMD1812-050-60 row].
  Input current at 12 V: 0.19 A at 0.4 A out, 0.24 A at 0.5 A out (eta ~88 %) [I].
  Margin 1.25-1.5x; a Wi-Fi TX burst on top of a warm board will not trip it, but
  a 125 °C dongle interior would.
- Fix: acceptable; if the dongle interior measures >65 °C, use SMD1812-075-24
  (0.75 A hold, 24 V, still above the 13 V bus) or move the fuse to 0.5 A hold at
  a lower Vmax rating.

### P2-5 No test points for 12 V, 5 V, 3V3, GND; only TP1 (proxy)
- The README's "measure at C7 / C3" means probing 0805/1206 cap ends with the
  XIAO socketed; there is no GND loop for a scope. The bottom side has free area at
  x 118-125, y 106-112 (clear of the foam-tape rectangle and R5/R6/C5/C6).
- Fix: five 1.0 mm SMD test pads on B.Cu: +12V_P, +5V_BUCK, +5V_X, +3V3, GND,
  plus two for RX_RESP/RX_REQ. Zero height; they sit inside the tail height.

### P2-6 DNP parts are not flagged "exclude from BOM/POS" in the PCB
- pcbnew: R5, R6, C5, C6, R12 have dnp=True but exclBOM/exclPOS False; JP1/TP1 are
  excluded. `fab/carrier_bom_jlc.csv` (14 lines) and `carrier_cpl_jlc.csv` (17
  placements) are correct because `gen_*` filters on dnp, but a kicad-cli export
  would include them.
- Fix: set both attributes in `design.py` for dnp parts so every export path agrees.

### P2-7 CPL rotations need the JLC preview check
- JLC's rotation origin differs from KiCad's for many libraries; SOT-23-6 (U2 at
  270), SOD-123/123F (D1 270, TVS1 90), SOD-123W (D2 180) and the GH connector
  (J1 0) are the usual offenders. The CSV format (Designator, Mid X, Mid Y, Layer,
  Rotation; bottom-left origin) is correct.
- Fix: in the order preview, confirm pin 1 of U2 is at the top-right pad as the
  render shows, the diode bands match the silk bands, and J1's opening faces the
  board edge.

### P2-8 Silkscreen text below JLC's recommended 1.0 mm
- `gen_pcb.py` min_text_height 0.8 mm; JLC recommends >= 1.0 mm height / 0.15 mm
  width for legibility (same capabilities page). DRC silk clearance is 0, so silk
  over pads is possible; JLC clips it, but the pinout text should be checked in the
  silk render.
- Fix: 1.0 mm text where it fits; set silk clearance 0.1.

### P2-9 R3/R4 and the tap routing: 20 mm of 0.2 mm track along the top edge on F.Cu/In2
- R3/R4 at (102.4, 102.6) / (102.4, 101.0) are 20 mm from XIAO pins 1/2
  (122.555 / 120.015, 101.78); TAP nets run 20 mm from J1 up the left edge. With
  10 k + 1 k in series and 9600 baud this is electrically irrelevant, but the raw
  TAP nets (before R3/R4) run the length of the board next to GND only, and the
  ESD path from the harness is: 10 k (off-board) -> 1 k -> GPIO clamp.
- Fix: populate C5/C6 (100 pF, 0402, bottom) by default; the RC (11 k x 100 pF
  = 1.1 us) is 1 % of a 104 us bit. Optionally move R3/R4 next to J1 so the
  series resistance is at the entry point.

### P2-10 USB bench power with 12 V absent: benign, but C3 exceeds the USB inrush limit
- With USB only, VBUS (XIAO pin 14) sits at ~5 V on +5V_X. D2 is reverse biased
  by ~5 V: IR 25 uA typ / 100 uA max at 40 V, 25 °C [V], far less at 5 V. The
  leaked uA charge C7 and, through L1 and the HS body diode, lift +12V_P to ~4 V
  at no current; LMR51610 UVLO is 3.82 V typ so it may briefly "wake" with no
  input current to speak of. D1 blocks any path back to J1 [V, B5819W 40 V]. No
  damage mechanism found. The 100 uF C3 plus the XIAO's caps exceed the USB 2.0
  10 uF bulk limit; a PC port will tolerate it, a strict hub may not.
- With 12 V present and USB plugged: USB drives +5V_X to ~5 V, D2 reverse ~0.3 V;
  the only hazard is the ground loop the silk already warns about.
- Fix: none required; note the inrush in README.

### P2-11 Inrush on the DB9 supply
- C1 10 uF + C2 charge through PPTC (0.15-1.4 ohm) + D1 in microseconds; C3's
  100 uF is behind the buck's 2.3 ms soft-start (not reflected as a 12 V surge).
  The DB9 port's own fuse/source impedance is unknown (G4 gate).
- Fix: none; keep the inline DB9 fuse. If G4 shows a weak port, add 10 ohm in
  series before C1 (the buck tolerates it at 0.24 A).

### P2-12 Buck thermal at 65 °C ambient
- Loss in U2 at 12 V -> 5 V, 0.5 A: HS 0.7 ohm x D 0.42 x 0.25 A^2 = 0.07 W, LS
  0.36 ohm x 0.58 x 0.25 = 0.05 W, switching/driver ~0.06 W -> ~0.2 W [I]. RthJA
  95 (EVM) - 148 (JEDEC) K/W [V] -> Tj 84-95 °C at 65 °C ambient, below the
  165 °C shutdown. The 27 mm 4-layer board with GND pours is between the two.
- Fix: none. If the dongle interior is hotter than 65 °C, note that Tj rises
  linearly and the PPTC (P2-4) is the first thing to give.

---

## Verified correct

Netlist and circuit (from `scripts/design.py` and pcbnew, pin-by-pin):
- J1: 1 +12V_IN, 2 GND, 3 NC, 4 GND, 5 TAP_RESP, 6 TAP_REQ, MP GND. Matches
  README harness pinout and `tests/test_design.py`.
- F1 1 +12V_IN / 2 +12V_F; D1 B5819W pad 1 (K) = +12V_P, pad 2 (A) = +12V_F:
  forward from J1 to the rail, blocks reverse [V, KiCad SOD-123 pad 1 = cathode;
  JLC C8598 40 V 1 A, Vf 0.6 V at 1 A]. TVS1 SMF18A pad 1 (K) +12V_P, pad 2 (A)
  GND: correct unidirectional orientation [V, LCSC C123787: Vrwm 18 V, VBR 22.1 V,
  Vc 29.2 V at 6.8 A, 200 W]. Clamp 29.2 V vs LMR51610 operating range 4-65 V [V,
  TI SLUSEY1B]: wide margin. Standoff 18 V vs 11.4-13 V bus: OK.
- U2 LMR51610YDBVR, SOT-23-6: symbol/footprint pins 1 CB, 2 GND, 3 FB, 4 EN, 5 VIN,
  6 SW match the TI pinout; EN tied to VIN is a datasheet-sanctioned option
  ("EN can be tied to VIN"); UVLO is the internal 3.82 V. Y variant = 1.1 MHz
  [V]. CB cap C8 between CB and SW, 100 nF 50 V per BOM [datasheet requires
  >= 16 V; the C307331 page was not re-fetched]. Cin C1 10 uF 50 V X5R 1206
  (C13585) [V] + C2 100 nF at the pins [>= 2.2 uF + 0.1 uF required, V]. FB
  divider 27k/5.1k -> 5.035 V [V, Vfb 0.788-0.812]; R13/R14 1 % per README
  (C25771, C25905 not re-fetched).
- L1 FNR4030S100MT 10 uH, Isat 2.4 A, Irms 1.6 A, 130 mohm, shielded [V, LCSC
  C167879]; TI table 8-1 for 1.1 MHz/5 V gives 10 uH; peak current at 0.5 A load
  = 0.5 + 0.13 = 0.63 A vs the 1.25 A minimum current limit [V].
- Cout C7 22 uF 25 V X5R 0805 (C45783): ~13-15 uF effective at 5 V [I, typical
  X5R 0805 DC-bias], above TI's 10 uF. C3 100 uF 6.3 V X5R 1206 (C15008) on +5V_X
  after D2; C4 100 nF.
- D2 PMEG4030ER pad 1 (K) = +5V_X, pad 2 (A) = +5V_BUCK: backfeed blocking from
  USB into the buck [V, Nexperia: pin 1 cathode, 40 V, 1 A, CFP3/SOD-123W].
- XIAO U1 nets: 1 RX_RESP, 2 RX_REQ, 10 PROXY_GPIO8, 12 +3V3, 13 GND, 14 +5V_X.
  Seeed Plus pin map: D0 = GPIO1 (pin 1), D1 = GPIO2 (pin 2), D9 = GPIO8 (pin 10),
  3V3 (12), GND (13), 5V (14) [V, https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/].
  GPIO1/2/8 are not ESP32-S3 strapping pins.
- XIAO footprint handedness [V against Seeed's Plus V1.1 PCB]: pads 1 (D0) and 14
  (VBUS) are both at the USB end; rotating the Plus so USB points +x puts pad 1 at
  (+7.6, -7.6) and pad 14 at (+7.6, +7.6), exactly the carrier's pin 1 (122.555,
  101.78) and pin 14 (122.555, 117.02). USB-C overhang reaches x = 127.0 = board
  edge. Not mirrored, not rotated.
- Passive-only: TAP_RESP/TAP_REQ touch only J1.5/J1.6 and R3.1/R4.1; R3/R4 = 1 k,
  populated; PROXY_GPIO8 -> R12 (DNP) -> JP1 (open solder jumper, not in BOM) ->
  TP1, never to J1; `tests/test_design.py` asserts all of this. BOM (14 lines) and
  CPL (17 placements) contain no DNP part. A firmware fault driving GPIO1/2 as
  outputs is limited to ~0.3 mA by the 11 k.
- LCSC part numbers: 10 of 14 fetched at jlcpcb.com/partdetail/<code> and resolve
  to the intended part and package: C13585, C15008, C45783, C8598, C389355,
  C462518, C51940119, C167879, C123787, C22427220. Extended parts per those pages
  and the README stock table: U2, L1, F1, TVS1, D2, R13, J1 (7 x $3 fee); the
  rest Basic. LMR51610 is eligible for "Economic and Standard" PCBA [V,
  https://jlcpcb.com/partdetail/TexasInstruments-LMR51610YDBVR/C22427220]. J1
  11,460 in stock at LCSC (https://www.lcsc.com/product-detail/C51940119.html).
  Economic PCBA supports 4-layer, single-sided SMT [V,
  https://jlcpcb.com/capabilities/pcb-assembly-capabilities].
- DRC rules vs JLC 4-layer: track/clearance 0.127 (JLC 0.09), via 0.6/0.3 (JLC
  0.45/0.2), copper-to-edge 0.3 (JLC 0.2), hole-to-hole 0.5 (JLC 0.5). All
  conservative. DRC and ERC: 0 violations at every severity.
- Gerbers: F/In1/In2/B.Cu, F/B mask, F/B paste, F/B silk, Edge.Cuts, drill (PTH
  0.3 via x27, 1.52 x14), drill map, job file. Complete. Single-sided SMT.
- Layout: SW node is a 0.6 mm track 2.7 mm long from U2 pad 6 to L1 plus a 0.3 mm
  stub to C8; FB leaves pad 3 away from SW and reaches R13/R14 in 2.5 mm; the
  +5V_BUCK sense link is a separate 0.2 mm In2 track from C7 to R13, not the
  power track; In1 is an unbroken GND plane; 19 GND stitching vias; +12V and +5V
  tracks 0.5-0.6 mm for <= 0.5 A. Creepage at 12 V is not a concern at 0.15 mm.
  XIAO THT pins connect to the zones through thermal relief (hand-solderable).
- Mechanical: nothing taller than a via is under the XIAO on the top side
  (courtyard x 104.4-127.05, y 100.45-118.35; U2/L1/C3 row starts at y 119.25,
  F1/D1/TVS1 at x <= 104.3). The Plus's bottom side carries only test points, so
  it is flat over the flanges. Foam-tape rectangle (105-116.6, 104-111.2) on the
  bottom is clear of the receptacle tails and the DNP 0402s. U.FL position on the
  Plus (-8.84 along, -4.85 across, top side) projects to (106.1, 104.55) on the
  carrier, matching the User.Drawings rectangle and README. BOOT/RESET and USB-C
  are on top of the XIAO and reachable when socketed.

## Could not verify

- Mill-Max 7305 drawing: flange thickness, shell OD, whether 2.67 mm includes the
  flange (mill-max.com product URLs 404, Mouser PDF timed out, chipdip mirror
  refused). Distributor attribute tables only.
- XIAO ESP32S3 Plus height (no Seeed figure; the standard XIAO STEP in scratch is
  not the Plus and its coordinate extents are not a usable height).
- XY-SM06B-GHS-TB drawing (LCSC PDF unreadable): pin-1 side, land pattern vs the
  KiCad JST GH footprint, mated-plug overhang, JST GH mating compatibility.
- LCSC pages for C307331 (C2/C4/C8 100 nF), C11702 (R3/R4 1 k), C25771 (R13 27 k)
  and C25905 (R14 5.1 k): values, tolerance and voltage taken from the BOM/README,
  not re-fetched.
- Samsung DC-bias curves for C7/C3 (typical X5R behaviour assumed).
- The XIAO Plus's VBUS-side parts (charger SGM40567, LMBR4010) against a raised
  5.2-5.3 V VBUS (P2-3); no datasheets fetched.
- LMR51610 stock at JLC (page shows no quantity; earlier request returned 429).
- Which other BOM lines are Economic-eligible (only U2 checked explicitly).
- The PPTC datasheet is branded R+O (Zhuhai Hongjiacheng) while LCSC lists
  "PTTC"; same tables, but the brand mismatch is unexplained.
- Dongle cavity: whether wires may leave at the J1 edge, and the interior
  temperature (drives P2-4 and P2-12).
