#!/usr/bin/env python3
"""Reject incompatible snapshots even when diagnostic text is omitted or tiny."""
from test_debug_input_ports import ROOT, execute, function


def main():
    source = (ROOT / "runtime/src/boot_state.c").read_text(encoding="utf-8")
    includes = "".join(f'#include "{(ROOT / path).as_posix()}"\n' for path in
                       ["runtime/include/boot_state.h", "runtime/include/pst_wire.h"])
    code = includes + r"""
#include <stdio.h>
#include <string.h>
#define PSX_OVERLAY_CODEGEN_HASH 0x12abcdefu
#define PSX_OVERLAY_ABI_TAG 0x1234
#define PSX_OVERLAY_CODEGEN_VER 10u
""" + "\n".join(function(source, name) for name in
                     ["boot_state_parse_header", "boot_state_append_reason", "boot_state_check_buffer"])
    code += r"""
int main(void) {
    uint8_t wire[BOOT_STATE_HEADER_WIRE_BYTES];
    const uint32_t fields[] = {BOOT_STATE_MAGIC, BOOT_STATE_VERSION, 0x31415926,
        0x80010000, PSX_OVERLAY_CODEGEN_HASH, PSX_OVERLAY_ABI_TAG,
        PSX_OVERLAY_CODEGEN_VER, 16, 0};
    char reason[256], tiny[1];
    int failures = 0;
    for (int mismatch = -1; mismatch < 7; ++mismatch) {
        PstW w; pst_w_init(&w, wire, sizeof wire);
        for (int i = 0; i < 9; ++i)
            pst_w_u32(&w, fields[i] ^ (i == mismatch ? 0x80000000u : 0u));
        int expected = mismatch < 0;
        int results[] = {
            boot_state_check_buffer(wire, sizeof wire, fields[2], fields[3], reason, sizeof reason),
            boot_state_check_buffer(wire, sizeof wire, fields[2], fields[3], NULL, 0),
            boot_state_check_buffer(wire, sizeof wire, fields[2], fields[3], tiny, sizeof tiny),
            boot_state_check_buffer(wire, sizeof wire, fields[2], fields[3], reason, 0)};
        for (int i = 0; i < 4; ++i) if (results[i] != expected) {
            fprintf(stderr, "field %d diagnostics mode %d accepted=%d expected=%d\n", mismatch, i, results[i], expected);
            ++failures;
        }
    }
    if (boot_state_check_buffer(wire, sizeof wire - 1, fields[2], fields[3], NULL, 0)) ++failures;
    if (failures) return 1;
    puts("snapshot identity rejection is independent of diagnostic storage");
    return 0;
}
"""
    execute("boot-state-header", code)


if __name__ == "__main__":
    main()
