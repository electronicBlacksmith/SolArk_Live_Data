# Rev B-diy pricing: two working boards, landed in the US (2026-10-13, updated 2026-10-14)

Prices are USD, before sales tax.

Sources:
- Digi-Key prices are cut tape at the quantity bought ([V], from the `digikey.com/en/products/result?keywords=<PN>` pages). Digi-Key's first price break is at 10, so buying 2 costs 2 x the single-unit price.
- Fab prices are [V] at the URLs given, except where marked [I].
- C3 (TDK, $1.11) and the harness 10 k ($0.023 at 10) were re-read on 2026-10-14 [V].

No Mill-Max parts are used. The header pins are included.

## Recommendation: route (b), OSH Park bare boards + Digi-Key, everything hand-soldered

**Total ≈ $39.13 + tax.** Route (a) is about $57 at web prices. Route (b) is also the one where every price is published; route (a) needs a live JLC quote.

| Route | Board fab | Assembly | Parts + shipping | Fab shipping + duty | **Total** |
|---|---|---|---|---|---|
| **(b) OSH Park + hand** | $13.49 (3 boards) [V] | you | $25.64 [V] | $0 [V] | **$39.13** |
| (a) JLC Economic places the Basic parts, you fit the rest | ≈ $8 (5 boards) [I] | $11.84 [V fees] | $20.06 [V] | ≈ $17.3 [I] | **≈ $57** |

**Same files for both routes.** The Gerbers, drill file and job file are the same; every DRC minimum is the stricter of the two fabs' published 4-layer values (`test_drc_rules_are_at_least_as_strict_as_both_fabs`).
- Route (a) also uses `fab/carrier_bom_jlc.csv` and `fab/carrier_cpl_jlc.csv`. They list only the Basic parts JLC places.
- Check the CPL rotations in JLC's placement preview before paying (OPEN-ITEMS O6).

## Route (b) detail

### OSH Park 4-layer prototype

Source: https://docs.oshpark.com/services/four-layer/ [V].
- Price: $10 per sq in for 3 copies.
- Board: 29 x 30 mm = 870 mm² = 1.349 sq in, so **$13.49 for 3 boards** (2 to build, 1 spare).
- Shipping: USPS First Class is free; Priority is $6.70-7.35 (https://docs.oshpark.com/submitting-orders/shipping-information/) [V].
- Lead time: ships in 9-14 calendar days.
- Finish: ENIG, which is good for hand soldering.
- The design meets OSH Park's 4-layer rules (10 mil drill, 4 mil ring, 5/5 mil trace/space, 15 mil to edge, 10 mil from plated drill to inner copper) and JLC's stricter ones (0.15 mm PTH and via ring, 0.15 mm pad to pad, 0.3 mm PTH hole to copper, 0.45 mm pad hole to hole). This is enforced by `test_drc_rules_are_at_least_as_strict_as_both_fabs` and DRC.
- Upload `fab/carrier_gerbers.zip`. Its zones are already filled.

### Digi-Key order for 2 boards (`fab/carrier_bom_digikey.csv`)

| Item | DK PN | Buy | Unit | Ext |
|---|---|---|---|---|
| U2 LMR51610YDBVR | 296-LMR51610YDBVRCT-ND | 2 | 1.71 | 3.42 |
| U3 SN74LVC2G17DBVR | 296-SN74LVC2G17DBVRCT-ND | 2 | 0.20 | 0.40 |
| L1 SRP4020TA-100M | SRP4020TA-100MCT-ND | 2 | 1.07 | 2.14 |
| F1 MF-MSMF050/60X-2 | 118-MF-MSMF050/60X-2CT-ND | 2 | 0.91 | 1.82 |
| TVS1 SMF18A | F5820CT-ND | 2 | 0.57 | 1.14 |
| D1 B5819W-TP | B5819W-TPMSCT-ND | 2 | 0.28 | 0.56 |
| D2 PMEG4030ER | 1727-5313-1-ND | 2 | 0.59 | 1.18 |
| R13 20.5k 0.1 % | P20.5KDBCT-ND | 2 | 0.11 | 0.22 |
| R14 3.83k 0.1 % | P3.83KDBCT-ND | 2 | 0.11 | 0.22 |
| C1 10 µF 50 V 1206 | 13-CC1206KKX5R9BB106CT-ND | 2 | 0.75 | 1.50 |
| C3 100 µF 6.3 V 1206, TDK C3216X5R0J107M160AB | 445-6008-1-ND | 2 | 1.11 | 2.22 |
| C7 22 µF 25 V 1206 | 587-3246-1-ND | 2 | 0.45 | 0.90 |
| R3/R4/R7/R8 1k 0603 (need 8) | 311-1.00KHRCT-ND | 10 | 0.025 | 0.25 |
| R5/R6 100k 0603 (need 4) | 311-100KHRCT-ND | 10 | 0.025 | 0.25 |
| C2/C4/C8/C9 100 nF 0603 (need 8) | 311-1344-1-ND | 10 | 0.080 | 0.80 |
| Header pins PRPC040SAAN-RC, 40-pin strip | S1011EC-40-ND | 2 | 1.23 | 2.46 |
| Harness plug PPTC061LFBN-RC (6-way female) | S7004-ND | 2 | 0.47 | 0.94 |
| **Harness series 10 k, Stackpole CF18JT10K0 (need 4, required)** | CF18JT10K0CT-ND | 10 | 0.023 | 0.23 |
| **Parts subtotal** | | | | **20.65** |
| USPS Ground Advantage (https://www.digikey.com/en/help-support/delivery-information/delivery-time-and-cost) | | | | 4.99 |
| **Digi-Key landed** | | | | **25.64** |

The harness 10 k resistors are **required**, not optional: Board B has no ESD diodes, and that is acceptable only with these 10 k in series at the dongle end of each tap wire (2 per board, 4 for two boards; 10 cost less than 4 at Digi-Key's price break). Stock 261,497, $0.10 each at 1, $0.023 at 10 ([V] 2026-10-14, https://www.digikey.com/en/products/result?keywords=CF18JT10K0).

Header pin count:
- Each board needs 14 pins for the XIAO and 6 pins on the J1 wires.
- Two boards need exactly 40 pins, one full strip. The second strip ($1.23) is spare stock for mistakes.

Optional spares (+$0.40): 1 x U3 and 1 x R13/R14. These are the easiest to lose or mis-place.

**Route (b) total: $13.49 + $25.64 = $39.13 + sales tax.**

There is no JLCONE adjustment for route (b), since JLC is not used.

## Route (a) detail (web price)

### JLC fees

Source: https://jlcpcb.com/help/article/40-pcb-assembly-price [V].

The brief allowed Basic and Preferred-Extended parts. All the other parts (U2 C22427220, U3 C10429, L1 C189929, TVS1 C409420 and D2 C389355) are plain Extended, not Preferred, per the JLC parts API [V]. Placing them would cost $3.07 each in feeder fees, so they are hand-fitted. The 0.1 % resistors are not stocked at JLC.

JLC places 13 parts per board. All are Basic, so there are no extended-feeder fees:
- D1 (CJ B5819W, C8598)
- C1 and C3 (Samsung)
- C2, C4, C8, C9
- R3-R8 (Uniroyal)

| Item | Basis | $ |
|---|---|---|
| 4-layer bare PCB, 5 pcs | **No 4-layer price is published.** Needs a live quote. | ≈ 8 [I] |
| Economic setup | [V] | 8.18 |
| Stencil | [V] | 1.53 |
| Confirm parts placement | [V] | 0.45 |
| SMT joints | 26 joints/board x 2 boards x $0.0016 [V] | 0.08 |
| Pre-reflow | 52 x $0.016 [V] (counted to be conservative) | 0.83 |
| Basic parts, including LCSC minimum order quantities | [I] | ≈ 0.77 |
| **PCBA subtotal** | | **11.84** |
| US DDP duty | 35 % PCB, 35 % SMT, 90 % stencil (https://jlcpcb.com/news/logistics-update-us-china-tariff) [V], applied to the [I] PCB price | ≈ 7.8 |
| Shipping | No published table; forum reports put it at $8-11 [I] | ≈ 9.5 |

Other conditions:
- Economic PCBA allows 4-layer boards and 2-50 pcs [V].
- Assembling 2 of 5 boards is allowed by JLC's T&C wording [I].

### Digi-Key hand kit for route (a)

This is the hand-fit part of the route (b) list:

| Items | $ |
|---|---|
| U2, U3, L1, F1, TVS1, D2, R13, R14, C7 | 11.44 |
| 2 header strips | 2.46 |
| 2 harness plugs | 0.94 |
| 10 harness 10 k resistors (4 needed) | 0.23 |
| **Subtotal** | **$15.07** |
| Shipping | $4.99 |
| **Digi-Key landed** | **$20.06** |

**Route (a) web total ≈ $8 + 11.84 + 7.8 + 9.5 + 20.06 ≈ $57 + tax.** The board price, duty and shipping lines are [I].

### JLCONE adjustment (separate, unverified for this order)

Source: https://jlcpcb.com/news/jlcpcb-jlcone-desktop-app [V].

JLC's published terms for orders through the JLCONE desktop app:
- "a random discount between $1 and $20 will be automatically applied to your order total". It is a limited-time event.
- A "$104 coupon package" is credited to the account. Only one coupon applies per order, and it stacks with the random discount.
- The "$2 PCB deal" and "special shipping rates" are now JLCONE-only. The article does not say whether the $2 deal covers 4-layer boards. Only an undated LCSC page claims 4-layer 50 x 50 mm for $2 [I].

The possible effect on route (a) is **−$1 to about −$28**:
- −$1 to −$20 from the random discount.
- About −$6 PCB and −$2 duty if the $2 deal covers 4-layer.
- An unknown amount from a coupon.

That puts route (a) at about **$29-56**. Even at its best it beats route (b) only if every unverified discount lands. It still leaves 9 SMD parts per board to hand-solder, against 22 for route (b).

A JLC bare 4-layer board through JLCONE could also undercut OSH Park's $13.49 in route (b), but there is no published price to verify that [I].
