"""Generate carrier.kicad_sch from design.py (label-at-pin netlist style).

Run from hardware/carrier:  python3 scripts/gen_sch.py
"""

from __future__ import annotations

import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from design import PARTS
from sexp import Sym, dump, find, parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KLIB = os.environ.get(
    "KICAD_SYMBOL_DIR", "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"
)
NS = uuid.UUID("6f1c2a52-1f0e-4c39-9d2b-5a7e0c0a0001")
U = lambda *k: str(uuid.uuid5(NS, "/".join(k)))
ROOT_UUID = U("root")

POS = {  # ref: (x, y) on an A3 sheet, mm (multiples of 2.54)
    "J1": (30.48, 76.2),
    "F1": (66.04, 58.42),
    "D1": (96.52, 58.42),
    "TVS1": (124.46, 71.12),
    "C1": (142.24, 71.12),
    "C2": (160.02, 71.12),
    "U2": (200.66, 66.04),
    "C8": (238.76, 50.8),
    "L1": (256.54, 66.04),
    "C7": (279.4, 76.2),
    "R13": (297.18, 63.5),
    "R14": (297.18, 88.9),
    "D2": (325.12, 66.04),
    "C3": (350.52, 76.2),
    "C4": (370.84, 76.2),
    "R3": (91.44, 152.4),
    "R4": (91.44, 190.5),
    "R5": (129.54, 139.7),
    "R6": (129.54, 177.8),
    "C5": (154.94, 152.4),
    "C6": (154.94, 190.5),
    "U1": (228.6, 170.18),
    "R12": (304.8, 160.02),
    "JP1": (330.2, 160.02),
    "TP1": (355.6, 160.02),
}

NOTES = [
    (
        (25.4, 30.48),
        "POWER: harness 12 V -> F1 PPTC -> D1 reverse-polarity -> TVS1/C1/C2 -> U2 buck 5.04 V -> D2 backfeed block -> C3/C4 -> XIAO 5V",
    ),
    (
        (25.4, 116.84),
        "TAPS (PASSIVE ONLY): harness carries the off-board 10k series resistors; on-board R3/R4 1k are the second series element.",
    ),
    (
        (25.4, 121.92),
        "R5/R6 pull-ups and C5/C6 filters are DNP footprints. No default-populated part lets a XIAO pin drive a tap line.",
    ),
    (
        (269.24, 139.7),
        "DNP: proxy only. R12 + JP1 (open) + TP1 reserve a future GPIO8 TX path; TP1 is NOT wired to J1.",
    ),
    (
        (269.24, 144.78),
        "Fitting R12 and bridging JP1 requires an explicitly approved proxy-mode change.",
    ),
    (
        (25.4, 228.6),
        "NO USB WHILE INSTALLED without a USB isolator (XIAO 5V is fed from the inverter through D2).",
    ),
    (
        (25.4, 233.68),
        "J1 pinout: 1 +12V, 2 GND (power), 3 spare (NC), 4 GND (signal), 5 TAP pad 9 (inverter replies), 6 TAP pad 10 (dongle requests).",
    ),
]


def load_lib(path):
    with open(path) as fh:
        lib = parse(fh.read())
    return {e[1]: e for e in find(lib, "symbol")}


_LIBS: dict = {}


def lib_symbol(lib_id, cache=_LIBS):
    lib, name = lib_id.split(":")
    if lib not in cache:
        p = (
            os.path.join(ROOT, "lib", "carrier.kicad_sym")
            if lib == "carrier"
            else os.path.join(KLIB, lib + ".kicad_sym")
        )
        cache[lib] = load_lib(p)
    sym = cache[lib][name]
    if find(sym, "extends"):
        raise SystemExit(f"{lib_id} uses extends; not supported")
    return sym


def pins_of(sym):
    out = {}
    for unit in find(sym, "symbol"):
        for p in find(unit, "pin"):
            at = find(p, "at")[0]
            num = find(p, "number")[0][1]
            out[num] = (float(at[1]), float(at[2]), int(float(at[3])))
    return out


def prop(name, val, x, y, rot=0, hide=False):
    p = [Sym("property"), name, val, [Sym("at"), x, y, rot]]
    eff = [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]
    if hide:
        eff.append([Sym("hide"), Sym("yes")])
    p.append(eff)
    return p


def label(net, x, y, pin_ang, key):
    rot = (pin_ang + 180) % 360
    just = "left" if rot in (0, 90) else "right"
    return [
        Sym("label"),
        net,
        [Sym("at"), x, y, rot],
        [
            Sym("effects"),
            [Sym("font"), [Sym("size"), 1.27, 1.27]],
            [Sym("justify"), Sym(just), Sym("bottom")],
        ],
        [Sym("uuid"), U("label", key)],
    ]


def yn(b):
    return Sym("yes" if b else "no")


def main():
    items, libsyms, used = [], [], set()
    for ref, (lib_id, value, fp, lcsc, dnp, in_bom, conns, desc) in PARTS.items():
        sym = lib_symbol(lib_id)
        if lib_id not in used:
            used.add(lib_id)
            emb = [Sym("symbol"), lib_id] + sym[2:]
            libsyms.append(emb)
        X, Y = POS[ref]
        lp = {e[1]: e for e in find(sym, "property")}

        def at_of(k, lp=lp, X=X, Y=Y):
            a = find(lp[k], "at")[0]
            return X + float(a[1]), Y - float(a[2]), int(float(a[3]))

        rx, ry, rr = at_of("Reference")
        vx, vy, vr = at_of("Value")
        inst = [
            Sym("symbol"),
            [Sym("lib_id"), lib_id],
            [Sym("at"), X, Y, 0],
            [Sym("unit"), 1],
            [Sym("exclude_from_sim"), Sym("no")],
            [Sym("in_bom"), yn(in_bom)],
            [Sym("on_board"), Sym("yes")],
            [Sym("dnp"), yn(dnp)],
            [Sym("uuid"), U("sym", ref)],
            prop("Reference", ref, rx, ry, rr),
            prop("Value", value, vx, vy, vr),
            prop("Footprint", fp, X, Y, 0, True),
            prop("Datasheet", "", X, Y, 0, True),
            prop("Description", desc, X, Y, 0, True),
        ]
        if lcsc:
            inst.append(prop("LCSC", lcsc, X, Y, 0, True))
        pins = pins_of(sym)
        for num in pins:
            inst.append([Sym("pin"), num, [Sym("uuid"), U("pin", ref, num)]])
        inst.append(
            [
                Sym("instances"),
                [
                    Sym("project"),
                    "carrier",
                    [
                        Sym("path"),
                        "/" + ROOT_UUID,
                        [Sym("reference"), ref],
                        [Sym("unit"), 1],
                    ],
                ],
            ]
        )
        items.append(inst)
        if set(pins) != set(conns):
            raise SystemExit(f"{ref}: pins {sorted(pins)} != design {sorted(conns)}")
        for num, (px, py, pa) in pins.items():
            sx, sy = round(X + px, 4), round(Y - py, 4)
            net = conns[num]
            if net is None:
                items.append(
                    [
                        Sym("no_connect"),
                        [Sym("at"), sx, sy],
                        [Sym("uuid"), U("nc", ref, num)],
                    ]
                )
            else:
                items.append(label(net, sx, sy, pa, ref + "." + num))
    for i, ((x, y), t) in enumerate(NOTES):
        items.append(
            [
                Sym("text"),
                t,
                [Sym("exclude_from_sim"), Sym("no")],
                [Sym("at"), x, y, 0],
                [
                    Sym("effects"),
                    [Sym("font"), [Sym("size"), 1.524, 1.524]],
                    [Sym("justify"), Sym("left"), Sym("bottom")],
                ],
                [Sym("uuid"), U("note", str(i))],
            ]
        )
    sch = (
        [
            Sym("kicad_sch"),
            [Sym("version"), Sym("20250114")],
            [Sym("generator"), "eeschema"],
            [Sym("generator_version"), "9.0"],
            [Sym("uuid"), ROOT_UUID],
            [Sym("paper"), "A3"],
            [
                Sym("title_block"),
                [Sym("title"), "SolArk XIAO tap carrier"],
                [Sym("date"), "2026-10-12"],
                [Sym("rev"), "A"],
                [Sym("company"), "SolArk_Live_Data"],
                [
                    Sym("comment"),
                    1,
                    "Passive Modbus tap carrier for XIAO ESP32S3 Plus (generated by scripts/gen_sch.py)",
                ],
            ],
            [Sym("lib_symbols")] + libsyms,
        ]
        + items
        + [
            [Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]],
            [Sym("embedded_fonts"), Sym("no")],
        ]
    )
    with open(os.path.join(ROOT, "carrier.kicad_sch"), "w") as fh:
        fh.write(dump(sch) + "\n")
    print("wrote carrier.kicad_sch")


if __name__ == "__main__":
    main()
