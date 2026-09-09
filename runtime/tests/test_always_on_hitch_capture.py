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
LATENCY = (ROOT / "runtime" / "src" / "latency_ring.c").read_text(encoding="utf-8")


assert '#define HITCH_FILE     "psx_hitch_report.json"' in HEARTBEAT
assert "#define HITCH_WINDOW_TICKS 6u" in HEARTBEAT
assert "#define HITCH_HARD_MAX_FRAME_DELTA 1u" in HEARTBEAT
assert "#define HITCH_SLOW_MAX_FRAME_DELTA 18u" in HEARTBEAT
assert "#define HITCH_REARM_MIN_FRAME_DELTA 24u" in HEARTBEAT
assert "static int      s_hitch_armed = 0;" in HEARTBEAT
assert "static volatile long s_snapshot_requested = 0;" in HEARTBEAT
assert "void freeze_heartbeat_request_snapshot(void)" in HEARTBEAT
assert "const int preserve_hitch_report = manual_capture || auto_hitch_capture;" in HEARTBEAT
assert '\\"capture\\":{\\"manual\\":%d,\\"auto_hitch\\":%d' in HEARTBEAT
assert '\\"auto_hitch_kind\\":%d' in HEARTBEAT
assert '\\"execution\\":{\\"overlay_native\\":%llu' in HEARTBEAT
assert '\\"overlay_interp\\":%llu,\\"interrupt_checks\\":%llu' in HEARTBEAT
assert '\\"checks\\":%llu,\\"ovl_native\\":%llu,\\"ovl_interp\\":%llu' in HEARTBEAT
assert '\\"audio\\":{\\"pump_calls\\":%llu,\\"pump_skips\\":%llu' in HEARTBEAT
assert '\\"cdrom\\":{\\"sectors\\":%llu,\\"commands\\":%llu' in HEARTBEAT
assert '\\"latency\\":%s' in HEARTBEAT
assert "audio_trace_get_stats(&audio_stats);" in HEARTBEAT
assert "cdrom_get_telemetry(&cd_stats);" in HEARTBEAT
assert "overlay_loader_get_counters(" in HEARTBEAT
assert "latency_ring_summary_json(" in HEARTBEAT
assert "double tmp[LAT_RING_SIZE];" in LATENCY
assert "static double tmp[LAT_RING_SIZE];" not in LATENCY
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

CDROM_H = (ROOT / "runtime" / "include" / "cdrom.h").read_text(encoding="utf-8")
CDROM = (ROOT / "runtime" / "src" / "cdrom.c").read_text(encoding="utf-8")
assert "typedef struct CDROMTelemetry" in CDROM_H
assert "void cdrom_get_telemetry(CDROMTelemetry* out);" in CDROM_H
assert "s_xa_audio_sectors_delivered++;" in CDROM
assert "s_xa_pcm_frames_delivered += (uint64_t)out_frames;" in CDROM
assert "void cdrom_get_telemetry(CDROMTelemetry* out)" in CDROM
assert "s_telemetry_commands_total++;" in CDROM
assert "s_telemetry_sectors_total++;" in CDROM
assert "s_telemetry_commands_total = 0" not in CDROM
assert "s_telemetry_sectors_total = 0" not in CDROM

print("always-on hitch capture guard passed")
