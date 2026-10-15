"""Silkscreen fitting and checking against JLC's legend rules (design.SILK).

fit(board): widen every silk stroke to SILK["min_width"], then cut footprint and board silk
lines back from pad mask openings, holes and the board edge (rectangles are split into four
lines first). Texts are never moved here: their positions live in the generators, and
violations() reports any that are too close.
Used by gen_pcb.py (fit) and check_silk.py (violations, marks). Needs KiCad's pcbnew.
"""

from __future__ import annotations

import math

import design as D
import pcbnew as P

MM, TOMM = P.FromMM, P.ToMM
S = D.SILK
SIDES = {P.F_SilkS: P.F_Cu, P.B_SilkS: P.B_Cu}


def _mask_margin(pad, cu):
    try:
        return max(pad.GetSolderMaskExpansion(cu), 0)
    except (AttributeError, TypeError):
        return 0


def obstacles(board, silk_layer):
    """[(name, shape, clearance nm)] that silk on `silk_layer` must keep clear of."""
    cu = SIDES[silk_layer]
    out = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            name = f"pad {fp.GetReference()}.{pad.GetNumber()}"
            if pad.GetAttribute() == P.PAD_ATTRIB_NPTH:
                out.append((name, pad.GetEffectiveHoleShape(), MM(S["hole_clear"]) + _mask_margin(pad, cu)))
            elif pad.IsOnLayer(cu):
                out.append((name, pad.GetEffectiveShape(cu), MM(S["pad_clear"]) + _mask_margin(pad, cu)))
                if pad.HasHole():
                    out.append((name + " hole", pad.GetEffectiveHoleShape(), MM(S["hole_clear"])))
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            nm = f"via {TOMM(p.x):.2f},{TOMM(p.y):.2f}"
            out.append((nm, t.GetEffectiveHoleShape(), MM(S["hole_clear"])))
    for d in board.GetDrawings():
        if d.GetLayer() == P.Edge_Cuts:
            out.append(("board edge", d.GetEffectiveShape(P.Edge_Cuts), MM(S["edge_clear"])))
    return out


def _hits(shape, obst):
    return [n for n, o, c in obst if o.Collide(shape, c)]


def _seg_shape(a, b, w):
    return P.SHAPE_SEGMENT(a, b, w)


def _runs(a, b, w, obst):
    """Clear sub-segments of a-b (as (start, end) VECTOR2I pairs) at SILK["step"] resolution."""
    length = math.hypot(b.x - a.x, b.y - a.y)
    n = max(1, math.ceil(length / MM(S["step"])))
    pts = [P.VECTOR2I(int(a.x + (b.x - a.x) * i / n), int(a.y + (b.y - a.y) * i / n)) for i in range(n + 1)]
    ok = [not _hits(P.SHAPE_CIRCLE(p, w // 2), obst) for p in pts]
    runs, start = [], None
    for i, good in enumerate(ok + [False]):
        if good and start is None:
            start = i
        elif not good and start is not None:
            s, e = pts[start], pts[i - 1]
            if math.hypot(e.x - s.x, e.y - s.y) >= MM(S["min_piece"]):
                runs.append((s, e))
            start = None
    return runs


def _new_seg(parent, layer, s, e, w):
    g = P.PCB_SHAPE(parent)
    g.SetShape(P.SHAPE_T_SEGMENT)
    g.SetLayer(layer)
    g.SetWidth(w)
    g.SetStart(s)
    g.SetEnd(e)
    return g


def _fit_items(board, container, items):
    """Widen, split rects, trim lines; returns the removed item count."""
    removed = 0
    wmin = MM(S["min_width"])
    cache = {}
    for g in list(items):
        lay = g.GetLayer()
        if lay not in SIDES:
            continue
        obst = cache.setdefault(lay, obstacles(board, lay))
        if isinstance(g, P.PCB_TEXT) or g.GetClass() in ("PCB_TEXT", "PCB_FIELD"):
            g.SetTextThickness(max(g.GetTextThickness(), wmin))
            continue
        w = max(g.GetWidth(), wmin)
        g.SetWidth(w)
        shape = g.GetShape()
        if shape == P.SHAPE_T_RECT:
            x0, y0 = g.GetStart().x, g.GetStart().y
            x1, y1 = g.GetEnd().x, g.GetEnd().y
            corners = [P.VECTOR2I(x0, y0), P.VECTOR2I(x1, y0), P.VECTOR2I(x1, y1), P.VECTOR2I(x0, y1)]
            segs = [(corners[i], corners[(i + 1) % 4]) for i in range(4)]
        elif shape == P.SHAPE_T_SEGMENT:
            segs = [(g.GetStart(), g.GetEnd())]
        else:
            if _hits(g.GetEffectiveShape(lay), obst):
                container.Remove(g)
                removed += 1
            continue
        if shape == P.SHAPE_T_SEGMENT and not _hits(g.GetEffectiveShape(lay), obst):
            continue
        if shape == P.SHAPE_T_RECT and not _hits(g.GetEffectiveShape(lay), obst):
            continue
        container.Remove(g)
        for a, b in segs:
            for s, e in _runs(a, b, w, obst):
                container.Add(_new_seg(container, lay, s, e, w))
    return removed


def fit(board):
    removed = 0
    for fp in board.GetFootprints():
        removed += _fit_items(board, fp, fp.GraphicalItems())
    removed += _fit_items(board, board, board.GetDrawings())
    return removed


def silk_items(board):
    """[(owner, item)] for every visible silk item (footprint graphics, fields, board)."""
    out = []
    for fp in board.GetFootprints():
        for g in list(fp.GraphicalItems()) + list(fp.GetFields()):
            if g.GetLayer() in SIDES and (not hasattr(g, "IsVisible") or g.IsVisible()):
                out.append((fp.GetReference(), g))
    for d in board.GetDrawings():
        if d.GetLayer() in SIDES:
            out.append(("board", d))
    return out


def _label(g):
    return g.GetText() if hasattr(g, "GetText") else g.GetClass()


def violations(board):
    bad = []
    obst = {lay: obstacles(board, lay) for lay in SIDES}
    for owner, g in silk_items(board):
        lay = g.GetLayer()
        if hasattr(g, "GetTextThickness"):
            w, h = TOMM(g.GetTextThickness()), TOMM(g.GetTextHeight())
            if h < S["min_text_h"] - 1e-6:
                bad.append(f"{owner} {_label(g)!r} text height {h:.3f}")
        else:
            w = TOMM(g.GetWidth())
        if w < S["min_width"] - 1e-6:
            bad.append(f"{owner} {_label(g)!r} width {w:.3f}")
        for n in _hits(g.GetEffectiveShape(lay), obst[lay]):
            bad.append(f"{owner} {_label(g)!r} on {board.GetLayerName(lay)} too close to {n}")
    return bad


def _dist(a, b):
    """Edge-to-edge distance between two shapes (nm), 0 if they touch."""
    if a.Collide(b, 0):
        return 0
    lo, hi = 0, MM(5)
    if not a.Collide(b, hi):
        return hi
    while hi - lo > MM(0.005):
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if a.Collide(b, mid) else (mid, hi)
    return hi


def mark_ok(board, ref):
    """Silk of `ref` within mark_dist of pad 1 and nearer pad 1 than any other pad."""
    fp = board.FindFootprintByReference(ref)
    items = [g for o, g in silk_items(board) if o == ref]
    pads = list(fp.Pads())
    p1 = next(p for p in pads if p.GetNumber() == "1")
    for g in items:
        sh = g.GetEffectiveShape(g.GetLayer())
        cu = SIDES[g.GetLayer()]
        d1 = _dist(sh, p1.GetEffectiveShape(cu))
        others = [_dist(sh, p.GetEffectiveShape(cu)) for p in pads if p.GetNumber() != "1" and p.IsOnLayer(cu)]
        if d1 <= MM(S["mark_dist"]) and all(d1 < d for d in others):
            return True, f"{_label(g)} {TOMM(d1):.2f} mm from pad 1"
    return False, "no silk next to pad 1"
