#!/usr/bin/env python3
"""Exercise restore invalidation through the real loader and a synthetic DLL."""

import argparse
import pathlib
import platform
import shutil
import tempfile

from test_overlay_pair_dedup_runtime import (
    compile_fixture, compile_harness, manifest, publish, run,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gcc", default=shutil.which("gcc") or shutil.which("cc"))
    args = parser.parse_args()
    if not args.gcc:
        raise SystemExit("gcc/cc is required")
    with tempfile.TemporaryDirectory(prefix="psx-restore-", ignore_cleanup_errors=True) as raw:
        tmp = pathlib.Path(raw)
        ext = ".dll" if platform.system() == "Windows" else ".so"
        fixture = tmp / f"fixture{ext}"
        harness = tmp / ("restore.exe" if platform.system() == "Windows" else "restore")
        compile_fixture(args.gcc, fixture, instance=1)
        compile_harness(args.gcc, harness)
        for scenario in ("restore-entry", "restore-continuation"):
            cache = tmp / scenario
            library = publish(cache, "gcc", f"00010000_11111111{ext}", fixture,
                              manifest([(0x80010000, 8)]))
            run([str(harness), str(cache), scenario, str(library), str(library)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
