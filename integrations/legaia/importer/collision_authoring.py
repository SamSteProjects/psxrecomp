"""Exact source MAP wall-bit edits; no live movement or script paint inference.

Uses field_map._rectangles' evidenced row/column/quadrant convention. The low
nibble stores floor-tier information and is never changed by this authoring API.
"""
from hashlib import sha256

from .core import ImportError


def patch_collision_walls(original: bytes, expected_sha256: str, edits: list[dict]):
    """Return an equal-size MAP and field audit without modifying source bytes."""
    if not isinstance(original, bytes) or len(original) != 0x12000:
        raise ImportError("Collision authoring requires the supported 0x12000-byte MAP")
    if sha256(original).hexdigest() != expected_sha256:
        raise ImportError("Collision MAP source hash differs from the authored binding")
    if not isinstance(edits, list) or len(edits) > 4096:
        raise ImportError("Collision authoring accepts at most 4096 wall-bit edits")
    seen = set()
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {"row", "column", "quadrant", "blocked"}:
            raise ImportError("Wall edits require row, column, quadrant and blocked only")
        for key, low, high in (("row", 1, 127), ("column", 0, 127), ("quadrant", 0, 3)):
            if type(edit[key]) is not int or not low <= edit[key] <= high:
                raise ImportError(f"Wall {key} is outside the evidenced canonical grid")
        if type(edit["blocked"]) is not bool:
            raise ImportError("Wall blocked value must be boolean")
        key = (edit["row"], edit["column"], edit["quadrant"])
        if key in seen:
            raise ImportError("Duplicate collision wall-bit edit")
        seen.add(key)
    result, audit = bytearray(original), []
    for edit in sorted(edits, key=lambda e: (e["row"], e["column"], e["quadrant"])):
        offset = 0x4000 + edit["row"] * 128 + edit["column"]
        mask = 1 << (4 + edit["quadrant"])
        before = bool(original[offset] & mask)
        if before == edit["blocked"]:
            continue
        result[offset] = result[offset] | mask if edit["blocked"] else result[offset] & ~mask
        audit.append({**edit, "field": "collision.blocked", "byte_offset": offset,
                      "bit_mask": mask, "before_value": before, "after_value": edit["blocked"],
                      "scope": "source-MAP-wall-bit-only"})
    allowed = {}
    for row in audit:
        allowed[row["byte_offset"]] = allowed.get(row["byte_offset"], 0) | row["bit_mask"]
    if any((a ^ b) & ~allowed.get(i, 0) for i, (a, b) in enumerate(zip(original, result))):
        raise ImportError("Collision patch altered an unaudited bit")
    return bytes(result), audit
