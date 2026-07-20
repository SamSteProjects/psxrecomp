#!/usr/bin/env python3
"""Capture one fail-closed, metadata-only Legaia runtime observation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from integrations.legaia.layouts import load_profile  # noqa: E402
from integrations.legaia.observer import (  # noqa: E402
    LoadedProfile,
    ObserverError,
    ProtocolClient,
    RuntimeObserver,
)


DEFAULT_PROFILE = REPOSITORY_ROOT / "integrations" / "legaia" / "layouts" / "scus94254-na-field-v1.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="legaia-observe",
        description="Capture one headless, read-only field actor-node observation from native PSXRecomp.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4370)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--connection-timeout", type=float, default=3.0)
    parser.add_argument("--request-timeout", type=float, default=5.0)
    parser.add_argument("--maximum-snapshot-attempts", type=int)
    parser.add_argument(
        "--boundary-only",
        action="store_true",
        help="validate a scoped scene epoch without reading actor nodes",
    )
    parser.add_argument(
        "--boundary-samples",
        type=int,
        default=10,
        help="additional compatible guard-only samples (default: 10)",
    )
    parser.add_argument("--full-json", action="store_true", help="also print the metadata JSON to stdout")
    args = parser.parse_args(argv)
    try:
        profile = LoadedProfile.from_document(load_profile(args.profile))
        with ProtocolClient(
            args.host,
            args.port,
            connection_timeout=args.connection_timeout,
            request_timeout=args.request_timeout,
        ) as client:
            observer = RuntimeObserver(client, profile)
            if not args.boundary_only:
                raise ValueError(
                    "retail actor traversal remains gated; use --boundary-only"
                )
            snapshot = observer.capture_boundary(args.boundary_samples)
        encoded = json.dumps(
            snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ) + "\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    except (OSError, ValueError, ObserverError) as exc:
        parser.exit(2, f"legaia-observe: error: {exc}\n")
    metrics = snapshot["metrics"]
    print(
        f"Accepted scoped boundary: epoch={snapshot['epoch']['epoch_id'][:18]}... "
        f"guard={snapshot['guard']['token'][:12]} "
        f"samples={snapshot['guard']['compatible_sample_count']} "
        f"frames={snapshot['frames']['first']}->{snapshot['frames']['last']} "
        f"requests={metrics['request_count']} actor_bytes=0 "
        f"duration_ms={metrics['duration_ms']}"
    )
    print(f"Saved metadata-only boundary diagnostic to {args.output}")
    if args.full_json:
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
