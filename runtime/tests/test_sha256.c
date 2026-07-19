#include "sha256.h"

#include <stdio.h>
#include <string.h>

static int check(const char *input, const char *expected) {
    uint8_t digest[32];
    char actual[65];
    psx_sha256(input, strlen(input), digest);
    psx_sha256_hex(digest, actual);
    if (strcmp(actual, expected) != 0) {
        fprintf(stderr, "SHA-256 mismatch for synthetic vector\n");
        return 0;
    }
    return 1;
}

int main(void) {
    if (!check("", "e3b0c44298fc1c149afbf4c8996fb924"
                   "27ae41e4649b934ca495991b7852b855")) return 1;
    if (!check("abc", "ba7816bf8f01cfea414140de5dae2223"
                      "b00361a396177a9cb410ff61f20015ad")) return 1;
    puts("PASS: SHA-256 synthetic vectors");
    return 0;
}
