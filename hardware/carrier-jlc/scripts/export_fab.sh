#!/bin/sh
# Regenerate everything in fab/ from carrier.kicad_sch / carrier.kicad_pcb.
# Usage (from hardware/carrier):  sh scripts/export_fab.sh
set -eu
K=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
KPY=${KICAD_PYTHON:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3}
cd "$(dirname "$0")/.."
OUT=fab
G=$OUT/gerbers
rm -rf "$G" && mkdir -p "$G"

# Both checks exit non-zero on any violation (set -e stops the build).
$K sch erc --severity-all --exit-code-violations -o $OUT/erc.rpt carrier.kicad_sch
$K pcb drc --schematic-parity --severity-all --refill-zones --exit-code-violations \
    -o $OUT/drc.rpt carrier.kicad_pcb
# Silkscreen vs pads, holes and edge (JLC legend rules, design.SILK); exits 1 on a violation.
$KPY -I scripts/check_silk.py carrier.kicad_pcb $OUT/silk.rpt
$K sch export pdf -o $OUT/carrier_schematic.pdf carrier.kicad_sch
$K pcb export gerbers --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.SilkS,B.SilkS,Edge.Cuts \
    --use-drill-file-origin --subtract-soldermask -o "$G" carrier.kicad_pcb
$K pcb export drill --format excellon --drill-origin plot --excellon-units mm --excellon-separate-th \
    --generate-map --map-format gerberx2 -o "$G/" carrier.kicad_pcb
rm -f $OUT/carrier_gerbers.zip
(cd "$G" && zip -q -X ../carrier_gerbers.zip ./*)

# JLC BOM: Comment, Designator, Footprint, LCSC Part # (DNP and not-in-BOM parts excluded)
$K sch export bom --fields 'Value,Reference,Footprint,LCSC' \
    --labels 'Comment,Designator,Footprint,LCSC Part #' --group-by 'Value,Footprint,LCSC' \
    --exclude-dnp --ref-range-delimiter '' -o $OUT/carrier_bom_jlc.csv carrier.kicad_sch

# CPL: KiCad rotations plus the design.CPL_ROTATION offsets (confirm in JLC's preview)
$K pcb export pos --format csv --units mm --side front --use-drill-file-origin \
    --exclude-dnp --exclude-fp-th -o $OUT/kicad_pos_front.csv carrier.kicad_pcb
python3 -I - scripts "$OUT/kicad_pos_front.csv" "$OUT/carrier_cpl_jlc.csv" <<'PY'
import csv, re, sys
sys.path.insert(0, sys.argv[1])
from design import CPL_ROTATION
rows = list(csv.DictReader(open(sys.argv[2])))
with open(sys.argv[3], "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for r in rows:
        off = next((o for pat, o in CPL_ROTATION if re.match(pat, r["Package"])), 0)
        w.writerow([r["Ref"], r["PosX"] + "mm", r["PosY"] + "mm",
                    "Top" if r["Side"] == "top" else "Bottom",
                    "%g" % ((float(r["Rot"]) + off) % 360)])
PY
rm -f $OUT/kicad_pos_front.csv

for s in top bottom; do
  $K pcb render --side $s -w 1200 -h 1200 --quality high --background opaque --zoom 0.75 \
      -o $OUT/render_$s.png carrier.kicad_pcb >/dev/null
done
for s in front right; do  # side views: total height incl. receptacle tails
  $K pcb render --side $s -w 1400 -h 700 --quality high --background opaque --zoom 1.0 \
      -o $OUT/render_side_$s.png carrier.kicad_pcb >/dev/null
done
$K pcb render --side top --rotate '-50,0,35' -w 1200 -h 900 --quality high --background opaque \
    --perspective -o $OUT/render_iso.png carrier.kicad_pcb >/dev/null
sed -i.bak "s#$(pwd)#.#g" $OUT/erc.rpt $OUT/drc.rpt && rm -f $OUT/*.bak
echo "fab exports done"
