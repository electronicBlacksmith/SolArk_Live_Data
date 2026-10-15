#!/bin/sh
# Regenerate everything in fab/ from carrier.kicad_sch / carrier.kicad_pcb.
# Exits non-zero on any ERC or DRC violation (warnings included).
# Usage (from hardware/carrier-diy):  sh scripts/export_fab.sh
set -eu
K=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
KPY=${KICAD_PYTHON:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3}
cd "$(dirname "$0")/.."
OUT=fab
G=$OUT/gerbers
rm -rf "$G" && mkdir -p "$G"

$K sch erc --severity-all --exit-code-violations -o $OUT/erc.rpt carrier.kicad_sch
$K pcb drc --schematic-parity --severity-all --exit-code-violations --refill-zones -o $OUT/drc.rpt carrier.kicad_pcb
$K sch export pdf -o $OUT/carrier_schematic.pdf carrier.kicad_sch
$K pcb export gerbers --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.SilkS,B.SilkS,Edge.Cuts \
    --use-drill-file-origin --subtract-soldermask -o "$G" carrier.kicad_pcb
$K pcb export drill --format excellon --drill-origin plot --excellon-units mm \
    --generate-map --map-format gerberx2 -o "$G/" carrier.kicad_pcb
rm -f $OUT/carrier_gerbers.zip
(cd "$G" && zip -q -X ../carrier_gerbers.zip ./*)

# BOMs and CPL. kicad-cli writes the full fitted BOM and the top-side placements;
# export_bom.py keeps only the parts JLC places in route (a) (design.SOURCE fit == "jlc")
# and writes the Digi-Key BOM for route (b) from design.py.
$K sch export bom --fields 'Value,Reference,Footprint,LCSC' \
    --labels 'Comment,Designator,Footprint,LCSC Part #' --group-by 'Value,Footprint,LCSC' \
    --exclude-dnp --ref-range-delimiter '' -o $OUT/kicad_bom.csv carrier.kicad_sch
$K pcb export pos --format csv --units mm --side front --use-drill-file-origin \
    --exclude-dnp --exclude-fp-th -o $OUT/kicad_pos_front.csv carrier.kicad_pcb
python3 -I scripts/export_bom.py $OUT/kicad_bom.csv $OUT/kicad_pos_front.csv $OUT
rm -f $OUT/kicad_bom.csv $OUT/kicad_pos_front.csv

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
