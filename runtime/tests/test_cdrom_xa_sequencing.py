#!/usr/bin/env python3
"""Structural regressions for CD/XA sequencing and exception-time VBlank.

These checks pin the small generic corrections recovered from the earlier
Legaia runtime branch without carrying its title-specific probes or debug UI.
"""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
CDROM = (ROOT / "runtime" / "src" / "cdrom.c").read_text(encoding="utf-8")
INTERRUPTS = (ROOT / "runtime" / "src" / "interrupts.c").read_text(
    encoding="utf-8"
)


def function_body(source: str, name: str) -> str:
    match = re.search(rf"\b{name}\s*\([^;]*?\)\s*\{{", source, re.S)
    if not match:
        raise AssertionError(f"missing function: {name}")
    start = match.end()
    depth = 1
    for pos in range(start, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[start:pos]
    raise AssertionError(f"unterminated function: {name}")


def require(pattern: str, text: str, message: str) -> None:
    if not re.search(pattern, text, re.S):
        raise AssertionError(message)


def main() -> int:
    scheduled = function_body(INTERRUPTS, "interrupts_service_scheduled_events")
    require(
        r"while\s*\(\s*cycles_since_vblank\s*>=\s*VBLANK_CYCLES\s*\)",
        scheduled,
        "scheduled VBlank edges are missing",
    )
    if re.search(r"if\s*\(\s*in_exception\s*\)\s*return", scheduled):
        raise AssertionError("VBlank scheduling is still suppressed in exceptions")

    read_sector = function_body(CDROM, "read_sector_at")
    require(
        r"sector_available\s*=\s*delivery\.data_delivered\s*\?\s*1\s*:\s*0",
        read_sector,
        "FIFO visibility is no longer separated from physical delivery",
    )
    require(
        r"return\s+1\s*;\s*$",
        read_sector,
        "filtered XA sectors no longer report a physical-sector arrival",
    )

    require(
        r"case\s+0x15:[\s\S]*?case\s+0x16:[\s\S]*?last_sector_lba\s*=\s*"
        r"msf_to_lba\(seek_min,\s*seek_sec,\s*seek_sect\)",
        CDROM,
        "seek completion does not update the reported drive position",
    )

    visibility = function_body(CDROM, "response_visibility_delayed")
    require(
        r'getenv\("PSX_CD_RESPONSE_VISIBILITY_DELAY"\)',
        visibility,
        "response-visibility compatibility switch is missing",
    )
    require(
        r"PSX_CD_RESPONSE_VISIBILITY_DELAY_DEFAULT",
        visibility,
        "response visibility has no per-game build default",
    )
    for expression in (
        r"!response_visibility_delayed\(\).*response_read\s*<\s*response_count",
        r"response_visibility_delayed\(\)\s*\?\s*0xE0\s*:\s*irq_flag",
    ):
        require(expression, CDROM, "controller response visibility is not gated")

    print("PASS: CD/XA sequencing corrections remain present")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}")
        sys.exit(1)
