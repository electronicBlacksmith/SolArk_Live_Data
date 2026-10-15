"""Generate carrier.kicad_pcb (placement, routing, zones, silk) with KiCad's pcbnew API.

Run from hardware/carrier with KiCad's bundled Python:
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 -I scripts/gen_pcb.py
Requires carrier.net (kicad-cli sch export netlist -o carrier.net carrier.kicad_sch);
net names are taken verbatim from it so DRC schematic parity matches.
"""

from __future__ import annotations

import json
import os
import sys

import pcbnew as P

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import design as D
from design import PARTS
from gen_sch import ROOT_UUID, U
from sexp import find, parse

FPDIR = os.environ.get(
    "KICAD_FOOTPRINT_DIR",
    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints",
)
MM = P.FromMM
OX, OY = 100.0, 100.0  # board origin (mm)
W, H = D.BOARD_W, D.BOARD_H

# ref: (x, y, rotation_deg, side); every part is on the top side (JLC top-only assembly)
PLACE = {
    "U1": (114.935, 109.4, 0, "F"),
    "J1": (101.2, 125.6, 0, "F"),
    "TVS1": (102.3, 106.6, 90, "F"),
    "D1": (102.3, 111.5, 270, "F"),
    "F1": (102.3, 117.3, 90, "F"),
    "C1": (113.85, 123.4, 90, "F"),
    "U2": (116.8, 123.4, 270, "F"),
    "C8": (119.07, 123.4, 270, "F"),
    "L1": (121.95, 123.4, 0, "F"),
    "C3": (125.6, 123.4, 270, "F"),
    "C2": (116.3, 126.1, 0, "F"),
    "R14": (113.67, 119.75, 180, "F"),
    "R13": (115.67, 119.75, 180, "F"),
    "C7": (118.5, 119.75, 180, "F"),
    "D2": (122.65, 119.75, 180, "F"),
    "C4": (125.85, 119.75, 0, "F"),
    # tap chain (bottom-left band): ESD -> 1k -> buffer -> 1k
    "D3": (108.1, 123.95, 180, "F"),
    "D4": (110.65, 123.95, 180, "F"),
    "R3": (108.82, 122.2, 90, "F"),
    "R4": (111.36, 122.2, 90, "F"),
    "U3": (106.85, 121.0, 180, "F"),
    "R5": (107.3, 122.85, 0, "F"),
    "R6": (107.3, 119.2, 0, "F"),
    "R7": (105.2, 123.15, 270, "F"),
    "R8": (104.9, 119.6, 90, "F"),
    "C9": (102.8, 121.0, 180, "F"),
}


def V(x, y):
    return P.VECTOR2I(MM(x), MM(y))


def load_nets(path):
    with open(path) as fh:
        n = parse(fh.read())
    pins = {}
    for net in find(find(n, "nets")[0], "net"):
        name = find(net, "name")[0][1]
        for node in find(net, "node"):
            pins[(find(node, "ref")[0][1], find(node, "pin")[0][1])] = name
    return pins


def main(stage="full"):
    board = P.CreateEmptyBoard()
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(MM(1.6))
    board.SetAuxOrigin(V(OX, OY + H)) if False else ds.SetAuxOrigin(V(OX, OY + H))
    # outline
    pts = [(OX, OY), (OX + W, OY), (OX + W, OY + H), (OX, OY + H)]
    for i in range(4):
        s = P.PCB_SHAPE(board)
        s.SetShape(P.SHAPE_T_SEGMENT)
        s.SetStart(V(*pts[i]))
        s.SetEnd(V(*pts[(i + 1) % 4]))
        s.SetLayer(P.Edge_Cuts)
        s.SetWidth(MM(0.1))
        board.Add(s)

    pinnet = load_nets(os.path.join(ROOT, "carrier.net"))
    nets = {}
    for name in sorted(set(pinnet.values())):
        ni = P.NETINFO_ITEM(board, name)
        board.Add(ni)
        nets[name] = ni

    fps = {}
    for ref, (lib_id, value, fpid, lcsc, dnp, in_bom, conns, desc) in PARTS.items():
        lib, name = fpid.split(":")
        path = (
            os.path.join(ROOT, "lib", "carrier.pretty")
            if lib == "carrier"
            else os.path.join(FPDIR, lib + ".pretty")
        )
        fp = P.FootprintLoad(path, name)
        fp.SetFPID(P.LIB_ID(lib, name))
        if ref == "F1":  # stock footprint names a STEP that KiCad does not ship
            m = P.FP_3DMODEL()
            m.m_Filename = "${KIPRJMOD}/lib/3d/Fuse_1812_box.wrl"
            fp.Models().clear()
            fp.Models().push_back(m)
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetPath(P.KIID_PATH("/" + ROOT_UUID + "/" + U("sym", ref)))
        fp.SetSheetname("/")
        fp.SetSheetfile("carrier.kicad_sch")
        x, y, rot, side = PLACE[ref]
        fp.SetPosition(V(x, y))
        board.Add(fp)
        if side == "B":
            fp.Flip(V(x, y), P.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetOrientationDegrees(rot)
        fp.GetField(P.FIELD_T_DESCRIPTION).SetText(desc)
        fp.SetDNP(dnp)
        fp.SetExcludedFromBOM(not in_bom)
        if dnp or not in_bom:
            fp.SetExcludedFromPosFiles(True)
        if lcsc:
            fld = P.PCB_FIELD(fp, P.FIELD_T_USER, "LCSC")
            fld.SetText(lcsc)
            fld.SetVisible(False)
            fld.SetLayer(P.F_Fab if side == "F" else P.B_Fab)
            fp.Add(fld)
        # refdes live on the fab layer: the board is too dense for silk refdes
        r = fp.Reference()
        r.SetLayer(P.F_Fab if side == "F" else P.B_Fab)
        r.SetTextSize(V(0.5, 0.5))
        r.SetTextThickness(MM(0.08))
        r.SetPosition(V(x, y))
        for pad in fp.Pads():
            nm = pinnet.get((ref, pad.GetNumber()))
            if nm:
                pad.SetNet(nets[nm])
        fps[ref] = fp

    # JLC assembly tooling holes (board-only NPTH footprints, not in the schematic/BOM/CPL)
    th_name = f"ToolingHole_NPTH_{D.TOOLING['drill']:g}mm"
    for i, (hx, hy) in enumerate(D.tooling_holes()):
        fp = P.FootprintLoad(os.path.join(ROOT, "lib", "carrier.pretty"), th_name)
        fp.SetFPID(P.LIB_ID("carrier", th_name))
        fp.SetReference(f"TH{i + 1}")
        fp.SetValue("TOOLING")
        fp.SetPosition(V(OX + hx, OY + hy))
        fp.SetBoardOnly(True)
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)
        fp.Reference().SetLayer(P.F_Fab)
        fp.Reference().SetTextSize(V(0.5, 0.5))
        fp.Reference().SetTextThickness(MM(0.08))
        fp.Reference().SetPosition(V(OX + hx, OY + hy))
        board.Add(fp)

    if stage == "place":
        for ref, fp in fps.items():
            for pad in fp.Pads():
                p = pad.GetPosition()
                print(
                    ref,
                    pad.GetNumber(),
                    f"{P.ToMM(p.x):.3f} {P.ToMM(p.y):.3f}",
                    pad.GetNetname(),
                )
    else:
        import routes

        routes.build(board, fps, nets, W, H)
        import silk

        print("silk items dropped:", silk.fit(board))
        P.ZONE_FILLER(board).Fill(board.Zones())

    out = os.path.join(ROOT, "carrier.kicad_pcb")
    P.SaveBoard(out, board)
    write_stackup(out)
    write_rules()
    print("saved", out)


def write_stackup(path):
    """Insert the JLC stackup into (setup ...): the bundled pcbnew API cannot edit it."""
    rows = ['(layer "F.SilkS" (type "Top Silk Screen"))', '(layer "F.Paste" (type "Top Solder Paste"))']
    for name, kind, t, mat, er in D.STACKUP:
        extra = f' (material "{mat}") (epsilon_r {er}) (loss_tangent 0.02)' if mat else ""
        rows.append(f'(layer "{name}" (type "{kind}") (thickness {t}){extra})')
    rows += [
        '(layer "B.Paste" (type "Bottom Solder Paste"))',
        '(layer "B.SilkS" (type "Bottom Silk Screen"))',
        '(copper_finish "None")',
        "(dielectric_constraints no)",
    ]
    block = "(stackup " + " ".join(rows) + ")"
    with open(path) as fh:
        txt = fh.read()
    if "(stackup" in txt:
        raise SystemExit("unexpected existing stackup in " + path)
    i = txt.index("(setup")
    txt = txt[: i + len("(setup")] + " " + block + txt[i + len("(setup") :]
    with open(path, "w") as fh:
        fh.write(txt)


def write_rules():
    """JLCPCB 4-layer capability (standard service) as project design rules."""
    pro = os.path.join(ROOT, "carrier.kicad_pro")
    try:
        with open(pro) as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        d = {}
    d.setdefault("meta", {"filename": "carrier.kicad_pro", "version": 3})
    b = d.setdefault("board", {}).setdefault("design_settings", {})
    b.setdefault("rules", {}).update(
        {
            **D.DRC_RULES,
            "min_silk_clearance": D.SILK["pad_clear"],
            "min_text_height": D.SILK["min_text_h"],
            "min_microvia_diameter": 0.2,
            "min_microvia_drill": 0.1,
            "solder_mask_to_copper_clearance": 0.0,
        }
    )
    b.setdefault("rule_severities", {}).update(D.DRC_SEVERITY)
    d.setdefault("net_settings", {})["classes"] = [
        {
            "name": "Default",
            "clearance": 0.15,
            "track_width": 0.2,
            "via_diameter": 0.6,
            "via_drill": 0.3,
            "microvia_diameter": 0.3,
            "microvia_drill": 0.1,
            "diff_pair_width": 0.2,
            "diff_pair_gap": 0.25,
            "diff_pair_via_gap": 0.25,
            "wire_width": 6,
            "bus_width": 12,
            "line_style": 0,
            "pcb_color": "rgba(0, 0, 0, 0.000)",
            "schematic_color": "rgba(0, 0, 0, 0.000)",
            "priority": 2147483647,
        }
    ]
    with open(pro, "w") as fh:
        json.dump(d, fh, indent=2)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "full")
