# Rev A carrier review: merged findings (2026-10-12)

Sources:
- Fable review: `review-fable.md` (this directory).
- Codex review: model `gpt-6.1-sol`, reasoning effort `xhigh`, session `01a1330c-6e19-7151-bb51-1ed438fd57d0`, read-only with web search. The full text was kept in the session scratchpad and summarized here.

"Verified" means the claim was checked against the repo files during the merge.

**Verdict: do not order Rev A yet.** Both reviews agree that the netlist, the polarity of every diode and the TVS, the buck design, the 5.035 V nominal output, the XIAO pin map and handedness, DNP exclusion, the Gerber set and DRC-vs-JLC are all correct. What blocks ordering is mechanical fit, the socket holes, and one passive-only and USB-power question.

## Must fix before ordering

1. **Socket holes are too tight. Both reviewers flagged this. Verified.**
   - Issue: `scripts/gen_lib.py:39` uses `THT_DRILL = 1.52`. The Mill-Max 7305 is *solder-mount* and needs at least a 1.52 mm finished hole. JLC's PTH tolerance is +0.13/−0.08 mm, so a hole can come out at 1.44 mm.
   - Fix: change the drill to 1.60–1.75 mm with a pad of at least 2.2 mm, then recheck annular rings and routing.
   - Also correct README lines 135, 197 and 217, which call the part "press-fit".
2. **J1's mated plug sticks out past the 28 mm envelope. Both reviewers flagged this.**
   - Issue: the housing face sits 0.75–0.8 mm inside the board edge, so the plug and the wire bend extend about 3–6 mm beyond it.
   - Fix: measure the dongle cavity first. If the plug doesn't fit, either solder the harness straight to pads (always fits) or re-layout with a recessed or inward-facing connector.
3. **Real stack height is unverified. Both reviewers flagged this.**
   - Issue: the 7.6 mm figure assumes `XIAO_THK = 4.9` and `SOCKET_GAP = 0.3` (`gen_lib.py:41-43`).
   - Fix: measure a real Plus with its U.FL plug, plus one receptacle, before ordering.
4. **The flat-solder option can short to the Plus's 1.27 mm castellations (Fable). Codex found a related flange overlap.**
   - Issue: the 1.524 mm pads sit about 0.06 mm from the neighbouring Plus pads.
   - Fix: use Seeed's Plus SMD land pattern (pads 0.95–1.0 mm wide, extended past the edge) or drop the flat-mount option. Also confirm that the socket flanges clear the Plus's extra underside pads.
5. **Remove the "plain cable to a laptop" test step. Codex (P0). Verified at `docs/hardware/README.md:327-329`.**
   - Issue: D2 only blocks USB→buck. With 12 V present, buck→XIAO 5V→VBUS→host still conducts, so the step can backfeed the laptop's port.
   - Fix: delete the step. The rule becomes: disconnect J1 before using a plain USB cable, or use a VBUS-blocking isolator when both are connected. Put this rule on the silkscreen.

## Decide before ordering

6. **Hardware RX-only buffer (Codex P1).**
   - Issue: populated `GPIO1/2 → 1 k → J1 → 10 k → pad` paths are bidirectional. Codex cites ESP32-S3 datasheet Table 2-2 (not yet re-checked) as listing GPIO1 and GPIO2 among pins with a ~60 µs low glitch at power-up, before firmware runs. Through 11 k this is about 0.3 mA against a push-pull driver, so corrupting the link is unlikely, but it breaks the literal "cannot transmit" guarantee in Standing Rule 6.
   - Fix: an SN74LVC2G17 (2× Schmitt buffer, SOT-23-6, 5.5 V-tolerant inputs, Ioff powered-down protection) in front of the GPIOs makes the board unidirectional in hardware. It also addresses powered-off back-injection and harness ESD (Codex P1-10).
   - **Recommended:** add it. It costs one small part and some layout space.
7. **VBUS margin (both reviewers).**
   - Issue: worst case is about 4.44 V at the 5V pad, not the 4.46 V the README claims. The cause is the TI reference tolerance (±1.5%), 1% divider resistors, and D2's 0.44 V drop at 1 A.
   - Fix: raise Vout to about 5.2 V (Fable) or use 0.1% low-tempco divider resistors. Update the commissioning window to match.

## Fix in Rev A if cheap, otherwise test on the bench

8. **Buck input hot loop (Codex P1, Fable P2).**
   - Issue: the C1/C2 ground return to U2 pin 2 goes through the inner plane because the FB trace cuts across it.
   - Fix: move FB to an inner layer and add a ground via beside U2 pin 2.
9. **C3 effective capacitance (Codex).** C3 is a 100 µF 6.3 V X5R in 1206, which delivers well under 100 µF at 5 V because of DC-bias derating. It also sits directly on USB VBUS, which exceeds the USB inrush limit (Fable). Size it from a droop budget, or use a low-profile polymer cap.
10. **Test points (both reviewers).** Add labelled pads for 12 V, +5V_BUCK, +5V_X, 3V3, GND and both taps, plus a scope-ground spot.
11. **Populate C5/C6 (Fable)**, or rely on the buffer from item 6, for ESD on the harness inputs.
12. **Build safeguards (Codex). Verified.**
    - `scripts/build.sh:11` swallows PCB-generation failures with `|| true`. Make the build fail on a generation error, an ERC violation or a DRC violation.
    - `fab/gerbers/carrier-job.gbrjob` declares 35 µm inner copper, but the README stackup says 0.5 oz. Set the real JLC stackup and re-export.
13. **Housekeeping.**
    - Set DNP attributes in the PCB (not just omit the parts from the BOM).
    - Check rotations in JLC's placement preview, especially J1, D2 and TVS1.
    - Increase silk text from 0.8 mm.

## Verify on the bench (no board change)

- **Thermal:** buck Tj is estimated at about 84–132 °C at 65 °C ambient, and the XIAO is only rated to 65 °C. Measure inside the closed dongle at a 0.4–0.5 A load.
- **DB9 inrush and sustained overvoltage:** F1's 150 ms trip spec is at 8 A, so the PPTC is not an inrush limiter. Measure startup current and rail sag on the real harness. TVS1's 18 V standoff still needs checking against the measured maximum of the rail.
- **Parts:** LCSC lists C307331 (100 nF 0402) and C11702 (1 k 0402) as out of stock. JLC Basic inventory is separate, so check it at order time.

## Agreed correct (not just unmentioned)

- Netlist: every net is correct (see the net table in the Codex review).
- Polarity of D1, D2 and TVS1, and every orientation target.
- U2 is the LMR51610 1.1 MHz variant. EN is tied to VIN (internal UVLO), the BOOT cap is correct, and the feedback divider gives 5.035 V nominal. L1 is 10 µH with 2.4 A saturation, against a peak of about 0.63 A.
- F1 holds 0.37 A at 60 °C. TVS1's clamp is far below U2's 70 V absolute maximum.
- XIAO pin map: D0=GPIO1, D1=GPIO2, 5V, GND and 3V3 are neither mirrored nor rotated. Fable checked this against Seeed's Plus V1.1 KiCad PCB.
- Passive-only by population: R5, R6, C5, C6, R12, JP1 and TP1 are absent from the BOM and CPL. GPIO8 has no populated path to J1.
- ERC, DRC and schematic parity are all clean. The BOM and CPL formats are right, the Gerber/drill set is complete, and the board is within JLC Economic assembly limits for 4 layers at 1.6 mm.
