# Carrier Rev B (JLC variant): open items before ordering

The user must measure or decide these. Measurements come first: items 1-3 could change the layout.

**Status 2026-10-14: ordered** (5 boards, all assembled, Economic PCBA). Items 2-7 are settled by the user's measurements below [V, user]; items 8-9c were checked in JLC's preview, and JLC's post-order DFM review is still to read.

## Decisions

1. **The harness is soldered into J1 (5 wire pads); there is no connector on the board.**
   - This was chosen because a mated GH plug overhangs the 27 x 27 outline by 3-6 mm (review item 2). Wire pads are the minimum fix that reliably fits.
   - Cost: unplugging the harness for USB (the "12V OFF FOR USB" rule) means:
     - an inline connector in the harness (recommended: any 4-5 pin latching inline pair), or
     - unplugging at the dongle end.
   - Alternative, which the user must approve: a GH connector moved inboard, using the 29 x 30 mm allowance. That brings back one Extended fee ($3.07) and a re-layout.
2. **Header spacer on or off.** Each option has a hard condition:
   - **Off: a Kapton shim is required.** The top 1.70 mm header rings clear the XIAO Plus underside pads 15-23 by only 0.049 mm when flush (VERIFY-revB.md), so the XIAO must never sit on bare copper. Shim: 0.06-0.2 mm of polyimide, i.e. 1-3 layers of the kit tape (Bertech PPTA-1/2, 0.064 mm per layer), over both header rows. Stack 7.4-7.5 mm.
   - **On: only if the measured height passes.** 9.8 mm with the assumed 4.9 mm XIAO, over the 9.0 mm limit. It is allowed only if item 4 measures the XIAO at 4.1 mm or less (0.8 + 1.6 + 2.5 + XIAO at most 9.0).
   - **Settled 2026-10-14: spacer off, Kapton shim.** The XIAO measured 4.52 mm (item 4), so spacer-on is 9.42 mm, over the limit. Spacer-off stack: 0.8 + 1.6 + 0.06-0.2 + 4.52 = 6.98-7.12 mm.
   - Either way, trim the post tails to 0.8 mm under the board, and the posts above the XIAO.
3. **Assemble 2 or all 5.** All 5 costs about $9.74 more (PRICING.md). Check the order form's PCBA-quantity box: that you can assemble 2 of 5 boards is inferred, not confirmed on JLC's pages.
   - **Settled 2026-10-14: all 5 assembled.** Quote $73.37; paid $50.68 with economy shipping (about $3) and a $10 coupon [V, user].

## Measure

4. **XIAO ESP32S3 Plus overall height**, including the USB-C and the mated U.FL. 4.9 mm is assumed [I]. Also measure the dongle cavity depth and footprint.
   - **Measured 2026-10-14 [V, user]: 4.52 mm**, the USB-C being the tallest part; the mated U.FL plug is lower. Cavity: a little over 31 x 31 x 9 mm, so the 27 x 27 board fits with about 2 mm per side and the 7.1 mm stack leaves about 1.9 mm.
5. **Harness wire exit and strain relief.** The wires leave vertically from pads along the bottom edge. Check:
   - that the bend fits the cavity;
   - the glue or tape point for strain relief.
   - **Dropped 2026-10-14** (user: "I'm not too worried about this").
6. **Tap logic level.** Measure UT3232G VCC (pad 7) under power ("not yet measured" in `docs/serial-link-findings.md`).
   - D3/D4 (VBR 5.6 V minimum) and U3 (5.5 V operating) assume the level is 5.5 V or less.
   - If it is 3.3 V, this is all margin.
   - If it is over 5.5 V, stop and redesign.
   - **Measured 2026-10-14 [V, user]: 3.278 V** (pad 7 to pad 6). All margin.
7. **12 V rail maximum** at the DB9 under all inverter states. TVS1 starts conducting at about 20 V. If the rail can exceed about 17 V, use SMF24A.
   - **Measured 2026-10-14 [V, user]: 12.098 V DC** (one reading). Well under 17 V: TVS1 stays SMF18A.

## Confirm in JLC's order preview (Confirm Parts Placement = Yes)

8. **CPL rotations.**
   - The offsets come from the JLCKicadTools database, not from JLC [I]: SOT-23* -90 (U2, which then reads 180) and SOT363-2 180 (U3, which then reads 0).
   - The diodes have no offset.
   - The custom SOT363-2 footprint has the same pad map as stock KiCad SOT-363_SC-70-6 (pin 1 top-left, counter-clockwise), which is the footprint the rule targets. A test checks this.
   - Check U2 pin 1 (CB) at C8, U3 pin 1 (1A) at R3/R5, and the D1/D2/TVS1 bands against `fab/render_top.png`.
9. **Stock and status** on the day of ordering. U2 (3,160) and R14 (6,968) have the thinnest stock. Basic/Extended status can change.

9a. **Tooling holes = "Added by Customer".** TH1/TH2 are on the top-left and top-right corners (adjacent, not diagonal). JLC's page says "opposite corners" and never "diagonal" [V], but its DFM could read the top pair as not opposite and fall back to its own diagonal holes, which could cut J1 pad 1 (+12V_IN) at the bottom-left. If JLC asks, do not accept their default holes. The only way to a diagonal pair is to move C3 (its pad 2 sits about 1.5 mm from the bottom-right corner) and probably L1 and C4: a layout change for you to decide.
9b. **TH2 is under the XIAO** (inside U1's courtyard; DRC `npth_inside_courtyard` is ignored for it). An NPTH has no copper and the fixture pin is used only during SMT, before the XIAO is fitted; the Kapton shim covers it. No action unless JLC objects.
9c. **JLC "mask opening exposing trace" (1 hit)**: not changed. Likely one of three same-net traces along a pad opening (C2 pad 1, R8 pad 1, C7 pad 2); no short risk. Check the location in JLC's DFM viewer if it reappears.

## Not re-verified in Rev B

10. **Kept Rev A parts:** U2, L1, F1, D1, D2, C1-C4, C7 and C8.
    - Their netlist, polarity and ratings were confirmed in the Rev A review (`review-synthesis.md`, "Agreed correct").
    - Their stock KiCad land patterns were not re-read against each datasheet today. Only TVS1 (SOD-123F) was re-checked [V].
    - Spot-check F1 (1812) and L1 (FNR4030S) against their datasheets before ordering.
11. **Sullins post tolerance.**
    - Drawing 11635 rev B gives a 0.64 mm post with a 1.00 mm recommended hole.
    - Its ±0.20 mm general tolerance is a title-block default, not a stated post tolerance.
    - The sibling drawing 10492 rev L gives the hole as 1.02 ± 0.05 mm.
    - At the largest post that tolerance allows (0.84 mm, diagonal 1.19 mm), a 1.02 mm minimum hole would not fit. Real 0.64 mm square headers fit 1.0 mm holes in practice [I].
    - Check the actual strip against a drilled sample, or a Rev A board, if you have one.
12. **PPTC derating.** The F1 hold current at 60 C is about 0.375 A, inferred from typical PPTC derating; at least 0.3 A is needed. Check the SMD1812P050TF/60 derating table.
13. **D2 forward voltage when cold.** VF is at most 440 mV at 1 A and 25 C [V]. The VBUS floor has 0.12 V of margin. Cold VF is a little higher [I].
14. **JLCONE discount**, unverified (PRICING.md).

## Hand-fit kit

15. **Order the Digi-Key hand-fit kit** with the JLC order (README "Hand-fit kit", `design.KIT`): header strip, Kapton tape, and the harness 10 k resistors (2 per board, CF14JT10K0CT-ND). The 10 k are in no JLC BOM; without them the tap wires lose their series protection.

## Parts to watch

16. **C3 (Samsung CL31A107MQHNNNE, C15008, Basic) is NRND** on Samsung's page and gives about 29 uF at 5 V, not 100 uF (VERIFY-revB.md). No change now: it is in stock (1,482,754 at JLC, read 2026-10-14 [V]) and only bulk storage after D2.
    - There is **no other Basic or Preferred 100 uF 1206 MLCC at JLC** [V]: a JLC parts API search ("100uF 1206", "100uF 1206 6.3V", "100uF 1206 10V", 1,050 unique results, read 2026-10-14) returned only C15008 itself as Basic and no Preferred parts. The only other Basic hit, C16133 (TAJB107K006RNJ), is a 3528 tantalum, not a drop-in.
    - If C3 has to change, the nearest in-stock drop-ins are Extended (+$3.07 feeder fee): Murata GRM31CR60J107ME39L, C77085 (6.3 V, 212,235 in stock), or a 10 V part such as Murata GRM31CR61A107ME05L, C312983 (33,062 in stock), which keeps more capacitance at 5 V [I]. Their lifecycle status was not checked.
