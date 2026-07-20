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
    SceneTransitionWatcher,
    TransitionLimits,
)


DEFAULT_PROFILE = REPOSITORY_ROOT / "integrations" / "legaia" / "layouts" / "scus94254-na-field-v1.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="legaia-observe",
        description="Run one headless, read-only Legaia observation acceptance action.",
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
    parser.add_argument(
        "--transition-watch",
        action="store_true",
        help="watch a manual normal exit and re-entry without actor reads",
    )
    parser.add_argument("--poll-interval", type=float, default=0.1)
    parser.add_argument("--initial-timeout", type=float, default=30.0)
    parser.add_argument("--exit-timeout", type=float, default=180.0)
    parser.add_argument("--outside-timeout", type=float, default=30.0)
    parser.add_argument("--reentry-timeout", type=float, default=180.0)
    parser.add_argument("--stabilization-timeout", type=float, default=30.0)
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
            if args.boundary_only and args.transition_watch:
                raise ValueError("choose either --boundary-only or --transition-watch")
            if args.transition_watch:
                watcher = SceneTransitionWatcher(
                    observer.selector,
                    profile,
                    limits=TransitionLimits(
                        poll_interval_seconds=args.poll_interval,
                        initial_timeout_seconds=args.initial_timeout,
                        exit_timeout_seconds=args.exit_timeout,
                        outside_timeout_seconds=args.outside_timeout,
                        reentry_timeout_seconds=args.reentry_timeout,
                        stabilization_timeout_seconds=args.stabilization_timeout,
                    ),
                )
                snapshot = watcher.run()
            elif args.boundary_only:
                snapshot = observer.capture_boundary(args.boundary_samples)
            else:
                raise ValueError(
                    "retail actor traversal remains gated; use --boundary-only or --transition-watch"
                )
        encoded = json.dumps(
            snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ) + "\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    except (OSError, ValueError, ObserverError) as exc:
        parser.exit(2, f"legaia-observe: error: {exc}\n")
    metrics = snapshot["metrics"]
    if args.transition_watch:
        print(
            "Accepted town01 transition: "
            f"initial={snapshot['initial_epoch']['token'][:12]} "
            f"reentry={snapshot['reentry_epoch']['token'][:12]} "
            f"requests={metrics['request_count']} actor_bytes=0 "
            f"duration_ms={metrics['duration_ms']}"
        )
        print(f"Saved metadata-only transition report to {args.output}")
    else:
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
