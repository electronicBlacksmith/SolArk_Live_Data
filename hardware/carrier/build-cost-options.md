# Carrier build: cost options (research, 2026-10-12)

This report covers how to get 1–2 working carrier boards built for the least
money per order, and which design changes would cut that cost. It is research
only:
- No design file was changed.
- Nothing was uploaded to a quote site, ordered or signed up for.

Every price was read on 2026-10-12 from the source shown. Each figure is
marked:
- **[V]** verified: read on a vendor page or from the JLC parts-search API on that date.
- **[I]** inferred: my arithmetic or estimate. Check it in the real cart.

The baseline assumes the in-flight review fixes land:
- an SN74LVC2G17 RX buffer (U3, SOT-23-6) on the top side
- test points as bare pads
- socket drill of 1.60–1.75 mm

## Bottom line

The §1.2 table ranks options by cash. The recommendations below also weigh your labor and risk, which is why they lead with JLC.

| Pick | What | Cash per order, 2 working boards | Lead time |
|---|---|---|---|
| **No design change** | JLCPCB 4-layer + Economic PCBA, fab 5, assemble 2 | **≈ $110** landed, of which ≈ $78 is the JLC order and ≈ $34 is the Digi-Key hand-fit kit | ≈ 1–2 weeks |
| **Cheapest with changes, still JLC-assembled** | Same, plus 4 BOM and footprint changes (listed below) | **≈ $85** | ≈ 1–2 weeks |
| Cheapest cash overall, if you are set up to hand-solder 0402s and a bottom-terminated inductor | OSH Park 4-layer (3 boards) + Digi-Key parts, self-assembled | **≈ $58** (≈ $80 if you must also buy solder paste) | ≈ 2–3 weeks, plus your bench time |

What drives the cost, in order [I, from the tables below]:
1. Shipping plus the 35 % US duty prepay on a JLC order (≈ $35).
2. JLC Extended-part fees (8 × $3.07 = $24.56).
3. The Mill-Max sockets (≈ $21 for two boards).

The PCB itself is about $2. The 2-layer question barely matters at JLC. It matters only at OSH Park and Aisler.

## 1. Option comparison

### 1.1 Common to every option: the hand-fit kit from Digi-Key

Every route needs these for 2 working boards. They are bought in the US, so no import duty applies.

| Item | Qty | Price | Source |
|---|---|---|---|
| Mill-Max 7305-0-15-15-47-27-10-0 | 30 (2 × 14 + 2 spares) | $0.688 each at 25+ [V], so ≈ $20.60 [I] | [Digi-Key](https://www.digikey.com/en/products/result?keywords=7305-0-15-15-47-27-10-0) |
| Sullins PRPC040SAAN-RC header (XIAO pins) | 1 | $1.23 [V] | [Digi-Key](https://www.digikey.com/en/products/result?keywords=PRPC040SAAN-RC) |
| GH harness: GHR-06V-S $0.16 [V] + pre-crimped leads, e.g. AGHGH28K305, $0.58 [V] | 2 housings + ≈ 8 leads | ≈ $5 [I] | [GHR-06V-S](https://www.digikey.com/en/products/result?keywords=GHR-06V-S), [AGHGH28K305](https://www.digikey.com/en/products/result?keywords=AGHGH28K305) |
| Shipping, USPS Ground Advantage | — | $4.99 [V] | [Digi-Key shipping](https://www.digikey.com/en/help/same-day-shipping) |
| **Kit total** | | **≈ $32–34 [I]** | |

### 1.2 Ranked options (cost per order, landed in the US)

"2 asm" means 5 bare PCBs with 2 assembled. "All asm" means every board the fab ships is assembled. The kit from 1.1 is included in every total.

| Rank | Option | 2 asm | All asm | Lead time | Design change |
|---|---|---|---|---|---|
| 1 | **OSH Park 4-layer** (3 boards) + Digi-Key parts, hand or hot-plate assembled | **≈ $58** | ≈ $63 (3 boards) | 9–14 days fab [V] + parts, plus your labor | None, except the inductor footprint check in 1.4 |
| 2 | **JLC Economic, basic parts only.** JLC places the passives, D1, D2 and TVS (after the changes in §3). You hand-fit U2, L1, F1 and U3 from Digi-Key | ≈ $73 | ≈ $78 | ≈ 1–2 weeks | The §3 changes |
| 3 | **JLC Economic, with the §3 changes** (4 Extended parts) | **≈ $85** | ≈ $95 | ≈ 1–2 weeks | The §3 changes |
| 4 | **JLC Economic, as designed** (8 Extended parts) | **≈ $110** | ≈ $125 | ≈ 1–2 weeks | None |
| 5 | OSH Park **2-layer** + self-assembly | ≈ $52 | ≈ $57 | 9–12 days [V] | 2-layer re-layout (§2). Saves only $5.65 |
| 6 | JLC bare PCB + stencil, self-assembled | ≈ $75–80 | — | ≈ 1–2 weeks | None. Shipping and duty swamp the $2 board, so this is worse than option 1 |
| — | Aisler 4-layer bare (3 boards) + self-assembly | ≈ €42 boards [V] + UPS + duty | — | not found | None. Strictly worse than OSH Park for a US buyer |
| — | PCBWay, Seeed Fusion, NextPCB, Elecrow (turnkey PCBA) | not priced (no published small-qty table) | — | 1–4 weeks | None. Expected to cost more than JLC [I]; see 1.5 |

### 1.3 JLC arithmetic (the basis for rows 2–4)

**Fees** [V] ([JLC PCBA price page, last updated 2026-09-09](https://jlcpcb.com/help/article/40-pcb-assembly-price)):

| Fee | Economic | Standard |
|---|---|---|
| Setup | $8.18 | $25.56 (one side) |
| Stencil | $1.53 | $8.21 |
| Feeder loading | $3.07 per Extended part | $1.53 per Basic **and** Extended part |
| Joints | $0.016 pre-reflow + $0.0016 SMT per joint | same |
| Confirm parts placement | $0.45 | $0.45 |
| Hand-solder labor | $3.58 per order | $3.58 per order |

**Does a 4-layer board force Standard?** No [V]. Per the [JLC PCBA capabilities page](https://jlcpcb.com/capabilities/pcb-assembly-capabilities), Economic allows:
- 2, 4 or 6 layers
- 0.8–1.6 mm thickness
- single-side placement only
- 2–50 pcs
- 0402 minimum, 0.4 mm minimum pitch

This board meets all of that. Known risk 5 in the carrier README ("4-layer may require Standard") is therefore not a risk. Standard would cost ≈ $40 more here [I].

**Preferred Extended parts** are exempt from the Economic feeder fee [V] ([JLC PCBA FAQ](https://jlcpcb.com/help/article/pcb-assembly-faqs)).

**PCB price:**
- "From $2.00 / 5 pcs" for FR-4 1–32 layers [V] ([jlcpcb.com](https://jlcpcb.com/)).
- The $2 applies at 50×50 mm or smaller with default options. A non-default colour, copper weight or panelization adds the normal charges [V, secondary: [JLC 4-layer news](https://jlcpcb.com/news/discount-on-quality-4-layer-pcbs), [LCSC price page](https://www.lcsc.com/pcba/price)].
- The ENIG upcharge was **not found** on a published page. The README asks for ENIG but says lead-free HASL also works. **Choose HASL to stay near $2.**

**Duty:**
- JLC's US notice says that since **2026-03-17** the DDP prepay is **35 % on PCB and SMT** and **90 % on stencils** [V] ([JLC US tariff notice](https://jlcpcb.com/news/logistics-update-us-china-tariff)).
- US de minimis is gone for all countries (effective 2025-08-29, per FedEx via search summary; not opened directly).
- One forum report (May 2026) puts DDP brokerage at about $40 versus about $20 on DHL CPT ([EEVblog](https://www.eevblog.com/forum/manufacture/jlc-tarriffs-etc-to-us/)). Treat it as anecdotal.

**Shipping to the US:** no official table was found. I use **≈ $20 for DHL** [I], based on [Hack Club's JLC guide](https://highway.hackclub.com/guides/JLC-cost-optimizing) and [this shipping post](https://www.petertanner.dev/posts/JLCPCB-shipping-price-hack/). Global Standard Direct is cheaper but slower.

**Parts:** JLC prices from the parts-search API on 2026-10-12 [V], at quantity 1:

| Part | Price | Library status |
|---|---|---|
| U2 LMR51610 | $1.12 | Extended |
| U3 SN74LVC2G17 (C10429) | $0.23 | Extended |
| F1 | $0.30 | Extended |
| D2 | $0.27 | Extended |
| J1 | $0.07 | Extended |
| L1 | $0.05 | Extended |
| TVS1 | $0.03 | Extended |
| D1 | $0.03 | Basic |
| Passives | ≈ $0.15 [I] | Basic, except R13 |

Total parts per board ≈ $2.30 [I]. The board has about 52 joints, so ≈ $0.94 per board in joint fees [I].

**Row 4, as designed (assemble 2):**

| Item | Cost |
|---|---|
| PCB | $2 |
| Setup | $8.18 |
| Stencil | $1.53 |
| Feeder fees (8 × $3.07) | $24.56 |
| Joints | $1.88 |
| Parts | $4.60 |
| Confirm placement | $0.45 |
| **JLC subtotal** | **$43.2** |
| Duty (35 %) | ≈ $15 |
| DHL | ≈ $20 |
| Kit | ≈ $33 |
| **Total** | **≈ $110** [I] |

Assembling all 5 adds ≈ $3.24 per board in parts and joints, plus 35 % duty on it, for a total of **≈ $125** [I].

**Row 3, with the §3 changes:**
- Feeder fees drop to 4 × $3.07 = $12.28.
- D2 and J1 become cheap or go away.
- The JLC subtotal is ≈ $30, duty ≈ $10.50 and DHL ≈ $20.
- The kit drops to ≈ $28 (no GH parts).
- **Total ≈ $85** [I].

**Row 2, basic parts only:**
- No feeder fees. The JLC subtotal is ≈ $14, duty ≈ $5 and DHL ≈ $20.
- Digi-Key parts for U2, L1, F1 and U3 cost ≈ $7 for 2 sets [I].
- **Total ≈ $73** [I].
- You hand-solder a SOT-23-6 regulator, an 1812 fuse, a SOT-23-6 buffer and a 4×4 mm inductor whose pads sit underneath it (hot air or a hot plate needed).
- The same Digi-Key catches as the OSH Park route apply (1.4): FNR4030S is not stocked, so the SRN4018 land pattern must be checked, and a 60 V 1812 PPTC was not found.

**Fab 5, assemble 2:** JLC's published pages say Economic takes 2–50 pcs. They do not say outright that you can assemble fewer boards than you fabricate [not found]. It is widely reported that the quote form allows this. Confirm on the quote page.

### 1.4 OSH Park arithmetic (rows 1 and 5)

- **4-layer:** $10 per sq in for 3 boards [V] ([OSH Park 4-layer](https://docs.oshpark.com/services/four-layer/)). The board is 1.13 sq in, so **$11.30** [I].
- **2-layer:** $5 per sq in for 3 boards [V] ([2-layer](https://docs.oshpark.com/services/two-layer/)), so **$5.65** [I].
- Shipping is free worldwide [V] ([services](https://docs.oshpark.com/services/)). The board is made in the US, so there is no import duty.
- **Capabilities** [V]:

  | Service | Min drill | Min ring | Min trace/space |
  |---|---|---|---|
  | 4-layer | 10 mil | 4 mil | 5/5 mil |
  | 2-layer | 10 mil | 5 mil | 6/6 mil |

  This design uses an 11.8 mil via drill, a 5.9 mil ring and 7.9 mil trace/space. **Both services pass.** I did not find a maximum PTH drill, so check the 1.60–1.75 mm socket holes.
- **Digi-Key parts for 2 boards: ≈ $12.50** [I]. Per-board prices [V] ([Digi-Key searches](https://www.digikey.com/en/products/result?keywords=LMR51610YDBVR)):
  - LMR51610 $1.71
  - SRN4018-100M $0.37
  - 1812L050/30 PPTC $1.24
  - SMF18A $0.065
  - PMEG4030ER $0.59
  - B5819W $0.09
  - SN74LVC2G17 $0.20
  - SM06B-GHS-TB $0.49
  - 0402 passives about $0.02–0.07 each at qty 10
- **Total ≈ $11.30 + $12.50 + the $33 kit = ≈ $58** [I].
- Add **$20.95** for Chip Quik SMD291AX10 paste [V] ([Digi-Key](https://www.digikey.com/en/products/result?keywords=SMD291AX10)) if you don't have paste.
- A Miniware MHP30 hot plate is ≈ $100 [V] ([SainSmart](https://sainsmart.com/products/miniware-60w-mini-hot-plate-preheater-soldering-station)) if you have neither a plate nor hot air.
- OSH Stencils' current price was **not found**. Paste can be dispensed by syringe for 2 boards.
- **Catches on the Digi-Key route** [I]:
  - The JLC inductor (Changjiang FNR4030S) is not at Digi-Key. A Bourns SRN4018-100M is a 4×4 mm substitute, but its land pattern must be checked against the `L_Changjiang_FNR4030S` footprint before you treat this as "no change".
  - The 60 V LCSC PPTC was not found at Digi-Key. The Littelfuse 1812L050/30 is rated only 30 V. That is fine for a 12 V rail but close to TVS1's 29 V clamp. Find a 1812 0.5 A PPTC rated at least 60 V, or accept the 30 V part knowingly.
  - You place about 20 parts per board by hand, including 0402s. This is cheapest only if your time is free and you already own the tools.

### 1.5 Other fabs (why they are not ranked with numbers)

None of these publishes a small-quantity price table that can be read without the quote tool, which needs an upload [V, all accessed 2026-10-12].

- **NextPCB:** "$200 off turnkey PCBA, 1–10 pcs", but the SMT cost after the discount is **at least $50**, shipping is extra, and the offer does not apply if 5 % or more of the parts are customer-supplied ([NextPCB promo](https://www.nextpcb.com/blog/Free-PCB-Assembly-50-pieces)). Typical lead time is 17–30 business days ([lead time](https://www.nextpcb.com/helpcenter/lead-time-for-pcb-assembly-orders)). The $50 floor alone exceeds JLC's whole row-3 subtotal, so I rank it **below JLC** [I].
- **PCBWay:**
  - The setup fee is not published.
  - Its assembly page shows the stencil as part of the quote, and separate stencil orders at $10–15.
  - The importer of record pays duty ([PCBWay assembly](https://www.pcbway.com/pcb-assembly.html), [duty FAQ](https://www.pcbway.com/helpcenter/shipping_instructions/Who_will_be_responsible_for_the_customs_duty_that_may_be_levied_at_my_country_.html)).
  - A "$29 free shipping, 1–20 pcs assembly" banner has terms I could not find.
  - Parts come from Western distributors at a markup, so the Extended-part situation does not apply. Expected to land at or above JLC [I].
- **Seeed Fusion:**
  - The free 5-piece assembly offer was terminated ([Seeed notice](https://support.seeed.cc/portal/en/kb/articles/termination-of-the-5-pieces-pcba-free-assembly-offer)).
  - Terms are DAP (you pay duty on delivery), and a 2025 note cited about 30–45 % duty on PCBA ([Seeed duties](https://support.seeed.cc/portal/en/kb/articles/customs-duties-and-taxes)).
  - No current setup fee was found.
- **Elecrow:**
  - The only figures found were from a dated brochure: $10 engineering fee, $0.03 per SMD pad, $5 per design under 20 pcs, and a $12 stencil in the sample quote ([Elecrow PCBA](https://www.elecrow.com/pcb-assembly.html), [brochure](https://elecrow.com/blog/elecrow-pcba-service.html)).
  - PCBA lead time is about 3 weeks.
  - Its minimum via drill is 0.3 mm, exactly this design's via [V] ([Elecrow PCB](https://www.elecrow.com/pcb-manufacturing.html)).
- **Aisler:**
  - Price = job fee + area fee, in sets of 3 [V] ([Aisler pricing](https://community.aisler.net/t/our-simple-pricing/102)):
    - 4-layer ENIG: €14 + €0.13/cm², so ≈ €42 for 3 boards [I].
    - 2-layer HASL: €12 + €0.067/cm², so ≈ €26 for 3 boards [I].
  - US orders ship by UPS only. The customer pays duty, which Aisler cannot collect in advance ([Aisler shipping](https://community.aisler.net/t/shipping-methods/672)).
  - The assembly price is not published.
  - Already more than OSH Park before shipping.

**Fab capability check** against this design (0.3/0.6 mm via, 0.2 mm trace/space, 1.6–1.75 mm PTH) [V]:

| Fab | Result | Source |
|---|---|---|
| JLC | Passes. Minimum via 0.15/0.25 mm. Minimum PTH ring 0.15 mm on 4-layer, 0.18 mm on 2-layer | [JLC capabilities](https://jlcpcb.com/capabilities/Capabilities) |
| PCBWay | Passes, but the 0.15 mm ring is at its standard minimum | [PCBWay capabilities](https://www.pcbway.com/capabilities.html) |
| OSH Park | Passes | see 1.4 |
| Aisler | Passes at the 150 µm via-ring minimum | [Aisler 4-layer rules](https://community.aisler.net/t/4-layer-70-m-hasl-design-rules/5773) |
| Elecrow | 0.3 mm via drill is at its minimum | see Elecrow above |

## 2. Can the board go to 2 layers?

**Short answer:** yes, it is technically feasible. **It saves almost nothing at JLC.** Both layer counts are advertised "from $2" for 5 boards at 50×50 mm or smaller [I: the homepage gives only one starting price for 1–32 layers, and the 4-layer $2 figure comes from undated pages]. Even if 4-layer actually quotes at the commonly reported ~$7–8, the 2-layer saving is only ~$5–6 [I]. The other savings are $5.65 at OSH Park and about €16 at Aisler [I]. The re-layout risks the one part of the board that is hard to get right: the buck return path. **Not recommended** unless you are already re-laying the bottom half for other reasons.

**What the inner layers carry now** (from `scripts/routes.py`):
- **In1** is a solid GND plane. It is the only low-impedance path between C1's ground and U2's GND pin. The README admits the compromise: the FB trace on F.Cu passes between C1's GND pad and U2 pin 2, so C1 returns through vias to In1.
- **In2** carries only three things:
  - TAP_RESP, along x ≈ 104.3 mm, about 18 mm long
  - TAP_REQ, along x ≈ 104.9 mm
  - a 3.3 mm +5V_BUCK sense link at y = 118.85 mm, under the buck
- **B.Cu** already carries +12V_P (0.5 mm, x = 103.6 then along y = 125), +3V3, the DNP options and a GND pour.

**What a 2-layer version would need:**
1. **Taps.** Move both tap runs from In2 to B.Cu beside the +12V_P run. Spacing is about 0.35–0.4 mm edge to edge [I], which is enough at 0.2 mm clearance, but it splits the bottom GND pour in the left strip into slivers. That is harmless for DC and 9600 baud.
2. **The real problem: the buck ground.** TI's layout guidance [V] ([LMR51610 datasheet SLUSEY1B, §8.4.1](https://www.ti.com/lit/ds/symlink/lmr51610.pdf)) says:
   - "Grounding for both the input and output capacitors must consist of localized top side planes that connect to the GND pin."
   - Use a middle-layer ground plane "if possible".
   - Route the FB sense "preferably through a layer on the other side of a shielded layer".

   On 2 layers there is no In1 to fall back on, so the current FB crossing becomes a real defect. Review item 8's fix (move FB to an inner layer) is also no longer available. The FB trace must stay on top **without** cutting the C1 → U2 GND copper. That means re-placing R13 and R14 (or C1) so FB leaves U2 pin 3 away from pin 2 and the C1 ground pad, and giving C1, C2 and C7 a continuous top-layer GND island to U2 pin 2.
3. **Sense link.** The +5V_BUCK sense link must go on B.Cu right under the switching area, or be re-routed on top around L1. TI says the VOUT-to-divider trace "can be long" if it avoids SW and the inductor [V, same section].
4. **Thermal.** TI quotes RθJA ≈ 95 °C/W "with a 2-layer PCB" and the same 95 °C/W for its EVM [V, §6.4], so 2 layers is thermally workable. The reviews already flagged buck junction temperature in a closed dongle at 65 °C ambient as a bench item. Losing two inner copper planes moves that the wrong way [I].
5. **Density.** The new U3, the test points and the larger socket pads all compete for the same left strip and bottom side. A 2-layer re-route is a fresh layout of the bottom half of the board, not a layer-count switch.

**Verdict.** At JLC, stay on 4 layers: Economic accepts them [V], so the "4-layer forces Standard" worry in the README is void. Consider 2 layers only for an OSH Park or Aisler self-build, and even then the $5.65 saving doesn't pay for the re-layout and re-review.

## 3. BOM cost levers

### 3.1 JLC Extended parts and Basic or Preferred equivalents

Status is from the JLC parts-search API (`componentLibraryType`, `preferredComponentFlag`) on 2026-10-12 [V].

| Ref | Part | Status | Basic or Preferred equivalent that meets the rating | Action |
|---|---|---|---|---|
| U2 | LMR51610 (C22427220) | Extended | None. The Basic and Preferred bucks are TPS5430, TPS54331, XL1509, LM2596 and LM2576: SOIC-8 or TO-263 parts at 52–570 kHz, which need a much larger inductor. None fits the board | Keep. Pay $3.07 |
| L1 | FNR4030S 10 µH (C167879) | Extended | None. The only Basic 10 µH parts are multilayer chips rated 3–25 mA (C1035, C1046, C1051) | Keep. Pay $3.07 |
| F1 | SMD1812P050TF/60 (C462518) | Extended | None. No Basic or Preferred PPTC or fuse was found | Keep, or hand-solder (an easy 1812 part) |
| U3 | SN74LVC2G17 (C10429) | Extended | None equivalent. The only Basic Schmitt part is the 74HC14D (C5605). It inverts, it comes in a larger SOIC-14, and it lacks 5.5 V-tolerant inputs and Ioff powered-down protection, which were the reasons for choosing the LVC2G17 | Keep. Pay $3.07 |
| TVS1 | SMF18A (C123787) | Extended | **SMAJ18A, C19077538, Preferred Extended** (no Economic fee): 18 V standoff, 29.2 V clamp, 400 W, 54,570 in stock. It matches or beats the SMF18A's rating, but in the larger SMA package | **Swap, only if the SMA footprint fits** in the left strip (see §5, item 3). Needs a footprint change, SOD-123F to SMA |
| D2 | PMEG4030ER (C389355) | Extended | **SS34, C8678, Basic** (40 V 3 A, 0.55 V at 3 A, SMA package), or **B5819W, C8598, Basic** (already D1; 40 V 1 A, 0.6 V at 1 A, SOD-123) | **Swap** to B5819W (one fewer BOM line) together with the divider change below. The higher Vf is paid for by the higher Vout. Footprint change |
| R13 | 27 k 0402 (C25771) | Extended | **R13 = 12 k (C25752, Basic), R14 = 2.2 k (C25879, Basic).** Vout = 0.8 × (1 + 12/2.2) = **5.164 V** [I]. This is the only Basic 0402 1 % pair that lands in 5.0–5.35 V | **Swap.** It also moves toward review item 7's 5.2 V. RFBT = 12 k is inside TI's recommended 10–100 kΩ range [V, datasheet §7.3.2]. The 2.2 k RFBB draws about 0.36 mA of divider current, which doesn't matter at a 0.45 A load [I] |
| J1 | XY-SM06B-GHS-TB (C51940119) | Extended | No Preferred GH or 1.25 mm connector exists | **Replace with wire pads** (3.5) |
| all others | C1, C2/C4/C8, C3, C7, R3/R4, R14, D1 | Basic [V] | — | — |

**Fee impact:**
- As designed: 8 Extended × $3.07 = $24.56.
- After swapping TVS1, D2, R13 and J1: 4 × $3.07 = **$12.28**.
- With F1 also hand-soldered: $9.21.

**VBUS margin with the B5819W** [I]:
- Vout is 5.164 V nominal and about 5.03 V worst case (±1.5 % reference and 1 % resistors).
- B5819W Vf at 0.45 A is about 0.45–0.5 V. This is estimated from the 0.6 V at 1 A rating; confirm against the curve in the datasheet.
- That leaves about 4.53–4.58 V at the XIAO's 5 V pin, against a 4.4 V requirement.
- This is better than the current design's ≈ 4.44 V worst case (review item 7), so the swap improves margin.
- If the Vf curve disagrees, use the SS34 instead. It is Basic, 0.55 V at 3 A, and so lower at 0.45 A, but its footprint is larger.

### 3.2 Hand-soldering instead of paying fees

Each part you hand-fit saves $3.07 plus 35 % duty, about $4.15 [I]. You then buy the part at Digi-Key (U2 $1.71, F1 about $1.24, U3 $0.20 [V]), which shares the shipping of the kit order.

| Part | Ease by hand |
|---|---|
| U2, U3 (SOT-23-6) | Easy with an iron |
| F1 (1812) | Easy |
| TVS1, D2 (SOD) | Easy |
| J1 (GH SMD, 1.25 mm) | Fiddly, but doable |
| L1 (4×4 mm, terminals underneath) | Needs hot air or a hot plate |

That gives row 2 of the table: JLC places only Basic and Preferred parts, and you fit four parts per board. It saves about $12 more than row 3 [I] and adds hand-soldering of the regulator, which is the most important part to get right. **Recommendation:** pay the fee for U2 and L1 (the hot loop matters). Hand-fitting F1 is a reasonable $4 saving if you are already soldering sockets.

### 3.3 Single-sided assembly

The board already is single-sided. All fitted SMD parts are on top, and the bottom carries only the DNP R5, R6, C5, C6 and R12 plus bare pads. Economic requires single-side placement [V]. Keep the new U3 and the test points on **top**, or as bare pads, so this stays true.

### 3.4 Mill-Max sockets: are they the dominant cost?

No, but they come second. For 2 boards, 30 × $0.688 ≈ **$20.60** [I from V], against $24.56 in Extended fees and ≈ $35 in shipping plus duty on a JLC order.

Cheaper but still sound mounting options inside the 10 mm limit:

1. **Socket one board only.** Make the dev board removable and solder the second XIAO's header straight into the carrier (no receptacles). This saves ≈ $10 [I].
   - The trimmed male header through the 1.6–1.75 mm hole is a loose fit for a 0.64 mm square pin. Solder fills it, but it is a big hole for a header pin [I].
   - Stack height is about the flat-solder figure plus the header gap.
2. **Flat-solder the XIAO** to castellation pads. This costs nothing in parts and gives the lowest stack (6.6 mm). It is **blocked until review item 4 is fixed**: use Seeed's Plus SMD land pattern, because the current pads sit about 0.06 mm from the Plus's 1.27 mm-pitch pads.
3. Standard 2.54 mm female headers (Sullins PPTC series) are about 8.5 mm tall [I] and **do not fit** the 9.0 mm design limit once you add 1.6 mm of board and 4.9 mm of XIAO. Do not use them.

### 3.5 J1 → direct-solder wire pads

**Recommended.** It:
- removes one Extended fee and the $0.07 part
- removes the GH housing and crimp or pre-crimped leads (≈ $5 per order) [I]
- **fixes review must-fix item 2**: the mated plug and wire bend stick 3–6 mm past the 28 mm envelope, while pads need only the wire's bend radius

**What you give up:** tool-free disconnect from the harness.

**What it needs:**
- Six pads at 2.0–2.54 mm pitch along the bottom edge, sized for 26–28 AWG.
- Strain relief (glue or tie-down holes).
- Keep the pin order and silk labels.
- The passive-only tests in `tests/test_design.py` still apply. The pads replace J1 pin-for-pin.

## 4. Alternatives to a custom board

**Verdict: no off-the-shelf route meets the full spec in 28×28×10 mm.**

**Geometry** [I]. A 21×17.8 mm XIAO in a 28×28 mm envelope leaves:
- one strip of about 10.2×28 mm
- one strip of about 7×17.8 mm

Under the XIAO is not usable: the README shows less than 1 mm of clearance with a socket gap.

| Candidate | Size (mm) | Fits? | Source |
|---|---|---|---|
| Pololu **D36V6F5** ($5.95): 5.2–50 V in, 600 mA | 13 × 10 × 3 | Fits the 10 mm strip, leaving about 15 × 10 mm. No reverse protection, which Pololu states | [V] [Pololu 3792](https://www.pololu.com/product/3792) |
| Pololu D24V5F5 ($8.95) | 13 × 10 × 3 | Fits, but costs more for less | [V] [Pololu 2843](https://www.pololu.com/product/2843) |
| Pololu D24V10F5 ($12.95) | 18 × 13 × 3.5 | Too big (the README already showed this) | [V] [Pololu 2831](https://www.pololu.com/product/2831) |
| RECOM R-78E / R-78K SIP-3 | about 10 mm tall standing | Too tall. Laid-flat height not verified | [aggregator data](https://my.element14.com/recom-power/r-78k5-0-0-5/dc-dc-converter-5v-0-5a/dp/4171419) |
| TI TPSM365R6 (3–65 V, 600 mA) | 4.5 × 3.5 × 2, QFN | Tiny, but needs a PCB to mount it. Not a no-PCB option | [TI](https://www.ti.com/product/TPSM365R6) |
| MPS MPM3610 | QFN | 21 V maximum input, too little margin above the TVS | [MPS](https://www.monolithicpower.com/jp/products/power-management/power-modules/mpm3610.html) |
| Generic mini-360 (MP2307) | 17 × 11 × 3.8 | Fits physically. 23 V maximum input, trimpot-set output, independent testing found it under-delivers | [Gough Lui](https://goughlui.com/2018/07/04/tested-mini-360-mp2307-based-3a-buck-converter-module/) |
| Generic MP1584 | about 22 × 17 | Too big | — |
| Seeed XIAO power add-on with a 12 V buck | — | None found | — |

**Pololu D36V6F5 on perfboard: the closest fit, and why it still falls short** [I]:
- The remaining 15 × 10 mm of strip must hold:
  - the PPTC (the radial MF-R050 used in the old build guide is far too big, so it would be an SMD 1812 dead-bugged onto perfboard)
  - the reverse diode, the TVS, the backfeed diode, C3 and the harness wires
  - two input resistors and, for the RX buffer, a SOT-23-6 on an adapter board
- On a 2.54 mm grid that is not credible at this size. The earlier perfboard design (`docs/hardware/README.md` §1, §5 G10) needed about 40 × 30 mm for the same reason.
- Without the buffer it might squeeze in, but it would give up the hardware passive-only guarantee (review item 6), carry hand-wired SMD parts on perfboard inside an inverter, and save only about $50 against row 3.

**Honest answer:** the custom carrier is the right call. Within it, the levers are the four BOM swaps and not paying for parts you can fit by hand.

## 5. Recommendation

### No design change: JLCPCB, 4-layer, Economic PCBA, fab 5, assemble 2

- **Order options:**
  - HASL lead-free (not ENIG, to stay on the $2 price)
  - default green and default stackup
  - Economic PCBA, top side only
  - Confirm Parts Placement on
  - DHL
- **Cost:** about **$110 landed** for 2 working boards, including the Digi-Key hand-fit kit. About $125 if all 5 are assembled. JLC's quote will show the real PCB, parts and shipping numbers.
- **Prerequisite:** the review must-fix items still apply before ordering. This route assumes they are done.
- **Lead time:** about 1–2 weeks.

### Cheapest with changes: same JLC route, plus these 4 changes (about $85 landed, saving about $25)

1. **R13 → 12 k (C25752), R14 → 2.2 k (C25879).** Both are Basic. Vout becomes 5.164 V, which also addresses review item 7. Update the README Vout, the bench window and the test that asserts Vout.
2. **D2 → B5819W (C8598, Basic, already used for D1).**
   - Change the footprint from SOD-123W to SOD-123.
   - Confirm the Vf at 0.45 A from the datasheet curve.
   - If that margin fails, use SS34 (C8678, Basic, SMA) instead.
3. **TVS1 → SMAJ18A (C19077538, Preferred Extended, no Economic fee).** Change the footprint from SOD-123F to SMA (DO-214AC).
   - This is the weakest of the four swaps: it saves about $4 landed.
   - It may not fit. In the CPL, D1 sits at y = 15.5 mm, TVS1 at 20.4 mm and R3 at 24.4 mm. An SMA footprint with its pads spans about 6.5 mm, which is about the whole gap between D1's and R3's pads, leaving no courtyard margin. U3 and the test points are landing in the same strip [I].
   - Drop this swap if it doesn't fit cleanly.
4. **J1 → 6 solder pads** with strain relief. This also clears the plug-outside-envelope must-fix (item 2), and the kit drops the GH parts.

**Optional extras:**
- Hand-fit F1 (saves about $4).
- Socket only one of the two XIAOs (saves about $10).
- Once review item 4 fixes the land pattern, flat-solder the second XIAO.

The Extended-part count goes from 8 to 4 (U2, L1, F1, U3). Do not try to remove those four. There is no Basic part that meets their ratings in the space available.

### If you would rather solder than pay

OSH Park 4-layer plus Digi-Key parts, self-assembled, costs about **$58** with no import duty. It is the lowest cash option, but it costs bench time and needs the inductor footprint and 60 V PPTC substitutions checked first (1.4).

## 6. What was not found (check before ordering)

- JLC's ENIG and lead-free HASL upcharges, and DHL rates to the US. Both need the quote page, and the quote page needs an upload.
- JLC landed cost. The rows assume ≈ $20 DHL plus the 35 % prepay. If brokerage of $20–40 also applies (one forum anecdote, cited in 1.3), the JLC rows rise to about $120–130 (as designed) and $95–105 (with changes). The ranking does not change.
- Whether JLC lets you assemble 2 of 5 boards. It is widely reported to, but not stated on a published page.
- Small-quantity prices for PCBWay, Seeed, NextPCB and Elecrow, and their US shipping rates.
- OSH Park's maximum drill size and OSH Stencils' current price.
- The B5819W Vf at 0.45 A, and whether the SRN4018 land pattern matches the FNR4030S footprint.

**Uploading for a quote:** JLC, OSH Park and the others all need the Gerbers uploaded to quote. Whether to upload, and where, is your call. Nothing was uploaded for this report.
