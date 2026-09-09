#!/usr/bin/env python3
"""Command line entry point for the read-only Legaia metadata importer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

INTEGRATION_ROOT = Path(__file__).resolve().parents[1]
if str(INTEGRATION_ROOT) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_ROOT))

from importer.pipeline import ImportError, import_scene, list_scenes, write_metadata  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="legaia-import",
        description="Import deterministic field-scene metadata from a user-owned Legaia disc.",
    )
    parser.add_argument("--disc", required=True, type=Path, help="Mode 2/2352 .bin image or matching .cue")
    parser.add_argument("--scene", default="town01", help="exact CDNAME scene label; unsupported layouts fail explicitly")
    parser.add_argument("--list-scenes", action="store_true", help="probe a bounded page of CDNAME blocks for field scenes")
    parser.add_argument("--offset", type=int, default=0, help="catalog block offset")
    parser.add_argument("--limit", type=int, default=64, help="catalog blocks to inspect, 1-128")
    parser.add_argument("--prefix", default="", help="catalog label prefix, for example town")
    parser.add_argument("--output", required=True, type=Path, help="metadata JSON destination")
    args = parser.parse_args(argv)
    try:
        result = (list_scenes(args.disc, offset=args.offset, limit=args.limit, prefix=args.prefix)
                  if args.list_scenes else import_scene(args.disc, args.scene))
        write_metadata(args.output, result)
    except ImportError as exc:
        parser.exit(2, f"legaia-import: error: {exc}\n")
    if args.list_scenes:
        print(f"Found {len(result['scenes'])} scenes in {result['scanned_blocks']} blocks; next_offset={result['next_offset']}; wrote {args.output}")
    else:
        print(f"Imported {len(result['actors'])} actor placements for {args.scene} to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
