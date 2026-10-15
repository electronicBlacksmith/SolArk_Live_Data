#!/bin/sh
# Full regeneration: libraries -> schematic -> netlist -> PCB -> ERC/DRC + fab outputs.
# Usage (from anywhere):  sh hardware/carrier/scripts/build.sh
set -eu
K=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
KPY=${KICAD_PYTHON:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3}
cd "$(dirname "$0")/.."
python3 -I scripts/gen_lib.py
python3 -I scripts/gen_sch.py
$K sch export netlist -o carrier.net carrier.kicad_sch
PYTHONDONTWRITEBYTECODE=1 $KPY -I scripts/gen_pcb.py 2>&1 | grep -v -i -E "assert|wxwidgets|^\s*$" || true
sh scripts/export_fab.sh
rm -rf scripts/__pycache__
