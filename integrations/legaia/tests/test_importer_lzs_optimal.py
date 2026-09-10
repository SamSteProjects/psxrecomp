"""Minimum exact-expansion token costs, ring parity and bounded fallback checks."""
from itertools import product
import os
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from importer.core import ImportError, decompress_lzs
from importer.lzs_optimal import MAX_OPTIMAL_BYTES, compress_lzs_optimal
from importer.serialization import compress_lzs, serialize_man_decoded


def strict_decode(encoded, size):
    """Independent full-token expansion: never clips a reference to final size."""
    window = bytearray(4096)
    write, offset = 0xFEE, 0
    decoded = bytearray()
    while len(decoded) < size:
        flags = encoded[offset]
        offset += 1
        for bit in range(8):
            if flags & (1 << bit):
                values = [encoded[offset]]
                offset += 1
                length = 1
            else:
                source = encoded[offset] | ((encoded[offset + 1] & 0xF0) << 4)
                length = (encoded[offset + 1] & 15) + 3
                offset += 2
                values = None
            if len(decoded) + length > size:
                raise AssertionError("token expands past the declared decoded size")
            for step in range(length):
                value = values[0] if values else window[(source + step) & 4095]
                decoded.append(value)
                window[write] = value
                write = (write + 1) & 4095
            if len(decoded) == size:
                break
    if offset != len(encoded):
        raise AssertionError("unused bytes after final exact token")
    return bytes(decoded)


def brute_cost(data):
    """Enumerate token-count/payload-count possibilities for tiny input.

    Matches are independently simulated by appending to a history buffer.
    Eighteen initial zeros cover all distinct initial matches for these short
    inputs; unlike the encoder this oracle stores absolute token counts.
    """
    reachable = [set() for _ in range(len(data) + 1)]
    reachable[0].add((0, 0))
    for cursor in range(len(data)):
        copies = set()
        history = b"\0" * 18 + data[:cursor]
        for distance in range(1, len(history) + 1):
            trial = bytearray(history)
            for length in range(1, min(18, len(data) - cursor) + 1):
                value = trial[-distance]
                if value != data[cursor + length - 1]:
                    break
                trial.append(value)
                if length >= 3:
                    copies.add(length)
        for tokens, payload in reachable[cursor]:
            reachable[cursor + 1].add((tokens + 1, payload + 1))
            for length in copies:
                reachable[cursor + length].add((tokens + 1, payload + 2))
    return min((payload + (tokens + 7) // 8 for tokens, payload in reachable[-1]), default=0)


class OptimalLzsTests(unittest.TestCase):
    def test_exhaustive_small_inputs_match_bruteforce_token_cost(self):
        for size in range(10):
            for values in product((0, 65), repeat=size):
                data = bytes(values)
                encoded = compress_lzs_optimal(data)
                self.assertEqual(len(encoded), brute_cost(data), data.hex())
                self.assertEqual(strict_decode(encoded, len(data)), data)
        # Extra cases cross more than one eight-token control group.
        for data in (bytes(range(1, 18)), b"ABCDEFGABCDEFGHI", b"abcabcXabcabcYabcabc"):
            self.assertEqual(len(compress_lzs_optimal(data)), brute_cost(data))

    def test_zero_window_overlap_ring_wrap_and_determinism(self):
        rng = random.Random(94254)
        cases = [b"\0" * 8193, b"AB" * 4097, bytes(range(256)) * 33]
        cases += [bytes(rng.randrange(8) for _ in range(size)) for size in (17, 18, 19, 72, 4095, 4096, 4097)]
        for data in cases:
            encoded = compress_lzs_optimal(data)
            self.assertEqual(strict_decode(encoded, len(data)), data)
            self.assertEqual(decompress_lzs(encoded, len(data)), (data, len(encoded)))
            self.assertEqual(compress_lzs_optimal(data), encoded)
            self.assertLessEqual(len(encoded), len(compress_lzs(data)))

    def test_bound_and_allocation_failure_reject_cleanly(self):
        for data in (bytearray(b"x"), "x", bytes(MAX_OPTIMAL_BYTES + 1)):
            with self.assertRaisesRegex(ImportError, "256 KiB"):
                compress_lzs_optimal(data)
        with patch("importer.lzs_optimal.array", side_effect=MemoryError):
            with self.assertRaisesRegex(ImportError, "insufficient memory"):
                compress_lzs_optimal(b"test")
        largest = bytes(MAX_OPTIMAL_BYTES)
        encoded = compress_lzs_optimal(largest)
        self.assertEqual(strict_decode(encoded, len(largest)), largest)

    def test_noop_and_greedy_fits_keep_exact_bytes_and_statistics(self):
        baseline = b"A" * 64
        # Generous literal-coded source span proves greedy fitting behavior.
        stream = b"".join(b"\xff" + baseline[n:n + 8] for n in range(0, len(baseline), 8))
        with patch("importer.lzs_optimal.compress_lzs_optimal", side_effect=AssertionError("fallback should not run")):
            same, stats = serialize_man_decoded(stream, len(baseline), baseline, "fixture")
            self.assertEqual(same, stream)
            self.assertNotIn("compression_strategy", stats)
            changed = b"B" * 64
            result, stats = serialize_man_decoded(stream, len(baseline), changed, "fixture")
            greedy = compress_lzs(changed)
            self.assertEqual(result, greedy + stream[len(greedy):])
            self.assertEqual(stats, {"original_encoded_size": len(stream),
                                     "new_encoded_size": len(greedy), "decoded_size": len(baseline)})

    def test_provably_incompressible_change_still_rejects_capacity(self):
        baseline = bytes(64)
        original = compress_lzs(baseline)
        changed = bytes(range(64))
        # No three-byte repetition, nor three initial zero bytes: only literals.
        self.assertEqual(len(compress_lzs_optimal(changed)), 72)
        with self.assertRaisesRegex(ImportError, "requires 72 compressed bytes.*relocation is unsupported"):
            serialize_man_decoded(original, len(changed), changed, "fixture")
        self.assertEqual(decompress_lzs(original, len(baseline))[0], baseline)


@unittest.skipUnless(os.environ.get("LEGAIA_DISC_BIN"), "requires private retail disc")
class RetailOptimalLzsTests(unittest.TestCase):
    def test_actual_dialogue_plus_position_overflow_uses_exact_optimal_fallback(self):
        from importer.dialogue_authoring import load_dialogue_authoring_context
        from importer.pipeline import _disc_context
        from importer.serialization import patch_man_positions
        disc = os.environ["LEGAIA_DISC_BIN"]
        with _disc_context(disc):
            context = load_dialogue_authoring_context(disc, "town01")
            run = context.options("scene://town01/actors/man-p1/0049")["runs"][0]
            changed, _ = context.patch({run["semantic_id"]: "SDK text"})
            changed, _ = patch_man_positions(changed, "town01", {1: {"x": 9984}})
            original = context._stream  # Private verified source bytes; never tracked.
            self.assertEqual(len(original), 24894)
            self.assertEqual(len(compress_lzs(changed)), 24896)
            result, stats = serialize_man_decoded(original, len(changed), changed, "town01")
            self.assertEqual(stats["compression_strategy"], "bounded_optimal_lzs")
            self.assertEqual(stats["greedy_encoded_size"], 24896)
            self.assertEqual(stats["new_encoded_size"], 24504)
            self.assertEqual(len(result), len(original))
            self.assertEqual(strict_decode(result[:stats["new_encoded_size"]], len(changed)), changed)
            self.assertEqual(result[stats["new_encoded_size"]:], original[stats["new_encoded_size"]:])


if __name__ == "__main__":
    unittest.main()
