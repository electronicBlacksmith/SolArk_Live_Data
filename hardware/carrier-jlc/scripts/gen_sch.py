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
    "D3": (60.96, 152.4),
    "D4": (60.96, 190.5),
    "R3": (91.44, 152.4),
    "R4": (91.44, 190.5),
    "R5": (116.84, 139.7),
    "R6": (116.84, 177.8),
    "U3": (152.4, 170.18),
    "C9": (152.4, 213.36),
    "R7": (190.5, 152.4),
    "R8": (190.5, 190.5),
    "U1": (254.0, 170.18),
}

NOTES = [
    (
        (25.4, 30.48),
        "POWER: harness 12 V -> F1 PPTC -> D1 reverse-polarity -> TVS1/C1/C2 -> U2 buck 5.065 V -> D2 backfeed block -> C3/C4 -> XIAO 5V",
    ),
    (
        (25.4, 116.84),
        "TAPS (PASSIVE ONLY): harness 10k (off-board) -> D3/D4 ESD -> R3/R4 1k -> U3 74LVC2G17 one-way Schmitt buffer -> R7/R8 1k -> XIAO RX.",
    ),
    (
        (25.4, 121.92),
        "No part lets a XIAO pin drive a tap line: U3 only conducts A -> Y. R5/R6 100k hold the buffer inputs high when the harness is idle.",
    ),
    (
        (25.4, 228.6),
        "12V OFF FOR USB: unplug the harness inline connector or the dongle before plugging a plain USB cable into the XIAO (XIAO 5V is fed through D2), or use a VBUS-blocking USB isolator.",
    ),
    (
        (25.4, 233.68),
        "J1 wire pads: 1 +12V, 2 GND (power), 3 GND (signal), 4 TAP pad 9 (inverter replies), 5 TAP pad 10 (dongle requests).",
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
                [Sym("date"), "2026-10-13"],
                [Sym("rev"), "B"],
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
