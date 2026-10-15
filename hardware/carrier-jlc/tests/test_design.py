"""Invariants of the carrier netlist (design.py). Run: pytest hardware/carrier-jlc/tests."""

from __future__ import annotations

import math
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import design as D  # noqa: E402
from design import PARTS  # noqa: E402

TAPS = {"TAP_RESP", "TAP_REQ"}
POWER = {"GND", "+3V3", "+5V_X", "+5V_BUCK", "+12V_IN", "+12V_F", "+12V_P"}


def populated(ref: str) -> bool:
    _, _, _, _, dnp, _, _, _ = PARTS[ref]
    return not dnp


def nets_of(ref: str) -> set[str]:
    return {n for n in PARTS[ref][6].values() if n}


def gpio_nets() -> set[str]:
    return nets_of("U1") - POWER


def walk(start: set[str], use_buffer: bool) -> set[str]:
    """Nets reachable from `start` through every part (DNP or not, worst case).

    Power nets are terminals (a pull-up to +3V3 does not let a signal reach
    every other +3V3 pin). U1 and the harness pads J1 are endpoints and are
    not crossed. A buffer
    only conducts from its input pin to its output pin, and only when
    `use_buffer` is set.
    """
    reach, frontier = set(start), list(start)
    while frontier:
        net = frontier.pop()
        if net in POWER:
            continue
        for ref, part in PARTS.items():
            conns = part[6]
            if ref in ("U1", "J1"):
                continue
            if ref in D.BUFFERS:
                if not use_buffer:
                    continue
                for a, y in D.BUFFERS[ref].items():
                    if conns[a] == net and conns[y] not in reach:
                        reach.add(conns[y])
                        frontier.append(conns[y])
                continue
            if net not in conns.values():
                continue
            for other in nets_of(ref) - reach:
                reach.add(other)
                frontier.append(other)
    return reach


def test_every_assembled_part_has_an_lcsc_number_and_jlc_status() -> None:
    for ref, (_, _, _, lcsc, dnp, in_bom, _, _) in PARTS.items():
        if in_bom and not dnp:
            assert lcsc.startswith("C"), ref
            assert D.JLC_STATUS[lcsc] in {"Basic", "Preferred", "Extended"}, ref


def test_no_dnp_parts_left() -> None:
    # Rev B has no "unpopulated but present" provisions: every footprint is fitted.
    assert [r for r, p in PARTS.items() if p[4]] == []


def test_tap_nets_touch_only_harness_esd_and_series_resistors() -> None:
    allowed = {
        ("J1", "4"),
        ("J1", "5"),
        ("R3", "1"),
        ("R4", "1"),
        ("D3", "1"),
        ("D4", "1"),
    }
    seen = set()
    for ref, (_, _, _, _, _, _, conns, _) in PARTS.items():
        for pin, net in conns.items():
            if net in TAPS:
                assert (ref, pin) in allowed, (ref, pin)
                seen.add((ref, pin))
    assert seen == allowed
    for d in ("D3", "D4"):
        assert PARTS[d][6]["2"] == "GND"
        assert PARTS[d][3] == "C7420372"  # bidirectional 5 V ESD, VBR >= 5.6 V


def test_series_resistors_are_populated_1k() -> None:
    for ref in ("R3", "R4", "R7", "R8"):
        assert populated(ref) and PARTS[ref][1] == "1k", ref


def test_buffer_is_the_only_path_from_tap_to_gpio() -> None:
    # Without the buffer, no tap reaches any XIAO GPIO.
    assert not (walk(TAPS, use_buffer=False) & gpio_nets())
    # With the buffer, both taps reach exactly their RX pins.
    assert walk({"TAP_RESP"}, use_buffer=True) & gpio_nets() == {"RX_RESP"}
    assert walk({"TAP_REQ"}, use_buffer=True) & gpio_nets() == {"RX_REQ"}


def test_no_gpio_can_reach_a_tap() -> None:
    # The buffer is one-way, so from the XIAO side the taps are unreachable
    # even with every footprint fitted (CLAUDE.md rule 6: passive only).
    assert not (walk(gpio_nets(), use_buffer=True) & TAPS)


def test_buffer_part_and_pinout() -> None:
    lib, value, fp, lcsc, dnp, in_bom, conns, _ = PARTS["U3"]
    assert value == "74LVC2G17GW" and lcsc == "C80500" and not dnp and in_bom
    # Nexperia 74LVC2G17 Table 3: 1 1A, 2 GND, 3 2A, 4 2Y, 5 VCC, 6 1Y
    assert conns == {
        "1": "BUF_IN_RESP",
        "2": "GND",
        "3": "BUF_IN_REQ",
        "4": "BUF_OUT_REQ",
        "5": "+3V3",
        "6": "BUF_OUT_RESP",
    }
    assert D.BUFFERS == {"U3": {"1": "6", "3": "4"}}


def test_no_tx_or_proxy_provision() -> None:
    nets = {n for r in PARTS for n in nets_of(r)}
    assert not {n for n in nets if "PROXY" in n or "TX" in n}
    assert not [r for r in PARTS if r.startswith(("JP", "TP"))]


def test_harness_pinout() -> None:
    assert PARTS["J1"][6] == {
        "1": "+12V_IN",
        "2": "GND",
        "3": "GND",
        "4": "TAP_RESP",
        "5": "TAP_REQ",
    }


def _ohms(v: str) -> float:
    n = v.split()[0]
    return float(n[:-1]) * 1000 if n.endswith("k") else float(n)


def _tol(v: str) -> tuple[float, float]:
    pct = re.search(r"([\d.]+)%", v)
    ppm = re.search(r"(\d+)ppm", v)
    assert pct and ppm, v
    return float(pct.group(1)) / 100, float(ppm.group(1)) * 1e-6


def vout_window() -> tuple[float, float, float]:
    top, bot = PARTS["R13"][1], PARTS["R14"][1]
    k = _ohms(top) / _ohms(bot)
    (tt, tct), (tb, tcb) = _tol(top), _tol(bot)
    dt = D.BUCK["temp_span_k"]
    hi = k * (1 + tt + tct * dt) / (1 - tb - tcb * dt)
    lo = k * (1 - tt - tct * dt) / (1 + tb + tcb * dt)
    b = D.BUCK
    vmax = b["vfb_nom"] * (1 + b["pfm_hi"]) * (1 + hi)
    vmin = b["vfb_min"] * (1 + lo)
    return k, vmin, vmax


def test_feedback_divider_worst_case_window() -> None:
    k, vmin, vmax = vout_window()
    assert 4.95 <= 0.8 * (1 + k) <= 5.15
    # Ceiling applied before D2 (stricter than at the XIAO pin).
    assert vmax <= D.XIAO_5V["vmax"], vmax
    # Floor after D2 at its rated-current forward-voltage maximum.
    assert vmin - D.XIAO_5V["d2_vf_max"] >= D.XIAO_5V["vmin"], vmin


def test_outline_within_limit() -> None:
    w, h = D.BOARD_W, D.BOARD_H
    assert w <= D.OUTLINE_MAX[0] and h <= D.OUTLINE_MAX[1]
    pcb = os.path.join(ROOT, "carrier.kicad_pcb")
    if os.path.exists(pcb):
        xs, ys = [], []
        for chunk in open(pcb).read().split("(gr_line")[1:]:
            chunk = chunk.split("(gr_")[0].split("(footprint")[0]
            if '(layer "Edge.Cuts")' not in chunk:
                continue
            for x, y in re.findall(r"\((?:start|end) ([\d.]+) ([\d.]+)\)", chunk):
                xs.append(float(x))
                ys.append(float(y))
        assert xs, "no Edge.Cuts outline"
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        assert math.isclose(x1 - x0, w) and math.isclose(y1 - y0, h)


def _pads(fp_name: str) -> list[str]:
    path = os.path.join(ROOT, "lib", "carrier.pretty", fp_name + ".kicad_mod")
    return re.findall(r"\(pad .*", open(path).read())


def test_xiao_header_holes_fit_square_pins_with_jlc_tolerance() -> None:
    drill, pad = D.XIAO_PIN_DRILL, D.XIAO_PIN_PAD
    lo, hi = drill - D.JLC_PTH_TOL[1], drill + D.JLC_PTH_TOL[0]
    assert lo >= D.HEADER["rec_hole"]  # Sullins recommended hole, at JLC's minimum
    assert lo - D.HEADER["post"] * math.sqrt(2) >= 0.1  # pin diagonal clearance
    assert (pad - hi) / 2 >= D.JLC_MIN_RING
    assert D.HEADER["pitch"] - pad >= 0.2 + 2 * 0.15  # one 0.2 track between pins
    fp = PARTS["U1"][2].split(":")[1]
    pads = _pads(fp)
    assert len(pads) == 14
    for p in pads:
        assert "thru_hole" in p and f"(drill {drill:g})" in p, p
        assert f"(size {pad:g} {pad:g})" in p, p


def test_no_socket_parts() -> None:
    for ref, (lib, value, fp, _, _, _, _, desc) in PARTS.items():
        blob = " ".join((lib, value, fp, desc)).lower()
        assert not re.search(r"mill-?max|socket|receptacle|castell", blob), ref
    assert "SMD" not in PARTS["U1"][2]


def test_harness_pads_are_through_hole() -> None:
    fp = PARTS["J1"][2].split(":")[1]
    pads = _pads(fp)
    assert len(pads) == 5
    for p in pads:
        assert "thru_hole" in p and f"(drill {D.HARNESS['drill']:g})" in p, p


def test_job_file_declares_the_jlc_4_layer_stackup() -> None:
    # JLC04161H-7628 (jlcpcb.com/impedance): outer 0.035, inner 0.0152, 7628 prepreg 0.2104,
    # core 1.065. The board's stackup is written by gen_pcb.py from design.STACKUP.
    import glob
    import json

    jobs = glob.glob(os.path.join(ROOT, "fab", "gerbers", "*.gbrjob"))
    assert jobs, "run scripts/build.sh"
    stack = json.load(open(jobs[0]))["MaterialStackup"]
    cu = {e["Name"]: e["Thickness"] for e in stack if e["Type"] == "Copper"}
    assert cu == {"F.Cu": 0.035, "In1.Cu": 0.0152, "In2.Cu": 0.0152, "B.Cu": 0.035}, cu
    diel = [e["Thickness"] for e in stack if e["Type"] == "Dielectric"]
    assert diel == [0.2104, 1.065, 0.2104], diel


def _place() -> dict[str, tuple]:
    import ast

    tree = ast.parse(open(os.path.join(ROOT, "scripts", "gen_pcb.py")).read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "PLACE":
            return ast.literal_eval(node.value)
    raise AssertionError("PLACE not found")


def test_cpl_lists_exactly_the_assembled_parts_with_jlc_rotation_offsets() -> None:
    import csv

    path = os.path.join(ROOT, "fab", "carrier_cpl_jlc.csv")
    rows = {r["Designator"]: r for r in csv.DictReader(open(path))}
    assembled = {ref for ref, p in PARTS.items() if p[5] and not p[4]}
    assert set(rows) == assembled
    place = _place()
    for ref, row in rows.items():
        assert place[ref][3] == "F" and row["Layer"] == "Top", ref
        fp = PARTS[ref][2].split(":")[1]
        off = next((o for pat, o in D.CPL_ROTATION if re.match(pat, fp)), 0)
        assert float(row["Rotation"]) == (place[ref][2] + off) % 360, ref


def _pad_xy(fp_name: str) -> dict[str, tuple[float, float]]:
    path = os.path.join(ROOT, "lib", "carrier.pretty", fp_name + ".kicad_mod")
    found = re.findall(r'\(pad "(\d+)" smd \w+ \(at ([-\d.]+) ([-\d.]+)', open(path).read())
    return {n: (float(x), float(y)) for n, x, y in found}


def test_sot363_pad_ring_is_counter_clockwise_like_kicad_stock() -> None:
    # Nexperia SOT363-2 (top view): pins 1-3 down the left column, 4-6 up the right,
    # so 6 faces 1 and 4 faces 3. Same pad map as KiCad's stock SOT-363_SC-70-6, which
    # is the footprint the JLCKicadTools "^SOT-363" rotation offset was written for.
    xy = _pad_xy(PARTS["U3"][2].split(":")[1])
    assert sorted(xy) == ["1", "2", "3", "4", "5", "6"]
    assert all(xy[p][0] < 0 for p in "123") and all(xy[p][0] > 0 for p in "456")
    assert xy["1"][1] < xy["2"][1] < xy["3"][1]
    assert xy["6"][1] == xy["1"][1] and xy["4"][1] == xy["3"][1]
    assert math.isclose(xy["4"][0] - xy["3"][0], 1.95)  # Nexperia sot363-2_fr land pitch


def _pro_rules() -> dict[str, float]:
    import json

    with open(os.path.join(ROOT, "carrier.kicad_pro")) as fh:
        pro = json.load(fh)
    return pro["board"]["design_settings"]["rules"]


def test_drc_rules_are_at_least_as_strict_as_jlc_4_layer_minimums() -> None:
    # D.JLC_MIN: JLC's published multilayer 1 oz minimums (design.py cites the page).
    rules = _pro_rules()
    assert set(D.JLC_MIN) <= set(rules), set(D.JLC_MIN) - set(rules)
    loose = {k: (rules[k], v) for k, v in D.JLC_MIN.items() if rules[k] < v - 1e-9}
    assert not loose, f"rule below JLC minimum (ours, JLC): {loose}"
    assert rules["min_via_annular_width"] >= 0.15  # JLC multilayer PTH ring, abs. min
    assert rules["min_hole_clearance"] >= 0.30  # JLC inner-layer PTH hole to copper
    assert rules["min_clearance"] >= 0.15  # JLC SMD pad to pad, different nets


def test_project_rules_come_from_design() -> None:
    rules = _pro_rules()
    for k, v in D.DRC_RULES.items():
        assert math.isclose(rules[k], v), (k, rules[k], v)


def _kit(word: str) -> list[dict]:
    return [k for k in D.KIT if word.lower() in (k["mpn"] + " " + k["use"]).lower()]


def _stack(gap: float) -> float:
    pcb = sum(t for _, kind, t, _, _ in D.STACKUP if "Mask" not in kind)
    return D.MOUNT["tail"] + pcb + gap + D.MOUNT["xiao_thk"]


def test_kit_has_one_harness_10k_per_tap_wire() -> None:
    (r,) = _kit("10k")
    assert r["per_board"] == len(TAPS), r
    assert r["dk"] and r["mpn"], r


def test_kit_has_kapton_within_the_shim_range() -> None:
    (k,) = _kit("polyimide")
    lo, hi = D.SHIM["min"], D.SHIM["max"]
    assert lo <= k["thk"] <= hi, (k, D.SHIM)
    assert 3 * k["thk"] <= hi  # README: 1-3 layers of the kit tape
    assert _stack(hi) <= D.HEIGHT_MAX  # spacer off, thickest shim: inside the limit
    assert _stack(D.HEADER["insulator"]) > D.HEIGHT_MAX  # spacer on: over the limit


def test_kit_parts_are_priced_and_documented() -> None:
    docs = {}
    for f in ("README.md", "PRICING.md"):
        with open(os.path.join(ROOT, f)) as fh:
            docs[f] = fh.read()
    for k in D.KIT:
        for name, txt in docs.items():
            assert k["dk"] in txt, (k["dk"], name)


# --- JLC assembly tooling holes (customer-placed) ---------------------------------------


def _board():
    from sexp import find, parse

    return find, parse(open(os.path.join(ROOT, "carrier.kicad_pcb")).read())


def _abs(fp_at: list, pad_at: list) -> tuple[float, float]:
    """Pad centre in board coordinates (KiCad: y down, rotation counter-clockwise)."""
    x, y = float(fp_at[1]), float(fp_at[2])
    a = math.radians(float(fp_at[3])) if len(fp_at) > 3 else 0.0
    dx, dy = float(pad_at[1]), float(pad_at[2])
    return x + dx * math.cos(a) + dy * math.sin(a), y - dx * math.sin(a) + dy * math.cos(a)


def _origin(find, pcb) -> tuple[float, float]:
    pts = [
        (float(e[1]), float(e[2]))
        for g in find(pcb, "gr_line")
        if find(g, "layer")[0][1] == "Edge.Cuts"
        for e in find(g, "start") + find(g, "end")
    ]
    return min(p[0] for p in pts), min(p[1] for p in pts)


def _tooling_and_copper():
    """(tooling holes [(x, y, drill, mask_margin)], copper [(kind, geometry, half-width)])."""
    find, pcb = _board()
    holes, copper = [], []
    for fp in find(pcb, "footprint"):
        at = find(fp, "at")[0]
        for pad in find(fp, "pad"):
            xy = _abs(at, find(pad, "at")[0])
            if pad[2] == "np_thru_hole":
                mm = find(pad, "solder_mask_margin")
                drill = float(find(pad, "drill")[0][1])
                holes.append((*xy, drill, float(mm[0][1]) if mm else None, fp[1]))
            else:
                w, h = (float(v) for v in find(pad, "size")[0][1:3])
                copper.append(("pad", (xy, xy), math.hypot(w, h) / 2))  # circumscribed
    for v in find(pcb, "via"):
        xy = tuple(float(c) for c in find(v, "at")[0][1:3])
        copper.append(("via", (xy, xy), float(find(v, "size")[0][1]) / 2))
    for s in find(pcb, "segment"):
        a = tuple(float(c) for c in find(s, "start")[0][1:3])
        b = tuple(float(c) for c in find(s, "end")[0][1:3])
        copper.append(("track", (a, b), float(find(s, "width")[0][1]) / 2))
    return find, pcb, holes, copper


def _seg_dist(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def test_tooling_holes_match_jlc_spec() -> None:
    # jlcpcb.com/help/article/how-to-add-tooling-holes-for-pcb-assembly-order (read 2026-10-14):
    # 1.152 mm round non-plated, 0.148 mm solder mask expansion, two or three holes.
    t = D.TOOLING
    assert math.isclose(t["drill"], 1.152) and math.isclose(t["mask_margin"], 0.148)
    find, pcb, holes, _ = _tooling_and_copper()
    assert 2 <= len(holes) <= 3, holes
    ox, oy = _origin(find, pcb)
    want = sorted((ox + x, oy + y) for x, y in D.tooling_holes())
    got = sorted((h[0], h[1]) for h in holes)
    assert len(want) == len(got)
    for (wx, wy), (gx, gy) in zip(want, got):
        assert math.isclose(wx, gx, abs_tol=1e-3) and math.isclose(wy, gy, abs_tol=1e-3)
    for x, y, drill, margin, _ in holes:
        assert math.isclose(drill, t["drill"]) and math.isclose(margin, t["mask_margin"])
        edge = min(x - ox, y - oy, ox + D.BOARD_W - x, oy + D.BOARD_H - y) - drill / 2
        assert edge >= t["min_edge"] - 1e-9, (x, y, edge)
    # as far apart as practical: in different corners, at least most of a board side apart
    (ax, ay), (bx, by) = got[0], got[-1]
    assert math.hypot(ax - bx, ay - by) >= min(D.BOARD_W, D.BOARD_H) - 2 * t["edge_inset"] - 1e-9


def test_tooling_holes_keep_clear_of_copper() -> None:
    _, _, holes, copper = _tooling_and_copper()
    assert holes
    for x, y, drill, _, _ in holes:
        for kind, (a, b), half in copper:
            gap = _seg_dist((x, y), a, b) - half - drill / 2
            assert gap >= D.TOOLING["copper_clear"] - 1e-9, (x, y, kind, a, b, gap)


def test_pours_clear_the_tooling_holes() -> None:
    find, pcb, holes, _ = _tooling_and_copper()
    assert holes
    need = D.DRC_RULES["min_hole_clearance"]
    for z in find(pcb, "zone"):
        for fpoly in find(z, "filled_polygon"):
            for xy in find(find(fpoly, "pts")[0], "xy"):
                p = (float(xy[1]), float(xy[2]))
                for x, y, drill, _, _ in holes:
                    assert math.hypot(p[0] - x, p[1] - y) - drill / 2 >= need - 1e-3, (p, x, y)


def test_tooling_holes_are_in_the_drill_file() -> None:
    import zipfile

    z = zipfile.ZipFile(os.path.join(ROOT, "fab", "carrier_gerbers.zip"))
    npth = [n for n in z.namelist() if n.endswith(".drl") and "NPTH" in n]
    assert len(npth) == 1, z.namelist()
    txt = z.read(npth[0]).decode()
    tools = dict(re.findall(r"^(T\d+)C([\d.]+)", txt, re.M))
    tool = [k for k, v in tools.items() if math.isclose(float(v), D.TOOLING["drill"])]
    assert len(tool) == 1, tools
    hits = re.findall(rf"^{tool[0]}\n((?:X[-\d.]+Y[-\d.]+\n)+)", txt, re.M)
    assert hits and len(hits[0].split()) == len(D.tooling_holes()), txt


def test_only_the_tooling_courtyard_check_is_downgraded() -> None:
    # TH2 sits under the XIAO (U1 courtyard covers the whole top-right), so the project file
    # ignores npth_inside_courtyard; lib_footprint_mismatch is ignored because gen_pcb trims
    # silk on the board copies. Nothing else may be downgraded, and every NPTH on the
    # board must be a tooling hole, so the override can never hide a real part hole.
    import json

    with open(os.path.join(ROOT, "carrier.kicad_pro")) as fh:
        sev = json.load(fh)["board"]["design_settings"].get("rule_severities", {})
    # KiCad 9 writes these as "ignore" by default (the build never sets them)
    kicad_default_ignore = {
        "footprint_filters_mismatch",
        "footprint_type_mismatch",
        "missing_courtyard",
        "track_not_centered_on_via",
        "tuning_profile_track_geometries",
    }
    ignored = {k for k, v in sev.items() if v == "ignore"}
    ours = {k for k, v in D.DRC_SEVERITY.items() if v == "ignore"}
    assert ours == {"npth_inside_courtyard", "lib_footprint_mismatch"}, ours
    assert ignored - kicad_default_ignore == ours, ignored
    assert all(sev[k] == v for k, v in D.DRC_SEVERITY.items())
    _, _, holes, _ = _tooling_and_copper()
    assert holes and all(h[4].startswith("carrier:ToolingHole_NPTH_") for h in holes), holes


# --- Silkscreen (JLC DFM: silk to pad / hole, silk line width) --------------------------

SILK_LAYERS = {"F.SilkS", "B.SilkS", "F.Silkscreen", "B.Silkscreen"}


def test_silk_rules_are_drc_errors() -> None:
    # JLC (jlcpcb.com/capabilities/pcb-capabilities, read 2026-10-14): line >= 0.15 mm,
    # text >= 1.0 mm, pad to silkscreen >= 0.15 mm.
    import json

    s = D.SILK
    assert s["min_width"] >= 0.15 and s["min_text_h"] >= 1.0 and s["pad_clear"] >= 0.15
    with open(os.path.join(ROOT, "carrier.kicad_pro")) as fh:
        ds = json.load(fh)["board"]["design_settings"]
    assert math.isclose(ds["rules"]["min_silk_clearance"], s["pad_clear"])
    assert ds["rules"]["min_text_thickness"] >= s["min_width"]
    assert ds["rules"]["min_text_height"] >= s["min_text_h"]
    for k in ("silk_over_copper", "silk_overlap", "silk_edge_clearance"):
        assert ds["rule_severities"][k] == "error", k
        assert D.DRC_SEVERITY[k] == "error", k


def _silk_items():
    find, pcb = _board()
    out = []

    def walk(node):
        for e in node:
            if not isinstance(e, list) or not e:
                continue
            lay = find(e, "layer")
            if lay and lay[0][1] in SILK_LAYERS and e[0] != "pad":
                out.append(e)
            elif e[0] in ("footprint",):
                walk(e)

    walk(pcb)
    return find, out


def test_silk_strokes_and_text_meet_jlc_minimums() -> None:
    find, items = _silk_items()
    assert items
    for e in items:
        if e[0] in ("fp_text", "gr_text", "property"):
            eff = find(e, "effects")
            if not eff or any(h == "hide" or h == ["hide", "yes"] for h in eff[0]) or find(
                e, "hide"
            ) == [["hide", "yes"]]:
                continue
            font = find(eff[0], "font")[0]
            h = float(find(font, "size")[0][1])
            t = float(find(font, "thickness")[0][1])
            assert h >= D.SILK["min_text_h"] - 1e-9, e[:3]
            assert t >= D.SILK["min_width"] - 1e-9, e[:3]
        else:
            stroke = find(e, "stroke")
            w = float(find(stroke[0], "width")[0][1]) if stroke else float(find(e, "width")[0][1])
            assert w >= D.SILK["min_width"] - 1e-9, e[:2]


def test_silk_check_report_is_clean() -> None:
    # scripts/check_silk.py (run by export_fab.sh) measures every silk item against pad
    # mask openings, holes and the board edge, and confirms the polarity / pin-1 marks.
    rpt = open(os.path.join(ROOT, "fab", "silk.rpt")).read()
    assert re.search(r"^silk violations: 0$", rpt, re.M), rpt
    for ref in D.SILK["marks"]:
        assert re.search(rf"^mark {ref} ok", rpt, re.M), (ref, rpt)
    assert "12V OFF FOR USB" in rpt


def test_xiao_pin_1_is_marked_by_a_square_pad() -> None:
    pads = _pads(PARTS["U1"][2].split(":")[1])
    assert next(p for p in pads if p.startswith('(pad "1" ')).split()[3] == "rect"
    assert all(p.split()[3] == "circle" for p in pads if not p.startswith('(pad "1" '))
