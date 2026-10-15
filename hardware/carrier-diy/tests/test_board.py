"""Invariants of the generated board, footprints and fab outputs.

These read the generator constants and the files `scripts/build.sh` writes, so run
the build first. Run: pytest hardware/carrier-diy/tests.
"""

from __future__ import annotations

import csv
import glob
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import gen_lib as G
from design import BOARD, KIT, MAX_OUTLINE, PARTS, SOURCE
from sexp import find, parse

FAB = os.path.join(ROOT, "fab")


def _read(path: str) -> str:
    with open(path) as fh:
        return fh.read()


def _fitted(ref: str) -> bool:
    _, _, _, _, dnp, in_bom, _, _ = PARTS[ref]
    return in_bom and not dnp


def _edge_bbox() -> tuple[float, float, float, float]:
    pcb = parse(_read(os.path.join(ROOT, "carrier.kicad_pcb")))
    xs, ys = [], []
    for kind in ("gr_line", "gr_rect"):
        for seg in find(pcb, kind):
            if find(seg, "layer")[0][1] != "Edge.Cuts":
                continue
            for key in ("start", "end"):
                p = find(seg, key)[0]
                xs.append(float(p[1]))
                ys.append(float(p[2]))
    return min(xs), min(ys), max(xs), max(ys)


def test_outline_within_the_user_limit() -> None:
    x0, y0, x1, y1 = _edge_bbox()
    w, h = round(x1 - x0, 3), round(y1 - y0, 3)
    assert (w, h) == (BOARD[2], BOARD[3])
    assert sorted((w, h)) <= sorted(MAX_OUTLINE)


def test_xiao_hole_fits_a_0p64_square_header_pin_at_every_tolerance() -> None:
    diag = G.PIN_SQ_MAX * math.sqrt(2)
    hole_min = G.THT_DRILL + G.PTH_TOL[1]
    hole_max = G.THT_DRILL + G.PTH_TOL[0]
    assert hole_min >= diag + 0.05, (hole_min, diag)  # pin always enters
    assert hole_max <= G.PIN_HOLE_MAX  # not sloppier than the header maker allows
    for pad in (G.THT_PAD_F, G.THT_PAD_B):
        assert (pad - G.THT_DRILL) / 2 >= 0.15  # designed ring: JLC 0.15 min
        assert (pad - hole_max) / 2 >= 0.1016  # worst-case ring: OSH Park 4 mil


def test_top_pad_clears_the_plus_castellations_when_flush() -> None:
    # Seeed Plus SMD land pattern pads 15-23 sit between the main pins at the edge.
    s = _read(os.path.join(ROOT, "lib", "seeed", "XIAO-ESP32-S3-Plus-SMD.kicad_mod"))
    pads = re.findall(
        r'\(pad "(\d+)".*?\(at ([-\d.]+) ([-\d.]+)(?: [-\d.]+)?\).*?\(size ([\d.]+) ([\d.]+)\)',
        s,
        re.S,
    )
    r_top = G.THT_PAD_F / 2
    worst = 99.0
    for num, x, y, sx, sy in pads:
        if not 15 <= int(num) <= 23:
            continue
        x, y, sx, sy = float(x), float(y), float(sx), float(sy)
        # pads are rotated 90/270: size x is along y. Only the part on the XIAO
        # (inside its edge at |y| = 8.9) can touch the carrier.
        hx, y_in = sy / 2, abs(y) - sx / 2
        for n in range(1, 15):
            px, py = G.pin_xy(n)
            if (py < 0) != (y < 0):
                continue
            dx = max(abs(px - x) - hx, 0.0)
            dy = max(y_in - abs(py), 0.0)
            worst = min(worst, math.hypot(dx, dy) - r_top)
    assert worst >= 0.15, worst


def test_xiao_footprint_has_no_castellation_pads() -> None:
    fp = _read(os.path.join(ROOT, "lib", "carrier.pretty", G.XIAO_FP + ".kicad_mod"))
    assert "Socket" not in G.XIAO_FP
    for m in re.finditer(r'\(pad "\d+" (\w+)[^\n]*', fp):
        kind, line = m.group(1), m.group(0)
        assert kind == "thru_hole" or '"B.Cu"' in line, line  # B.Cu = solder-side ring


def test_jlc_bom_and_cpl_list_exactly_the_jlc_placed_parts() -> None:
    want = {r for r in PARTS if _fitted(r) and SOURCE[r]["fit"] == "jlc"}
    with open(os.path.join(FAB, "carrier_bom_jlc.csv")) as fh:
        bom = {d for row in csv.DictReader(fh) for d in row["Designator"].split(",")}
    with open(os.path.join(FAB, "carrier_cpl_jlc.csv")) as fh:
        cpl = {row["Designator"] for row in csv.DictReader(fh)}
    assert bom == want and cpl == want


def test_digikey_bom_lists_every_fitted_part() -> None:
    with open(os.path.join(FAB, "carrier_bom_digikey.csv")) as fh:
        rows = list(csv.DictReader(fh))
    parts = [row for row in rows if row["Route (a) fit"] != "kit"]
    refs = {d for row in parts for d in row["Designators"].split(",")}
    assert refs == {r for r in PARTS if _fitted(r)}
    assert all(row["Digi-Key PN"] for row in rows)
    kit = {row["Digi-Key PN"] for row in rows if row["Route (a) fit"] == "kit"}
    assert kit == {k["dk"] for k in KIT}  # header pins and harness plug are bought too
    row = next(r for r in rows if r["Designators"] == "C3")
    assert row["MPN"].startswith("TDK C3216X5R0J107M160AB") and row["Digi-Key PN"] == "445-6008-1-ND"


def test_c3_is_the_active_tdk_part() -> None:
    # JMK316BJ107ML-T is "Not For New Designs" at Digi-Key (2026-10-14).
    assert SOURCE["C3"]["dk"] == "445-6008-1-ND"
    assert SOURCE["C3"]["mpn"].startswith("TDK C3216X5R0J107M160AB")
    assert "JMK316" not in SOURCE["C3"]["mpn"]
    assert PARTS["C3"][2] == "Capacitor_SMD:C_1206_3216Metric"


def test_kit_includes_the_harness_10k_series_resistors() -> None:
    # Board B has no D3/D4 ESD diodes; that is acceptable only with these fitted.
    r = [k for k in KIT if k["dk"] == "CF18JT10K0CT-ND"]
    assert len(r) == 1 and r[0]["qty"] == "2" and "10k" in r[0]["use"].replace(" ", "")
    with open(os.path.join(FAB, "carrier_bom_digikey.csv")) as fh:
        assert any(row["Digi-Key PN"] == "CF18JT10K0CT-ND" for row in csv.DictReader(fh))


def test_build_fails_on_errors() -> None:
    build = _read(os.path.join(ROOT, "scripts", "build.sh"))
    fab = _read(os.path.join(ROOT, "scripts", "export_fab.sh"))
    assert "|| true" not in build
    assert re.search(r"sch erc[^\n]*--exit-code-violations", fab)
    assert re.search(r"pcb drc[^\n]*--exit-code-violations", fab)


def test_job_file_declares_the_jlc_7628_stackup() -> None:
    job = json.loads(_read(glob.glob(os.path.join(FAB, "gerbers", "*.gbrjob"))[0]))
    cu = [L["Thickness"] for L in job["MaterialStackup"] if L["Type"] == "Copper"]
    assert cu == [0.035, 0.0152, 0.0152, 0.035]
    diel = [L["Thickness"] for L in job["MaterialStackup"] if L["Type"] == "Dielectric"]
    assert diel == [0.2104, 1.065, 0.2104]


def test_reports_are_clean() -> None:
    erc = _read(os.path.join(FAB, "erc.rpt"))
    drc = _read(os.path.join(FAB, "drc.rpt"))
    assert "** ERC messages: 0" in erc and "Errors 0" in erc
    assert "** Found 0 DRC violations **" in drc
    assert "** Found 0 unconnected pads **" in drc


# Datasheet land patterns (read 2026-10-13, URLs in CHANGES-revB.md):
# ref: (pad length along the part axis, pad width across, pad centre-to-centre), mm.
LAND = {
    "L1": (1.5, 2.4, 3.7),  # Bourns SRP4020TA: 5.2 overall, 2.2 gap, 2.4 tall
    "F1": (1.68, 2.95, 4.78),  # Bourns MF-MSMF: 1.68 x 2.95 pads, 3.1 inner gap
    "TVS1": (1.3, 1.4, 2.9),  # Littelfuse SMF mounting pad layout: 1.3 x 1.4, 1.6 gap
    "D1": (0.91, 1.22, 3.27),  # MCC B5819W SOD-123 suggested layout: 2.36 gap
    "D2": (1.2, 1.2, 2.8),  # Nexperia CFP3 (SOD123W) solder land
    "U3": (1.1, 0.6, 2.6),  # TI DBV0006A: 1.1 x 0.6, rows 2.6 apart
}


def _fp_pads(fpid: str) -> list[tuple[float, float, float, float]]:
    lib, name = fpid.split(":")
    if lib == "carrier":
        path = os.path.join(ROOT, "lib", "carrier.pretty", name + ".kicad_mod")
    else:
        base = os.environ.get(
            "KICAD_FOOTPRINT_DIR",
            "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints",
        )
        path = os.path.join(base, lib + ".pretty", name + ".kicad_mod")
    fp = parse(_read(path))
    out = []
    for pad in find(fp, "pad"):
        at, size = find(pad, "at")[0], find(pad, "size")[0]
        out.append((float(at[1]), float(at[2]), float(size[1]), float(size[2])))
    return out


def test_land_patterns_match_the_datasheets() -> None:
    for ref, (length, width, pitch) in LAND.items():
        pads = _fp_pads(PARTS[ref][2])
        xs = sorted({round(p[0], 3) for p in pads})
        assert abs((xs[-1] - xs[0]) - pitch) <= 0.05, (ref, xs)
        for _, _, sx, sy in pads:
            assert abs(sx - length) <= 0.05 and abs(sy - width) <= 0.05, (ref, sx, sy)


# Published 4-layer minimums, mm, read 2026-10-14. The same files go to either fab, so
# every DRC minimum must be at least the stricter of the two. KiCad's annular-width rule
# covers vias and PTH pads alike, and its hole-clearance rule covers via and pad holes.
FAB_MINIMUMS = {
    # https://jlcpcb.com/capabilities/pcb-capabilities
    "jlc": {
        "min_clearance": 0.15,  # trace spacing 0.09; SMD pad to pad (different nets) 0.15
        "min_track_width": 0.09,
        "min_via_annular_width": 0.15,  # PTH ring, 1 oz: absolute minimum 0.15 (0.20 recommended)
        "min_via_diameter": 0.25,
        "min_through_hole_diameter": 0.15,
        "min_hole_clearance": 0.30,  # inner-layer PTH hole to copper 0.3 (PTH to track 0.28)
        "min_hole_to_hole": 0.45,  # pad hole to hole 0.45 (via 0.2)
        "min_copper_edge_clearance": 0.20,  # routed edge
    },
    # https://docs.oshpark.com/services/four-layer/
    "osh": {
        "min_clearance": 0.127,  # 5 mil
        "min_track_width": 0.127,  # 5 mil
        "min_via_annular_width": 0.1016,  # 4 mil
        "min_via_diameter": 0.254 + 2 * 0.1016,  # 10 mil drill + 2 x 4 mil ring
        "min_through_hole_diameter": 0.254,  # 10 mil
        "min_hole_clearance": 0.254,  # drill to inner copper 10 mil
        "min_hole_to_hole": 0.127,  # 5 mil recommended
        "min_copper_edge_clearance": 0.381,  # 15 mil
    },
}


def test_drc_rules_are_at_least_as_strict_as_both_fabs() -> None:
    pro = json.loads(_read(os.path.join(ROOT, "carrier.kicad_pro")))
    rules = pro["board"]["design_settings"]["rules"]
    for fab, need in FAB_MINIMUMS.items():
        for key, val in need.items():
            assert rules[key] >= val - 1e-9, (fab, key, rules[key], val)
