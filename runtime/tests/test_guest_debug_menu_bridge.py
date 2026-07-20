#!/usr/bin/env python3
"""Structural checks for the optional game-owned debug-menu bridge."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
MAIN = (ROOT / "runtime" / "src" / "main.cpp").read_text(encoding="utf-8")
CMAKE = (ROOT / "runtime" / "runtime.cmake").read_text(encoding="utf-8")


def require(text: str, source: str, message: str) -> None:
    if text not in source:
        raise AssertionError(message)


def main() -> int:
    for setting in (
        "PSX_GUEST_DEBUG_GATE_ADDR",
        "PSX_GUEST_DEBUG_PAD_SLOT",
        "PSX_GUEST_DEBUG_PAD_CHORD",
        "PSX_GUEST_DEBUG_READY_ADDR",
        "PSX_GUEST_DEBUG_READY_VALUE",
        "PSX_GUEST_DEBUG_ACTIVATE_ADDR",
        "PSX_GUEST_DEBUG_ACTIVATE_VALUE",
    ):
        require(setting, CMAKE, f"missing generic CMake setting {setting}")
        require(setting, MAIN, f"missing runtime use of {setting}")

    require("!defined(PSX_NO_DEBUG_TOOLS)", MAIN,
            "bridge is not restricted to debug-tools builds")
    require("guest_debug_bridge_ready()", MAIN,
            "activation does not fail closed on the configured ready signal")
    require("g_guest_debug_bridge_frames = 2", MAIN,
            "bridge no longer begins with a bounded two-sample pulse")
    require("psx_write_word((uint32_t)PSX_GUEST_DEBUG_ACTIVATE_ADDR", MAIN,
            "configured activation must select the game-owned debug lifecycle")
    require("g_guest_debug_bridge_frames = 0", MAIN,
            "lifecycle activation must not also pulse the compact-menu chord")
    require("sio_set_pad_state_slot", MAIN,
            "bridge bypasses the normal controller input path")
    require("sio_set_pad_connected((int)PSX_GUEST_DEBUG_PAD_SLOT, 1)", MAIN,
            "configured debug pad remains disconnected and cannot be polled")
    require("connected = connected || guest_debug_bridge_owns_slot(s)", MAIN,
            "device refresh can disconnect the configured debug pad")
    if MAIN.count("connected = connected || guest_debug_bridge_owns_slot(s)") < 2:
        raise AssertionError("debug pad must be present at boot and after SDL refresh")
    require("psx_write_byte((uint32_t)PSX_GUEST_DEBUG_GATE_ADDR, 1u)", MAIN,
            "configured game-owned gate is not asserted")
    require("(mod & KMOD_CTRL) != 0 && (mod & KMOD_SHIFT) != 0", MAIN,
            "shortcut must accept either-side Ctrl plus either-side Shift")
    if "(mod & (KMOD_CTRL | KMOD_SHIFT)) ==" in MAIN:
        raise AssertionError("shortcut incorrectly requires every modifier-side bit")

    # The generic runtime must not acquire the Legaia addresses or title name.
    for forbidden in ("8007B98F", "8007B83C", "LEGAIA_DEBUG_MENU_GATE"):
        if forbidden in MAIN or forbidden in CMAKE:
            raise AssertionError(f"title-specific value leaked into runtime: {forbidden}")

    print("PASS: optional guest debug-menu bridge is generic and gated")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}")
        sys.exit(1)
