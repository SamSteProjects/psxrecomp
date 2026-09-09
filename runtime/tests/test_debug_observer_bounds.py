#!/usr/bin/env python3
"""Exercise actual observer parsing; malformed requests never reach RAM reads."""
from test_debug_input_ports import SERVER, execute, function
import re


def main():
    start = SERVER.index("typedef struct {\n    char key[65];\n    int has_key;")
    end = SERVER.index("static int observer_key_valid", start)
    declarations = SERVER[start:end]
    constants = "\n".join(re.findall(r"^#define OBS_[A-Z_]+ .*", SERVER, re.M))
    names = ["observer_scalar", "observer_uint", "observer_int", "observer_ram_phys",
             "observer_key_valid", "observer_sha256_valid", "json_extract_named_object",
             "guard_region_compare", "guard_witness_compare", "parse_guard_regions",
             "parse_guard_witnesses", "parse_observation_guard", "parse_observer_regions"]
    code = r'''
#include <assert.h>
#include <stdint.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
''' + constants + "\n" + declarations + "\n".join(function(SERVER, name) for name in names) + r'''
static void read_case(const char *addr, const char *len, int valid) {
    char json[1024]; ObserverReadRegion regions[OBS_MAX_REGIONS];
    int count = -1; uint32_t total = 0; const char *error = NULL;
    snprintf(json, sizeof(json), "{\"regions\":[{\"addr\":%s,\"len\":%s}]}", addr, len);
    int accepted = parse_observer_regions(json, regions, &count, &total, &error);
    assert(accepted == valid);
    if (!valid) assert(error && count == -1 && total == 0);
    else assert(count == 1 && total == 4 && regions[0].phys == 0x1000);
}
static void witness_case(const char *pc, int valid) {
    char json[1024]; ObservationGuardDescriptor guard; const char *error = NULL;
    snprintf(json, sizeof(json), "{\"guard\":{\"ram_regions\":[],"
        "\"execution_witnesses\":[{\"pc\":%s,\"require_current\":true}]}}", pc);
    assert(parse_observation_guard(json, &guard, &error) == valid);
    if (valid) assert(guard.witnesses[0].pc == 0x80001000);
}
int main(void) {
    read_case("\"0x80001000\"", "4", 1);
    read_case("4096", "4", 1);
    read_case("\"0xa0201000\"", "4", 1);
    const char *bad_addresses[] = {"\"garbage\"", "\"0x1000junk\"", "\"\"",
        "-1", "1.5", "true", "\"0x100000000\"", "\"0x20001000\"",
        "\"0xc0001000\"", "\"0x80801000\"", "\"0xA0801000\""};
    for (unsigned i = 0; i < sizeof(bad_addresses)/sizeof(*bad_addresses); ++i) {
        read_case(bad_addresses[i], "4", 0); witness_case(bad_addresses[i], 0);
    }
    const char *bad_lengths[] = {"0", "-1", "1.5", "4junk", "true", "4294967300",
        "\"4junk\"", "\"+4\"", "\"18446744073709551620\""};
    for (unsigned i = 0; i < sizeof(bad_lengths)/sizeof(*bad_lengths); ++i)
        read_case("\"0x1000\"", bad_lengths[i], 0);
    witness_case("\"0x80001000\"", 1);
    witness_case("\"0xa0201000\"", 1);
    witness_case("\"0x1001\"", 0);
    ObservationGuardDescriptor guard; const char *error = NULL;
    assert(!parse_observation_guard("{\"guard\":{\"ram_regions\":[],"
        "\"execution_witnesses\":[{\"pc\":4096},{\"pc\":\"0x80001000\"}]}}", &guard, &error));
    uint64_t value = 0;
    assert(observer_uint("{\"cursor\":\"18446744073709551615\"}", "cursor", UINT64_MAX, &value) == 1);
    assert(value == UINT64_MAX);
    assert(observer_uint("{\"cursor\":\"18446744073709551616\"}", "cursor", UINT64_MAX, &value) == -1);
    assert(observer_int("{\"limit\":1.5}", "limit", 16) == -1);
    assert(observer_int("{}", "limit", 16) == 16);
    puts("strict numeric fields, RAM aliases, canonical duplicate witnesses: passed");
    return 0;
}
'''
    execute("observer-bounds", code)


if __name__ == "__main__":
    main()
