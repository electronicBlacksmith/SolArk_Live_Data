"""Hand-planned routing, zones and silkscreen for the carrier (called by gen_pcb.py).

Layer use: F.Cu parts + short routes + GND pour; In1.Cu solid GND; In2.Cu RX/sense
signals + GND pour; B.Cu +12V_P feed, +3V3 + GND pour. No parts on the bottom.
"""

from __future__ import annotations

import design as D
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

    def zone(self, net, layer, inset=0.0, prio=0, x1=127.0, y1=127.0):
        z = P.ZONE(self.b)
        z.SetLayer(LAYER[layer])
        z.SetNet(self.net(net))
        o = z.Outline()
        o.NewOutline()
        for x, y in [
            (100 + inset, 100 + inset),
            (x1 - inset, 100 + inset),
            (x1 - inset, y1 - inset),
            (100 + inset, y1 - inset),
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

    def text(self, s, x, y, layer, size=None, thick=None, angle=0):
        size = D.SILK["min_text_h"] if size is None else size
        thick = D.SILK["min_width"] if thick is None else thick
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

    def rect(self, layer, x0, y0, x1, y1, w=None):
        w = D.SILK["min_width"] if w is None else w
        s = P.PCB_SHAPE(self.b)
        s.SetShape(P.SHAPE_T_RECT)
        s.SetStart(V(x0, y0))
        s.SetEnd(V(x1, y1))
        s.SetLayer(layer)
        s.SetWidth(MM(w))
        self.b.Add(s)


def build(board, fps, nets, W=27.0, H=27.0):
    r = Router(board, fps, nets)

    # ---- input protection chain (left strip, F.Cu) -----------------------
    r.track("+12V_IN", "F", [("J1", 1), (101.2, 120.4), ("F1", 1)], W_PWR)
    r.track("+12V_F", "F", [("F1", 2), ("D1", 2)], W_PWR)
    r.track("+12V_P", "F", [("D1", 1), ("TVS1", 1)], W_PWR)
    r.track("+12V_P", "F", [(102.3, 108.9), (103.6, 108.9)], W_PWR)
    r.via("+12V_P", 103.6, 108.9)
    # +12V_P to the buck on B.Cu: under the XIAO, down between U1 pins 12/13,
    # then left above the harness pads (keeps clear of the +3V3 feed at y 118.25)
    r.track(
        "+12V_P",
        "B",
        [(103.6, 108.9), (118.745, 108.9), (118.745, 124.4), (112.55, 124.4), (112.55, 124.9)],
        0.4,
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

    # ---- taps: J1 pads -> D3/D4 ESD -> R3/R4 -> U3 (one-way) -> R7/R8 -> In2 -> D0/D1
    r.track("TAP_RESP", "F", [("J1", 4), ("D3", 1), ("R3", 1)], W_SIG)
    r.track("TAP_REQ", "F", [("J1", 5), ("D4", 1), ("R4", 1)], W_SIG)
    r.track("BUF_IN_RESP", "F", [("R3", 2), ("U3", 1)], W_SIG)
    r.track("BUF_IN_RESP", "F", [("U3", 1), (107.81, 122.2), ("R5", 2)], W_SIG)
    r.track("BUF_IN_REQ", "F", [("R4", 2), (111.36, 120.35), ("U3", 3)], W_SIG)
    r.track("BUF_IN_REQ", "F", [("R6", 2), (107.825, 119.7), ("U3", 3)], W_SIG)
    r.track("BUF_OUT_REQ", "F", [("U3", 4), (105.2, 120.35), ("R8", 1)], W_SIG)
    r.track("BUF_OUT_RESP", "F", [("U3", 6), ("R7", 1)], W_SIG)
    r.track("RX_REQ", "F", [("R8", 2), (104.9, 118.0)], W_SIG)
    r.via("RX_REQ", 104.9, 118.0)
    r.track(
        "RX_REQ", "In2", [(104.9, 118.0), (104.9, 103.4), (120.015, 103.4), ("U1", 2)], W_SIG
    )
    r.track("RX_RESP", "F", [("R7", 2), (105.2, 124.35)], W_SIG)
    r.via("RX_RESP", 105.2, 124.35)
    r.track(
        "RX_RESP",
        "In2",
        [(105.2, 124.35), (105.7, 123.85), (105.7, 104.2), (122.555, 104.2), ("U1", 1)],
        W_SIG,
    )
    # +3V3: U1 pin 12 on B.Cu -> vias at R6, C9/U3 VCC and R5
    r.track(
        "+3V3",
        "B",
        [("U1", 12), (117.475, 118.25), (106.79, 118.25), (106.79, 123.3), (106.6, 123.85)],
        W_SIG,
    )
    r.track("+3V3", "B", [(106.79, 121.0), (104.15, 121.0)], W_SIG)
    for x, y in ((106.79, 118.25), (104.15, 121.0), (106.6, 123.85)):
        r.via("+3V3", x, y)
    r.track("+3V3", "F", [(106.79, 118.25), ("R6", 1)], W_SIG)
    r.track("+3V3", "F", [("C9", 1), (104.15, 121.0), ("U3", 5)], W_SIG)
    r.track("+3V3", "F", [("R5", 1), (106.6, 123.85)], W_SIG)

    # ---- GND vias (stitch top pads to the In1 plane) ---------------------
    for x, y in [
        (100.8, 105.2),
        (113.0, 120.85),
        (117.9, 121.1),
        (117.55, 126.3),
        (125.6, 126.2),
        (100.8, 112.0),
        (113.0, 126.3),
        (121.9, 126.3),
        (126.4, 118.0),
        (108.0, 108.0),
        (112.0, 106.5),
        (121.0, 112.0),
        (124.0, 110.0),
        (102.32, 121.85),  # C9
        (107.675, 124.75),  # D3
        (110.225, 124.75),  # D4
        (110.1, 121.0),  # U3
    ]:
        r.via("GND", x, y)
    r.track("GND", "F", [("C9", 2), (102.32, 121.85)], 0.3)
    r.track("GND", "F", [("D3", 2), (107.675, 124.75), ("J1", 3)], 0.3)
    r.track("GND", "F", [("D4", 2), (110.225, 124.75)], 0.3)
    r.track("GND", "F", [("U3", 2), (110.1, 121.0)], W_SIG)
    r.track("GND", "F", [("C2", 2), (117.55, 126.3)], 0.3)

    # ---- pours --------------------------------------------------------------
    for lay in ("F", "In1", "In2", "B"):
        r.zone("GND", lay, x1=100 + W, y1=100 + H)

    # ---- silkscreen / documentation ----------------------------------------
    BS, FS = P.B_SilkS, P.F_SilkS
    # positions keep >= SILK pad/hole clearance from vias and pads (check_silk.py)
    r.text("SolArk carrier rev B", 119.3, 121.95, BS)
    r.text("12V OFF FOR USB", 119.3, 123.45, BS)
    r.text("(or USB isolator)", 119.3, 124.95, BS)
    for i, lab in enumerate(("12V", "G", "G", "9", "10")):
        x, _ = r.pad("J1", i + 1)
        dx = -0.45 if i == 2 else 0.0  # pad 3's G label clears the GND via beside it
        r.text(lab, max(x + dx, 101.75), 122.65 if i == 0 else 123.75, BS)
    r.text("12V", 101.75, 123.75, FS)
    r.rect(BS, 105.0, 104.0, 116.6, 111.2)
    r.text("FOAM TAPE", 110.95, 107.6, BS)
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
