"""Generate the project-local symbol library, XIAO footprint and 3D box models.

Run from hardware/carrier:  python3 scripts/gen_lib.py
Dimensions come from Seeed's XIAO-ESP32-S3-DIP footprint (lib/seeed, CC BY-SA 4.0) and
the Mill-Max 7305 receptacle datasheet; see README "Verified vs inferred".
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
THT_PAD, THT_DRILL = 2.0, 1.52  # Mill-Max 7305 needs a 1.52 mm hole; 0.24 mm ring
SMD_W, SMD_L, SMD_C = 1.524, 1.85, 7.925  # castellation pad: y 7.0..8.85
SOCKET_GAP = 0.3  # XIAO underside above carrier top (receptacle flange)
XIAO_THK = 4.9  # XIAO Plus overall height incl. USB-C (approx, see README)
TAIL = 0.77  # 2.67 mm receptacle - 0.3 flange - 1.6 board (inferred flange)


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
        "carrier:XIAO_ESP32S3_Socket_SMD",
        "Seeed XIAO ESP32S3 (Plus), 14 edge pins only; socketed or soldered flat",
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
    out = (
        '(kicad_symbol_lib (version 20251024) (generator "carrier_gen_lib") '
        '(generator_version "1")\n' + xiao + "\n" + lmr + "\n)\n"
    )
    with open(os.path.join(ROOT, "lib", "carrier.kicad_sym"), "w") as fh:
        fh.write(out)


def gen_footprint():
    L = [
        '(footprint "XIAO_ESP32S3_Socket_SMD" (version 20241229) (generator "carrier_gen_lib")',
        '(layer "F.Cu")',
        (
            '(descr "XIAO ESP32S3 (Plus) edge pins: 1.52 mm PTH for Mill-Max 7305 receptacles '
            'plus castellation pads for flat SMT. Derived from Seeed XIAO-ESP32-S3-DIP (CC BY-SA 4.0).")'
        ),
        "(attr through_hole exclude_from_bom)",
        '(property "Reference" "U1" (at 0 -2 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
        '(property "Value" "XIAO_ESP32S3" (at 0 0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
    ]

    # fab + silk outline of the XIAO and its USB-C overhang
    def rect(layer, x0, y0, x1, y1, w):
        return (
            f"(fp_rect (start {F(x0)} {F(y0)}) (end {F(x1)} {F(y1)}) "
            f'(stroke (width {w}) (type solid)) (fill no) (layer "{layer}"))'
        )

    L.append(rect("F.Fab", XIAO_X0, -XIAO_HALF_W, XIAO_X1, XIAO_HALF_W, 0.1))
    L.append(rect("F.Fab", XIAO_X1, -USB_HALF_W, USB_X1, USB_HALF_W, 0.1))
    L.append(
        rect(
            "F.CrtYd",
            XIAO_X0 - 0.1,
            -(SMD_C + SMD_L / 2) - 0.05,
            USB_X1,
            SMD_C + SMD_L / 2 + 0.05,
            0.05,
        )
    )
    # silk: XIAO outline inside the pad rows (visible before the XIAO is fitted)
    L.append(rect("F.SilkS", XIAO_X0 + 0.2, -3.6, XIAO_X1 - 0.2, 3.6, 0.15))
    L.append(
        '(fp_text user "USB" (at 8.6 0 90) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.15))))'
    )
    for n, nm in XIAO_PINS:
        x, y = pin_xy(n)
        short = nm.split("/")[0]
        ty = y + (2.4 if y < 0 else -2.4)
        L.append(
            f'(fp_text user "{short}" (at {F(x)} {F(ty)} 90) (layer "F.SilkS") '
            "(effects (font (size 0.8 0.8) (thickness 0.15))))"
        )
        L.append(
            f'(pad "{n}" thru_hole {"rect" if n == 1 else "circle"} (at {F(x)} {F(y)}) '
            f'(size {THT_PAD} {THT_PAD}) (drill {THT_DRILL}) (layers "*.Cu" "*.Mask"))'
        )
        sy = -SMD_C if y < 0 else SMD_C
        L.append(
            f'(pad "{n}" smd roundrect (at {F(x)} {F(sy)}) (size {SMD_W} {SMD_L}) '
            '(layers "F.Cu" "F.Mask") (roundrect_rratio 0.15))'
        )
    L.append(
        '(model "${KIPRJMOD}/lib/3d/XIAO_ESP32S3_socketed_box.wrl" '
        "(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))"
    )
    L.append(")")
    os.makedirs(os.path.join(ROOT, "lib", "carrier.pretty"), exist_ok=True)
    with open(
        os.path.join(
            ROOT, "lib", "carrier.pretty", "XIAO_ESP32S3_Socket_SMD.kicad_mod"
        ),
        "w",
    ) as fh:
        fh.write("\n".join(L) + "\n")


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
    top = SOCKET_GAP
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
    for n, _ in XIAO_PINS:  # receptacle flange above and tail below a 1.6 mm board
        x, y = pin_xy(n)
        shapes.append(
            wrl_box(
                x - 0.98, y - 0.98, 0, x + 0.98, y + 0.98, SOCKET_GAP, (0.85, 0.7, 0.2)
            )
        )
        shapes.append(
            wrl_box(
                x - 0.5, y - 0.5, -1.6 - TAIL, x + 0.5, y + 0.5, -1.6, (0.85, 0.7, 0.2)
            )
        )
    with open(os.path.join(d, "XIAO_ESP32S3_socketed_box.wrl"), "w") as fh:
        fh.write(
            "#VRML V2.0 utf8\n# Approximate box model: XIAO ESP32S3 Plus on Mill-Max 7305 receptacles.\n"
        )
        fh.write("".join(shapes))
    # KiCad ships no 3D model for Fuse_1812_4532Metric: box from the SMD1812P050TF/60
    # LCSC listing (4.73 x 3.41 x 1.8 mm max)
    with open(os.path.join(d, "Fuse_1812_box.wrl"), "w") as fh:
        fh.write(
            "#VRML V2.0 utf8\n# Approximate box model: 1812 PPTC, 1.8 mm max height.\n"
        )
        fh.write(wrl_box(-2.365, -1.705, 0, 2.365, 1.705, 1.8, (0.75, 0.6, 0.2)))


if __name__ == "__main__":
    gen_symbols()
    gen_footprint()
    gen_models()
    print("ok")
