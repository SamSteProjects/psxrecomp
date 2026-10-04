#pragma once

#include <array>
#include <cstdint>
#include <cstring>

namespace PS1::CDSector {

using Raw = std::array<uint8_t, 2352>;

inline bool IsMode2(const Raw& sector) {
    if (sector[0] || sector[11] || sector[15] != 2) return false;
    for (unsigned i = 1; i < 11; ++i) if (sector[i] != 0xFF) return false;
    return true;
}

struct Tables {
    std::array<uint32_t, 256> crc{};
    std::array<uint8_t, 256> forward{}, backward{};
    Tables() {
        for (unsigned value = 0; value < 256; ++value) {
            uint32_t c = value;
            for (unsigned bit = 0; bit < 8; ++bit)
                c = (c >> 1) ^ ((c & 1) ? 0xD8018001u : 0u);
            crc[value] = c;
            unsigned doubled = (value << 1) ^ ((value & 0x80) ? 0x11D : 0);
            forward[value] = static_cast<uint8_t>(doubled);
            backward[value ^ doubled] = static_cast<uint8_t>(value);
        }
    }
};

inline void Parity(const uint8_t* data, uint8_t* output, unsigned majors,
                   unsigned minors, unsigned stride, unsigned increment, const Tables& tables) {
    for (unsigned major = 0; major < majors; ++major) {
        unsigned index = (major / 2) * stride + (major & 1);
        uint8_t a = 0, b = 0;
        for (unsigned minor = 0; minor < minors; ++minor) {
            uint8_t value = data[index];
            index = (index + increment) % (majors * minors);
            a = tables.forward[a ^ value];
            b ^= value;
        }
        a = tables.backward[tables.forward[a] ^ b];
        output[major] = a;
        output[major + majors] = a ^ b;
    }
}

// Mode 2 Form 1 EDC/P/Q; header MSF is excluded from protection. Invalid
// framing fails before touching bytes. Layout mirrors tools/cd_sector.py.
inline bool EncodeForm1(Raw& sector) {
    if (!IsMode2(sector) || std::memcmp(sector.data() + 16, sector.data() + 20, 4) || (sector[18] & 0x20))
        return false;
    static const Tables tables;
    uint32_t crc = 0;
    for (unsigned i = 16; i < 2072; ++i) crc = (crc >> 8) ^ tables.crc[(crc ^ sector[i]) & 255];
    for (unsigned i = 0; i < 4; ++i) sector[2072 + i] = static_cast<uint8_t>(crc >> (8 * i));
    std::array<uint8_t, 4> header{};
    std::memcpy(header.data(), sector.data() + 12, 4);
    std::memset(sector.data() + 12, 0, 4);
    Parity(sector.data() + 12, sector.data() + 2076, 86, 24, 2, 86, tables);
    Parity(sector.data() + 12, sector.data() + 2248, 52, 43, 86, 88, tables);
    std::memcpy(sector.data() + 12, header.data(), 4);
    return true;
}

inline bool RelocateMode2(Raw& sector, uint32_t lba) {
    if (!IsMode2(sector) || lba >= 100u * 60u * 75u - 150u) return false;
    uint32_t frames = lba + 150;
    const std::array<uint32_t, 3> values{frames / 4500, frames / 75 % 60, frames % 75};
    for (unsigned i = 0; i < 3; ++i)
        sector[12 + i] = static_cast<uint8_t>((values[i] / 10) * 16 + values[i] % 10);
    return true;
}

} // namespace PS1::CDSector
