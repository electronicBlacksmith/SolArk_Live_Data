#!/bin/sh
# Full regeneration: libraries -> schematic -> netlist -> PCB -> ERC/DRC + fab outputs.
# Fails (non-zero exit) on any generator error, ERC violation or DRC violation.
# Usage (from anywhere):  sh hardware/carrier-diy/scripts/build.sh
set -eu
K=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
KPY=${KICAD_PYTHON:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3}
cd "$(dirname "$0")/.."
python3 -I scripts/gen_lib.py
python3 -I scripts/gen_sch.py
$K sch export netlist -o carrier.net carrier.kicad_sch
# POSIX sh has no pipefail: keep gen_pcb's exit status, then filter wx noise from its log.
LOG=fab/gen_pcb.log
mkdir -p fab
status=0
PYTHONDONTWRITEBYTECODE=1 $KPY -I scripts/gen_pcb.py >"$LOG" 2>&1 || status=$?
grep -v -i -E "assert|wxwidgets|^\s*$" "$LOG" || [ $? -eq 1 ]
rm -f "$LOG"
if [ "$status" -ne 0 ]; then
  echo "gen_pcb.py failed (exit $status)" >&2
  exit "$status"
fi
sh scripts/export_fab.sh
rm -rf scripts/__pycache__
