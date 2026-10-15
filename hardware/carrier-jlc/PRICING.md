# Carrier Rev B (JLC variant): landed cost estimate

These are estimates read from JLC's published pages and parts API on 2026-10-13. They are **not a
quote**: nothing was uploaded to any site. The parent session gets the real quote, with the user's
approval.

Route:
- JLCPCB 4-layer, 27 x 27 mm, 1.6 mm, 5 PCBs.
- Economic PCBA, top side, assembling either 2 or all 5.
- DHL to the US with DDP.

Sources [V], read today:
- PCBA fees: https://jlcpcb.com/help/article/40-pcb-assembly-price ($8.18 Economic setup, $1.53 stencil, $3.07 per Extended part, $0.0016 per joint, $0.45 "confirm parts placement").
- Preferred parts pay no feeder fee in Economic: https://jlcpcb.com/help/article/PCB-assembly-faqs
- Economic PCBA allows 4 layers and 2-50 pcs: https://jlcpcb.com/capabilities/pcb-assembly-capabilities
- 4-layer PCB price: "4-layer PCBs (10x10cm) start at just $7", from https://jlcpcb.com/features/prototype-pcb-way. The quantity is not stated; 5 pcs is assumed [I].
- DDP prepaid duty: PCB 35 %, SMT 35 %, stencil 90 % (https://jlcpcb.com/news/logistics-update-us-china-tariff, March 17 2026 entry). US personal orders under $800 ship DDP (https://jlcpcb.com/help/article/us-tariff-policy-faq).
- Parts: JLC parts API (`selectSmtComponentList`), which gives the unit-price tier, minimum order quantity (leastPatchNumber) and attrition (lossNumber).
  - Order quantity per part = max(needed + attrition, minimum order).
  - The per-part list is in CHANGES-revB.md.
- Hand-fit kit, Digi-Key (`design.KIT`, README "Hand-fit kit"):
  - Header pins: S1011EC-40-ND (Sullins PRPC040SAAN-RC), $1.23, 45,650 in stock (read 2026-10-13). One 40-pin strip covers 2 boards (28 pins); two strips cover 5 boards.
  - Kapton shim tape: 4393-PPTA-1/2-ND (Bertech PPTA-1/2, 1/2 in x 36 yd, 0.064 mm), $13.95, 660 in stock (read 2026-10-14, https://www.digikey.com/en/products/detail/bertech/PPTA-1-2/14670716). One roll covers every board.
  - Harness 10 k: CF14JT10K0CT-ND (Stackpole CF14JT10K0, 1/4 W axial), $0.10 each at 1, $0.027 each at 10, 571,559 in stock (read 2026-10-14, https://www.digikey.com/en/products/detail/stackpole-electronics-inc/CF14JT10K0/1741265). 2 per board; 10 cost less than 4, so buy 10 for either quantity.

## Extended feeder fees

7 parts x $3.07 = **$21.49**: U2, L1, F1, D2, U3, R13 and R14.
- TVS1, D3 and D4 are Preferred, so they pay no fee.
- The other 9 lines are Basic, so they pay no fee either.

Two fees would be saveable, but are kept on purpose:
- R13/R14 (precision divider, $6.14). A Basic 1 % pair fails the VBUS window (CHANGES-revB.md).
- U3 (the buffer, $3.07). There is no Basic or Preferred 74LVC2G17-class part.

## Web price

| Item | 2 assembled | All 5 assembled | Basis |
|---|---|---|---|
| PCB, 5 pcs, 4-layer | 7.00 | 7.00 | [V] "from" price. The real quote may be higher. |
| Economic setup | 8.18 | 8.18 | [V] |
| Stencil | 1.53 | 1.53 | [V] |
| Extended feeder fees (7) | 21.49 | 21.49 | [V] |
| SMT joints (112 / 280 x $0.0016) | 0.18 | 0.45 | [V] rate. Joints counted from the footprints. |
| Confirm parts placement | 0.45 | 0.45 | [V] |
| LCSC parts (minimums and attrition included) | 15.22 | 21.25 | [V] API price tiers |
| **JLC subtotal** | **54.05** | **60.35** | |
| DDP duty (35 % PCB + 35 % SMT + 90 % stencil) | 19.76 | 21.97 | [V] rates. The SMT base = setup + fees + joints + placement + parts [I]. |
| DHL shipping | ~20 | ~20 | [I] Typical; not quoted. |
| Header pins (Digi-Key, 1 / 2 strips) | 1.23 | 2.46 | [V] Digi-Key shipping is not included. |
| Kapton tape (Digi-Key, 1 roll) | 13.95 | 13.95 | [V] |
| Harness 10 k (Digi-Key, 10 pcs) | 0.27 | 0.27 | [V] |
| **Landed total** | **~109.26** | **~119.00** | |
| Per working board | ~54.63 | ~23.80 | |

Assembling all 5 costs only about **$9.74 more** than assembling 2. Most of the cost is per-order
(setup, feeder fees, shipping), and most parts have minimum order quantities above 2 sets anyway.

Possible discounts [I]. These are not counted in the totals:
- New-customer coupons (https://jlcpcb.com/help/article/new-customer-coupons [V]): SMT $10, PCB $6, stencil $7 and shipping $10.
- Eligibility, and whether those coupons stack on one order, are unverified. The page says "multiple coupons cannot be combined on a single order".
- So the realistic saving is one coupon, about $6-10.

## JLCONE adjustment (separate, unverified)

Source: https://jlcpcb.com/help/article/jlcone-desktop-app [V]. That page states:
- A $104 coupon pack on install, with no PCBA terms given. The same page family also quotes $123, so the figures conflict.
- A random "$1-$20 off your order total".
- One promo coupon may be stacked with the random discount.
- "Selected shipping rates and routes" are JLCONE-only.
- The $2 PCB deal is JLCONE-only. It is likely 1-2 layer only, so it probably does not apply to this 4-layer board [I].
- No PCBA price difference is stated.

**Adjustment: between $0 and about $30 off [I].** That is the random $1-20 plus at most one coupon,
whose PCBA eligibility is unknown. This cannot be verified without installing the app and logging in,
which the brief forbids. Treat the web price above as the planning number.
