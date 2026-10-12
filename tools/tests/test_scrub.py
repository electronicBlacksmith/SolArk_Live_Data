"""Tests for scrub.py, using synthetic data only (no real secrets in tests)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scrub
from analyze import crc16_modbus, crc_ok


def with_crc(body: bytes) -> bytes:
    c = crc16_modbus(body)
    return body + bytes([c & 0xFF, c >> 8])


def row(t, ch, frame: bytes, kind=""):
    return {"t_start": f"{t:.6f}", "t_end": f"{t + 0.01:.6f}", "channel": ch,
            "len": str(len(frame)), "crc_ok": str(int(crc_ok(frame))), "kind": kind,
            "hex": frame.hex(" ")}


SERIAL = b"QX7RTW2K9P"  # 10 ASCII chars = registers 3..7


def block0_reply(count=19):
    regs = bytearray(2 * count)
    regs[6:16] = SERIAL  # registers 3..7
    regs[0:2] = b"\x00\x03"
    return with_crc(bytes([1, 3, 2 * count]) + bytes(regs))


def test_parse_register_spec():
    assert scrub.parse_registers("3-7") == {3, 4, 5, 6, 7}
    assert scrub.parse_registers("3-5,9,20-21") == {3, 4, 5, 9, 20, 21}
    assert scrub.parse_registers("") == set()


def test_paired_read_reply_zeroes_only_scrubbed_registers_and_fixes_crc():
    req = with_crc(bytes([1, 3, 0, 0, 0, 19]))
    rows = [row(1.0, "Channel 1", req, "read_req"), row(1.1, "Channel 0", block0_reply(), "read_resp")]
    out = scrub.scrub_frames(rows, {3, 4, 5, 6, 7})
    reply = bytes.fromhex(out[1]["hex"])
    assert crc_ok(reply)
    assert out[1]["crc_ok"] == "1"
    assert SERIAL not in reply
    assert reply[3:5] == b"\x00\x03"  # register 0 untouched
    assert out[0]["hex"] == rows[0]["hex"]  # requests carry no values


def test_reply_not_covering_scrubbed_registers_is_unchanged():
    req = with_crc(bytes([1, 3, 0, 59, 0, 2]))
    rep = with_crc(bytes([1, 3, 4, 0x12, 0x34, 0x56, 0x78]))
    rows = [row(1.0, "Channel 1", req, "read_req"), row(1.1, "Channel 0", rep, "read_resp")]
    assert scrub.scrub_frames(rows, {3, 4, 5, 6, 7})[1]["hex"] == rep.hex(" ")


def test_unpaired_reply_has_all_data_zeroed():
    rows = [row(1.1, "Channel 0", block0_reply(), "read_resp")]
    reply = bytes.fromhex(scrub.scrub_frames(rows, {3})[0]["hex"])
    assert crc_ok(reply)
    assert set(reply[3:-2]) == {0}


def test_crc_failed_frame_keeps_header_and_zeroes_rest():
    bad = block0_reply()[:20]
    rows = [row(1.0, "Channel 0", bad)]
    out = bytes.fromhex(scrub.scrub_frames(rows, {3})[0]["hex"])
    assert out[:3] == bad[:3]
    assert set(out[3:]) == {0}
    assert len(out) == len(bad)


def test_write_to_scrubbed_register_is_zeroed():
    w = with_crc(bytes([1, 0x10, 0, 3, 0, 1, 2]) + b"AB")
    out = bytes.fromhex(scrub.scrub_frames([row(1.0, "Channel 1", w, "writeN_req")], {3})[0]["hex"])
    assert crc_ok(out)
    assert b"AB" not in out


def test_scrub_registers_zeroes_values():
    rows = [{"t": "1", "addr": "1", "fc": "3", "register": "4", "value_u16": "12345"},
            {"t": "1", "addr": "1", "fc": "3", "register": "59", "value_u16": "2"}]
    out = scrub.scrub_registers(rows, {4})
    assert out[0]["value_u16"] == "0" and out[1]["value_u16"] == "2"


def test_console_allowlist_and_redaction():
    text = (
        "I (1) wifi_manager:   SSID: MyNet\n"
        "I (1) wifi_manager:   Password: hunter2-secret\n"
        "I (2) tcp_client: Config item: 0 (op:1, at:0, fc:3, addr:15, rn:1)\n"
        "I (3) tcp_client: Data RX on address: 192.168.1.50\n"
        "I (4) MB: 0x3ffbb5bc   02 00 24 02  |..$.|\n"
        "I (5) WIFI_STA MAC: 0xa8, 0x48, 0xfa, 0x79, 0x3f, 0x48\n"
    )
    allow = [r"tcp_client: Config item", r"tcp_client: Data RX"]
    out = scrub.scrub_console(text, allow)
    assert "Config item: 0" in out
    assert "hunter2" not in out and "MyNet" not in out and "0xa8" not in out
    assert "192.168.1.50" not in out and "<IP>" in out
    assert "0x3ffbb5bc" not in out


def test_find_secrets_from_raw_inputs():
    console = "I (1) wifi_manager:   SSID: MyNet\nI (1) wifi_manager:   Password: hunter2-secret\n"
    regs = {3: 0x5158, 4: 0x3752, 5: 0x5457, 6: 0x324B, 7: 0x3950}
    secrets = scrub.find_secrets(console, regs, {3, 4, 5, 6, 7})
    assert "hunter2-secret" in secrets and "MyNet" in secrets
    assert "QX7RTW2K9P" in secrets
    assert "51 58 37 52 54 57 32 4b 39 50" in secrets  # hex form as written in frames.csv


def test_verify_clean_detects_leak(tmp_path):
    (tmp_path / "a.txt").write_text("all fine")
    assert scrub.verify_clean(tmp_path, ["hunter2-secret"]) == []
    (tmp_path / "b.txt").write_text("oops hunter2-secret")
    assert scrub.verify_clean(tmp_path, ["hunter2-secret"]) == ["b.txt"]


def test_scrub_report_drops_example_and_console_lines():
    rep = "Channel 0: ok\n      e.g. t=1s  01 03 00\n      | I (1) secret\nPolled blocks\n"
    assert scrub.scrub_report(rep) == "Channel 0: ok\nPolled blocks\n"


def test_short_secrets_ignored_to_avoid_false_positives():
    console = "I (1) wifi_manager:   SSID: ab\n"
    assert "ab" not in scrub.find_secrets(console, {}, set())


def test_collect_secrets_across_capture_dirs(tmp_path):
    a = tmp_path / "cap1"
    a.mkdir()
    (a / "Channel_2_ascii.txt").write_text("I (1) wifi_manager:   Password: hunter2-secret\n")
    b = tmp_path / "cap2"
    b.mkdir()
    (b / "registers.csv").write_text(
        "t,addr,fc,register,value_u16\n" + "".join(
            f"1,1,3,{r},{v}\n" for r, v in {3: 0x5158, 4: 0x3752, 5: 0x5457, 6: 0x324B, 7: 0x3950}.items()))
    secrets = scrub.collect_secrets(tmp_path, {3, 4, 5, 6, 7})
    assert "hunter2-secret" in secrets and "QX7RTW2K9P" in secrets


def test_collect_secrets_missing_dir_returns_empty(tmp_path):
    assert scrub.collect_secrets(tmp_path / "nope", {3}) == []


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
