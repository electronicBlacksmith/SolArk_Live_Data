"""Write the route-(a) JLC BOM/CPL and the route-(b) Digi-Key BOM.

Usage: python3 -I scripts/export_bom.py <kicad_bom.csv> <kicad_pos_front.csv> <fab dir>

- carrier_bom_jlc.csv / carrier_cpl_jlc.csv: only the parts JLC Economic places
  (design.SOURCE[ref]["fit"] == "jlc": Basic or Preferred-Extended, no feeder fee).
  CPL rotations are KiCad's; see README "JLC rotation check" before ordering.
- carrier_bom_digikey.csv: every fitted part (route b, or the hand-fit kit for route a).
"""

from __future__ import annotations

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from design import KIT, PARTS, SOURCE


def fitted(ref: str) -> bool:
    _, _, _, _, dnp, in_bom, _, _ = PARTS[ref]
    return in_bom and not dnp


def jlc(ref: str) -> bool:
    return fitted(ref) and SOURCE[ref]["fit"] == "jlc"


def main(bom_in: str, pos_in: str, out: str) -> None:
    with open(bom_in) as fh:
        rows = list(csv.DictReader(fh))
    with open(os.path.join(out, "carrier_bom_jlc.csv"), "w", newline="") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_ALL)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for r in rows:
            refs = [d for d in r["Designator"].split(",") if jlc(d)]
            if refs:
                w.writerow([r["Comment"], ",".join(refs), r["Footprint"], r["LCSC Part #"]])

    with open(pos_in) as fh:
        pos = list(csv.DictReader(fh))
    with open(os.path.join(out, "carrier_cpl_jlc.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in pos:
            if jlc(r["Ref"]):
                side = "Top" if r["Side"] == "top" else "Bottom"
                rot = "%g" % (float(r["Rot"]) % 360)
                w.writerow([r["Ref"], r["PosX"] + "mm", r["PosY"] + "mm", side, rot])

    groups: dict[str, list[str]] = {}
    for ref in PARTS:
        if fitted(ref):
            groups.setdefault(SOURCE[ref]["dk"], []).append(ref)
    with open(os.path.join(out, "carrier_bom_digikey.csv"), "w", newline="") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_ALL)
        w.writerow(
            ["Digi-Key PN", "MPN", "Qty per board", "Designators", "Value", "Footprint",
             "Route (a) fit"]
        )
        for dk, refs in groups.items():
            p = PARTS[refs[0]]
            w.writerow(
                [dk, SOURCE[refs[0]]["mpn"], len(refs), ",".join(refs), p[1],
                 p[2].split(":")[1], SOURCE[refs[0]]["fit"]]
            )
        for k in KIT:
            w.writerow([k["dk"], k["mpn"], k["qty"], "-", k["use"], "-", "kit"])


if __name__ == "__main__":
    main(*sys.argv[1:4])
