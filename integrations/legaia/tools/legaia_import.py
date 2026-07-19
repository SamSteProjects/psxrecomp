#!/usr/bin/env python3
"""Command line entry point for the read-only Legaia metadata importer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

INTEGRATION_ROOT = Path(__file__).resolve().parents[1]
if str(INTEGRATION_ROOT) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_ROOT))

from importer.pipeline import ImportError, import_scene, write_metadata  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="legaia-import",
        description="Import deterministic, metadata-only town01 actor placements from a user-owned disc.",
    )
    parser.add_argument("--disc", required=True, type=Path, help="Mode 2/2352 .bin image or matching .cue")
    parser.add_argument("--scene", default="town01", help="scene label (currently town01 only)")
    parser.add_argument("--output", required=True, type=Path, help="metadata JSON destination")
    args = parser.parse_args(argv)
    try:
        result = import_scene(args.disc, args.scene)
        write_metadata(args.output, result)
    except ImportError as exc:
        parser.exit(2, f"legaia-import: error: {exc}\n")
    print(f"Imported {len(result['actors'])} actor placements for {args.scene} to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
