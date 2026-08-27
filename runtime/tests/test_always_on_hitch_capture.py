#!/usr/bin/env python3
"""Structural regression for bounded always-on hitch diagnostics."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HEARTBEAT = (ROOT / "runtime" / "src" / "freeze_heartbeat.c").read_text(
    encoding="utf-8"
)
HEARTBEAT_H = (ROOT / "runtime" / "include" / "freeze_heartbeat.h").read_text(
    encoding="utf-8"
)
CRASH = (ROOT / "runtime" / "src" / "crash_trace.c").read_text(encoding="utf-8")
MAIN = (ROOT / "runtime" / "src" / "main.cpp").read_text(encoding="utf-8")


assert '#define HITCH_FILE     "psx_hitch_report.json"' in HEARTBEAT
assert "#define HITCH_WINDOW_TICKS 6u" in HEARTBEAT
assert "#define HITCH_MAX_FRAME_DELTA 1u" in HEARTBEAT
assert "static int      s_hitch_armed = 0;" in HEARTBEAT
assert "static volatile long s_snapshot_requested = 0;" in HEARTBEAT
assert "void freeze_heartbeat_request_snapshot(void)" in HEARTBEAT
assert "const int preserve_hitch_report = manual_capture || auto_hitch_capture;" in HEARTBEAT
assert '\\"capture\\":{\\"manual\\":%d,\\"auto_hitch\\":%d' in HEARTBEAT
assert 'HITCH_FILE ".tmp"' in HEARTBEAT
assert "MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH" in HEARTBEAT
assert "void freeze_heartbeat_request_snapshot(void);" in HEARTBEAT_H

assert "void psx_crash_trace_manual_snapshot(void)" in CRASH
assert 'psx_crash_trace_dump("manual_snapshot", NULL);' in CRASH
assert 'copy_report_file(kReportPath, "psx_manual_snapshot.json");' in CRASH
assert "freeze_heartbeat_request_snapshot();" in CRASH

assert "PSX_HOTKEY_PAD_DIAGNOSTIC_SNAPSHOT" in MAIN
assert "SDL_CONTROLLER_BUTTON_LEFTSTICK" in MAIN
assert "SDL_CONTROLLER_BUTTON_RIGHTSTICK" in MAIN
assert "diagnostic_snapshot_poll_buttons();" in MAIN
assert "key == SDLK_F12 && (mod & KMOD_CTRL)" in MAIN
assert 'host_osd_push("Diagnostic snapshot saved", 1800);' in MAIN

print("always-on hitch capture guard passed")
