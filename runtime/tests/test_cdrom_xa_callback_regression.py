#!/usr/bin/env python3
"""Structural regressions for the CD/XA callback scheduling contract.

These rules are generic runtime behavior, but Legend of Legaia exercises all
of them through libcd's synchronous callback/VSync path.  Keep this test
source-level and payload-free so a rebase cannot silently drop the contract.
"""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
CDROM = (ROOT / "runtime" / "src" / "cdrom.c").read_text(encoding="utf-8")
INTERRUPTS = (ROOT / "runtime" / "src" / "interrupts.c").read_text(encoding="utf-8")
RUNTIME_CMAKE = (ROOT / "runtime" / "runtime.cmake").read_text(encoding="utf-8")


def body(source: str, name: str) -> str:
    match = re.search(rf"\b(?:static\s+)?(?:int|void|uint32_t)\s+{name}\s*\([^;]*?\)\s*\{{", source, re.S)
    if not match:
        raise AssertionError(f"missing {name}")
    depth = 1
    for offset, char in enumerate(source[match.end():], start=match.end()):
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[match.end():offset]
    raise AssertionError(f"unterminated {name}")


def require(pattern: str, source: str, label: str) -> None:
    if not re.search(pattern, source, re.S):
        raise AssertionError(label)


def main() -> int:
    visibility = body(CDROM, "response_visibility_delayed")
    require(r"getenv\s*\(\s*\"PSX_CD_RESPONSE_VISIBILITY_DELAY\"\s*\)", visibility,
            "missing response-visibility opt-in")
    require(r"cdrom_irq_present_due\s*!=\s*0", visibility,
            "visibility gate must use the absolute IRQ presentation deadline")
    require(r"psx_cycle_count\s*<\s*cdrom_irq_present_due", visibility,
            "visibility gate must hold until the IRQ presentation deadline")

    read = body(CDROM, "cdrom_read")
    for expression in (
        r"!response_visibility_delayed\(\)\s*&&\s*response_read\s*<\s*response_count",
        r"response_visibility_delayed\(\)\s*\?\s*0xE0\s*:\s*irq_flag",
    ):
        require(expression, read, "controller response is visible before IRQ presentation")

    sector = body(CDROM, "read_sector_at")
    require(r"Realtime XA[\s\S]*?return\s+1\s*;", sector,
            "realtime XA arrival no longer raises its physical-sector event")

    pending = body(CDROM, "process_pending")
    require(r"case\s+0x15[\s\S]*?case\s+0x16[\s\S]*?last_sector_lba\s*=\s*msf_to_lba", pending,
            "seek completion does not refresh the reported drive position")

    scheduled = body(INTERRUPTS, "interrupts_service_scheduled_events")
    if re.search(r"if\s*\(\s*in_exception\s*\)\s*return\s*;", scheduled):
        raise AssertionError("scheduled VBlank edges are suppressed inside callbacks")

    require(r"PSX_CD_RESPONSE_VISIBILITY_DELAY_DEFAULT.*CACHE\s+STRING",
            RUNTIME_CMAKE,
            "runtime cannot bake the response-visibility default into a packaged title")
    require(r"PSX_CD_RESPONSE_VISIBILITY_DELAY_DEFAULT=\$\{PSX_CD_RESPONSE_VISIBILITY_DELAY_DEFAULT\}",
            RUNTIME_CMAKE,
            "configured response-visibility default is not propagated to the target")

    print("PASS: CD/XA callback scheduling contract is present")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1)
