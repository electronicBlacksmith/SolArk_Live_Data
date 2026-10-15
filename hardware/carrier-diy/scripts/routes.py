"""Hand-planned routing, zones and silkscreen for the carrier (called by gen_pcb.py).

Layer use: F.Cu parts + short routes + GND pour; In1.Cu solid GND; In2.Cu tap/sense
signals + GND pour; B.Cu +12V_P feed, +3V3, DNP options + GND pour.
"""

from __future__ import annotations

import pcbnew as P
from design import BOARD

MM = P.FromMM
LAYER = {"F": P.F_Cu, "In1": P.In1_Cu, "In2": P.In2_Cu, "B": P.B_Cu}
VIA_D, VIA_DRILL = 0.6, 0.3
W_SIG, W_PWR, W_SW = 0.2, 0.5, 0.6


# ref: (x, y, rotation_deg, side); side "B" = bottom (DNP / bare-copper parts only)
PLACE = {
    "U1": (116.935, 109.4, 0, "F"),
    "J1": (107.65, 128.6, 180, "F"),
    # tap chain, left strip: RESP column x 101.6, REQ column x 105.0, J1 -> XIAO upward
    "R3": (101.6, 120.4, 90, "F"),
    "R4": (105.0, 120.4, 90, "F"),
    "R5": (101.6, 117.0, 270, "F"),
    "R6": (105.0, 117.0, 270, "F"),
    "U3": (103.3, 111.9, 90, "F"),
    "C9": (103.3, 108.4, 0, "F"),
    "R7": (101.6, 105.0, 90, "F"),
    "R8": (105.0, 105.0, 90, "F"),
    # input protection band, J1 pin 1 -> F1 -> D1 -> TVS1
    "TVS1": (110.0, 119.65, 180, "F"),
    "D1": (110.0, 122.05, 180, "F"),
    "F1": (110.0, 125.25, 180, "F"),
    # buck
    "C1": (114.75, 124.4, 90, "F"),
    "U2": (117.75, 124.6, 270, "F"),
    "C8": (120.3, 124.6, 270, "F"),
    "L1": (123.4, 125.4, 90, "F"),
    "C3": (127.6, 125.3, 270, "F"),
    "C2": (117.75, 127.9, 0, "F"),
    "R14": (114.4, 120.0, 90, "F"),
    "R13": (116.0, 120.0, 270, "F"),
    "C7": (119.2, 120.0, 180, "F"),
    "D2": (123.9, 119.8, 180, "F"),
    "C4": (127.4, 120.6, 270, "F"),
    # bottom side: bare-copper proxy reservation only (no bottom assembly)
    "R12": (113.0, 113.8, 180, "B"),
    "JP1": (109.7, 113.8, 180, "B"),
    "TP1": (106.8, 113.8, 0, "B"),
}


def V(x, y):
    return P.VECTOR2I(MM(x), MM(y))


class Router:
    def __init__(self, board, fps, nets):
        self.b, self.fps, self.nets = board, fps, nets

    def net(self, name):
        return self.nets["/" + name]

    def pad(self, ref, num):
        """Position of the first pad `num` of `ref` (THT pad first for U1)."""
        for p in self.fps[ref].Pads():
            if p.GetNumber() == str(num):
                q = p.GetPosition()
                return P.ToMM(q.x), P.ToMM(q.y)
        raise KeyError((ref, num))

    def track(self, net, layer, pts, w=W_SIG):
        pts = [self.pad(*p) if isinstance(p[0], str) else p for p in pts]
        for a, c in zip(pts, pts[1:]):  # noqa: RUF007 - KiCad bundles Python 3.9
            t = P.PCB_TRACK(self.b)
            t.SetStart(V(*a))
            t.SetEnd(V(*c))
            t.SetWidth(MM(w))
            t.SetLayer(LAYER[layer])
            t.SetNet(self.net(net))
            self.b.Add(t)

    def via(self, net, x, y):
        v = P.PCB_VIA(self.b)
        v.SetViaType(P.VIATYPE_THROUGH)
        v.SetPosition(V(x, y))
        v.SetWidth(MM(VIA_D))
        v.SetDrill(MM(VIA_DRILL))
        v.SetNet(self.net(net))
        self.b.Add(v)

    def zone(self, net, layer, inset=0.0, prio=0):
        z = P.ZONE(self.b)
        z.SetLayer(LAYER[layer])
        z.SetNet(self.net(net))
        o = z.Outline()
        o.NewOutline()
        x0, y0, w, h = BOARD
        for x, y in [
            (x0 + inset, y0 + inset),
            (x0 + w - inset, y0 + inset),
            (x0 + w - inset, y0 + h - inset),
            (x0 + inset, y0 + h - inset),
        ]:
            o.Append(MM(x), MM(y))
        z.SetLocalClearance(MM(0.2))
        z.SetMinThickness(MM(0.2))
        z.SetPadConnection(P.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(0.2))
        z.SetThermalReliefSpokeWidth(MM(0.3))
        z.SetIslandRemovalMode(P.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetAssignedPriority(prio)
        self.b.Add(z)

    def text(self, s, x, y, layer, size=0.8, thick=0.15, angle=0):
        t = P.PCB_TEXT(self.b)
        t.SetText(s)
        t.SetPosition(V(x, y))
        t.SetLayer(layer)
        t.SetTextSize(V(size, size))
        t.SetTextThickness(MM(thick))
        t.SetTextAngleDegrees(angle)
        if layer in (P.B_SilkS, P.B_Fab):
            t.SetMirrored(True)
        self.b.Add(t)

    def rect(self, layer, x0, y0, x1, y1, w=0.15):
        s = P.PCB_SHAPE(self.b)
        s.SetShape(P.SHAPE_T_RECT)
        s.SetStart(V(x0, y0))
        s.SetEnd(V(x1, y1))
        s.SetLayer(layer)
        s.SetWidth(MM(w))
        self.b.Add(s)


def build(board, fps, nets):
    r = Router(board, fps, nets)
    T, S = r.track, W_SIG

    # ---- taps: J1 -> R3/R4 (REQ crosses under RESP on In2) ------------------
    T("TAP_RESP", "F", [("J1", 5), (103.84, 127.4), (103.3, 126.86), (103.3, 122.6),
                        (101.6, 121.9), ("R3", 1)], S)
    T("TAP_REQ", "F", [("J1", 6), (100.9, 126.9)], S)
    r.via("TAP_REQ", 100.9, 126.9)
    T("TAP_REQ", "In2", [(100.9, 126.9), (101.4, 126.4), (105.9, 126.4)], S)
    r.via("TAP_REQ", 105.9, 126.4)
    T("TAP_REQ", "F", [(105.9, 126.4), (105.9, 122.3), (105.0, 121.6), ("R4", 1)], S)

    # ---- buffer inputs: series R -> bias R -> U3 (around the pull-up pads) --
    T("BUF_IN_RESP", "F", [("R3", 2), ("R5", 2), (100.7, 117.825), (100.7, 114.3),
                           (102.35, 114.3), ("U3", 1)], S)
    T("BUF_IN_REQ", "F", [("R4", 2), ("R6", 2), (105.9, 117.825), (105.9, 114.3),
                          (104.25, 114.3), ("U3", 3)], S)
    T("GND", "F", [("U3", 2), (103.3, 114.4)], 0.3)
    r.via("GND", 103.3, 114.4)

    # ---- +3V3: XIAO pin 12 -> In2 -> bias R, U3 VCC, C9 ----------------------
    T("+3V3", "F", [("R5", 1), ("R6", 1)], 0.25)
    r.via("+3V3", 103.3, 116.175)
    T("+3V3", "In2", [(103.3, 116.175), (103.9, 115.6), (118.9, 115.6), ("U1", 12)], 0.25)
    T("+3V3", "In2", [(106.3, 115.6), (106.3, 109.6), (103.3, 109.6)], 0.25)
    r.via("+3V3", 103.3, 109.6)
    T("+3V3", "F", [("U3", 5), (103.3, 109.6), ("C9", 1)], 0.25)
    T("GND", "F", [("C9", 2), (104.1, 107.3)], 0.3)
    r.via("GND", 104.1, 107.3)

    # ---- buffer outputs -> R7/R8 -> In2 under the XIAO -> D0/D1 --------------
    T("BUF_OUT_RESP", "F", [("U3", 6), (101.6, 109.85), ("R7", 1)], S)
    T("BUF_OUT_REQ", "F", [("U3", 4), (105.0, 109.85), ("R8", 1)], S)
    T("RX_RESP", "F", [("R7", 2), (101.6, 101.0)], S)
    r.via("RX_RESP", 101.6, 101.0)
    T("RX_RESP", "In2", [(101.6, 101.0), (101.9, 100.7), (123.9, 100.7), ("U1", 1)], S)
    T("RX_REQ", "F", [("R8", 2), (105.0, 103.3)], S)
    r.via("RX_REQ", 105.0, 103.3)
    T("RX_REQ", "In2", [(105.0, 103.3), (121.4, 103.3), ("U1", 2)], S)

    # ---- bottom: proxy reservation (DNP R12, open JP1, bare TP1) -------------
    T("PROXY_GPIO8", "B", [("U1", 10), (114.395, 114.6), ("R12", 1)], S)
    T("PROXY_TX", "B", [("R12", 2), ("JP1", 1)], S)
    T("PROXY_PAD", "B", [("JP1", 2), ("TP1", 1)], S)

    # ---- input protection: J1.1 -> F1 -> D1 -> TVS1 / buck -------------------
    T("+12V_IN", "F", [("F1", 1), (112.9, 126.9), (114.0, 128.0), ("J1", 1)], W_PWR)
    T("+12V_F", "F", [("F1", 2), (107.61, 123.4), (108.35, 122.66), ("D1", 2)], W_PWR)
    T("+12V_P", "F", [("D1", 1), ("TVS1", 1)], W_PWR)
    T("+12V_P", "F", [("D1", 1), (112.9, 122.05)], W_PWR)
    r.via("+12V_P", 112.9, 122.05)
    T("+12V_P", "B", [(112.9, 122.05), (112.9, 127.1), (115.9, 127.1)], W_PWR)
    r.via("+12V_P", 115.9, 127.1)
    T("+12V_P", "F", [("C1", 1), ("U2", 4), ("U2", 5)], 0.4)
    T("+12V_P", "F", [(115.9, 127.1), (115.9, 125.9)], W_PWR)
    T("+12V_P", "F", [(115.9, 127.1), (116.3, 127.9), ("C2", 1)], 0.4)
    T("GND", "F", [("TVS1", 2), (107.3, 119.65)], W_PWR)
    r.via("GND", 107.3, 119.65)

    # ---- buck core -----------------------------------------------------------
    T("GND", "F", [("C1", 2), (114.75, 121.85)], 0.4)
    r.via("GND", 114.75, 121.85)
    T("GND", "F", [("R14", 2), (113.3, 119.175)], 0.3)
    r.via("GND", 113.3, 119.175)
    T("FB", "F", [("R14", 1), ("R13", 2), (116.8, 121.6), ("U2", 3)], S)
    T("GND", "F", [("U2", 2), (117.75, 120.9), ("C7", 2)], 0.4)
    r.via("GND", 117.75, 122.2)
    T("CB", "F", [("U2", 1), (119.2, 123.3), (119.7, 123.8), ("C8", 1)], 0.3)
    T("SW", "F", [("U2", 6), (119.4, 125.425), ("C8", 2), (121.6, 126.7), ("L1", 1)], W_SW)
    T("GND", "F", [("C2", 2), (119.6, 128.2)], 0.3)
    r.via("GND", 119.6, 128.2)
    T("+5V_BUCK", "F", [("L1", 2), (122.5, 122.6), ("D2", 2)], W_SW)
    T("+5V_BUCK", "F", [("C7", 1), ("D2", 2)], W_SW)
    T("+5V_BUCK", "F", [("R13", 1), (116.0, 118.55), (120.675, 118.55), ("C7", 1)], S)
    # ---- +5V_X: D2 cathode -> C4, C3, XIAO 5V --------------------------------
    T("+5V_X", "F", [("D2", 1), ("C4", 1)], W_PWR)
    T("+5V_X", "F", [("D2", 1), (125.3, 118.2), (124.555, 117.4), ("U1", 14)], W_SW)
    T("+5V_X", "F", [("D2", 1), (126.2, 120.7), (126.2, 123.4), ("C3", 1)], W_PWR)
    T("GND", "F", [("C4", 2), (127.4, 122.45)], 0.3)
    r.via("GND", 127.4, 122.45)
    T("GND", "F", [("C3", 2), (127.6, 127.9)], 0.4)
    r.via("GND", 127.6, 127.9)

    # ---- GND stitching ---------------------------------------------------------
    for x, y in [(110.0, 106.0), (115.0, 106.0), (120.0, 106.0), (125.0, 106.0),
                 (112.0, 111.0), (118.0, 111.0), (124.0, 111.0), (109.0, 109.0)]:
        r.via("GND", x, y)

    # ---- pours -------------------------------------------------------------------
    for lay in ("F", "In1", "In2", "B"):
        r.zone("GND", lay)

    # ---- silkscreen (bottom; the XIAO covers most of the top) -----------------
    BS = P.B_SilkS
    r.text("SolArk carrier B-diy", 114.5, 119.2, BS, 1.0, 0.15)
    r.text("2026-10-13", 114.5, 120.7, BS, 1.0, 0.15)
    r.text("J1 OFF FOR USB", 118.5, 122.7, BS, 1.3, 0.2)
    r.text("unplug harness", 121.6, 124.4, BS, 1.0, 0.15)
    r.text("before USB-C", 121.6, 125.9, BS, 1.0, 0.15)
    r.text("RX ONLY", 103.3, 119.0, BS, 1.0, 0.15, angle=90)
    r.text("DNP: proxy only", 110.8, 111.6, BS, 1.0, 0.15)
    r.text("USB", 126.0, 109.4, BS, 1.0, 0.15, angle=90)
