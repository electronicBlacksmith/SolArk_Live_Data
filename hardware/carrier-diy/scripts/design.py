"""Single source of truth for the carrier circuit: parts, nets, sources, checks.

Rev B-diy: the hand-soldered, lowest-cash variant. Both gen_sch.py and gen_pcb.py
import this. Pin keys are symbol pin numbers, which equal footprint pad numbers for
every part used here. Part claims and their sources are in CHANGES-revB.md.
"""

from __future__ import annotations

R0603 = "Resistor_SMD:R_0603_1608Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"

# Board outline: x0, y0, width (along the J1 edge), height (along the USB-C edge), mm.
BOARD = (100.0, 100.0, 29.0, 30.0)
MAX_OUTLINE = (29.0, 30.0)  # user limit (rev B decision 2)

# ref: (lib_id, value, footprint, LCSC, dnp, in_bom, {pin: net}, description)
PARTS = {
    "J1": (
        "Connector_Generic:Conn_01x06",
        "HARNESS",
        "carrier:WirePads_1x06_P2.54",
        "",
        False,
        False,
        {
            "1": "+12V_IN",
            "2": "GND",
            "3": None,
            "4": "GND",
            "5": "TAP_RESP",
            "6": "TAP_REQ",
        },
        "Direct-solder harness wire pads (in-line plug lives on the harness)",
    ),
    "F1": (
        "Device:Polyfuse",
        "0.5A 60V PPTC",
        "carrier:Fuse_1812_Bourns_MF-MSMF",
        "",
        False,
        True,
        {"1": "+12V_IN", "2": "+12V_F"},
        "1812 PPTC, 0.5 A hold",
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
        "carrier:D_SOD-123FL_Littelfuse_SMF",
        "",
        False,
        True,
        {"1": "+12V_P", "2": "GND"},
        "TVS 18 V standoff, unidirectional",
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
        C0603,
        "C14663",
        False,
        True,
        {"1": "+12V_P", "2": "GND"},
        "Input HF decoupling",
    ),
    "U2": (
        "carrier:LMR51610",
        "LMR51610YDBVR",
        "carrier:SOT-23-6_TI_DBV0006A",
        "",
        False,
        True,
        {"1": "CB", "2": "GND", "3": "FB", "4": "+12V_P", "5": "+12V_P", "6": "SW"},
        "4-65 V 1 A buck, 1.1 MHz",
    ),
    "C8": (
        "Device:C",
        "100nF 50V",
        C0603,
        "C14663",
        False,
        True,
        {"1": "CB", "2": "SW"},
        "Bootstrap",
    ),
    "L1": (
        "Device:L",
        "10uH",
        "carrier:L_Bourns_SRP4020TA",
        "",
        False,
        True,
        {"1": "SW", "2": "+5V_BUCK"},
        "10 uH shielded 4x4 mm, extended pads for iron",
    ),
    "C7": (
        "Device:C",
        "22uF 25V",
        "Capacitor_SMD:C_1206_3216Metric",
        "",
        False,
        True,
        {"1": "+5V_BUCK", "2": "GND"},
        "Buck output cap",
    ),
    "R13": (
        "Device:R",
        "20.5k 0.1%",
        R0603,
        "",
        False,
        True,
        {"1": "+5V_BUCK", "2": "FB"},
        "FB divider top, 0.1 % thin film",
    ),
    "R14": (
        "Device:R",
        "3.83k 0.1%",
        R0603,
        "",
        False,
        True,
        {"1": "FB", "2": "GND"},
        "FB divider bottom, 0.1 % thin film",
    ),
    "D2": (
        "Device:D_Schottky",
        "PMEG4030ER",
        "Diode_SMD:Nexperia_CFP3_SOD-123W",
        "",
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
        C0603,
        "C14663",
        False,
        True,
        {"1": "+5V_X", "2": "GND"},
        "XIAO 5 V HF decoupling",
    ),
    "R3": (
        "Device:R",
        "1k",
        R0603,
        "C21190",
        False,
        True,
        {"1": "TAP_RESP", "2": "BUF_IN_RESP"},
        "Tap series R, dongle pad 9 (inverter replies)",
    ),
    "R4": (
        "Device:R",
        "1k",
        R0603,
        "C21190",
        False,
        True,
        {"1": "TAP_REQ", "2": "BUF_IN_REQ"},
        "Tap series R, dongle pad 10 (dongle requests)",
    ),
    "R5": (
        "Device:R",
        "100k",
        R0603,
        "C25803",
        False,
        True,
        {"1": "+3V3", "2": "BUF_IN_RESP"},
        "Buffer input bias (UART idle high when J1 is off)",
    ),
    "R6": (
        "Device:R",
        "100k",
        R0603,
        "C25803",
        False,
        True,
        {"1": "+3V3", "2": "BUF_IN_REQ"},
        "Buffer input bias (UART idle high when J1 is off)",
    ),
    "U3": (
        "carrier:74LVC2G17",
        "SN74LVC2G17DBVR",
        "carrier:SOT-23-6_TI_DBV0006A",
        "",
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
        "RX-only Schmitt buffer: hardware one-way barrier",
    ),
    "C9": (
        "Device:C",
        "100nF 50V",
        C0603,
        "C14663",
        False,
        True,
        {"1": "+3V3", "2": "GND"},
        "U3 decoupling",
    ),
    "R7": (
        "Device:R",
        "1k",
        R0603,
        "C21190",
        False,
        True,
        {"1": "BUF_OUT_RESP", "2": "RX_RESP"},
        "Buffer-to-GPIO series R (limits contention during the GPIO1 boot glitch)",
    ),
    "R8": (
        "Device:R",
        "1k",
        R0603,
        "C21190",
        False,
        True,
        {"1": "BUF_OUT_REQ", "2": "RX_REQ"},
        "Buffer-to-GPIO series R (limits contention during the GPIO2 boot glitch)",
    ),
    "R12": (
        "Device:R",
        "1k",
        R0603,
        "C21190",
        True,
        True,
        {"1": "PROXY_GPIO8", "2": "PROXY_TX"},
        "DNP: proxy only (future, needs approval)",
    ),
    "JP1": (
        "Jumper:SolderJumper_2_Open",
        "OPEN",
        "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
        "",
        False,
        False,
        {"1": "PROXY_TX", "2": "PROXY_PAD"},
        "Open solder jumper, proxy only",
    ),
    "TP1": (
        "Connector:TestPoint",
        "PROXY",
        "TestPoint:TestPoint_Pad_D1.0mm",
        "",
        False,
        False,
        {"1": "PROXY_PAD"},
        "Proxy TX pad, not wired to the harness",
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
            "10": "PROXY_GPIO8",
            "11": None,
            "12": "+3V3",
            "13": "GND",
            "14": "+5V_X",
        },
        "Soldered on 2.54 mm header pins, XIAO flush on the carrier",
    ),
}

# Where each fitted part comes from.
#   fit: route (a) assignment. "jlc" = JLC Economic places it (Basic or Preferred
#        Extended only, so no feeder fee); "hand" = the user solders it. In route (b)
#        (OSH Park bare boards) the user fits everything.
#   dk / mpn: the Digi-Key part bought for route (b), and for the "hand" parts in (a).
#   jlc: JLC library status of the LCSC number in PARTS (None = not used at JLC).
SOURCE = {
    "F1": {"fit": "hand", "dk": "118-MF-MSMF050/60X-2CT-ND", "mpn": "Bourns MF-MSMF050/60X-2", "jlc": None},
    "D1": {"fit": "jlc", "dk": "B5819W-TPMSCT-ND", "mpn": "MCC B5819W-TP (JLC: CJ B5819W C8598)", "jlc": "Basic"},
    "TVS1": {"fit": "hand", "dk": "F5820CT-ND", "mpn": "Littelfuse SMF18A", "jlc": None},
    "C1": {"fit": "jlc", "dk": "13-CC1206KKX5R9BB106CT-ND", "mpn": "Yageo CC1206KKX5R9BB106 (JLC: Samsung CL31A106KBHNNNE)", "jlc": "Basic"},
    "C2": {"fit": "jlc", "dk": "311-1344-1-ND", "mpn": "Yageo CC0603KRX7R9BB104", "jlc": "Basic"},
    "U2": {"fit": "hand", "dk": "296-LMR51610YDBVRCT-ND", "mpn": "TI LMR51610YDBVR", "jlc": None},
    "C8": {"fit": "jlc", "dk": "311-1344-1-ND", "mpn": "Yageo CC0603KRX7R9BB104", "jlc": "Basic"},
    "L1": {"fit": "hand", "dk": "SRP4020TA-100MCT-ND", "mpn": "Bourns SRP4020TA-100M", "jlc": None},
    "C7": {"fit": "hand", "dk": "587-3246-1-ND", "mpn": "Taiyo Yuden TMK316BBJ226ML-T", "jlc": None},
    "R13": {"fit": "hand", "dk": "P20.5KDBCT-ND", "mpn": "Panasonic ERA-3AEB2052V", "jlc": None},
    "R14": {"fit": "hand", "dk": "P3.83KDBCT-ND", "mpn": "Panasonic ERA-3AEB3831V", "jlc": None},
    "D2": {"fit": "hand", "dk": "1727-5313-1-ND", "mpn": "Nexperia PMEG4030ER,115", "jlc": None},
    "C3": {"fit": "jlc", "dk": "445-6008-1-ND", "mpn": "TDK C3216X5R0J107M160AB (JLC: Samsung CL31A107MQHNNNE)", "jlc": "Basic"},
    "C4": {"fit": "jlc", "dk": "311-1344-1-ND", "mpn": "Yageo CC0603KRX7R9BB104", "jlc": "Basic"},
    "R3": {"fit": "jlc", "dk": "311-1.00KHRCT-ND", "mpn": "Yageo RC0603FR-071KL (JLC: Uniroyal 0603WAF1001T5E)", "jlc": "Basic"},
    "R4": {"fit": "jlc", "dk": "311-1.00KHRCT-ND", "mpn": "Yageo RC0603FR-071KL (JLC: Uniroyal 0603WAF1001T5E)", "jlc": "Basic"},
    "R5": {"fit": "jlc", "dk": "311-100KHRCT-ND", "mpn": "Yageo RC0603FR-07100KL (JLC: Uniroyal 0603WAF1003T5E)", "jlc": "Basic"},
    "R6": {"fit": "jlc", "dk": "311-100KHRCT-ND", "mpn": "Yageo RC0603FR-07100KL (JLC: Uniroyal 0603WAF1003T5E)", "jlc": "Basic"},
    "U3": {"fit": "hand", "dk": "296-SN74LVC2G17DBVRCT-ND", "mpn": "TI SN74LVC2G17DBVR", "jlc": None},
    "C9": {"fit": "jlc", "dk": "311-1344-1-ND", "mpn": "Yageo CC0603KRX7R9BB104", "jlc": "Basic"},
    "R7": {"fit": "jlc", "dk": "311-1.00KHRCT-ND", "mpn": "Yageo RC0603FR-071KL (JLC: Uniroyal 0603WAF1001T5E)", "jlc": "Basic"},
    "R8": {"fit": "jlc", "dk": "311-1.00KHRCT-ND", "mpn": "Yageo RC0603FR-071KL (JLC: Uniroyal 0603WAF1001T5E)", "jlc": "Basic"},
}

# Bought with the parts but not placed as a footprint (route a and b alike).
KIT = [
    {"dk": "S1011EC-40-ND", "mpn": "Sullins PRPC040SAAN-RC", "qty": "2x7 pins",
     "use": "U1 mount: 0.64 mm square header pins, plastic removed after soldering"},
    {"dk": "S7004-ND", "mpn": "Sullins PPTC061LFBN-RC", "qty": "1",
     "use": "Harness in-line plug (female); mates with a 6-pin PRPC040 section (plastic kept) on the J1 wires"},
    {"dk": "CF18JT10K0CT-ND", "mpn": "Stackpole CF18JT10K0", "qty": "2",
     "use": "REQUIRED harness series 10 k, 1/8 W axial: one in each tap wire, at the dongle pad 9 and pad 10 ends"},
]
# Item 7: worst-case 5 V window at the XIAO 5V pin, after D2. Sources in CHANGES-revB.md.
VBUS = {
    "vfb": (0.788, 0.812),  # LMR51610 VFB min/max
    "r_tol": 0.001,  # divider resistor tolerance
    "r_tc_ppm": 25,  # divider tempco, ppm/C
    "dT": 60,  # |T - 25 C| worst case (85 C board)
    "vout_window": (4.95, 5.25),  # buck output limits we design to
    "d2_vf_load_max": 0.50,  # D2 VF bound at 0.5 A, -40 C (datasheet: 0.44 max @1 A 25 C)
    "d2_vf_idle_min": 0.0,  # D2 VF floor at idle: 0 V (no credit taken for the diode)
    "pin_min": 4.40,  # USB 2.0 low-power port VBUS minimum
    "pin_max": 5.25,  # USB VBUS maximum
}
