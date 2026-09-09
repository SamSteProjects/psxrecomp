#!/usr/bin/env python3
"""Run the actual bounded lifecycle implementation against synthetic RAM."""
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    source = (ROOT / "runtime/src/overlay_capture.c").read_text(encoding="utf-8")
    lifecycle = source.split("uint32_t g_overlay_witness_request_bitmap[16384];", 1)[1].split(
        "/* ---- Base64 encoder", 1)[0]
    code = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "overlay_capture.h"
#include "crc32.h"
uint32_t g_overlay_witness_request_bitmap[16384];
uint64_t s_frame_count = 10;
static int speculative;
int overlay_loader_observation_is_speculative(void) { return speculative; }
static uint8_t ram[0x200000];
static uint32_t generation[512];
uint8_t *memory_get_ram_ptr(void) { return ram; }
void overlay_watch_set_range(uint32_t phys, uint32_t length) {
    assert(phys < sizeof(ram) && length <= sizeof(ram) - phys);
}
uint32_t overlay_watch_pagegen_sum(uint32_t phys, uint32_t length) {
    assert(length == 4 && phys < sizeof(ram)); return generation[phys >> 12];
}
''' + lifecycle + r'''
int main(void) {
    OverlayExecutionOwner owner;
    OverlayLifecycleInstance instance;
    overlay_lifecycle_set_tracking_enabled(1);
    uint64_t initial = overlay_lifecycle_catalog_token();
    /* Unrequested execution cannot recreate the old per-instruction table. */
    overlay_lifecycle_observe_interpreter(0x80001000, 0x12345678);
    assert(overlay_lifecycle_owner_count() == 0);
    assert(!overlay_lifecycle_owner_at(0x80001000, &owner));
    assert(g_overlay_witness_request_bitmap[0x1000 >> 7]);
    lifecycle_create_dma_instance(0x1000, 16, ram + 0x1000);
    overlay_lifecycle_observe_interpreter(0x80001000, 0x12345678);
    assert(overlay_lifecycle_owner_at(0x80001000, &owner));
    assert(owner.owner == OVERLAY_EXEC_OWNER_INTERPRETER && owner.instance_id == 1);
    assert(owner.instruction_word_at_observation == 0x12345678);
    assert(overlay_lifecycle_owner_observation_current(&owner));
    assert(owner.hits == 1);
    speculative = 1;
    overlay_lifecycle_observe_interpreter(0x1000, 0xBAD);
    overlay_lifecycle_note_execution(0x1000, OVERLAY_EXEC_OWNER_STATIC_NATIVE, 0, 0);
    assert(overlay_lifecycle_owner_at(0x1000, &owner));
    assert(owner.hits == 1 && owner.instruction_word_at_observation == 0x12345678);
    speculative = 0;
    /* A write invalidates prior ownership even when the same bytes return. */
    ++generation[1];
    assert(!overlay_lifecycle_owner_observation_current(&owner));
    overlay_lifecycle_note_execution(0x80001000, OVERLAY_EXEC_OWNER_CACHED_NATIVE,
                                    7, OVERLAY_EXEC_REASON_NATIVE_DISPATCH);
    assert(overlay_lifecycle_owner_at(0x80001000, &owner));
    assert(owner.owner == OVERLAY_EXEC_OWNER_CACHED_NATIVE && owner.registration_id == 7);
    assert(owner.hits == 2 && overlay_lifecycle_owner_observation_current(&owner));
    lifecycle_create_dma_instance(0x1000, 16, ram + 0x1000);
    overlay_lifecycle_observe_interpreter(0x80001000, 0);
    assert(overlay_lifecycle_owner_at(0x80001000, &owner) && owner.instance_id == 2);
    assert(overlay_lifecycle_get_instance(0, &instance) && !instance.active);
    assert(instance.successor_id == 2);
    /* RAM restore resets evidence and changes identity without guest mutation. */
    uint64_t previous = overlay_lifecycle_catalog_token();
    overlay_lifecycle_reset();
    assert(previous != overlay_lifecycle_catalog_token());
    assert(initial != overlay_lifecycle_catalog_token());
    assert(!overlay_lifecycle_owner_at(0x1000, &owner));
    assert(overlay_lifecycle_instance_count() == 0);
    overlay_lifecycle_observe_interpreter(0x1000, 0);
    assert(overlay_lifecycle_owner_at(0x1000, &owner) && owner.instance_id == 0);
    /* Invalid and unaligned addresses cannot read beyond synthetic RAM. */
    overlay_lifecycle_note_execution(0x801FFFFF, 1, 0, 0);
    overlay_lifecycle_note_execution(0x80200000, 1, 0, 0);
    assert(overlay_lifecycle_owner_count() == 1);
    lifecycle_create_dma_instance(0x1FFFFF, 16, ram);
    assert(overlay_lifecycle_instance_count() == 0);
    puts("requested witnesses, backend changes, restore epochs and bounds: passed");
    return 0;
}
'''
    compiler = os.environ.get("CC") or shutil.which("gcc")
    if not compiler:
        fallback = Path("C:/msys64/ucrt64/bin/gcc.exe")
        if fallback.is_file(): compiler = str(fallback)
    if not compiler: raise RuntimeError("Set CC to a gcc-compatible compiler")
    env = dict(os.environ)
    env["PATH"] = str(Path(compiler).parent) + os.pathsep + env.get("PATH", "")
    with tempfile.TemporaryDirectory(prefix="observer-lifecycle-") as directory:
        c = Path(directory) / "test.c"
        exe = Path(directory) / "test.exe"
        c.write_text(code, encoding="utf-8")
        subprocess.run([compiler, "-std=c11", "-O1", "-Wall", "-Wextra",
                        "-I", str(ROOT / "runtime/include"), str(c),
                        str(ROOT / "runtime/src/crc32.c"), "-o", str(exe)],
                       env=env, check=True)
        subprocess.run([str(exe)], env=env, check=True)


if __name__ == "__main__":
    main()
