"""Check carrier.kicad_pcb silkscreen against design.SILK (JLC legend rules).

Usage (KiCad's Python): check_silk.py <board.kicad_pcb> <report>. Exits 1 on any violation
or a missing pin-1 / cathode mark. Report lines: "silk violations: N", "mark <ref> ok|MISSING",
"text <side>: <string>".
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D
import pcbnew as P
import silk


def main(pcb, rpt):
    board = P.LoadBoard(pcb)
    bad = silk.violations(board)
    lines = [f"silk violations: {len(bad)}"] + ["  " + b for b in bad]
    missing = 0
    for ref in D.SILK["marks"]:
        ok, why = silk.mark_ok(board, ref)
        missing += not ok
        lines.append(f"mark {ref} {'ok' if ok else 'MISSING'} ({why})")
    for owner, g in silk.silk_items(board):
        if owner == "board" and hasattr(g, "GetText"):
            lines.append(f"text {board.GetLayerName(g.GetLayer())}: {g.GetText()}")
    with open(rpt, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines[: 1 + len(bad)]))
    return 1 if bad or missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
