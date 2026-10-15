"""Hand-planned routing, zones and silkscreen for the carrier (called by gen_pcb.py).

Layer use: F.Cu parts + short routes + GND pour; In1.Cu solid GND; In2.Cu tap/sense
signals + GND pour; B.Cu +12V_P feed, +3V3, DNP options + GND pour.
"""

from __future__ import annotations

import pcbnew as P

MM = P.FromMM
LAYER = {"F": P.F_Cu, "In1": P.In1_Cu, "In2": P.In2_Cu, "B": P.B_Cu}
VIA_D, VIA_DRILL = 0.6, 0.3
W_SIG, W_PWR, W_SW = 0.2, 0.5, 0.6


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
        for x, y in [
            (100 + inset, 100 + inset),
            (127 - inset, 100 + inset),
            (127 - inset, 127 - inset),
            (100 + inset, 127 - inset),
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

    # ---- input protection chain (left strip, F.Cu) -----------------------
    r.track("+12V_IN", "F", [("J1", 1), (103.475, 119.6)], W_PWR)
    r.track("+12V_F", "F", [("F1", 2), ("D1", 2)], W_PWR)
    r.track("+12V_P", "F", [("D1", 1), ("TVS1", 1)], W_PWR)
    r.track("+12V_P", "F", [(102.3, 108.9), (103.6, 108.9)], W_PWR)
    r.via("+12V_P", 103.6, 108.9)
    # +12V_P to the buck on B.Cu
    r.track(
        "+12V_P",
        "B",
        [(103.6, 108.9), (103.6, 125.0), (112.55, 125.0), (112.55, 124.9)],
        W_PWR,
    )
    r.via("+12V_P", 112.55, 124.9)
    r.track(
        "+12V_P", "F", [(112.55, 124.9), ("C1", 1), (115.85, 124.875), ("U2", 5)], W_PWR
    )
    r.track("+12V_P", "F", [("U2", 4), (115.85, 125.6), ("C2", 1)], 0.4)

    # ---- buck core (F.Cu) ------------------------------------------------
    r.track("SW", "F", [("U2", 6), (120.45, 124.537)], W_SW)
    r.track("SW", "F", [("C8", 2), (119.07, 124.537)], 0.3)
    r.track("CB", "F", [("U2", 1), (118.4, 122.263), ("C8", 1)], 0.3)
    r.track("GND", "F", [("U2", 2), (116.8, 121.3), (117.55, 120.55), ("C7", 2)], 0.4)
    r.track("FB", "F", [("U2", 3), (115.85, 120.9), (115.16, 120.2), ("R13", 2)], W_SIG)
    r.track("FB", "F", [("R14", 1), ("R13", 2)], W_SIG)
    r.track("+5V_BUCK", "F", [(123.2, 121.8), ("D2", 2)], W_SW)
    r.track("+5V_BUCK", "F", [("C7", 1), ("D2", 2)], W_PWR)
    # FB divider top senses +5V_BUCK at C7 via In2
    r.track("+5V_BUCK", "F", [("R13", 1), (116.18, 118.85)], W_SIG)
    r.via("+5V_BUCK", 116.18, 118.85)
    r.track("+5V_BUCK", "In2", [(116.18, 118.85), (119.45, 118.85)], W_SIG)
    r.via("+5V_BUCK", 119.45, 118.85)
    r.track("+5V_BUCK", "F", [(119.45, 118.85), ("C7", 1)], W_SIG)
    # +5V_X: D2 cathode -> C4, C3, XIAO 5V
    r.track("+5V_X", "F", [("D2", 1), ("C4", 1), (125.37, 120.6), ("C3", 1)], W_PWR)
    r.track(
        "+5V_X",
        "F",
        [("D2", 1), (124.05, 119.4), (123.0, 118.3), (122.555, 117.6)],
        W_SW,
    )

    # ---- taps: J1 -> In2 -> R3/R4 (top-left) -> F.Cu under XIAO -> D0/D1 ----
    r.track("TAP_RESP", "F", [("J1", 5), (108.475, 120.5)], W_SIG)
    r.via("TAP_RESP", 108.475, 120.5)
    r.track(
        "TAP_RESP",
        "In2",
        [(108.475, 120.5), (104.3, 120.5), (104.3, 102.6), (100.85, 102.6)],
        W_SIG,
    )
    r.via("TAP_RESP", 100.85, 102.6)
    r.track("TAP_RESP", "F", [(100.85, 102.6), ("R3", 1)], W_SIG)
    r.track("TAP_REQ", "F", [("J1", 6), (109.725, 119.6)], W_SIG)
    r.via("TAP_REQ", 109.725, 119.6)
    r.track(
        "TAP_REQ",
        "In2",
        [(109.725, 119.6), (104.9, 119.6), (104.9, 101.0), (100.85, 101.0)],
        W_SIG,
    )
    r.via("TAP_REQ", 100.85, 101.0)
    r.track("TAP_REQ", "F", [(100.85, 101.0), ("R4", 1)], W_SIG)
    r.track(
        "RX_REQ",
        "F",
        [("R4", 2), (104.0, 101.0), (104.0, 103.4), (120.015, 103.4), ("U1", 2)],
        W_SIG,
    )
    r.track(
        "RX_RESP",
        "F",
        [("R3", 2), (103.3, 102.6), (103.3, 104.2), (122.555, 104.2), ("U1", 1)],
        W_SIG,
    )

    # ---- bottom: DNP pull-ups/filters at D0/D1, +3V3, proxy reservation ----
    r.track("RX_RESP", "B", [("U1", 1), ("R5", 2), ("C5", 1)], W_SIG)
    r.track("RX_REQ", "B", [("U1", 2), ("R6", 2), ("C6", 1)], W_SIG)
    r.track(
        "+3V3", "B", [("U1", 12), (117.475, 106.0), (122.555, 106.0), ("R5", 1)], W_SIG
    )
    r.track("+3V3", "B", [(120.015, 106.0), ("R6", 1)], W_SIG)
    r.track("PROXY_GPIO8", "B", [("U1", 10), (112.395, 114.6), ("R12", 1)], W_SIG)
    r.track("PROXY_TX", "B", [("R12", 2), ("JP1", 1)], W_SIG)
    r.track("PROXY_PAD", "B", [("JP1", 2), ("TP1", 1)], W_SIG)

    # ---- GND vias (stitch top pads to the In1 plane) ---------------------
    for x, y in [
        (100.8, 105.2),
        (113.0, 120.85),
        (118.3, 121.0),
        (117.55, 126.3),
        (125.6, 126.2),
        (104.725, 123.5),
        (107.225, 123.5),
        (101.6, 123.0),
        (111.6, 123.0),
        (100.8, 112.0),
        (100.8, 121.0),
        (113.0, 126.3),
        (121.9, 126.3),
        (126.4, 118.0),
        (108.0, 108.0),
        (112.0, 106.5),
        (119.2, 112.0),
        (124.0, 110.0),
        (104.0, 126.3),
    ]:
        r.via("GND", x, y)
    r.track("GND", "F", [("J1", 2), (104.725, 123.5)], 0.4)
    r.track("GND", "F", [("J1", 4), (107.225, 123.5)], 0.4)
    r.track("GND", "F", [("C2", 2), (117.55, 126.3)], 0.3)

    # ---- pours --------------------------------------------------------------
    for lay in ("F", "In1", "In2", "B"):
        r.zone("GND", lay)

    # ---- silkscreen / documentation ----------------------------------------
    BS = P.B_SilkS
    r.text("SolArk XIAO carrier", 113.5, 119.9, BS)
    r.text("rev A  2026-10-12", 113.5, 121.1, BS)
    r.text("NO USB WHILE INSTALLED", 113.5, 122.4, BS)
    r.text("without a USB isolator", 113.5, 123.6, BS)
    r.text("J1 1:12V 2:GND 3:NC", 113.5, 124.9, BS)
    r.text("4:GND 5:TAP9 6:TAP10", 113.5, 126.1, BS)
    r.text("DNP: proxy only", 108.3, 112.0, BS)
    r.rect(BS, 105.0, 104.0, 116.6, 111.2)
    r.text("FOAM TAPE AREA", 110.8, 107.6, BS)
    r.text("USB", 125.6, 109.4, BS, angle=90)
    # pigtail exit / U.FL note for assembly (fab + drawings layers)
    r.text(
        "U.FL: pigtail exits left over F1/D1/TVS1 (all <=1.6 mm)",
        113.0,
        99.0,
        P.Dwgs_User,
        0.6,
        0.1,
    )
    r.rect(P.Dwgs_User, 100.0, 103.0, 107.7, 106.1, 0.1)
