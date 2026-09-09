#!/usr/bin/env python3
"""Compile production snapshot code and run corruption/allocator regressions."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    cc = os.environ.get("CC") or shutil.which("gcc")
    if not cc and Path("C:/msys64/ucrt64/bin/gcc.exe").is_file():
        cc = "C:/msys64/ucrt64/bin/gcc.exe"
    if not cc:
        raise RuntimeError("Set CC to a GCC-compatible C compiler with zlib")
    env = dict(os.environ)
    env["PATH"] = str(Path(cc).parent) + os.pathsep + env.get("PATH", "")
    with tempfile.TemporaryDirectory(prefix="boot-state-transaction-") as tmp:
        objects = []
        for name in ("boot_state", "mdec", "dma", "sio"):
            obj = Path(tmp) / (name + ".o")
            extra = ["-Dmalloc=bs_test_malloc", "-Dfree=bs_test_free"] if name == "boot_state" else []
            if name == "mdec":
                extra += ["-Drealloc=bs_test_realloc"]
            subprocess.run([cc, "-std=c11", "-O2", "-flto", "-ffunction-sections", "-fdata-sections",
                            "-DPSX_NO_DEBUG_TOOLS", "-I" + str(ROOT / "runtime/include"), *extra,
                            "-c", str(ROOT / f"runtime/src/{name}.c"), "-o", str(obj)],
                           env=env, check=True)
            objects.append(str(obj))
        binary = Path(tmp) / "boot-state-transaction.exe"
        subprocess.run([cc, "-std=c11", "-O2", "-flto", "-I" + str(ROOT / "runtime/include"),
                        str(ROOT / "runtime/tests/test_boot_state_transaction.c"), *objects,
                        "-Wl,--gc-sections", "-lz", "-o", str(binary)], env=env, check=True)
        subprocess.run([str(binary)], env=env, check=True)
        invariant = subprocess.run([str(binary), "--commit-failure"], env=env,
                                   capture_output=True, text=True)
        assert invariant.returncode != 0
        assert "validated section 7 failed during commit" in invariant.stderr
        assert "BUG: returned from failed commit" not in invariant.stderr
        print("PASS internal commit invariant failure terminates instead of resuming a mixed machine")


if __name__ == "__main__":
    main()
