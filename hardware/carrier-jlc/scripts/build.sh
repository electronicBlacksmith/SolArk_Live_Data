#!/bin/sh
# Full regeneration: libraries -> schematic -> netlist -> PCB -> ERC/DRC + fab outputs.
# Fails (non-zero exit) on any generator error, ERC violation or DRC violation.
# Usage (from anywhere):  sh <board>/scripts/build.sh
set -eu
K=${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}
KPY=${KICAD_PYTHON:-/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3}
cd "$(dirname "$0")/.."
python3 -I scripts/gen_lib.py
python3 -I scripts/gen_sch.py
$K sch export netlist -o carrier.net carrier.kicad_sch
# gen_pcb: keep its exit status (no pipefail in POSIX sh), then show filtered output
LOG=$(mktemp)
rc=0
PYTHONDONTWRITEBYTECODE=1 $KPY -I scripts/gen_pcb.py >"$LOG" 2>&1 || rc=$?
grep -v -i -E "assert|wxwidgets|^\s*$" "$LOG" || true
if [ "$rc" -ne 0 ] || ! grep -q "^saved " "$LOG"; then
  rm -f "$LOG"
  echo "gen_pcb.py failed (exit $rc)" >&2
  exit 1
fi
rm -f "$LOG"
sh scripts/export_fab.sh
rm -rf scripts/__pycache__
