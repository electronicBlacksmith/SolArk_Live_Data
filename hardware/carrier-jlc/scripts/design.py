"""Single source of truth for the carrier circuit: parts, nets, LCSC numbers.

Both gen_sch.py and gen_pcb.py import this. Pin keys are symbol pin numbers,
which equal footprint pad numbers for every part used here.
"""

from __future__ import annotations

R0402 = "Resistor_SMD:R_0402_1005Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"

# --- Board and fab parameters (mm). Change here; generators and tests follow. ---
BOARD_W, BOARD_H = 27.0, 27.0  # outline (x along the J1/buck edge, y along USB-C edge)
OUTLINE_MAX = (29.0, 30.0)  # user limit
JLC_PTH_TOL = (0.13, 0.08)  # finished PTH +/-, jlcpcb.com/capabilities/pcb-capabilities
JLC_MIN_RING = 0.20  # PTH ring, JLC's *recommended* multilayer 1 oz value (same page)

# JLC multilayer, 1 oz outer, published minimums as KiCad rule keys
# (https://jlcpcb.com/capabilities/pcb-capabilities, read 2026-10-14 [V]). Where the page has
# several values for one KiCad rule, the strictest is used.
JLC_MIN = {
    "min_clearance": 0.15,  # SMD pad to pad, different nets (track spacing is 0.09)
    "min_track_width": 0.09,  # multilayer 1 oz
    "min_via_diameter": 0.25,  # "Min. Via hole size/diameter 0.15/0.25mm"
    "min_via_annular_width": 0.15,  # PTH ring, multilayer 1 oz absolute minimum (vias: 0.05)
    "min_through_hole_diameter": 0.15,  # via / PTH hole
    "min_hole_clearance": 0.30,  # inner-layer PTH hole to copper (PTH to track 0.28, via 0.2)
    "min_hole_to_hole": 0.45,  # pad hole to hole (via hole to hole 0.2)
    "min_copper_edge_clearance": 0.20,  # copper to routed board edge
    "min_text_height": 1.0,  # silkscreen text height
    "min_text_thickness": 0.15,  # silkscreen line width
}
# Project DRC minimums written to carrier.kicad_pro (gen_pcb.write_rules). Each is >= JLC_MIN
# (a test checks); some are stricter on purpose (via 0.45 avoids JLC's small-via surcharge).
DRC_RULES = {
    "min_clearance": 0.15,
    "min_track_width": 0.127,
    "min_via_diameter": 0.45,
    "min_via_annular_width": 0.15,
    "min_through_hole_diameter": 0.2,
    "min_hole_clearance": 0.30,
    "min_hole_to_hole": 0.5,
    "min_copper_edge_clearance": 0.3,
    "min_text_thickness": 0.15,
}

# JLC Economic PCBA tooling holes, "Added by Customer". JLC spec (jlcpcb.com/help/article/
# how-to-add-tooling-holes-for-pcb-assembly-order, read 2026-10-14 [V]): 1.152 mm round
# non-plated, 0.148 mm solder mask expansion, two or three holes in opposite corners, as far
# apart as practical, on empty space away from traces. The page gives no edge distance or
# copper clearance, so: min_edge = hole edge to board edge, borrowed from JLC's only
# hole-to-edge rule (castellated, >= 1 mm, pcb-capabilities page) [I]; copper_clear = hole
# edge to any pad/track/via, above JLC's NPTH-to-track 0.2 mm [V] for margin [I].
# Corners: "TL" "TR" "BL" "BR" (x along BOARD_W, y down). Only the top corners are free:
# BL holds J1 pad 1 (+12V_IN) and BR holds C3 (see OPEN-ITEMS.md).
TOOLING = {
    "drill": 1.152,
    "mask_margin": 0.148,
    "edge_inset": 2.0,  # hole centre to each adjacent board edge
    "min_edge": 1.0,
    "copper_clear": 0.5,
    "corners": ("TL", "TR"),
}

# DRC checks downgraded in carrier.kicad_pro. TH2 (top-right) lies under the XIAO, whose U1
# courtyard covers the whole top-right of the board; an NPTH has no copper and the fixture pin
# is used only during SMT, before the XIAO is hand-fitted. A test pins this to tooling holes.
DRC_SEVERITY = {
    "npth_inside_courtyard": "ignore",
    # gen_pcb trims stock footprints' silk on the board copy (JLC legend rules), so the board
    # copy differs from the library by design.
    "lib_footprint_mismatch": "ignore",
    "silk_over_copper": "error",
    "silk_overlap": "error",
    "silk_edge_clearance": "error",
    "text_height": "error",
    "text_thickness": "error",
}

# Silkscreen, JLC legend rules (jlcpcb.com/capabilities/pcb-capabilities, read 2026-10-14
# [V]): line >= 0.15 mm, text height >= 1.0 mm, pad to silkscreen >= 0.15 mm. The page gives
# no silk-to-hole or silk-to-edge value; the pad value is used for both [I]. gen_pcb widens
# every silk stroke to min_width and trims footprint silk lines back from pads, holes and the
# edge; pieces shorter than min_piece are dropped. check_silk.py fails the build on anything
# left and confirms each ref in `marks` keeps silk next to pad 1 (pin-1 / cathode mark).
SILK = {
    "min_width": 0.15,
    "min_text_h": 1.0,
    "pad_clear": 0.15,
    "hole_clear": 0.15,
    "edge_clear": 0.15,
    "min_piece": 0.3,
    "step": 0.02,  # trim resolution along a line
    "mark_dist": 1.0,  # pin-1 / cathode mark: silk within this of pad 1's edge
    "marks": ("U2", "U3", "D1", "D2", "TVS1"),  # U1's pin-1 mark is its square pad (test)
}


def tooling_holes() -> list[tuple[float, float]]:
    """Tooling hole centres relative to the board's top-left corner (mm)."""
    i = TOOLING["edge_inset"]
    xy = {"L": i, "R": BOARD_W - i, "T": i, "B": BOARD_H - i}
    return [(xy[c[1]], xy[c[0]]) for c in TOOLING["corners"]]


# XIAO mount: 2.54 mm male header, 0.64 mm square posts (Sullins PRPC040SAAN-RC,
# drawing 11635 rev B: post 0.64 sq, recommended hole 1.00, insulator 2.50).
HEADER = {"post": 0.64, "rec_hole": 1.00, "pitch": 2.54, "insulator": 2.50}
XIAO_PIN_DRILL, XIAO_PIN_PAD = 1.10, 1.70  # finished 1.02-1.23, ring >= 0.235

# Stack (mm). gap = XIAO underside above carrier top: HEADER["insulator"] with the
# plastic spacer left on, or ~0.1 (Kapton shim) with it slid off. xiao_thk = XIAO
# Plus PCB + tallest part (unmeasured, see OPEN-ITEMS.md). tail = trimmed pin below.
MOUNT = {"gap": HEADER["insulator"], "xiao_thk": 4.9, "tail": 0.8}
HEIGHT_MAX = 9.0  # user design limit: carrier bottom (tail) to XIAO top
# Spacer-off mount: the top THT ring clears XIAO Plus underside pads 15-23 by only 0.049 mm
# (VERIFY-revB.md), so a polyimide (Kapton) shim between the boards is mandatory.
# min = one layer of 1 mil film tape with adhesive [I]; max keeps the stack <= 7.5 mm,
# 1.5 mm under HEIGHT_MAX for the unmeasured XIAO height [I].
SHIM = {"min": 0.06, "max": 0.2}

# Hand-fit kit: bought from Digi-Key, not placed by JLC. per_board = pieces per carrier.
# Read 2026-10-14 [V]; prices and stock are in PRICING.md.
KIT = [
    {
        "dk": "S1011EC-40-ND",
        "mpn": "Sullins PRPC040SAAN-RC",
        "per_board": 14,
        "thk": None,
        "use": "U1 mount: 0.64 mm square header pins (one 40-pin strip covers 2 boards)",
    },
    {
        "dk": "4393-PPTA-1/2-ND",
        "mpn": "Bertech PPTA-1/2",
        "per_board": 1,
        "thk": 0.064,
        "use": "Shim: polyimide tape, 1/2 in x 36 yd, 0.064 mm total; one roll covers every board",
    },
    {
        "dk": "CF14JT10K0CT-ND",
        "mpn": "Stackpole CF14JT10K0",
        "per_board": 2,
        "thk": None,
        "use": "Harness series 10k, 5 %, 1/4 W axial, at the dongle end of each tap wire",
    },
]
# JLC04161H-7628, 1.6 mm 4-layer (jlcpcb.com/impedance, read 2026-10-13):
# (layer, type, thickness mm, material, epsilon_r). Prepreg 7628 er 4.4, core er 4.6,
# solder mask er 3.8.
STACKUP = [
    ("F.Mask", "Top Solder Mask", 0.01524, "LPI", 3.8),
    ("F.Cu", "copper", 0.035, None, None),
    ("dielectric 1", "prepreg", 0.2104, "7628", 4.4),
    ("In1.Cu", "copper", 0.0152, None, None),
    ("dielectric 2", "core", 1.065, "FR4", 4.6),
    ("In2.Cu", "copper", 0.0152, None, None),
    ("dielectric 3", "prepreg", 0.2104, "7628", 4.4),
    ("B.Cu", "copper", 0.035, None, None),
    ("B.Mask", "Bottom Solder Mask", 0.01524, "LPI", 3.8),
]

# CPL rotation offsets added to KiCad's rotation, first regex match on the footprint
# name wins. From matthewlai/JLCKicadTools cpl_rotations_db.csv ("^SOT-23" -90,
# "^SOT-363" 180) [inferred]: confirm every part in JLC's placement preview.
CPL_ROTATION = [
    (r"^SOT-23", -90),
    (r"^SOT363-2", 180),
]  # JLC minimum silkscreen text height

# Harness: wires soldered straight into plated holes (26-28 AWG).
HARNESS = {"pitch": 2.54, "drill": 1.0, "pad": 1.7}

# Buck output window. LMR51610 datasheet (SLUSEW3): Vfb 0.788/0.800/0.812 V,
# PFM Vout regulation -1.5 %/+2.5 %. temp_span_k = resistor TC excursion used.
BUCK = {"vfb_nom": 0.800, "vfb_min": 0.788, "pfm_hi": 0.025, "temp_span_k": 100}
# XIAO 5 V pin window (USB VBUS 4.40-5.25 V) and D2 PMEG4030ER VF max @ 1 A, 25 C.
XIAO_5V = {"vmin": 4.40, "vmax": 5.25, "d2_vf_max": 0.44}

# One-way parts: {ref: {input pin: output pin}} (signal crosses only A -> Y).
BUFFERS = {"U3": {"1": "6", "3": "4"}}

# JLC library status read 2026-10-13 from the JLC parts API
# (selectSmtComponentList). Preferred = Extended without the feeder fee.
JLC_STATUS = {
    "C462518": "Extended",  # F1
    "C8598": "Basic",  # D1
    "C19077512": "Preferred",  # TVS1
    "C13585": "Basic",  # C1
    "C307331": "Basic",  # C2 C4 C8 C9
    "C22427220": "Extended",  # U2
    "C167879": "Extended",  # L1
    "C45783": "Basic",  # C7
    "C728559": "Extended",  # R13
    "C705638": "Extended",  # R14
    "C389355": "Extended",  # D2
    "C15008": "Basic",  # C3
    "C11702": "Basic",  # R3 R4 R7 R8
    "C25741": "Basic",  # R5 R6
    "C7420372": "Preferred",  # D3 D4
    "C80500": "Extended",  # U3
}

# ref: (lib_id, value, footprint, LCSC, dnp, in_bom, {pin: net}, description)
PARTS = {
    "J1": (
        "Connector_Generic:Conn_01x05",
        "HARNESS",
        "carrier:Harness_WirePads_1x05_P2.54",
        "",
        False,
        False,
        {
            "1": "+12V_IN",
            "2": "GND",
            "3": "GND",
            "4": "TAP_RESP",
            "5": "TAP_REQ",
        },
        "Harness wires soldered into plated holes (no connector)",
    ),
    "F1": (
        "Device:Polyfuse",
        "0.5A 60V PPTC",
        "Fuse:Fuse_1812_4532Metric",
        "C462518",
        False,
        True,
        {"1": "+12V_IN", "2": "+12V_F"},
        "SMD1812P050TF/60",
    ),
    "D1": (
        "Device:D_Schottky",
        "B5819W",
        "Diode_SMD:D_SOD-123",
        "C8598",
        False,
        True,
        {"1": "+12V_P", "2": "+12V_F"},
        "Reverse-polarity Schottky 40 V 1 A",
    ),
    "TVS1": (
        "Device:D_Zener",
        "SMF18A",
        "Diode_SMD:D_SOD-123F",
        "C19077512",
        False,
        True,
        {"1": "+12V_P", "2": "GND"},
        "TVS 18 V standoff, unidirectional (Hongjiacheng SMF18A)",
    ),
    "C1": (
        "Device:C",
        "10uF 50V",
        "Capacitor_SMD:C_1206_3216Metric",
        "C13585",
        False,
        True,
        {"1": "+12V_P", "2": "GND"},
        "Input bulk X5R",
    ),
    "C2": (
        "Device:C",
        "100nF 50V",
        C0402,
        "C307331",
        False,
        True,
        {"1": "+12V_P", "2": "GND"},
        "Input HF decoupling",
    ),
    "U2": (
        "carrier:LMR51610",
        "LMR51610YDBVR",
        "Package_TO_SOT_SMD:SOT-23-6",
        "C22427220",
        False,
        True,
        {"1": "CB", "2": "GND", "3": "FB", "4": "+12V_P", "5": "+12V_P", "6": "SW"},
        "4-65 V 1 A buck, 1.1 MHz",
    ),
    "C8": (
        "Device:C",
        "100nF 50V",
        C0402,
        "C307331",
        False,
        True,
        {"1": "CB", "2": "SW"},
        "Bootstrap",
    ),
    "L1": (
        "Device:L",
        "10uH 1.6A",
        "Inductor_SMD:L_Changjiang_FNR4030S",
        "C167879",
        False,
        True,
        {"1": "SW", "2": "+5V_BUCK"},
        "FNR4030S100MT shielded 4x4x3 mm",
    ),
    "C7": (
        "Device:C",
        "22uF 25V",
        "Capacitor_SMD:C_0805_2012Metric",
        "C45783",
        False,
        True,
        {"1": "+5V_BUCK", "2": "GND"},
        "Buck output cap",
    ),
    "R13": (
        "Device:R",
        "33k 0.1% 25ppm",
        R0402,
        "C728559",
        False,
        True,
        {"1": "+5V_BUCK", "2": "FB"},
        "FB divider top",
    ),
    "R14": (
        "Device:R",
        "6.19k 0.1% 25ppm",
        R0402,
        "C705638",
        False,
        True,
        {"1": "FB", "2": "GND"},
        "FB divider bottom: Vout = 0.8*(1+33/6.19) = 5.065 V",
    ),
    "D2": (
        "Device:D_Schottky",
        "PMEG4030ER",
        "Diode_SMD:Nexperia_CFP3_SOD-123W",
        "C389355",
        False,
        True,
        {"1": "+5V_X", "2": "+5V_BUCK"},
        "Backfeed-blocking Schottky 40 V 3 A",
    ),
    "C3": (
        "Device:C",
        "100uF 6.3V",
        "Capacitor_SMD:C_1206_3216Metric",
        "C15008",
        False,
        True,
        {"1": "+5V_X", "2": "GND"},
        "XIAO 5 V bulk",
    ),
    "C4": (
        "Device:C",
        "100nF 50V",
        C0402,
        "C307331",
        False,
        True,
        {"1": "+5V_X", "2": "GND"},
        "XIAO 5 V HF decoupling",
    ),
    "D3": (
        "Device:D_TVS",
        "H5VL10B",
        "carrier:DFN1006-2L_H5VL10B",
        "C7420372",
        False,
        True,
        {"1": "TAP_RESP", "2": "GND"},
        "Bidirectional 5 V ESD, tap pad 9",
    ),
    "D4": (
        "Device:D_TVS",
        "H5VL10B",
        "carrier:DFN1006-2L_H5VL10B",
        "C7420372",
        False,
        True,
        {"1": "TAP_REQ", "2": "GND"},
        "Bidirectional 5 V ESD, tap pad 10",
    ),
    "R3": (
        "Device:R",
        "1k",
        R0402,
        "C11702",
        False,
        True,
        {"1": "TAP_RESP", "2": "BUF_IN_RESP"},
        "Tap series R, dongle pad 9 (inverter replies)",
    ),
    "R4": (
        "Device:R",
        "1k",
        R0402,
        "C11702",
        False,
        True,
        {"1": "TAP_REQ", "2": "BUF_IN_REQ"},
        "Tap series R, dongle pad 10 (dongle requests)",
    ),
    "R5": (
        "Device:R",
        "100k",
        R0402,
        "C25741",
        False,
        True,
        {"1": "+3V3", "2": "BUF_IN_RESP"},
        "Buffer input pull-up (idle high)",
    ),
    "R6": (
        "Device:R",
        "100k",
        R0402,
        "C25741",
        False,
        True,
        {"1": "+3V3", "2": "BUF_IN_REQ"},
        "Buffer input pull-up (idle high)",
    ),
    "U3": (
        "carrier:74LVC2G17",
        "74LVC2G17GW",
        "carrier:SOT363-2_Nexperia",
        "C80500",
        False,
        True,
        {
            "1": "BUF_IN_RESP",
            "2": "GND",
            "3": "BUF_IN_REQ",
            "4": "BUF_OUT_REQ",
            "5": "+3V3",
            "6": "BUF_OUT_RESP",
        },
        "Dual Schmitt buffer, 5.5 V-tolerant inputs, Ioff: one-way tap isolation",
    ),
    "C9": (
        "Device:C",
        "100nF 50V",
        C0402,
        "C307331",
        False,
        True,
        {"1": "+3V3", "2": "GND"},
        "U3 decoupling",
    ),
    "R7": (
        "Device:R",
        "1k",
        R0402,
        "C11702",
        False,
        True,
        {"1": "BUF_OUT_RESP", "2": "RX_RESP"},
        "Buffer output series R",
    ),
    "R8": (
        "Device:R",
        "1k",
        R0402,
        "C11702",
        False,
        True,
        {"1": "BUF_OUT_REQ", "2": "RX_REQ"},
        "Buffer output series R",
    ),
    "U1": (
        "carrier:XIAO_ESP32S3",
        "XIAO_ESP32S3_Plus",
        "carrier:XIAO_ESP32S3_Header_THT",
        "",
        False,
        False,
        {
            "1": "RX_RESP",
            "2": "RX_REQ",
            "3": None,
            "4": None,
            "5": None,
            "6": None,
            "7": None,
            "8": None,
            "9": None,
            "10": None,
            "11": None,
            "12": "+3V3",
            "13": "GND",
            "14": "+5V_X",
        },
        "Soldered on 2.54 mm male header pins (user-fitted)",
    ),
}
