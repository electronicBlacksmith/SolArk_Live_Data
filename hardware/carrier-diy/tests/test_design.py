"""Invariants of the carrier netlist (design.py). Run: pytest hardware/carrier-diy/tests."""

from __future__ import annotations

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
)
from design import PARTS, SOURCE, VBUS

TAPS = {"TAP_RESP", "TAP_REQ"}
POWER = {"GND", "+3V3", "+5V_X", "+5V_BUCK", "+12V_IN", "+12V_F", "+12V_P"}
GPIO_PINS = [str(n) for n in range(1, 12)]  # XIAO D0..D10


def populated(ref: str) -> bool:
    _, value, _, _, dnp, _, _, _ = PARTS[ref]
    return not dnp and not (ref.startswith("JP") and value == "OPEN")


def nets_of(ref: str) -> set[str]:
    return {n for n in PARTS[ref][6].values() if n}


def dc_parts() -> list[str]:
    """Populated two-terminal parts that conduct DC (resistors, jumpers, fuses)."""
    return [
        r
        for r in PARTS
        if populated(r) and r[0] in "RFLJ" and r != "J1" and len(nets_of(r)) == 2
    ]


def dc_reach(start: set[str]) -> set[str]:
    """Nets reachable from `start` through populated DC parts, stopping at power rails."""
    reach, frontier = set(start), list(start)
    while frontier:
        net = frontier.pop()
        if net in POWER:
            continue
        for ref in dc_parts():
            if net in nets_of(ref):
                for other in nets_of(ref) - reach:
                    reach.add(other)
                    frontier.append(other)
    return reach


def test_every_fitted_part_has_a_source() -> None:
    for ref, (_, _, _, lcsc, dnp, in_bom, _, _) in PARTS.items():
        if not (in_bom and not dnp):
            continue
        src = SOURCE[ref]
        assert src["dk"], ref  # route (b): every fitted part is bought at Digi-Key
        assert src["fit"] in ("jlc", "hand"), ref
        if src["fit"] == "jlc":  # route (a): JLC places only fee-free library parts
            assert lcsc.startswith("C"), ref
            assert src["jlc"] in ("Basic", "Preferred"), ref


def test_tap_nets_touch_only_the_harness_and_the_series_resistors() -> None:
    allowed = {("J1", "5"), ("J1", "6"), ("R3", "1"), ("R4", "1")}
    for ref, (_, _, _, _, _, _, conns, _) in PARTS.items():
        for pin, net in conns.items():
            if net in TAPS:
                assert (ref, pin) in allowed, (ref, pin)


def test_series_resistors_are_populated_1k() -> None:
    for ref in ("R3", "R4", "R7", "R8"):
        assert populated(ref) and PARTS[ref][1] == "1k", ref


def test_buffer_is_the_only_path_from_tap_to_gpio() -> None:
    # No populated DC path joins any XIAO GPIO to a tap pad: the buffer is a barrier.
    gpio_nets = {PARTS["U1"][6][p] for p in GPIO_PINS} - {None}
    assert not (dc_reach(gpio_nets) & TAPS)
    # Tap side reaches only buffer inputs (and the +3V3 bias rail, a sink).
    assert dc_reach(TAPS) - POWER == TAPS | {"BUF_IN_RESP", "BUF_IN_REQ"}
    u3 = PARTS["U3"][6]
    assert {u3["1"], u3["3"]} == {"BUF_IN_RESP", "BUF_IN_REQ"}  # 1A, 2A inputs
    assert {u3["6"], u3["4"]} == {"BUF_OUT_RESP", "BUF_OUT_REQ"}  # 1Y, 2Y outputs
    # Channel pairing: 1A->1Y, 2A->2Y
    assert u3["1"].replace("IN", "OUT") == u3["6"]
    assert u3["3"].replace("IN", "OUT") == u3["4"]
    # GPIO side: D0/D1 see only the buffer outputs through R7/R8.
    assert dc_reach({"RX_RESP"}) == {"RX_RESP", "BUF_OUT_RESP"}
    assert dc_reach({"RX_REQ"}) == {"RX_REQ", "BUF_OUT_REQ"}
    assert PARTS["U1"][6]["1"] == "RX_RESP" and PARTS["U1"][6]["2"] == "RX_REQ"


def test_buffer_is_powered_and_decoupled() -> None:
    u3 = PARTS["U3"][6]
    assert u3["5"] == "+3V3" and u3["2"] == "GND"
    assert populated("U3") and "74LVC2G17" in PARTS["U3"][1]
    assert populated("C9") and nets_of("C9") == {"+3V3", "GND"}


def test_buffer_inputs_are_biased_not_floating() -> None:
    for ref, net in (("R5", "BUF_IN_RESP"), ("R6", "BUF_IN_REQ")):
        assert populated(ref) and nets_of(ref) == {"+3V3", net}, ref


def test_no_populated_path_from_proxy_gpio_to_anything_but_its_pad() -> None:
    assert dc_reach({"PROXY_GPIO8"}) == {"PROXY_GPIO8"}
    assert not populated("R12") and not populated("JP1")
    assert "PROXY_PAD" not in nets_of("J1")


def test_harness_pinout() -> None:
    assert PARTS["J1"][6] == {
        "1": "+12V_IN",
        "2": "GND",
        "3": None,
        "4": "GND",
        "5": "TAP_RESP",
        "6": "TAP_REQ",
    }


def test_no_socket_or_castellation_parts() -> None:
    for ref, (lib_id, value, fp, _, _, _, _, desc) in PARTS.items():
        text = " ".join((lib_id, value, fp, desc)).lower()
        assert "mill-max" not in text and "socket" not in text, ref
        assert "7305" not in text and "castellation" not in text, ref


def test_fitted_parts_are_hand_solderable_packages() -> None:
    bad = ("0402", "0201", "DFN", "SOD-882", "SOT-363", "SC-70", "QFN")
    for ref, (_, _, fp, _, dnp, in_bom, _, _) in PARTS.items():
        if in_bom and not dnp:
            assert not any(b in fp for b in bad), (ref, fp)


def _ohms(v: str) -> float:
    n = v.split()[0]
    return float(n[:-1]) * 1000 if n.endswith("k") else float(n)


def test_vbus_window_at_the_xiao_pin_after_d2() -> None:
    rt, rb = _ohms(PARTS["R13"][1]), _ohms(PARTS["R14"][1])
    assert nets_of("R13") == {"+5V_BUCK", "FB"} and nets_of("R14") == {"FB", "GND"}
    tol = VBUS["r_tol"] + VBUS["r_tc_ppm"] * 1e-6 * VBUS["dT"]
    k_hi = rt * (1 + tol) / (rb * (1 - tol))
    k_lo = rt * (1 - tol) / (rb * (1 + tol))
    vout_max = VBUS["vfb"][1] * (1 + k_hi)
    vout_min = VBUS["vfb"][0] * (1 + k_lo)
    assert VBUS["vout_window"][0] <= vout_min and vout_max <= VBUS["vout_window"][1]
    pin_min = vout_min - VBUS["d2_vf_load_max"]
    pin_max = vout_max - VBUS["d2_vf_idle_min"]
    assert pin_min >= VBUS["pin_min"], pin_min
    assert pin_max <= VBUS["pin_max"], pin_max


def test_fb_divider_top_is_in_the_ti_recommended_range() -> None:
    # LMR51610 datasheet: RFBT 10 k to 100 k recommended
    assert 10_000 <= _ohms(PARTS["R13"][1]) <= 100_000
