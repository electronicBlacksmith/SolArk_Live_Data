# Rev B independent verification (2026-10-13)

This is a read-only check of `carrier-jlc/` (Board A) and `carrier-diy/` (Board B). No design file,
generator, test or fab output was edited. Nothing was uploaded, and no cart, account or order was
touched.

Tags:
- **[V]**: the primary source was read today (2026-10-13); the URL is given.
- **[I]**: inferred, or the source was a secondary one.

Sources used throughout:
- **JLC stock and price:** the JLC parts API, read today [V]. It was called as `POST
  https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList` with the
  keyword set to the C number. Each part's page is `https://jlcpcb.com/partdetail/<C#>`.
- **Digi-Key stock and price:** `https://www.digikey.com/en/products/result?keywords=<DK PN>`, read
  today [V].
- **Pad geometry:** taken from the placed footprints in each `carrier.kicad_pcb`, by a script, so the
  pads checked are the ones actually used on the board.

## Verdict

| Board | Verdict |
|---|---|
| A (JLC, 27 x 27) | **Orderable once the user's measurements pass.** No blocking part problem. One mount decision is tied to the height measurement (§2b). |
| B (DIY, 29 x 30) | **Orderable once the user's measurements pass.** No blocking part problem. |

These are the measurements both verdicts depend on. They are already open items in both boards'
`OPEN-ITEMS.md`:
- The DB9 12 V maximum. There is **no measured value anywhere in `docs/`**. The only figure is
  "+12V_P ≈ 11.7 V (after D1)", an expectation at `docs/hardware/README.md:322`; the [M] checklist
  is in `docs/research/hardware-electrical.md` §5.2 and §9.
- The pad 7 logic voltage.
- The XIAO height and the dongle cavity depth.

## 1. Parts check

Margins are judged against these conditions:
- Input: 12 V nominal. TVS1 starts conducting at 20 V min and clamps at 29.2 V.
- Load: 0.5 A peak at 5 V. That is about 0.28 A at 12 V, assuming 85 % efficiency and D2's loss [I].
- Ambient: the dongle is rated −20 to +55 °C (Sol-Ark 4G dongle datasheet as cited in
  `docs/research/hardware-electrical.md` §5.1; not re-read today, so [I]). A 60 °C derating point is used.

### Shared parts (same MPN on both boards)

**U2, TI LMR51610YDBVR.** Datasheet SLUSEY1B, https://www.ti.com/lit/ds/symlink/lmr51610.pdf [V].
- Ratings [V]:
  - VIN 4-65 V operating, 70 V abs max.
  - FB 5.5 V abs max.
  - High-side peak current limit 1.25 / 1.6 / 1.95 A.
  - The "Y" suffix means 1.1 MHz (0.935-1.265) PFM.
- TI's 5 V / 1.1 MHz row [V]: 10 µH, COUT 10 µF / 25 V, CIN "2.2 µF or higher".
- Margin: 12 V against 65 V, and the clamp (29.2 V) against 70 V. OK.
- Land pattern:
  - Board B uses TI's DBV0006A land (1.1 x 0.6 at ±1.3) [V]: **match**.
  - Board A uses the generic KiCad SOT-23-6 (1.325 x 0.6 at ±1.1375). The inner pad edge is 0.475 mm from centre, against TI's 0.75. **Acceptable** (an IPC-7351 variant, which TI's note 6 allows) [V].
  - Both CHANGES files said "stock, kept, [I]". This is now [V].
- Stock [V]:
  - JLC C22427220: 3,160 (Extended).
  - Digi-Key 296-LMR51610YDBVRCT-ND: 4,188 at $1.71.

**D2, Nexperia PMEG4030ER,115.** https://assets.nexperia.com/documents/data-sheet/PMEG4030ER.pdf [V].
- Ratings: 40 V, 3 A [V]. VF is 440 mV max at 1 A and 25 °C [V]. At 0.5 A the curve reads about 0.34 V at 25 °C and about 0.42 V at −40 °C [I].
- Land: 1.2 x 1.2 at ±1.4 against Fig. 15 [V]: **match** on both boards.
- Stock [V]:
  - JLC C389355: 11,286.
  - Digi-Key 1727-5313-1-ND: 195,583.

**D1, B5819W.** Board A and Board B's route (a) use CJ C8598; Board B's route (b) uses MCC B5819W-TP.
- CJ datasheet (LCSC mirror, https://www.lcsc.com/datasheet/lcsc_datasheet_2304140030_Jiangsu-Changjing-Electronics-Technology-Co---Ltd--B5819W-SL_C8598.pdf) [V]:
  - Ratings: 40 V, 1 A, IFSM 9 A.
  - Suggested pad 0.8 x 1.0 at ±1.62. Ours, 0.9 x 1.2 at ±1.65, is **acceptable**.
- MCC datasheet (https://www.mccsemi.com/pdf/Products/B5817W-B5819W(SOD-123).pdf) [V]: suggested pad 0.91 x 1.22, 2.36 gap. **Match**.
- Margin: 40 V against the 29.2 V clamp. OK.
- Stock [V]:
  - JLC C8598: 383,590 (Basic).
  - Digi-Key B5819W-TPMSCT-ND: 39,242.

**C1, 10 µF 50 V X5R 1206.** JLC C13585 is Samsung CL31A106KBHNNNE.
- DC bias: about 3.4 µF effective at 12 V ([V], the DC-bias graph data on https://product.samsungsem.com/mlcc/CL31A106KBHNNN.do).
- Margin: TI asks for at least 2.2 µF. OK, and 50 V against the 29.2 V clamp is also OK.
- Stock [V]:
  - JLC: 2,156,716.
  - Digi-Key 13-CC1206KKX5R9BB106CT-ND (Yageo): 22,608.

**C3, 100 µF 6.3 V X5R 1206.** The JLC part is Samsung CL31A107MQHNNNE; Board B's Digi-Key part is Taiyo Yuden JMK316BJ107ML-T.
- About **29 µF effective at 5 V** for the Samsung ([V], same Samsung page source).
- Samsung's page lists this part as **NRND** [V]. The Taiyo Yuden part is **NFND** at Digi-Key [V].
- Both are still in stock [V]: JLC 1,697,889; Digi-Key 587-1963-1-ND 394,421.
- This is non-blocking, because C3 is bulk storage after D2. But the "100 µF" in the docs is really about 30 µF in this circuit.

**R3, R4, R7, R8 (1k) and R5, R6 (100k).** These are Basic parts, all in stock [V]:
- Board A (0402): C11702 7.88 M, C25741 9.75 M.
- Board B's route (a) (0603): C21190 25.6 M, C25803 20.3 M.
- Board B's route (b) at Digi-Key: 311-1.00KHRCT-ND 2,586,193, and 311-100KHRCT-ND **7,010** (low for a common value, but enough).

### Board A only (JLC stock [V] from the API)

| Ref | Part / LCSC | Stock (min, attrition) | Land vs datasheet | Ratings in this circuit |
|---|---|---|---|---|
| L1 | cjiang FNR4030S100MT, C167879 | 105,918 (5, 5) | 1.1 x 3.7 at ±1.5 against the datasheet's a/b/c = 1.9/1.1/3.7: **match** [V, LCSC mirror of the CJ PDF] | 10 µH ±20 %, Irms 1.5 A, DCR 0.13 Ω max [V]. **Isat is 1.95 A (rated) / 2.40 A typical at a 30 % drop. That only equals U2's 1.95 A maximum peak limit**, and TI asks for Isat above the limit [V]. In normal use the peak is about 0.63 A, so this is a margin issue only in an overload or short. Non-blocking. |
| F1 | PTTC SMD1812P050TF/60, C462518 | 3,885 (5, 0) | Datasheet land is 1.78 x 3.15, gap 3.45 (centres ±2.615) [V, LCSC mirror]. Ours is the generic Fuse_1812, 1.125 x 3.4 at ±2.1375. **Acceptable, not a match**: it still covers the terminals (body 4.37-4.73 long, band 0.30-1.20) with a toe [I]. Non-blocking. | 60 V. Ihold 0.50 A at 23 °C, **0.37 A at 60 °C** [V], against about 0.28 A peak input: about 30 % margin. OK. |
| TVS1 | Hongjiacheng SMF18A, C19077512 (Preferred) | 70,450 (15, 4) | Datasheet gives no land. Overall length is 3.60-3.90 [V], so the outer pad edge (1.95) **equals the maximum lead tip**. The pad width (1.1) equals the lead width. This is **marginal but solderable** (flat leads) [I]. Littelfuse's SMF land (1.3 x 1.4 at ±1.45, used on Board B) would be better. Non-blocking. | VRWM 18 V, VBR 20-22.1 V, VC 29.2 V at 6.8 A, 200 W [V]. 12 V nominal has a 6 V standoff margin. Board A's OPEN-ITEMS 7 already says to use SMF24A if the rail exceeds 17 V. |
| C7 | Samsung CL21A226MAQNNNE 22 µF 25 V 0805, C45783 | 3,453,562 (2, 0) | Stock C_0805 | About **10.7 µF at 5 V** [V, Samsung page], against TI's 10 µF. Just enough. |
| C2, C4, C8, C9 | CL05B104KB54PNC, C307331 | 15,024,823 | Stock C_0402 | 50 V X7R. OK. |
| R13, R14 | Yageo RT0402BRD0733KL C728559 / RT0402BRD076K19L C705638 | 12,364 / 6,968 (20, 8) | Stock R_0402 | 0.1 %, 25 ppm. See §2c. |
| U3 | Nexperia 74LVC2G17GW,125, C80500 | 8,570 (5, 4) | Custom SOT363-2. The Board A agent verified it; not re-derived here. | 5.5 V-tolerant inputs, Ioff. |
| D3, D4 | Hongjiacheng H5VL10B, C7420372 (Preferred) | 10,117,515 (20, 12) | Custom DFN1006. The Board A agent verified it; not re-derived here. | VRWM 5 V. OK for 3.3 V or 5 V UART. 15 pF behind the 10 k gives RC = 150 ns, against a 104 µs bit. |

No part's minimum order quantity plus attrition exceeds JLC stock [V].

**Spec error carried from Rev A:** Board A's CHANGES table and BOM call L1 "10 µH 1.6 A, 2.4 A sat". The CJ datasheet guarantees Isat 1.95 A and Irms 1.5 A; 2.4 A and 1.6 A are the **typical** values [V].

**Board A mount hazard [V, computed].** Board A's top THT ring is 1.70 mm. It clears the XIAO Plus
pads 15-23 by only **0.049 mm** when the XIAO sits flush.
- This uses Board B's own test method against `carrier-jlc/lib/seeed/XIAO-ESP32-S3-Plus-SMD.kicad_mod`. Board B's 1.45 mm ring gives 0.174 mm.
- So Board A's spacer-off mount **needs** the 0.1 mm Kapton shim; it cannot be skipped.
- The spacer-on mount avoids the problem, but it is 9.8 mm, over the 9.0 mm limit (§2b).

### Board B only (Digi-Key [V])

| Ref | Part / DK PN | Stock, qty-1 $ | Land vs datasheet | Ratings |
|---|---|---|---|---|
| L1 | Bourns SRP4020TA-100M, SRP4020TA-100MCT-ND | 41,663, $1.07 | 1.5 x 2.4 at ±1.85 against Bourns: **match** (https://www.bourns.com/docs/Product-Datasheets/SRP4020TA.pdf) [V] | Isat 2.3 A (20 % drop), above the 1.95 A limit. Irms 1.8 A, DCR 0.243 Ω max [V]. OK. |
| F1 | Bourns MF-MSMF050/60X-2, 118-MF-MSMF050/60X-2CT-ND | **943**, $0.91 | 1.68 x 2.95, gap 3.1: **match** (https://www.bourns.com/docs/Product-Datasheets/mfmsmf.pdf) [V] | 60 V. Ihold 0.40 A at 60 °C against about 0.28 A [V]. OK. |
| TVS1 | Littelfuse SMF18A, F5820CT-ND | 21,298, $0.57 | 1.3 x 1.4 at ±1.45: **match**. [I] from my side, since littelfuse.com returned 403 to the helper; Board B cites an LCSC mirror of the Littelfuse sheet as [V]. | Same rating as Board A's TVS1. |
| U3 | TI SN74LVC2G17DBVR, 296-SN74LVC2G17DBVRCT-ND | 384,274, $0.20 | DBV0006A: **match** (https://www.ti.com/lit/ds/symlink/sn74lvc2g17.pdf) [V] | VI −0.5 to 6.5 V, Ioff ±10 µA, **HBM 2 kV, CDM 1 kV** [V]. Pinout 1A, GND, 2A, 2Y, VCC, 1Y matches [V]. |
| C7 | Taiyo Yuden TMK316BBJ226ML-T, 587-3246-1-ND | 414,245, $0.45 | 1206 | Taiyo Yuden lists the part as **renamed** to MSAST31LBB5226MTNA01 [V]. Digi-Key still shows it Active. Non-blocking. |
| R13, R14 | Panasonic ERA-3AEB2052V / ERA-3AEB3831V | 8,440 / 25,291, $0.11 | Generic R_0603. Panasonic publishes no land in the datasheet [V]; acceptable [I]. | ±0.1 %, ±25 ppm/K, 0.1 W [V] (https://industrial.panasonic.com/cdbs/www-data/pdf/RDM0000/AOA0000C307.pdf) |
| C2, C4, C8, C9 | Yageo CC0603KRX7R9BB104, 311-1344-1-ND | 4,770,583 | 0603 | OK |
| Header and plug | S1011EC-40-ND / S7004-ND | 45,650 / 26,627 | – | – |

All 17 Digi-Key part numbers map to the MPNs in `carrier_bom_digikey.csv` [V]. The parts subtotal of
**$20.34 is confirmed** [V].

## 2. Board-specific risks

### (a) Board B without D3/D4 ESD diodes

**Facts:**
- U3 is rated HBM 2 kV and CDM 1 kV [V].
- Both READMEs specify the 10 k at the **dongle-pad end** of each tap wire ([V],
  `carrier-diy/README.md:71`, `carrier-jlc/README.md:108`). **Neither board's BOM or kit includes
  those 10 k resistors.** Buy them separately.

**Judgement [I]:**
- The harness ends up inside a closed dongle, so once installed nothing is exposed.
- The exposure is during harness building and installation, with the board unpowered.
- A zap at the J1 end goes through R3/R4 (1 k) only, not through the 10 k. Adding 1 k to the 1.5 kΩ
  HBM network gives roughly a 3 kV equivalent on the J1 side, and about 15 kV through the dongle-end
  10 k.
- That is **adequate with basic ESD handling** (wrist strap, or touch ground before handling the J1
  wires). It is not adequate for "handled live" use.
- U3 failing cannot disturb the dongle link: the 10 k remains, and U3's outputs face only the XIAO.
- So this is **non-blocking**.

**Cost to keep the diodes:**
- The SOT-23 dual Board B's OPEN-ITEMS O9 suggests (Nexperia PESD5V0S2BT,215, 1727-3840-1-ND) is
  **out of stock until 13 Jul 2027** [V].
- An in-stock fit for 0-5 V UART lines is Littelfuse SP0502BAHTG (F2714CT-ND): 56,517 in stock,
  $1.18 [V]. It is a 2-channel unidirectional array, VRWM 5.5 V. One part covers both lines.
- Total about **$2.36 for 2 boards**, plus a SOT-23 land and a re-layout of the left strip. That costs
  a layout pass.
- On Board A, D3/D4 are Preferred at $0.0064 each with no feeder fee, so they are effectively free
  there.

### (b) Stack height

The two numbers describe **different mounts**. On the same mount the boards agree to within 0.4 mm:

| Mount | Board A | Board B | Difference |
|---|---|---|---|
| Header spacer left on (2.50 mm [V, Sullins]) | 0.8 + 1.6 + 2.5 + 4.9 = **9.8** | 1.0 + 1.6 + 2.5 + 4.9 = **10.0** | Tail trim (0.8 against 1.0) |
| Spacer removed | 0.8 + 1.6 + 0.1 (Kapton) + 4.9 = **7.4** | 1.0 + 1.6 + 0.3 (air gap) + 4.9 = **7.8** | Tail, plus shim against gap |

- Spacer-on fails the 9.0 mm limit on both boards.
- Spacer-off passes on both, but rests on the **4.9 mm XIAO height, which Seeed does not publish**.
  The wiki gives only 21 x 17.8 mm for the S3 and S3 Plus ([V],
  https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/). A third-party page says 5 mm [I].
- On Board A, spacer-off also requires the Kapton shim (0.049 mm ring clearance, §1).
- Measure the XIAO and the cavity before ordering. Board B's OPEN-ITEMS O1 gives the procedure.

### (c) Divider worst case (recomputed)

Inputs:
- VFB is 0.788 / 0.800 / 0.812 V [V].
- The datasheet's "PFM operation −1.5 % / +2.5 %" row has these conditions [V]: system level,
  typical components, VIN = 24 V, not production tested. **TI does not say whether it adds to the VFB
  tolerance.**
- Per-resistor tolerance: Board A uses 0.35 % (100 K excursion); Board B uses 0.25 % (60 K).

| | Board A 33k / 6.19k | Board B 20.5k / 3.83k |
|---|---|---|
| Ratio, nominal | 5.3312 → 5.065 V | 5.3525 → 5.082 V |
| The board's own max | 5.222 V (recomputed: **correct**) | 5.180 V (**correct**) |
| The board's own min at the pin | 4.520 V, using D2 0.44 V (**correct**) | 4.485 V, using D2 0.50 V (**correct**) |
| Stacked max: VFB max x 1.025, pre-D2 | 5.301 V | 5.309 V |
| Stacked min: VFB min x 0.985, D2 0.42 V at −40 °C [I] | 4.465 V | 4.490 V |
| Stacked min with D2 0.50 V | **4.385 V** | 4.410 V |

**Inconsistency:**
- Board A applies the PFM +2.5 % on the max side only and omits the −1.5 % on the min side.
- Board B omits the PFM term on both sides.
- Applying one model to both: in the most pessimistic stack, Board A's floor is 15 mV under the
  4.40 V target.

**Why it is non-blocking for both [I]:**
- 4.40 V is a USB host figure, not a load requirement. The real floor is the XIAO's SGM6029 3V3
  buck, which only needs about 0.5 V of headroom at 400 mA, so about 3.8 V
  (`docs/research/hardware-electrical.md:145-149`).
- The real ceiling is the SGM6029's 5.5 V operating rating [I, from Seeed's schematic], not 5.25 V,
  because the USB rule forbids having USB and 12 V connected at once.
- 5.31 V pre-D2 passes both.

## 3. Normalized pricing

One set of assumptions, used for every route:

| Item | Assumption | Tag |
|---|---|---|
| JLC 4-layer, 5 pcs (both outlines are under 10 x 10 cm) | $7.00 for both boards | [I]. JLC publishes "start at just $7" for 10 x 10 cm with no quantity stated (https://jlcpcb.com/features/prototype-pcb-way). The same page says "1-8 layer PCBs starting at $2" with no size stated. |
| PCBA fees | Setup $8.18, stencil $1.53, Extended $3.07 each, $0.0016/joint, confirm placement $0.45 | [V] https://jlcpcb.com/help/article/40-pcb-assembly-price |
| Preferred Extended parts | No feeder fee in Economic | [V] https://jlcpcb.com/help/article/PCB-assembly-faqs |
| Pre-reflow soldering, $0.016/joint | **Excluded from both** (the page states no condition). Sensitivity: +$1.79 for A (112 joints), +$0.83 for B-a (52). | rate [V], applicability [I] |
| LCSC parts | Recomputed from the API, using order quantity = max(need + attrition, minimum) | [V] |
| US DDP duty | PCB 35 %, SMT 35 %, stencil 90 % (latest entry, 17 Mar 2026). Base = product value, excluding shipping. | rates [V] https://jlcpcb.com/news/logistics-update-us-china-tariff; base [I], since neither JLC page states it (https://jlcpcb.com/help/article/us-tariff-policy-faq, updated 9 Sep 2026, confirms individual US orders ship DDP) |
| JLC shipping | **$20, DHL DDP, for both** | [I]. JLC publishes no rate table; the price shows only at checkout. Sensitivity: ±$10. |
| Digi-Key | Prices as read; USPS Ground Advantage $4.99 on every route that buys there | [V] https://www.digikey.com/en/help-support/delivery-information/delivery-time-and-cost |
| OSH Park | $10/sq in for 3 boards; USPS First Class free; made in the US, so no duty | [V] https://docs.oshpark.com/services/four-layer/, https://docs.oshpark.com/submitting-orders/shipping-information/ |

Excluded from every route: sales tax, the harness 10 k resistors, wire, and Kapton.

| Line ($) | A: JLC full assembly, 2 of 5 | A: all 5 | B-a: JLC Basic + hand-fit, 2 of 5 | B-b: OSH Park + Digi-Key, 3 bare |
|---|---|---|---|---|
| PCB | 7.00 [I] | 7.00 [I] | 7.00 [I] | 13.49 [V] |
| Setup, stencil, placement | 10.16 [V] | 10.16 [V] | 10.16 [V] | – |
| Extended fees | 21.49 (7) [V] | 21.49 [V] | 0 [V] | – |
| Joints | 0.18 [V] | 0.45 [V] | 0.08 [V] | – |
| LCSC parts | 15.21 [V] | 21.24 [V] | **2.69** [V] (Board B's file assumed 0.77 [I]) | – |
| Duty (35 % SMT rate applied to LCSC parts too [I]) | 19.76 | 21.96 | 7.82 | 0 |
| JLC shipping | 20 [I] | 20 [I] | 20 [I] | 0 [V] |
| Digi-Key parts | 1.23 (1 header strip) | 2.46 | 14.84 [V] | 20.34 [V] |
| Digi-Key shipping | 4.99 [V] (Board A's file excluded this) | 4.99 | 4.99 | 4.99 |
| **Total** | **≈ 100.02** | **≈ 109.75** | **≈ 67.58** | **38.82** |
| Per working board | 50.01 | 21.95 | 33.79 | 19.41 |
| Hand soldering | Headers and wires only | same | 9 SMD parts per board, plus headers and wires | 22 SMD parts per board, plus headers and wires |

Changes from the boards' own files:
- **A** goes from $95.04 to $100.02: Digi-Key shipping is added.
- **B-a** goes from ≈ $57 to $67.58:
  - shipping is $20 instead of $9.5;
  - the PCB is $7 instead of $8;
  - LCSC parts are $2.69 instead of $0.77;
  - pre-reflow is dropped.
- **B-b** is unchanged and fully [V].

Shipping sensitivity: at $10 shipping, A (2 boards) drops to about $90 and B-a to about $58. The
ranking is the same either way: B-b, then B-a, then A.

**JLCONE: unverified, not counted.** JLC's article, dated 22 Aug 2026
(https://jlcpcb.com/news/jlcpcb-jlcone-desktop-app) [V], says:
- a random $1-20 off the order total, as a "limited-time event" with no end date;
- a $104 coupon pack, of which one coupon may stack with the random discount;
- PCBA eligibility and the $2 PCB deal's layer limits are **not stated**.

Board A's file cites a different JLC page with a conflicting $123 figure. Possible effect on A or
B-a: −$1 to about −$30 [I].

## Problem list

Board A. Blocking: none.

Board A, non-blocking:
1. L1 FNR4030S100MT: Isat (1.95 A rated) only equals U2's maximum current limit [V]. The fix is a
   higher-Isat 4x4 part; check the land if it changes.
2. TVS1: the generic SOD-123F land sits flush with the maximum lead tip [V dims]. Consider the
   Littelfuse SMF land.
3. F1: the generic 1812 land is smaller than PTTC's recommendation [V]. Acceptable.
4. U2: the generic SOT-23-6 land, not TI's DBV0006A [V]. Acceptable.
5. C3 is NRND and gives about 29 µF effective [V].
6. The divider note omits the −1.5 % PFM term on the min side. The stacked floor is 4.385 V, which
   is fine against the real 3.8 V floor.
7. The spacer-off mount needs the Kapton shim (0.049 mm clearance); spacer-on is 9.8 mm, over the
   9.0 mm limit.
8. The PRICING.md total excludes Digi-Key shipping (it says so).
9. L1 is documented as "2.4 A sat", which is the typical value; the guaranteed Isat is 1.95 A [V].

Board B. Blocking: none.

Board B, non-blocking:
1. C3 JMK316BJ107ML-T is NFND [V]. An in-stock alternative is TDK C3216X5R0J107M160AB,
   445-6008-1-ND, 7,980 in stock, $1.11 [V].
2. C7 has been renamed by Taiyo Yuden [V].
3. F1 stock is 943 and R5/R6 stock is 7,010: enough, but watch them.
4. No ESD diodes (§2a). The adequacy is conditional on the 10 k harness resistors and on ESD
   handling.
5. The divider omits the PFM term; the stacked range is 4.41-5.31 V, which is fine.
6. The R12/JP1/TP1 proxy pads remain. TP1 connects to no tap net, so they are rule-6 compliant by
   population, but Board A removed them.
7. Route (a) pricing understates LCSC parts and shipping.
8. DRC uses `ring 0.11`, which is below JLC's 4-layer PTH minimum of 0.15 mm (recommended 0.20; https://jlcpcb.com/capabilities/pcb-capabilities [V]). So for route (a), DRC alone does not prove JLC compliance. The actual geometry does pass: XIAO top ring (1.45 − 1.10)/2 = **0.175 mm**, J1 ring 0.40, vias 0.6/0.3 = 0.15 [V, from the PCB]. It is below JLC's recommended 0.20 on the XIAO ring, so expect a possible DFM warning, not a rejection [I].

Board A's "0.235 mm worst case against JLC's 0.20 minimum" and Board B's "0.11 is the strictest of the two fabs" use different definitions. JLC's published rule is 0.15 minimum and 0.20 recommended on the nominal ring. By that rule, Board A has 0.30 nominal and Board B 0.175. Both boards' vias (0.6/0.3) sit exactly at the 0.15 minimum.

Both boards:
- The harness 10 k resistors are in no BOM. Buy them separately.
