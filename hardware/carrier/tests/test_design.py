"""Invariants of the carrier netlist (design.py). Run: pytest hardware/carrier/tests."""

from __future__ import annotations

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
)
from design import PARTS

TAPS = {"TAP_RESP", "TAP_REQ"}


def populated(ref: str) -> bool:
    _, value, _, _, dnp, _, _, _ = PARTS[ref]
    return not dnp and not (ref.startswith("JP") and value == "OPEN")


def nets_of(ref: str) -> set[str]:
    return {n for n in PARTS[ref][6].values() if n}


def test_every_assembled_part_has_an_lcsc_number() -> None:
    for ref, (_, _, _, lcsc, dnp, in_bom, _, _) in PARTS.items():
        if in_bom and not dnp:
            assert lcsc.startswith("C"), ref


def test_tap_nets_touch_only_the_harness_and_the_series_resistors() -> None:
    for ref, (_, _, _, _, _, _, conns, _) in PARTS.items():
        for pin, net in conns.items():
            if net in TAPS:
                assert (ref, pin) in {
                    ("J1", "5"),
                    ("J1", "6"),
                    ("R3", "1"),
                    ("R4", "1"),
                }, (ref, pin)


def test_series_resistors_are_populated_1k() -> None:
    for ref in ("R3", "R4"):
        assert populated(ref) and PARTS[ref][1] == "1k"


def test_no_populated_path_from_proxy_gpio_to_anything_but_its_pad() -> None:
    # Walk from GPIO8 through populated two-terminal parts only.
    reach, frontier = {"PROXY_GPIO8"}, ["PROXY_GPIO8"]
    while frontier:
        net = frontier.pop()
        for ref in PARTS:
            if ref == "U1" or not populated(ref) or net not in nets_of(ref):
                continue
            for other in nets_of(ref) - reach:
                reach.add(other)
                frontier.append(other)
    assert reach == {"PROXY_GPIO8"}
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
        "MP": "GND",
    }


def test_feedback_divider_sets_about_5v() -> None:
    def ohms(v: str) -> float:
        n = v.split()[0]
        return float(n[:-1]) * 1000 if n.endswith("k") else float(n)

    vout = 0.8 * (1 + ohms(PARTS["R13"][1]) / ohms(PARTS["R14"][1]))
    assert 4.95 <= vout <= 5.15
