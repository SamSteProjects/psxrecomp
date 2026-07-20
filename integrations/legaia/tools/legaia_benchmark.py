#!/usr/bin/env python3
"""Run one bounded, read-only performance interval against a running runtime."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from integrations.legaia.observer.client import ProtocolClient
from integrations.legaia.observer.performance import BenchmarkCase, PerformanceHarness, load_benchmark_targets


DEFAULT_TARGETS = REPOSITORY_ROOT / "integrations" / "legaia" / "benchmarks" / "scus94254-na-world-map-v1.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a bounded metadata-only PSXRecomp performance case.")
    parser.add_argument("--target", required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4370)
    parser.add_argument("--poll-hz", type=float, default=0.0)
    parser.add_argument("--warmup-seconds", type=float, default=5.0)
    parser.add_argument("--measurement-seconds", type=float, default=15.0)
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        targets = load_benchmark_targets(args.targets)
        case = BenchmarkCase(args.case_id, args.target, args.poll_hz, args.warmup_seconds, args.measurement_seconds, args.repetitions)
        with ProtocolClient(args.host, args.port) as client:
            client.negotiate()
            report = PerformanceHarness(client, targets).run_case(case)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(2, f"legaia-benchmark: error: {exc}\n")
    print(f"Saved metadata-only performance report to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
