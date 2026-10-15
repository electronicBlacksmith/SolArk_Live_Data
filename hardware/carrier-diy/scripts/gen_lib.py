"""Generate the project-local symbol library, XIAO footprint and 3D box models.

Run from hardware/carrier:  python3 scripts/gen_lib.py
Dimensions come from Seeed's XIAO-ESP32-S3-DIP and Plus SMD footprints (lib/seeed,
CC BY-SA 4.0) and the Sullins 2.54 mm header datasheet; see CHANGES-revB.md.
"""

from __future__ import annotations

import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
F = lambda v: f"{v:.4f}".rstrip("0").rstrip(".")

XIAO_PINS = [  # (number, name)
    (1, "D0/GPIO1"),
    (2, "D1/GPIO2"),
    (3, "D2/GPIO3"),
    (4, "D3/GPIO4"),
    (5, "D4/GPIO5"),
    (6, "D5/GPIO6"),
    (7, "D6/GPIO43"),
    (8, "D7/GPIO44"),
    (9, "D8/GPIO7"),
    (10, "D9/GPIO8"),
    (11, "D10/GPIO9"),
    (12, "3V3"),
    (13, "GND"),
    (14, "5V"),
]

# XIAO geometry (mm, footprint origin = XIAO PCB centre, USB toward +x)
ROW_Y = 7.62  # pin-row offset from centre (Seeed DIP footprint)
PITCH = 2.54
XIAO_X0, XIAO_X1 = -10.414, 10.541  # XIAO PCB ends (Seeed outline)
XIAO_HALF_W = 8.9  # 17.8 mm wide
USB_X1, USB_HALF_W = 12.065, 4.47  # USB-C overhang (Seeed outline)
XIAO_FP = "XIAO_ESP32S3_Header_THT"

# Header-pin mount (rev B): Sullins PRPC040SAAN-RC style 0.64 mm square pins, soldered.
PIN_SQ_MAX = 0.66  # 0.025" (0.635) square pin, +0.025 allowance [I, see CHANGES-revB.md]
PIN_HOLE_MAX = 1.27  # largest finished hole we accept for a 0.64 pin (solder still bridges) [I]
PTH_TOL = (0.13, -0.08)  # JLC plated-hole tolerance (+/-), mm [V, JLC capabilities]
THT_DRILL = 1.10  # finished 1.02..1.23 at JLC tolerance; >= 0.93 pin diagonal + 0.05
THT_PAD_F = 1.45  # top ring kept small: the XIAO sits flush on it (Plus pads 15-23)
THT_PAD_B = 1.80  # solder-side ring (B.Cu SMD pad overlaid on the PTH)
HEADER_GAP = 0.3  # XIAO underside above carrier top: XIAO-side solder fillets [I, measure]
XIAO_THK = 4.9  # XIAO Plus overall height incl. USB-C (approx, see README) [I]
TAIL = 1.0  # header tails trimmed to <= 1.0 mm below the carrier [I, user trims]

# Harness wire pads J1 (rev B): direct-solder, 2.54 mm pitch, 26-30 AWG
WIRE_PITCH, WIRE_DRILL, WIRE_PAD = 2.54, 1.0, 1.8
WIRE_FP = "WirePads_1x06_P2.54"

# Two-pad SMD land patterns taken straight from the datasheets (CHANGES-revB.md):
# name: (pad length along the axis, pad width across, centre-to-centre,
#        body x, body y, body height, descr)
TWO_PAD = {
    # Bourns SRP4020TA: 5.2 overall, 2.2 gap, 2.4 tall; body 4.45 x 4.06 x 2.0 max.
    # The terminal wraps onto the end face, so an iron reaches it at the pad.
    "L_Bourns_SRP4020TA": (1.5, 2.4, 3.7, 4.45, 4.06, 2.0,
                           "Bourns SRP4020TA shielded inductor, datasheet land pattern"),
    # Bourns MF-MSMF (style 2): 1.68 x 2.95 pads, 3.1 inner gap; body 4.83 x 3.41 x 1.8 max.
    "Fuse_1812_Bourns_MF-MSMF": (1.68, 2.95, 4.78, 4.83, 3.41, 1.8,
                                 "Bourns MF-MSMF 1812 PPTC, datasheet land pattern"),
    # Littelfuse SMF (SOD-123FL) mounting pad layout: 1.3 x 1.4 pads, 1.6 inner gap;
    # body A 2.7 x D 1.8 (nominal) x H 1.1 max; leads 3.4-3.9 tip to tip. Pad 1 = cathode.
    "D_SOD-123FL_Littelfuse_SMF": (1.3, 1.4, 2.9, 2.7, 1.8, 1.1,
                                   "Littelfuse SMF SOD-123FL TVS, datasheet mounting pad layout"),
}
# Two-pad parts with a polarity: a cathode bar is drawn on silk beside pad 1.
POLAR = {"D_SOD-123FL_Littelfuse_SMF"}
# TI DBV0006A (SOT-23-6) example land pattern: 1.1 x 0.6 pads, rows 2.6 apart.
DBV_FP = "SOT-23-6_TI_DBV0006A"
DBV_PAD = (1.1, 0.6)
DBV_ROW = 2.6


def pin_xy(n: int):
    if n <= 7:
        return 7.62 - (n - 1) * PITCH, -ROW_Y
    return -7.62 + (n - 8) * PITCH, ROW_Y


def txt(name, at, size=1.27, hide=False, extra=""):
    h = " (hide yes)" if hide else ""
    return f'(property "{name[0]}" "{name[1]}" (at {at}){h} (effects (font (size {size} {size})){extra}))'


def sym_pin(num, name, x, y, ang, length=5.08):
    return (
        f"(pin passive line (at {F(x)} {F(y)} {ang}) (length {F(length)}) "
        f'(name "{name}" (effects (font (size 1.27 1.27)))) '
        f'(number "{num}" (effects (font (size 1.27 1.27)))))'
    )


def symbol(name, ref, value, fp, desc, rect, pins):
    body = (
        f"(rectangle (start {F(rect[0])} {F(rect[1])}) (end {F(rect[2])} {F(rect[3])}) "
        "(stroke (width 0.254) (type default)) (fill (type background)))"
    )
    return "\n".join(
        [
            f'(symbol "{name}" (exclude_from_sim no) (in_bom yes) (on_board yes)',
            txt(("Reference", ref), f"0 {F(rect[1] + 1.27)} 0"),
            txt(("Value", value), f"0 {F(rect[3] - 1.27)} 0"),
            txt(("Footprint", fp), "0 0 0", hide=True),
            txt(("Datasheet", ""), "0 0 0", hide=True),
            txt(("Description", desc), "0 0 0", hide=True),
            f'(symbol "{name}_0_1" {body})',
            f'(symbol "{name}_1_1"',
            *pins,
            "))",
        ]
    )


def gen_symbols():
    xiao_pins = []
    for i, (n, nm) in enumerate(XIAO_PINS[:7]):
        xiao_pins.append(sym_pin(n, nm, -20.32, 7.62 - i * 2.54, 0))
    right = list(reversed(XIAO_PINS[7:]))  # 14 at top
    for i, (n, nm) in enumerate(right):
        xiao_pins.append(sym_pin(n, nm, 20.32, 7.62 - i * 2.54, 180))
    xiao = symbol(
        "XIAO_ESP32S3",
        "U",
        "XIAO_ESP32S3_Plus",
        f"carrier:{XIAO_FP}",
        "Seeed XIAO ESP32S3 (Plus), 14 edge pins only, on soldered header pins",
        (-15.24, 10.16, 15.24, -10.16),
        xiao_pins,
    )
    lmr_pins = [
        sym_pin(5, "VIN", -12.7, 2.54, 0),
        sym_pin(4, "EN", -12.7, 0, 0),
        sym_pin(2, "GND", 0, -10.16, 90),
        sym_pin(1, "CB", 12.7, 2.54, 180),
        sym_pin(6, "SW", 12.7, 0, 180),
        sym_pin(3, "FB", 12.7, -2.54, 180),
    ]
    lmr = symbol(
        "LMR51610",
        "U",
        "LMR51610YDBVR",
        "Package_TO_SOT_SMD:SOT-23-6",
        "TI LMR51610 4-65 V 1 A sync buck, SOT-23-6 (DBV)",
        (-7.62, 5.08, 7.62, -5.08),
        lmr_pins,
    )
    buf_pins = [  # TI SN74LVC2G17 DBV (SOT-23-6) pin numbers
        sym_pin(1, "1A", -12.7, 2.54, 0),
        sym_pin(3, "2A", -12.7, -2.54, 0),
        sym_pin(6, "1Y", 12.7, 2.54, 180),
        sym_pin(4, "2Y", 12.7, -2.54, 180),
        sym_pin(5, "VCC", 0, 10.16, 270),
        sym_pin(2, "GND", 0, -10.16, 90),
    ]
    buf = symbol(
        "74LVC2G17",
        "U",
        "SN74LVC2G17DBVR",
        "Package_TO_SOT_SMD:SOT-23-6",
        "Dual Schmitt-trigger buffer, 5.5 V tolerant inputs, Ioff, SOT-23-6 (DBV)",
        (-7.62, 5.08, 7.62, -5.08),
        buf_pins,
    )
    out = (
        '(kicad_symbol_lib (version 20251024) (generator "carrier_gen_lib") '
        '(generator_version "1")\n' + xiao + "\n" + lmr + "\n" + buf + "\n)\n"
    )
    with open(os.path.join(ROOT, "lib", "carrier.kicad_sym"), "w") as fh:
        fh.write(out)


def _rect(layer, x0, y0, x1, y1, w):
    return (
        f"(fp_rect (start {F(x0)} {F(y0)}) (end {F(x1)} {F(y1)}) "
        f'(stroke (width {w}) (type solid)) (fill no) (layer "{layer}"))'
    )


def _write_fp(name, lines):
    os.makedirs(os.path.join(ROOT, "lib", "carrier.pretty"), exist_ok=True)
    with open(os.path.join(ROOT, "lib", "carrier.pretty", name + ".kicad_mod"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


def gen_footprint():
    L = [
        f'(footprint "{XIAO_FP}" (version 20241229) (generator "carrier_gen_lib")',
        '(layer "F.Cu")',
        (
            f'(descr "XIAO ESP32S3 (Plus) edge pins on soldered 2.54 mm header pins (0.64 mm square): '
            f"{F(THT_DRILL)} mm PTH, small {F(THT_PAD_F)} mm top ring under the XIAO, {F(THT_PAD_B)} mm "
            'solder-side ring. Derived from Seeed XIAO-ESP32-S3-DIP (CC BY-SA 4.0).")'
        ),
        "(attr through_hole exclude_from_bom)",
        '(property "Reference" "U1" (at 0 -2 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
        '(property "Value" "XIAO_ESP32S3" (at 0 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
    ]
    # fab + silk outline of the XIAO and its USB-C overhang
    L.append(_rect("F.Fab", XIAO_X0, -XIAO_HALF_W, XIAO_X1, XIAO_HALF_W, 0.1))
    L.append(_rect("F.Fab", XIAO_X1, -USB_HALF_W, USB_X1, USB_HALF_W, 0.1))
    L.append(
        _rect("F.CrtYd", XIAO_X0 - 0.1, -XIAO_HALF_W - 0.05, USB_X1, XIAO_HALF_W + 0.05, 0.05)
    )
    # silk: XIAO outline inside the pad rows (visible before the XIAO is fitted)
    L.append(_rect("F.SilkS", XIAO_X0 + 0.2, -3.6, XIAO_X1 - 0.2, 3.6, 0.15))
    L.append(
        '(fp_text user "USB" (at 8.6 0 90) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))'
    )
    for n, nm in XIAO_PINS:
        x, y = pin_xy(n)
        short = nm.split("/")[0]
        ty = y + (2.5 if y < 0 else -2.5)
        L.append(
            f'(fp_text user "{short}" (at {F(x)} {F(ty)} 90) (layer "F.SilkS") '
            "(effects (font (size 1 1) (thickness 0.15))))"
        )
        shape = "rect" if n == 1 else "circle"
        L.append(
            f'(pad "{n}" thru_hole {shape} (at {F(x)} {F(y)}) '
            f'(size {F(THT_PAD_F)} {F(THT_PAD_F)}) (drill {F(THT_DRILL)}) (layers "*.Cu" "F.Mask"))'
        )
        L.append(
            f'(pad "{n}" smd {shape} (at {F(x)} {F(y)}) '
            f'(size {F(THT_PAD_B)} {F(THT_PAD_B)}) (layers "B.Cu" "B.Mask"))'
        )
    L.append(
        '(model "${KIPRJMOD}/lib/3d/XIAO_ESP32S3_header_box.wrl" '
        "(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))"
    )
    L.append(")")
    _write_fp(XIAO_FP, L)


def gen_two_pad():
    for name, (length, width, pitch, bx, by, _, descr) in TWO_PAD.items():
        xo = pitch / 2 + length / 2
        cx = max(xo + (0.35 if name in POLAR else 0), bx / 2) + 0.25
        cy = max(width, by) / 2 + 0.25
        L = [
            f'(footprint "{name}" (version 20241229) (generator "carrier_gen_lib")',
            '(layer "F.Cu")',
            f'(descr "{descr}")',
            "(attr smd)",
            '(property "Reference" "REF**" (at 0 -3 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
            f'(property "Value" "{name}" (at 0 3 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
            _rect("F.Fab", -bx / 2, -by / 2, bx / 2, by / 2, 0.1),
            _rect("F.CrtYd", -cx, -cy, cx, cy, 0.05),
        ]
        if name in POLAR:
            bar = -(xo + 0.3)
            L.append(
                f'(fp_line (start {F(bar)} {F(-width / 2)}) (end {F(bar)} {F(width / 2)}) '
                '(stroke (width 0.2) (type solid)) (layer "F.SilkS"))'
            )
        for num, sx in (("1", -1), ("2", 1)):
            L.append(
                f'(pad "{num}" smd roundrect (at {F(sx * pitch / 2)} 0) (size {F(length)} {F(width)}) '
                '(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.1))'
            )
        L.append(
            f'(model "${{KIPRJMOD}}/lib/3d/{name}_box.wrl" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'
        )
        L.append(")")
        _write_fp(name, L)


def gen_dbv():
    """KiCad's SOT-23-6 with TI's DBV0006A example pads (KiCad's are 1.325 x 0.6 at 2.275)."""
    base = os.environ.get(
        "KICAD_FOOTPRINT_DIR", "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
    )
    with open(os.path.join(base, "Package_TO_SOT_SMD.pretty", "SOT-23-6.kicad_mod")) as fh:
        s = fh.read()
    for old in ("(at -1.1375 ", "(at 1.1375 ", "(size 1.325 0.6)", '(footprint "SOT-23-6"'):
        if old not in s:
            raise RuntimeError("stock SOT-23-6 changed: " + old)
    h = F(DBV_ROW / 2)
    s = s.replace("(at -1.1375 ", f"(at -{h} ").replace("(at 1.1375 ", f"(at {h} ")
    s = s.replace("(size 1.325 0.6)", f"(size {F(DBV_PAD[0])} {F(DBV_PAD[1])})")
    s = s.replace('(footprint "SOT-23-6"', f'(footprint "{DBV_FP}"')
    _write_fp(DBV_FP, [s.rstrip("\n")])


def gen_wire_pads():
    """J1: six direct-solder harness pads in a row along +x, pad 1 square."""
    n = 6
    half = (n - 1) * WIRE_PITCH / 2
    c = WIRE_PAD / 2 + 0.25
    labels = ["12V", "GND", "NC", "GND", "T9", "T10"]
    L = [
        f'(footprint "{WIRE_FP}" (version 20241229) (generator "carrier_gen_lib")',
        '(layer "F.Cu")',
        '(descr "Six direct-solder harness wire pads, 2.54 mm pitch, 1.0 mm PTH for 26-30 AWG")',
        "(attr through_hole exclude_from_bom exclude_from_pos_files)",
        '(property "Reference" "J1" (at 0 -2.2 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
        '(property "Value" "HARNESS" (at 0 2.2 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
        _rect("F.CrtYd", -half - c, -c, half + c, c, 0.05),
        _rect("F.Fab", -half - WIRE_PAD / 2, -WIRE_PAD / 2, half + WIRE_PAD / 2, WIRE_PAD / 2, 0.1),
    ]
    for i in range(n):
        x = -half + i * WIRE_PITCH
        shape = "rect" if i == 0 else "circle"
        L.append(
            f'(pad "{i + 1}" thru_hole {shape} (at {F(x)} 0) (size {F(WIRE_PAD)} {F(WIRE_PAD)}) '
            f'(drill {F(WIRE_DRILL)}) (layers "*.Cu" "*.Mask"))'
        )
        L.append(
            f'(fp_text user "{labels[i]}" (at {F(x)} 2.0 90) (layer "B.SilkS") '
            "(effects (font (size 1 1) (thickness 0.15)) (justify right mirror)))"
        )
    L.append(")")
    _write_fp(WIRE_FP, L)


def wrl_box(x0, y0, z0, x1, y1, z1, rgb):
    # KiCad VRML unit = 0.1 inch = 2.54 mm; KiCad VRML y axis points up (board y down)
    s = 1 / 2.54
    xs, ys, zs = (x0 * s, x1 * s), (-y1 * s, -y0 * s), (z0 * s, z1 * s)
    pts = [(xs[i], ys[j], zs[k]) for k in (0, 1) for j in (0, 1) for i in (0, 1)]
    faces = [
        (0, 2, 3, 1),
        (4, 5, 7, 6),
        (0, 1, 5, 4),
        (2, 6, 7, 3),
        (0, 4, 6, 2),
        (1, 3, 7, 5),
    ]
    p = ", ".join(f"{a:.4f} {b:.4f} {c:.4f}" for a, b, c in pts)
    f = ", ".join(f"{a}, {b}, {c}, {d}, -1" for a, b, c, d in faces)
    return (
        "Shape { appearance Appearance { material Material { diffuseColor %.2f %.2f %.2f } }\n"
        " geometry IndexedFaceSet { solid FALSE coord Coordinate { point [ %s ] } coordIndex [ %s ] } }\n"
        % (rgb + (p, f))
    )


def gen_models():
    d = os.path.join(ROOT, "lib", "3d")
    os.makedirs(d, exist_ok=True)
    top = HEADER_GAP
    shapes = [
        wrl_box(
            XIAO_X0, -XIAO_HALF_W, top, XIAO_X1, XIAO_HALF_W, top + 1.6, (0.1, 0.1, 0.1)
        ),
        wrl_box(
            XIAO_X0 + 1.0,
            -6.5,
            top + 1.6,
            XIAO_X1 - 3.5,
            6.5,
            top + XIAO_THK,
            (0.75, 0.75, 0.78),
        ),
        wrl_box(
            XIAO_X1 - 7.4,
            -USB_HALF_W,
            top + 1.6,
            USB_X1,
            USB_HALF_W,
            top + XIAO_THK,
            (0.8, 0.8, 0.8),
        ),
    ]
    for n, _ in XIAO_PINS:  # 0.64 mm header pin: through both boards, tail trimmed below
        x, y = pin_xy(n)
        h = PIN_SQ_MAX / 2
        shapes.append(
            wrl_box(x - h, y - h, -1.6 - TAIL, x + h, y + h, top + 1.6, (0.85, 0.7, 0.2))
        )
    with open(os.path.join(d, "XIAO_ESP32S3_header_box.wrl"), "w") as fh:
        fh.write(
            "#VRML V2.0 utf8\n# Approximate box model: XIAO ESP32S3 Plus on soldered header pins.\n"
        )
        fh.write("".join(shapes))
    for name, (_, _, _, bx, by, bh, descr) in TWO_PAD.items():
        with open(os.path.join(d, name + "_box.wrl"), "w") as fh:
            fh.write(f"#VRML V2.0 utf8\n# Approximate box model: {descr}.\n")
            fh.write(wrl_box(-bx / 2, -by / 2, 0, bx / 2, by / 2, bh, (0.3, 0.3, 0.3)))

if __name__ == "__main__":
    gen_symbols()
    gen_footprint()
    gen_wire_pads()
    gen_two_pad()
    gen_dbv()
    gen_models()
    print("ok")
