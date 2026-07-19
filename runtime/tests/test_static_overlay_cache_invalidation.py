#!/usr/bin/env python3
"""Synthetic regression for generation-gated static overlay validation.

The runtime's static matcher is deliberately kept inside overlay_loader.c, so
this test combines a source-wiring assertion with an executable model of the
documented generation/CRC contract. No retail code or game-specific address is
used.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[2]
LOADER_SOURCE = ROOT / "runtime" / "src" / "overlay_loader.c"
MEMORY_SOURCE = ROOT / "runtime" / "src" / "memory.c"
PAGE_SIZE = 4096


def function_body(source: str, name: str) -> str:
    match = re.search(
        rf"\b(?:static\s+)?(?:inline\s+)?(?:int|void|uint32_t)\s+"
        rf"{re.escape(name)}\s*\([^;]*?\)\s*\{{",
        source,
        re.S,
    )
    if not match:
        raise AssertionError(f"missing function definition: {name}")

    start = match.end()
    depth = 1
    for pos in range(start, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[start:pos]
    raise AssertionError(f"unterminated function definition: {name}")


class GuestMemory:
    """Minimal model of memory.c's watched-page write chokepoint."""

    def __init__(self, size: int = PAGE_SIZE * 4) -> None:
        self.bytes = bytearray(size)
        self.watched: set[int] = set()
        self.generation = [0] * (size // PAGE_SIZE)

    def watch(self, base: int, length: int) -> None:
        first = base // PAGE_SIZE
        last = (base + length - 1) // PAGE_SIZE
        self.watched.update(range(first, last + 1))

    def generation_sum(self, base: int, length: int) -> int:
        first = base // PAGE_SIZE
        last = (base + length - 1) // PAGE_SIZE
        return sum(self.generation[first : last + 1])

    def guest_write(self, base: int, payload: bytes) -> None:
        """An ordinary guest write, not a debugger mutation."""
        first = base // PAGE_SIZE
        last = (base + len(payload) - 1) // PAGE_SIZE
        for page in range(first, last + 1):
            if page in self.watched:
                self.generation[page] += 1
        self.bytes[base : base + len(payload)] = payload


@dataclass(frozen=True)
class SourceIdentity:
    ranges: tuple[tuple[int, int], ...]
    compiled_crc: int
    abi: str


class StaticMatcher:
    """Contract model for psx_overlay_static_code_matches."""

    def __init__(self, memory: GuestMemory) -> None:
        self.memory = memory
        self.cache: dict[SourceIdentity, tuple[int, bool]] = {}
        self.rehashes = 0

    def matches(self, source: SourceIdentity) -> bool:
        for base, length in source.ranges:
            self.memory.watch(base, length)
        generation = sum(
            self.memory.generation_sum(base, length)
            for base, length in source.ranges
        )
        cached = self.cache.get(source)
        if cached is not None and cached[0] == generation:
            return cached[1]

        live = bytearray()
        for base, length in source.ranges:
            live.extend(self.memory.bytes[base : base + length])
        matches = (zlib.crc32(live) & 0xFFFFFFFF) == source.compiled_crc
        self.cache[source] = (generation, matches)
        self.rehashes += 1
        return matches


class StaticOverlayInvalidationTest(unittest.TestCase):
    def test_static_matcher_registers_pages_before_reading_generation(self) -> None:
        source = LOADER_SOURCE.read_text(encoding="utf-8")
        body = function_body(source, "psx_overlay_static_code_matches")

        bounds = body.find("len > 2u * 1024u * 1024u - lo")
        register = body.find("overlay_watch_set_range(lo, len)")
        generation = body.find("overlay_watch_pagegen_sum(lo, len)")
        self.assertGreaterEqual(bounds, 0)
        self.assertGreater(register, bounds)
        self.assertGreater(generation, register)
        self.assertIn("expected_crc", body)
        self.assertIn("crc == expected_crc", body)
        self.assertNotRegex(body, r"Legaia|SCUS[-_]?94254")

    def test_all_ordinary_ram_store_widths_advance_overlay_generation(self) -> None:
        source = MEMORY_SOURCE.read_text(encoding="utf-8")
        for name, width in (
            ("psx_write_word_raw", 4),
            ("psx_write_half_raw", 2),
            ("psx_write_byte_raw", 1),
        ):
            body = function_body(source, name)
            note = body.find(f"overlay_watch_note_write(phys, {width})")
            mutation_match = re.search(r"ram\[phys\]\s*=", body)
            mutation = mutation_match.start() if mutation_match else -1
            self.assertGreaterEqual(note, 0, f"{name} does not notify overlay watch")
            self.assertGreater(mutation, note, f"{name} notifies after RAM mutation")

    def test_same_address_replacement_cannot_reuse_stale_native_identity(self) -> None:
        memory = GuestMemory()
        matcher = StaticMatcher(memory)
        base = PAGE_SIZE + 64
        region_a = bytes.fromhex("102030405060708090a0b0c0d0e0f000")
        region_b = bytes.fromhex("ffeeddccbbaa99887766554433221100")
        ranges = ((base, len(region_a)),)
        source_a = SourceIdentity(ranges, zlib.crc32(region_a) & 0xFFFFFFFF, "abi-v1")
        source_b = SourceIdentity(ranges, zlib.crc32(region_b) & 0xFFFFFFFF, "abi-v1")

        # Initial loading occurs before registration, matching an overlay that
        # becomes dispatchable only after its compiled variant is considered.
        memory.guest_write(base, region_a)
        self.assertTrue(matcher.matches(source_a))
        self.assertEqual(matcher.rehashes, 1)

        # No write means the generation and correct cached verdict are reusable.
        self.assertTrue(matcher.matches(source_a))
        self.assertEqual(matcher.rehashes, 1)

        # An ordinary guest write replaces A at the same address and length.
        memory.guest_write(base, region_b)
        self.assertFalse(matcher.matches(source_a))
        self.assertEqual(matcher.rehashes, 2)

        # B has distinct content identity and becomes the only matching owner.
        self.assertNotEqual(source_a.compiled_crc, source_b.compiled_crc)
        self.assertTrue(matcher.matches(source_b))
        self.assertFalse(matcher.matches(source_a))

        # Even a same-byte write advances generation; revalidation may safely
        # accept B again, but it cannot bypass the live-byte hash.
        before = matcher.rehashes
        memory.guest_write(base, region_b)
        self.assertTrue(matcher.matches(source_b))
        self.assertEqual(matcher.rehashes, before + 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
