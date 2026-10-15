# Rev B-diy open items (2026-10-13, updated 2026-10-14)

Items are grouped by when they must be resolved. [I] means inferred and not yet verified.

## Before ordering

| # | Item | What to do |
|---|---|---|
| O1 | **Stack height.** The model gives 7.8 mm against the 9.0 mm limit, but three of its four inputs are [I]: the XIAO Plus height with its U.FL and USB-C (4.9 mm), the gap above the board (0.3 mm), and the trimmed tail (1.0 mm). | Measure with calipers: (1) a real XIAO Plus, from the bottom of its PCB to the top of the tallest part (U.FL, shield or USB-C); (2) the gap under the XIAO when it sits on bare pins with the plastic pulled; (3) the tail you can leave and still get a fillet. Pass if the sum plus 1.6 mm is at most 9.0 mm. |
| O2 | **The harness exits beyond the outline.** The J1 wires leave the bottom edge (the J1 edge); the wire bend and the in-line plug sit outside the 29 x 30 mm board. | Check there is room in the dongle enclosure for about 5 mm of wire bend plus the 2.5 x 15 mm in-line plug, or route the wires flat along the board. |
| O3 | **The dongle logic level is assumed to be 3.3 V.** It has not been measured. | Measure the high level at tap pads 9 and 10. Both 3.3 V and 5 V work: U3 inputs tolerate 5.5 V and a 5 V high reaches U3 at 4.83 V. Above 5.5 V, U3 must change. |

## Parts and footprints

| # | Item | What to do |
|---|---|---|
| O4 | **Resolved.** TVS1 now uses Littelfuse's own SMF mounting pad layout (1.3 x 1.4 mm pads, 1.6 mm gap [V]), read from the LCSC mirror of the Littelfuse datasheet because littelfuse.com returned 403. | None. |
| O5 | **JLC's D1 substitute** for route (a) is CJ B5819W (C8598). Its land pattern was not read. MCC's was [V]. | Route (a) only: read CJ's SOD-123 drawing. |
| O6 | **JLC CPL rotations** are taken straight from KiCad and have not been checked against JLC's reference orientation. D1 is at 180°. | Route (a) only: in JLC's placement preview, confirm the D1 cathode band and the orientation of every capacitor and resistor before paying. |
| O7 | **F1 stock is thin.** Digi-Key had 943 pieces. | Re-check stock at order time. No alternative 60 V 1812 PPTC was checked; a lower-voltage PPTC is not acceptable, because the input must survive up to the TVS clamp. |
| O8 | **C3 swapped (2026-10-14)** from the NFND Taiyo Yuden JMK316BJ107ML-T to the Active TDK C3216X5R0J107M160AB (445-6008-1-ND, 22,959 in stock [V]). It gives about 28.7 µF at 5 V [V], against about 30.2 µF [I] for the old part (from its renamed successor's curve), so it is about 5 % lower. KiCad's 1206 land differs from TDK's recommended land (gap 1.8 against 2.0-2.4). | Accept, since C3 is non-critical bulk. Or, at order time, check Digi-Key stock and status for the Taiyo Yuden successor MBASJ31LBB5107MTNA01 and confirm it really replaces JMK316BJ107ML-T: same curve, about $1.03. |
| O9 | **ESD.** Rev A's ESD parts (D3/D4) were removed. The protection left is U3's 2 kV HBM, the 1 k + 10 k series resistance, and the Schmitt inputs. That is adequate only with the two harness 10 k resistors fitted (now kit item CF18JT10K0CT-ND, **required**) and basic ESD handling (wrist strap, or touch ground before handling the J1 wires). The PESD5V0S2BT suggested earlier is out of stock until 13 Jul 2027 (VERIFY-revB.md §2a). | Fit both 10 k resistors at the dongle-pad ends. Adding diodes (e.g. Littelfuse SP0502BAHTG, SOT-23) would need a layout pass; recommended only if the harness gets handled live. |

## Ratings to confirm (all [I])

| # | Item |
|---|---|
| O10 | **F1 hold current at 60 °C.** Typical derating gives about 0.375 A. The load needs at most about 0.25 A at 12 V. Confirm against Bourns' MF-MSMF derating table. |
| O11 | **C1 DC-bias derating** of the 10 µF 50 V X5R part at 12 V. TI asks for at least 2.2 µF; expected effective value is about 4-6 µF. |
| O12 | **D2 forward voltage at 0.5 A, cold.** A 0.50 V bound is used. The datasheet gives 0.44 V max at 1 A and 25 °C [V]. |
| O13 | **USB VBUS floor of 4.40 V** (USB 2.0 low-power port). This is the requirement the 4.485 V worst case is checked against. |
| O14 | **XIAO Plus bottom-pad inward extent**, read from Seeed's KiCad files. The 0.174 mm ring clearance depends on it. |

## Out of scope (from the review; the board works without them)

- Item 8: the tightness of the buck hot loop. C2 is at the pins and C1 returns through vias.
- Item 9: margin on the size of C3.
- Item 10: test points. Probe the pads of C7 and C3 and the J1 pads instead.
- Thermal analysis. U2 dissipates about 0.2 W at 0.45 A load.
- Mechanical fixing. There is no room for a hole, so use tape or foam.
