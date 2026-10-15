"""Generate the project-local symbol library, XIAO footprint and 3D box models.

Run from the board directory:  python3 scripts/gen_lib.py
XIAO pin positions come from Seeed's XIAO-ESP32-S3-DIP footprint (lib/seeed, CC BY-SA 4.0);
hole sizes, header and land-pattern numbers come from design.py (sources cited there and in
CHANGES-revB.md).
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import design as D  # noqa: E402
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
THT_PAD, THT_DRILL = D.XIAO_PIN_PAD, D.XIAO_PIN_DRILL
GAP = D.MOUNT["gap"]  # XIAO underside above carrier top (header insulator or shim)
XIAO_THK = D.MOUNT["xiao_thk"]  # XIAO Plus PCB + parts incl. USB-C (unmeasured)
TAIL = D.MOUNT["tail"]  # header tail left below the carrier after trimming
TXT = D.SILK["min_text_h"]  # JLC minimum silkscreen text height
SW = D.SILK["min_width"]  # JLC minimum silkscreen line width


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
        "carrier:XIAO_ESP32S3_Header_THT",
        "Seeed XIAO ESP32S3 (Plus), 14 edge pins, soldered on 2.54 mm male headers",
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
    buf_pins = [  # Nexperia 74LVC2G17 Table 3
        sym_pin(1, "1A", -10.16, 2.54, 0),
        sym_pin(3, "2A", -10.16, -2.54, 0),
        sym_pin(6, "1Y", 10.16, 2.54, 180),
        sym_pin(4, "2Y", 10.16, -2.54, 180),
        sym_pin(5, "VCC", 0, 10.16, 270),
        sym_pin(2, "GND", 0, -10.16, 90),
    ]
    buf = symbol(
        "74LVC2G17",
        "U",
        "74LVC2G17GW",
        "carrier:SOT363-2_Nexperia",
        "Nexperia dual Schmitt buffer, 5.5 V-tolerant inputs, Ioff, SOT363-2",
        (-5.08, 5.08, 5.08, -5.08),
        buf_pins,
    )
    out = (
        '(kicad_symbol_lib (version 20251024) (generator "carrier_gen_lib") '
        '(generator_version "1")\n' + xiao + "\n" + lmr + "\n" + buf + "\n)\n"
    )
    with open(os.path.join(ROOT, "lib", "carrier.kicad_sym"), "w") as fh:
        fh.write(out)


def rect(layer, x0, y0, x1, y1, w):
    return (
        f"(fp_rect (start {F(x0)} {F(y0)}) (end {F(x1)} {F(y1)}) "
        f'(stroke (width {w}) (type solid)) (fill no) (layer "{layer}"))'
    )


def silk_text(text, x, y, rot=0, layer="F.SilkS"):
    return (
        f'(fp_text user "{text}" (at {F(x)} {F(y)} {rot}) (layer "{layer}") '
        f"(effects (font (size {TXT} {TXT}) (thickness {SW}))))"
    )


def fp_head(name, descr, attr, ref="REF**", value=None):
    return [
        f'(footprint "{name}" (version 20241229) (generator "carrier_gen_lib")',
        '(layer "F.Cu")',
        f'(descr "{descr}")',
        f"(attr {attr})",
        f'(property "Reference" "{ref}" (at 0 -2 0) (layer "F.SilkS") '
        f"(effects (font (size {TXT} {TXT}) (thickness {SW}))))",
        f'(property "Value" "{value or name}" (at 0 2 0) (layer "F.Fab") '
        "(effects (font (size 1 1) (thickness 0.15))))",
    ]


def write_fp(name, lines):
    d = os.path.join(ROOT, "lib", "carrier.pretty")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name + ".kicad_mod"), "w") as fh:
        fh.write("\n".join(lines + [")"]) + "\n")


def gen_footprint():
    L = fp_head(
        "XIAO_ESP32S3_Header_THT",
        f"XIAO ESP32S3 (Plus) on 2.54 mm male headers (0.64 mm square posts): "
        f"drill {THT_DRILL} / pad {THT_PAD}. Pin positions from Seeed XIAO-ESP32-S3-DIP "
        "(CC BY-SA 4.0).",
        "through_hole exclude_from_bom",
        "U1",
        "XIAO_ESP32S3",
    )
    # fab outline of the XIAO and its USB-C overhang; courtyard = XIAO body
    L.append(rect("F.Fab", XIAO_X0, -XIAO_HALF_W, XIAO_X1, XIAO_HALF_W, 0.1))
    L.append(rect("F.Fab", XIAO_X1, -USB_HALF_W, USB_X1, USB_HALF_W, 0.1))
    L.append(
        rect("F.CrtYd", XIAO_X0 - 0.1, -XIAO_HALF_W - 0.1, USB_X1, XIAO_HALF_W + 0.1, 0.05)
    )
    # silk inside the pin rows (visible before the XIAO is fitted)
    L.append(rect("F.SilkS", XIAO_X0 + 0.2, -2.9, XIAO_X1 - 0.2, 2.9, SW))
    L.append(silk_text("USB", 8.25, 0, 90))  # clear of the via at the USB end
    for n, nm in XIAO_PINS:
        x, y = pin_xy(n)
        ty = y + (2.75 if y < 0 else -2.75)
        L.append(silk_text(nm.split("/")[0], x, ty, 90))
        L.append(
            f'(pad "{n}" thru_hole {"rect" if n == 1 else "circle"} (at {F(x)} {F(y)}) '
            f'(size {F(THT_PAD)} {F(THT_PAD)}) (drill {F(THT_DRILL)}) (layers "*.Cu" "*.Mask"))'
        )
    L.append(
        '(model "${KIPRJMOD}/lib/3d/XIAO_ESP32S3_header_box.wrl" '
        "(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))"
    )
    write_fp("XIAO_ESP32S3_Header_THT", L)


def gen_sot363():
    # Nexperia SOT363-2 reflow footprint (sot363-2_fr): lands 0.75 x 0.40 at
    # x +-0.975 (1.95 centre to centre), pitch 0.65; occupied area 2.9 x 2.35.
    L = fp_head(
        "SOT363-2_Nexperia",
        "TSSOP6 / SOT363-2, Nexperia reflow footprint sot363-2_fr (22-11-07)",
        "smd",
    )
    for n, (x, y) in {
        1: (-0.975, -0.65), 2: (-0.975, 0), 3: (-0.975, 0.65),
        4: (0.975, 0.65), 5: (0.975, 0), 6: (0.975, -0.65),
    }.items():
        L.append(
            f'(pad "{n}" smd roundrect (at {F(x)} {F(y)}) (size 0.75 0.4) '
            '(layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.15))'
        )
    L.append(rect("F.Fab", -0.625, -1.0, 0.625, 1.0, 0.1))
    L.append(rect("F.CrtYd", -1.45, -1.175, 1.45, 1.175, 0.05))
    L.append(
        f"(fp_line (start -0.35 -1.1) (end 0.35 -1.1) (stroke (width {SW}) (type solid)) "
        '(layer "F.SilkS"))'
    )
    L.append(
        f"(fp_circle (center -0.25 -0.6) (end -0.15 -0.6) (stroke (width {SW}) (type solid)) "
        '(fill yes) (layer "F.SilkS"))'
    )
    L.append(
        '(model "${KICAD10_3DMODEL_DIR}/Package_TO_SOT_SMD.3dshapes/SOT-363_SC-70-6.step" '
        "(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))"
    )
    write_fp("SOT363-2_Nexperia", L)


def gen_dfn1006():
    # Hongjiacheng H5VL10B suggested pad layout: J 0.50-0.60 (pad x), K 0.25-0.35
    # (gap), M 0.55-0.65 (pad y). Chosen: 0.55 x 0.60, gap 0.30 -> centres +-0.425.
    L = fp_head(
        "DFN1006-2L_H5VL10B",
        "DFN1006-2L (1.0 x 0.6 mm), Hongjiacheng H5VL10B suggested pad layout",
        "smd",
    )
    for n, x in ((1, -0.425), (2, 0.425)):
        L.append(
            f'(pad "{n}" smd roundrect (at {F(x)} 0) (size 0.55 0.6) '
            '(layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.1))'
        )
    L.append(rect("F.Fab", -0.5, -0.3, 0.5, 0.3, 0.1))
    L.append(rect("F.CrtYd", -0.95, -0.55, 0.95, 0.55, 0.05))
    L.append(
        '(model "${KIPRJMOD}/lib/3d/DFN1006_box.wrl" '
        "(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))"
    )
    write_fp("DFN1006-2L_H5VL10B", L)


def gen_harness_pads():
    h = D.HARNESS
    n_pads = len(D.PARTS["J1"][6])
    L = fp_head(
        f"Harness_WirePads_1x{n_pads:02d}_P{h['pitch']:g}",
        f"Harness wires soldered into plated holes: drill {h['drill']} / pad {h['pad']}, "
        f"pitch {h['pitch']}. Pad 1 square.",
        "through_hole exclude_from_bom exclude_from_pos_files",
    )
    for i in range(n_pads):
        shape = "rect" if i == 0 else "circle"
        L.append(
            f'(pad "{i + 1}" thru_hole {shape} (at {F(i * h["pitch"])} 0) '
            f'(size {F(h["pad"])} {F(h["pad"])}) (drill {F(h["drill"])}) (layers "*.Cu" "*.Mask"))'
        )
    hp = h["pad"] / 2 + 0.25
    L.append(rect("F.CrtYd", -hp, -hp, (n_pads - 1) * h["pitch"] + hp, hp, 0.05))
    L.append(rect("F.Fab", -hp, -hp, (n_pads - 1) * h["pitch"] + hp, hp, 0.1))
    write_fp(f"Harness_WirePads_1x{n_pads:02d}_P{h['pitch']:g}", L)


def tooling_fp_name():
    return f"ToolingHole_NPTH_{D.TOOLING['drill']:g}mm"


def gen_tooling_hole():
    t = D.TOOLING
    name = tooling_fp_name()
    L = fp_head(
        name,
        f"JLC assembly tooling hole: {t['drill']:g} mm round NPTH, {t['mask_margin']:g} mm "
        "solder mask expansion (jlcpcb.com/help/article/"
        "how-to-add-tooling-holes-for-pcb-assembly-order)",
        "board_only exclude_from_pos_files exclude_from_bom",
    )
    L.append(
        f'(pad "" np_thru_hole circle (at 0 0) (size {F(t["drill"])} {F(t["drill"])}) '
        f'(drill {F(t["drill"])}) (layers "*.Cu" "*.Mask") '
        f"(solder_mask_margin {F(t['mask_margin'])}) (clearance {F(t['copper_clear'])}))"
    )
    write_fp(name, L)


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
    for old in ("XIAO_ESP32S3_socketed_box.wrl",):
        if os.path.exists(os.path.join(d, old)):
            os.remove(os.path.join(d, old))
    top = GAP
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
    post = D.HEADER["post"] / 2
    for row in (-ROW_Y, ROW_Y):  # header insulator strip between the boards
        x0, _ = pin_xy(1 if row < 0 else 8)
        x1, _ = pin_xy(7 if row < 0 else 14)
        lo, hi = min(x0, x1) - 1.27, max(x0, x1) + 1.27
        shapes.append(wrl_box(lo, row - 1.25, 0, hi, row + 1.25, GAP, (0.15, 0.15, 0.15)))
    for n, _ in XIAO_PINS:  # post: trimmed tail below to just above the XIAO PCB
        x, y = pin_xy(n)
        shapes.append(
            wrl_box(
                x - post, y - post, -1.6 - TAIL, x + post, y + post, top + 1.6 + 0.5,
                (0.85, 0.7, 0.2),
            )
        )
    with open(os.path.join(d, "XIAO_ESP32S3_header_box.wrl"), "w") as fh:
        fh.write(
            "#VRML V2.0 utf8\n# Approximate box model: XIAO ESP32S3 Plus on 2.54 mm male headers.\n"
        )
        fh.write("".join(shapes))
    with open(os.path.join(d, "DFN1006_box.wrl"), "w") as fh:
        fh.write("#VRML V2.0 utf8\n# Approximate box model: DFN1006-2L, 0.4 mm.\n")
        fh.write(wrl_box(-0.5, -0.3, 0, 0.5, 0.3, 0.4, (0.2, 0.2, 0.2)))
    # KiCad ships no 3D model for Fuse_1812_4532Metric: box from the SMD1812P050TF/60
    # LCSC listing (4.73 x 3.41 x 1.8 mm max)
    with open(os.path.join(d, "Fuse_1812_box.wrl"), "w") as fh:
        fh.write(
            "#VRML V2.0 utf8\n# Approximate box model: 1812 PPTC, 1.8 mm max height.\n"
        )
        fh.write(wrl_box(-2.365, -1.705, 0, 2.365, 1.705, 1.8, (0.75, 0.6, 0.2)))


if __name__ == "__main__":
    gen_symbols()
    for old in ("XIAO_ESP32S3_Socket_SMD.kicad_mod",):
        p = os.path.join(ROOT, "lib", "carrier.pretty", old)
        if os.path.exists(p):
            os.remove(p)
    gen_footprint()
    gen_sot363()
    gen_dfn1006()
    gen_harness_pads()
    gen_tooling_hole()
    gen_models()
    print("ok")
