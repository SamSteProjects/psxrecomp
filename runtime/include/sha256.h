#pragma once
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct { uint32_t state[8]; uint64_t bit_count; uint8_t block[64]; size_t block_len; } PSXSha256;
void psx_sha256_init(PSXSha256 *ctx);
void psx_sha256_update(PSXSha256 *ctx, const void *data, size_t len);
void psx_sha256_final(PSXSha256 *ctx, uint8_t out[32]);
void psx_sha256(const void *data, size_t len, uint8_t out[32]);
void psx_sha256_hex(const uint8_t digest[32], char out[65]);
#ifdef __cplusplus
}
#endif
